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
from methodos.providers.llm_litellm import LiteLLMProvider, key_problem


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
    assert kwargs["drop_params"] is True, "else models that refuse temperature fail"


def _serve_fake_anthropic(seen: dict):
    """A localhost stand-in for the Messages API that records the request body."""
    import json
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            seen["body"] = json.loads(self.rfile.read(int(self.headers["content-length"])))
            out = json.dumps(
                {
                    "id": "msg_test",
                    "type": "message",
                    "role": "assistant",
                    "model": seen["body"]["model"],
                    "content": [{"type": "text", "text": "ok"}],
                    "stop_reason": "end_turn",
                    "usage": {"input_tokens": 1, "output_tokens": 1},
                }
            ).encode()
            self.send_response(200)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(out)))
            self.end_headers()
            self.wfile.write(out)

        def log_message(self, *a):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


@pytest.mark.parametrize(
    ("model", "sends_temperature"),
    [("anthropic/claude-opus-5", False), ("anthropic/claude-sonnet-4-6", True)],
)
def test_temperature_reaches_only_models_that_take_it(monkeypatch, model, sends_temperature):
    """The Docker default (claude-opus-5) refuses `temperature`; litellm used to
    refuse the whole call on its behalf, so every explanation and every upload
    draft failed. Runs the real litellm against a localhost endpoint: no key, no
    network, but the exact request body that would go out."""
    seen: dict = {}
    server = _serve_fake_anthropic(seen)
    try:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.setenv("ANTHROPIC_API_BASE", f"http://127.0.0.1:{server.server_port}")
        monkeypatch.setenv("NO_PROXY", "127.0.0.1")
        out = LiteLLMProvider(model=model).complete("s", "u", temperature=0.2)
    finally:
        server.shutdown()
    assert out == "ok"
    assert ("temperature" in seen["body"]) is sends_temperature


def test_litellm_provider_names_an_exhausted_budget():
    """A thinking model can spend max_tokens before it writes anything."""
    fake = MagicMock()
    fake.choices = [MagicMock(message=MagicMock(content=None), finish_reason="length")]
    with (
        patch("methodos.providers.llm_litellm.litellm.completion", return_value=fake),
        pytest.raises(LLMError, match="max_tokens=16"),
    ):
        LiteLLMProvider(model="anthropic/claude-opus-5").complete("s", "u", max_tokens=16)


