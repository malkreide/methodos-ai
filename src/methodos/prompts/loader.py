"""Load and render prompt templates."""
from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

PROMPTS_DIR = Path(__file__).parent


def load_prompt(name: str) -> str:
    """Load a prompt template by name (without extension) from prompts/."""
    return (PROMPTS_DIR / f"{name}.txt").read_text(encoding="utf-8")


def split_system_user(text: str) -> tuple[str, str]:
    """Split a rendered prompt into (system_part, user_part) at SYSTEM:/USER: markers."""
    sys_marker = "SYSTEM:"
    user_marker = "USER:"
    if sys_marker not in text or user_marker not in text:
        raise ValueError("template must contain both SYSTEM: and USER: markers")
    sys_idx = text.index(sys_marker) + len(sys_marker)
    user_idx = text.index(user_marker)
    system_part = text[sys_idx:user_idx].strip()
    user_part = text[user_idx + len(user_marker) :].strip()
    return system_part, user_part


def _format_candidate(c: dict[str, Any]) -> str:
    strengths_b = "\n".join(f"  - {s}" for s in c["strengths"])
    weaknesses_b = "\n".join(f"  - {w}" for w in c["weaknesses"])
    return (
        f"### {c['name']}  (similarity: {c['similarity']:.2f}, "
        f"complexity: {c['complexity_score']}/5)\n"
        f"Use case: {c['use_case']}\n"
        f"Strengths:\n{strengths_b}\n"
        f"Weaknesses:\n{weaknesses_b}\n"
        f"Duration: {c['duration_min']}–{c['duration_max']} minutes\n"
        f"---"
    )


def render_explain_prompt(*, query: str, candidates: Sequence[dict[str, Any]]) -> str:
    """Render the explain template with query + candidate list.

    Uses string `.replace` rather than `.format` to avoid format-injection
    when a user's query contains literal `{` or `}` characters.
    """
    template = load_prompt("explain")
    candidates_block = "\n".join(_format_candidate(c) for c in candidates)
    return template.replace("{query}", query).replace("{candidates_block}", candidates_block)
