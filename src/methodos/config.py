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

    chroma_path: Path = Path("data/chroma")
    feedback_path: Path = Path("data/feedback.jsonl")
    top_k: int = 3
