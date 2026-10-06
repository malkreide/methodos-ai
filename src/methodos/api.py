"""HTTP API over the same retrieval the CLI and the MCP server use.

Thin, like `mcp_server.py`: every endpoint unpacks a request, calls into
`mcp_tools` or `search`, and translates errors. Nothing about ranking or about
the catalog is decided here.

Two things separate it from the MCP server, and both follow from the caller
being a human with a browser rather than a model:

  * It runs the LLM explanation. The MCP server deliberately does not — its
    caller already *is* a model holding the user's context. Here nothing else
    would write the prose, and the explain path is the one this deployment
    exists to exercise (see the Known gaps section of the README).
  * It serves a small console at `/`, so a query can be run, read and rated
    without a terminal.

**An explanation failure does not fail the request.** Retrieval and explanation
are independent steps, and a rejected API key should not hide a ranking that
worked: the error lands in `explanation_error` and the console shows it in red.
That is the same degrade-rather-than-fail choice `make_reranker` makes, for the
same reason. For an unambiguous yes/no on the LLM wiring there is
`POST /llm/check`, which fails loudly with the provider's own error.

Run it:
    uvicorn methodos.api:app --host 0.0.0.0 --port 8000   # needs the `api` extra

Needs an index: `methodos ingest` first. Configuration comes from the same
`METHODOS_*` environment and `.env` the CLI uses.
"""

from __future__ import annotations

import os
import tempfile
import time
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi import Path as PathParam
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, HttpUrl, ValidationError, model_validator
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import UploadFile

from methodos import __version__, mcp_tools
from methodos.config import Settings
from methodos.mcp_tools import (
    CatalogResult,
    MethodDetail,
    MethodMatch,
    MethodNotFoundError,
    RecommendResult,
)
from methodos.models import Context
from methodos.proposals import ProposalDraft
from methodos.providers import (
    EmbeddingProvider,
    LLMProvider,
    RerankProvider,
    TranscriptionProvider,
    make_embedding,
    make_llm,
    make_reranker,
    make_transcriber,
)
from methodos.providers.base import (
    EmbeddingError,
    LLMError,
    RerankError,
    TranscriberUnavailableError,
    TranscriptionError,
)
from methodos.search import StaleIndexError, collection_size, explain
from methodos.uploads import ACCEPTED_SUFFIXES, DOCUMENT_SUFFIXES, Kind

CONSOLE_HTML = Path(__file__).parent / "console.html"


def methods_dir() -> Path:
    """Where the catalog lives on disk.

    Not part of Settings, which only knows about derived artefacts. Same env var
    the MCP server reads, for the same reason: the process is often started from
    a working directory where the relative default resolves to nothing — in a
    container, always.
    """
    return Path(os.environ.get("METHODOS_METHODS_DIR", "methods"))


