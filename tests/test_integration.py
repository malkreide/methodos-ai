"""Integration tests for the query path — real providers, no fakes.

The unit suite pins ranking behaviour with `FakeEmbedding`, whose vectors are
sha256 bytes. That proves the plumbing (ingest → Chroma → retrieve → explain)
but says nothing about whether the shipped catalog is actually *retrievable*:
a method whose `use_case` is badly written would still rank fine under a hash.
These tests use the real embedding model against the real `methods/` directory,
so they fail if a method's text stops matching the problems it should match.

Deselected from the default suite via `-m "not integration"` in pyproject's
addopts. Run them explicitly:

    pytest -m integration

Requires the `local` extra (`pip install -e ".[dev,local]"`). The first run
downloads ~80MB of model weights into the HuggingFace cache; after that it is
offline. The LLM test needs a reachable backend on top of that and is opted
into separately with METHODOS_INTEGRATION_LLM=1.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from methodos.config import Settings
from methodos.providers import make_llm
from methodos.search import search

pytestmark = pytest.mark.integration

REPO_ROOT = Path(__file__).parent.parent
REPO_METHODS = REPO_ROOT / "methods"


@pytest.fixture(scope="module")
def real_embedding():
    """The default local model. Skips if the `local` extra isn't installed."""
    pytest.importorskip(
        "sentence_transformers",
        reason="needs the `local` extra: pip install -e '.[dev,local]'",
    )
    from methodos.providers.embedding_local import LocalEmbedding

    return LocalEmbedding(model_name="all-MiniLM-L6-v2")


@pytest.fixture(scope="module")
def real_index(tmp_path_factory, real_embedding) -> Path:
    """Ingest the real catalog once — model load plus ingest is slow."""
    from methodos.ingest import ingest

    chroma_path = tmp_path_factory.mktemp("chroma_integration")
    summary = ingest(
        methods_dir=REPO_METHODS,
        chroma_path=chroma_path,
        embedding=real_embedding,
    )
    assert summary.count >= 3, "expected the shipped catalog to ingest"
    assert summary.dimensions == 384, f"all-MiniLM-L6-v2 is 384d, got {summary.dimensions}"
    return chroma_path


# Only problems whose intended method wins by a wide margin are pinned here.
# "internal strengths and weaknesses vs external opportunities and threats"
# looks like the obvious SWOT probe, but it scores 0.468 against Porter's
# 0.427 — too close to assert on without inviting a flaky test.
@pytest.mark.parametrize(
    ("problem", "expected_top"),
    [
        (
            "should we enter this industry? how defensible is the position "
            "against competitors and new entrants",
            "Porters_Five_Forces",
        ),
        (
            "nobody knows who actually owns this decision and it has been stuck for weeks",
            "DACI_Matrix",
        ),
        (
            "who is the approver for this cross-functional decision",
            "DACI_Matrix",
        ),
    ],
)
def test_query_path_ranks_the_right_method_first(real_index, real_embedding, problem, expected_top):
    result = search(
        query=problem,
        embedding=real_embedding,
        llm=None,
        chroma_path=real_index,
        top_k=3,
    )

    assert result.explanation is None, "llm=None must skip the explanation call"
    assert len(result.candidates) == 3
    top, runner_up = result.candidates[0], result.candidates[1]
    assert top.id == expected_top, (
        f"expected {expected_top} first for {problem!r}, got "
        f"{[(c.id, round(c.similarity, 3)) for c in result.candidates]}"
    )
    # A real model should be decisive here, not win by rounding noise. Observed
    # margins for these probes are >0.35; 0.10 leaves room for model updates
    # while still failing if a `use_case` rewrite blurs the distinction.
    assert top.similarity - runner_up.similarity > 0.10, (
        f"{expected_top} won by only {top.similarity - runner_up.similarity:.3f}"
    )


def test_query_path_produces_descending_similarities(real_index, real_embedding):
    result = search(
        query="we need to enter a new market without burning cash",
        embedding=real_embedding,
        llm=None,
        chroma_path=real_index,
        top_k=3,
    )
    sims = [c.similarity for c in result.candidates]
    assert sims == sorted(sims, reverse=True)
    # Cosine over normalized vectors; anything outside this means the metric
    # or the `1 - distance` conversion in search.py drifted.
    assert all(-1.0 <= s <= 1.0 for s in sims)


def test_query_path_hydrates_candidates_from_the_catalog(real_index, real_embedding):
    """Metadata survives the round-trip through Chroma, not just the ids."""
    result = search(
        query="who is the approver for this cross-functional decision",
        embedding=real_embedding,
        llm=None,
        chroma_path=real_index,
        top_k=1,
    )
    top = result.candidates[0]
    assert top.id == "DACI_Matrix"
    assert top.name == "DACI Decision-Making Framework"
    assert top.category == "decision-making"
    assert 1 <= top.complexity_score <= 5
    assert top.strengths and top.weaknesses
    assert top.duration_min <= top.duration_max
    assert (REPO_ROOT / top.doc_path).is_file(), f"{top.doc_path} should exist on disk"


@pytest.mark.skipif(
    os.environ.get("METHODOS_INTEGRATION_LLM") != "1",
    reason="needs a reachable LLM backend; set METHODOS_INTEGRATION_LLM=1 to run",
)
def test_query_path_with_real_llm_returns_an_explanation(real_index, real_embedding):
    """Exercises the one path fakes can't: a real completion through litellm.

    Assertions stay loose on purpose — the wording is non-deterministic. What
    matters is that the prompt renders, the call succeeds, and the model wrote
    about the methods it was actually given.
    """
    settings = Settings()
    result = search(
        query="should we enter this industry? how defensible is the position",
        embedding=real_embedding,
        llm=make_llm(settings),
        chroma_path=real_index,
        top_k=2,
    )

    assert result.explanation is not None
    assert result.explanation.strip(), "explanation must not be blank"
    names = [c.name for c in result.candidates]
    assert any(name.split()[0] in result.explanation for name in names), (
        f"explanation mentions none of {names}: {result.explanation[:200]!r}"
    )
