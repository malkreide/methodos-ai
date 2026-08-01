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


# One probe per method, phrased as a user would state the problem — never by
# naming the method or echoing its vocabulary, which would test the query
# rather than the catalog.
#
# Third element is the minimum margin over the runner-up. 0.10 is the default;
# a lower value is an explicit statement that two methods in the catalog are
# genuinely adjacent, not a licence to weaken a failing probe. Every value here
# was measured against the full catalog.
#
# Rejected candidates, kept so they don't get re-added:
#   "internal strengths and weaknesses vs external opportunities and threats"
#       -> SWOT by 0.041 over Porter's. The four-quadrant vocabulary is shared.
#   "the same defect keeps coming back after every fix"
#       -> Five_Whys by 0.110 over Ishikawa. Both are root-cause methods; the
#          probe has to name the symptom-vs-cause framing to separate them.
#   "which external forces beyond our competitors should we monitor"
#       -> PESTEL by 0.057 over Porter's. Naming the actual forces separates them.
#   "we keep spending engineering effort on infrastructure that is now a
#    standard utility" -> Wardley only reached #2. Its problem-shaped phrasings
#    lose to Porter's and PESTEL on shared market vocabulary; the build-buy-
#    outsource question is what separates it.
#   "this decision bounces between teams, nobody has authority to approve it"
#       -> was a second DACI probe, fell to 0.022 over Cynefin once Cynefin's
#          use_case was made problem-shaped ("teams that cannot agree how to
#          tackle a problem"). Dropped rather than reworded: phrasings that did
#          clear the bar all leaned on DACI's own role names. One probe per
#          method is the design; DACI's approver probe already covers it.
PROBES = [
    (
        "should we enter this industry? how defensible is the position "
        "against competitors and new entrants",
        "Porters_Five_Forces",
        0.10,
    ),
    (
        "strategic planning kickoff: assess our own position and the "
        "external landscape in four quadrants",
        "SWOT",
        0.10,
    ),
    (
        "scan the wider environment: legislation, demographics, climate "
        "exposure and macroeconomic conditions",
        "PESTEL_Analysis",
        0.10,
    ),
    (
        "map out how this new venture creates and captures value on one page",
        "Business_Model_Canvas",
        0.10,
    ),
    (
        "should we build this component ourselves, buy it off the shelf, or outsource it",
        "Wardley_Mapping",
        0.10,
    ),
    (
        "we cannot forecast a single number for this decade, which choices "
        "hold up across several plausible futures",
        "Scenario_Planning",
        0.10,
    ),
    (
        "who is the approver for this cross-functional decision",
        "DACI_Matrix",
        0.10,
    ),
    (
        "one group wants a detailed plan up front and another wants to start "
        "experimenting, we disagree on what kind of problem this is",
        "Cynefin_Framework",
        0.10,
    ),
    (
        "express the costs and the benefits in money, discount them, and "
        "compare the net present value of each option",
        "Cost_Benefit_Analysis",
        0.10,
    ),
    (
        "the discussion has split into advocates and critics and the same "
        "person is always the sceptic",
        "Six_Thinking_Hats",
        0.10,
    ),
    (
        "we keep fixing the symptom of this recurring failure instead of what actually causes it",
        "Five_Whys",
        0.10,
    ),
    (
        "many possible causes across people process equipment and materials, we need to map them",
        "Ishikawa_Diagram",
        0.10,
    ),
    (
        "before we commit to this launch, imagine it failed and surface "
        "the risks nobody is voicing",
        "Pre_Mortem",
        0.10,
    ),
    (
        "tickets take six weeks end to end but the actual work is only a few hours",
        "Value_Stream_Mapping",
        0.10,
    ),
    (
        "interview customers about what they were struggling with when they "
        "switched and what they stopped using",
        "Jobs_To_Be_Done",
        0.10,
    ),
    (
        "what is resisting this change, and how do we weaken the restraints "
        "instead of pushing harder",
        "Force_Field_Analysis",
        0.10,
    ),
    # Prioritization is the most crowded corner of the catalog: RICE, MoSCoW,
    # Eisenhower and Value Stream Mapping all speak about too much work and not
    # enough capacity. RICE's distinguishing feature is quantified scoring, and
    # a probe only surfaces that by naming reach/impact/effort — which would be
    # testing the query. So this probe keeps the user's phrasing and accepts a
    # narrower margin instead.
    (
        "we have more backlog items than capacity and need a defensible ranked order",
        "RICE_Scoring",
        0.05,
    ),
    (
        "fixed release date, we must agree now which requirements get dropped",
        "MoSCoW_Method",
        0.10,
    ),
    (
        "which features are table stakes that earn no credit and which would "
        "actually delight customers",
        "Kano_Model",
        0.10,
    ),
    (
        "my week is eaten by interruptions and the important work never gets started",
        "Eisenhower_Matrix",
        0.10,
    ),
    (
        "end of sprint team retrospective, what should we start and stop doing",
        "Start_Stop_Continue",
        0.10,
    ),
    # Two retrospective formats sit close together by construction; this probe
    # leans on the "one picture" framing to separate them and still only clears
    # the bar by a little. Expect it to need re-measuring if more retrospective
    # formats are added.
    (
        "the team has gone quiet in our usual list-based retrospectives, we "
        "need goal drag and upcoming risks in one picture",
        "Sailboat_Retrospective",
        0.10,
    ),
    (
        "debrief the launch we just finished: what did we expect versus what happened",
        "After_Action_Review",
        0.10,
    ),
]


