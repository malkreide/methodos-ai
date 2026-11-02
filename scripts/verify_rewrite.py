"""Would search find more if a model restated the problem first?

`scripts/audit_search.py` showed what is left after the catalog work: problems
that name a place and a feeling ("Unser Sommerfest ist jedes Jahr ein
Durcheinander") miss in any language and with any of the models tried, while
the same problem stated as a need ("the same things go wrong every year; we
want to learn from it") is found. This script measures whether an LLM can do
that restating, before anyone builds it into the product.

For every problem in search_queries.json and search_queries_holdout.json it
asks the model for a one- or two-sentence restatement, then runs the shipped
ranking three ways:

  raw       the problem as typed (what search does today)
  rewrite   the restatement alone
  both      the problem followed by the restatement

and prints top-1 / top-3 per file and per way, every restatement next to its
problem, and each problem whose result changed. Deliberately not a test: the
numbers decide whether a rewrite step earns its cost — one more model call
before every search, seconds of latency, and the problem sent to the provider
even when no explanation is asked for. The MCP server would not get it either
way; its caller is already a model.

The prompt never sees the catalog, and a restatement that names a catalog
method anyway is flagged: a rewrite that guesses the answer measures the
model's knowledge of management methods, not whether search improves.

Measured 2026-10-12 with anthropic/claude-opus-5, 71 methods, overfetch 8:

                         raw          rewrite      both
  search_queries (40)    33 (38)      25 (32)      29 (35)     top-1 (top-3)
  holdout (15)            7 (10)       9 (10)       9 (13)
  4.8-5.5 s per restatement; no restatement named a method.

On the 40 the rewrite loses, which is partly built in: their use cases were
written against the problems as typed. On the 15 it gains two first places,
within what one wording more or less moves. The restatements were faithful
but alike — about a third became "wants to understand why this keeps
happening", for problems as different as intranet forms and a school merger —
and lost the nouns that separated the right method (intranet forms went to the
Eisenhower Matrix instead of Card Sorting). Eight came back in German despite
the prompt. Not worth a model call before every search.

Needs a reachable LLM (METHODOS_MODEL / --model), an ingested index and the
`local` extra.

Examples:
    python scripts/verify_rewrite.py
    python scripts/verify_rewrite.py --model anthropic/claude-haiku-5-5
    docker compose run --rm --entrypoint python cli scripts/verify_rewrite.py

Exit codes:
  0  - every restatement came back (says nothing about whether they helped)
  1  - a model call failed, or the index is missing
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

from methodos.config import Settings
from methodos.providers import make_embedding, make_llm, make_reranker
from methodos.providers.base import LLMError, LLMProvider
from methodos.search import Candidate, StaleIndexError, retrieve

HERE = Path(__file__).parent
FILES = [HERE / "search_queries.json", HERE / "search_queries_holdout.json"]
WAYS = ("raw", "rewrite", "both")
ALL = 10_000

SYSTEM = """\
You help a search engine understand problems that people in schools and public
administrations type in a few words. Restate the problem in one or two plain
English sentences that say what is happening and what the person needs: to
understand a cause, to decide, to prioritise, to involve people, to learn from
something that keeps going wrong, and so on.

Do not name any method, framework or technique. Do not add facts that are not
in the problem. If the problem is ambiguous, state the most likely reading.
Answer with the restatement only."""


def rewrite(llm: LLMProvider, problem: str) -> str:
    # Room for a model that thinks before it writes; see LiteLLMProvider.
    text = llm.complete(SYSTEM, problem, max_tokens=2048)
    return " ".join(text.split())


def leaked(text: str, methods: list[Candidate]) -> list[str]:
    """Catalog methods the text names: by name without its parenthesis, by id,
    or by a leading acronym ("RACI", "PDCA") matched case-sensitively."""
    low = text.lower()
    found = []
    for m in methods:
        name = m.name.split("(")[0].strip()
        first = name.split()[0]
        if (
            name.lower() in low
            or m.id.replace("_", " ").lower() in low
            or (first.isupper() and len(first) > 2 and re.search(rf"\b{first}\b", text))
        ):
            found.append(m.name)
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--model", help="litellm model string; default: METHODOS_MODEL")
    ap.add_argument("--queries", type=Path, action="append", help="default: both query files")
    args = ap.parse_args()

    settings = Settings()
    if args.model:
        settings = settings.model_copy(update={"model": args.model})
    llm = make_llm(settings)
    embedding = make_embedding(settings)
    reranker = make_reranker(settings, required=True)

    def run(query: str) -> list[Candidate]:
        return retrieve(
            query=query,
            embedding=embedding,
            chroma_path=settings.chroma_path,
            top_k=settings.top_k,
            reranker=reranker,
            overfetch_factor=settings.overfetch_factor,
        )

    try:
        methods = retrieve(
            query="x", embedding=embedding, chroma_path=settings.chroma_path, top_k=ALL
        )
    except StaleIndexError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    if not methods:
        print(f"error: {settings.chroma_path} holds no methods — run ingest", file=sys.stderr)
        return 1

    print(f"model: {settings.model}\n")
    totals: list[str] = []
    for path in args.queries or FILES:
        cases = json.loads(path.read_text(encoding="utf-8"))
        hits = {w: [0, 0] for w in WAYS}
        leaks = 0
        seconds: list[float] = []
        print(f"=== {path.name} ({len(cases)} problems)")
        for case in cases:
            problem, good = case["query"], set(case["acceptable"])
            started = time.monotonic()
            try:
                restated = rewrite(llm, problem)
            except LLMError as e:
                print(f"FAILED on {problem!r}: {e}", file=sys.stderr)
                return 1
            seconds.append(time.monotonic() - started)
            tops = {
                "raw": run(problem),
                "rewrite": run(restated),
                "both": run(f"{problem}\n{restated}"),
            }
            for w, out in tops.items():
                hits[w][0] += out[0].id in good
                hits[w][1] += any(c.id in good for c in out)
            marks = " ".join(f"{w}:{'ok' if tops[w][0].id in good else '--'}" for w in WAYS)
            print(f"\n{marks}  {problem}\n  -> {restated}")
            if named := leaked(restated, methods):
                leaks += 1
                print(f"  !! names a method: {', '.join(named)} — this row proves nothing")
            if any((tops[w][0].id in good) != (tops["raw"][0].id in good) for w in WAYS):
                for w in WAYS:
                    print(f"     {w:<8}{', '.join(c.id for c in tops[w])}")
        n = len(cases)
        line = f"{path.name}: " + "   ".join(
            f"{w} {hits[w][0]}/{n} ({hits[w][1]}/{n} top-3)" for w in WAYS
        )
        line += f"   rewrite {sum(seconds) / n:.1f} s/problem"
        if leaks:
            line += f"   ({leaks} restatement(s) named a method; discount those)"
        totals.append(line)
        print()

    print("\n".join(["=== top-1 (top-3)", *totals]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
