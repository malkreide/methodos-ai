import json
from pathlib import Path

import pytest

from methodos.ingest import ingest
from methodos.search import SearchResult, StaleIndexError, retrieve, search


def _write(dir: Path, id: str, use_case: str) -> None:
    payload = {
        "id": id,
        "name": id,
        "category": "strategy",
        "use_case": use_case,
        "strengths": ["s"],
        "weaknesses": ["w"],
        "complexity_score": 2,
        "estimated_duration": {"min_minutes": 30, "max_minutes": 60},
    }
    (dir / f"{id}.json").write_text(json.dumps(payload), encoding="utf-8")
    (dir / f"{id}.md").write_text(f"# {id}\n", encoding="utf-8")


def _seed(tmp_path: Path, embedding) -> Path:
    methods = tmp_path / "methods"
    methods.mkdir()
    _write(methods, "Alpha", "alpha alpha alpha alpha alpha alpha alpha alpha alpha")
    _write(methods, "Beta", "beta beta beta beta beta beta beta beta beta beta beta")
    _write(methods, "Gamma", "gamma gamma gamma gamma gamma gamma gamma gamma gamma")
    chroma_path = tmp_path / "chroma"
    ingest(methods_dir=methods, chroma_path=chroma_path, embedding=embedding)
    return chroma_path


def test_retrieve_returns_top_k_sorted_by_similarity(tmp_path, fake_embedding):
    chroma_path = _seed(tmp_path, fake_embedding)
    results = retrieve(
        query="alpha alpha alpha alpha alpha alpha alpha alpha",
        embedding=fake_embedding,
        chroma_path=chroma_path,
        top_k=3,
    )
    assert len(results) == 3
    sims = [r.similarity for r in results]
    assert sims == sorted(sims, reverse=True)


def test_retrieve_raises_on_provider_mismatch(tmp_path, fake_embedding):
    chroma_path = _seed(tmp_path, fake_embedding)
    from tests.conftest import FakeEmbedding

    different = FakeEmbedding(dimensions=8)
    different.name = "different-provider"
    with pytest.raises(StaleIndexError):
        retrieve(query="x", embedding=different, chroma_path=chroma_path, top_k=2)


def test_search_calls_llm_with_rendered_prompt(tmp_path, fake_embedding, fake_llm):
    chroma_path = _seed(tmp_path, fake_embedding)
    out = search(
        query="alpha alpha alpha alpha alpha alpha alpha",
        embedding=fake_embedding,
        llm=fake_llm,
        chroma_path=chroma_path,
        top_k=2,
    )
    assert isinstance(out, SearchResult)
    assert len(out.candidates) == 2
    assert out.explanation == "stub explanation"
    assert len(fake_llm.calls) == 1
    system, user = fake_llm.calls[0]
    assert "expert management consultant" in system.lower()
    assert "alpha" in user


def test_search_with_no_llm_skips_explanation(tmp_path, fake_embedding, fake_llm):
    chroma_path = _seed(tmp_path, fake_embedding)
    out = search(
        query="alpha alpha alpha",
        embedding=fake_embedding,
        llm=None,
        chroma_path=chroma_path,
        top_k=2,
    )
    assert out.explanation is None
    assert fake_llm.calls == []


# --- rerank ----------------------------------------------------------------


def _seed_lexical(tmp_path: Path, embedding) -> Path:
    """Seed docs whose lexical overlap with the probe differs from hash order."""
    methods = tmp_path / "methods"
    methods.mkdir()
    _write(methods, "Match", "stalled decision ownership approval authority stalled decision")
    _write(methods, "Partial", "decision making generally speaking about various topics here")
    _write(methods, "Unrelated", "gardening tomatoes greenhouse watering compost soil mulch")
    chroma_path = tmp_path / "chroma"
    ingest(methods_dir=methods, chroma_path=chroma_path, embedding=embedding)
    return chroma_path


