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
