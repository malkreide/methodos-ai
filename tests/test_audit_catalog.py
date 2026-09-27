"""The curator agent's backlog: deterministic, reproducible, offline."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).parent.parent
SCRIPT = REPO / "scripts" / "audit_catalog.py"

_spec = importlib.util.spec_from_file_location("audit_catalog", SCRIPT)
assert _spec and _spec.loader
audit_catalog = importlib.util.module_from_spec(_spec)
sys.modules["audit_catalog"] = audit_catalog
_spec.loader.exec_module(audit_catalog)

TODAY = date(2026, 9, 27)


def _write(dir: Path, id: str, **extra: object) -> None:
    payload = {
        "id": id,
        "name": id,
        "category": "strategy",
        "use_case": "x" * 50,
        "strengths": ["a"],
        "weaknesses": ["b"],
        "complexity_score": 1,
        "estimated_duration": {"min_minutes": 5, "max_minutes": 10},
        **extra,
    }
    (dir / f"{id}.json").write_text(json.dumps(payload), encoding="utf-8")
    (dir / f"{id}.md").write_text(f"# {id}\n", encoding="utf-8")


COMPLETE = {
    "use_cases": ["y" * 50],
    "contexts": ["business"],
    "formats": ["in-person"],
    "owner": "Hayal Özkan",
    "last_reviewed": "2026-06-01",
}


def _kinds(findings, method_id):
    return {f.kind for f in findings if f.method_id == method_id}


def test_a_complete_recent_method_has_no_findings(tmp_path):
    _write(tmp_path, "Done", **COMPLETE)
    assert audit_catalog.audit(methods_dir=tmp_path, feedback_path=None, today=TODAY) == []


def test_a_bare_method_reports_every_gap(tmp_path):
    _write(tmp_path, "Bare")
    kinds = _kinds(
        audit_catalog.audit(methods_dir=tmp_path, feedback_path=None, today=TODAY), "Bare"
    )
    assert kinds == {"never-reviewed", "unclassified", "single-use-case", "no-owner"}


def test_review_older_than_the_limit_is_stale(tmp_path):
    _write(tmp_path, "Old", **{**COMPLETE, "last_reviewed": "2025-01-01"})
    findings = audit_catalog.audit(methods_dir=tmp_path, feedback_path=None, today=TODAY)
    assert [f.kind for f in findings] == ["stale"]
    assert "2025-01-01" in findings[0].detail


def test_low_ratings_rank_first_and_need_enough_votes(tmp_path):
    _write(tmp_path, "Liked", **COMPLETE)
    _write(tmp_path, "Disliked", **COMPLETE)
    _write(tmp_path, "Unproven", **COMPLETE)
    log = tmp_path / "feedback.jsonl"
    events = [("Disliked", 1), ("Disliked", 2), ("Disliked", 2), ("Unproven", 1), ("Liked", 5)]
    log.write_text(
        "".join(
            json.dumps(
                {
                    "event": "rating",
                    "timestamp": "2026-09-01T00:00:00Z",
                    "query_id": None,
                    "method_id": mid,
                    "rating": r,
                }
            )
            + "\n"
            for mid, r in events
        ),
        encoding="utf-8",
    )
    _write(tmp_path, "Bare")
    findings = audit_catalog.audit(methods_dir=tmp_path, feedback_path=log, today=TODAY)
    assert findings[0].method_id == "Disliked" and findings[0].kind == "low-rating"
    assert "low-rating" not in _kinds(findings, "Unproven"), "one vote is not a signal"


def test_cli_emits_json_for_agents(tmp_path):
    _write(tmp_path, "Bare")
    res = subprocess.run(
        [sys.executable, str(SCRIPT), "--methods-dir", str(tmp_path), "--json"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stderr
    kinds = {f["kind"] for f in json.loads(res.stdout)}
    assert "never-reviewed" in kinds


def test_cli_runs_against_the_shipped_catalog():
    res = subprocess.run([sys.executable, str(SCRIPT)], cwd=REPO, capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
    assert res.stdout.startswith(("# Catalog audit", "All "))
