"""Provider Protocols — the only seam between application code and SDKs."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable


class LLMError(Exception):
    """Raised by any LLMProvider on backend failure (rate limit, timeout, bad creds, etc.)."""


class EmbeddingError(Exception):
    """Raised by any EmbeddingProvider on backend failure."""


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Turn text into vectors. Implementations should be deterministic for same input."""

    name: str
    dimensions: int

    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


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