def test_retrieve_without_reranker_is_unchanged(tmp_path, fake_embedding, fake_reranker):
    chroma_path = _seed_lexical(tmp_path, fake_embedding)
    base = retrieve(
        query="stalled decision", embedding=fake_embedding, chroma_path=chroma_path, top_k=3
    )
    same = retrieve(
        query="stalled decision",
        embedding=fake_embedding,
        chroma_path=chroma_path,
        top_k=3,
        reranker=None,
    )
    assert [c.id for c in base] == [c.id for c in same]
    assert all(c.rerank_score is None for c in base)
    assert fake_reranker.calls == []


def test_retrieve_with_reranker_reorders_by_score(tmp_path, fake_embedding, fake_reranker):
    chroma_path = _seed_lexical(tmp_path, fake_embedding)
    out = retrieve(
        query="stalled decision",
        embedding=fake_embedding,
        chroma_path=chroma_path,
        top_k=3,
        reranker=fake_reranker,
    )
    # FakeReranker scores lexical overlap, so "Match" must come first regardless
    # of where the sha256 embedding happened to put it.
    assert out[0].id == "Match"
    assert [c.rerank_score for c in out] == sorted((c.rerank_score for c in out), reverse=True)
    assert out[-1].id == "Unrelated"


def test_retrieve_reranks_the_overfetched_pool_not_just_top_k(
    tmp_path, fake_embedding, fake_reranker
):
    """The point of over-fetching: a method outside the top-k can be promoted."""
    chroma_path = _seed_lexical(tmp_path, fake_embedding)
    out = retrieve(
        query="stalled decision",
        embedding=fake_embedding,
        chroma_path=chroma_path,
        top_k=1,
        reranker=fake_reranker,
    )
    assert len(out) == 1
    assert out[0].id == "Match"
    # top_k=1 with the default factor of 2 means the reranker saw 2 candidates.
    assert len(fake_reranker.calls) == 1
    assert len(fake_reranker.calls[0][1]) == 2


def test_retrieve_keeps_similarity_alongside_rerank_score(tmp_path, fake_embedding, fake_reranker):
    """Rerank score is a separate field; the retrieval similarity is not overwritten."""
    chroma_path = _seed_lexical(tmp_path, fake_embedding)
    out = retrieve(
        query="stalled decision",
        embedding=fake_embedding,
        chroma_path=chroma_path,
        top_k=3,
        reranker=fake_reranker,
    )
    for c in out:
        assert -1.0 <= c.similarity <= 1.0
        assert c.rerank_score is not None


def test_retrieve_passes_use_case_text_to_the_reranker(tmp_path, fake_embedding, fake_reranker):
    chroma_path = _seed_lexical(tmp_path, fake_embedding)
    retrieve(
        query="stalled decision",
        embedding=fake_embedding,
        chroma_path=chroma_path,
        top_k=3,
        reranker=fake_reranker,
    )
    query, docs = fake_reranker.calls[0]
    assert query == "stalled decision"
    assert any("gardening" in d for d in docs), "reranker should see the use_case text"


def test_search_threads_the_reranker_through(tmp_path, fake_embedding, fake_reranker):
    chroma_path = _seed_lexical(tmp_path, fake_embedding)
    out = search(
        query="stalled decision",
        embedding=fake_embedding,
        llm=None,
        chroma_path=chroma_path,
        top_k=2,
        reranker=fake_reranker,
    )
    assert out.candidates[0].id == "Match"
    assert len(fake_reranker.calls) == 1


def test_retrieve_survives_a_reranker_returning_wrong_count(tmp_path, fake_embedding):
    """A misbehaving provider must not silently corrupt the ordering."""
    from methodos.providers.base import RerankError

    class BadReranker:
        name = "bad"

        def score(self, query, documents):
            return [1.0]  # too few

    chroma_path = _seed_lexical(tmp_path, fake_embedding)
    with pytest.raises(RerankError, match="returned 1 score"):
        retrieve(
            query="stalled decision",
            embedding=fake_embedding,
            chroma_path=chroma_path,
            top_k=3,
            reranker=BadReranker(),
        )
