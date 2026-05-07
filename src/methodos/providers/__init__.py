"""Provider factories and re-exports."""

from __future__ import annotations

from methodos.config import Settings
from methodos.providers.base import (
    EmbeddingError,
    EmbeddingProvider,
    LLMError,
    LLMProvider,
)


def make_llm(settings: Settings) -> LLMProvider:
    """Construct an LLM provider from settings (currently always litellm)."""
    from methodos.providers.llm_litellm import LiteLLMProvider

    return LiteLLMProvider(model=settings.model)


def make_embedding(settings: Settings) -> EmbeddingProvider:
    """Construct an embedding provider per settings.embedding_provider."""
    if settings.embedding_provider == "local":
        from methodos.providers.embedding_local import LocalEmbedding

        return LocalEmbedding(model_name=settings.embedding_model)
    if settings.embedding_provider == "openai":
        from methodos.providers.embedding_openai import OpenAIEmbedding

        return OpenAIEmbedding(model_name=settings.embedding_model)
    raise ValueError(f"unknown embedding_provider: {settings.embedding_provider}")


__all__ = [
    "EmbeddingError",
    "EmbeddingProvider",
    "LLMError",
    "LLMProvider",
    "make_embedding",
    "make_llm",
]
