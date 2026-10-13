"""The data scripts/verify_goals.py measures with: labels and translations that fit."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from methodos.cli import _console_goals

REPO = Path(__file__).parent.parent
SCRIPT = REPO / "scripts" / "verify_goals.py"

_spec = importlib.util.spec_from_file_location("verify_goals", SCRIPT)
assert _spec and _spec.loader
verify_goals = importlib.util.module_from_spec(_spec)
sys.modules["verify_goals"] = verify_goals
_spec.loader.exec_module(verify_goals)


def _load(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("lang", ["de", "en"])
def test_every_goal_has_a_sentence_in_each_language(lang):
    assert set(verify_goals.goal_sentences(lang)) == set(_console_goals())


@pytest.mark.parametrize("de, en", list(zip(*verify_goals.FILES.values(), strict=True)))
def test_the_english_files_translate_the_german_ones_and_nothing_else(de, en):
    """Same problems in the same order: only `query` may differ, so a result
    that differs between the languages is the language's doing."""
    de_cases, en_cases = _load(de), _load(en)
    assert len(de_cases) == len(en_cases)
    for d, e in zip(de_cases, en_cases, strict=True):
        assert (d["acceptable"], d["goal"]) == (e["acceptable"], e["goal"]), d["query"]


@pytest.mark.parametrize("path", [p for ps in verify_goals.FILES.values() for p in ps])
def test_every_label_is_a_goal_the_console_offers(path):
    offered = set(_console_goals())
    for case in _load(path):
        assert "goal" in case, f"{case['query']}: label it, or null when no goal fits"
        assert case["goal"] is None or case["goal"] in offered, case
