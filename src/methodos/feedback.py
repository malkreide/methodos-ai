"""Feedback loop placeholder — append-only JSONL of recommendations and ratings.

Designed to outgrow itself: when volume justifies it, a one-shot import script
turns this file into a SQLite database without changing the writer API. Until
then, JSONL gives us crash-safety, git-friendly diffs, and trivial concurrent
appends.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Iterator
from dataclasses import dataclass
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
) -> str:
    """Append a recommendation event. Returns the freshly-minted query_id (ULID)."""
    qid = str(ULID())
    ev = RecommendationEvent(
        timestamp=_now_iso(),
        query_id=qid,
        query=query,
        method_ids=method_ids,
        model=model,
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
