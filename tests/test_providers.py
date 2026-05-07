from methodos.providers.base import (
    EmbeddingProvider, LLMProvider, LLMError, EmbeddingError,
)


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


from unittest.mock import MagicMock, patch
from methodos.providers.llm_litellm import LiteLLMProvider


def test_litellm_provider_satisfies_protocol():
    p = LiteLLMProvider(model="ollama/llama3.1:8b")
    assert isinstance(p, LLMProvider)
    assert p.name == "ollama/llama3.1:8b"


def test_litellm_provider_passes_messages_correctly():
    fake_response = MagicMock()
    fake_response.choices = [MagicMock(message=MagicMock(content="hi from litellm"))]
    with patch("methodos.providers.llm_litellm.litellm.completion", return_value=fake_response) as m:
        p = LiteLLMProvider(model="anthropic/claude-3-5-haiku-20241022")
        out = p.complete("you are helpful", "say hi", max_tokens=10, temperature=0.5)
    assert out == "hi from litellm"
    args, kwargs = m.call_args
    assert kwargs["model"] == "anthropic/claude-3-5-haiku-20241022"
    assert kwargs["messages"] == [
        {"role": "system", "content": "you are helpful"},
        {"role": "user", "content": "say hi"},
    ]
    assert kwargs["max_tokens"] == 10
    assert kwargs["temperature"] == 0.5


def test_litellm_provider_wraps_exceptions_into_llmerror():
    import pytest
    with patch("methodos.providers.llm_litellm.litellm.completion", side_effect=RuntimeError("boom")):
        p = LiteLLMProvider(model="ollama/llama3.1:8b")
        with pytest.raises(LLMError) as ei:
            p.complete("s", "u")
        assert "boom" in str(ei.value)
