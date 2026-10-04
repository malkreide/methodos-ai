"""Runtime settings loaded from environment + .env."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field
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
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    """For provider='local': sentence-transformers model name.

    Multilingual by default: a German question has to find an English method
    and vice versa. The English-only all-MiniLM-L6-v2 this replaced ranked 7 of
    23 German probes correctly; see tests/test_integration.py for the numbers.
    For provider='openai': e.g. 'text-embedding-3-small'."""

    rerank_provider: Literal["none", "cross-encoder"] = "cross-encoder"
    """On by default: it measurably improves ranking on the shipped catalog.

    It needs sentence-transformers (the `local` extra). When that is missing —
    e.g. an OpenAI-embeddings install — `make_reranker` degrades to no
    reranking rather than failing the query, because ranking quality is an
    enhancement and a missing optional model should not break `methodos query`.
    An explicit `--rerank` still fails loudly; see make_reranker(required=...).
    """

    rerank_model: str = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
    """Only consulted when rerank_provider != 'none'."""

    chroma_path: Path = Path("data/chroma")
    feedback_path: Path = Path("data/feedback.jsonl")
    top_k: int = Field(default=3, ge=1)
    """Multiplied by overfetch_factor to form Chroma's n_results, which
    rejects zero and negatives with an opaque TypeError — so bound it here."""

    overfetch_factor: int = Field(default=3, ge=1)
    """Chroma returns top_k * this, then the shortlist is truncated to top_k.
    Raising it gives a reranker more to work with, at linear cost in rerank
    time; without a reranker it changes nothing but the query size.

    3 since the catalog reached 39 methods: at 2, two pinned probes found their
    method only 6th by embedding, the last slot of a 6-method shortlist, and
    three authoring runs independently pushed one of them out. 9 keeps all 78
    probes first for about 15% more rerank time (48 texts instead of 32)."""
