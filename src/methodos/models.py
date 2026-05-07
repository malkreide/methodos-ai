"""Canonical data model for a management method."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, Field, StringConstraints

NonEmptyStr = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
"""A trimmed string with at least one non-whitespace character."""


class Category(StrEnum):
    """Coarse-grained categorization of methods.

    Adding a category is a non-breaking schema change; bump `schema_version`
    only when a *required* field changes.
    """

    STRATEGY = "strategy"
    DECISION_MAKING = "decision-making"
    ANALYSIS = "analysis"
    PRIORITIZATION = "prioritization"
    RETROSPECTIVE = "retrospective"


class Duration(BaseModel):
    """Estimated wall-clock time to apply the method end-to-end."""

    min_minutes: int = Field(ge=5, le=10_000)
    max_minutes: int = Field(ge=5, le=10_000)

    def model_post_init(self, __context: Any) -> None:
        if self.max_minutes < self.min_minutes:
            raise ValueError("max_minutes must be >= min_minutes")


class Method(BaseModel):
    """A management method as represented in the catalog.

    The `use_case` field is the text we embed for retrieval. All other fields
    are surfaced to the user via CLI rendering or filtering. Adding a new
    field that is *not* required is non-breaking; adding a required field
    bumps `schema_version` and requires a migration of existing JSON files.
    """

    schema_version: int = 1
    id: Annotated[str, StringConstraints(pattern=r"^[A-Z][A-Za-z0-9_]*$")]
    name: NonEmptyStr
    category: Category
    use_case: Annotated[str, StringConstraints(min_length=40)]
    strengths: list[NonEmptyStr] = Field(min_length=1, max_length=12)
    weaknesses: list[NonEmptyStr] = Field(min_length=1, max_length=12)
    complexity_score: int = Field(ge=1, le=5)
    estimated_duration: Duration
    references: list[str] = Field(default_factory=list)

    @property
    def doc_path(self) -> str:
        """Relative path to the human-readable Markdown companion."""
        return f"methods/{self.id}.md"
