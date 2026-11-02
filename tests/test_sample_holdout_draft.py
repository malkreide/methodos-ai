"""The practice draft for holdout_from_log: the right shape, solvable, never real."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).parent.parent
SCRIPT = REPO / "scripts" / "sample_holdout_draft.py"

_spec = importlib.util.spec_from_file_location("sample_holdout_draft", SCRIPT)
assert _spec and _spec.loader
practice = importlib.util.module_from_spec(_spec)
sys.modules["sample_holdout_draft"] = practice
_spec.loader.exec_module(practice)
holdout = practice.holdout


def _write(tmp_path: Path, solved: bool) -> Path:
    path = tmp_path / ("solved.json" if solved else "practice.json")
    path.write_text(json.dumps(practice.build(solved), ensure_ascii=False), encoding="utf-8")
    return path


def test_the_exercise_looks_like_what_extract_writes():
    entries = practice.build(solved=False)
    assert len(entries) == len(practice.PROBLEMS)
    for e in entries:
        assert set(e) == {"query", "asked", "flags", "keep", "acceptable", "goal", "practice"}
        assert (e["keep"], e["acceptable"], e["goal"], e["practice"]) == (False, [], None, True)
    kinds = {f.split(":")[0] for e in entries for f in e["flags"]}
    assert {"e-mail address", "phone number", "salutation with a name", "possible name"} <= kinds
    assert [e["asked"] for e in entries] == sorted((e["asked"] for e in entries), reverse=True)


def test_every_kept_solution_passes_the_check():
    """Catches a method renamed or a goal dropped that would leave the example
    teaching an answer `add` no longer takes."""
    ids, goals = holdout._catalog_ids(), holdout._console_goals()
    kept = [e for e in practice.build(solved=True) if e["keep"]]
    assert kept
    for e in kept:
        assert holdout.check(e, ids, goals) == [], e["query"]
        assert not [f for f in holdout.flags(e["query"]) if not f.startswith("possible name")]


def test_practice_entries_never_reach_the_real_holdout(tmp_path, monkeypatch):
    real = tmp_path / "search_queries_holdout_log.json"
    monkeypatch.setattr(holdout, "TARGET", real)
    n, errors = holdout.add(_write(tmp_path, solved=True), real)
    assert n == 0
    assert any("practice entry" in e for e in errors)
    assert not real.exists()


def test_the_solution_goes_into_a_file_of_its_own(tmp_path):
    own = tmp_path / "practice_holdout.json"
    n, errors = holdout.add(_write(tmp_path, solved=False), own)
    assert (n, errors) == (0, []), "the exercise keeps nothing until someone reviews it"

    n, errors = holdout.add(_write(tmp_path, solved=True), own)
    kept = sum(1 for e in practice.build(solved=True) if e["keep"])
    assert n == kept - 1, "the one already in the benchmark is skipped"
    assert any("already in a benchmark file" in e for e in errors)
    assert len(json.loads(own.read_text(encoding="utf-8"))) == n


@pytest.mark.parametrize("where", ["existing", "repository"])
def test_never_written_over_a_file_or_into_the_repository(tmp_path, monkeypatch, where):
    out = tmp_path / "taken.json" if where == "existing" else REPO / "practice_not_here.json"
    if where == "existing":
        out.write_text("keep me\n", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["sample_holdout_draft.py", str(out)])
    assert practice.main() == 1
    if where == "existing":
        assert out.read_text(encoding="utf-8") == "keep me\n"
    else:
        assert not out.exists()
