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
