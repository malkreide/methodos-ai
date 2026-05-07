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
