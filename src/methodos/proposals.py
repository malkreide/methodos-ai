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
import re
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Literal
from urllib.parse import urlencode

from pydantic import BaseModel, Field
from ulid import ULID

from methodos.feedback import _append_line, _now_iso
from methodos.models import Context
from methodos.providers.base import LLMProvider
from methodos.uploads import Kind

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
    extracted_from: Kind | None = Field(
        default=None,
        description="Set when the person started from an uploaded file. Only the "
        "kind is kept — the file and its text are not.",
    )
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
    extracted_from: Kind | None = None,
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
        extracted_from=extracted_from,
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


DRAFT_INPUT_CHARS = 24_000
"""About 6000 tokens: enough for a handout or a half-hour transcript, and a
bound on what one upload costs at the LLM provider."""

LANGUAGES = {"de": "German", "en": "English"}


class DraftError(ValueError):
    """The model's answer could not be read as a draft."""


DraftWarning = Literal[
    "copied_text",
    "instructions_in_document",
    "source_not_in_document",
    "wrong_language",
    "from_transcript",
]
"""Findings of `check_draft`. Codes, not prose: the console words them in the
viewer's language."""


class ProposalDraft(BaseModel):
    """What the LLM made of an uploaded file. Never stored: it prefills a form."""

    name: str = ""
    problem: str = ""
    description: str = ""
    sources: str | None = None
    contexts: list[Context] = Field(default_factory=list)
    is_method: bool = True
    note: str | None = None
    warnings: list[DraftWarning] = Field(
        default_factory=list,
        description="What `check_draft` found wrong with this draft. Computed, not "
        "written by the model, so it holds whatever model produced the draft.",
    )


def draft_from_text(text: str, *, llm: LLMProvider, language: str = "en") -> ProposalDraft:
    """Ask the LLM for a proposal draft. Raises LLMError or DraftError.

    Lenient about the envelope (code fences, a sentence before the JSON) and
    strict about the content: an unknown context is dropped rather than
    failing the whole draft, because the person is about to review every
    field anyway.
    """
    from methodos.prompts.loader import render_draft_prompt, split_system_user

    prompt = render_draft_prompt(
        document=text[:DRAFT_INPUT_CHARS],
        language=LANGUAGES.get(language, "English"),
        contexts=[c.value for c in Context],
        truncated=len(text) > DRAFT_INPUT_CHARS,
    )
    system, user = split_system_user(prompt)
    # 4096: room for thinking before the JSON on current Claude models.
    raw = llm.complete(system, user, max_tokens=4096, temperature=0.2)

    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end <= start:
        raise DraftError("the model did not answer with a JSON object")
    try:
        data = json.loads(raw[start : end + 1])
    except json.JSONDecodeError as e:
        raise DraftError(f"the model's JSON is malformed: {e}") from e
    if not isinstance(data, dict):
        raise DraftError("the model did not answer with a JSON object")

    valid = {c.value for c in Context}
    contexts = data.get("contexts")
    data["contexts"] = (
        [c for c in contexts if isinstance(c, str) and c in valid]
        if isinstance(contexts, list)
        else []
    )
    for key in ("name", "problem", "description"):
        if not isinstance(data.get(key), str):
            data[key] = ""
    for key in ("sources", "note"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            data[key] = None
    if not isinstance(data.get("is_method"), bool):
        data["is_method"] = True
    if language == "de":
        # Swiss spelling, which is what this catalog's German readers write.
        # Done here rather than asked for: models trained mostly on German
        # German write ß whatever the prompt says.
        for key in ("name", "problem", "description", "sources", "note"):
            if isinstance(data.get(key), str):
                data[key] = data[key].replace("ß", "ss")
    draft = ProposalDraft.model_validate(
        {k: data[k] for k in ProposalDraft.model_fields if k in data and k != "warnings"}
    )
    draft.warnings = check_draft(draft, document=text, language=language)
    return draft


# --- checks that do not trust the model ---------------------------------------
#
# Run against Llama 3.1 8B (the CLI's default model), the draft prompt was
# followed for format every time and broken for content often enough to matter:
# an instruction planted in the document was obeyed, the description copied a
# whole passage, a misheard name from a transcript came back as the source, and
# an English document produced an English draft. Prompt wording moved some of
# that and not the rest. These checks are deterministic, so they hold for any
# model; they cannot fix a draft, only tell the person where to look.

COPY_RUN_WORDS = 12
"""Consecutive words shared with the document that count as copying. Short
enough to catch a lifted sentence, long enough that a method's own phrases
("stimmen ab, welche Themen besprochen werden") do not trip it."""

_INSTRUCTION_PATTERNS = re.compile(
    r"ignor\w*\s+(all\w*\s+)?(previous|prior|above|vorherig\w*|bisherig\w*|obig\w*)\s+"
    r"(instructions?|anweisung\w*|regeln|rules)"
    r"|^\s*(system|assistant)\s*:"
    r"|\byou are now\b|\bdu bist (jetzt|nun)\b"
    r"|\b(set|setze)\s+\W?(name|sources|contexts)\W?\s+(to|auf)\b",
    re.IGNORECASE | re.MULTILINE,
)

_SOURCE_FILLER = frozenset(
    [
        "and",
        "und",
        "the",
        "der",
        "die",
        "das",
        "des",
        "von",
        "van",
        "von",
        "for",
        "für",
        "of",
        "et",
        "al",
        "eds",
        "hrsg",
        "ed",
    ]
)

_STOPWORDS = {
    "de": frozenset(
        [
            "der",
            "die",
            "das",
            "und",
            "ist",
            "nicht",
            "ein",
            "eine",
            "einen",
            "mit",
            "zu",
            "sich",
            "auf",
            "für",
            "von",
            "dem",
            "den",
            "werden",
            "wird",
            "sie",
            "es",
            "im",
            "in",
            "auch",
            "als",
            "bei",
            "oder",
            "wenn",
        ]
    ),
    "en": frozenset(
        [
            "the",
            "and",
            "is",
            "not",
            "a",
            "an",
            "with",
            "to",
            "of",
            "for",
            "on",
            "in",
            "it",
            "they",
            "are",
            "be",
            "by",
            "or",
            "when",
            "this",
            "that",
            "their",
        ]
    ),
}


def _words(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


def check_draft(draft: ProposalDraft, *, document: str, language: str) -> list[DraftWarning]:
    """Where a draft is likely wrong, whatever model wrote it."""
    warnings: list[DraftWarning] = []

    doc_words = _words(document)
    n = COPY_RUN_WORDS
    doc_runs = {tuple(doc_words[i : i + n]) for i in range(len(doc_words) - n + 1)}
    for field in (draft.problem, draft.description):
        w = _words(field)
        if any(tuple(w[i : i + n]) in doc_runs for i in range(len(w) - n + 1)):
            warnings.append("copied_text")
            break

    if _INSTRUCTION_PATTERNS.search(document):
        warnings.append("instructions_in_document")

    if draft.sources:
        doc_vocab = set(doc_words)
        cited = [
            w
            for w in _words(draft.sources)
            if w not in _SOURCE_FILLER and (len(w) >= 3 or w.isdigit())
        ]
        if any(w not in doc_vocab for w in cited):
            warnings.append("source_not_in_document")

    target = _STOPWORDS.get(language)
    other = _STOPWORDS["en" if language == "de" else "de"]
    if target is not None:
        written = _words(f"{draft.problem} {draft.description}")
        if sum(w in other for w in written) > sum(w in target for w in written):
            warnings.append("wrong_language")

    return warnings
