# Methodos AI — Design Specification

**Status:** Approved (brainstorming phase complete)
**Date:** 2026-05-07
**Author:** Hayal Özkan (with Claude)

## 1. Overview

Methodos AI is an open-source, GitHub-based catalog of management methods (SWOT, Porter's Five Forces, DACI, etc.) paired with a CLI tool that recommends the right method for a stated problem via Retrieval-Augmented Generation.

Two audiences:
- **Humans** browse `methods/*.md` on GitHub for narrative documentation.
- **Machines** index `methods/*.json` (strict, validated) into a local vector store and serve recommendations through a CLI.

The architecture is deliberately small but expert-level: a Pydantic-typed knowledge layer, a Protocol-based provider abstraction (any LLM, any embedding model), an always-rebuild ingest pipeline, and a JSONL feedback log designed to outgrow itself.

### Goals

1. A clone-and-run repo that works offline by default (Ollama + local embeddings).
2. A trivially extensible knowledge base — adding a method is a PR with two files, no code.
3. Provider neutrality — Anthropic, OpenAI, Google, Mistral, Ollama, etc., all behind one Protocol.
4. A foundation for future supervised re-ranking via the feedback loop.

### Non-goals (v1)

- Multi-user identity / authentication.
- Online learning from feedback (re-ranking by ratings).
- A web UI.
- Hosted vector store or backend service.

## 2. Architectural decisions (recorded)

| # | Decision | Choice | Rationale |
|---|---|---|---|
| 1 | Provider strategy | Hybrid behind Protocol; default local | Clone-and-run; expert architecture; one env var swaps to cloud |
| 2 | LLM mechanism | `litellm` wrapped in our `LLMProvider` Protocol | 100+ providers via one dep; we own the seam |
| 3 | Vector store | ChromaDB | First-class metadata, persistence, filtering; FAISS overkill for <10k vectors |
| 4 | Method docs | JSON (canonical, validated) + Markdown (narrative) per method | Separates machine and human audiences cleanly |
| 5 | CLI | Typer + Rich | Type-hint-driven, modern, Markdown rendering in terminal |
| 6 | Schema | Pydantic-generated JSON Schema | Single source of truth; schema is a build artifact |
| 7 | Packaging | `src/` layout + `pyproject.toml` console_script | `methodos query "..."` works as a real shell command |
| 8 | Feedback storage | JSONL append-only | Crash-safe, git-friendly, upgradable to SQLite later |
| 9 | Ingest strategy | Always-rebuild | Chroma is a derived artifact; simpler invariant |
| 10 | Metadata storage | Stash flattened in Chroma | Fewer disk reads at query time; trade denormalization for speed |
| 11 | LLM call shape | One call for all top-k results | Coherent recommendation, one round-trip, one bill |
| 12 | Default cloud LLM | Anthropic Haiku (current model string lives in README, not in code defaults) | Recommended cloud option; one env-var swap. Model strings rot — keep them out of the spec table |
| 13 | Default embedding | `sentence-transformers/all-MiniLM-L6-v2` (local) | 384-dim, ~80MB, runs CPU-only in ms |
| 14 | TTY hint | Print "rate this" hint only when `stdout.isatty()` | Pipe-clean for `methodos query "..." \| jq` |

## 3. Repository structure

```
methodos-ai/
├── README.md                          # Quickstart, Anthropic recommended cloud default
├── CLAUDE.md                          # Imperative rules for AI-assisted development
├── CONTRIBUTING.md                    # How to add a method, run tests, regenerate schema
├── LICENSE                            # MIT
├── pyproject.toml                     # Build, deps, [project.scripts] methodos = ...
├── .env.example                       # MODEL, ANTHROPIC_API_KEY, OPENAI_API_KEY
├── .gitignore                         # data/, .env, __pycache__, .venv
│
├── methods/                           # Knowledge base — pure data
│   ├── SWOT.json
│   ├── SWOT.md
│   ├── Porters_Five_Forces.json
│   ├── Porters_Five_Forces.md
│   ├── DACI_Matrix.json
│   └── DACI_Matrix.md
│
├── schemas/
│   └── method_schema.json             # Generated from Pydantic; CI checks freshness
│
├── src/
│   └── methodos/
│       ├── __init__.py                # __version__
│       ├── models.py                  # Pydantic Method, Category, Duration
│       ├── config.py                  # pydantic-settings Settings
│       ├── ingest.py                  # Read JSON → validate → embed → upsert
│       ├── search.py                  # Query → embed → retrieve → explain
│       ├── feedback.py                # JSONL append + read + stats
│       ├── cli.py                     # Typer app + Rich rendering
│       ├── prompts/
│       │   └── explain.txt            # Prompt template for the explanation step
│       └── providers/
│           ├── __init__.py            # make_llm, make_embedding factories
│           ├── base.py                # LLMProvider, EmbeddingProvider Protocols
│           ├── llm_litellm.py         # Single LLM impl, any model string
│           ├── embedding_local.py     # sentence-transformers (default)
│           └── embedding_openai.py    # OpenAI embeddings (opt-in)
│
├── data/                              # Gitignored — local state
│   ├── chroma/                        # Persistent ChromaDB
│   └── feedback.jsonl                 # Append-only ratings
│
├── tests/
│   ├── conftest.py                    # FakeLLM, FakeEmbedding, tmp Chroma fixtures
│   ├── test_models.py
│   ├── test_ingest.py
│   ├── test_search.py
│   ├── test_feedback.py
│   ├── test_providers.py
│   └── test_cli.py
│
├── scripts/
│   ├── regenerate_schema.py           # Method.model_json_schema() → schemas/...
│   └── validate_methods.py            # Standalone validator (pre-commit + CI)
│
├── Makefile                           # test, lint, ingest, schema, demo
│
└── .github/
    └── workflows/
        ├── ci.yml                     # ruff + mypy + pytest + schema drift
        └── pr-method-validate.yml     # Validates new method JSONs on PR
```

### Three deliberate structural choices

1. **`methods/` at repo root, not under `src/`.** It is data, not code. PRs adding a method should not touch Python.
2. **`scripts/` are imperative one-shots**, separate from the importable `methodos` package. CI runs `regenerate_schema.py` then `git diff --exit-code` to detect drift.
3. **`tests/conftest.py` ships `FakeLLM` and `FakeEmbedding`.** All search tests use them — no network, no flakiness, no API keys in CI.

## 4. Data model

The Pydantic `Method` model is the single source of truth. `schemas/method_schema.json` is *derived* from it via `Method.model_json_schema()`.

### Method (Pydantic)

```python
from enum import Enum
from typing import Annotated
from pydantic import BaseModel, Field, StringConstraints

NonEmptyStr = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]

class Category(str, Enum):
    STRATEGY = "strategy"
    DECISION_MAKING = "decision-making"
    ANALYSIS = "analysis"
    PRIORITIZATION = "prioritization"
    RETROSPECTIVE = "retrospective"

class Duration(BaseModel):
    min_minutes: int = Field(ge=5, le=10_000)
    max_minutes: int = Field(ge=5, le=10_000)

    def model_post_init(self, __context) -> None:
        if self.max_minutes < self.min_minutes:
            raise ValueError("max_minutes must be >= min_minutes")

class Method(BaseModel):
    schema_version: int = 1
    id: Annotated[str, StringConstraints(pattern=r"^[A-Z][A-Za-z0-9_]*$")]
    name: NonEmptyStr
    category: Category
    use_case: Annotated[str, StringConstraints(min_length=40)]
    strengths: list[NonEmptyStr] = Field(min_length=1, max_length=12)
    weaknesses: list[NonEmptyStr] = Field(min_length=1, max_length=12)
    complexity_score: int = Field(ge=1, le=5)
    estimated_duration: Duration
    references: list[str] = Field(default_factory=list)

    @property
    def doc_path(self) -> str:
        return f"methods/{self.id}.md"
```

### Field constraints — rationale

| Field | Constraint | Why |
|---|---|---|
| `id` | regex `^[A-Z][A-Za-z0-9_]*$` | Used as filename + Chroma ID; filesystem-safe and unique |
| `use_case` | `min_length=40` | Embedded text; soft floor against under-specified entries |
| `strengths` / `weaknesses` | min 1, max 12 | At least one of each justifies inclusion; cap prevents bloat |
| `complexity_score` | 1–5 int | Low-cardinality, sortable, filterable in Chroma |
| `estimated_duration` | nested model | Range, not point; ordering enforced |
| `schema_version` | default 1 | Reserved for future migrations |

### Schema regeneration

`scripts/regenerate_schema.py`:

```python
import json
from pathlib import Path
from methodos.models import Method

schema = Method.model_json_schema()
schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
schema["$id"] = "https://github.com/<org>/methodos-ai/schemas/method_schema.json"
Path("schemas/method_schema.json").write_text(json.dumps(schema, indent=2) + "\n")
```

CI runs this and `git diff --exit-code schemas/method_schema.json`. Drift fails the build with a clear message: "Run `make schema` to regenerate."

## 5. Provider abstraction

Two `Protocol`s, three concrete v1 implementations, all swappable via env var. `Protocol` (PEP 544) gives us structural typing — a class needn't inherit from `LLMProvider`, only match its shape.

### Protocols (`src/methodos/providers/base.py`)

```python
from typing import Protocol, runtime_checkable, Sequence

@runtime_checkable
class EmbeddingProvider(Protocol):
    name: str
    dimensions: int
    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...

@runtime_checkable
class LLMProvider(Protocol):
    name: str
    def complete(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> str: ...
```

### Shape decisions

- `embed` takes a sequence (batched APIs are universal; ingesting one-at-a-time is wasteful).
- `dimensions` is exposed so ingest can detect provider mismatch against an existing Chroma collection.
- `name` is stored in collection metadata; mismatch refuses to query and instructs re-ingest.
- `complete` takes split `system` and `user` — every modern provider supports this; litellm normalizes.
- Default `temperature=0.2` for the explanation step: grounded prose, slight variation, not creative writing.

### Error contract

`LLMProvider.complete` raises on failure (rate limits, timeouts, bad credentials, model not found) — it does not return empty strings or sentinel values. We define a single `LLMError(Exception)` in `providers/base.py`; `LiteLLMProvider` wraps litellm's varied exception types into it. `cli.py` catches `LLMError` and renders a Rich-styled error panel *without* dropping the retrieval output — the user still sees ranked methods, just not the explanation. This is what makes `--no-llm` a graceful fallback rather than a workaround. Same pattern for `EmbeddingProvider.embed` → `EmbeddingError`.

### Concrete v1 implementations

1. **`LiteLLMProvider`** (`providers/llm_litellm.py`) — implements `LLMProvider` for any model string of the form `<provider>/<model>`. ~40 lines wrapping `litellm.completion(...)`.
2. **`LocalEmbedding`** (`providers/embedding_local.py`) — implements `EmbeddingProvider` via `sentence-transformers`. Lazy-loads the model on first call.
3. **`OpenAIEmbedding`** (`providers/embedding_openai.py`) — implements `EmbeddingProvider` via the OpenAI SDK. Lazy-imported on construction.

### Lazy imports — mandatory rule

Heavy SDK imports (`openai`, `anthropic`, `sentence_transformers`) MUST happen inside the provider class, never at module top level. Result: a user with only `litellm + chromadb` installed and Anthropic + local embeddings does not pay the OpenAI SDK import cost. CI runs the test suite without ML deps installed for tests using `FakeLLM`.

### Configuration (`src/methodos/config.py`)

```python
from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    model: str = "ollama/llama3.1:8b"
    embedding_provider: Literal["local", "openai"] = "local"
    embedding_model: str = "all-MiniLM-L6-v2"
    chroma_path: Path = Path("data/chroma")
    feedback_path: Path = Path("data/feedback.jsonl")
    top_k: int = 3
```

API keys (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, etc.) are read by litellm itself from env.

### Test fakes

```python
class FakeLLM:
    name = "fake"
    def __init__(self, response: str = "stub explanation"):
        self.response = response
        self.calls: list[tuple[str, str]] = []
    def complete(self, system: str, user: str, **kw) -> str:
        self.calls.append((system, user))
        return self.response

class FakeEmbedding:
    name = "fake"
    dimensions = 4
    def embed(self, texts):
        # Deterministic: hash → first `dimensions` bytes / 255
        import hashlib
        return [
            [b / 255.0 for b in hashlib.sha256(t.encode()).digest()[:self.dimensions]]
            for t in texts
        ]
```

Both satisfy their Protocols structurally. Search tests assert exact orderings against this deterministic embedding.

## 6. Ingest pipeline

`methodos ingest` rebuilds the Chroma collection from `/methods/*.json`. Always-rebuild — no incremental hashing. Chroma is a derived artifact, like a build output.

### Algorithm

```
1. Load Settings, build embedding provider.
2. Glob methods/*.json, parse + Pydantic-validate all.
   Collect errors; do not abort on first failure.
3. If any errors: print all, exit 1.
   Validation also asserts `Path(file).stem == method.id` (filename must match id field).
   Validation rejects duplicate `id` across files.
4. Open Chroma client at settings.chroma_path.
5. Drop existing "methods" collection if present.
6. Create fresh "methods" collection with metadata:
   { "embedding_provider_name": provider.name,
     "embedding_dimensions":     provider.dimensions,
     "schema_version":           1 }
7. Embed all methods.use_case in one batched call.
8. Upsert all (id, embedding, document=use_case, metadata=flattened).
9. Print summary: "ingested N methods (provider: <name>, <dim>d)".
```

### Metadata flattening

Chroma metadata is flat (str/int/float/bool only). Lists are JSON-serialized:

```python
metadata = {
    "name":             method.name,
    "category":         method.category.value,
    "complexity_score": method.complexity_score,
    "duration_min":     method.estimated_duration.min_minutes,
    "duration_max":     method.estimated_duration.max_minutes,
    "strengths_json":   json.dumps(method.strengths),
    "weaknesses_json":  json.dumps(method.weaknesses),
    "references_json":  json.dumps(method.references),
    "doc_path":         method.doc_path,
}
```

The query path reverses this: deserialize `_json` fields, hand structured object to LLM and renderer.

### Math comment block (mandatory, in `ingest.py` and referenced from `search.py`)

```python
# === Similarity scoring math ===
# Embeddings map each method's `use_case` (natural-language description)
# into R^<provider.dimensions> via <provider.name>.
#
# At query time, ChromaDB ranks documents by cosine similarity:
#
#     cos(q, d) = (q · d) / (||q|| * ||d||)
#
# where q is the query embedding and d is a document embedding.
# Higher cosine = more semantically similar in the embedding space.
#
# Chroma returns the cosine *distance* = 1 - cos(q, d). search.py converts:
#     similarity = 1 - distance     ∈ [0, 2], typically [0, 1] for normalized
#
# Note: cosine assumes embeddings are roughly normalized. Both
# sentence-transformers and OpenAI embedding models produce normalized
# vectors by default, so this assumption holds for shipped providers.
```

### Edge cases handled

| Scenario | Behavior |
|---|---|
| Empty `/methods/` | "No methods found", exit 0 |
| JSON parse error | Report file + line, continue, exit 1 at end |
| Pydantic validation error | Report all field errors, continue, exit 1 at end |
| Duplicate `id` | Detected post-load, error |
| Provider changed since last ingest | Drop + recreate (always-rebuild handles it) |

## 7. Search & CLI flow

### End-to-end (`methodos query "<problem>"`)

```
1. cli.py:
   settings  = Settings()
   embedding = make_embedding(settings)
   llm       = make_llm(settings)
   results   = search(query, embedding, llm, top_k=settings.top_k)

2. search.py:retrieve(query, top_k):
   # Verify provider compatibility with the persisted index.
   if collection.metadata["embedding_provider_name"] != embedding.name:
       raise StaleIndexError("embedding provider changed; run `methodos ingest`")
   q_vec = embedding.embed([query])[0]
   raw   = chroma.query(query_embeddings=[q_vec],
                        n_results=top_k * 2,         ← over-fetch
                        include=["metadatas",
                                 "documents",
                                 "distances"])
   candidates = [_rehydrate(r) for r in raw]         ← unflatten metadata
   for c in candidates:
       c.similarity = 1 - c.distance                 ← cosine distance → similarity
   candidates.sort(by=similarity, descending=True)
   top = candidates[:top_k]

3. search.py:explain(query, top):
   prompt = render_template("explain.txt", query=query, methods=top)
   text   = llm.complete(SYSTEM, prompt, temperature=0.2)
   return SearchResults(top, text)

4. cli.py:render(results):
   For each method: Rich Panel (name, complexity dots, strengths,
                                similarity, doc_path)
   Then: Markdown(llm_explanation)
   If sys.stdout.isatty(): print rate hint with query_id
```

### Key design choices

1. **Over-fetch then re-rank.** Chroma returns `top_k * 2`; we keep `top_k` after sorting. Soft hook for a future cross-encoder re-ranker without restructuring.
2. **One LLM call, not N.** All top-k results in a single prompt. The LLM compares/contrasts; we get coherent prose, one round-trip, one bill.
3. **Prompt template in `src/methodos/prompts/explain.txt`**, loaded at runtime. Tweakable without code changes.
4. **`--no-llm` flag** skips the LLM step — useful for debugging retrieval ranking, scripting, demos without API keys.

### Prompt template (`src/methodos/prompts/explain.txt`)

```
SYSTEM:
You are an expert management consultant helping a user select the right method
for their problem. You have a curated catalog of methods. Given the user's
problem and a list of candidate methods (with descriptions, strengths, weaknesses,
complexity, and duration), explain in 2-4 short paragraphs why each candidate
fits or doesn't fit, and give a final recommendation. Be specific to the user's
problem, not generic. If a method is a poor fit despite high similarity, say so.

USER:
Problem:
"""
{query}
"""

Candidate methods (ranked by semantic similarity):

{for each method in top:}
### {method.name}  (similarity: {similarity:.2f}, complexity: {complexity}/5)
Use case: {use_case}
Strengths: {strengths_bullets}
Weaknesses: {weaknesses_bullets}
Duration: {min_minutes}–{max_minutes} minutes
---

Now: explain fit, contrast methods, recommend.
```

### CLI command surface (Typer, finalized)

```
methodos ingest                                           Build vector store from /methods
methodos query "<problem>" [--top-k N]                    Recommend methods
                          [--model MODEL]                  Override LLM
                          [--no-llm]                       Retrieval-only output
methodos list [--category CAT] [--max-complexity N]       Browse the catalog
methodos show ID                                          Print full method (Markdown)
methodos feedback ID --rating 1-5 [--note "..."] [--query-id ID]   Record outcome
methodos stats                                            Aggregated ratings table
methodos --version                                        Version + active providers
```

## 8. Feedback loop (placeholder)

Append-only JSONL at `data/feedback.jsonl`. Two event types:

| event | Emitted by | Purpose |
|---|---|---|
| `recommendation` | every `methodos query` (auto) | Records what the system *suggested* |
| `rating` | `methodos feedback` (manual) | User's verdict on a previously-recommended method |

### Linking the two

`cli.py` mints the ULID — `search.py` stays pure, knowing nothing about feedback. The CLI calls `feedback.log_recommendation(...)` after rendering, then prints the `query_id` in the CLI footer (TTY only):

```
─────
Logged as 01HXY9V8R2K3J9F8M0Q3W4E5T6 · rate with: methodos feedback Porters_Five_Forces -r 4
```

ULIDs are sortable and require no global registry. Without `query_id`, "I rated SWOT 4 stars" floats free with no context — the failure mode that makes naïve feedback loops useless.

### API (`src/methodos/feedback.py`)

```python
def log_recommendation(query: str, method_ids: list[str], model: str) -> str:
    """Append a recommendation event. Returns query_id."""

def log_rating(method_id: str, rating: int, note: str | None,
               query_id: str | None) -> None: ...

def read_events(path: Path = ...) -> Iterator[FeedbackEvent]: ...

def stats() -> dict[str, MethodStats]:
    """Aggregate ratings by method_id; used by `methodos stats`."""
```

`FeedbackEvent` is a Pydantic discriminated union — malformed lines are caught at parse. `read_events` is **lenient**: it skips malformed lines, logs them to stderr with line numbers, and reports a count of skipped events at the end. A years-old log with one corrupt line from a crashed write must not break `methodos stats`.

### Concurrency

JSONL append is *almost* atomic on POSIX for writes < `PIPE_BUF` (4096 bytes), but rating notes can exceed that. Use `with open(path, "a") as f: f.write(line)` plus a `fcntl.flock` advisory lock on POSIX, no-op on Windows where two CLIs racing on the same machine is rare enough to ignore for a placeholder. Documented in code comments.

### Non-features (YAGNI)

- User identity / multi-user.
- Online learning (re-ranking by ratings) — documented as the *first* improvement potential after v1.
- Backend service.

## 9. Testing & CI

### Test layers

| Layer | File | Approach |
|---|---|---|
| Models | `test_models.py` | JSON round-trip; schema regen check; boundary cases |
| Providers | `test_providers.py` | Protocol conformance via `isinstance(p, LLMProvider)`; no network |
| Ingest | `test_ingest.py` | Tmp Chroma + `FakeEmbedding`; idempotency; error path |
| Search | `test_search.py` | Pre-seeded Chroma + `FakeEmbedding(dim=4)`; assert exact ordering; assert prompt content |
| Feedback | `test_feedback.py` | JSONL round-trip; `stats()` aggregation; concurrency (POSIX-only) |
| CLI | `test_cli.py` | `typer.testing.CliRunner`; `--help`, `--version`, error exits, JSON-piped output |

### Two principles

1. **No network.** Every test uses fakes. Real providers only via opt-in `pytest -m integration`, gated on `ANTHROPIC_API_KEY`/`OPENAI_API_KEY`, never run in CI.
2. **Determinism.** `FakeEmbedding` returns vectors derived from `hashlib.sha256(text)[:dim]` so same text → same vector → same Chroma ranking. Tests assert exact orderings.

### CI (`.github/workflows/ci.yml`)

```yaml
- ruff check + format
- mypy --strict src/methodos/
- python scripts/regenerate_schema.py
  git diff --exit-code schemas/         (schema drift check)
- python scripts/validate_methods.py    (every method JSON passes schema)
- pytest -q                             (default marks only)
- pytest --collect-only -m integration  (sanity that integration tests parse)
```

`pyproject.toml` `[project.optional-dependencies].dev` declares ruff, mypy, pytest, types stubs. Onboarding: `pip install -e ".[dev]"`.

**Note:** `litellm` ships incomplete type stubs as of writing; `pyproject.toml` includes a `[[tool.mypy.overrides]] module = "litellm.*" ignore_missing_imports = true` block to keep `mypy --strict` green without polluting code with `# type: ignore` pragmas.

A second workflow `pr-method-validate.yml` runs only on PRs touching `methods/**` — fast feedback for community method-additions, the most common kind of PR.

## 10. CLAUDE.md outline

Imperative, short, every line earns its place:

```markdown
# CLAUDE.md — Working with Methodos AI

## Project shape
- src/ layout, Pydantic-everything, Typer CLI, ChromaDB + litellm.
- Methods are data (`methods/*.json` + `*.md`), not code.
- The schema in `schemas/` is *generated*, never hand-edited.

## Commands you'll run constantly
make test       # pytest with fast (non-network) tests
make lint       # ruff + mypy
make ingest     # rebuild local Chroma from /methods
make schema     # regenerate schemas/method_schema.json from Pydantic
make demo       # ingest + a sample query, end-to-end smoke

## Hard rules (override defaults)
1. NEVER import `openai`, `anthropic`, `sentence_transformers`, etc. at module
   top level. They MUST be lazy-imported inside the provider class.
2. NEVER add a method to /methods without a matching .md companion.
3. NEVER hand-edit schemas/method_schema.json. Run `make schema`.
4. ALWAYS run with `--no-llm` first when debugging retrieval — separates
   ranking issues from LLM issues.

## How to add a new method
1. Create methods/<Id>.json + methods/<Id>.md
2. python -m methodos.ingest
3. methodos query "<test problem>"

## How to add a new provider
1. Implement the Protocol in src/methodos/providers/
2. Wire it in providers/__init__.py
3. Add a test in test_providers.py asserting Protocol conformance
4. Lazy-import any heavy deps inside __init__

## Architectural principles (priority order)
1. Knowledge layer is data. Code never hard-codes a method.
2. Provider boundary is sacred — only Protocols cross it.
3. Always-rebuild ingest. Chroma is a derived artifact.
4. Determinism in tests. Fakes, not mocks.
5. JSONL feedback is the placeholder. Don't pre-build a SQLite migration.

## Things to leave alone
- The math comment block in ingest.py / search.py (prompt requirement).
- The TTY-only feedback hint (intentional UX choice).
- The over-fetch-then-rerank shape in search.py (extension hook).
```

## 11. Implementation phases

The implementation plan (next skill — `writing-plans`) will sequence work as:

1. **Skeleton** — `pyproject.toml`, src layout, empty modules, `models.py` + Method, schema regeneration script, CI green.
2. **Knowledge base** — three sample methods (JSON + MD), validator script, schema drift check.
3. **Provider layer** — Protocols, `LiteLLMProvider`, `LocalEmbedding`, `OpenAIEmbedding`, `FakeLLM` / `FakeEmbedding`, conformance tests.
4. **Ingest** — full pipeline + math comment + tests with `FakeEmbedding`.
5. **Search** — retrieve + explain + prompt template + tests.
6. **CLI** — Typer commands, Rich rendering, TTY detection.
7. **Feedback** — JSONL + stats + tests.
8. **Docs** — README + CLAUDE.md + CONTRIBUTING.md + LICENSE — written only after the code shape is concrete.

## 12. Improvement potentials (post-v1)

Documented in README, ordered by ROI:

1. **Online learning re-ranker** — boost methods that are highly rated for similar queries.
2. **Cross-encoder re-rank step** — post-retrieval, pre-LLM; dedicated quality bump.
3. **Migrate feedback JSONL → SQLite** — when volume justifies it (importer is a one-shot script).
4. **Hybrid search** — combine BM25 over `name`/`category` with semantic search.
5. **Multilingual embeddings** — for non-English problem statements.
6. **Web UI / Streamlit demo** — for users uncomfortable with CLI.
7. **Claude Code MCP server** — expose `methodos query` as a tool to other agents.
8. **Method composition** — recommend *sequences* of methods (e.g., "SWOT then DACI").
