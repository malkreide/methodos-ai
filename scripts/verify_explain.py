"""Print the reranked ranking next to what each model says about it.

Answers the question the test suite cannot: *does a real model act on the
`ranking_basis` sentence?* `render_explain_prompt` tells the model the list is
ordered by cross-encoder relevance and that the printed similarity is not the
sort key. Whether a given model honours that or quietly re-sorts by similarity
is a property of the model, so it has to be re-checked whenever the model
changes — which is what this script is for.

Deliberately not a test. There is no threshold at which an explanation is
"correct"; the useful output is the ranking and the prose side by side, for a
human to judge. The one mechanical signal — which method the explanation
introduces first — is printed as a verdict line, the same proxy asserted by
`test_real_llm_leads_with_the_reranked_top_not_the_most_similar`.

Needs a reachable backend for every model named. Requires an ingested index and
the `local` extra for the cross-encoder.

Examples:
    # the default model from Settings / .env
    python scripts/verify_explain.py

    # compare two backends on the same ranking
    python scripts/verify_explain.py \
        --model ollama/llama3.1:8b --model openai/gpt-4o-mini

    # a problem of your own
    python scripts/verify_explain.py --query "our release keeps slipping"

Exit codes:
  0  - every model answered (say nothing about the *quality* of the answers)
  1  - a model call failed, or the index is missing/stale
  2  - usage error
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from methodos.config import Settings
from methodos.providers import make_embedding, make_llm, make_reranker
from methodos.search import Candidate, StaleIndexError, retrieve, search

# Chosen because the reranker and the embedding disagree here, measured against
# the 23-method catalog at top_k=3, overfetch_factor=2:
#
#   SWOT Analysis         sim 0.457  rerank  +7.14   (embedding had it #3)
#   Porter's Five Forces  sim 0.469  rerank  -8.14   (embedding had it #1)
#   PESTEL Analysis       sim 0.465  rerank  -8.22   (embedding had it #2)
#
# So the prompt presents a top candidate that is *less* similar than both
# entries below it. Without that inversion the model is never actually asked to
# trust the stated ranking basis and every model looks compliant — which is how
# the first draft of this script picked a query that proved nothing. The
# no-conflict path below exists to say so out loud rather than print a
# reassuring verdict.
DEFAULT_QUERY = "internal strengths and weaknesses vs external opportunities and threats"


def _first_mention(text: str, method_name: str) -> int | None:
    """Index where `method_name` is first referred to, or None.

    Matches the leading word only — models write "Porter's Five Forces", "the
    Five Forces model", or just "Porter's". Kept in sync by hand with the copy
    in tests/test_integration.py; four lines is cheaper than a shared import
    from tests into scripts.
    """
    token = method_name.split()[0].removesuffix("'s").strip(".,:;'\"").lower()
    idx = text.lower().find(token)
    return None if idx < 0 else idx


def _print_ranking(candidates: list[Candidate]) -> None:
    by_similarity = sorted(candidates, key=lambda c: c.similarity, reverse=True)
    print(f"  {'#':<3}{'method':<28}{'similarity':>11}{'rerank':>10}   embedding rank")
    for pos, c in enumerate(candidates, start=1):
        rerank = f"{c.rerank_score:+.2f}" if c.rerank_score is not None else "—"
        was = by_similarity.index(c) + 1
        moved = "" if was == pos else f"  (was #{was})"
        print(f"  {pos:<3}{c.name[:27]:<28}{c.similarity:>11.3f}{rerank:>10}{moved}")

    conflicts = [c for c in candidates[1:] if c.similarity > candidates[0].similarity]
    if conflicts:
        print(
            f"\n  Conflict present: {candidates[0].name} leads on rerank despite a lower "
            f"similarity than {', '.join(c.name for c in conflicts)}."
        )
    else:
        print(
            "\n  NOTE: no similarity/rerank conflict for this query — the top result is "
            "also the most similar, so this run cannot show whether the model trusts "
            "the reranked order. Try a different --query."
        )


def _verdict(explanation: str, candidates: list[Candidate]) -> str:
    mentioned = [
        (idx, c) for c in candidates if (idx := _first_mention(explanation, c.name)) is not None
    ]
    if not mentioned:
        return "LEADS WITH: (no candidate named in the explanation)"
    mentioned.sort()
    leader = mentioned[0][1]
    if leader.id == candidates[0].id:
        return f"LEADS WITH: {leader.name} — matches the reranked top."
    return (
        f"LEADS WITH: {leader.name} (similarity {leader.similarity:.3f}) "
        f"but the reranked top is {candidates[0].name} (similarity "
        f"{candidates[0].similarity:.3f}) — model may be re-sorting by similarity."
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--query", default=DEFAULT_QUERY, help="problem to ask about")
    parser.add_argument(
        "--model",
        action="append",
        dest="models",
        metavar="LITELLM_MODEL",
        help="litellm model string, repeatable. Defaults to METHODOS_MODEL / Settings.",
    )
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--chroma-path", type=Path, default=None)
    parser.add_argument(
        "--no-rerank",
        action="store_true",
        help="skip the cross-encoder — leaves no conflict to test, but useful "
        "for seeing what the prompt looks like without one",
    )
    args = parser.parse_args()

    base = Settings()
    chroma_path = args.chroma_path or base.chroma_path
    models = args.models or [base.model]

    embedding = make_embedding(base)
    reranker = None if args.no_rerank else make_reranker(base, required=True)

    try:
        candidates = retrieve(
            query=args.query,
            embedding=embedding,
            chroma_path=chroma_path,
            top_k=args.top_k,
            reranker=reranker,
            overfetch_factor=base.overfetch_factor,
        )
    except StaleIndexError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if not candidates:
        print(
            f"error: no candidates for {args.query!r} — is {chroma_path} ingested?", file=sys.stderr
        )
        return 1

    print(f"query: {args.query!r}\n")
    _print_ranking(candidates)

    failures = 0
    for model in models:
        print(f"\n{'=' * 78}\nmodel: {model}\n{'=' * 78}")
        try:
            # Re-runs retrieval per model. Wasteful, but it keeps the shown
            # ranking and the explanation provably from the same call rather
            # than two paths that could drift.
            result = search(
                query=args.query,
                embedding=embedding,
                llm=make_llm(base.model_copy(update={"model": model})),
                chroma_path=chroma_path,
                top_k=args.top_k,
                reranker=reranker,
                overfetch_factor=base.overfetch_factor,
            )
        # Broad on purpose: one unreachable backend should not hide the models
        # that did answer, and litellm raises a wide range of provider errors.
        except Exception as e:
            failures += 1
            print(f"FAILED: {type(e).__name__}: {e}", file=sys.stderr)
            continue

        explanation = result.explanation or ""
        print(explanation.strip() or "(empty explanation)")
        print(f"\n  → {_verdict(explanation, result.candidates)}")

    if failures:
        print(f"\n{failures}/{len(models)} model(s) failed to answer.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
