import json
from pathlib import Path

import pytest

from methodos.ingest import IngestError, ingest


def _write_method(dir: Path, id: str, *, use_case_suffix: str = "") -> None:
    payload = {
        "id": id,
        "name": id.replace("_", " "),
        "category": "strategy",
        "use_case": ("a useful method for problems involving " + id + " " + use_case_suffix).ljust(
            60, "."
        ),
        "strengths": ["s"],
        "weaknesses": ["w"],
        "complexity_score": 2,
        "estimated_duration": {"min_minutes": 30, "max_minutes": 60},
    }
    (dir / f"{id}.json").write_text(json.dumps(payload), encoding="utf-8")
    (dir / f"{id}.md").write_text(f"# {id}\n", encoding="utf-8")


def test_ingest_creates_collection_and_upserts(tmp_path, fake_embedding):
    methods = tmp_path / "methods"
    methods.mkdir()
    _write_method(methods, "Alpha")
    _write_method(methods, "Beta")

    chroma_path = tmp_path / "chroma"
    summary = ingest(
        methods_dir=methods,
        chroma_path=chroma_path,
        embedding=fake_embedding,
    )
    assert summary.count == 2
    assert "Alpha" in summary.ids and "Beta" in summary.ids

    summary2 = ingest(
        methods_dir=methods,
        chroma_path=chroma_path,
        embedding=fake_embedding,
    )
    assert summary2.count == 2


def test_ingest_aborts_on_validation_errors(tmp_path, fake_embedding):
    methods = tmp_path / "methods"
    methods.mkdir()
    (methods / "Bad.json").write_text(json.dumps({"id": "Bad"}), encoding="utf-8")
    (methods / "Bad.md").write_text("# bad", encoding="utf-8")
    with pytest.raises(IngestError) as ei:
        ingest(methods_dir=methods, chroma_path=tmp_path / "chroma", embedding=fake_embedding)
    assert "Bad.json" in str(ei.value)


def test_ingest_aborts_on_filename_id_mismatch(tmp_path, fake_embedding):
    methods = tmp_path / "methods"
    methods.mkdir()
    payload = {
        "id": "Real",
        "name": "Real",
        "category": "strategy",
        "use_case": "x" * 60,
        "strengths": ["s"],
        "weaknesses": ["w"],
        "complexity_score": 1,
        "estimated_duration": {"min_minutes": 5, "max_minutes": 10},
    }
    (methods / "Wrong.json").write_text(json.dumps(payload), encoding="utf-8")
    (methods / "Wrong.md").write_text("# wrong", encoding="utf-8")
    with pytest.raises(IngestError) as ei:
        ingest(methods_dir=methods, chroma_path=tmp_path / "chroma", embedding=fake_embedding)
    assert "mismatch" in str(ei.value).lower() or "must equal" in str(ei.value).lower()


def test_ingest_aborts_on_empty_methods_dir(tmp_path, fake_embedding):
    methods = tmp_path / "methods"
    methods.mkdir()
    summary = ingest(
        methods_dir=methods,
        chroma_path=tmp_path / "chroma",
        embedding=fake_embedding,
    )
    assert summary.count == 0


def test_ingest_persists_provider_metadata(tmp_path, fake_embedding):
    methods = tmp_path / "methods"
    methods.mkdir()
    _write_method(methods, "Gamma")

    chroma_path = tmp_path / "chroma"
    ingest(methods_dir=methods, chroma_path=chroma_path, embedding=fake_embedding)

    import chromadb

    client = chromadb.PersistentClient(path=str(chroma_path))
    coll = client.get_collection("methods")
    assert coll.metadata["embedding_provider_name"] == fake_embedding.name
    assert coll.metadata["embedding_dimensions"] == fake_embedding.dimensions
