"""Does adding the console's goal sentence help search — in German and in English?

When the ranking is unsure the console asks «Was möchten Sie erreichen?» and
appends the sentence of the goal a person picks (console.html, `goal_*_q`).
The German sentences were measured when that went in (mcp_tools,
UNSURE_TOP_SCORE). This script measures them again, and the English ones for
the first time, on the problems people type:

  de  search_queries.json and search_queries_holdout.json
  en  search_queries_en.json and search_queries_holdout_en.json (the same
      problems, translated; same acceptable methods, same goal)

Each problem carries the goal a person would pick (`goal`, or null where none
of the ten fits) — judgement, like `acceptable`. For every problem the shipped
rule flags (`clarify`), the problem is searched again with that goal's
sentence appended, exactly as the console does, and the script reports:

  * how many wrong first places the rule catches, and how many right ones it
    asks about needlessly;
  * for the flagged problems with a fitting goal: right first place, and a
    right method among the results, before and after — and after with the
    earlier first match kept on screen, as the console keeps it.

Deliberately not a test: the goals and the acceptable sets are judgement, and
the numbers are a baseline to move. Run it after changing a goal sentence, the
reranker, or the catalog's wording, before and after.

Measured 2026-10-13 on the 87-method catalog, overfetch 9 (flagged problems
with a fitting goal; "shown" counts the earlier first match the console keeps):

                     asked on        first place right    a right one shown
                     wrong  right    wrong      right     wrong      right
  de                 10/15  7/40     0 -> 5/9   7 -> 3/7  4 -> 8/9   7 -> 7/7
  en                  9/15  5/40     0 -> 4/8   5 -> 4/5  3 -> 5/8   5 -> 5/5

The English sentences hold up: about as many first places lifted, fewer wrong
ones brought into view, fewer right ones pushed down. Most English failures
are problems whose English top three is unrelated before and after.

Usage:
    python scripts/verify_goals.py              # both languages
    python scripts/verify_goals.py --lang en
    docker compose run --rm --entrypoint python cli scripts/verify_goals.py

Needs an ingested index and the `local` extra. Exit code is 0 whatever it finds.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from methodos import mcp_tools
from methodos.config import Settings
from methodos.providers import make_embedding, make_reranker

HERE = Path(__file__).parent
CONSOLE = HERE.parent / "src" / "methodos" / "console.html"
FILES = {
    "de": [HERE / "search_queries.json", HERE / "search_queries_holdout.json"],
    "en": [HERE / "search_queries_en.json", HERE / "search_queries_holdout_en.json"],
}


def goal_sentences(lang: str) -> dict[str, str]:
    """The sentence the console appends for each goal, in one language."""
    html = CONSOLE.read_text(encoding="utf-8")
    de, en = html.split("const I18N = {", 1)[1].split("\n};", 1)[0].split("\n  en: {", 1)
    block = de if lang == "de" else en
    return dict(re.findall(r"^ {4}goal_(\w+)_q: '([^']*)',$", block, re.M))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--lang", choices=sorted(FILES), action="append", help="default: both")
    args = ap.parse_args()

    settings = Settings()
    embedding = make_embedding(settings)
    reranker = make_reranker(settings, required=True)

    def search(problem: str) -> mcp_tools.RecommendResult:
        return mcp_tools.recommend_methods(
            problem=problem,
            embedding=embedding,
            chroma_path=settings.chroma_path,
            top_k=settings.top_k,
            reranker=reranker,
            overfetch_factor=settings.overfetch_factor,
        )

    summary: list[str] = []
    for lang in args.lang or sorted(FILES):
        sentences = goal_sentences(lang)
        cases = [c for f in FILES[lang] for c in json.loads(f.read_text(encoding="utf-8"))]
        n = Counter()
        print(f"=== {lang} ({len(cases)} problems)")
        for case in cases:
            good = set(case["acceptable"])
            before = search(case["query"])
            ids = [m.id for m in before.matches]
            right = ids[0] in good
            n["right" if right else "wrong"] += 1
            if before.clarify is None:
                continue
            kind = "right" if right else "wrong"
            n[f"{kind}_asked"] += 1
            goal = case.get("goal")
            if goal is None:
                n[f"{kind}_nogoal"] += 1
                print(f"{kind:<6}no goal fits   {case['query']}")
                continue
            after = [m.id for m in search(f"{case['query']} {sentences[goal]}").matches]
            kept = after if ids[0] in after else [*after, ids[0]]
            n[f"{kind}_n"] += 1
            n[f"{kind}_top1"] += after[0] in good
            n[f"{kind}_top3_before"] += any(m in good for m in ids)
            n[f"{kind}_top3_after"] += any(m in good for m in after)
            n[f"{kind}_kept"] += any(m in good for m in kept)
            mark = "ok" if after[0] in good else "--"
            print(f"{kind:<6}{goal:<11}{mark}  {case['query']}")
            print(f"        before {', '.join(ids)}\n        after  {', '.join(after)}")

        lines = [
            f"{lang}: asked on {n['wrong_asked']} of {n['wrong']} wrong first places and "
            f"{n['right_asked']} of {n['right']} right ones; no goal fits "
            f"{n['wrong_nogoal'] + n['right_nogoal']}",
            "                       first place right   a right one shown (with the kept first)",
        ]
        for kind, label in (("wrong", "wrong before"), ("right", "right before")):
            k = n[f"{kind}_n"]
            first = 0 if kind == "wrong" else k
            lines.append(
                f"  {label} ({k:>2})       {first:>2} -> {n[f'{kind}_top1']:<2}"
                f"             {n[f'{kind}_top3_before']:>2} -> {n[f'{kind}_top3_after']:<2}"
                f" ({n[f'{kind}_kept']})"
            )
        summary.append("\n".join(lines))
        print()

    print("\n\n".join(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
