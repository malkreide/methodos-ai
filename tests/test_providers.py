from unittest.mock import MagicMock, patch

import pytest

from methodos.config import Settings
from methodos.providers import make_embedding, make_llm
from methodos.providers.base import (
    EmbeddingError,
    EmbeddingProvider,
    LLMError,
    LLMProvider,
)
from methodos.providers.embedding_local import LocalEmbedding
from methodos.providers.embedding_openai import OpenAIEmbedding
from methodos.providers.llm_litellm import LiteLLMProvider


def test_protocols_are_runtime_checkable():
    class MinimalLLM:
        name = "x"

        def complete(self, system, user, *, max_tokens=1024, temperature=0.2):
            return ""

    class MinimalEmbedding:
        name = "x"
        dimensions = 4

        def embed(self, texts):
            return [[0.0, 0.0, 0.0, 0.0] for _ in texts]

    assert isinstance(MinimalLLM(), LLMProvider)
    assert isinstance(MinimalEmbedding(), EmbeddingProvider)


def test_errors_are_distinguishable():
    assert issubclass(LLMError, Exception)
    assert issubclass(EmbeddingError, Exception)
    assert not issubclass(LLMError, EmbeddingError)


def test_fake_llm_satisfies_protocol(fake_llm):
    assert isinstance(fake_llm, LLMProvider)


def test_fake_embedding_satisfies_protocol(fake_embedding):
    assert isinstance(fake_embedding, EmbeddingProvider)


def test_fake_embedding_is_deterministic(fake_embedding):
    a = fake_embedding.embed(["hello"])
    b = fake_embedding.embed(["hello"])
    assert a == b


def test_fake_llm_records_calls(fake_llm):
    fake_llm.complete("S", "U")
    fake_llm.complete("S2", "U2")
    assert fake_llm.calls == [("S", "U"), ("S2", "U2")]


def test_litellm_provider_satisfies_protocol():
    p = LiteLLMProvider(model="ollama/llama3.1:8b")
    assert isinstance(p, LLMProvider)
    assert p.name == "ollama/llama3.1:8b"


def test_litellm_provider_passes_messages_correctly():
    fake_response = MagicMock()
    fake_response.choices = [MagicMock(message=MagicMock(content="hi from litellm"))]
    with patch(
        "methodos.providers.llm_litellm.litellm.completion", return_value=fake_response
    ) as m:
        p = LiteLLMProvider(model="anthropic/claude-3-5-haiku-20241022")
        out = p.complete("you are helpful", "say hi", max_tokens=10, temperature=0.5)
    assert out == "hi from litellm"
    kwargs = m.call_args.kwargs
    assert kwargs["model"] == "anthropic/claude-3-5-haiku-20241022"
    assert kwargs["messages"] == [
        {"role": "system", "content": "you are helpful"},
        {"role": "user", "content": "say hi"},
    ]
    assert kwargs["max_tokens"] == 10
    assert kwargs["temperature"] == 0.5


def test_litellm_provider_wraps_exceptions_into_llmerror():
    with patch(
        "methodos.providers.llm_litellm.litellm.completion", side_effect=RuntimeError("boom")
    ):
        p = LiteLLMProvider(model="ollama/llama3.1:8b")
        with pytest.raises(LLMError) as ei:
            p.complete("s", "u")
        assert "boom" in str(ei.value)


def test_local_embedding_lazy_loads_model():
    p = LocalEmbedding(model_name="all-MiniLM-L6-v2")
    assert p.name == "local:all-MiniLM-L6-v2"
    assert getattr(p, "_model", None) is None


def test_local_embedding_calls_underlying_model():
    fake = MagicMock()
    fake.get_sentence_embedding_dimension.return_value = 384
    fake.encode.return_value = [[0.1] * 384, [0.2] * 384]
    with patch("methodos.providers.embedding_local._load_st_model", return_value=fake) as ld:
        p = LocalEmbedding(model_name="all-MiniLM-L6-v2")
        out = p.embed(["a", "b"])
    assert out == [[0.1] * 384, [0.2] * 384]
    assert p.dimensions == 384
    ld.assert_called_once_with("all-MiniLM-L6-v2")


def test_local_embedding_satisfies_protocol():
    assert isinstance(LocalEmbedding(model_name="x"), EmbeddingProvider)


def test_local_embedding_wraps_errors():
    with patch(
        "methodos.providers.embedding_local._load_st_model",
        side_effect=RuntimeError("model not found"),
    ):
        p = LocalEmbedding(model_name="bogus")
        with pytest.raises(EmbeddingError):
            p.embed(["x"])


def test_openai_embedding_satisfies_protocol():
    assert isinstance(OpenAIEmbedding(model_name="text-embedding-3-small"), EmbeddingProvider)
    p = OpenAIEmbedding(model_name="text-embedding-3-small")
    assert p.name == "openai:text-embedding-3-small"
    assert p.dimensions == 1536


def test_openai_embedding_uses_client():
    fake_client = MagicMock()
    fake_client.embeddings.create.return_value = MagicMock(
        data=[MagicMock(embedding=[0.1] * 1536), MagicMock(embedding=[0.2] * 1536)]
    )
    with patch("methodos.providers.embedding_openai._client", return_value=fake_client):
        p = OpenAIEmbedding(model_name="text-embedding-3-small")
        out = p.embed(["a", "b"])
    assert out == [[0.1] * 1536, [0.2] * 1536]
    fake_client.embeddings.create.assert_called_once_with(
        model="text-embedding-3-small", input=["a", "b"]
    )


def test_openai_embedding_wraps_errors():
    fake_client = MagicMock()
    fake_client.embeddings.create.side_effect = RuntimeError("rate limit")
    with patch("methodos.providers.embedding_openai._client", return_value=fake_client):
        p = OpenAIEmbedding(model_name="text-embedding-3-small")
        with pytest.raises(EmbeddingError):
            p.embed(["a"])


def test_make_llm_returns_litellm_provider(monkeypatch):
    monkeypatch.setenv("METHODOS_MODEL", "ollama/llama3.1:8b")
    s = Settings(_env_file=None)
    llm = make_llm(s)
    assert isinstance(llm, LiteLLMProvider)
    assert llm.name == "ollama/llama3.1:8b"


def test_make_embedding_local_default(monkeypatch):
    for k in ("METHODOS_EMBEDDING_PROVIDER", "METHODOS_EMBEDDING_MODEL"):
        monkeypatch.delenv(k, raising=False)
    s = Settings(_env_file=None)
    e = make_embedding(s)
    assert isinstance(e, LocalEmbedding)
    assert e.name.startswith("local:")


def test_make_embedding_openai(monkeypatch):
    monkeypatch.setenv("METHODOS_EMBEDDING_PROVIDER", "openai")
    monkeypatch.setenv("METHODOS_EMBEDDING_MODEL", "text-embedding-3-small")
    s = Settings(_env_file=None)
    e = make_embedding(s)
    assert isinstance(e, OpenAIEmbedding)
