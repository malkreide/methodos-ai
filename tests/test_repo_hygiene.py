"""Properties of the checkout itself, not of the code."""

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]


@pytest.mark.parametrize("path", ["docker/entrypoint.sh", "Dockerfile", "Makefile"])
def test_container_and_shell_files_keep_lf_on_every_platform(path):
    """A Windows checkout with Git's default core.autocrlf=true turns these into
    CRLF unless .gitattributes pins them — and a CRLF entrypoint.sh stops the
    container from starting at all."""
    if shutil.which("git") is None or not (ROOT / ".git").exists():
        pytest.skip("needs a git checkout")
    out = subprocess.run(
        ["git", "check-attr", "eol", "--", path],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert out.strip().endswith("eol: lf"), out
