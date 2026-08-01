import json
import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

runner = CliRunner()


class BrokenEmbedding:
    """Embedding provider whose backend is unavailable (e.g. extra not installed)."""

    name = "broken:model"

    @property
    def dimensions(self) -> int:
        from methodos.providers.base import EmbeddingError

        raise EmbeddingError("failed to load model: No module named 'sentence_transformers'")

    def embed(self, texts):
        from methodos.providers.base import EmbeddingError

        raise EmbeddingError("failed to load model: No module named 'sentence_transformers'")


def _seed_methods_fixture(repo_root: Path, dst: Path) -> None:
    """Copy real methods into a temp dir for CLI tests."""
    src = repo_root / "methods"
    dst.mkdir()
    for f in src.iterdir():
        (dst / f.name).write_bytes(f.read_bytes())


def test_version_command():
    from methodos.cli import app

    res = runner.invoke(app, ["--version"])
    assert res.exit_code == 0
    assert "methodos" in res.stdout.lower()


def test_ingest_command_runs(tmp_path, monkeypatch):
    from methodos.cli import app

    repo_root = Path(__file__).parent.parent
    methods = tmp_path / "methods"
    _seed_methods_fixture(repo_root, methods)

    from tests.conftest import FakeEmbedding

    fake = FakeEmbedding(dimensions=8)

    monkeypatch.setenv("METHODOS_CHROMA_PATH", str(tmp_path / "chroma"))

    import methodos.cli as cli_mod

    monkeypatch.setattr(cli_mod, "make_embedding", lambda settings: fake)
    monkeypatch.setattr(cli_mod, "make_reranker", lambda s, **kw: None)

    res = runner.invoke(app, ["ingest", "--methods-dir", str(methods)])
    assert res.exit_code == 0, res.stdout
    assert "ingested" in res.stdout.lower()


def test_query_no_llm_renders_results(tmp_path, monkeypatch):
    from methodos.cli import app

    repo_root = Path(__file__).parent.parent
    methods = tmp_path / "methods"
    _seed_methods_fixture(repo_root, methods)

    from tests.conftest import FakeEmbedding

    fake = FakeEmbedding(dimensions=8)
    import methodos.cli as cli_mod

    monkeypatch.setattr(cli_mod, "make_embedding", lambda s: fake)
    monkeypatch.setattr(cli_mod, "make_reranker", lambda s, **kw: None)
    monkeypatch.setenv("METHODOS_CHROMA_PATH", str(tmp_path / "chroma"))

    runner.invoke(app, ["ingest", "--methods-dir", str(methods)])
    res = runner.invoke(app, ["query", "evaluate strengths and weaknesses", "--no-llm", "-k", "2"])
    assert res.exit_code == 0, res.stdout

    # FakeEmbedding hashes text, so *which* methods rank top is arbitrary and
    # changes whenever the catalog does. Assert on the rendering contract —
    # k panels, each with a similarity and a doc path — not on catalog content.
    # Semantic ranking is the integration suite's job.
    assert res.stdout.count("(sim ") == 2
    assert res.stdout.count("methods/") >= 2
    assert "complexity" in res.stdout


def test_query_with_llm_calls_llm(tmp_path, monkeypatch):
    from methodos.cli import app

    repo_root = Path(__file__).parent.parent
    methods = tmp_path / "methods"
    _seed_methods_fixture(repo_root, methods)

    from tests.conftest import FakeEmbedding, FakeLLM

    fake_e = FakeEmbedding(dimensions=8)
    fake_l = FakeLLM(response="canned explanation")

    import methodos.cli as cli_mod

    monkeypatch.setattr(cli_mod, "make_embedding", lambda s: fake_e)
    monkeypatch.setattr(cli_mod, "make_reranker", lambda s, **kw: None)
    monkeypatch.setattr(cli_mod, "make_llm", lambda s: fake_l)
    monkeypatch.setenv("METHODOS_CHROMA_PATH", str(tmp_path / "chroma"))

    runner.invoke(app, ["ingest", "--methods-dir", str(methods)])
    res = runner.invoke(app, ["query", "decision making for cross-functional teams", "-k", "2"])
    assert res.exit_code == 0, res.stdout
    assert "canned explanation" in res.stdout


