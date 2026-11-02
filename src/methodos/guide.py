"""Structured guidance parsed from a method's Markdown companion.

Every `methods/*.md` follows the same shape, and this module relies on it:

  * `## When *not* to use`               -> bullets             -> `not_a_fit_when`
  * `## Facilitation outline (<length>)` -> numbered steps      -> `steps`, `outline_duration`
    (also `## Outline (<length>)` and `## Facilitation outline: <label>`; the length is optional)
  * `## Common pitfalls`                 -> bullets             -> `pitfalls`
  * `## See also`                        -> `- [Label](Target) — note` -> `see_also`

A step may open with a time box such as `(5 min)`; indented lines continue the
item above them. Inline Markdown (links, emphasis) is reduced to plain text,
because the user page renders everything escaped.

The Markdown stays the single source: nothing here is copied into the JSON. And
parsing never raises on content — a missing or malformed section comes back
empty, so one badly edited file degrades its own guidance instead of breaking
`get_method` for it.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, Field

_NUMBERED = re.compile(r"^\d+\.\s+(.*)$")
_BULLET = re.compile(r"^-\s+(.*)$")
_TIME_BOX = re.compile(r"^\((\d[^)]*)\)\s*(.*)$")
# "Facilitation outline (45 min)", but also "Outline (...)" and
# "Facilitation outline: one selection meeting (2 h)" — the catalog has all three.
_OUTLINE = re.compile(r"^(?:Facilitation )?[Oo]utline\s*(?::\s*(.+?)|\((.+)\))?\s*$")
_SEE_ALSO = re.compile(r"^\[([^\]]+)\]\(([^)\s]+)\)\s*(?:—\s*(.*))?$")
_LINK = re.compile(r"\[([^\]]+)\]\([^)]*\)")
_EMPHASIS = re.compile(r"(\*{1,2})([^*]+)\1")


class GuideStep(BaseModel):
    text: str
    time_box: str | None = Field(description="e.g. '5 min'; null when the step has none.")


class SeeAlsoLink(BaseModel):
    label: str
    method_id: str | None = Field(description="Set when the link points at another method.")
    url: str | None = Field(description="Set when the link points outside the catalog.")
    note: str | None = None


class MethodGuide(BaseModel):
    outline_duration: str | None = Field(
        description="The outline's own length label, e.g. '45 min' or 'half a day'."
    )
    steps: list[GuideStep]
    not_a_fit_when: list[str]
    pitfalls: list[str]
    see_also: list[SeeAlsoLink]


def _plain(text: str) -> str:
    return _EMPHASIS.sub(r"\2", _LINK.sub(r"\1", text)).strip()


def _sections(markdown: str) -> dict[str, list[str]]:
    """Body lines under each `## ` heading, keyed by the heading text."""
    out: dict[str, list[str]] = {}
    current: list[str] | None = None
    for line in markdown.splitlines():
        if line.startswith("## "):
            current = out.setdefault(line[3:].strip(), [])
        elif line.startswith("# "):
            current = None
        elif current is not None:
            current.append(line)
    return out


def _items(lines: list[str], start: re.Pattern[str]) -> list[str]:
    """List items opened by `start`; indented lines are joined onto the item above."""
    items: list[str] = []
    for line in lines:
        m = start.match(line)
        if m:
            items.append(m.group(1).strip())
        elif items and line[:1].isspace() and line.strip():
            items[-1] += " " + line.strip()
    return items


def parse_guide(markdown: str) -> MethodGuide:
    """Parse the four guidance sections. Missing sections come back empty."""
    sections = _sections(markdown)

    outline_duration: str | None = None
    steps: list[GuideStep] = []
    for heading, body in sections.items():
        m = _OUTLINE.match(heading)
        if m:
            outline_duration = m.group(1) or m.group(2)
            for item in _items(body, _NUMBERED):
                box = _TIME_BOX.match(item)
                text, time_box = (box.group(2), box.group(1)) if box else (item, None)
                steps.append(GuideStep(text=_plain(text), time_box=time_box))
            break

    see_also: list[SeeAlsoLink] = []
    for item in _items(sections.get("See also", []), _BULLET):
        m = _SEE_ALSO.match(item)
        if not m:
            continue
        label, target, note = m.groups()
        is_method = target.endswith(".md")
        see_also.append(
            SeeAlsoLink(
                label=_plain(label),
                method_id=target[: -len(".md")] if is_method else None,
                url=None if is_method else target,
                note=_plain(note) if note else None,
            )
        )

    return MethodGuide(
        outline_duration=outline_duration,
        steps=steps,
        not_a_fit_when=[_plain(i) for i in _items(sections.get("When *not* to use", []), _BULLET)],
        pitfalls=[_plain(i) for i in _items(sections.get("Common pitfalls", []), _BULLET)],
        see_also=see_also,
    )
