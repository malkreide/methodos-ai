"""Provider factories and re-exports."""

from __future__ import annotations

from methodos.config import Settings
from methodos.providers.base import (
    EmbeddingError,
    EmbeddingProvider,
    LLMError,
    LLMProvider,
    RerankError,
    RerankProvider,
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


def make_reranker(settings: Settings) -> RerankProvider | None:
    """Construct a reranker per settings, or None when reranking is off.

    Returning None rather than a no-op provider keeps the "did we rerank?"
    question answerable from the call site, which the CLI reports to the user.
    """
    if settings.rerank_provider == "none":
        return None
    if settings.rerank_provider == "cross-encoder":
        from methodos.providers.rerank_cross_encoder import CrossEncoderRerank

        return CrossEncoderRerank(model_name=settings.rerank_model)
    raise ValueError(f"unknown rerank_provider: {settings.rerank_provider}")


__all__ = [
    "EmbeddingError",
    "EmbeddingProvider",
    "LLMError",
    "LLMProvider",
    "RerankError",
    "RerankProvider",
    "make_embedding",
    "make_llm",
    "make_reranker",
]
