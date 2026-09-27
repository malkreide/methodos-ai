"""Canonical data model for a management method."""

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, Field, StringConstraints, model_validator

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
    FACILITATION = "facilitation"
    CHANGE_MANAGEMENT = "change-management"


class Context(StrEnum):
    """The kind of organisation a method has been shown to work in.

    Deliberately coarse: it answers "is this for us at all?", not "which
    department". Finer distinctions belong in `use_cases`, where the search
    can see them.
    """

    BUSINESS = "business"
    PUBLIC_SECTOR = "public-sector"
    EDUCATION = "education"
    NONPROFIT = "nonprofit"
    PERSONAL = "personal"


class Format(StrEnum):
    """How the method can be run."""

    IN_PERSON = "in-person"
    HYBRID = "hybrid"
    REMOTE = "remote"
    ASYNC = "async"


class AssetKind(StrEnum):
    TEMPLATE = "template"
    WORKSHEET = "worksheet"
    SLIDES = "slides"
    BOARD = "board"
    CHECKLIST = "checklist"
    VIDEO = "video"
    OTHER = "other"


class AssetAccess(StrEnum):
    """Who may use an asset.

    `open` assets are part of the public catalog. `premium` assets are not: the
    catalog only *points* at them, and the file itself lives wherever it is
    sold or licensed — never in this repository, which is public.
    """

    OPEN = "open"
    PREMIUM = "premium"


class Duration(BaseModel):
    """Estimated wall-clock time to apply the method end-to-end."""

    min_minutes: int = Field(ge=5, le=10_000)
    max_minutes: int = Field(ge=5, le=10_000)

    def model_post_init(self, __context: Any) -> None:
        if self.max_minutes < self.min_minutes:
            raise ValueError("max_minutes must be >= min_minutes")


class GroupSize(BaseModel):
    """How many participants the method works for."""

    min_people: int = Field(ge=1, le=10_000)
    max_people: int = Field(ge=1, le=10_000)

    def model_post_init(self, __context: Any) -> None:
        if self.max_people < self.min_people:
            raise ValueError("max_people must be >= min_people")


AssetPath = Annotated[
    str,
    StringConstraints(pattern=r"^[A-Za-z0-9_-][A-Za-z0-9_.-]*(/[A-Za-z0-9_-][A-Za-z0-9_.-]*)*$"),
]
"""Relative to `methods/assets/<Id>/`.

No segment may start with a dot, which rules out `..` and hidden files without
the look-ahead the schema's regex engine does not support.
"""


class Asset(BaseModel):
    """Supporting material for a method: a template, a board, a slide deck.

    Exactly one of `path` and `url`. A `path` is a file shipped in this
    repository under `methods/assets/<Id>/`; a `url` points elsewhere. Premium
    assets must use `url` — see AssetAccess.
    """

    title: NonEmptyStr
    kind: AssetKind
    access: AssetAccess = AssetAccess.OPEN
    path: AssetPath | None = None
    url: Annotated[str, StringConstraints(pattern=r"^https://")] | None = None
    license: NonEmptyStr | None = None
    """SPDX identifier where one exists, e.g. 'CC-BY-SA-4.0'."""

    @model_validator(mode="after")
    def _one_location(self) -> Asset:
        if (self.path is None) == (self.url is None):
            raise ValueError("an asset needs exactly one of `path` and `url`")
        if self.access is AssetAccess.PREMIUM and self.path is not None:
            raise ValueError(
                "premium assets must be referenced by `url`: the repository is public, "
                "so a file under methods/assets/ is open by definition"
            )
        return self


UseCaseStr = Annotated[str, StringConstraints(min_length=40, strip_whitespace=True)]


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
    use_cases: list[UseCaseStr] = Field(default_factory=list, max_length=20)
    """Further situations the method fits, each embedded as its own vector.

    `use_case` is the canonical description; these are the other problems the
    same method answers — often in a different context or phrased for a
    different audience. A query only has to be close to *one* of them.
    """
    strengths: list[NonEmptyStr] = Field(min_length=1, max_length=12)
    weaknesses: list[NonEmptyStr] = Field(min_length=1, max_length=12)
    complexity_score: int = Field(ge=1, le=5)
    estimated_duration: Duration
    references: list[str] = Field(default_factory=list)

    # --- optional metadata (non-breaking: absent in schema_version 1 files) ---
    contexts: list[Context] = Field(default_factory=list)
    formats: list[Format] = Field(default_factory=list)
    group_size: GroupSize | None = None
    audience: list[NonEmptyStr] = Field(default_factory=list, max_length=12)
    language: Annotated[str, StringConstraints(pattern=r"^[a-z]{2}$")] = "en"
    """ISO 639-1 code of the text in this file and its Markdown companion."""
    assets: list[Asset] = Field(default_factory=list)
    owner: NonEmptyStr | None = None
    last_reviewed: date | None = None
    """When the owner last checked the content against current practice."""

    @model_validator(mode="after")
    def _no_duplicates(self) -> Method:
        for field in ("contexts", "formats", "use_cases"):
            values = getattr(self, field)
            if len(values) != len(set(values)):
                raise ValueError(f"{field} contains duplicates")
        if self.use_case in self.use_cases:
            raise ValueError("use_cases repeats use_case")
        return self

    @property
    def doc_path(self) -> str:
        """Relative path to the human-readable Markdown companion."""
        return f"methods/{self.id}.md"