class Providers:
    """The three provider slots, constructed once for the process.

    Construction is cheap — every provider loads its backend lazily — but it is
    not free to *repeat*: a per-request `make_embedding` would hand each request
    a fresh LocalEmbedding whose `_model` is None, re-loading ~470MB of weights
    on every call. One instance per process keeps the loaded model resident.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.embedding: EmbeddingProvider = make_embedding(settings)
        self.reranker: RerankProvider | None = make_reranker(settings)
        self.llm: LLMProvider = make_llm(settings)
        self.transcriber: TranscriptionProvider | None = make_transcriber(settings)


@lru_cache(maxsize=1)
def _build_providers() -> Providers:
    return Providers(Settings())


def get_providers() -> Providers:
    """FastAPI dependency. Overridden in tests; cached in production.

    `except Exception` is deliberately broad, matching `_make_embedding_or_exit`
    in the CLI: this guards third-party constructors and a bad `METHODOS_*`
    value is the operator's environment, not a bug. 503 rather than 500 —
    nothing is wrong with the request.
    """
    try:
        return _build_providers()
    except ValidationError as e:
        raise HTTPException(
            status_code=503,
            detail=f"invalid configuration — check the METHODOS_* environment: {e}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=503, detail=f"failed to construct providers: {type(e).__name__}: {e}"
        ) from e


ProvidersDep = Annotated[Providers, Depends(get_providers)]


class QueryRequest(BaseModel):
    problem: str = Field(
        min_length=3,
        description="The problem in plain language. Describe the decision or the "
        "symptom, not a method — the search matches on problem descriptions. "
        "Stored verbatim in the feedback log, and sent to the LLM provider when "
        "`explain` is true: leave out personal data.",
        examples=["we need to enter a new market without burning cash"],
    )
    top_k: int = Field(default=3, ge=1, le=25, description="How many methods to return.")
    category: str | None = Field(
        default=None,
        description="Restrict to one category. Applied inside the search, not to "
        f"its output. Valid values: {', '.join(mcp_tools.valid_categories())}.",
    )
    explain: bool = Field(
        default=True,
        description="Run the LLM explanation step. Set false to isolate retrieval "
        "from the LLM when debugging — the API equivalent of `--no-llm`.",
    )
    rerank: bool | None = Field(
        default=None,
        description="Override cross-encoder reranking for this query. null uses "
        "METHODOS_RERANK_PROVIDER. true fails loudly when the reranker is "
        "unavailable, exactly as `--rerank` does.",
    )


class QueryResponse(RecommendResult):
    """The MCP server's payload plus what only this surface adds.

    Subclassed rather than nested so the fields a caller reads for retrieval —
    `ranking_basis`, `guidance`, `total_in_scope` — sit at the same level here
    as they do there, and mean exactly the same thing.
    """

    query_id: str = Field(description="ULID of the logged recommendation. Pass it to /feedback.")
    explanation: str | None = Field(
        default=None, description="Markdown prose from the LLM, or null if it did not run."
    )
    explanation_model: str | None = Field(
        default=None, description="The litellm model string that produced the explanation."
    )
    explanation_error: str | None = Field(
        default=None,
        description="Set when the explain step failed while retrieval succeeded. "
        "The matches above are unaffected — the ranking never touches the LLM.",
    )


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"] = Field(
        description="'degraded' means the index is unusable; every other field is "
        "still reported so the cause is visible."
    )
    version: str
    model: str = Field(description="litellm model string used for the explain step.")
    embedding: str
    reranker: str | None = Field(description="null when reranking is off or unavailable.")
    methods_dir: str
    chroma_path: str
    indexed_methods: int | None
    index_error: str | None = None
    transcriber: str | None = Field(
        default=None,
        description="Speech-to-text model for uploaded audio and video; null when "
        "only documents can be uploaded.",
    )
    upload_max_mb: int
    media_max_minutes: int
    upload_suffixes: list[str] = Field(
        description="File types /proposals/extract reads on this server. Audio and "
        "video are missing when no transcriber is installed."
    )


class LLMCheckResponse(BaseModel):
    """Answers 'is the LLM actually reachable', which /health deliberately does not.

    /health stays free and side-effect-free so it can back a container health
    check; proving the API key works costs a real completion, so it gets its own
    endpoint and its own (POST) verb.
    """

    ok: Literal[True]
    model: str
    latency_ms: int
    reply: str


class FeedbackRequest(BaseModel):
    method_id: str = Field(description="Exact method id, e.g. 'SWOT'.")
    rating: int = Field(ge=1, le=5)
    note: str | None = Field(
        default=None,
        description="Free-text comment, stored verbatim in the feedback log. "
        "Leave out personal data.",
    )
    query_id: str | None = Field(
        default=None, description="The query_id from /query, to tie the rating to a query."
    )


class FeedbackResponse(BaseModel):
    recorded: Literal[True]
    method_id: str
    rating: int


class ProposalRequest(BaseModel):
    """What someone knows about a method the catalog is missing.

    Mirrors the "Propose a method" issue form, so a proposal from the console
    and one from GitHub reach the `method-author` agent in the same shape.
    """

    name: str = Field(min_length=2, max_length=120, examples=["Lean Coffee"])
    problem: str = Field(
        min_length=20,
        max_length=2000,
        description="The situation someone is in when they need the method — not "
        "the method itself. This is what the catalog search will match on. Stored "
        "verbatim: leave out personal data.",
    )
    description: str | None = Field(
        default=None,
        max_length=3000,
        description="How it works, in your own words. Do not paste text you did "
        "not write — the catalog is published under CC BY-SA 4.0.",
    )
    sources: str | None = Field(
        default=None,
        max_length=1000,
        description="Original author, book, article or standard.",
    )
    links: list[HttpUrl] = Field(
        default_factory=list,
        max_length=5,
        description="Where the method is described: an article, a video, a podcast "
        "episode. Linked, never copied.",
    )
    contexts: list[Context] = Field(
        default_factory=list, description="Where you have seen it work."
    )
    existing_method_id: str | None = Field(
        default=None,
        description="Set when this is a new situation for a method already in the "
        "catalog rather than a new method.",
    )
    extracted_from: Kind | None = Field(
        default=None,
        description="The kind of file the person started from via "
        "/proposals/extract, if any. Kept so the reviewer knows the fields began "
        "as a machine draft.",
    )

    @model_validator(mode="after")
    def _needs_a_source(self) -> ProposalRequest:
        if not (self.sources and self.sources.strip()) and not self.links:
            raise ValueError("give at least one source or link — a method needs provenance")
        return self


class ProposalResponse(BaseModel):
    recorded: Literal[True]
    proposal_id: str = Field(description="ULID of the stored proposal.")
    similar: list[MethodMatch] = Field(
        description="What the catalog search returns for `problem`. If one of these "
        "already covers it, the better proposal is a new situation for that method."
    )
    similar_error: str | None = Field(
        default=None,
        description="Set when the duplicate check could not run. The proposal is "
        "stored regardless — an index problem must not lose it.",
    )
    issue_url: str | None = Field(
        default=None,
        description="The GitHub issue form, prefilled. null when no repository is "
        "configured (METHODOS_ISSUE_REPO) or the text is too long for a URL.",
    )
    issue_url_omitted: list[str] = Field(
        default_factory=list,
        description="Fields left out of `issue_url` to stay under GitHub's URL limit.",
    )


class ExtractResponse(BaseModel):
    """The text of an uploaded file, and a draft proposal made from it.

    Nothing in here is stored. The file is deleted before this response is
    sent; the text and the draft exist only in the browser until the person
    submits the form, and then only the fields they kept.
    """

    kind: Kind
    characters: int = Field(description="Length of the full extracted text.")
    text: str = Field(description="The extracted text, cut to the first 20,000 characters.")
    text_truncated: bool
    duration_seconds: float | None = Field(
        default=None, description="Length of the recording, for audio and video."
    )
    language: str | None = Field(default=None, description="Spoken language Whisper detected.")
    transcriber: str | None = None
    draft: ProposalDraft | None = Field(
        default=None, description="null when `draft` was false or the LLM step failed."
    )
    draft_model: str | None = None
    draft_error: str | None = Field(
        default=None,
        description="Set when the draft step failed. The text above is unaffected — "
        "the person can still fill the form from it.",
    )


class MethodStatsEntry(BaseModel):
    method_id: str
    recommendation_count: int
    rating_count: int
    avg_rating: float | None = Field(
        description="null until the method has been rated at least once."
    )


class StatsResponse(BaseModel):
    entries: list[MethodStatsEntry]


app = FastAPI(
    title="Methodos AI",
    version=__version__,
    summary="Recommend a management method for a problem stated in natural language.",
    description=__doc__,
)


def _check_category(category: str | None) -> None:
    if category is not None and category not in mcp_tools.valid_categories():
        raise HTTPException(
            status_code=422,
            detail=f"unknown category {category!r}. "
            f"Valid: {', '.join(mcp_tools.valid_categories())}",
        )


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def console() -> HTMLResponse:
    """A single self-contained page for trying queries and rating the results."""
    return HTMLResponse(CONSOLE_HTML.read_text(encoding="utf-8"))


@app.get("/health", response_model=HealthResponse)
def health(providers: ProvidersDep) -> HealthResponse:
    """Config and index state. Never calls the LLM — see LLMCheckResponse."""
    s = providers.settings
    indexed: int | None = None
    index_error: str | None = None
    try:
        indexed = collection_size(s.chroma_path, providers.embedding)
    except (StaleIndexError, EmbeddingError) as e:
        index_error = str(e)
    except Exception as e:
        # Broad on purpose, like get_providers: this endpoint exists to say why
        # the service is unwell, and a 500 says nothing. Anything the index
        # layer throws that the two errors above do not cover is still an
        # unusable index, and belongs in the report rather than in a traceback.
        index_error = f"{type(e).__name__}: {e}"

    return HealthResponse(
        status="ok" if index_error is None else "degraded",
        version=__version__,
        model=s.model,
        embedding=providers.embedding.name,
        reranker=providers.reranker.name if providers.reranker else None,
        methods_dir=str(methods_dir()),
        chroma_path=str(s.chroma_path),
        indexed_methods=indexed,
        index_error=index_error,
        transcriber=providers.transcriber.name if providers.transcriber else None,
        upload_max_mb=s.upload_max_mb,
        media_max_minutes=s.media_max_minutes,
        upload_suffixes=list(
            ACCEPTED_SUFFIXES if providers.transcriber else DOCUMENT_SUFFIXES.keys()
        ),
    )


@app.post("/llm/check", response_model=LLMCheckResponse)
def llm_check(providers: ProvidersDep) -> LLMCheckResponse:
    """One real completion against the configured model. 502 with the provider's error.

    Deliberately the smallest call that proves the whole chain — credentials,
    model string, network — rather than a mocked reachability probe.
    """
    started = time.monotonic()
    try:
        reply = providers.llm.complete(
            "You are a connectivity check.",
            "Reply with the single word: ok",
            max_tokens=16,
        )
    except LLMError as e:
        raise HTTPException(
            status_code=502,
            detail=f"LLM provider '{providers.settings.model}' failed: {e}",
        ) from e
    return LLMCheckResponse(
        ok=True,
        model=providers.settings.model,
        latency_ms=int((time.monotonic() - started) * 1000),
        reply=reply.strip(),
    )


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest, providers: ProvidersDep) -> QueryResponse:
    """Recommend methods for a problem, and explain the ranking."""
    from methodos.feedback import log_recommendation

    _check_category(req.category)

    reranker = providers.reranker
    if req.rerank is False:
        reranker = None
    elif req.rerank is True and reranker is None:
        raise HTTPException(
            status_code=503,
            detail="rerank=true was requested but the cross-encoder is unavailable: "
            'install the `local` extra (pip install -e ".[local]"), or omit rerank.',
        )

    s = providers.settings
    try:
        result, candidates = mcp_tools.recommend_with_candidates(
            problem=req.problem,
            embedding=providers.embedding,
            chroma_path=s.chroma_path,
            top_k=req.top_k,
            category=req.category,
            reranker=reranker,
            overfetch_factor=s.overfetch_factor,
        )
    except StaleIndexError as e:
        raise HTTPException(status_code=503, detail=f"the search index is unusable: {e}") from e
    except EmbeddingError as e:
        raise HTTPException(status_code=503, detail=f"embedding provider failed: {e}") from e
    except RerankError as e:
        raise HTTPException(
            status_code=503,
            detail=f"reranker failed: {e} — retry with rerank=false to rank by embedding only.",
        ) from e

    query_id = log_recommendation(
        query=req.problem,
        method_ids=[c.id for c in candidates],
        model=s.model,
        path=s.feedback_path,
    )

    explanation: str | None = None
    explanation_error: str | None = None
    if req.explain and candidates:
        try:
            explanation = explain(query=req.problem, candidates=candidates, llm=providers.llm)
        except LLMError as e:
            # Not a 502: the matches above are a complete, correct answer to the
            # retrieval question, and hiding them behind an LLM outage would
            # make a working ranking look broken. See the module docstring.
            explanation_error = str(e)

    return QueryResponse(
        **result.model_dump(),
        query_id=query_id,
        explanation=explanation,
        explanation_model=s.model if req.explain else None,
        explanation_error=explanation_error,
    )


@app.get("/methods", response_model=CatalogResult)
def list_methods(category: str | None = None, context: str | None = None) -> CatalogResult:
    """The complete catalog — no search, no ranking, no truncation."""
    _check_category(category)
    if context is not None and context not in mcp_tools.valid_contexts():
        raise HTTPException(
            status_code=422,
            detail=f"unknown context {context!r}. Valid: {', '.join(mcp_tools.valid_contexts())}",
        )
    return mcp_tools.list_methods(methods_dir=methods_dir(), category=category, context=context)


@app.get("/methods/{method_id}", response_model=MethodDetail)
def get_method(
    method_id: Annotated[str, PathParam(description="Exact method id, e.g. 'SWOT'.")],
) -> MethodDetail:
    """One method's full record plus its Markdown companion."""
    try:
        return mcp_tools.get_method(method_id=method_id, methods_dir=methods_dir())
    except MethodNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@app.post("/feedback", response_model=FeedbackResponse)
