"""Contract tests for the MCP tool layer.

These use fakes and never import `mcp`, so they run in CI on `".[dev]"`. That
is the point of the mcp_tools / mcp_server split: the fields that stop a calling
model from being silently misled are worth more than the decorator wiring, and
only one of the two can be covered by the default install.

What is asserted here is the *contract*, not the ranking — ranking quality is
`test_search.py`'s job with fakes and `test_integration.py`'s with real models.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from methodos.ingest import ingest
from methodos.mcp_tools import (
    WEAK_MATCH_SIMILARITY,
    MethodNotFoundError,
    get_method,
    list_methods,
    recommend_methods,
)
from methodos.search import StaleIndexError

CATEGORIES = {"Alpha": "strategy", "Beta": "strategy", "Gamma": "analysis"}


def _write(dir: Path, id: str, use_case: str, category: str) -> None:
    payload = {
        "id": id,
        "name": id,
        "category": category,
        "use_case": use_case,
        "strengths": ["s"],
        "weaknesses": ["w"],
        "complexity_score": 2,
        "estimated_duration": {"min_minutes": 30, "max_minutes": 60},
    }
    (dir / f"{id}.json").write_text(json.dumps(payload), encoding="utf-8")
    (dir / f"{id}.md").write_text(f"# {id}\n\nFull documentation for {id}.\n", encoding="utf-8")


@pytest.fixture
def catalog(tmp_path: Path) -> Path:
    methods = tmp_path / "methods"
    methods.mkdir()
    _write(methods, "Alpha", "alpha " * 9, CATEGORIES["Alpha"])
    _write(methods, "Beta", "beta " * 11, CATEGORIES["Beta"])
    _write(methods, "Gamma", "gamma " * 9, CATEGORIES["Gamma"])
    return methods


@pytest.fixture
def indexed(catalog: Path, tmp_path: Path, fake_embedding) -> Path:
    chroma_path = tmp_path / "chroma"
    ingest(methods_dir=catalog, chroma_path=chroma_path, embedding=fake_embedding)
    return chroma_path


# --- recommend_methods: the narrowings must be visible -----------------------


def test_truncated_result_reports_the_full_catalog_size(indexed, fake_embedding):
    """A caller seeing 1 of 3 must be able to tell it is not seeing everything."""
    result = recommend_methods(
        problem="alpha alpha alpha",
        embedding=fake_embedding,
        chroma_path=indexed,
        top_k=1,
    )
    assert result.returned == 1
    assert result.total_indexed == 3
    assert result.total_in_scope == 3


def test_category_filter_narrows_the_search_not_its_output(indexed, fake_embedding):
    """The filter goes to Chroma, so top_k applies *after* it.

    Post-filtering would let a top_k of 2 return zero strategy methods while two
    exist — the caller would read that as "the catalog has none".
    """
    result = recommend_methods(
        problem="gamma gamma gamma",
        embedding=fake_embedding,
        chroma_path=indexed,
        top_k=2,
        category="strategy",
    )
    assert result.category == "strategy"
    assert result.total_in_scope == 2, "two methods are in 'strategy'"
    assert result.total_indexed == 3
    assert result.returned == 2, "the strategy methods must survive a gamma-shaped query"
    assert {m.id for m in result.matches} == {"Alpha", "Beta"}
    assert all(m.category == "strategy" for m in result.matches)


def test_ranking_basis_reports_embedding_when_no_reranker_ran(indexed, fake_embedding):
    result = recommend_methods(
        problem="alpha alpha alpha",
        embedding=fake_embedding,
        chroma_path=indexed,
        top_k=3,
    )
    assert result.ranking_basis == "embedding-similarity"
    assert all(m.rerank_score is None for m in result.matches)


def test_ranking_basis_reports_cross_encoder_when_one_did(indexed, fake_embedding, fake_reranker):
    """Read off the data, not off `reranker is not None`.

    `make_reranker` degrades to None when sentence-transformers is missing, so
    an install without the `local` extra silently changes what the order means.
    The field has to follow what actually happened.
    """
    result = recommend_methods(
        problem="alpha alpha alpha",
        embedding=fake_embedding,
        chroma_path=indexed,
        top_k=3,
        reranker=fake_reranker,
    )
    assert result.ranking_basis == "cross-encoder"
    assert all(m.rerank_score is not None for m in result.matches)


def test_both_scores_survive_to_the_payload(indexed, fake_embedding, fake_reranker):
    """Neither score overwrites the other; they are different scales."""
    result = recommend_methods(
        problem="beta beta beta",
        embedding=fake_embedding,
        chroma_path=indexed,
        top_k=3,
        reranker=fake_reranker,
    )
    for m in result.matches:
        assert 0.0 <= m.similarity <= 1.0
        assert m.rerank_score is not None


# --- recommend_methods: the silent-success failure mode ----------------------


def test_weak_match_carries_actionable_guidance(indexed, fake_embedding, monkeypatch):
    """Vector search never returns empty, so a bad query still looks answered.

    The floor is patched rather than hunted for: with sha256 fakes there is no
    query that reliably scores low, and the behaviour under test is "when the
    top score is below the floor", not the floor's own value.
    """
    monkeypatch.setattr("methodos.mcp_tools.WEAK_MATCH_SIMILARITY", 1.1)
    result = recommend_methods(
        problem="entirely unrelated to this catalog",
        embedding=fake_embedding,
        chroma_path=indexed,
        top_k=2,
    )
    assert result.matches, "results are still returned — guidance is a hint, not a filter"
    assert result.guidance is not None
    assert "list_methods" in result.guidance, "must name a concrete next step"
    assert "3" in result.guidance, "must say how big the catalog actually is"
    assert "not" in result.guidance.lower(), "must forbid inventing a method"


def test_strong_match_carries_no_guidance(indexed, fake_embedding, monkeypatch):
    monkeypatch.setattr("methodos.mcp_tools.WEAK_MATCH_SIMILARITY", 0.0)
    result = recommend_methods(
        problem="alpha alpha alpha",
        embedding=fake_embedding,
        chroma_path=indexed,
        top_k=2,
    )
    assert result.guidance is None


def test_guidance_never_explains_away_a_weak_result(indexed, fake_embedding, monkeypatch):
    """A tool description that *interprets* an empty result invites confabulation.

    Guarding the phrasing in a test because it is the kind of wording that gets
    softened during an unrelated edit, and the damage is invisible: a model
    handed "this usually means X" will report X rather than retry.
    """
    monkeypatch.setattr("methodos.mcp_tools.WEAK_MATCH_SIMILARITY", 1.1)
    guidance = recommend_methods(
        problem="unrelated",
        embedding=fake_embedding,
        chroma_path=indexed,
        top_k=1,
    ).guidance
    assert guidance is not None
    for excuse in ("usually means", "likely means", "probably means", "suggests that"):
        assert excuse not in guidance.lower(), f"guidance must not license a conclusion: {excuse!r}"


def test_weak_match_floor_sits_between_the_two_measured_populations():
    """Pins the constant's justification, so a casual bump has to argue with it.

    Measured on the shipped catalog: the weakest pinned integration probe tops
    out at 0.321, and queries the catalog does not cover reach 0.127 at most.
    """
    assert 0.127 < WEAK_MATCH_SIMILARITY < 0.321


# --- errors that a model has to be able to act on ----------------------------


def test_stale_index_is_raised_not_swallowed(indexed, fake_embedding):
    from tests.conftest import FakeEmbedding

    other = FakeEmbedding(dimensions=8)
    other.name = "some-other-provider"
    with pytest.raises(StaleIndexError) as excinfo:
        recommend_methods(problem="alpha", embedding=other, chroma_path=indexed, top_k=1)
    assert "ingest" in str(excinfo.value)


def test_unknown_method_id_lists_the_valid_ones(catalog):
    with pytest.raises(MethodNotFoundError) as excinfo:
        get_method(method_id="Nonexistent", methods_dir=catalog)
    message = str(excinfo.value)
    assert "Alpha" in message and "Beta" in message and "Gamma" in message


# --- list_methods / get_method ----------------------------------------------


def test_list_methods_returns_the_whole_catalog_untruncated(catalog):
    result = list_methods(methods_dir=catalog)
    assert result.returned == result.total == 3
    assert sorted(result.categories) == ["analysis", "strategy"]
    assert [m.id for m in result.methods] == ["Alpha", "Beta", "Gamma"]


def test_list_methods_reports_the_unfiltered_total_alongside_a_filter(catalog):
    result = list_methods(methods_dir=catalog, category="analysis")
    assert result.returned == 1
    assert result.total == 3, "the unfiltered size stays visible"
    assert result.category == "analysis"


def test_get_method_includes_the_markdown_companion(catalog):
    detail = get_method(method_id="Alpha", methods_dir=catalog)
    assert detail.id == "Alpha"
    assert "Full documentation for Alpha." in detail.documentation
    assert detail.duration_min == 30 and detail.duration_max == 60


def test_missing_companion_is_reported_as_a_sync_problem(catalog):
    (catalog / "Alpha.md").unlink()
    with pytest.raises(MethodNotFoundError) as excinfo:
        get_method(method_id="Alpha", methods_dir=catalog)
    assert "out of sync" in str(excinfo.value)
