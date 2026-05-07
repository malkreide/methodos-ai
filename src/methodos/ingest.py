"""Ingest /methods/*.json into a ChromaDB collection.

Always-rebuild semantics: the existing 'methods' collection is dropped and
recreated on every run. The collection is a derived artifact — like a build
output — and treating it as cache simplifies the invariant that the index is a
pure function of the JSON files on disk.

# === Similarity scoring math ===
# Embeddings map each method's `use_case` (natural-language description)
# into R^<provider.dimensions> via <provider.name>.
#
# At query time, ChromaDB ranks documents by cosine similarity:
#
#     cos(q, d) = (q · d) / (||q|| * ||d||)
#
# where q is the query embedding and d is a document embedding.
# Higher cosine = more semantically similar in the embedding space.
#
# Chroma returns the cosine *distance* = 1 - cos(q, d). search.py converts:
#     similarity = 1 - distance     ∈ [0, 2], typically [0, 1] for normalized
#
# Note: cosine assumes embeddings are roughly normalized. Both
# sentence-transformers (with normalize_embeddings=True) and OpenAI embedding
# models produce normalized vectors by default, so this assumption holds.
#
# CRITICAL: ChromaDB defaults to L2 distance unless `hnsw:space=cosine` is
# specified in collection metadata. This file sets it explicitly.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from methodos.models import Method
from methodos.providers.base import EmbeddingProvider


class IngestError(Exception):
    """Raised when ingest cannot complete (validation, IO, etc.)."""


@dataclass(frozen=True)
class IngestSummary:
    count: int
    ids: list[str]
    provider_name: str
    dimensions: int


def _flatten_metadata(method: Method) -> dict[str, Any]:
    return {
        "name": method.name,
        "category": method.category.value,
        "complexity_score": method.complexity_score,
        "duration_min": method.estimated_duration.min_minutes,
        "duration_max": method.estimated_duration.max_minutes,
        "strengths_json": json.dumps(method.strengths),
        "weaknesses_json": json.dumps(method.weaknesses),
        "references_json": json.dumps(method.references),
        "doc_path": method.doc_path,
    }


def _load_and_validate(methods_dir: Path) -> list[Method]:
    """Parse all JSON files, validate, return Method list. Raises IngestError on failure."""
    if not methods_dir.is_dir():
        raise IngestError(f"{methods_dir} is not a directory")

    files = sorted(methods_dir.glob("*.json"))
    if not files:
        return []

    methods: list[Method] = []
    errors: list[str] = []
    seen: dict[str, Path] = {}

    for path in files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append(f"{path}: invalid JSON: {e}")
            continue
        try:
            method = Method.model_validate(data)
        except ValidationError as e:
            errors.append(f"{path}: {e}")
            continue
        if path.stem != method.id:
            errors.append(
                f"{path}: filename stem '{path.stem}' must equal id '{method.id}'"
            )
            continue
        if not path.with_suffix(".md").exists():
            errors.append(f"{path}: missing companion {path.stem}.md")
            continue
        if method.id in seen:
            errors.append(
                f"{path}: duplicate id '{method.id}' (also in {seen[method.id]})"
            )
            continue
        seen[method.id] = path
        methods.append(method)

    if errors:
        raise IngestError("\n".join(errors))
    return methods


def ingest(
    *,
    methods_dir: Path,
    chroma_path: Path,
    embedding: EmbeddingProvider,
) -> IngestSummary:
    """Rebuild the 'methods' Chroma collection from /methods/*.json.

    Drops any existing collection. Returns a summary of what was ingested.
    Raises IngestError on validation failure (collection is left untouched).
    """
    methods = _load_and_validate(methods_dir)
    if not methods:
        return IngestSummary(
            count=0, ids=[], provider_name=embedding.name, dimensions=embedding.dimensions
        )

    import chromadb

    chroma_path.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(chroma_path))

    try:
        client.delete_collection("methods")
    except Exception:
        pass

    collection = client.create_collection(
        name="methods",
        metadata={
            # CRITICAL: ChromaDB defaults to L2 (Euclidean) distance. Force cosine
            # so the math comment block above is actually true. Without this,
            # `similarity = 1 - distance` is meaningless and rankings are wrong.
            "hnsw:space": "cosine",
            "embedding_provider_name": embedding.name,
            "embedding_dimensions": embedding.dimensions,
            "schema_version": 1,
        },
    )

    use_cases = [m.use_case for m in methods]
    vectors = embedding.embed(use_cases)
    if any(len(v) != embedding.dimensions for v in vectors):
        raise IngestError(
            f"embedding provider returned wrong dimensionality "
            f"(expected {embedding.dimensions})"
        )

    collection.upsert(
        ids=[m.id for m in methods],
        embeddings=vectors,
        documents=use_cases,
        metadatas=[_flatten_metadata(m) for m in methods],
    )

    return IngestSummary(
        count=len(methods),
        ids=[m.id for m in methods],
        provider_name=embedding.name,
        dimensions=embedding.dimensions,
    )
