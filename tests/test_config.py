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
    assert s.rerank_provider == "cross-encoder", "reranking ships on by default"
    assert s.overfetch_factor == 2
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


def test_overfetch_factor_must_be_positive(monkeypatch):
    """0 or negative reaches Chroma as n_results and raises an opaque TypeError."""
    import pytest
    from pydantic import ValidationError

    for bad in ("0", "-1"):
        monkeypatch.setenv("METHODOS_OVERFETCH_FACTOR", bad)
        with pytest.raises(ValidationError):
            Settings(_env_file=None)


def test_top_k_must_be_positive(monkeypatch):
    """Same exposure: top_k * overfetch_factor is the n_results Chroma gets."""
    import pytest
    from pydantic import ValidationError

    monkeypatch.setenv("METHODOS_TOP_K", "0")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
