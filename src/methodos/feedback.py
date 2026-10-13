"""Feedback loop placeholder — append-only JSONL of recommendations and ratings.

Designed to outgrow itself: when volume justifies it, a one-shot import script
turns this file into a SQLite database without changing the writer API. Until
then, JSONL gives us crash-safety, git-friendly diffs, and trivial concurrent
appends.

Privacy: `RecommendationEvent.query` and `RatingEvent.note` are free text typed
by users and stored verbatim — whatever personal data someone types ends up
here. Every surface that writes them says so to the person typing (console,
OpenAPI descriptions, CLI help); see "Privacy" in the README for operators.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field
from ulid import ULID


def _now_iso() -> str:
    return datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class RecommendationEvent(BaseModel):
    event: Literal["recommendation"] = "recommendation"
    timestamp: str
    query_id: str
    query: str
    method_ids: list[str]
    model: str
    # The console's question back (`clarify`) and what people did with it; see
    # goal_stats(). None on `clarify` means not recorded — lines written before
    # these fields existed, and the CLI, which never asks — not "not asked".
    clarify: bool | None = None
    goal: str | None = None
    refines: str | None = None


class RatingEvent(BaseModel):
    event: Literal["rating"] = "rating"
    timestamp: str
    query_id: str | None
    method_id: str
    rating: int = Field(ge=1, le=5)
    note: str | None = None


FeedbackEvent = RecommendationEvent | RatingEvent


def _append_line(path: Path, payload: BaseModel) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = payload.model_dump_json() + "\n"
    try:
        import fcntl  # type: ignore[import-not-found,unused-ignore]

        with path.open("a", encoding="utf-8") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # type: ignore[attr-defined,unused-ignore]
            try:
                f.write(line)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # type: ignore[attr-defined,unused-ignore]
    except ImportError:
        with path.open("a", encoding="utf-8") as f:
            f.write(line)


def log_recommendation(
    *,
    query: str,
    method_ids: list[str],
    model: str,
    path: Path,
    clarify: bool | None = None,
    goal: str | None = None,
    refines: str | None = None,
) -> str:
    """Append a recommendation event. Returns the freshly-minted query_id (ULID).

    `refines` is the query_id of the search this one builds on, when the person
    picked a goal (`goal`) or went back to the problem as typed (no `goal`).
    """
    qid = str(ULID())
    ev = RecommendationEvent(
        timestamp=_now_iso(),
        query_id=qid,
        query=query,
        method_ids=method_ids,
        model=model,
        clarify=clarify,
        goal=goal,
        refines=refines,
    )
    _append_line(path, ev)
    return qid


def log_rating(
    *,
    method_id: str,
    rating: int,
    note: str | None,
    query_id: str | None,
    path: Path,
) -> None:
    """Append a rating event. Validates rating in [1, 5]."""
    if rating < 1 or rating > 5:
        raise ValueError(f"rating must be 1..5, got {rating}")
    ev = RatingEvent(
        timestamp=_now_iso(),
        query_id=query_id,
        method_id=method_id,
        rating=rating,
        note=note,
    )
    _append_line(path, ev)


def read_events(path: Path) -> Iterator[FeedbackEvent]:
    """Stream events. Lenient: skips malformed lines with a stderr warning."""
    if not path.exists():
        return
    skipped = 0
    with path.open(encoding="utf-8") as f:
        for lineno, raw in enumerate(f, 1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
                kind = obj.get("event")
                if kind == "recommendation":
                    yield RecommendationEvent.model_validate(obj)
                elif kind == "rating":
                    yield RatingEvent.model_validate(obj)
                else:
                    raise ValueError(f"unknown event type: {kind}")
            except Exception as e:
                skipped += 1
                print(f"feedback: skipped malformed line {lineno}: {e}", file=sys.stderr)
    if skipped:
        print(f"feedback: {skipped} line(s) skipped", file=sys.stderr)


@dataclass
class MethodStats:
    method_id: str
    recommendation_count: int = 0
    rating_count: int = 0
    rating_sum: int = 0

    @property
    def avg_rating(self) -> float:
        return self.rating_sum / self.rating_count if self.rating_count else 0.0


def stats(path: Path) -> dict[str, MethodStats]:
    out: dict[str, MethodStats] = {}
    for ev in read_events(path):
        if isinstance(ev, RecommendationEvent):
            for mid in ev.method_ids:
                s = out.setdefault(mid, MethodStats(method_id=mid))
                s.method_id = mid
                s.recommendation_count += 1
        elif isinstance(ev, RatingEvent):
            s = out.setdefault(ev.method_id, MethodStats(method_id=ev.method_id))
            s.method_id = ev.method_id
            s.rating_count += 1
            s.rating_sum += ev.rating
    return out


@dataclass
class GoalRow:
    """What happened after one goal was picked, over every time it was."""

    goal: str
    clicks: int = 0
    first_changed: int = 0
    """Refined searches whose first method differs from the one before the goal."""
    ratings: list[int] = field(default_factory=list)
    """Ratings of the refined results."""
    before: list[int] = field(default_factory=list)
    """Ratings of the first method before the goal, given on the original search."""


@dataclass
class GoalStats:
    recorded: int = 0
    """Searches that recorded whether the question was asked."""
    asked: int = 0
    """Searches typed by a person that got the question."""
    answered: int = 0
    """Of those, how many were followed by at least one goal."""
    back: int = 0
    """Times someone went from a goal back to the problem as typed."""
    rows: dict[str, GoalRow] = field(default_factory=dict)


def goal_stats(path: Path) -> GoalStats:
    """How people answered "Was möchten Sie erreichen?", read off the log.

    Built to check the measurement behind mcp_tools.UNSURE_TOP_SCORE in use:
    there a goal lifted a right method about as often as it pushed one down,
    with goals picked by whoever ran the benchmark. Here the people who had
    the problem pick them, and their ratings say whether it helped.
    """
    searches: dict[str, RecommendationEvent] = {}
    ratings: list[RatingEvent] = []
    for ev in read_events(path):
        if isinstance(ev, RecommendationEvent):
            searches[ev.query_id] = ev
        else:
            ratings.append(ev)

    out = GoalStats()
    answered: set[str] = set()
    for ev in searches.values():
        if ev.clarify is not None:
            out.recorded += 1
        if ev.refines is None:
            out.asked += bool(ev.clarify)
            continue
        if ev.goal is None:
            out.back += 1
            continue
        root = searches.get(ev.refines)
        row = out.rows.setdefault(ev.goal, GoalRow(goal=ev.goal))
        row.clicks += 1
        answered.add(ev.refines)
        if root and root.method_ids and ev.method_ids:
            row.first_changed += root.method_ids[0] != ev.method_ids[0]
        row.ratings += [r.rating for r in ratings if r.query_id == ev.query_id]
    out.answered = sum(1 for qid in answered if qid in searches and searches[qid].clarify)

    # The first method before a goal, rated on the original search: either
    # before the click, or on the card the console keeps on screen after it.
    firsts = {
        qid: searches[qid].method_ids[0]
        for qid in answered
        if qid in searches and searches[qid].method_ids
    }
    goals_of: dict[str, set[str]] = {}
    for ev in searches.values():
        if ev.refines in firsts and ev.goal:
            goals_of.setdefault(ev.refines, set()).add(ev.goal)
    for r in ratings:
        if r.query_id in firsts and r.method_id == firsts[r.query_id]:
            for g in goals_of[r.query_id]:
                out.rows[g].before.append(r.rating)
    return out
