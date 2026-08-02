"""Tool logic behind the MCP server, with no `mcp` dependency.

Split from `mcp_server.py` on purpose: nothing here imports the `mcp` package,
so the contract is verifiable wherever the repo is checked out, whether or not
the SDK is installed. CI does install the extra — mypy type-checks
`mcp_server.py` and cannot see the SDK otherwise — but this repo has already
been bitten once by a path CI never installed (the OpenAI embedding provider,
unverified until it was tested explicitly), and the contract below is the last
thing that should go dark if the install line changes again. `mcp_server.py`
stays thin enough that its correctness is visible by reading it.

The result models are the actual deliverable. A retrieval tool talking to a
model has a failure mode a CLI does not: the caller cannot see what it was not
shown, so anything the server silently narrows has to be stated in the payload.
Three such narrowings exist here, and each has a field:

  * `top_k` cuts the catalog down     -> `returned` / `total_in_scope` / `total_indexed`
  * the reranker may be absent        -> `ranking_basis`
  * vector search never returns empty -> `guidance` when the best match is weak

That last one is the important one. `retrieve()` answers every query with its
nearest neighbours, so "how do I fix my bicycle chain" comes back with Five
Whys at similarity 0.106 and looks exactly like a real hit.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from methodos.models import Category, Method
from methodos.providers.base import EmbeddingProvider, RerankProvider
from methodos.search import Candidate, collection_size, retrieve

WEAK_MATCH_SIMILARITY = 0.25
"""Below this cosine similarity, `recommend_methods` attaches `guidance`.

Measured against the shipped 23-method catalog, not guessed. The weakest of the
23 pinned integration probes tops out at 0.321 (Value Stream Mapping); queries
the catalog genuinely does not cover land far lower — 0.106 for "how do I fix
my bicycle chain", 0.048 for "what is the capital of France". 0.25 sits in the
empty band between those two populations.

