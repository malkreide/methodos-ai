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
            "complexity_score": self.complexity_score,
            "use_case": self.use_case,
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
    """Reconstruct a Candidate from Chroma's flat metadata."""
    similarity = 1.0 - distance
    return Candidate(
        id=chroma_id,
        name=metadata["name"],
        category=metadata["category"],
        complexity_score=int(metadata["complexity_score"]),
        use_case=document,
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
    scores = reranker.score(query, [c.use_case for c in candidates])
    if len(scores) != len(candidates):
        raise RerankError(
            f"{reranker.name} returned {len(scores)} score(s) for {len(candidates)} document(s)"
        )
    rescored = [replace(c, rerank_score=s) for c, s in zip(candidates, scores, strict=True)]
    # `sorted` is stable, so ties keep the retrieval order rather than shuffling.
    return sorted(rescored, key=lambda c: c.rerank_score or 0.0, reverse=True)


def retrieve(
    *,
    query: str,
    embedding: EmbeddingProvider,
    chroma_path: Path,
    top_k: int,
    reranker: RerankProvider | None = None,
    overfetch_factor: int = 2,
) -> list[Candidate]:
    """Return up to top_k candidates, best first.

    Over-fetches `top_k * overfetch_factor` from Chroma so a reranker can
    promote something the embedding ranked just below the cut. Without a
    reranker the extra candidates are simply discarded, exactly as before.
    """
    coll = _open_collection(chroma_path, embedding)
    q_vec = embedding.embed([query])[0]

    raw = coll.query(
        query_embeddings=[q_vec],
        n_results=top_k * overfetch_factor,
        include=["metadatas", "documents", "distances"],
    )
    ids = raw["ids"][0]
    docs = raw["documents"][0]
    metas = raw["metadatas"][0]
    dists = raw["distances"][0]

    candidates = [
        _rehydrate(i, d, m, dist) for i, d, m, dist in zip(ids, docs, metas, dists, strict=True)
    ]
    candidates.sort(key=lambda c: c.similarity, reverse=True)
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
