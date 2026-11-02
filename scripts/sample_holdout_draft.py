"""Write a practice draft for scripts/holdout_from_log.py, before real searches exist.

`holdout_from_log.py extract` turns the feedback log into a draft that a
person reviews: anonymise each problem, name the methods that would be a right
answer, pick a goal, decide what to keep. This script writes a draft of the
same shape from twelve invented problems, so the review can be practised — and
explained to whoever will do it — before the console has been used.

The problems are made up, but typed the way people type: lower case, a phone
number left in, a colleague named, a school's street in the team's name. Each
one is there for a reason that `--solved` spells out in `note`:

  * personal data the check blocks (an e-mail address, a phone number, a
    salutation with a name) and data it only suspects (two capitalised words);
  * a suspected name that is no name at all ("Lehrplan Volksschule"), which a
    person confirms with `names_checked: true`;
  * a problem already in the benchmark, which `add` skips;
  * a search that is no problem a method could answer, which is not kept.

Without `--solved` the draft is the exercise: every entry `keep: false`, no
`acceptable`, no goal, the problems as typed. With it, one way of solving it:
rewritten, labelled and marked. The `acceptable` sets are judgement, like the
benchmark's.

Every entry carries `practice: true`, and `holdout_from_log.py add` refuses
those for the real holdout file; try them against a file of their own:

    python scripts/sample_holdout_draft.py /tmp/practice.json
    python scripts/sample_holdout_draft.py /tmp/solved.json --solved
    python scripts/holdout_from_log.py add /tmp/practice.json --target /tmp/h.json  # refused
    python scripts/holdout_from_log.py add /tmp/solved.json --target /tmp/h.json
    python scripts/audit_search.py --queries /tmp/h.json

Treat the twelve like a holdout too: they were written without looking at any
use case. Run through `audit_search.py` on 87 methods (2026-10-13), search led
with one of the methods named in the solution for 3 of the 10 kept — a hint of
what real problems may show, not a measurement: the problems and the answers
are one person's invention. Do not tune catalog texts against them.

Refuses to write over a file or into the repository, like `extract`.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
REPO = HERE.parent

_spec = importlib.util.spec_from_file_location("holdout_from_log", HERE / "holdout_from_log.py")
assert _spec and _spec.loader
holdout = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("holdout_from_log", holdout)
_spec.loader.exec_module(holdout)

# (as typed, times asked, as solved: query, acceptable, goal, keep, note)
PROBLEMS: list[tuple[str, int, dict]] = [
    (
        "Frau Keller im Sekretariat ist ständig überlastet, wie verteilen wir die Arbeit besser?",
        4,
        {
            "query": "Eine Mitarbeiterin im Sekretariat ist ständig überlastet, wie verteilen "
            "wir die Arbeit im Team besser?",
            "acceptable": ["RACI_Matrix", "Value_Stream_Mapping"],
            "goal": None,
            "note": "Name and salutation removed; the problem is the distribution of work.",
        },
    ),
    (
        "bitte rückmeldung an p.muster@example.org: der elternrat will bei der neuen "
        "pausenregel mitreden",
        3,
        {
            "query": "Der Elternrat will bei der neuen Pausenregel mitreden, wie beziehen wir "
            "ihn sinnvoll ein?",
            "acceptable": ["World_Cafe", "Consent_Decision_Making", "Fishbowl"],
            "goal": "involve",
            "note": "E-mail address removed; the request to reply is not part of the problem.",
        },
    ),
    (
        "Seit dem Wechsel zur neuen Lernplattform melden sich jede Woche mehr Lehrpersonen "
        "mit Problemen",
        3,
        {
            "acceptable": ["Ishikawa_Diagram", "Five_Whys", "Pareto_Analysis"],
            "goal": "cause",
            "note": "Nothing to anonymise.",
        },
    ),
    (
        "Mit Thomas Brunner aus der 5b gibt es seit Wochen Streit wegen der Noten",
        2,
        {
            "query": "Mit einem Vater gibt es seit Wochen Streit wegen der Noten seines Kindes",
            "acceptable": ["Principled_Negotiation", "Collegial_Case_Consultation"],
            "goal": "conflict",
            "names_checked": True,
            "note": "Name and class removed: together they identify a pupil. The check still "
            "suspects 'Wochen Streit' — two nouns, no name: names_checked.",
        },
    ),
    (
        "Rückruf bitte unter 079 123 45 67, es geht um die Anmeldung für den Mittagstisch",
        2,
        {
            "query": "Die Anmeldung für den Mittagstisch ist für viele Eltern unklar und führt "
            "zu vielen Rückfragen",
            "acceptable": ["Customer_Journey_Map", "Value_Stream_Mapping"],
            "goal": "cause",
            "note": "Phone number removed; the problem written out from the hint it gave.",
        },
    ),
    (
        "Die Schulleitung möchte wissen, ob das neue Lesetraining in der Unterstufe wirkt",
        2,
        {
            "acceptable": ["Theory_of_Change", "Most_Significant_Change"],
            "goal": "impact",
            "note": "Nothing to anonymise.",
        },
    ),
    (
        "Das Team der Tagesbetreuung Neue Schulhausstrasse ist zerstritten und redet nur "
        "noch übereinander",
        1,
        {
            "query": "Das Team der Tagesbetreuung ist zerstritten und redet nur noch übereinander",
            "acceptable": ["Principled_Negotiation", "Johari_Window", "Team_Charter"],
            "goal": "conflict",
            "note": "Flagged as a possible name: it is a street, which names the school. Removed.",
        },
    ),
    (
        "Der Lehrplan Volksschule verlangt neue Beurteilungsformen, wie führen wir sie ein?",
        1,
        {
            "acceptable": ["Kotter_Eight_Steps", "ADKAR_Model", "PDCA_Cycle"],
            "goal": "pilot",
            "names_checked": True,
            "note": "Flagged as a possible name, but it is the curriculum: names_checked.",
        },
    ),
    (
        "Wir planen eine Projektwoche mit allen Klassen und wissen nicht, wo wir anfangen sollen",
        1,
        {
            "acceptable": ["Critical_Path_Method", "RACI_Matrix"],
            "goal": None,
            "note": "Nothing to anonymise; no goal on offer fits a plan.",
        },
    ),
    (
        "Wir kommen in der Steuergruppe nie zu einem Entscheid!",
        1,
        {
            "acceptable": ["Consent_Decision_Making", "Nominal_Group_Technique"],
            "goal": "decide",
            "note": "Already in search_queries.json; add skips it. extract leaves such "
            "problems out — it is here to show what add does.",
        },
    ),
    (
        "wie funktioniert das hier eigentlich genau",
        5,
        {
            "keep": False,
            "note": "Not a problem a method could answer. Asked most often, kept never.",
        },
    ),
    (
        "Unsere Lehrpersonen sind nach den Herbstferien schon wieder erschöpft, was können "
        "wir als Schulleitung tun?",
        1,
        {
            "acceptable": ["Force_Field_Analysis", "Five_Whys", "Eisenhower_Matrix"],
            "goal": "cause",
            "note": "Nothing to anonymise. The acceptable set is the hard part here: "
            "argue it out with a second reviewer.",
        },
    ),
]


def build(solved: bool) -> list[dict]:
    out = []
    for typed, asked, answer in sorted(PROBLEMS, key=lambda p: -p[1]):
        entry = {
            "query": typed,
            "asked": asked,
            "flags": holdout.flags(typed),
            "keep": False,
            "acceptable": [],
            "goal": None,
            "practice": True,
        }
        if solved:
            entry.update(
                {
                    "query": answer.get("query", typed),
                    "keep": answer.get("keep", True),
                    "acceptable": answer.get("acceptable", []),
                    "goal": answer.get("goal"),
                    "note": answer["note"],
                }
            )
            if answer.get("names_checked"):
                entry["names_checked"] = True
        out.append(entry)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("out", type=Path)
    ap.add_argument("--solved", action="store_true", help="write one way of solving the draft")
    args = ap.parse_args()
    if args.out.exists():
        print(f"error: {args.out} exists — never written over", file=sys.stderr)
        return 1
    if args.out.resolve().is_relative_to(REPO.resolve()):
        print("error: write it outside the repository, as a real draft would be", file=sys.stderr)
        return 1
    entries = build(args.solved)
    args.out.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    flagged = sum(1 for e in entries if e["flags"])
    kind = "solved practice draft" if args.solved else "practice draft"
    print(f"wrote a {kind} of {len(entries)} invented problems to {args.out} ({flagged} flagged)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
