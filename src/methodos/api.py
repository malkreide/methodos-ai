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
import time
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, HTTPException
from fastapi import Path as PathParam
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, ValidationError

from methodos import __version__, mcp_tools
from methodos.config import Settings
from methodos.mcp_tools import CatalogResult, MethodDetail, MethodNotFoundError, RecommendResult
from methodos.providers import (
    EmbeddingProvider,
    LLMProvider,
    RerankProvider,
    make_embedding,
    make_llm,
    make_reranker,
)
from methodos.providers.base import EmbeddingError, LLMError, RerankError
from methodos.search import StaleIndexError, collection_size, explain

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
    a fresh LocalEmbedding whose `_model` is None, re-loading ~80MB of weights
    on every call. One instance per process keeps the loaded model resident.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.embedding: EmbeddingProvider = make_embedding(settings)
        self.reranker: RerankProvider | None = make_reranker(settings)
        self.llm: LLMProvider = make_llm(settings)


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
        "symptom, not a method — the search matches on problem descriptions.",
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
    note: str | None = None
    query_id: str | None = Field(
        default=None, description="The query_id from /query, to tie the rating to a query."
    )


class FeedbackResponse(BaseModel):
    recorded: Literal[True]
    method_id: str
    rating: int


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
def list_methods(category: str | None = None) -> CatalogResult:
    """The complete catalog — no search, no ranking, no truncation."""
    _check_category(category)
    return mcp_tools.list_methods(methods_dir=methods_dir(), category=category)


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
