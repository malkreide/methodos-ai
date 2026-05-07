from pathlib import Path

from typer.testing import CliRunner

runner = CliRunner()


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
    monkeypatch.setenv("METHODOS_CHROMA_PATH", str(tmp_path / "chroma"))

    runner.invoke(app, ["ingest", "--methods-dir", str(methods)])
    res = runner.invoke(app, ["query", "evaluate strengths and weaknesses", "--no-llm", "-k", "2"])
    assert res.exit_code == 0, res.stdout
    assert any(name in res.stdout for name in ("SWOT", "Porter", "DACI"))


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
    monkeypatch.setattr(cli_mod, "make_llm", lambda s: fake_l)
    monkeypatch.setenv("METHODOS_CHROMA_PATH", str(tmp_path / "chroma"))

    runner.invoke(app, ["ingest", "--methods-dir", str(methods)])
    res = runner.invoke(app, ["query", "decision making for cross-functional teams", "-k", "2"])
    assert res.exit_code == 0, res.stdout
    assert "canned explanation" in res.stdout
