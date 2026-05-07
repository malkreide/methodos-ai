"""OpenAI embeddings — opt-in cloud alternative to LocalEmbedding."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from methodos.providers.base import EmbeddingError

_KNOWN_DIMS: dict[str, int] = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
}


def _client() -> Any:
    """Lazy-construct the OpenAI client (reads OPENAI_API_KEY from env)."""
    from openai import OpenAI

    return OpenAI()


class OpenAIEmbedding:
    def __init__(self, model_name: str = "text-embedding-3-small") -> None:
        self.name = f"openai:{model_name}"
        self._model_name = model_name
        if model_name not in _KNOWN_DIMS:
            raise ValueError(
                f"Unknown OpenAI embedding model: {model_name}. "
                f"Add its dimension to _KNOWN_DIMS in embedding_openai.py."
            )
        self.dimensions = _KNOWN_DIMS[model_name]

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        try:
            client = _client()
            resp = client.embeddings.create(model=self._model_name, input=list(texts))
        except Exception as e:
            raise EmbeddingError(f"{type(e).__name__}: {e}") from e
        return [list(item.embedding) for item in resp.data]