def feedback(req: FeedbackRequest, providers: ProvidersDep) -> FeedbackResponse:
    """Record an outcome rating.

    The id is checked against the catalog first. The CLI does not check, because
    a typo there is visible in the shell the moment `stats` is run; over HTTP the
    writer is a browser and nobody would see a rating quietly accumulating
    against a method that does not exist.
    """
    from methodos.feedback import log_rating

    known = {m.id for m in mcp_tools.load_catalog(methods_dir())}
    if req.method_id not in known:
        raise HTTPException(
            status_code=404,
            detail=f"no method with id {req.method_id!r}. Valid ids: {', '.join(sorted(known))}",
        )

    log_rating(
        method_id=req.method_id,
        rating=req.rating,
        note=req.note,
        query_id=req.query_id,
        path=providers.settings.feedback_path,
    )
    return FeedbackResponse(recorded=True, method_id=req.method_id, rating=req.rating)


@app.post("/proposals", response_model=ProposalResponse)
def propose(req: ProposalRequest, providers: ProvidersDep) -> ProposalResponse:
    """Submit a method the catalog is missing. Nothing is published by this call.

    The proposal goes to the server's inbox (`proposals.jsonl`) and, when a
    repository is configured, comes back as a prefilled GitHub issue link the
    person can submit under their own account. Either way it reaches the
    catalog only through the `method-author` agent and the owner's review.

    No LLM call: the duplicate check is the same retrieval `/query` runs.
    """
    from methodos.proposals import issue_url, log_proposal

    if req.existing_method_id is not None:
        known = {m.id for m in mcp_tools.load_catalog(methods_dir())}
        if req.existing_method_id not in known:
            raise HTTPException(
                status_code=422,
                detail=f"no method with id {req.existing_method_id!r}. "
                f"Valid ids: {', '.join(sorted(known))}",
            )

    s = providers.settings
    similar: list[MethodMatch] = []
    similar_error: str | None = None
    try:
        result = mcp_tools.recommend_methods(
            problem=req.problem,
            embedding=providers.embedding,
            chroma_path=s.chroma_path,
            top_k=3,
            reranker=providers.reranker,
            overfetch_factor=s.overfetch_factor,
        )
        similar = result.matches
    except (StaleIndexError, EmbeddingError, RerankError) as e:
        similar_error = str(e)

    proposal = log_proposal(
        name=req.name.strip(),
        problem=req.problem.strip(),
        description=req.description.strip() if req.description else None,
        sources=req.sources.strip() if req.sources else None,
        links=[str(u) for u in req.links],
        contexts=req.contexts,
        existing_method_id=req.existing_method_id,
        similar_method_ids=[m.id for m in similar],
        path=s.proposals_path,
        extracted_from=req.extracted_from,
    )
    link = issue_url(proposal, s.issue_repo) if s.issue_repo else None

    return ProposalResponse(
        recorded=True,
        proposal_id=proposal.proposal_id,
        similar=similar,
        similar_error=similar_error,
        issue_url=link.url if link else None,
        issue_url_omitted=link.omitted if link else [],
    )


