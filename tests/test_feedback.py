import json

import pytest

from methodos.feedback import (
    RatingEvent,
    log_rating,
    log_recommendation,
    read_events,
    stats,
)


def test_log_recommendation_returns_query_id_and_appends(tmp_path):
    fb = tmp_path / "fb.jsonl"
    qid = log_recommendation(
        query="enter new market",
        method_ids=["SWOT", "Porters_Five_Forces"],
        model="anthropic/claude-3-5-haiku-20241022",
        path=fb,
    )
    assert qid and len(qid) == 26
    lines = fb.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    obj = json.loads(lines[0])
    assert obj["event"] == "recommendation"
    assert obj["query_id"] == qid
    assert obj["method_ids"] == ["SWOT", "Porters_Five_Forces"]


def test_log_rating_appends(tmp_path):
    fb = tmp_path / "fb.jsonl"
    log_rating(method_id="SWOT", rating=4, note="worked well", query_id="01HX", path=fb)
    log_rating(method_id="DACI_Matrix", rating=5, note=None, query_id=None, path=fb)
    lines = fb.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    a, b = json.loads(lines[0]), json.loads(lines[1])
    assert a["event"] == "rating" and a["rating"] == 4 and a["note"] == "worked well"
    assert b["event"] == "rating" and b["query_id"] is None


def test_log_rating_rejects_out_of_range(tmp_path):
    fb = tmp_path / "fb.jsonl"
    with pytest.raises(ValueError):
        log_rating(method_id="SWOT", rating=0, note=None, query_id=None, path=fb)
    with pytest.raises(ValueError):
        log_rating(method_id="SWOT", rating=6, note=None, query_id=None, path=fb)


def test_read_events_skips_corrupt_lines(tmp_path, capsys):
    fb = tmp_path / "fb.jsonl"
    log_rating(method_id="SWOT", rating=3, note=None, query_id=None, path=fb)
    with fb.open("a", encoding="utf-8") as f:
        f.write("this-is-not-json\n")
    log_rating(method_id="DACI_Matrix", rating=4, note=None, query_id=None, path=fb)

    events = list(read_events(fb))
    assert len(events) == 2
    assert all(isinstance(e, RatingEvent) for e in events)
    err = capsys.readouterr().err
    assert "skipped" in err.lower() or "corrupt" in err.lower() or "malformed" in err.lower()


def test_stats_aggregates(tmp_path):
    fb = tmp_path / "fb.jsonl"
    log_recommendation(query="q1", method_ids=["SWOT"], model="m", path=fb)
    log_rating(method_id="SWOT", rating=4, note=None, query_id=None, path=fb)
    log_rating(method_id="SWOT", rating=2, note=None, query_id=None, path=fb)
    log_rating(method_id="DACI_Matrix", rating=5, note=None, query_id=None, path=fb)
    s = stats(fb)
    assert s["SWOT"].rating_count == 2
    assert abs(s["SWOT"].avg_rating - 3.0) < 1e-9
    assert s["SWOT"].recommendation_count == 1
    assert s["DACI_Matrix"].rating_count == 1
