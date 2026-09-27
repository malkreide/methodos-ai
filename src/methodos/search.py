"""Retrieval + LLM explanation. See ingest.py for the similarity-math comment block."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from methodos.prompts.loader import render_explain_prompt, split_system_user
from methodos.providers.base import (
    EmbeddingProvider,
    LLMProvider,
    RerankError,
    RerankProvider,
)


class StaleIndexError(Exception):
    """The Chroma collection's embedding provider doesn't match the current one."""


@dataclass(frozen=True)
class Candidate:
    id: str
    name: str
    category: str
    complexity_score: int
    use_case: str
    strengths: list[str]
    weaknesses: list[str]
    duration_min: int
    duration_max: int
    doc_path: str
    similarity: float
    matched_use_case: str | None = None
    """The further use case the query matched, or None if it was `use_case`.

    Similarity (and the reranker's score) are computed against this text when
    it is set, so it is the evidence for the ranking and worth showing.
    """
    rerank_score: float | None = None
    """Cross-encoder score when a reranker ran, else None.

    Kept separate from `similarity` on purpose: the two are different scales
    (cosine vs. model logits) and overwriting one with the other would make the
    rendered numbers silently incomparable between runs.
    """

    def to_render_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "similarity": self.similarity,
            "rerank_score": self.rerank_score,
            "complexity_score": self.complexity_score,
            "use_case": self.use_case,
            "matched_use_case": self.matched_use_case,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "duration_min": self.duration_min,
            "duration_max": self.duration_max,
        }


@dataclass(frozen=True)
class SearchResult:
    candidates: list[Candidate]
    explanation: str | None


def _rehydrate(
    chroma_id: str, document: str, metadata: dict[str, Any], distance: float
) -> Candidate:
    """Reconstruct a Candidate from Chroma's flat metadata.

    A method with several use cases has several Chroma entries (`Id`, `Id#1`,
    …); `method_id` and `use_case` in the metadata name the method and its
    canonical text. Indexes built before those keys existed fall back to the
    Chroma id and the document, which is what they held.
    """
    similarity = 1.0 - distance
    use_case = metadata.get("use_case", document)
    return Candidate(
        id=metadata.get("method_id", chroma_id),
        name=metadata["name"],
        category=metadata["category"],
        complexity_score=int(metadata["complexity_score"]),
        use_case=use_case,
        matched_use_case=None if document == use_case else document,
        strengths=json.loads(metadata["strengths_json"]),
        weaknesses=json.loads(metadata["weaknesses_json"]),
        duration_min=int(metadata["duration_min"]),
        duration_max=int(metadata["duration_max"]),
        doc_path=metadata["doc_path"],
        similarity=similarity,
    )


def _open_collection(chroma_path: Path, embedding: EmbeddingProvider) -> Any:
    import chromadb

    if not chroma_path.exists():
        raise StaleIndexError(
            f"chroma path {chroma_path} does not exist — run `methodos ingest` first"
        )
    client = chromadb.PersistentClient(path=str(chroma_path))
    try:
        coll = client.get_collection("methods")
    except Exception as e:
        raise StaleIndexError(f"no 'methods' collection — run `methodos ingest`: {e}") from e

    persisted = (coll.metadata or {}).get("embedding_provider_name")
    if persisted != embedding.name:
        raise StaleIndexError(
            f"index was built with provider '{persisted}' but current is "
            f"'{embedding.name}' — run `methodos ingest` to rebuild"
        )
    return coll


def _rerank(query: str, candidates: list[Candidate], reranker: RerankProvider) -> list[Candidate]:
    """Re-score the shortlist with a cross-encoder and re-sort by that score."""
    scores = reranker.score(query, [c.matched_use_case or c.use_case for c in candidates])
    if len(scores) != len(candidates):
        raise RerankError(
            f"{reranker.name} returned {len(scores)} score(s) for {len(candidates)} document(s)"
        )
    rescored = [replace(c, rerank_score=s) for c, s in zip(candidates, scores, strict=True)]
    # `sorted` is stable, so ties keep the retrieval order rather than shuffling.
    return sorted(rescored, key=lambda c: c.rerank_score or 0.0, reverse=True)


def collection_size(
    chroma_path: Path,
    embedding: EmbeddingProvider,
    *,
    where: dict[str, Any] | None = None,
) -> int:
    """How many methods the index holds, optionally within a metadata filter.

    Exists so a caller can report "3 of 23" rather than just handing back three
    results: a consumer that only ever sees `top_k` entries has no way to tell a
    small catalog from a truncated view of a large one.
    """
    coll = _open_collection(chroma_path, embedding)
    got = coll.get(where=where, include=["metadatas"])
    metas = got["metadatas"] or [None] * len(got["ids"])
    # Methods, not vectors: one method with three use cases is three entries.
    return len(
        {
            (meta or {}).get("method_id", doc_id)
            for doc_id, meta in zip(got["ids"], metas, strict=True)
        }
    )


def _best_per_method(candidates: list[Candidate]) -> list[Candidate]:
    """Keep each method's best-matching use case; input must be best-first."""
    seen: set[str] = set()
    out: list[Candidate] = []
    for c in candidates:
        if c.id not in seen:
            seen.add(c.id)
            out.append(c)
    return out


def retrieve(
    *,
    query: str,
    embedding: EmbeddingProvider,
    chroma_path: Path,
    top_k: int,
    reranker: RerankProvider | None = None,
    overfetch_factor: int = 2,
    where: dict[str, Any] | None = None,
) -> list[Candidate]:
    """Return up to top_k candidates, best first.

    Over-fetches `top_k * overfetch_factor` from Chroma so a reranker can
    promote something the embedding ranked just below the cut. Without a
    reranker the extra candidates are simply discarded, exactly as before.

    `where` is handed to Chroma as a metadata filter, so the restriction applies
    *before* the nearest-neighbour cut. Filtering the returned list instead
    would quietly under-deliver — a top_k of 5 that happens to contain one
    strategy method would look like the catalog holds one.
    """
    coll = _open_collection(chroma_path, embedding)
    q_vec = embedding.embed([query])[0]

    shortlist = top_k * overfetch_factor
    # Collapsing a method's use cases into one candidate (below) must not leave
    # fewer than `shortlist` distinct methods. Either bound guarantees that:
    # every extra vector could belong to a method already listed, and no method
    # has more than `per_method` vectors. Take the smaller, so query size grows
    # with the widest method rather than with the whole catalog.
    meta = coll.metadata or {}
    extra = int(meta.get("extra_documents", 0))
    per_method = int(meta.get("max_documents_per_method", 1))
    raw = coll.query(
        query_embeddings=[q_vec],
        n_results=min(shortlist + extra, shortlist * per_method),
        include=["metadatas", "documents", "distances"],
        **({"where": where} if where else {}),
    )
    ids = raw["ids"][0]
    docs = raw["documents"][0]
    metas = raw["metadatas"][0]
    dists = raw["distances"][0]

    candidates = [
        _rehydrate(i, d, m, dist) for i, d, m, dist in zip(ids, docs, metas, dists, strict=True)
    ]
    candidates.sort(key=lambda c: c.similarity, reverse=True)
    candidates = _best_per_method(candidates)[:shortlist]
    if reranker is not None:
        candidates = _rerank(query, candidates, reranker)
    return candidates[:top_k]


def explain(
    *,
    query: str,
    candidates: list[Candidate],
    llm: LLMProvider,
) -> str:
    """Single LLM call, all candidates in one prompt for coherent comparison."""
    rendered = render_explain_prompt(
        query=query,
        candidates=[c.to_render_dict() for c in candidates],
    )
    system, user = split_system_user(rendered)
    return llm.complete(system, user)


def search(
    *,
    query: str,
    embedding: EmbeddingProvider,
    llm: LLMProvider | None,
    chroma_path: Path,
    top_k: int,
    reranker: RerankProvider | None = None,
    overfetch_factor: int = 2,
) -> SearchResult:
    """End-to-end: retrieve top_k, optionally rerank, then optionally LLM-explain."""
    candidates = retrieve(
        query=query,
        embedding=embedding,
        chroma_path=chroma_path,
        top_k=top_k,
        reranker=reranker,
        overfetch_factor=overfetch_factor,
    )
    if llm is None or not candidates:
        return SearchResult(candidates=candidates, explanation=None)
    explanation = explain(query=query, candidates=candidates, llm=llm)
    return SearchResult(candidates=candidates, explanation=explanation)