TEXT_PREVIEW_CHARS = 20_000
MULTIPART_OVERHEAD = 64 * 1024
"""Headroom for the multipart envelope and the small form fields, on top of the
file itself, when judging the Content-Length before the body is read."""

_EXTRACT_FORM = {
    "requestBody": {
        "required": True,
        "content": {
            "multipart/form-data": {
                "schema": {
                    "type": "object",
                    "required": ["file"],
                    "properties": {
                        "file": {
                            "type": "string",
                            "format": "binary",
                            "description": f"One of: {', '.join(ACCEPTED_SUFFIXES)}",
                        },
                        "draft": {
                            "type": "boolean",
                            "default": True,
                            "description": "Ask the LLM for a draft proposal. Sends the "
                            "extracted text to the configured model provider.",
                        },
                        "language": {
                            "type": "string",
                            "enum": ["de", "en"],
                            "default": "en",
                            "description": "Language to write the draft in.",
                        },
                    },
                }
            }
        },
    }
}


def _read_upload(
    path: Path, kind: Kind, providers: Providers
) -> tuple[str, float | None, str | None]:
    """Text, duration and detected language of a file on disk. Blocking: run in a thread."""
    from methodos.uploads import NoTextError, extract_document_text, normalise

    if kind in ("audio", "video"):
        if providers.transcriber is None:
            raise HTTPException(
                status_code=503,
                detail="audio and video cannot be read on this server: the `transcribe` "
                'extra is not installed (pip install -e ".[transcribe]"). PDF, Word and '
                "text files still work.",
            )
        transcript = providers.transcriber.transcribe(
            path, max_seconds=providers.settings.media_max_minutes * 60
        )
        text = normalise(transcript.text)
        if not text:
            raise NoTextError("no speech was recognised in the recording")
        return text, transcript.duration_seconds, transcript.language
    return extract_document_text(path, kind), None, None


