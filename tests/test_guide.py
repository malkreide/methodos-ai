"""Parsing the Markdown companions into guidance the user page can render.

The last test runs against the shipped catalog on purpose: the parser is only
as good as its fit to the 23 real files, and a method whose outline stops
parsing must fail here rather than show an empty checklist to a user.
"""

from __future__ import annotations

from pathlib import Path

from methodos.guide import MethodGuide, parse_guide

METHODS_DIR = Path(__file__).parent.parent / "methods"

FIVE_WHYS_LIKE = """# X

## When *not* to use

- When several causes contributed — use an [Ishikawa diagram](Ishikawa_Diagram.md)
- For problems nobody has first-hand knowledge of

## Facilitation outline (45 min)

1. (5 min) Write the failure as one factual sentence.
2. (25 min) Ask why. Write the answer.
   Each link must be supported with evidence.
3. Assign one owner.

## Common pitfalls

- Ending at "human error"

## See also

- [Ishikawa (Fishbone) Diagram](Ishikawa_Diagram.md) — when the failure has several causes
- [Wikipedia: Five whys](https://en.wikipedia.org/wiki/Five_whys)
"""


def test_steps_keep_time_box_and_join_continuation_lines():
    g = parse_guide(FIVE_WHYS_LIKE)
    assert g.outline_duration == "45 min"
    assert [s.time_box for s in g.steps] == ["5 min", "25 min", None]
    assert (
        g.steps[1].text == "Ask why. Write the answer. Each link must be supported with evidence."
    )
    assert g.steps[2].text == "Assign one owner."


def test_bullet_sections_are_parsed():
    g = parse_guide(FIVE_WHYS_LIKE)
    assert len(g.not_a_fit_when) == 2
    assert g.pitfalls == ['Ending at "human error"']


def test_inline_markdown_is_reduced_to_plain_text():
    """The page escapes everything it renders, so raw Markdown would show literally."""
    g = parse_guide(FIVE_WHYS_LIKE.replace("one factual sentence", "*one* factual sentence"))
    assert g.not_a_fit_when[0] == "When several causes contributed — use an Ishikawa diagram"
    assert g.steps[0].text == "Write the failure as one factual sentence."


def test_see_also_separates_methods_from_urls():
    g = parse_guide(FIVE_WHYS_LIKE)
    assert g.see_also[0].method_id == "Ishikawa_Diagram" and g.see_also[0].url is None
    assert g.see_also[0].label == "Ishikawa (Fishbone) Diagram"
    assert g.see_also[0].note == "when the failure has several causes"
    assert g.see_also[1].method_id is None
    assert g.see_also[1].url == "https://en.wikipedia.org/wiki/Five_whys"


def test_missing_sections_degrade_to_empty():
    g = parse_guide("# Only a title\n\nSome prose.\n")
    assert g == MethodGuide(
        outline_duration=None, steps=[], not_a_fit_when=[], pitfalls=[], see_also=[]
    )


def test_every_shipped_method_yields_usable_guidance():
    ids = {p.stem for p in METHODS_DIR.glob("*.json")}
    mds = sorted(METHODS_DIR.glob("*.md"))
    assert len(mds) == len(ids)
    for md in mds:
        g = parse_guide(md.read_text(encoding="utf-8"))
        assert len(g.steps) >= 3, md.name
        assert g.not_a_fit_when and g.pitfalls and g.see_also, md.name
        assert g.outline_duration, md.name
        for link in g.see_also:
            assert link.method_id is None or link.method_id in ids, (md.name, link.method_id)
