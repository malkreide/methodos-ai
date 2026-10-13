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

and one judgement the ranking cannot make alone:

  * a problem that names a place and a feeling but no goal ("unser Sommerfest
    ist jedes Jahr ein Durcheinander") -> `clarify` when the ranking is unsure

The weak-match case is the important one. `retrieve()` answers every query with its
nearest neighbours, so "how do I fix my bicycle chain" comes back with a
method at similarity 0.146 and looks exactly like a real hit.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from methodos.models import Asset, Category, Context, Format, GroupSize, Method
from methodos.providers.base import EmbeddingProvider, RerankProvider
from methodos.search import Candidate, collection_size, retrieve

WEAK_MATCH_SIMILARITY = 0.33
"""Below this cosine similarity, `recommend_methods` attaches `guidance`.

Measured against the shipped catalog (23 methods, re-checked at 27, 39, 43,
47, 51, 55, 59, 63, 67, 71, 79 and 87) with the default multilingual embedding, not guessed. Every
one of the 174 pinned integration probes (87 English, 87 German) reaches at least
0.380 with its best match; questions the catalog genuinely does not cover top
out at 0.329 ("wie flicke ich meine Velokette", 0.265 until the Eisenhower
Matrix gained a problem-voice use case, "I have far more on my plate…", in the
71-method catalog), with "Rezept für Zürcher Geschnetzeltes" at 0.291 and "how
do I fix my bicycle chain" at 0.224. 0.33 sits in the empty band between those
two populations, now only 0.001 above its upper edge.
tests/test_integration.py pins both sides.

The band is narrower than it was under the English-only model (0.127-0.321),
because a multilingual model maps more of everyday language near *something*.
Re-measure after changing the embedding model or adding many methods.

It is a hint threshold, never a filter: results below it are still returned,
because a weak match plus a stated caveat is more useful than an empty list
that a model will fill in from memory.
"""

UNSURE_TOP_SCORE = 0.0
UNSURE_MARGIN = 1.0
"""`clarify` is set when the cross-encoder's best score is below UNSURE_TOP_SCORE
and leads the runner-up by less than UNSURE_MARGIN.

Measured 2026-10-12 on the 79-method catalog against the 55 problems in
scripts/search_queries.json and search_queries_holdout.json (problems as people
type them, with their acceptable methods). The rule catches 12 of the 15 whose
first result is wrong, at the price of 8 of the 40 whose first result is right.
Of the 158 pinned integration probes it asks on 5, all of them already right.
Neither score alone separates them: a wrong first place at +0.6 exists, and a
right one at -2.

What a person does with the question was measured too. Adding the goal they
would name ("Wir wollen herausfinden, woran es liegt.") to the problem:

                          first place right     a right one in the top 3
  wrong before (10)         0 -> 5                  4 -> 8
  right before  (8)         8 -> 4                  8 -> 7

so a goal moves the right method up about as often as it pushes a right one
down. The console therefore shows the refined results *and* keeps the earlier
first place: with it, all 8 stay visible and 8 of the 10 gain a right method.
Two of the 20 flagged problems had no goal on offer that fits. Re-measure with
the rule and the goals after changing the reranker or the catalog's wording.
"""

RankingBasis = Literal["cross-encoder", "embedding-similarity"]

_WEAK_MATCH_GUIDANCE = (
    "The best match scored {top:.3f}, below the {floor} the catalog's own probes "
    "reach. Rephrase the problem in terms of the decision or symptom rather than "
    "the domain, or call `list_methods` to see the {total} methods that exist. "
    "If none of them fit, say so — the catalog is a fixed set of {total} methods "
    "and does not contain everything. Do not name a method that is not in it."
)


_CLARIFY = (
    "The ranking is unsure: the best match scored {top:+.2f} and leads the next by "
    "{margin:.2f}. The problem likely names a situation but not what the user wants "
    "from it. Ask the user what they want to achieve — understand a cause, learn "
    "from something that keeps going wrong, decide between options, set "
    "priorities, involve the people concerned, generate ideas, think through "
    "consequences beforehand, show whether something works, try it small first, "
    "resolve a conflict — and call `recommend_methods` again with that goal added "
    "to the problem in one sentence. Keep the current first match in view: a goal "
    "added to a problem can push a right answer down as well as up."
)


class MethodMatch(BaseModel):
    """One retrieved method. Mirrors `search.Candidate` as a serialisable model."""

    id: str
    name: str
    category: str
    complexity_score: int = Field(ge=1, le=5)
    use_case: str
    matched_use_case: str | None = Field(
        default=None,
        description="The further use case of this method the problem matched, "
        "when it was not `use_case` itself. Scores refer to this text.",
    )
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
    clarify: str | None = Field(
        default=None,
        description="Set when the cross-encoder could not separate the top matches "
        "and none of them scored well: ask the user what they want to achieve "
        "before relying on the order. Never set together with `guidance`, and "
        "only when ranking_basis is 'cross-encoder' and at least two methods "
        "were returned.",
    )


class CatalogEntry(BaseModel):
    id: str
    name: str
    category: str
    complexity_score: int
    duration_min: int
    duration_max: int
    contexts: list[Context] = Field(
        default_factory=list, description="Empty means not yet classified, not 'none'."
    )
    formats: list[Format] = Field(default_factory=list)
    language: str


class CatalogResult(BaseModel):
    returned: int
    total: int = Field(
        description="Methods in the catalog overall, ignoring `category` and `context`."
    )
    category: str | None = None
    context: str | None = None
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
    use_cases: list[str] = Field(default_factory=list)
    contexts: list[Context] = Field(default_factory=list)
    formats: list[Format] = Field(default_factory=list)
    group_size: GroupSize | None = None
    audience: list[str] = Field(default_factory=list)
    language: str = "en"
    assets: list[Asset] = Field(
        default_factory=list,
        description="Supporting material. `path` is relative to methods/assets/<id>/; "
        "`access: premium` assets are licensed separately.",
    )
    owner: str | None = None
    last_reviewed: str | None = Field(default=None, description="ISO date, or null.")
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
        matched_use_case=c.matched_use_case,
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


def recommend_with_candidates(
    *,
    problem: str,
    embedding: EmbeddingProvider,
    chroma_path: Path,
    top_k: int = 5,
    category: str | None = None,
    reranker: RerankProvider | None = None,
    overfetch_factor: int = 3,
) -> tuple[RecommendResult, list[Candidate]]:
    """`recommend_methods`, plus the raw candidates it was built from.

    The HTTP API needs both: the result for its payload, and the candidates
    again to feed `search.explain`, which takes Candidates rather than the
    serialisable MethodMatch. Returning the pair keeps the guidance and
    ranking_basis rules below as the single implementation — the alternative
    was a second retrieval in the API that would drift from this one.
    """
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

    clarify = None
    if guidance is None and len(candidates) >= 2:
        top, second = candidates[0].rerank_score, candidates[1].rerank_score
        # A weak match is outside the catalog, and asking for the goal will not
        # bring it in; `guidance` already says what to do there.
        if (
            top is not None
            and second is not None
            and top < UNSURE_TOP_SCORE
            and top - second < UNSURE_MARGIN
        ):
            clarify = _CLARIFY.format(top=top, margin=top - second)

    result = RecommendResult(
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
        clarify=clarify,
    )
    return result, candidates


def recommend_methods(
    *,
    problem: str,
    embedding: EmbeddingProvider,
    chroma_path: Path,
    top_k: int = 5,
    category: str | None = None,
    reranker: RerankProvider | None = None,
    overfetch_factor: int = 3,
) -> RecommendResult:
    """Semantic search over the indexed catalog, with the narrowings reported."""
    result, _ = recommend_with_candidates(
        problem=problem,
        embedding=embedding,
        chroma_path=chroma_path,
        top_k=top_k,
        category=category,
        reranker=reranker,
        overfetch_factor=overfetch_factor,
    )
    return result


def list_methods(
    *, methods_dir: Path, category: str | None = None, context: str | None = None
) -> CatalogResult:
    """The whole catalog. No search, no ranking, no truncation.

    `context` keeps only methods that declare it. A method without any
    `contexts` is unclassified rather than context-free, so it is excluded by
    the filter — the payload's `total` still counts it.
    """
    catalog = load_catalog(methods_dir)
    selected = [
        m
        for m in catalog
        if (category is None or m.category.value == category)
        and (context is None or context in m.contexts)
    ]
    return CatalogResult(
        returned=len(selected),
        total=len(catalog),
        category=category,
        context=context,
        categories=sorted({m.category.value for m in catalog}),
        methods=[
            CatalogEntry(
                id=m.id,
                name=m.name,
                category=m.category.value,
                complexity_score=m.complexity_score,
                duration_min=m.estimated_duration.min_minutes,
                duration_max=m.estimated_duration.max_minutes,
                contexts=m.contexts,
                formats=m.formats,
                language=m.language,
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
        use_cases=found.use_cases,
        contexts=found.contexts,
        formats=found.formats,
        group_size=found.group_size,
        audience=found.audience,
        language=found.language,
        assets=found.assets,
        owner=found.owner,
        last_reviewed=found.last_reviewed.isoformat() if found.last_reviewed else None,
        documentation=doc.read_text(encoding="utf-8"),
    )


def valid_categories() -> list[str]:
    return sorted(c.value for c in Category)


def valid_contexts() -> list[str]:
    return sorted(c.value for c in Context)