@app.post(
    "/proposals/extract",
    response_model=ExtractResponse,
    openapi_extra=_EXTRACT_FORM,
    responses={
        411: {"description": "No Content-Length header."},
        413: {"description": "Larger than METHODOS_UPLOAD_MAX_MB."},
        415: {"description": "Not a supported file type."},
        422: {"description": "No text in the file, or the recording is too long."},
        503: {"description": "Audio or video, and no transcriber is installed."},
    },
)
async def extract_proposal(request: Request, providers: ProvidersDep) -> ExtractResponse:
    """Read a file and draft a proposal from it. Stores nothing, publishes nothing.

    PDF, Word (.docx), text and Markdown are read in-process. Audio and video
    are transcribed **on this server** (faster-whisper); the recording never
    leaves it. With `draft` on (the default) the extracted text — not the file
    — goes to the configured LLM, which returns a draft to prefill the
    proposal form. The person edits it and submits through `/proposals`.

    The file is held in a temporary directory for the duration of the request
    and deleted before the response is sent.
    """
    from methodos.proposals import DraftError, draft_from_text
    from methodos.uploads import UnsupportedFileError, UploadError, detect_kind

    s = providers.settings
    limit = s.upload_max_mb * 1024 * 1024
    # Checked before the body is read: the multipart parser would otherwise
    # spool the whole upload to disk first. The server enforces that the body
    # matches Content-Length, so the header can be trusted for this.
    length = request.headers.get("content-length")
    if length is None or not length.isdigit():
        raise HTTPException(status_code=411, detail="Content-Length is required")
    if int(length) > limit + MULTIPART_OVERHEAD:
        raise HTTPException(status_code=413, detail=f"the file is larger than {s.upload_max_mb} MB")

    form = await request.form(max_files=1, max_fields=4)
    try:
        upload = form.get("file")
        if not isinstance(upload, UploadFile) or not upload.filename:
            raise HTTPException(status_code=422, detail="no file in the `file` field")
        if upload.size is not None and upload.size > limit:
            raise HTTPException(
                status_code=413, detail=f"the file is larger than {s.upload_max_mb} MB"
            )
        want_draft = str(form.get("draft", "true")).lower() not in ("false", "0", "off", "")
        language = str(form.get("language", "en"))

        head = await upload.read(8)
        await upload.seek(0)
        try:
            kind = detect_kind(upload.filename, head)
        except UnsupportedFileError as e:
            raise HTTPException(status_code=415, detail=str(e)) from e

        with tempfile.TemporaryDirectory(prefix="methodos-upload-") as tmp:
            # Only the extension survives into the temporary name: a file name
            # can carry a person's name, and nothing here needs it.
            path = Path(tmp) / f"upload{Path(upload.filename).suffix.lower()}"
            with path.open("wb") as out:
                while chunk := await upload.read(1024 * 1024):
                    out.write(chunk)
            try:
                text, duration, spoken = await run_in_threadpool(
                    _read_upload, path, kind, providers
                )
            except TranscriberUnavailableError as e:
                raise HTTPException(status_code=503, detail=str(e)) from e
            except (UploadError, TranscriptionError) as e:
                # Covers MediaTooLongError: the file is the problem, not the server.
                raise HTTPException(status_code=422, detail=str(e)) from e
    finally:
        await form.close()

    draft: ProposalDraft | None = None
    draft_error: str | None = None
    if want_draft:
        try:
            draft = await run_in_threadpool(
                draft_from_text, text, llm=providers.llm, language=language
            )
        except (LLMError, DraftError) as e:
            # Not a failure of the request, for the same reason as in /query:
            # the text is the reliable half, and the form can be filled from it.
            draft_error = str(e)

    return ExtractResponse(
        kind=kind,
        characters=len(text),
        text=text[:TEXT_PREVIEW_CHARS],
        text_truncated=len(text) > TEXT_PREVIEW_CHARS,
        duration_seconds=duration,
        language=spoken,
        transcriber=providers.transcriber.name
        if kind in ("audio", "video") and providers.transcriber
        else None,
        draft=draft,
        draft_model=s.model if draft is not None else None,
        draft_error=draft_error,
    )


@app.get("/stats", response_model=StatsResponse)
def stats(providers: ProvidersDep) -> StatsResponse:
    """Aggregated ratings, same JSONL the CLI's `stats` reads."""
    from methodos.feedback import stats as read_stats

    return StatsResponse(
        entries=[
            MethodStatsEntry(
                method_id=mid,
                recommendation_count=st.recommendation_count,
                rating_count=st.rating_count,
                avg_rating=st.avg_rating if st.rating_count else None,
            )
            for mid, st in sorted(read_stats(providers.settings.feedback_path).items())
        ]
    )
