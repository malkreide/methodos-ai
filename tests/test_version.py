"""The version lives in two hand-maintained places; keep them equal.

`pyproject.toml` and `src/methodos/__init__.py` each declare it, and nothing
tied them together — which is how main came to say 0.1.0 while the newest tag
said v0.3.1 and `methodos --version` happily printed the stale number. These
tests are the tie.

Deliberately stdlib-only (`tomllib` ships with 3.11, our floor): CI installs
`.[dev]` and nothing more, so a version guard must not reach for an extra.
Reading the file rather than `importlib.metadata.version("methodos")` is also
on purpose — an editable install keeps serving the metadata captured at install
time, so that route passes in fresh CI and fails locally until you reinstall.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

from typer.testing import CliRunner

import methodos

REPO_ROOT = Path(__file__).resolve().parent.parent


def _pyproject_version() -> str:
    data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return str(data["project"]["version"])


def test_pyproject_and_package_version_agree():
    assert methodos.__version__ == _pyproject_version(), (
        "pyproject.toml and src/methodos/__init__.py disagree — bump both, in the same commit"
    )


def test_version_is_semver():
    """A tag is cut from this string, so it has to be tag-shaped."""
    assert re.fullmatch(r"\d+\.\d+\.\d+", methodos.__version__), methodos.__version__


def test_cli_reports_the_declared_version():
    """`methodos --version` is the third copy — the one users actually read."""
    from methodos.cli import app

    res = CliRunner().invoke(app, ["--version"])
    assert res.exit_code == 0, res.stdout
    assert methodos.__version__ in res.stdout
