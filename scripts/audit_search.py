"""Measure search on problems phrased the way people type them.

The pinned probes in tests/test_integration.py all pass, and say less than that
suggests: several were reworded until this reranker put their method first
(see the comments there), and most use the method's own vocabulary ("debrief
the launch we just finished"). People write the problem instead — "nach jedem
Schulprojekt wiederholen wir dieselben Fehler". `search_queries.json` holds such
problems, each with the methods that would be a right answer, and this script
reports how often the shipped pipeline leads with one.

Deliberately not a test: the acceptable sets are judgement, and the number is
a baseline to move, not a bar to hold. Change the catalog or the ranking, run
it before and after, and compare.

With --diagnose every miss also shows where its best acceptable method sits in
the whole catalog, by embedding and by reranker, which says what kind of fix it
needs:

  shortlist OUT, rerank high   the reranker would choose it but never sees it:
                               the embedding misses it (overfetch, or wording)
  shortlist in,  rerank low    seen and demoted: the method's texts do not
                               describe this problem — a `use_cases` line

Measured 2026-10-09 on the 71-method catalog: top-1 19/36 and top-3 30/36 at
overfetch 3, the default until then; 23/36 and 32/36 at 8, the default since
(+5 first places, -1). The embedding alone: 16/36. The same 36 in English
scored the same, so the gap is not the language. BAAI/bge-reranker-v2-m3 in
place of the default reranker: 23/36 at fifteen times the time per query,
missing largely the same problems — what is left is catalog wording.

Usage:
    python scripts/audit_search.py                    # summary, one line per query
    python scripts/audit_search.py --diagnose         # + where each miss sits (slow)
    python scripts/audit_search.py --overfetch 8      # try another shortlist size

Needs an ingested index and the `local` extra. Exit code is 0 whatever it finds.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from methodos.config import Settings
from methodos.providers import make_embedding, make_reranker
from methodos.search import Candidate, retrieve

QUERIES = Path(__file__).with_name("search_queries.json")
ALL = 10_000
"""top_k that returns the whole catalog; retrieve() stops at what is indexed."""


def _rank(order: list[Candidate], method_id: str) -> int:
    return next(i for i, c in enumerate(order, 1) if c.id == method_id)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--queries", type=Path, default=QUERIES)
    ap.add_argument("--overfetch", type=int, default=None, help="default: Settings")
    ap.add_argument("--diagnose", action="store_true")
    args = ap.parse_args()

    settings = Settings()
    overfetch = args.overfetch or settings.overfetch_factor
    shortlist = settings.top_k * overfetch
    embedding = make_embedding(settings)
    reranker = make_reranker(settings, required=True)
    cases = json.loads(args.queries.read_text(encoding="utf-8"))

    def run(query: str, top_k: int, factor: int, rerank: bool) -> list[Candidate]:
        return retrieve(
            query=query,
            embedding=embedding,
            chroma_path=settings.chroma_path,
            top_k=top_k,
            reranker=reranker if rerank else None,
            overfetch_factor=factor,
        )

    top1 = top3 = 0
    for case in cases:
        query, good = case["query"], set(case["acceptable"])
        out = run(query, settings.top_k, overfetch, rerank=True)
        hit1, hit3 = out[0].id in good, any(c.id in good for c in out)
        top1 += hit1
        top3 += hit3
        mark = "ok " if hit1 else ("top3" if hit3 else "miss")
        found = ", ".join(f"{c.id} ({c.rerank_score:+.1f})" for c in out)
        print(f"{mark:<5}{query}\n     -> {found}")
        if args.diagnose and not hit1:
            by_sim = run(query, ALL, 1, rerank=False)
            by_rerank = run(query, ALL, 1, rerank=True)
            best = min(good, key=lambda m: _rank(by_rerank, m))
            s, r = _rank(by_sim, best), _rank(by_rerank, best)
            where = "in" if s <= shortlist else "OUT"
            print(f"     {best}: embedding #{s}, reranker #{r} of {len(by_sim)}; shortlist {where}")

    n = len(cases)
    print(
        f"\ntop-1 {top1}/{n}   top-3 {top3}/{n}   (top_k {settings.top_k}, overfetch {overfetch})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
