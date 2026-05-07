"""Retrieval + LLM explanation. See ingest.py for the similarity-math comment block."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from methodos.prompts.loader import render_explain_prompt, split_system_user
from methodos.providers.base import EmbeddingProvider, LLMProvider


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


def retrieve(
    *,
    query: str,
    embedding: EmbeddingProvider,
    chroma_path: Path,
    top_k: int,
) -> list[Candidate]:
    """Return up to top_k candidates sorted by similarity (descending)."""
    coll = _open_collection(chroma_path, embedding)
    q_vec = embedding.embed([query])[0]

    raw = coll.query(
        query_embeddings=[q_vec],
        n_results=top_k * 2,
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
) -> SearchResult:
    """End-to-end: retrieve top_k, then optionally LLM-explain."""
    candidates = retrieve(query=query, embedding=embedding, chroma_path=chroma_path, top_k=top_k)
    if llm is None or not candidates:
        return SearchResult(candidates=candidates, explanation=None)
    explanation = explain(query=query, candidates=candidates, llm=llm)
    return SearchResult(candidates=candidates, explanation=explanation)
