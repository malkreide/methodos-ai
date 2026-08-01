"""MCP server exposing the method catalog over stdio.

Thin by design: every tool here unpacks arguments, calls into `mcp_tools`, and
translates errors. The contract those tools return — what was narrowed, on what
basis, and when a match is too weak to trust — lives in `mcp_tools`, which
carries no `mcp` dependency and is therefore covered by the CI test run.

Retrieval only. The server never calls an LLM, even though `search.search()`
would: the caller *is* a model, with the user's full context in hand, so a
second model explaining the ranking to the first would cost an extra call and a
key to produce a worse explanation. `explain()` stays the CLI's job.

Run it:
    methodos-mcp                      # after pip install -e ".[mcp]"
    python -m methodos.mcp_server

Needs an index: `methodos ingest` first. Configuration comes from the same
`METHODOS_*` environment and `.env` the CLI uses.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations
from pydantic import Field

from methodos import mcp_tools
from methodos.config import Settings
from methodos.mcp_tools import CatalogResult, MethodDetail, MethodNotFoundError, RecommendResult
from methodos.providers import make_embedding, make_reranker
from methodos.search import StaleIndexError

_READ_ONLY = ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True)

server = MCPServer(
    name="methodos",
    instructions=(
        "A fixed catalog of structured problem-solving and decision-making methods "
        "(SWOT, Five Whys, Cynefin, RICE and similar), searchable by describing a "
        "problem in plain language.\n\n"
        "`recommend_methods` is a vector search: it always returns its nearest "
        "neighbours and never an empty list, so a result is not by itself evidence "
        "that the catalog covers the question. Read `similarity` and `guidance` "
        "before treating a match as an answer. The catalog is a closed set — "
        "`list_methods` is the complete inventory, and a method that is not in it "
        "is not available here regardless of how well known it is elsewhere."
    ),
)


def _settings() -> Settings:
    return Settings()


def _methods_dir() -> Path:
    """Where the catalog lives on disk.

    Not part of Settings, which only knows about derived artefacts. The env var
    exists because an MCP server is typically launched by a client from an
    arbitrary working directory, where the relative default resolves to nothing.
    """
    return Path(os.environ.get("METHODOS_METHODS_DIR", "methods"))


@server.tool(
    name="recommend_methods",
    description=(
        "Find methods in the catalog that fit a described problem.\n\n"
        "Describe the problem itself — the decision to make, the symptom seen, the "
        "disagreement to resolve. Do not name a method or use its vocabulary; the "
        "search matches on problem descriptions, so naming a method mostly "
        "retrieves that method.\n\n"
        "Returns nearest neighbours by vector search, ordered per `ranking_basis`. "
        "When that is 'cross-encoder', `similarity` is NOT the sort key and a "
        "lower-similarity method can legitimately outrank a higher one; do not "
        "re-sort by similarity. Compare `returned` against `total_in_scope` before "
        "concluding the catalog holds nothing else, and read `guidance` when present."
    ),
    annotations=_READ_ONLY,
)
def recommend_methods(
    problem: Annotated[
        str,
        Field(
            description="The problem in plain language, e.g. 'tickets take six "
            "weeks end to end but the actual work is only a few hours'.",
            min_length=3,
        ),
    ],
    top_k: Annotated[int, Field(description="How many methods to return.", ge=1, le=25)] = 5,
    category: Annotated[
        str | None,
        Field(
            description="Restrict to one category. Applied inside the search, not "
            "to its output, so the ranking is over that category only. Valid "
            f"values: {', '.join(mcp_tools.valid_categories())}."
        ),
    ] = None,
) -> RecommendResult:
    settings = _settings()
    if category is not None and category not in mcp_tools.valid_categories():
        raise ValueError(
            f"unknown category {category!r}. Valid: {', '.join(mcp_tools.valid_categories())}"
        )
    try:
        return mcp_tools.recommend_methods(
            problem=problem,
            embedding=make_embedding(settings),
            chroma_path=settings.chroma_path,
            top_k=top_k,
            category=category,
            reranker=make_reranker(settings),
            overfetch_factor=settings.overfetch_factor,
        )
    except StaleIndexError as e:
        raise ValueError(f"the search index is unusable: {e}") from e


@server.tool(
    name="list_methods",
    description=(
        "The complete catalog — every method, no search and no truncation. Use it "
        "to see what exists before concluding a problem is uncovered, and to check "
        "whether a method you have in mind is actually available here."
    ),
    annotations=_READ_ONLY,
)
def list_methods(
    category: Annotated[
        str | None,
        Field(
            description="Restrict to one category. Valid values: "
            f"{', '.join(mcp_tools.valid_categories())}."
        ),
    ] = None,
) -> CatalogResult:
    if category is not None and category not in mcp_tools.valid_categories():
        raise ValueError(
            f"unknown category {category!r}. Valid: {', '.join(mcp_tools.valid_categories())}"
        )
    return mcp_tools.list_methods(methods_dir=_methods_dir(), category=category)


@server.tool(
    name="get_method",
    description=(
        "Full documentation for one method: the complete Markdown companion plus "
        "its structured record. `recommend_methods` returns only a one-line use "
        "case, so call this before walking someone through a method's actual steps."
    ),
    annotations=_READ_ONLY,
)
def get_method(
    method_id: Annotated[
        str,
        Field(description="Exact id as returned by the other tools, e.g. 'SWOT'."),
    ],
) -> MethodDetail:
    try:
        return mcp_tools.get_method(method_id=method_id, methods_dir=_methods_dir())
    except MethodNotFoundError as e:
        raise ValueError(str(e)) from e


def main() -> None:
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
