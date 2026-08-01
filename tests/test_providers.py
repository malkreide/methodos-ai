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
    """sentence-transformers >=5, where the getter is `get_embedding_dimension`.

    `spec` matters here: a bare MagicMock answers to *both* getter names, which
    would hide whichever one the provider actually calls.
    """
    fake = MagicMock(spec=["get_embedding_dimension", "encode"])
    fake.get_embedding_dimension.return_value = 384
    fake.encode.return_value = [[0.1] * 384, [0.2] * 384]
    with patch("methodos.providers.embedding_local._load_st_model", return_value=fake) as ld:
        p = LocalEmbedding(model_name="all-MiniLM-L6-v2")
        out = p.embed(["a", "b"])
    assert out == [[0.1] * 384, [0.2] * 384]
    assert p.dimensions == 384
    ld.assert_called_once_with("all-MiniLM-L6-v2")


def test_local_embedding_supports_legacy_dimension_getter():
    """sentence-transformers <5 only has `get_sentence_embedding_dimension`.

    pyproject allows >=2.7, so both generations must work.
    """
    fake = MagicMock(spec=["get_sentence_embedding_dimension", "encode"])
    fake.get_sentence_embedding_dimension.return_value = 384
    fake.encode.return_value = [[0.1] * 384]
    with patch("methodos.providers.embedding_local._load_st_model", return_value=fake):
        p = LocalEmbedding(model_name="all-MiniLM-L6-v2")
        p.embed(["a"])
    assert p.dimensions == 384


def test_local_embedding_prefers_new_getter_when_both_exist():
    """The old name still exists in 5.x but warns — the new one must win."""
    fake = MagicMock(spec=["get_embedding_dimension", "get_sentence_embedding_dimension", "encode"])
    fake.get_embedding_dimension.return_value = 384
    fake.encode.return_value = [[0.1] * 384]
    with patch("methodos.providers.embedding_local._load_st_model", return_value=fake):
        p = LocalEmbedding(model_name="all-MiniLM-L6-v2")
        p.embed(["a"])
    assert p.dimensions == 384
    fake.get_sentence_embedding_dimension.assert_not_called()


def test_local_embedding_errors_when_no_dimension_getter():
    fake = MagicMock(spec=["encode"])
    with patch("methodos.providers.embedding_local._load_st_model", return_value=fake):
        p = LocalEmbedding(model_name="all-MiniLM-L6-v2")
        with pytest.raises(EmbeddingError, match="dimensionality"):
            p.embed(["a"])


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


# --- rerank ----------------------------------------------------------------


def test_rerank_protocol_is_runtime_checkable(fake_reranker):
    from methodos.providers.base import RerankProvider

    assert isinstance(fake_reranker, RerankProvider)


def test_rerank_error_is_distinguishable():
    from methodos.providers.base import EmbeddingError, LLMError, RerankError

    assert issubclass(RerankError, Exception)
    assert not issubclass(RerankError, EmbeddingError)
    assert not issubclass(RerankError, LLMError)


def test_cross_encoder_satisfies_protocol_without_loading():
    """Constructing must not touch sentence-transformers — same rule as embeddings."""
    from methodos.providers.base import RerankProvider
    from methodos.providers.rerank_cross_encoder import CrossEncoderRerank

    p = CrossEncoderRerank(model_name="cross-encoder/ms-marco-MiniLM-L-6-v2")
    assert isinstance(p, RerankProvider)
    assert p.name == "cross-encoder:cross-encoder/ms-marco-MiniLM-L-6-v2"
    assert getattr(p, "_model", None) is None


def test_cross_encoder_scores_query_document_pairs():
    from methodos.providers.rerank_cross_encoder import CrossEncoderRerank

    fake = MagicMock(spec=["predict"])
    fake.predict.return_value = [2.5, -1.0]
    with patch(
        "methodos.providers.rerank_cross_encoder._load_cross_encoder", return_value=fake
    ) as ld:
        p = CrossEncoderRerank(model_name="m")
        out = p.score("a query", ["doc one", "doc two"])

    assert out == [2.5, -1.0]
    ld.assert_called_once_with("m")
    # The model must see (query, document) pairs, not documents alone.
    assert fake.predict.call_args[0][0] == [("a query", "doc one"), ("a query", "doc two")]


