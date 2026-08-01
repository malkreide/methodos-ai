"""Shared test fixtures: deterministic provider fakes and tmp Chroma."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from pathlib import Path

import pytest


class FakeLLM:
    """Deterministic LLM fake. Records calls for assertions."""

    name = "fake-llm"

    def __init__(self, response: str = "stub explanation") -> None:
        self.response = response
        self.calls: list[tuple[str, str]] = []

    def complete(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> str:
        self.calls.append((system, user))
        return self.response


class FakeEmbedding:
    """Deterministic embedding fake.

    Vector = first `dimensions` bytes of sha256(text), normalized to [0, 1].
    Same text → same vector → same Chroma ranking.
    """

    def __init__(self, dimensions: int = 4) -> None:
        self.name = f"fake-embedding-{dimensions}d"
        self.dimensions = dimensions

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for t in texts:
            h = hashlib.sha256(t.encode("utf-8")).digest()
            out.append([b / 255.0 for b in h[: self.dimensions]])
        return out


class FakeReranker:
    """Deterministic rerank fake: score = number of query terms in the document.

    Lexical overlap deliberately disagrees with FakeEmbedding's sha256 ordering,
    so a test can tell whether reranking actually reordered anything rather than
    happening to agree with retrieval.
    """

    name = "fake-reranker"

    def __init__(self) -> None:
        self.calls: list[tuple[str, list[str]]] = []

    def score(self, query: str, documents: Sequence[str]) -> list[float]:
        self.calls.append((query, list(documents)))
        terms = {t for t in query.lower().split() if t}
        return [float(sum(1 for t in terms if t in doc.lower())) for doc in documents]


@pytest.fixture
def fake_llm() -> FakeLLM:
    return FakeLLM()


@pytest.fixture
def fake_reranker() -> FakeReranker:
    return FakeReranker()


@pytest.fixture
def fake_embedding() -> FakeEmbedding:
    return FakeEmbedding(dimensions=8)


@pytest.fixture
def tmp_chroma_path(tmp_path: Path) -> Path:
    """A clean Chroma directory for each test."""
    p = tmp_path / "chroma"
    p.mkdir()
    return p
