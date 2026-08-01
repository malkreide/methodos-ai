"""Provider factories and re-exports."""

from __future__ import annotations

from importlib.util import find_spec

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


def make_reranker(settings: Settings, *, required: bool = False) -> RerankProvider | None:
    """Construct a reranker per settings, or None when reranking won't run.

    Returning None rather than a no-op provider keeps the "did we rerank?"
    question answerable from the call site, which the CLI reports to the user.

    Reranking is on by default but needs sentence-transformers, which the base
    install does not pull in. Since ranking quality is an enhancement, a missing
    optional dependency degrades to no reranking instead of failing the query —
    unless the caller asked for it explicitly (`required=True`, i.e. `--rerank`),
    in which case silently ignoring the request would be worse than an error.
    """
    if settings.rerank_provider == "none":
        return None
    if settings.rerank_provider == "cross-encoder":
        # find_spec checks availability without importing — hard rule 1 stands.
        if find_spec("sentence_transformers") is None:
            if required:
                raise RerankError(
                    "cross-encoder reranking needs sentence-transformers: "
                    'pip install -e ".[local]" (or run with --no-rerank)'
                )
            return None
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