@pytest.mark.parametrize(("problem", "expected_top", "min_margin"), PROBES)
def test_query_path_ranks_the_right_method_first(
    real_index, real_embedding, problem, expected_top, min_margin
):
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
    # A real model should be decisive here, not win by rounding noise. The bar
    # leaves room for model updates and for the catalog growing denser, while
    # still failing if a `use_case` rewrite blurs two methods together.
    margin = top.similarity - runner_up.similarity
    assert margin > min_margin, (
        f"{expected_top} won by only {margin:.3f} over {runner_up.id} (bar {min_margin})"
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


def test_every_method_in_the_catalog_has_a_probe():
    """A new method must arrive with a probe, or it goes untested.

    Needs no model, so it fails fast even without the `local` extra: a method
    added without a probe could otherwise sit in the catalog unretrievable and
    nothing here would notice.
    """
    catalog = {p.stem for p in REPO_METHODS.glob("*.json")}
    probed = {expected for _, expected, _ in PROBES}
    assert catalog == probed, (
        f"methods with no probe: {sorted(catalog - probed)}; "
        f"probes naming an unknown method: {sorted(probed - catalog)}"
    )


# --- cross-encoder rerank --------------------------------------------------


@pytest.fixture(scope="module")
def real_reranker():
    """The default cross-encoder. Skips if the `local` extra isn't installed."""
    pytest.importorskip(
        "sentence_transformers",
        reason="needs the `local` extra: pip install -e '.[dev,local]'",
    )
    from methodos.providers.rerank_cross_encoder import CrossEncoderRerank

    return CrossEncoderRerank()


@pytest.mark.parametrize(("problem", "expected_top", "min_margin"), PROBES)
def test_rerank_keeps_every_pinned_probe_correct(
    real_index, real_embedding, real_reranker, problem, expected_top, min_margin
):
    """Reranking must not break what embedding-only retrieval already gets right.

    `min_margin` is unused here on purpose: cross-encoder outputs are logits on
    a different scale from cosine similarity, so the 0.10 bar does not transfer.
    What matters is that the ordering survives.
    """
    from methodos.search import retrieve

    out = retrieve(
        query=problem,
        embedding=real_embedding,
        chroma_path=real_index,
        top_k=3,
        reranker=real_reranker,
        overfetch_factor=4,
    )
    assert out[0].id == expected_top, (
        f"rerank moved {expected_top} off the top for {problem!r}: "
        f"{[(c.id, round(c.rerank_score or 0, 2)) for c in out]}"
    )
    assert all(c.rerank_score is not None for c in out)
    scores = [c.rerank_score for c in out]
    assert scores == sorted(scores, reverse=True)


# Probes that embedding-only retrieval cannot separate — each was rejected
# during PR #12/#13 for landing under the 0.10 bar or missing outright, which
# forced the pinned probe to be reworded. Measured against the 23-method
# catalog with overfetch_factor=4:
#
#   SWOT probe    : embedding 0.004 behind Porter's (miss) -> rerank +15.3 ahead
#   Wardley probe : embedding 0.009 behind (miss)          -> rerank  +9.3 ahead
#
# These assert only the reranked outcome. Asserting the embedding-only failure
# too would turn a future embedding improvement into a spurious test failure.
@pytest.mark.parametrize(
    ("problem", "expected_top"),
    [
        (
            "internal strengths and weaknesses vs external opportunities and threats",
            "SWOT",
        ),
        (
            "we keep spending engineering effort on infrastructure that is now a standard utility",
            "Wardley_Mapping",
        ),
    ],
)
def test_rerank_rescues_probes_the_embedding_cannot_separate(
    real_index, real_embedding, real_reranker, problem, expected_top
):
    from methodos.search import retrieve

    out = retrieve(
        query=problem,
        embedding=real_embedding,
        chroma_path=real_index,
        top_k=3,
        reranker=real_reranker,
        overfetch_factor=4,
    )
    assert out[0].id == expected_top, (
        f"expected {expected_top} first for {problem!r}, got "
        f"{[(c.id, round(c.rerank_score or 0, 2)) for c in out]}"
    )


def test_rerank_leaves_the_retrieval_similarity_intact(real_index, real_embedding, real_reranker):
    """Both scores survive to the renderer; neither overwrites the other."""
    from methodos.search import retrieve

    out = retrieve(
        query="who is the approver for this cross-functional decision",
        embedding=real_embedding,
        chroma_path=real_index,
        top_k=3,
        reranker=real_reranker,
        overfetch_factor=4,
    )
    for c in out:
        assert -1.0 <= c.similarity <= 1.0, "cosine similarity must stay in range"
        assert c.rerank_score is not None
