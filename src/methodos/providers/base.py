"""Provider Protocols — the only seam between application code and SDKs."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable


class LLMError(Exception):
    """Raised by any LLMProvider on backend failure (rate limit, timeout, bad creds, etc.)."""


class EmbeddingError(Exception):
    """Raised by any EmbeddingProvider on backend failure."""


class RerankError(Exception):
    """Raised by any RerankProvider on backend failure."""


class TranscriptionError(Exception):
    """Raised by any TranscriptionProvider on backend failure or undecodable media."""


class MediaTooLongError(TranscriptionError):
    """The recording is longer than the caller allows. Raised before any decoding."""


class TranscriberUnavailableError(TranscriptionError):
    """The backend itself failed (the model would not load), not the recording."""


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


@dataclass(frozen=True)
class Transcript:
    text: str
    duration_seconds: float
    language: str | None = None
    """Detected spoken language (ISO 639-1), when the backend reports one."""


@runtime_checkable
class TranscriptionProvider(Protocol):
    """Speech to text for an audio or video file on local disk.

    Local by contract: a recording of a meeting or a lesson carries the voices
    of people who never agreed to send them anywhere, so an implementation
    must not ship the audio to a remote service. Whatever happens to the text
    afterwards is the caller's decision and the caller's notice to give.
    """

    name: str

    def transcribe(self, path: Path, *, max_seconds: float) -> Transcript:
        """Raise MediaTooLongError past `max_seconds`, TranscriptionError on any failure."""
        ...