@pytest.mark.parametrize(
    ("key", "found"),
    [
        ("sk-ant-api03-\u2026", "'…' at position 13"),
        ("sk-ant-api03-abc def", "' ' at position 16"),
        ("sk-ant-...", "placeholder"),
        ("<your key>", "placeholder"),
    ],
)
def test_litellm_provider_names_a_key_that_is_not_one(monkeypatch, key, found):
    """The docs' placeholder pasted as the key used to fail inside litellm as
    "'ascii' codec can't encode character '\\u2026' in position 13" — on a
    real machine, with the image freshly built. Now it fails before the call,
    naming the variable, and without repeating the key."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", key)
    with (
        patch("methodos.providers.llm_litellm.litellm.completion") as m,
        pytest.raises(LLMError, match="ANTHROPIC_API_KEY") as ei,
    ):
        LiteLLMProvider(model="anthropic/claude-opus-5").complete("s", "u")
    assert found in str(ei.value)
    m.assert_not_called()


@pytest.mark.parametrize(
    ("model", "env"),
    [
        ("anthropic/claude-opus-5", {"ANTHROPIC_API_KEY": "sk-ant-api03-" + "x" * 95}),
        ("anthropic/claude-opus-5", {}),  # missing: litellm says so itself
        ("ollama/llama3.1:8b", {"ANTHROPIC_API_KEY": "sk-ant-api03-\u2026"}),  # not its key
        ("gpt-4o-mini", {"OPENAI_API_KEY": "sk-\u2026"}),  # no provider prefix: not guessed
    ],
)
def test_key_problem_leaves_usable_and_unrelated_keys_alone(model, env):
    assert key_problem(model, env) is None


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
    """Asserts the policy, not the machine.

    find_spec is patched so this reads the same whether or not the `local` extra
    is installed — otherwise the test would pass on a dev box and fail in CI,
    which installs `[dev]` only.
    """
    from methodos.providers import make_reranker
    from methodos.providers.rerank_cross_encoder import CrossEncoderRerank

    monkeypatch.delenv("METHODOS_RERANK_PROVIDER", raising=False)
    with patch("methodos.providers.find_spec", return_value=object()):
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


# --- transcription ---------------------------------------------------------


def test_fake_transcriber_satisfies_the_protocol():
    from methodos.providers.base import TranscriptionProvider
    from tests.conftest import FakeTranscriber

    assert isinstance(FakeTranscriber(), TranscriptionProvider)


def test_faster_whisper_satisfies_the_protocol_without_loading_anything():
    from methodos.providers.base import TranscriptionProvider
    from methodos.providers.transcribe_whisper import FasterWhisperTranscriber

    t = FasterWhisperTranscriber(model_name="small")
    assert isinstance(t, TranscriptionProvider)
    assert t.name == "faster-whisper:small"
    assert t._model is None


def test_make_transcriber_is_on_by_default(monkeypatch):
    from methodos.providers import make_transcriber
    from methodos.providers.transcribe_whisper import FasterWhisperTranscriber

    monkeypatch.delenv("METHODOS_TRANSCRIBE_PROVIDER", raising=False)
    with patch("methodos.providers.find_spec", return_value=object()) as fs:
        assert isinstance(make_transcriber(Settings(_env_file=None)), FasterWhisperTranscriber)
    fs.assert_called_once_with("faster_whisper")


def test_make_transcriber_degrades_when_the_extra_is_missing(monkeypatch):
    """Documents must keep working on a server without the `transcribe` extra."""
    from methodos.providers import make_transcriber

    monkeypatch.delenv("METHODOS_TRANSCRIBE_PROVIDER", raising=False)
    with patch("methodos.providers.find_spec", return_value=None):
        assert make_transcriber(Settings(_env_file=None)) is None


def test_make_transcriber_raises_when_required_but_missing(monkeypatch):
    from methodos.providers import make_transcriber
    from methodos.providers.base import TranscriptionError

    monkeypatch.delenv("METHODOS_TRANSCRIBE_PROVIDER", raising=False)
    with (
        patch("methodos.providers.find_spec", return_value=None),
        pytest.raises(TranscriptionError, match="transcribe"),
    ):
        make_transcriber(Settings(_env_file=None), required=True)


def test_make_transcriber_returns_none_when_disabled(monkeypatch):
    from methodos.providers import make_transcriber

    monkeypatch.setenv("METHODOS_TRANSCRIBE_PROVIDER", "none")
    assert make_transcriber(Settings(_env_file=None)) is None


def _segment(text):
    s = MagicMock()
    s.text = text
    return s


def test_whisper_refuses_a_long_recording_before_loading_the_model(tmp_path):
    from methodos.providers import transcribe_whisper as tw
    from methodos.providers.base import MediaTooLongError

    with (
        patch.object(tw, "_probe_duration", return_value=3600.0),
        patch.object(tw, "_load_whisper") as load,
        pytest.raises(MediaTooLongError, match="60 minutes"),
    ):
        tw.FasterWhisperTranscriber().transcribe(tmp_path / "a.mp3", max_seconds=1200)
    load.assert_not_called()


def test_whisper_joins_segments_and_reports_the_language(tmp_path):
    from methodos.providers import transcribe_whisper as tw

    model = MagicMock()
    info = MagicMock(duration=42.0, language="de")
    model.transcribe.return_value = (
        iter([_segment(" Erstens "), _segment(""), _segment("zweitens.")]),
        info,
    )
    with (
        patch.object(tw, "_probe_duration", return_value=42.0),
        patch.object(tw, "_load_whisper", return_value=model),
    ):
        t = tw.FasterWhisperTranscriber().transcribe(tmp_path / "a.mp3", max_seconds=1200)
    assert t.text == "Erstens zweitens."
    assert t.language == "de"
    assert t.duration_seconds == 42.0


def test_whisper_checks_the_decoded_length_when_the_header_has_none(tmp_path):
    from methodos.providers import transcribe_whisper as tw
    from methodos.providers.base import MediaTooLongError

    model = MagicMock()
    model.transcribe.return_value = (iter([]), MagicMock(duration=5000.0, language="de"))
    with (
        patch.object(tw, "_probe_duration", return_value=None),
        patch.object(tw, "_load_whisper", return_value=model),
        pytest.raises(MediaTooLongError),
    ):
        tw.FasterWhisperTranscriber().transcribe(tmp_path / "a.mp3", max_seconds=1200)


def test_whisper_wraps_backend_failures(tmp_path):
    from methodos.providers import transcribe_whisper as tw
    from methodos.providers.base import TranscriptionError

    model = MagicMock()
    model.transcribe.side_effect = RuntimeError("decoder exploded")
    with (
        patch.object(tw, "_probe_duration", return_value=10.0),
        patch.object(tw, "_load_whisper", return_value=model),
        pytest.raises(TranscriptionError, match="decoder exploded"),
    ):
        tw.FasterWhisperTranscriber().transcribe(tmp_path / "a.mp3", max_seconds=1200)


def test_whisper_that_will_not_load_is_unavailable_not_a_bad_file(tmp_path):
    from methodos.providers import transcribe_whisper as tw
    from methodos.providers.base import TranscriberUnavailableError

    with (
        patch.object(tw, "_probe_duration", return_value=10.0),
        patch.object(tw, "_load_whisper", side_effect=OSError("no such model")),
        pytest.raises(TranscriberUnavailableError, match="no such model"),
    ):
        tw.FasterWhisperTranscriber().transcribe(tmp_path / "a.mp3", max_seconds=1200)


def test_faster_whisper_can_decode_with_the_installed_pyav(tmp_path):
    """faster-whisper and PyAV must agree on av.open()'s signature.

    PyAV 19 dropped an argument faster-whisper 1.2.1 still passes, which broke
    every transcription in the Docker image while a 3.11 dev box (av 18) was
    fine. No model is loaded: decoding a generated tone exercises exactly the
    call that broke. Skipped where the `transcribe` extra is not installed.
    """
    import math
    import struct
    import wave

    pytest.importorskip("faster_whisper")
    from faster_whisper.audio import decode_audio

    from methodos.providers.transcribe_whisper import _probe_duration

    path = tmp_path / "tone.wav"
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(
            b"".join(
                struct.pack("<h", int(8000 * math.sin(2 * math.pi * 440 * i / 16000)))
                for i in range(16000)
            )
        )
    assert len(decode_audio(str(path))) == 16000
    assert _probe_duration(path) == pytest.approx(1.0, abs=0.05)
