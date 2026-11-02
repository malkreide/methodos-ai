"""Turn real searches from the feedback log into new holdout problems.

The holdout files were written by the people who also wrote the catalog's use
cases, before the use cases, but by the same hands. The fairest test of search
is what people actually type. This script takes those problems from
`feedback.jsonl` and, after a person has reviewed them, adds them to
`search_queries_holdout_log.json` — a holdout nobody wrote, read with
`audit_search.py --queries` like the others.

Two steps, with a person in between:

  extract LOG DRAFT   Writes every distinct problem people typed (not a goal
                      refinement, not sample data, not too short, not already
                      in a benchmark file) to DRAFT, most-asked first, each
                      with `keep: false`, an empty `acceptable`, `goal: null`
                      and `flags` for anything that looks like personal data.

  add DRAFT           Takes the entries marked `keep: true`, checks them, and
                      appends them to scripts/search_queries_holdout_log.json.

Between the two, a person edits DRAFT:

  * Rewrite the problem until no person, class, school or address can be
    recognised. The repository is public; the log is not. `add` refuses a
    problem that still holds an e-mail address, a phone number, a link or a
    salutation with a name ("Frau Meier"), and one flagged as a possible name
    unless `names_checked: true` says someone looked.
  * Fill `acceptable` from the catalog (`methodos list`), not from what search
    returned. That is why the draft does not show the results: a benchmark
    whose answers were copied from the ranking measures the ranking against
    itself.
  * Set `goal` to the goal a person would pick when asked («Was möchten Sie
    erreichen?»), or leave it null.

The file is a holdout from the moment an entry lands in it: never write or
reword a use case while looking at it (docs/curation.md). The log itself stays
where it is; the draft holds only problem texts, never timestamps or ids.

Usage:
    python scripts/holdout_from_log.py extract data/feedback.jsonl /tmp/draft.json
    python scripts/holdout_from_log.py add /tmp/draft.json
    python scripts/holdout_from_log.py add /tmp/draft.json --target /tmp/other.json

Entries marked `practice: true` (scripts/sample_holdout_draft.py) are refused
for the real holdout file; send them elsewhere with --target.

    docker compose run --rm --entrypoint python cli \\
        scripts/holdout_from_log.py extract /data/feedback.jsonl /data/holdout_draft.json
    docker compose cp methodos:/data/holdout_draft.json .
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path

from methodos.feedback import RecommendationEvent, read_events

HERE = Path(__file__).parent
REPO = HERE.parent
TARGET = HERE / "search_queries_holdout_log.json"
SAMPLE_MODEL = "sample-data"
MIN_WORDS = 4
NEAR_DUPLICATE = 0.9
"""Two problems this similar (difflib ratio, case-folded) count as one."""

BLOCKING = {
    "e-mail address": re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),
    "phone number": re.compile(r"(?:\+|\b0)[\d ()/-]{8,}\d"),
    "link": re.compile(r"https?://|www\.", re.I),
    "salutation with a name": re.compile(
        r"\b(?:Herr|Frau|Hr\.|Fr\.|Mr\.?|Mrs\.?|Ms\.?|Dr\.)\s+[A-ZÄÖÜ][\w-]+"
    ),
}
"""Patterns `add` never lets into the public file."""

POSSIBLE_NAME = re.compile(r"(?<=[a-zäöüß,;:] )[A-ZÄÖÜ][a-zäöüß]+ [A-ZÄÖÜ][a-zäöüß]+\b")
"""Two capitalised words mid-sentence — a full name, or a German noun phrase.
Too many false hits to block on, so a person confirms with `names_checked`."""


def flags(text: str) -> list[str]:
    found = [f"{what}: {m.group(0)!r}" for what, rx in BLOCKING.items() for m in rx.finditer(text)]
    found += [f"possible name: {m.group(0)!r}" for m in POSSIBLE_NAME.finditer(text)]
    return found


def _norm(text: str) -> str:
    return " ".join(text.casefold().split())


def _benchmark_queries() -> list[str]:
    return [
        _norm(c["query"])
        for f in sorted(HERE.glob("search_queries*.json"))
        for c in json.loads(f.read_text(encoding="utf-8"))
    ]


def _similar(a: str, known: list[str]) -> bool:
    return any(SequenceMatcher(None, a, k).ratio() >= NEAR_DUPLICATE for k in known)


def extract(log: Path) -> list[dict]:
    """Distinct typed problems from the log, most-asked first."""
    asked: Counter[str] = Counter()
    text: dict[str, str] = {}
    for ev in read_events(log):
        if not isinstance(ev, RecommendationEvent):
            continue
        if ev.model == SAMPLE_MODEL or ev.refines is not None:
            continue
        query = " ".join(ev.query.split())
        if len(query.split()) < MIN_WORDS:
            continue
        key = _norm(query)
        asked[key] += 1
        text.setdefault(key, query)

    known = _benchmark_queries()
    kept: list[str] = []
    for key, _ in sorted(asked.items(), key=lambda kv: (-kv[1], kv[0])):
        if _similar(key, known) or _similar(key, kept):
            continue
        kept.append(key)
    return [
        {
            "query": text[key],
            "asked": asked[key],
            "flags": flags(text[key]),
            "keep": False,
            "acceptable": [],
            "goal": None,
        }
        for key in kept
    ]


def _catalog_ids() -> set[str]:
    return {p.stem for p in (REPO / "methods").glob("*.json")}


def _console_goals() -> set[str]:
    html = (REPO / "src" / "methodos" / "console.html").read_text(encoding="utf-8")
    return set(re.findall(r"'(\w+)'", html.split("const GOALS = [", 1)[1].split("];", 1)[0]))


def check(entry: dict, ids: set[str], goals: set[str]) -> list[str]:
    """Why an entry marked `keep` may not go into the public file."""
    problems = []
    query = entry.get("query", "")
    if len(query.split()) < MIN_WORDS:
        problems.append("the problem is too short to be a fair test")
    blocking = [f for f in flags(query) if not f.startswith("possible name")]
    problems += [f"still contains an {f}" for f in blocking]
    if any(f.startswith("possible name") for f in flags(query)) and not entry.get("names_checked"):
        problems.append("flagged as a possible name: rewrite it, or set names_checked: true")
    acceptable = entry.get("acceptable") or []
    if not acceptable:
        problems.append("acceptable is empty: name the methods that would be a right answer")
    problems += [f"no method with id {m!r}" for m in acceptable if m not in ids]
    goal = entry.get("goal")
    if goal is not None and goal not in goals:
        problems.append(f"goal {goal!r} is not one the console offers: {', '.join(sorted(goals))}")
    return problems


def add(draft: Path, target: Path = TARGET) -> tuple[int, list[str]]:
    """Append the reviewed entries; return how many, and every refusal."""
    entries = [e for e in json.loads(draft.read_text(encoding="utf-8")) if e.get("keep")]
    ids, goals = _catalog_ids(), _console_goals()
    errors = [f"{e.get('query', '?')!r}: {why}" for e in entries for why in check(e, ids, goals)]
    # Invented problems from scripts/sample_holdout_draft.py may be added to a
    # file of their own, never to the real holdout.
    if target.resolve() == TARGET.resolve():
        errors += [
            f"{e.get('query', '?')!r}: a practice entry — add it with --target elsewhere"
            for e in entries
            if e.get("practice")
        ]
    if errors:
        return 0, errors

    existing = json.loads(target.read_text(encoding="utf-8")) if target.exists() else []
    known = _benchmark_queries() + [_norm(c["query"]) for c in existing]
    added = []
    for e in entries:
        if _similar(_norm(e["query"]), known):
            errors.append(f"{e['query']!r}: already in a benchmark file, skipped")
            continue
        known.append(_norm(e["query"]))
        added.append(
            {
                "query": e["query"],
                "acceptable": e["acceptable"],
                "goal": e.get("goal"),
                "added": date.today().isoformat(),
            }
        )
    if added:
        target.write_text(
            json.dumps(existing + added, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    return len(added), errors


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    ex = sub.add_parser("extract", help="log -> draft for a person to review")
    ex.add_argument("log", type=Path)
    ex.add_argument("draft", type=Path)
    ad = sub.add_parser("add", help="reviewed draft -> search_queries_holdout_log.json")
    ad.add_argument("draft", type=Path)
    ad.add_argument(
        "--target",
        type=Path,
        default=TARGET,
        help="default: scripts/search_queries_holdout_log.json",
    )
    args = ap.parse_args()

    if args.cmd == "extract":
        if args.draft.exists():
            print(f"error: {args.draft} exists — a draft is never written over", file=sys.stderr)
            return 1
        if args.draft.resolve().is_relative_to(REPO.resolve()):
            print(
                "error: write the draft outside the repository — it holds problems "
                "exactly as people typed them",
                file=sys.stderr,
            )
            return 1
        entries = extract(args.log)
        args.draft.write_text(
            json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        flagged = sum(1 for e in entries if e["flags"])
        print(f"wrote {len(entries)} problems to {args.draft} ({flagged} flagged).")
        print("Review it — anonymise, fill acceptable and goal, set keep — then run add.")
        return 0

    n, errors = add(args.draft, args.target)
    for line in errors:
        print(f"refused {line}", file=sys.stderr)
    if n:
        print(f"added {n} problem(s) to {args.target}")
    elif not errors:
        print("nothing added: no entry in the draft is marked keep: true")
    return 1 if errors and not n else 0


if __name__ == "__main__":
    sys.exit(main())
