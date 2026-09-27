"""The curator agent's backlog: deterministic, reproducible, offline."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

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


def test_a_dropped_connection_is_a_broken_link_not_a_crash(monkeypatch):
    """One site closing the socket must not take the whole weekly audit down."""
    import http.client

    def drop(*_a, **_k):
        raise http.client.RemoteDisconnected("Remote end closed connection without response")

    monkeypatch.setattr(audit_catalog.urllib.request, "urlopen", drop)
    assert audit_catalog._link_ok("https://example.org/x", timeout=1) is False


class _Response:
    def __init__(self, url: str, status: int = 200) -> None:
        self._url, self.status = url, status

    def geturl(self) -> str:
        return self._url

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False


@pytest.mark.parametrize(
    ("requested", "landed", "ok"),
    [
        # A deep page swallowed by a site's generic landing page: gone.
        (
            "https://www.toyota-global.com/company/toyota_traditions/quality/mar_apr_2006.html",
            "https://global.toyota/en/company/",
            False,
        ),
        # Routine redirects that keep the content: fine.
        ("http://example.org/a/b", "https://example.org/a/b", True),
        ("https://example.org/a/b", "https://www.example.org/a/b/", True),
        ("https://old.example.org/guide/moscow", "https://new.example.com/guide/moscow-2", True),
    ],
)
def test_redirect_to_a_generic_page_counts_as_broken(monkeypatch, requested, landed, ok):
    monkeypatch.setattr(
        audit_catalog.urllib.request, "urlopen", lambda *_a, **_k: _Response(landed)
    )
    assert audit_catalog._link_ok(requested, timeout=1) is ok


@pytest.mark.parametrize("code", [301, 302, 307, 308])
def test_a_redirect_loop_is_a_broken_link(monkeypatch, code):
    """urllib gives up on a redirect loop with an HTTPError carrying the 3xx code.

    Treating it like a refused HEAD (any non-404) passed the UXBooth Kano page,
    which redirects between its slash and no-slash forms forever.
    """
    import urllib.error

    def loop(req, **_k):
        raise urllib.error.HTTPError(
            req.full_url, code, "redirect error that would lead to an infinite loop", {}, None
        )

    monkeypatch.setattr(audit_catalog.urllib.request, "urlopen", loop)
    assert audit_catalog._link_ok("https://example.org/x", timeout=1) is False
