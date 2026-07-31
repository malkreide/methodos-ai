"""Local embeddings via sentence-transformers (CPU-friendly, offline)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from methodos.providers.base import EmbeddingError


def _load_st_model(model_name: str) -> Any:
    """Indirection so tests can patch this single function."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


def _read_dimensions(model: Any) -> int:
    """Read embedding dimensionality across sentence-transformers versions.

    5.x renamed `get_sentence_embedding_dimension` to `get_embedding_dimension`
    and warns on the old name; releases before that only have the old one, and
    pyproject allows >=2.7. Prefer the new name, fall back to the old.
    """
    for attr in ("get_embedding_dimension", "get_sentence_embedding_dimension"):
        getter = getattr(model, attr, None)
        if callable(getter):
            return int(getter())
    raise EmbeddingError(
        "sentence-transformers model exposes no known dimensionality getter "
        "(tried get_embedding_dimension, get_sentence_embedding_dimension)"
    )


class LocalEmbedding:
    """Lazy-loaded sentence-transformers model.

    The model file (~80MB for all-MiniLM-L6-v2) downloads on first use into
    HuggingFace's standard cache. After that, fully offline.

    The `_model` attribute starts as None; populated on first `embed()` call.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.name = f"local:{model_name}"
        self._model_name = model_name
        self._model: Any = None
        # `dimensions` is a plain attribute (not a property) so that
        # `hasattr(instance, "dimensions")` — used by Protocol's runtime
        # isinstance check — does NOT trigger lazy model loading.
        # Populated on first _ensure_loaded() call.
        self.dimensions: int = 0

    def _ensure_loaded(self) -> None:
        if self._model is None:
            try:
                self._model = _load_st_model(self._model_name)
            except Exception as e:
                raise EmbeddingError(f"failed to load {self._model_name}: {e}") from e
            self.dimensions = _read_dimensions(self._model)

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        self._ensure_loaded()
        try:
            vecs = self._model.encode(list(texts), normalize_embeddings=True)
        except Exception as e:
            raise EmbeddingError(f"encode failed: {e}") from e
        return [list(map(float, v)) for v in vecs]