REPO_METHODS = str(Path(__file__).parent.parent / "methods")


def test_list_command_shows_all_methods():
    from methodos.cli import app

    res = runner.invoke(app, ["list", "--methods-dir", REPO_METHODS])
    assert res.exit_code == 0
    assert "SWOT" in res.stdout
    assert "DACI" in res.stdout


def test_list_filters_by_category():
    from methodos.cli import app

    res = runner.invoke(
        app, ["list", "--methods-dir", REPO_METHODS, "--category", "decision-making"]
    )
    assert res.exit_code == 0
    assert "DACI" in res.stdout
    assert "SWOT" not in res.stdout


def test_show_renders_markdown():
    from methodos.cli import app

    res = runner.invoke(app, ["show", "SWOT", "--methods-dir", REPO_METHODS])
    assert res.exit_code == 0
    assert "SWOT" in res.stdout


def test_show_unknown_id_errors():
    from methodos.cli import app

    res = runner.invoke(app, ["show", "Nonexistent", "--methods-dir", REPO_METHODS])
    assert res.exit_code == 1
    assert "Nonexistent" in res.stdout


def test_feedback_command_appends_rating(tmp_path, monkeypatch):
    from methodos.cli import app

    fb = tmp_path / "fb.jsonl"
    monkeypatch.setenv("METHODOS_FEEDBACK_PATH", str(fb))
    res = runner.invoke(app, ["feedback", "SWOT", "--rating", "4", "--note", "great"])
    assert res.exit_code == 0, res.stdout
    line = fb.read_text(encoding="utf-8").splitlines()[0]
    obj = json.loads(line)
    assert obj["method_id"] == "SWOT"
    assert obj["rating"] == 4
    assert obj["note"] == "great"


def test_feedback_command_validates_rating_range(tmp_path, monkeypatch):
    from methodos.cli import app

    monkeypatch.setenv("METHODOS_FEEDBACK_PATH", str(tmp_path / "fb.jsonl"))
    res = runner.invoke(app, ["feedback", "SWOT", "--rating", "9"])
    assert res.exit_code != 0


def test_query_logs_recommendation(tmp_path, monkeypatch):
    from methodos.cli import app

    repo_root = Path(__file__).parent.parent
    methods = tmp_path / "methods"
    _seed_methods_fixture(repo_root, methods)

    from tests.conftest import FakeEmbedding, FakeLLM

    fake_e = FakeEmbedding(dimensions=8)
    fake_l = FakeLLM(response="ok")
    import methodos.cli as cli_mod

    monkeypatch.setattr(cli_mod, "make_embedding", lambda s: fake_e)
    monkeypatch.setattr(cli_mod, "make_reranker", lambda s, **kw: None)
    monkeypatch.setattr(cli_mod, "make_llm", lambda s: fake_l)

    fb = tmp_path / "fb.jsonl"
    monkeypatch.setenv("METHODOS_FEEDBACK_PATH", str(fb))
    monkeypatch.setenv("METHODOS_CHROMA_PATH", str(tmp_path / "chroma"))
    runner.invoke(app, ["ingest", "--methods-dir", str(methods)])
    res = runner.invoke(app, ["query", "decision making for cross-functional teams", "-k", "2"])
    assert res.exit_code == 0
    lines = fb.read_text(encoding="utf-8").splitlines()
    rec_lines = [
        line
        for line in lines
        if '"event": "recommendation"' in line or '"event":"recommendation"' in line
    ]
    assert len(rec_lines) == 1


