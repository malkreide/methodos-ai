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


# --- goal_stats: what people did with the console's question back ------------


def _search(fb, query, ids, *, clarify=None, goal=None, refines=None):
    return log_recommendation(
        query=query,
        method_ids=ids,
        model="m",
        path=fb,
        clarify=clarify,
        goal=goal,
        refines=refines,
    )


def test_goal_stats_counts_questions_answers_and_ratings(tmp_path):
    from methodos.feedback import goal_stats

    fb = tmp_path / "fb.jsonl"
    # Asked, and two goals tried; the first place before them is rated on the
    # original search (the card the console keeps on screen).
    a = _search(fb, "Sommerfest", ["World_Cafe", "AAR"], clarify=True)
    a_learn = _search(
        fb, "Sommerfest +learn", ["AAR", "World_Cafe"], clarify=True, goal="learn", refines=a
    )
    _search(
        fb, "Sommerfest +cause", ["World_Cafe", "Five_Whys"], clarify=False, goal="cause", refines=a
    )
    _search(fb, "Sommerfest", ["World_Cafe", "AAR"], clarify=True, refines=a)  # back, no goal
    log_rating(method_id="AAR", rating=5, note=None, query_id=a_learn, path=fb)
    log_rating(method_id="World_Cafe", rating=2, note=None, query_id=a, path=fb)
    # Asked, no goal picked; not asked; and the CLI, which records nothing.
    _search(fb, "Elternabend", ["X", "Y"], clarify=True)
    _search(fb, "RACI", ["RACI_Matrix", "Y"], clarify=False)
    _search(fb, "cli query", ["X", "Y"])

    g = goal_stats(fb)
    assert (g.recorded, g.asked, g.answered, g.back) == (6, 2, 1, 1)
    learn, cause = g.rows["learn"], g.rows["cause"]
    assert (learn.clicks, learn.first_changed, learn.ratings, learn.before) == (1, 1, [5], [2])
    assert (cause.clicks, cause.first_changed, cause.ratings, cause.before) == (1, 0, [], [2])


def test_goal_stats_reads_logs_written_before_the_fields_existed(tmp_path):
    """Old lines lack clarify/goal/refines: not recorded, rather than "not asked"."""
    from methodos.feedback import goal_stats

    fb = tmp_path / "fb.jsonl"
    fb.write_text(
        json.dumps(
            {
                "event": "recommendation",
                "timestamp": "2026-10-01T00:00:00Z",
                "query_id": "01HX0000000000000000000000",
                "query": "q",
                "method_ids": ["A"],
                "model": "m",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    g = goal_stats(fb)
    assert (g.recorded, g.asked, g.answered, g.rows) == (0, 0, 0, {})
