"""Provider Protocols — the only seam between application code and SDKs."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable


class LLMError(Exception):
    """Raised by any LLMProvider on backend failure (rate limit, timeout, bad creds, etc.)."""


class EmbeddingError(Exception):
    """Raised by any EmbeddingProvider on backend failure."""


class RerankError(Exception):
    """Raised by any RerankProvider on backend failure."""


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Turn text into vectors. Implementations should be deterministic for same input."""

    name: str
    dimensions: int

    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


@runtime_checkable
class RerankProvider(Protocol):
    """Score (query, document) pairs jointly.

    An EmbeddingProvider encodes the query and the document independently, so
    it can only compare two vectors that never saw each other. A reranker feeds
    both into one model at once, which is far more accurate and far too slow to
    run over a whole corpus — hence the over-fetch-then-rerank shape in
    `search.py`: cheap recall first, expensive precision on the shortlist.

    Returns raw scores, not an ordering: ranking is `search.py`'s job, and
    scores let callers see how close the contenders were.
    """

    name: str

    def score(self, query: str, documents: Sequence[str]) -> list[float]:
        """One score per document, higher is more relevant. Raise RerankError on failure.

        Scores are model-specific logits, not similarities: they are not bounded
        to [-1, 1] and are only meaningful relative to each other within one call.
        """
        ...


@runtime_checkable
class LLMProvider(Protocol):
    """Generate a chat completion. May be non-deterministic; that's by design."""

    name: str

    def complete(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> str: ...
