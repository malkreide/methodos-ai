"""Contract tests for the HTTP API.

Skipped without the `api` extra. CI installs it, so these do run there.

Everything here goes through deterministic fakes and a tmp Chroma built by the
real `ingest`, so no test needs a network, a key, or a model download. The
provider trio is injected by overriding the `get_providers` dependency — the
same seam the container uses, just handed different objects.

What is worth asserting here is only what this layer adds: that the MCP
contract's fields survive into the HTTP payload, that a failing LLM does not
take the ranking down with it, and that the feedback round-trip works. Ranking
itself is `test_search.py`'s and `test_mcp_tools.py`'s job.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("fastapi", reason="needs the `api` extra: pip install -e '.[dev,api]'")

from fastapi.testclient import TestClient

from methodos import api as api_mod
from methodos.api import Providers, app, get_providers, methods_dir
from methodos.config import Settings
from methodos.ingest import ingest
from methodos.providers.base import LLMError
from tests.conftest import FakeEmbedding, FakeLLM, FakeReranker


def _write(dir: Path, id: str, use_case: str, category: str = "strategy") -> None:
    payload = {
        "id": id,
        "name": id,
        "category": category,
        "use_case": use_case,
        "strengths": ["s1", "s2"],
        "weaknesses": ["w1"],
        "complexity_score": 2,
        "estimated_duration": {"min_minutes": 30, "max_minutes": 60},
    }
    (dir / f"{id}.json").write_text(json.dumps(payload), encoding="utf-8")
    (dir / f"{id}.md").write_text(f"# {id}\n\nFull documentation for {id}.\n", encoding="utf-8")


class _FakeProviders(Providers):
    """Providers without calling the real factories."""

    def __init__(self, settings: Settings, llm: FakeLLM) -> None:
        self.settings = settings
        self.embedding = FakeEmbedding(dimensions=8)
        self.reranker = FakeReranker()
        self.llm = llm


@pytest.fixture
def env(tmp_path, monkeypatch):
    """A working deployment in a tmp dir: catalog on disk, index built, fakes wired."""
    methods = tmp_path / "methods"
    methods.mkdir()
    _write(methods, "Alpha", "alpha alpha alpha alpha alpha alpha alpha alpha alpha")
    _write(methods, "Beta", "beta beta beta beta beta beta beta beta beta beta beta")
    _write(methods, "Gamma", "gamma gamma gamma gamma gamma gamma gamma", "analysis")

    embedding = FakeEmbedding(dimensions=8)
    chroma_path = tmp_path / "chroma"
    ingest(methods_dir=methods, chroma_path=chroma_path, embedding=embedding)

    monkeypatch.setenv("METHODOS_METHODS_DIR", str(methods))
    settings = Settings(
        chroma_path=chroma_path,
        feedback_path=tmp_path / "feedback.jsonl",
    )
    llm = FakeLLM("Alpha fits because it fits.")
    providers = _FakeProviders(settings, llm)
    app.dependency_overrides[get_providers] = lambda: providers
    yield {
        "client": TestClient(app),
        "settings": settings,
        "llm": llm,
        "methods": methods,
        "providers": providers,
    }
    app.dependency_overrides.clear()


def test_health_reports_the_index_and_the_active_providers(env):
    body = env["client"].get("/health").json()
    assert body["status"] == "ok"
    assert body["indexed_methods"] == 3
    assert body["index_error"] is None
    assert body["embedding"] == "fake-embedding-8d"
    assert body["reranker"] == "fake-reranker"


def test_health_is_degraded_rather_than_500_when_the_index_is_missing(tmp_path, env):
    """A container with no index must still answer /health — that is how you learn why."""
    env["providers"].settings = Settings(chroma_path=tmp_path / "nope")
    body = env["client"].get("/health").json()
    assert body["status"] == "degraded"
    assert body["indexed_methods"] is None
    assert "ingest" in body["index_error"]


def test_query_returns_the_mcp_narrowing_fields_alongside_the_explanation(env):
    body = env["client"].post("/query", json={"problem": "alpha alpha alpha"}).json()
    assert body["returned"] == 3
    assert body["total_in_scope"] == 3
    assert body["total_indexed"] == 3
    assert body["ranking_basis"] == "cross-encoder"
    assert body["explanation"] == "Alpha fits because it fits."
    assert body["explanation_error"] is None
    assert body["query_id"]


def test_query_with_explain_false_never_touches_the_llm(env):
    body = (
        env["client"].post("/query", json={"problem": "alpha alpha alpha", "explain": False}).json()
    )
    assert body["explanation"] is None
    assert body["explanation_model"] is None
    assert env["llm"].calls == []
    assert body["matches"], "retrieval must still work with the LLM out of the picture"


def test_rerank_false_falls_back_to_embedding_order(env):
    body = (
        env["client"].post("/query", json={"problem": "alpha alpha alpha", "rerank": False}).json()
    )
    assert body["ranking_basis"] == "embedding-similarity"
    assert all(m["rerank_score"] is None for m in body["matches"])


def test_rerank_true_fails_loudly_when_the_reranker_is_unavailable(env):
    """Mirrors the CLI's `--rerank`: silently ignoring a direct request is worse."""
    env["providers"].reranker = None
    res = env["client"].post("/query", json={"problem": "alpha", "rerank": True})
    assert res.status_code == 503
    assert "local" in res.json()["detail"]


