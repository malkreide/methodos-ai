"""Runtime settings loaded from environment + .env."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All env vars are prefixed `METHODOS_` (e.g., METHODOS_MODEL)."""

    model_config = SettingsConfigDict(
        env_prefix="METHODOS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    model: str = "ollama/llama3.1:8b"
    """Litellm model string in the form '<provider>/<model>'."""

    embedding_provider: Literal["local", "openai"] = "local"
    embedding_model: str = "all-MiniLM-L6-v2"
    """For provider='local': sentence-transformers model name.
    For provider='openai': e.g. 'text-embedding-3-small'."""

    rerank_provider: Literal["none", "cross-encoder"] = "cross-encoder"
    """On by default: it measurably improves ranking on the shipped catalog.

    It needs sentence-transformers (the `local` extra). When that is missing —
    e.g. an OpenAI-embeddings install — `make_reranker` degrades to no
    reranking rather than failing the query, because ranking quality is an
    enhancement and a missing optional model should not break `methodos query`.
    An explicit `--rerank` still fails loudly; see make_reranker(required=...).
    """

    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    """Only consulted when rerank_provider != 'none'."""

    chroma_path: Path = Path("data/chroma")
    feedback_path: Path = Path("data/feedback.jsonl")
    top_k: int = 3

    overfetch_factor: int = 2
    """Chroma returns top_k * this, then the shortlist is truncated to top_k.
    Raising it gives a reranker more to work with, at linear cost in rerank
    time; without a reranker it changes nothing but the query size."""
