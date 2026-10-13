"""The invented log behind `methodos goals`: reproducible, readable, never real."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from methodos.feedback import goal_stats

REPO = Path(__file__).parent.parent
SCRIPT = REPO / "scripts" / "sample_goal_log.py"

_spec = importlib.util.spec_from_file_location("sample_goal_log", SCRIPT)
assert _spec and _spec.loader
sample_goal_log = importlib.util.module_from_spec(_spec)
sys.modules["sample_goal_log"] = sample_goal_log
_spec.loader.exec_module(sample_goal_log)


def _write(tmp_path: Path, questions: int = 60, seed: int = 7) -> Path:
    out = tmp_path / f"sample-{questions}-{seed}.jsonl"
    out.write_text("\n".join(sample_goal_log.build(questions, seed)) + "\n", encoding="utf-8")
    return out


def test_the_report_has_something_in_every_part(tmp_path):
    log = _write(tmp_path)
    g = goal_stats(log)
    assert g.asked == 60
    assert 0 < g.answered < g.asked
    assert g.back > 0
    events = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines()]
    searches = [e for e in events if e["event"] == "recommendation"]
    old = [e for e in searches if "clarify" not in e]
    assert old, "some lines predate the fields, as in a log that has been running"
    assert g.recorded == len(searches) - len(old)
    assert "anticipate" not in g.rows, "one goal is never picked, so that line shows"
    assert any(r.ratings for r in g.rows.values()) and any(r.before for r in g.rows.values())


def test_every_goal_the_sample_knows_is_one_the_console_offers():
    """A goal renamed in the console would otherwise leave the sample picking a
    key no one can click, and its queries without the sentence."""
    from methodos.cli import _console_goals

    assert set(sample_goal_log.PROFILES) == set(_console_goals())
    assert set(sample_goal_log.goal_sentences()) == set(_console_goals())


def test_same_seed_same_log_other_seed_other_log():
    assert sample_goal_log.build(20, 7) == sample_goal_log.build(20, 7)
    assert sample_goal_log.build(20, 7) != sample_goal_log.build(20, 8)


def test_every_search_is_marked_as_sample_data(tmp_path):
    for line in _write(tmp_path, questions=10).read_text(encoding="utf-8").splitlines():
        event = json.loads(line)
        if event["event"] == "recommendation":
            assert event["model"] == "sample-data"


def test_few_questions_trigger_the_anecdote_warning(tmp_path, monkeypatch):
    from typer.testing import CliRunner

    from methodos.cli import app

    monkeypatch.setenv("METHODOS_FEEDBACK_PATH", str(_write(tmp_path, questions=12)))
    res = CliRunner().invoke(app, ["goals"])
    assert res.exit_code == 0
    assert "Asked on 12 of" in res.stdout
    assert "anecdotes" in res.stdout


@pytest.mark.parametrize("target", ["existing", "configured"])
def test_never_writes_over_a_file_or_the_real_log(tmp_path, monkeypatch, target):
    real = tmp_path / "feedback.jsonl"
    monkeypatch.setenv("METHODOS_FEEDBACK_PATH", str(real))
    out = tmp_path / "taken.jsonl" if target == "existing" else real
    if target == "existing":
        out.write_text("keep me\n", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["sample_goal_log.py", str(out)])
    assert sample_goal_log.main() == 1
    if target == "existing":
        assert out.read_text(encoding="utf-8") == "keep me\n"
    else:
        assert not out.exists()
