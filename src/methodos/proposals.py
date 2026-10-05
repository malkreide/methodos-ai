"""Method proposals — an append-only inbox, plus a prefilled GitHub issue link.

A proposal is not a method. It is what someone knows about one — a name, the
problem it answers, sources — and it reaches the catalog only the way every
other method does: the `method-author` agent turns it into a draft pull
request, and the owner's merge is the review (see docs/curation.md). Nothing
here writes to `methods/`.

Two exits, because the people who know a good method mostly have no GitHub
account:

  * Every proposal is appended to `proposals.jsonl` on the server, the same
    placeholder shape as `feedback.jsonl`.
  * `issue_url` builds a link to the "Propose a method" issue form with the
    fields already filled in. The person who has an account opens it, reads
    it and submits it under their own name; the server never holds a GitHub
    token and never posts on anyone's behalf.

Privacy: every text field is stored verbatim, like the query in the feedback
log. The console says so to the person typing.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Literal
from urllib.parse import urlencode

from pydantic import BaseModel, Field
from ulid import ULID

from methodos.feedback import _append_line, _now_iso
from methodos.models import Context

ISSUE_TEMPLATE = "method-proposal.yml"

MAX_ISSUE_URL = 8000
"""GitHub rejects longer URLs. Percent-encoded German text roughly doubles in
length, so a long proposal can cross it; `issue_url` then drops optional fields
rather than produce a link that fails."""


class ProposalEvent(BaseModel):
    event: Literal["proposal"] = "proposal"
    timestamp: str
    proposal_id: str
    name: str
    problem: str
    description: str | None = None
    sources: str | None = None
    links: list[str] = Field(default_factory=list)
    contexts: list[Context] = Field(default_factory=list)
    existing_method_id: str | None = None
    similar_method_ids: list[str] = Field(
        default_factory=list,
        description="What the catalog search returned for `problem` at submission "
        "time — the first thing the reviewer checks for a duplicate.",
    )


def log_proposal(
    *,
    name: str,
    problem: str,
    description: str | None,
    sources: str | None,
    links: list[str],
    contexts: list[Context],
    existing_method_id: str | None,
    similar_method_ids: list[str],
    path: Path,
) -> ProposalEvent:
    """Append a proposal. Returns the stored event, id and timestamp included."""
    ev = ProposalEvent(
        timestamp=_now_iso(),
        proposal_id=str(ULID()),
        name=name,
        problem=problem,
        description=description,
        sources=sources,
        links=links,
        contexts=contexts,
        existing_method_id=existing_method_id,
        similar_method_ids=similar_method_ids,
    )
    _append_line(path, ev)
    return ev


def read_proposals(path: Path) -> Iterator[ProposalEvent]:
    """Stream proposals. Lenient like `feedback.read_events`."""
    if not path.exists():
        return
    with path.open(encoding="utf-8") as f:
        for lineno, raw in enumerate(f, 1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                yield ProposalEvent.model_validate(json.loads(raw))
            except Exception as e:
                print(f"proposals: skipped malformed line {lineno}: {e}", file=sys.stderr)


class IssueLink(BaseModel):
    url: str | None = Field(description="null when even the shortest form exceeds GitHub's limit.")
    omitted: list[str] = Field(
        default_factory=list,
        description="Issue-form fields left out to fit the URL limit. They have to "
        "be pasted into the form by hand; the server's copy is complete.",
    )


def issue_url(proposal: ProposalEvent, repo: str) -> IssueLink:
    """A link to the issue form with the proposal filled in.

    Keys are the field ids in `.github/ISSUE_TEMPLATE/method-proposal.yml`;
    rename one there and the prefill silently stops working for it, which
    `test_issue_url_keys_match_the_issue_form` catches. Dropdown prefills are
    passed as labels — the person reviews the form before submitting, so a
    value GitHub does not take is visible rather than lost.
    """
    sources = "\n".join(
        part for part in [proposal.sources or "", *(f"- {u}" for u in proposal.links)] if part
    )
    fields: dict[str, str] = {
        "template": ISSUE_TEMPLATE,
        "title": f"Method: {proposal.name}",
        "name": proposal.existing_method_id or proposal.name,
        "problem": proposal.problem,
        "sources": sources,
        "contexts": ",".join(c.value for c in proposal.contexts),
        "existing": (
            "Yes (name it above)" if proposal.existing_method_id else "No, it is a new method"
        ),
        "description": proposal.description or "",
    }
    base = f"https://github.com/{repo}/issues/new?"
    omitted: list[str] = []
    # Least important first: what is dropped still sits in proposals.jsonl.
    for drop in (None, "description", "sources", "problem"):
        if drop is not None and fields.pop(drop, ""):
            omitted.append(drop)
        url = base + urlencode({k: v for k, v in fields.items() if v})
        if len(url) <= MAX_ISSUE_URL:
            return IssueLink(url=url, omitted=omitted)
    return IssueLink(url=None, omitted=omitted)
