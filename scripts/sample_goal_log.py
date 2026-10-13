"""Write an invented feedback log to try `methodos goals` on before real data exists.

The console's question back («Was möchten Sie erreichen?») only produces data
once people use it. This script writes a log of the same shape — searches
asked and not asked, goals picked, ways back without a goal, ratings before
and after — so the report can be read, explained and checked now.

Every number in it is invented. The problems are real ones from
search_queries.json, but who picked which goal, which method came first and
how anything was rated are drawn from made-up profiles (PROFILES below), and
one goal ("anticipate") is never picked on purpose, so the "Never picked" line
shows. Each search carries `model: "sample-data"`. Do not mix the output into
a real log, and do not quote what `methodos goals` says about it.

The same seed writes the same file, byte for byte.

Usage:
    python scripts/sample_goal_log.py /tmp/sample.jsonl
    METHODOS_FEEDBACK_PATH=/tmp/sample.jsonl methodos goals

    python scripts/sample_goal_log.py /tmp/few.jsonl --questions 12   # the anecdote warning

    docker compose run --rm --entrypoint python cli scripts/sample_goal_log.py /data/sample.jsonl
    docker compose run --rm -e METHODOS_FEEDBACK_PATH=/data/sample.jsonl cli goals

Refuses to write over an existing file or to the configured feedback log.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from ulid import ULID

from methodos.config import Settings
from methodos.feedback import RatingEvent, RecommendationEvent

HERE = Path(__file__).parent
CONSOLE = HERE.parent / "src" / "methodos" / "console.html"
QUERY_FILES = [HERE / "search_queries.json", HERE / "search_queries_holdout.json"]
MODEL = "sample-data"
START = datetime(2026, 9, 1, 7, 30, tzinfo=UTC)
NEW_FIELDS = {"clarify", "goal", "refines"}


@dataclass(frozen=True)
class Profile:
    """How one goal behaves in the invented data."""

    weight: int
    """Relative chance of being picked; 0 means never."""
    changes: float
    """Chance that the goal changes the first method."""
    after: float
    """Mean rating of the refined results."""
    before: float
    """Mean rating of the first method before the goal."""


# Invented. Shaped so the table has something to read — goals that help, one
# that hurts ("decide"), rare ones, one never picked — not to predict anything.
PROFILES = {
    "cause": Profile(5, 0.6, 3.8, 2.8),
    "learn": Profile(4, 0.7, 4.0, 2.5),
    "involve": Profile(3, 0.5, 3.5, 3.0),
    "prioritise": Profile(2, 0.5, 3.6, 3.2),
    "decide": Profile(2, 0.4, 2.9, 3.5),
    "impact": Profile(2, 0.6, 3.8, 2.7),
    "ideas": Profile(1, 0.3, 3.2, 3.3),
    "pilot": Profile(1, 0.5, 4.0, 3.0),
    "conflict": Profile(1, 0.5, 2.6, 3.0),
    "anticipate": Profile(0, 0.5, 3.0, 3.0),
}
ANSWER = 0.4
"""Chance that a person picks a goal when asked."""
SECOND_GOAL = 0.15
BACK = 0.1
RATE_AFTER = 0.5
RATE_BEFORE = 0.35


def goal_sentences() -> dict[str, str]:
    """The German sentence the console appends for each goal, read off the
    console so the sample's queries look like the ones it would log."""
    html = CONSOLE.read_text(encoding="utf-8")
    german = html.split("const I18N = {", 1)[1].split("\n  en: {", 1)[0]
    return dict(re.findall(r"^ {4}goal_(\w+)_q: '([^']*)',$", german, re.M))


