"""Several use cases per method: one vector each, one candidate per method.

FakeEmbedding hashes text, so a query identical to a use case matches it at
similarity 1.0 and nothing else closely — which makes "which text matched" a
deterministic question.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from methodos.ingest import IngestError, ingest
from methodos.search import collection_size, retrieve

SCHOOL = "A school leadership team deciding which projects to drop before term starts."


def _write(dir: Path, id: str, use_case: str, **extra: object) -> None:
    payload = {
        "id": id,
        "name": id,
        "category": "strategy",
        "use_case": use_case,
        "strengths": ["s"],
        "weaknesses": ["w"],
        "complexity_score": 2,
        "estimated_duration": {"min_minutes": 30, "max_minutes": 60},
        **extra,
    }
    (dir / f"{id}.json").write_text(json.dumps(payload), encoding="utf-8")
    (dir / f"{id}.md").write_text(f"# {id}\n", encoding="utf-8")


@pytest.fixture
def seeded(tmp_path, fake_embedding):
    methods = tmp_path / "methods"
    methods.mkdir()
    _write(
        methods,
        "Alpha",
        "alpha alpha alpha alpha alpha alpha alpha alpha alpha",
        use_cases=[
            SCHOOL,
            "An executive board cutting the project portfolio to fit next year's budget.",
        ],
    )
    _write(methods, "Beta", "beta beta beta beta beta beta beta beta beta beta beta")
    _write(methods, "Gamma", "gamma gamma gamma gamma gamma gamma gamma gamma gamma")
    chroma = tmp_path / "chroma"
    summary = ingest(methods_dir=methods, chroma_path=chroma, embedding=fake_embedding)
    return summary, chroma


def test_every_use_case_becomes_a_vector(seeded):
    summary, _ = seeded
    assert summary.count == 3
    assert summary.documents == 5
    assert summary.ids == ["Alpha", "Beta", "Gamma"]


def test_catalog_size_counts_methods_not_vectors(seeded, fake_embedding):
    _, chroma = seeded
    assert collection_size(chroma, fake_embedding) == 3
    assert collection_size(chroma, fake_embedding, where={"category": "strategy"}) == 3


def test_a_method_appears_once_even_when_several_use_cases_match(seeded, fake_embedding):
    _, chroma = seeded
    out = retrieve(query=SCHOOL, embedding=fake_embedding, chroma_path=chroma, top_k=3)
    assert [c.id for c in out].count("Alpha") == 1
    assert len(out) == 3, "collapsing duplicates must not shrink the shortlist"


def test_matching_a_further_use_case_reports_it(seeded, fake_embedding):
    _, chroma = seeded
    top = retrieve(query=SCHOOL, embedding=fake_embedding, chroma_path=chroma, top_k=1)[0]
    assert top.id == "Alpha"
    assert top.similarity == pytest.approx(1.0)
    assert top.matched_use_case == SCHOOL
    assert top.use_case.startswith("alpha"), "use_case stays the canonical text"


def test_matching_the_canonical_use_case_reports_no_further_match(seeded, fake_embedding):
    _, chroma = seeded
    q = "beta beta beta beta beta beta beta beta beta beta beta"
    top = retrieve(query=q, embedding=fake_embedding, chroma_path=chroma, top_k=1)[0]
    assert top.id == "Beta"
    assert top.matched_use_case is None


def test_reranker_scores_the_text_that_matched(seeded, fake_embedding, fake_reranker):
    _, chroma = seeded
    retrieve(
        query=SCHOOL, embedding=fake_embedding, chroma_path=chroma, top_k=1, reranker=fake_reranker
    )
    _, documents = fake_reranker.calls[0]
    assert SCHOOL in documents


def test_ingest_rejects_a_missing_asset_file(tmp_path, fake_embedding):
    methods = tmp_path / "methods"
    methods.mkdir()
    _write(
        methods,
        "Alpha",
        "alpha alpha alpha alpha alpha alpha alpha alpha alpha",
        assets=[{"title": "Canvas", "kind": "template", "path": "canvas.pdf"}],
    )
    with pytest.raises(IngestError, match=r"canvas\.pdf"):
        ingest(methods_dir=methods, chroma_path=tmp_path / "c", embedding=fake_embedding)

    (methods / "assets" / "Alpha").mkdir(parents=True)
    (methods / "assets" / "Alpha" / "canvas.pdf").write_bytes(b"%PDF-1.4")
    assert (
        ingest(methods_dir=methods, chroma_path=tmp_path / "c", embedding=fake_embedding).count == 1
    )


class _TableReranker:
    """Scores from a fixed table, so the test states exactly what the cross-encoder thinks."""

    name = "table-reranker"

    def __init__(self, table: dict[str, float]) -> None:
        self.table = table
        self.calls: list[list[str]] = []

    def score(self, query: str, documents) -> list[float]:
        self.calls.append(list(documents))
        return [self.table.get(d, 0.0) for d in documents]


ALPHA = "alpha alpha alpha alpha alpha alpha alpha alpha alpha"
ALPHA_EXTRA = "An executive board cutting the project portfolio to fit next year's budget."
BETA = "beta beta beta beta beta beta beta beta beta beta beta"


def test_a_method_is_reranked_on_its_best_text_not_its_nearest(seeded, fake_embedding):
    """The query is Alpha's canonical text, so the embedding picks that text.

    The cross-encoder rates it low and Alpha's further use case high. Scoring
    only the nearest text would rank Beta first; scoring every text must not.
    """
    _, chroma = seeded
    reranker = _TableReranker({ALPHA: 1.0, ALPHA_EXTRA: 9.0, BETA: 5.0})
    out = retrieve(
        query=ALPHA, embedding=fake_embedding, chroma_path=chroma, top_k=3, reranker=reranker
    )
    assert [c.id for c in out][:2] == ["Alpha", "Beta"]
    assert out[0].rerank_score == 9.0
    assert out[0].matched_use_case == ALPHA_EXTRA, "report the text that won"
    assert out[0].similarity == pytest.approx(1.0), "similarity stays the embedding's"
    scored = reranker.calls[0]
    assert {ALPHA, ALPHA_EXTRA, SCHOOL, BETA} <= set(scored), "every text of a method is scored"


def test_the_canonical_text_winning_reports_no_further_match(seeded, fake_embedding):
    _, chroma = seeded
    reranker = _TableReranker({ALPHA: 9.0, ALPHA_EXTRA: 1.0, SCHOOL: 1.0})
    top = retrieve(
        query=SCHOOL, embedding=fake_embedding, chroma_path=chroma, top_k=1, reranker=reranker
    )[0]
    assert top.id == "Alpha"
    assert top.matched_use_case is None, (
        "the embedding matched SCHOOL, the reranker preferred use_case"
    )
