"""Wiring checks for the MCP server itself.

Skipped without the `mcp` extra, which means skipped in CI — the reason the
contract lives in `mcp_tools` and is tested in `test_mcp_tools.py` instead.
What is left here is what only the real server object can answer: that the
tools are registered, that their schemas reached the protocol layer, and that
they are declared read-only.
"""

from __future__ import annotations

import asyncio

import pytest

pytest.importorskip("mcp", reason="needs the `mcp` extra: pip install -e '.[dev,mcp]'")

from methodos.mcp_server import server


@pytest.fixture(scope="module")
def tools():
    return {t.name: t for t in asyncio.run(server.list_tools())}


def test_exactly_the_three_intended_tools_are_exposed(tools):
    """`ingest` is deliberately absent: it mutates state and is the CLI's job."""
    assert set(tools) == {"recommend_methods", "list_methods", "get_method"}


def test_every_tool_is_annotated_read_only(tools):
    for name, tool in tools.items():
        assert tool.annotations is not None, f"{name} has no annotations"
        assert tool.annotations.read_only_hint is True, name
        assert tool.annotations.destructive_hint is False, name


def test_every_tool_declares_a_structured_output_schema(tools):
    """Without it the payload degrades to prose and the contract fields vanish."""
    for name, tool in tools.items():
        assert tool.output_schema, f"{name} returns unstructured output"


def test_recommend_exposes_the_fields_that_prevent_silent_narrowing(tools):
    properties = tools["recommend_methods"].output_schema["properties"]
    for field in ("returned", "total_in_scope", "total_indexed", "ranking_basis", "guidance"):
        assert field in properties, f"recommend_methods must report {field}"


def test_server_instructions_state_that_search_never_returns_empty(tools):
    """The one thing a caller cannot discover from a successful response."""
    assert server.instructions is not None
    assert "never an empty list" in server.instructions
    assert "closed set" in server.instructions
