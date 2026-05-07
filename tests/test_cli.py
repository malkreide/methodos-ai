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