def test_a_failing_llm_leaves_the_ranking_intact(env):
    """The whole reason explanation errors are a field and not a 502."""

    def boom(*a, **kw):
        raise LLMError("AuthenticationError: invalid x-api-key")

    env["llm"].complete = boom
    res = env["client"].post("/query", json={"problem": "alpha alpha alpha"})
    assert res.status_code == 200
    body = res.json()
    assert body["returned"] == 3
    assert body["explanation"] is None
    assert "invalid x-api-key" in body["explanation_error"]


def test_llm_check_reports_the_provider_error_as_502(env):
    def boom(*a, **kw):
        raise LLMError("NotFoundError: model not found")

    env["llm"].complete = boom
    res = env["client"].post("/llm/check")
    assert res.status_code == 502
    assert "model not found" in res.json()["detail"]


def test_llm_check_confirms_a_working_model(env):
    body = env["client"].post("/llm/check").json()
    assert body["ok"] is True
    assert body["reply"] == "Alpha fits because it fits."
    assert body["latency_ms"] >= 0


def test_category_filter_applies_inside_the_search(env):
    body = env["client"].post("/query", json={"problem": "gamma", "category": "analysis"}).json()
    assert body["total_in_scope"] == 1
    assert body["total_indexed"] == 3
    assert [m["id"] for m in body["matches"]] == ["Gamma"]


def test_unknown_category_is_rejected_with_the_valid_ones(env):
    res = env["client"].post("/query", json={"problem": "alpha", "category": "nonsense"})
    assert res.status_code == 422
    assert "strategy" in res.json()["detail"]


def test_methods_endpoints_serve_the_catalog_and_the_markdown(env):
    catalog = env["client"].get("/methods").json()
    assert catalog["total"] == 3
    assert sorted(catalog["categories"]) == ["analysis", "strategy"]

    detail = env["client"].get("/methods/Alpha").json()
    assert detail["id"] == "Alpha"
    assert "Full documentation for Alpha" in detail["documentation"]


def test_unknown_method_404s_with_the_valid_ids(env):
    res = env["client"].get("/methods/Nope")
    assert res.status_code == 404
    assert "Alpha" in res.json()["detail"]


def test_feedback_round_trip_reaches_stats(env):
    client = env["client"]
    query_id = client.post("/query", json={"problem": "alpha alpha alpha"}).json()["query_id"]

    assert client.post(
        "/feedback", json={"method_id": "Alpha", "rating": 5, "query_id": query_id}
    ).json() == {"recorded": True, "method_id": "Alpha", "rating": 5}

    entries = {e["method_id"]: e for e in client.get("/stats").json()["entries"]}
    assert entries["Alpha"]["rating_count"] == 1
    assert entries["Alpha"]["avg_rating"] == 5.0
    assert entries["Beta"]["recommendation_count"] == 1
    assert entries["Beta"]["avg_rating"] is None


def test_feedback_rejects_an_id_that_is_not_in_the_catalog(env):
    """Over HTTP nobody watches the shell, so a typo must not accumulate silently."""
    res = env["client"].post("/feedback", json={"method_id": "Typo", "rating": 4})
    assert res.status_code == 404
    assert "Alpha" in res.json()["detail"]
    assert not env["settings"].feedback_path.exists()


def test_feedback_rating_is_bounded(env):
    assert (
        env["client"].post("/feedback", json={"method_id": "Alpha", "rating": 9}).status_code == 422
    )


def test_console_is_served_and_self_contained(env):
    """The container may have no egress, so the page must not reference one."""
    html = env["client"].get("/").text
    assert "<title>Methodos AI</title>" in html
    assert "http://" not in html
    assert "https://" not in html
    assert "src=" not in html, "no external script or stylesheet may be pulled in"


def test_methods_dir_follows_the_env_var(tmp_path, monkeypatch):
    """A client launches the process from an arbitrary cwd; the default resolves to nothing."""
    monkeypatch.setenv("METHODOS_METHODS_DIR", str(tmp_path / "elsewhere"))
    assert methods_dir() == tmp_path / "elsewhere"
    monkeypatch.delenv("METHODOS_METHODS_DIR")
    assert methods_dir() == Path("methods")


def test_providers_are_built_once_per_process():
    """A fresh provider per request would re-load ~80MB of weights every call."""
    api_mod._build_providers.cache_clear()
    try:
        first = api_mod._build_providers()
        assert api_mod._build_providers() is first
    finally:
        api_mod._build_providers.cache_clear()