def test_cross_encoder_returns_plain_floats():
    """sentence-transformers hands back numpy scalars; callers get float."""
    import array

    from methodos.providers.rerank_cross_encoder import CrossEncoderRerank

    fake = MagicMock(spec=["predict"])
    fake.predict.return_value = array.array("d", [1.5, 0.5])
    with patch("methodos.providers.rerank_cross_encoder._load_cross_encoder", return_value=fake):
        out = CrossEncoderRerank(model_name="m").score("q", ["a", "b"])
    assert out == [1.5, 0.5]
    assert all(type(x) is float for x in out)


def test_cross_encoder_wraps_load_errors():
    from methodos.providers.base import RerankError
    from methodos.providers.rerank_cross_encoder import CrossEncoderRerank

    with (
        patch(
            "methodos.providers.rerank_cross_encoder._load_cross_encoder",
            side_effect=RuntimeError("model not found"),
        ),
        pytest.raises(RerankError, match="model not found"),
    ):
        CrossEncoderRerank(model_name="bogus").score("q", ["a"])


def test_cross_encoder_wraps_predict_errors():
    from methodos.providers.base import RerankError
    from methodos.providers.rerank_cross_encoder import CrossEncoderRerank

    fake = MagicMock(spec=["predict"])
    fake.predict.side_effect = RuntimeError("boom")
    with (
        patch("methodos.providers.rerank_cross_encoder._load_cross_encoder", return_value=fake),
        pytest.raises(RerankError, match="boom"),
    ):
        CrossEncoderRerank(model_name="m").score("q", ["a"])


def test_cross_encoder_short_circuits_on_empty_documents():
    """No documents means no model load — reranking an empty shortlist is free."""
    from methodos.providers.rerank_cross_encoder import CrossEncoderRerank

    with patch("methodos.providers.rerank_cross_encoder._load_cross_encoder") as ld:
        assert CrossEncoderRerank(model_name="m").score("q", []) == []
    ld.assert_not_called()


def test_make_reranker_is_on_by_default(monkeypatch):
    from methodos.providers import make_reranker
    from methodos.providers.rerank_cross_encoder import CrossEncoderRerank

    monkeypatch.delenv("METHODOS_RERANK_PROVIDER", raising=False)
    assert isinstance(make_reranker(Settings(_env_file=None)), CrossEncoderRerank)


def test_make_reranker_returns_none_when_explicitly_disabled(monkeypatch):
    from methodos.providers import make_reranker

    monkeypatch.setenv("METHODOS_RERANK_PROVIDER", "none")
    assert make_reranker(Settings(_env_file=None)) is None


def test_make_reranker_degrades_when_sentence_transformers_is_missing(monkeypatch):
    """Base install + OpenAI embeddings must keep working, just without rerank."""
    from methodos.providers import make_reranker

    monkeypatch.delenv("METHODOS_RERANK_PROVIDER", raising=False)
    with patch("methodos.providers.find_spec", return_value=None):
        assert make_reranker(Settings(_env_file=None)) is None


def test_make_reranker_raises_when_explicitly_required_but_missing(monkeypatch):
    """`--rerank` asked for it; silently ignoring that would be worse than failing."""
    from methodos.providers import make_reranker
    from methodos.providers.base import RerankError

    monkeypatch.delenv("METHODOS_RERANK_PROVIDER", raising=False)
    with (
        patch("methodos.providers.find_spec", return_value=None),
        pytest.raises(RerankError, match="sentence-transformers"),
    ):
        make_reranker(Settings(_env_file=None), required=True)


def test_make_reranker_does_not_import_sentence_transformers_to_check(monkeypatch):
    """Availability check must not import the heavy dep — hard rule 1."""
    from methodos.providers import make_reranker

    monkeypatch.delenv("METHODOS_RERANK_PROVIDER", raising=False)
    with patch("methodos.providers.find_spec", return_value=object()) as fs:
        make_reranker(Settings(_env_file=None))
    fs.assert_called_once_with("sentence_transformers")


def test_make_reranker_rejects_unknown_provider(monkeypatch):
    from pydantic import ValidationError

    monkeypatch.setenv("METHODOS_RERANK_PROVIDER", "magic")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
