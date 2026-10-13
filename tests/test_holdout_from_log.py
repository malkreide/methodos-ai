"""Real searches to holdout problems: only reviewed, anonymised and labelled ones get in."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from methodos.feedback import log_recommendation

REPO = Path(__file__).parent.parent
SCRIPT = REPO / "scripts" / "holdout_from_log.py"

_spec = importlib.util.spec_from_file_location("holdout_from_log", SCRIPT)
assert _spec and _spec.loader
holdout = importlib.util.module_from_spec(_spec)
sys.modules["holdout_from_log"] = holdout
_spec.loader.exec_module(holdout)

TYPED = "Die Lehrpersonen streiten seit Wochen über die neue Pausenaufsicht"


def _log(path: Path, query: str, *, model: str = "m", refines: str | None = None) -> str:
    return log_recommendation(
        query=query, method_ids=["A", "B"], model=model, path=path, clarify=True, refines=refines
    )


def test_extract_keeps_only_what_people_typed(tmp_path):
    log = tmp_path / "feedback.jsonl"
    root = _log(log, TYPED)
    _log(log, "  die lehrpersonen STREITEN seit Wochen über die neue Pausenaufsicht ")
    _log(log, f"{TYPED} Wir wollen einen Konflikt klären.", refines=root)  # a goal, not typed
    _log(log, "Unser Sommerfest ist ein einziges Chaos gewesen", model="sample-data")
    _log(log, "zu kurz hier")
    # Already in search_queries.json, give or take a letter:
    _log(log, "Ich ertrinke in Aufgaben und weiss nicht was ich zuerst erledigen soll")
    _log(log, "Niemand liest die Protokolle unserer Sitzungen")

    entries = holdout.extract(log)
    assert [e["query"] for e in entries] == [
        TYPED,
        "Niemand liest die Protokolle unserer Sitzungen",
    ]
    assert entries[0]["asked"] == 2, "spelling and spacing variants count as one problem"
    for e in entries:
        assert set(e) == {"query", "asked", "flags", "keep", "acceptable", "goal"}, (
            "no timestamps, ids or search results in the draft"
        )
        assert (e["keep"], e["acceptable"], e["goal"]) == (False, [], None)


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Bitte melden unter anna.meier@schule.ch wegen der Klasse", "e-mail address"),
        ("Rückruf an 044 123 45 67 wegen der Elternbeschwerde", "phone number"),
        ("Siehe https://intranet.example/x für die Vorlage dazu", "link"),
        ("Frau Meier beschwert sich über die Hausaufgaben", "salutation with a name"),
        ("Mit der Lehrerin Anna Meier gibt es seit Wochen Streit", "possible name"),
    ],
)
def test_personal_data_is_flagged(text, expected):
    assert any(f.startswith(expected) for f in holdout.flags(text))


def test_a_plain_problem_is_not_flagged():
    assert holdout.flags(TYPED) == []


def _draft(tmp_path: Path, *entries: dict) -> Path:
    path = tmp_path / "draft.json"
    path.write_text(json.dumps(list(entries), ensure_ascii=False), encoding="utf-8")
    return path


GOOD = {"query": TYPED, "keep": True, "acceptable": ["Principled_Negotiation"], "goal": "conflict"}


@pytest.mark.parametrize(
    "change, reason",
    [
        ({"acceptable": []}, "acceptable is empty"),
        ({"acceptable": ["Not_A_Method"]}, "no method with id"),
        ({"goal": "win"}, "not one the console offers"),
        ({"query": "Frau Meier und die neue Pausenaufsicht im Schulhaus"}, "salutation"),
        ({"query": "Mit der Lehrerin Anna Meier gibt es seit Wochen Streit"}, "possible name"),
    ],
)
def test_add_refuses_what_is_not_ready_and_writes_nothing(tmp_path, change, reason):
    target = tmp_path / "holdout.json"
    n, errors = holdout.add(_draft(tmp_path, {**GOOD, **change}), target)
    assert n == 0
    assert any(reason in e for e in errors), errors
    assert not target.exists(), "one bad entry stops the whole batch"


def test_add_appends_reviewed_entries_in_the_benchmark_format(tmp_path):
    target = tmp_path / "holdout.json"
    named = {
        **GOOD,
        "query": "Mit der Lehrerin Anna Meier gibt es seit Wochen Streit",
        "names_checked": True,  # a person decided it is fine
    }
    skipped = {**GOOD, "query": "Niemand liest die Protokolle unserer Sitzungen", "keep": False}
    n, errors = holdout.add(_draft(tmp_path, GOOD, named, skipped), target)
    assert (n, errors) == (2, [])
    saved = json.loads(target.read_text(encoding="utf-8"))
    assert [e["query"] for e in saved] == [GOOD["query"], named["query"]]
    assert set(saved[0]) == {"query", "acceptable", "goal", "added"}

    n, errors = holdout.add(_draft(tmp_path, GOOD), target)
    assert n == 0 and "already in a benchmark file" in errors[0]
    assert len(json.loads(target.read_text(encoding="utf-8"))) == 2


def test_extract_refuses_to_write_the_draft_into_the_repository(tmp_path, monkeypatch):
    log = tmp_path / "feedback.jsonl"
    _log(log, TYPED)
    inside = REPO / "scripts" / "draft_should_not_exist.json"
    monkeypatch.setattr(sys, "argv", ["holdout_from_log.py", "extract", str(log), str(inside)])
    assert holdout.main() == 1
    assert not inside.exists()
