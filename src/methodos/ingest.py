"""Ingest /methods/*.json into a ChromaDB collection.

Always-rebuild semantics: the existing 'methods' collection is dropped and
recreated on every run. The collection is a derived artifact — like a build
output — and treating it as cache simplifies the invariant that the index is a
pure function of the JSON files on disk.

# === Similarity scoring math ===
# Embeddings map each method's `use_case` (natural-language description)
# into R^<provider.dimensions> via <provider.name>.
#
# A method with further `use_cases` gets one vector per use case. search.py
# collapses them again, scoring each method by its best-matching use case:
#
#     sim(q, method) = max_i cos(q, d_i)
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

import contextlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

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
    documents: int = 0
    """Vectors written: one per use case, so >= count."""


def _flatten_metadata(method: Method) -> dict[str, Any]:
    return {
        "method_id": method.id,
        "use_case": method.use_case,
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


def asset_problems(method: Method, methods_dir: Path) -> list[str]:
    """Shipped assets whose file is missing from `methods/assets/<Id>/`.

    The model can check an asset's shape but not the filesystem, and a dangling
    path would only surface when someone clicked it.
    """
    root = methods_dir / "assets" / method.id
    return [
        f"asset {a.title!r}: {root / a.path} does not exist"
        for a in method.assets
        if a.path is not None and not (root / a.path).is_file()
    ]


def _documents(method: Method) -> list[tuple[str, str]]:
    """(chroma id, text) for every use case of a method.

    The canonical `use_case` keeps the bare method id, so an index holding no
    extra use cases is id-for-id what it was before they existed.
    """
    return [(method.id, method.use_case)] + [
        (f"{method.id}#{n}", text) for n, text in enumerate(method.use_cases, 1)
    ]


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
            errors.append(f"{path}: filename stem '{path.stem}' must equal id '{method.id}'")
            continue
        if not path.with_suffix(".md").exists():
            errors.append(f"{path}: missing companion {path.stem}.md")
            continue
        if missing := asset_problems(method, methods_dir):
            errors.extend(f"{path}: {m}" for m in missing)
            continue
        if method.id in seen:
            errors.append(f"{path}: duplicate id '{method.id}' (also in {seen[method.id]})")
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

    from methodos.chroma import persistent_client

    chroma_path.mkdir(parents=True, exist_ok=True)
    client = persistent_client(chroma_path)

    with contextlib.suppress(Exception):
        client.delete_collection("methods")

    collection = client.create_collection(
        name="methods",
        metadata={
            # CRITICAL: ChromaDB defaults to L2 (Euclidean) distance. Force cosine
            # so the math comment block above is actually true. Without this,
            # `similarity = 1 - distance` is meaningless and rankings are wrong.
            "hnsw:space": "cosine",
            "embedding_provider_name": embedding.name,
            "embedding_dimensions": embedding.dimensions,
            "schema_version": 2,
            # search.py over-fetches by these so that collapsing a method's use
            # cases back into one candidate cannot shrink the shortlist.
            "extra_documents": sum(len(m.use_cases) for m in methods),
            "max_documents_per_method": 1 + max(len(m.use_cases) for m in methods),
        },
    )

    doc_ids: list[str] = []
    texts: list[str] = []
    metadatas: list[dict[str, Any]] = []
    for m in methods:
        meta = _flatten_metadata(m)
        for doc_id, text in _documents(m):
            doc_ids.append(doc_id)
            texts.append(text)
            metadatas.append(meta)

    vectors = embedding.embed(texts)
    if any(len(v) != embedding.dimensions for v in vectors):
        raise IngestError(
            f"embedding provider returned wrong dimensionality (expected {embedding.dimensions})"
        )

    collection.upsert(
        ids=doc_ids,
        embeddings=cast(Any, vectors),
        documents=texts,
        metadatas=cast(Any, metadatas),
    )

    return IngestSummary(
        count=len(methods),
        ids=[m.id for m in methods],
        provider_name=embedding.name,
        dimensions=embedding.dimensions,
        documents=len(doc_ids),
    )