class Writer:
    def __init__(self, rng: random.Random) -> None:
        self.rng = rng
        self.clock = START
        self.lines: list[str] = []

    def _tick(self) -> datetime:
        self.clock += timedelta(minutes=self.rng.randint(1, 240))
        return self.clock

    def _id(self, at: datetime) -> str:
        ms = int(at.timestamp() * 1000)
        return str(ULID.from_bytes(ms.to_bytes(6, "big") + self.rng.randbytes(10)))

    def search(
        self,
        query: str,
        ids: list[str],
        *,
        clarify: bool | None,
        goal: str | None = None,
        refines: str | None = None,
    ) -> str:
        at = self._tick()
        ev = RecommendationEvent(
            timestamp=at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            query_id=self._id(at),
            query=query,
            method_ids=ids,
            model=MODEL,
            clarify=clarify,
            goal=goal,
            refines=refines,
        )
        # A line from before the fields existed carries none of them at all.
        exclude = NEW_FIELDS if clarify is None else None
        self.lines.append(ev.model_dump_json(exclude=exclude))
        return ev.query_id

    def rate(self, query_id: str, method_id: str, mean: float) -> None:
        at = self._tick()
        rating = max(1, min(5, round(self.rng.gauss(mean, 0.9))))
        ev = RatingEvent(
            timestamp=at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            query_id=query_id,
            method_id=method_id,
            rating=rating,
        )
        self.lines.append(ev.model_dump_json())


def build(questions: int, seed: int) -> list[str]:
    rng = random.Random(seed)
    w = Writer(rng)
    cases = [c for f in QUERY_FILES for c in json.loads(f.read_text(encoding="utf-8"))]
    pool = sorted({m for c in cases for m in c["acceptable"]})
    sentences = goal_sentences()
    goals = [g for g, p in PROFILES.items() if p.weight]

    def methods(first: str | None = None) -> list[str]:
        rest = rng.sample([m for m in pool if m != first], 3)
        return [first, *rest[:2]] if first else rest

    def refine(root: str, case: dict, root_ids: list[str], taken: set[str]) -> None:
        left = [g for g in goals if g not in taken]
        goal = rng.choices(left, [PROFILES[g].weight for g in left])[0]
        taken.add(goal)
        p = PROFILES[goal]
        changed = rng.random() < p.changes
        ids = methods(None if changed else root_ids[0])
        if changed and ids[0] == root_ids[0]:
            ids = [ids[1], ids[0], ids[2]]
        query = f"{case['query']} {sentences[goal]}"
        qid = w.search(query, ids, clarify=rng.random() < 0.3, goal=goal, refines=root)
        if rng.random() < RATE_AFTER:
            w.rate(qid, rng.choice(ids[:2]), p.after)
        if rng.random() < RATE_BEFORE:
            w.rate(root, root_ids[0], p.before)

    # Lines from before the question was recorded, as an existing log has them.
    for case in rng.sample(cases, 8):
        w.search(case["query"], methods(), clarify=None)

    for _ in range(questions):
        # Most searches are never asked: about two for every one that is.
        for _ in range(2):
            case = rng.choice(cases)
            qid = w.search(case["query"], methods(), clarify=False)
            if rng.random() < 0.3:
                w.rate(qid, rng.choice(case["acceptable"]), 4.0)

        case = rng.choice(cases)
        root_ids = methods()
        root = w.search(case["query"], root_ids, clarify=True)
        if rng.random() >= ANSWER:
            if rng.random() < 0.2:
                w.rate(root, root_ids[0], 2.8)
            continue
        taken: set[str] = set()
        refine(root, case, root_ids, taken)
        if rng.random() < SECOND_GOAL:
            refine(root, case, root_ids, taken)
        if rng.random() < BACK:
            w.search(case["query"], root_ids, clarify=True, refines=root)
    return w.lines


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("out", type=Path, help="where to write the sample log")
    ap.add_argument(
        "--questions", type=int, default=60, help="searches that get asked (default 60)"
    )
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    if args.out.exists():
        print(
            f"error: {args.out} exists — the sample is never written over a file", file=sys.stderr
        )
        return 1
    if args.out.resolve() == Settings().feedback_path.resolve():
        print(
            f"error: {args.out} is the configured feedback log; write the sample elsewhere",
            file=sys.stderr,
        )
        return 1

    lines = build(args.questions, args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {len(lines)} invented events to {args.out}")
    print(f"read them with:  METHODOS_FEEDBACK_PATH={args.out} methodos goals")
    return 0


if __name__ == "__main__":
    sys.exit(main())