It is a hint threshold, never a filter: results below it are still returned,
because a weak match plus a stated caveat is more useful than an empty list
that a model will fill in from memory.
"""

RankingBasis = Literal["cross-encoder", "embedding-similarity"]

_WEAK_MATCH_GUIDANCE = (
    "The best match scored {top:.3f}, below the {floor} the catalog's own probes "
    "reach. Rephrase the problem in terms of the decision or symptom rather than "
    "the domain, or call `list_methods` to see the {total} methods that exist. "
    "If none of them fit, say so — the catalog is a fixed set of {total} methods "
    "and does not contain everything. Do not name a method that is not in it."
)


class MethodMatch(BaseModel):
    """One retrieved method. Mirrors `search.Candidate` as a serialisable model."""

    id: str
    name: str
    category: str
    complexity_score: int = Field(ge=1, le=5)
    use_case: str
    strengths: list[str]
    weaknesses: list[str]
    duration_min: int
    duration_max: int
    similarity: float = Field(
        description="Cosine similarity from the embedding, 0-1. Not the sort key "
        "when ranking_basis is 'cross-encoder'."
    )
    rerank_score: float | None = Field(
        default=None,
        description="Cross-encoder logit when a reranker ran, else null. A "
        "different scale from similarity; the two are not comparable.",
    )


class RecommendResult(BaseModel):
    problem: str
    returned: int = Field(description="How many methods are in `matches`.")
    total_in_scope: int = Field(
        description="Methods the search could have drawn from, after `category`."
    )
    total_indexed: int = Field(description="Methods in the whole index, ignoring `category`.")
    category: str | None = Field(default=None, description="Echo of the filter that was applied.")
    ranking_basis: RankingBasis = Field(
        description="'cross-encoder' means `matches` is ordered by a reranker and "
        "similarity is NOT the sort key — a lower-similarity method can rank "
        "above a higher one, deliberately. 'embedding-similarity' means the "
        "reranker was unavailable and the order is plain cosine similarity."
    )
    matches: list[MethodMatch]
    guidance: str | None = Field(
        default=None,
        description="Set when the best match is weak. Names a next step; absence "
        "of it is not a quality guarantee.",
    )


class CatalogEntry(BaseModel):
    id: str
    name: str
    category: str
    complexity_score: int
    duration_min: int
    duration_max: int


class CatalogResult(BaseModel):
    returned: int
    total: int = Field(description="Methods in the catalog overall, ignoring `category`.")
    category: str | None = None
    categories: list[str] = Field(description="Every category present in the catalog.")
    methods: list[CatalogEntry]


class MethodDetail(BaseModel):
    id: str
    name: str
    category: str
    use_case: str
    strengths: list[str]
    weaknesses: list[str]
    complexity_score: int
    duration_min: int
    duration_max: int
    references: list[str]
    documentation: str = Field(description="Full Markdown companion document.")


class MethodNotFoundError(LookupError):
    """Raised with the valid ids listed, so the caller can retry without guessing."""


def _to_match(c: Candidate) -> MethodMatch:
    return MethodMatch(
        id=c.id,
        name=c.name,
        category=c.category,
        complexity_score=c.complexity_score,
        use_case=c.use_case,
        strengths=c.strengths,
        weaknesses=c.weaknesses,
        duration_min=c.duration_min,
        duration_max=c.duration_max,
        similarity=c.similarity,
        rerank_score=c.rerank_score,
    )


def load_catalog(methods_dir: Path) -> list[Method]:
    """Every method JSON, id-sorted. The catalog on disk, not the index."""
    import json

    return sorted(
        (
            Method.model_validate(json.loads(f.read_text(encoding="utf-8")))
            for f in methods_dir.glob("*.json")
        ),
        key=lambda m: m.id,
    )


def recommend_methods(
    *,
    problem: str,
    embedding: EmbeddingProvider,
    chroma_path: Path,
    top_k: int = 5,
    category: str | None = None,
    reranker: RerankProvider | None = None,
    overfetch_factor: int = 2,
) -> RecommendResult:
    """Semantic search over the indexed catalog, with the narrowings reported."""
    where = {"category": category} if category else None
    candidates = retrieve(
        query=problem,
        embedding=embedding,
        chroma_path=chroma_path,
        top_k=top_k,
        reranker=reranker,
        overfetch_factor=overfetch_factor,
        where=where,
    )
    total_indexed = collection_size(chroma_path, embedding)
    total_in_scope = (
        total_indexed if where is None else collection_size(chroma_path, embedding, where=where)
    )

    guidance = None
    if not candidates:
        guidance = (
            f"No method matched. The index holds {total_indexed} methods"
            + (f", none of them in category '{category}'. " if category else ". ")
            + "Call `list_methods` to see what exists, and do not name a method "
            "that is not in the catalog."
        )
    elif candidates[0].similarity < WEAK_MATCH_SIMILARITY:
        guidance = _WEAK_MATCH_GUIDANCE.format(
            top=candidates[0].similarity,
            floor=WEAK_MATCH_SIMILARITY,
            total=total_indexed,
        )

    return RecommendResult(
        problem=problem,
        returned=len(candidates),
        total_in_scope=total_in_scope,
        total_indexed=total_indexed,
        category=category,
        # Read off the data rather than off `reranker is not None`: make_reranker
        # degrades to None when sentence-transformers is missing, and the caller
        # must learn that the order changed meaning.
        ranking_basis=(
            "cross-encoder"
            if candidates and candidates[0].rerank_score is not None
            else "embedding-similarity"
        ),
        matches=[_to_match(c) for c in candidates],
        guidance=guidance,
    )


def list_methods(*, methods_dir: Path, category: str | None = None) -> CatalogResult:
    """The whole catalog. No search, no ranking, no truncation."""
    catalog = load_catalog(methods_dir)
    selected = [m for m in catalog if category is None or m.category.value == category]
    return CatalogResult(
        returned=len(selected),
        total=len(catalog),
        category=category,
        categories=sorted({m.category.value for m in catalog}),
        methods=[
            CatalogEntry(
                id=m.id,
                name=m.name,
                category=m.category.value,
                complexity_score=m.complexity_score,
                duration_min=m.estimated_duration.min_minutes,
                duration_max=m.estimated_duration.max_minutes,
            )
            for m in selected
        ],
    )


def get_method(*, method_id: str, methods_dir: Path) -> MethodDetail:
    """Full record plus the Markdown companion.

    Raises MethodNotFoundError listing every valid id — a model that guessed an
    id can correct itself from the error instead of inventing a second guess.
    """
    catalog = load_catalog(methods_dir)
    found = next((m for m in catalog if m.id == method_id), None)
    if found is None:
        raise MethodNotFoundError(
            f"no method with id {method_id!r}. Valid ids: {', '.join(m.id for m in catalog)}"
        )

    doc = methods_dir.parent / found.doc_path
    if not doc.is_file():
        doc = methods_dir / f"{found.id}.md"
    if not doc.is_file():
        raise MethodNotFoundError(
            f"method {method_id!r} exists but its documentation is missing at "
            f"{found.doc_path} — the index and the catalog on disk may be out of sync."
        )

    return MethodDetail(
        id=found.id,
        name=found.name,
        category=found.category.value,
        use_case=found.use_case,
        strengths=found.strengths,
        weaknesses=found.weaknesses,
        complexity_score=found.complexity_score,
        duration_min=found.estimated_duration.min_minutes,
        duration_max=found.estimated_duration.max_minutes,
        references=found.references,
        documentation=doc.read_text(encoding="utf-8"),
    )


def valid_categories() -> list[str]:
    return sorted(c.value for c in Category)
