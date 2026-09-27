"""Audit the catalog for maintenance work: the curator agent's to-do list.

Deterministic on purpose. It decides *what* needs attention; the
`method-curator` agent (.claude/agents/) decides *how* to fix it and opens a
pull request, and the owner's merge is the review. Keeping the finding step
out of the model means the backlog is reproducible and can be checked in CI.

Findings, most urgent first:

  low-rating      avg rating < 3 over at least --min-ratings ratings
  never-reviewed  no `last_reviewed`
  stale           `last_reviewed` older than --max-age-days
  broken-link     a reference URL that does not answer, or that redirects to
                  another site's shallower page, or loops (only with --check-links)
  unclassified    no `contexts` or no `formats`
  single-use-case no further `use_cases` — the method is findable one way only
  no-owner        no `owner`

Usage:
    python scripts/audit_catalog.py                     # Markdown report
    python scripts/audit_catalog.py --json              # for agents
    python scripts/audit_catalog.py --check-links       # also HEAD every reference

Exit code is 0 whatever it finds: a backlog is not a failure.
"""

from __future__ import annotations

import argparse
import http.client
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

from methodos.feedback import stats
from methodos.models import Method

SEVERITY = {
    "low-rating": 0,
    "never-reviewed": 1,
    "stale": 1,
    "broken-link": 2,
    "unclassified": 3,
    "single-use-case": 4,
    "no-owner": 5,
}


@dataclass(frozen=True)
class Finding:
    method_id: str
    kind: str
    detail: str


def _host(netloc: str) -> str:
    return netloc.lower().removeprefix("www.")


def _depth(path: str) -> int:
    return len([seg for seg in path.split("/") if seg])


def _landed_elsewhere(requested: str, landed: str) -> bool:
    """A redirect to another site's shallower page: the content is gone.

    Deep pages that a site retires often redirect to its home or section page
    with a 200, which a status check calls healthy. Scheme, `www.` and trailing
    slashes are routine; a new host *and* a shallower path is not.
    """
    a, b = urllib.parse.urlsplit(requested), urllib.parse.urlsplit(landed)
    return _host(a.netloc) != _host(b.netloc) and _depth(b.path) < _depth(a.path)


def _link_ok(url: str, timeout: float) -> bool:
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "methodos-audit"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            return bool(res.status < 400) and not _landed_elsewhere(url, res.geturl())
    except urllib.error.HTTPError as e:
        # Some sites refuse HEAD but serve GET, so a 403 or 405 is not proof of
        # anything. A 404/410 is. So is a 3xx: urllib only surfaces one as an
        # error after following redirects failed, i.e. a loop no client escapes.
        return e.code not in (404, 410) and not 300 <= e.code < 400
    except (urllib.error.URLError, http.client.HTTPException, OSError, ValueError):
        # OSError covers timeouts and resets; HTTPException covers a server that
        # drops the connection mid-response. Either way one bad site must not
        # abort the audit of every other method.
        return False


def audit(
    *,
    methods_dir: Path,
    feedback_path: Path | None,
    today: date,
    max_age_days: int = 365,
    min_ratings: int = 3,
    check_links: bool = False,
    link_timeout: float = 8.0,
) -> list[Finding]:
    methods = [
        Method.model_validate_json(p.read_text(encoding="utf-8"))
        for p in sorted(methods_dir.glob("*.json"))
    ]
    ratings = stats(feedback_path) if feedback_path else {}

    out: list[Finding] = []
    for m in methods:
        st = ratings.get(m.id)
        if st and st.rating_count >= min_ratings and st.avg_rating < 3:
            out.append(
                Finding(
                    m.id,
                    "low-rating",
                    f"avg {st.avg_rating:.2f} over {st.rating_count} ratings",
                )
            )
        if m.last_reviewed is None:
            out.append(Finding(m.id, "never-reviewed", "no last_reviewed date"))
        elif (age := (today - m.last_reviewed).days) > max_age_days:
            out.append(Finding(m.id, "stale", f"last reviewed {m.last_reviewed} ({age} days)"))
        if check_links:
            out.extend(
                Finding(m.id, "broken-link", url)
                for url in m.references
                if not _link_ok(url, link_timeout)
            )
        missing = [f for f in ("contexts", "formats") if not getattr(m, f)]
        if missing:
            out.append(Finding(m.id, "unclassified", "missing " + ", ".join(missing)))
        if not m.use_cases:
            out.append(Finding(m.id, "single-use-case", "no further use_cases"))
        if m.owner is None:
            out.append(Finding(m.id, "no-owner", "no owner"))

    return sorted(out, key=lambda f: (SEVERITY[f.kind], f.method_id))


def _markdown(findings: list[Finding], total: int) -> str:
    if not findings:
        return f"All {total} methods are up to date.\n"
    affected = len({f.method_id for f in findings})
    lines = [
        f"# Catalog audit: {len(findings)} findings across {affected} of {total} methods",
        "",
        "| Method | Finding | Detail |",
        "|---|---|---|",
    ]
    lines += [f"| {f.method_id} | {f.kind} | {f.detail} |" for f in findings]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--methods-dir", type=Path, default=Path("methods"))
    parser.add_argument(
        "--feedback",
        type=Path,
        default=Path("data/feedback.jsonl"),
        help="Feedback log for rating signals; skipped if it does not exist.",
    )
    parser.add_argument("--max-age-days", type=int, default=365)
    parser.add_argument("--min-ratings", type=int, default=3)
    parser.add_argument("--check-links", action="store_true")
    parser.add_argument("--json", action="store_true", help="Machine-readable output.")
    parser.add_argument("--today", type=date.fromisoformat, default=date.today())
    args = parser.parse_args()

    if not args.methods_dir.is_dir():
        print(f"error: {args.methods_dir} is not a directory", file=sys.stderr)
        return 2

    findings = audit(
        methods_dir=args.methods_dir,
        feedback_path=args.feedback if args.feedback.exists() else None,
        today=args.today,
        max_age_days=args.max_age_days,
        min_ratings=args.min_ratings,
        check_links=args.check_links,
    )
    if args.json:
        print(json.dumps([asdict(f) for f in findings], indent=2))
    else:
        print(_markdown(findings, total=len(list(args.methods_dir.glob("*.json")))), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
