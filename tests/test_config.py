from pathlib import Path

from methodos.config import Settings


def test_defaults_are_offline_friendly(monkeypatch):
    for k in (
        "METHODOS_MODEL",
        "METHODOS_EMBEDDING_PROVIDER",
        "METHODOS_EMBEDDING_MODEL",
        "METHODOS_TOP_K",
    ):
        monkeypatch.delenv(k, raising=False)
    s = Settings(_env_file=None)
    assert s.model.startswith("ollama/")
    assert s.embedding_provider == "local"
    assert s.top_k == 3
    assert isinstance(s.chroma_path, Path)


def test_env_overrides(monkeypatch):
    monkeypatch.setenv("METHODOS_MODEL", "anthropic/claude-3-5-haiku-20241022")
    monkeypatch.setenv("METHODOS_EMBEDDING_PROVIDER", "openai")
    monkeypatch.setenv("METHODOS_TOP_K", "5")
    s = Settings(_env_file=None)
    assert s.model == "anthropic/claude-3-5-haiku-20241022"
    assert s.embedding_provider == "openai"
    assert s.top_k == 5


def test_invalid_embedding_provider_rejected(monkeypatch):
    monkeypatch.setenv("METHODOS_EMBEDDING_PROVIDER", "elasticsearch")
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Settings(_env_file=None)
