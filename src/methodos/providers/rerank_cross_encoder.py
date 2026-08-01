"""Cross-encoder reranking via sentence-transformers (CPU-friendly, offline)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from methodos.providers.base import RerankError

DEFAULT_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


def _load_cross_encoder(model_name: str) -> Any:
    """Indirection so tests can patch this single function."""
    from sentence_transformers import CrossEncoder

    return CrossEncoder(model_name)


class CrossEncoderRerank:
    """Lazy-loaded cross-encoder that scores (query, document) pairs jointly.

    The model (~80MB for ms-marco-MiniLM-L-6-v2) downloads on first use into
    HuggingFace's standard cache. After that, fully offline.

    Unlike an embedding model this cannot be precomputed: the query and the
    document have to go through the network together, so cost is linear in the
    size of the shortlist. That is why it runs after retrieval, never instead
    of it.
    """

    def __init__(self, model_name: str = DEFAULT_MODEL) -> None:
        self.name = f"cross-encoder:{model_name}"
        self._model_name = model_name
        self._model: Any = None

    def _ensure_loaded(self) -> None:
        if self._model is None:
            try:
                self._model = _load_cross_encoder(self._model_name)
            except Exception as e:
                raise RerankError(f"failed to load {self._model_name}: {e}") from e

    def score(self, query: str, documents: Sequence[str]) -> list[float]:
        if not documents:
            # Skip the model load entirely — an empty shortlist costs nothing.
            return []
        self._ensure_loaded()
        pairs = [(query, doc) for doc in documents]
        try:
            raw = self._model.predict(pairs)
        except Exception as e:
            raise RerankError(f"predict failed: {e}") from e
        # sentence-transformers returns a numpy array; callers get plain floats.
        return [float(x) for x in raw]