def test_stats_command_prints_table(tmp_path, monkeypatch):
    from methodos.cli import app

    fb = tmp_path / "fb.jsonl"
    monkeypatch.setenv("METHODOS_FEEDBACK_PATH", str(fb))
    runner.invoke(app, ["feedback", "SWOT", "--rating", "4"])
    runner.invoke(app, ["feedback", "SWOT", "--rating", "5"])
    res = runner.invoke(app, ["stats"])
    assert res.exit_code == 0
    assert "SWOT" in res.stdout


def test_version_reflects_active_model(monkeypatch):
    """--version must show the model the user is actually about to use."""
    from methodos.cli import app

    monkeypatch.setenv("METHODOS_MODEL", "anthropic/claude-3-5-haiku-20241022")
    res = runner.invoke(app, ["--version"])
    assert res.exit_code == 0
    assert "anthropic/claude-3-5-haiku-20241022" in res.stdout


def test_module_entrypoint_dispatches_to_app():
    """`python -m methodos.cli` is the form used by the Makefile and CLAUDE.md.

    Without a __main__ guard the module imports and exits 0 silently, so
    `make ingest` / `make demo` become no-ops.
    """
    res = subprocess.run(
        [sys.executable, "-m", "methodos.cli", "--version"],
        cwd=Path(__file__).parent.parent,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stderr
    assert "methodos" in res.stdout.lower()


def test_ingest_reports_embedding_backend_failure(tmp_path, monkeypatch):
    """A missing embedding backend must print a message, not a traceback."""
    from methodos.cli import app

    repo_root = Path(__file__).parent.parent
    methods = tmp_path / "methods"
    _seed_methods_fixture(repo_root, methods)

    import methodos.cli as cli_mod

    monkeypatch.setattr(cli_mod, "make_embedding", lambda s: BrokenEmbedding())
    monkeypatch.setattr(cli_mod, "make_reranker", lambda s, **kw: None)
    monkeypatch.setenv("METHODOS_CHROMA_PATH", str(tmp_path / "chroma"))

    res = runner.invoke(app, ["ingest", "--methods-dir", str(methods)])
    assert res.exit_code == 2
    assert res.exception is None or isinstance(res.exception, SystemExit)
    assert "sentence_transformers" in res.stdout


def test_query_reports_embedding_backend_failure(tmp_path, monkeypatch):
    """Same for query — the most commonly run command.

    Models an index built earlier, then a backend that stops loading (e.g. the
    venv was recreated without the `local` extra). The provider name matches, so
    the stale-index check passes and the failure lands on the embedding call.
    """
    from methodos.cli import app

    repo_root = Path(__file__).parent.parent
    methods = tmp_path / "methods"
    _seed_methods_fixture(repo_root, methods)

    from tests.conftest import FakeEmbedding

    working = FakeEmbedding(dimensions=8)
    working.name = BrokenEmbedding.name

    import methodos.cli as cli_mod

    monkeypatch.setattr(cli_mod, "make_embedding", lambda s: working)
    monkeypatch.setattr(cli_mod, "make_reranker", lambda s, **kw: None)
    monkeypatch.setenv("METHODOS_CHROMA_PATH", str(tmp_path / "chroma"))
    runner.invoke(app, ["ingest", "--methods-dir", str(methods)])

    monkeypatch.setattr(cli_mod, "make_embedding", lambda s: BrokenEmbedding())
    monkeypatch.setattr(cli_mod, "make_reranker", lambda s, **kw: None)
    res = runner.invoke(app, ["query", "how do we pick a strategy", "--no-llm"])
    assert res.exit_code == 2
    assert res.exception is None or isinstance(res.exception, SystemExit)
    assert "sentence_transformers" in res.stdout


def test_query_reports_llm_failure(tmp_path, monkeypatch):
    """An LLM backend failure must not surface as a traceback either."""
    from methodos.cli import app
    from methodos.providers.base import LLMError

    repo_root = Path(__file__).parent.parent
    methods = tmp_path / "methods"
    _seed_methods_fixture(repo_root, methods)

    from tests.conftest import FakeEmbedding

    class BrokenLLM:
        name = "broken-llm"

        def complete(self, system, user, *, max_tokens=1024, temperature=0.2):
            raise LLMError("APIConnectionError: ollama not running")

    import methodos.cli as cli_mod

    monkeypatch.setattr(cli_mod, "make_embedding", lambda s: FakeEmbedding(dimensions=8))
    monkeypatch.setattr(cli_mod, "make_reranker", lambda s, **kw: None)
    monkeypatch.setenv("METHODOS_CHROMA_PATH", str(tmp_path / "chroma"))
    runner.invoke(app, ["ingest", "--methods-dir", str(methods)])

    monkeypatch.setattr(cli_mod, "make_llm", lambda s: BrokenLLM())
    res = runner.invoke(app, ["query", "how do we pick a strategy", "-k", "2"])
    assert res.exit_code == 2
    assert res.exception is None or isinstance(res.exception, SystemExit)
    assert "ollama not running" in res.stdout


def test_query_renders_the_rerank_score_when_a_reranker_runs(tmp_path, monkeypatch):
    """Both scores reach the panel; the reranker decides the order."""
    from methodos.cli import app

    repo_root = Path(__file__).parent.parent
    methods = tmp_path / "methods"
    _seed_methods_fixture(repo_root, methods)

    import methodos.cli as cli_mod
    from tests.conftest import FakeEmbedding, FakeReranker

    monkeypatch.setattr(cli_mod, "make_embedding", lambda s: FakeEmbedding(dimensions=8))
    monkeypatch.setattr(cli_mod, "make_reranker", lambda s, **kw: None)
    monkeypatch.setenv("METHODOS_CHROMA_PATH", str(tmp_path / "chroma"))
    runner.invoke(app, ["ingest", "--methods-dir", str(methods)])

    monkeypatch.setattr(cli_mod, "make_reranker", lambda s, **kw: FakeReranker())
    res = runner.invoke(app, ["query", "decision approval authority", "--no-llm", "-k", "2"])
    assert res.exit_code == 0, res.stdout
    assert "rerank" in res.stdout, "the rerank score must be visible next to sim"
    assert res.stdout.count("sim ") == 2


def test_query_reports_when_reranking_is_unavailable(tmp_path, monkeypatch):
    """Default-on reranking degrades quietly, but the user is told."""
    from methodos.cli import app

    repo_root = Path(__file__).parent.parent
    methods = tmp_path / "methods"
    _seed_methods_fixture(repo_root, methods)

    import methodos.cli as cli_mod
    from tests.conftest import FakeEmbedding

    monkeypatch.setattr(cli_mod, "make_embedding", lambda s: FakeEmbedding(dimensions=8))
    monkeypatch.setattr(cli_mod, "make_reranker", lambda s, **kw: None)
    monkeypatch.setenv("METHODOS_CHROMA_PATH", str(tmp_path / "chroma"))
    runner.invoke(app, ["ingest", "--methods-dir", str(methods)])

    res = runner.invoke(app, ["query", "anything at all", "--no-llm", "-k", "2"])
    assert res.exit_code == 0, res.stdout
    assert "Reranking unavailable" in res.stdout


def test_query_reports_explicit_rerank_that_cannot_run(tmp_path, monkeypatch):
    """`--rerank` without the dependency must be a clean exit 2, not a traceback.

    make_reranker raises at construction, outside the search() call, so it needs
    its own guard — the same gap that used to let EmbeddingError escape.
    """
    import methodos.cli as cli_mod
    from methodos.cli import app
    from methodos.providers.base import RerankError

    def _boom(settings, **kw):
        raise RerankError("cross-encoder reranking needs sentence-transformers")

    monkeypatch.setattr(cli_mod, "make_reranker", _boom)
    monkeypatch.setenv("METHODOS_CHROMA_PATH", str(tmp_path / "chroma"))

    res = runner.invoke(app, ["query", "anything", "--no-llm", "--rerank"])
    assert res.exit_code == 2
    assert res.exception is None or isinstance(res.exception, SystemExit)
    assert "sentence-transformers" in res.stdout


def test_error_messages_survive_rich_markup(tmp_path, monkeypatch):
    """`[local]` in an error is a Rich tag unless escaped — and it got eaten once.

    The install hint is the whole value of that message, so assert the brackets
    reach stdout intact.
    """
    import methodos.cli as cli_mod
    from methodos.cli import app
    from methodos.providers.base import RerankError

    def _boom(settings, **kw):
        raise RerankError('needs sentence-transformers: pip install -e ".[local]"')

    monkeypatch.setattr(cli_mod, "make_reranker", _boom)
    monkeypatch.setenv("METHODOS_CHROMA_PATH", str(tmp_path / "chroma"))

    res = runner.invoke(app, ["query", "anything", "--no-llm", "--rerank"])
    assert res.exit_code == 2
    assert ".[local]" in res.stdout, f"markup ate the hint: {res.stdout!r}"


def test_invalid_settings_name_the_offending_field(monkeypatch):
    """`METHODOS_OVERFETCH_FACTOR=0` used to exit 1 with a raw pydantic traceback.

    The field name is the whole payload of the message — without it you know the
    config is wrong but not which knob, so assert on it rather than on exit 2 alone.
    """
    from methodos.cli import app

    monkeypatch.setenv("METHODOS_OVERFETCH_FACTOR", "0")

    res = runner.invoke(app, ["query", "x", "--no-llm"])
    assert res.exit_code == 2
    assert res.exception is None or isinstance(res.exception, SystemExit)
    assert "overfetch_factor" in res.stdout
    assert "METHODOS_OVERFETCH_FACTOR" in res.stdout
    assert "Traceback" not in res.stdout


def test_invalid_settings_report_every_bad_field(monkeypatch):
    """Fixing one env var at a time is a slow loop; list them all in one pass."""
    from methodos.cli import app

    monkeypatch.setenv("METHODOS_OVERFETCH_FACTOR", "0")
    monkeypatch.setenv("METHODOS_TOP_K", "0")
    monkeypatch.setenv("METHODOS_EMBEDDING_PROVIDER", "elasticsearch")

    res = runner.invoke(app, ["stats"])
    assert res.exit_code == 2
    for field in ("overfetch_factor", "top_k", "embedding_provider"):
        assert field in res.stdout, f"{field} missing from: {res.stdout!r}"


@pytest.mark.parametrize(
    "argv",
    [
        ["--version"],
        ["ingest"],
        ["query", "x", "--no-llm"],
        ["feedback", "SWOT", "-r", "4"],
        ["stats"],
    ],
    ids=["version", "ingest", "query", "feedback", "stats"],
)
def test_every_command_reports_bad_settings_the_same_way(argv, monkeypatch, tmp_path):
    """Each command builds its own Settings, so each is its own chance to regress.

    `ingest` and `query` must fail here *before* touching a provider — a config
    error should never surface as a missing-model error from sentence-transformers.
    """
    from methodos.cli import app

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("METHODOS_TOP_K", "not-a-number")

    res = runner.invoke(app, argv)
    assert res.exit_code == 2, f"{argv} -> {res.exit_code}: {res.stdout!r}"
    assert "Invalid configuration" in res.stdout
    assert "top_k" in res.stdout


def test_settings_errors_survive_rich_markup(monkeypatch):
    """Same trap as the RerankError hint: a bracketed *value* is Rich markup.

    `METHODOS_EMBEDDING_PROVIDER='[local]'` is exactly the typo a reader of the
    install docs makes, and swallowing the brackets hides what they actually set.
    """
    from methodos.cli import app

    monkeypatch.setenv("METHODOS_EMBEDDING_PROVIDER", "[local]")

    res = runner.invoke(app, ["stats"])
    assert res.exit_code == 2
    assert "[local]" in res.stdout, f"markup ate the value: {res.stdout!r}"
