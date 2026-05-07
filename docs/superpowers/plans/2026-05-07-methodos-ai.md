# Methodos AI Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an open-source GitHub-based catalog of management methods (SWOT, Porter's, DACI) with a CLI RAG tool that recommends methods for natural-language problems.

**Architecture:** A Pydantic-typed knowledge layer (`methods/*.json` + `*.md`), a Protocol-based provider abstraction (`LLMProvider`, `EmbeddingProvider`) with a litellm-backed implementation, an always-rebuild ChromaDB ingest pipeline, a Typer + Rich CLI, and an append-only JSONL feedback log. Default config runs offline (Ollama + sentence-transformers); one env var swaps to Anthropic / OpenAI cloud.

**Tech Stack:** Python 3.11+, Pydantic 2, pydantic-settings, ChromaDB, litellm, sentence-transformers (optional), Typer, Rich, pytest, ruff, mypy. Build via `pyproject.toml` (PEP 621), src/ layout, console_script entry point.

**Reference spec:** [docs/superpowers/specs/2026-05-07-methodos-ai-design.md](../specs/2026-05-07-methodos-ai-design.md)

---

## Conventions

- **TDD throughout.** Every implementation step is preceded by a failing test step. Skip only for pure config files (pyproject.toml, .gitignore).
- **Frequent commits.** Each task ends with a commit. Commit messages follow conventional commits (`feat:`, `test:`, `chore:`, `docs:`).
- **Run from worktree root.** All commands assume `cwd` is the worktree root.
- **Python venv.** First task creates a venv at `.venv/`. Activate with `.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (POSIX). All `python` / `pytest` commands assume an active venv.
- **Code style.** Ruff format + check. Mypy `--strict` on `src/methodos/`. Tests can be looser-typed where readable.

---

## Chunk 1: Project skeleton

Goal of this chunk: a working Python package that imports cleanly, has CI green on lint + types + tests (even with no real tests yet), and a Pydantic `Method` model that produces a JSON Schema artifact in `schemas/`.

### Task 1: Bootstrap pyproject.toml + src layout + venv

**Files:**
- Create: `pyproject.toml`
- Create: `src/methodos/__init__.py`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `Makefile`

- [ ] **Step 1: Create `.gitignore`**

```
.venv/
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/
.mypy_cache/
.ruff_cache/
*.egg-info/
build/
dist/
.env
data/
.coverage
htmlcov/
```

- [ ] **Step 2: Create `pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "methodos"
version = "0.1.0"
description = "An expert-level RAG catalog of management methods."
readme = "README.md"
requires-python = ">=3.11"
license = { text = "MIT" }
authors = [{ name = "Hayal Özkan" }]
keywords = ["rag", "management", "methods", "swot", "decision-making"]
classifiers = [
  "Development Status :: 3 - Alpha",
  "License :: OSI Approved :: MIT License",
  "Programming Language :: Python :: 3.11",
  "Programming Language :: Python :: 3.12",
]
dependencies = [
  "pydantic>=2.6",
  "pydantic-settings>=2.2",
  "chromadb>=0.5",
  "litellm>=1.40",
  "typer>=0.12",
  "rich>=13.7",
  "python-ulid>=2.2",
  "jsonschema>=4.21",
]

[project.optional-dependencies]
local = ["sentence-transformers>=2.7"]
openai = ["openai>=1.30"]
dev = [
  "pytest>=8",
  "pytest-cov>=5",
  "ruff>=0.4",
  "mypy>=1.10",
  "types-jsonschema",
]

[project.scripts]
methodos = "methodos.cli:app"

[tool.hatch.build.targets.wheel]
packages = ["src/methodos"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "SIM", "RUF"]
ignore = ["E501"]  # handled by formatter

[tool.mypy]
python_version = "3.11"
strict = true
files = ["src/methodos"]

[[tool.mypy.overrides]]
module = "litellm.*"
ignore_missing_imports = true

[[tool.mypy.overrides]]
module = "chromadb.*"
ignore_missing_imports = true

[[tool.mypy.overrides]]
module = "sentence_transformers.*"
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
  "integration: requires network/API keys; not run in default suite",
]
addopts = "-q --strict-markers"
```

- [ ] **Step 3: Create `src/methodos/__init__.py`**

```python
"""Methodos AI — RAG catalog of management methods."""
__version__ = "0.1.0"
```

- [ ] **Step 4: Create `.env.example`**

```
# Pick one cloud LLM (or leave blank to use the local Ollama default)
# ANTHROPIC_API_KEY=sk-ant-...
# OPENAI_API_KEY=sk-...

# Override the default model:
# METHODOS_MODEL=anthropic/claude-3-5-haiku-20241022
# METHODOS_MODEL=openai/gpt-4o-mini
# METHODOS_MODEL=ollama/llama3.1:8b

# Optional: switch embedding provider to OpenAI (default: local sentence-transformers)
# METHODOS_EMBEDDING_PROVIDER=openai
# METHODOS_EMBEDDING_MODEL=text-embedding-3-small
```

- [ ] **Step 5: Create `Makefile`**

```makefile
.PHONY: install test lint fmt schema ingest demo clean

install:
	pip install -e ".[dev,local]"

test:
	pytest

lint:
	ruff check src tests scripts
	ruff format --check src tests scripts
	mypy src/methodos

fmt:
	ruff format src tests scripts
	ruff check --fix src tests scripts

schema:
	python scripts/regenerate_schema.py

ingest:
	python -m methodos.cli ingest

demo: ingest
	python -m methodos.cli query "we need to enter a new market without burning cash" --no-llm

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache build dist *.egg-info data/chroma
```

- [ ] **Step 6: Create venv, install, verify import**

Run:
```
python -m venv .venv
.venv\Scripts\activate    (or: source .venv/bin/activate)
pip install -e ".[dev]"
python -c "import methodos; print(methodos.__version__)"
```
Expected: `0.1.0`

- [ ] **Step 7: Commit**

```
git add pyproject.toml src/methodos/__init__.py .gitignore .env.example Makefile
git commit -m "chore: bootstrap project skeleton with src/ layout"
```

---

### Task 2: Pydantic `Method` model with TDD

**Files:**
- Create: `src/methodos/models.py`
- Create: `tests/__init__.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write failing test `test_models.py`**

```python
import pytest
from pydantic import ValidationError
from methodos.models import Method, Category, Duration

def _valid_payload(**overrides):
    base = dict(
        id="SWOT",
        name="SWOT Analysis",
        category="strategy",
        use_case="A structured framework for evaluating internal strengths and weaknesses against external opportunities and threats.",
        strengths=["widely recognized", "simple to facilitate"],
        weaknesses=["can be superficial", "no prioritization"],
        complexity_score=2,
        estimated_duration={"min_minutes": 60, "max_minutes": 180},
        references=["https://en.wikipedia.org/wiki/SWOT_analysis"],
    )
    base.update(overrides)
    return base

def test_valid_method_round_trips():
    m = Method.model_validate(_valid_payload())
    assert m.id == "SWOT"
    assert m.category is Category.STRATEGY
    assert m.estimated_duration.min_minutes == 60
    assert m.doc_path == "methods/SWOT.md"

def test_id_must_be_pascal_or_snake_case_starting_capital():
    with pytest.raises(ValidationError):
        Method.model_validate(_valid_payload(id="swot"))   # lowercase start
    with pytest.raises(ValidationError):
        Method.model_validate(_valid_payload(id="2SWOT"))  # digit start

def test_use_case_minimum_length_enforced():
    with pytest.raises(ValidationError):
        Method.model_validate(_valid_payload(use_case="too short"))

def test_strengths_must_be_non_empty():
    with pytest.raises(ValidationError):
        Method.model_validate(_valid_payload(strengths=[]))

def test_strengths_capped_at_twelve():
    with pytest.raises(ValidationError):
        Method.model_validate(_valid_payload(strengths=[f"item {i}" for i in range(13)]))

def test_complexity_score_bounded_one_to_five():
    with pytest.raises(ValidationError):
        Method.model_validate(_valid_payload(complexity_score=0))
    with pytest.raises(ValidationError):
        Method.model_validate(_valid_payload(complexity_score=6))

def test_duration_max_must_be_ge_min():
    with pytest.raises(ValidationError):
        Method.model_validate(_valid_payload(
            estimated_duration={"min_minutes": 120, "max_minutes": 60}
        ))

def test_unknown_category_rejected():
    with pytest.raises(ValidationError):
        Method.model_validate(_valid_payload(category="dance"))
```

- [ ] **Step 2: Run test, expect failure**

Run: `pytest tests/test_models.py -v`
Expected: ImportError or ModuleNotFoundError on `methodos.models`.

- [ ] **Step 3: Implement `src/methodos/models.py`**

```python
"""Canonical data model for a management method."""
from __future__ import annotations

from enum import Enum
from typing import Annotated, Any

from pydantic import BaseModel, Field, StringConstraints

NonEmptyStr = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
"""A trimmed string with at least one non-whitespace character."""


class Category(str, Enum):
    """Coarse-grained categorization of methods.

    Adding a category is a non-breaking schema change; bump `schema_version`
    only when a *required* field changes.
    """

    STRATEGY = "strategy"
    DECISION_MAKING = "decision-making"
    ANALYSIS = "analysis"
    PRIORITIZATION = "prioritization"
    RETROSPECTIVE = "retrospective"


class Duration(BaseModel):
    """Estimated wall-clock time to apply the method end-to-end."""

    min_minutes: int = Field(ge=5, le=10_000)
    max_minutes: int = Field(ge=5, le=10_000)

    def model_post_init(self, __context: Any) -> None:
        if self.max_minutes < self.min_minutes:
            raise ValueError("max_minutes must be >= min_minutes")


class Method(BaseModel):
    """A management method as represented in the catalog.

    The `use_case` field is the text we embed for retrieval. All other fields
    are surfaced to the user via CLI rendering or filtering. Adding a new
    field that is *not* required is non-breaking; adding a required field
    bumps `schema_version` and requires a migration of existing JSON files.
    """

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
        """Relative path to the human-readable Markdown companion."""
        return f"methods/{self.id}.md"
```

- [ ] **Step 4: Run tests, expect all pass**

Run: `pytest tests/test_models.py -v`
Expected: 8 passed.

- [ ] **Step 5: Commit**

```
git add src/methodos/models.py tests/__init__.py tests/test_models.py
git commit -m "feat(models): add Method/Category/Duration with full validation"
```

---

### Task 3: Schema regeneration script + drift check

**Files:**
- Create: `scripts/regenerate_schema.py`
- Create: `schemas/method_schema.json`
- Modify: `tests/test_models.py` (append schema-drift test)

- [ ] **Step 1: Add failing schema-drift test to `tests/test_models.py`**

Append:
```python
import json
import subprocess
import sys
from pathlib import Path

def test_committed_schema_matches_pydantic_model(tmp_path):
    """Regenerating the schema should produce a byte-identical file."""
    repo_root = Path(__file__).parent.parent
    target = tmp_path / "method_schema.json"
    script = repo_root / "scripts" / "regenerate_schema.py"
    subprocess.check_call(
        [sys.executable, str(script), "--out", str(target)],
        cwd=repo_root,
    )
    committed = (repo_root / "schemas" / "method_schema.json").read_text()
    regenerated = target.read_text()
    assert committed == regenerated, "Run `make schema` to update the committed schema."
```

- [ ] **Step 2: Run, expect failure**

Run: `pytest tests/test_models.py::test_committed_schema_matches_pydantic_model -v`
Expected: FileNotFoundError on the script.

- [ ] **Step 3: Implement `scripts/regenerate_schema.py`**

```python
"""Regenerate schemas/method_schema.json from the Pydantic Method model.

The Pydantic model is the single source of truth. Run after any change to
`src/methodos/models.py`. CI will fail if the committed schema drifts.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from methodos.models import Method


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("schemas/method_schema.json"),
        help="Output path (default: schemas/method_schema.json)",
    )
    args = parser.parse_args()

    schema = Method.model_json_schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = (
        "https://github.com/Malkreide/methodos-ai/blob/main/schemas/method_schema.json"
    )
    schema["title"] = "Method"

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(schema, indent=2, sort_keys=False) + "\n")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Generate the schema and commit it**

Run: `python scripts/regenerate_schema.py`
Expected: writes `schemas/method_schema.json`. Inspect briefly.

- [ ] **Step 5: Run drift test, expect pass**

Run: `pytest tests/test_models.py::test_committed_schema_matches_pydantic_model -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```
git add scripts/regenerate_schema.py schemas/method_schema.json tests/test_models.py
git commit -m "feat(schema): generate JSON Schema from Pydantic model with drift check"
```

---

### Task 4: Settings via pydantic-settings

**Files:**
- Create: `src/methodos/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Failing test**

```python
from pathlib import Path
import os
from methodos.config import Settings

def test_defaults_are_offline_friendly(monkeypatch):
    for k in ("METHODOS_MODEL", "METHODOS_EMBEDDING_PROVIDER",
             "METHODOS_EMBEDDING_MODEL", "METHODOS_TOP_K"):
        monkeypatch.delenv(k, raising=False)
    s = Settings(_env_file=None)
    assert s.model.startswith("ollama/")
    assert s.embedding_provider == "local"
    assert s.top_k == 3
    assert isinstance(s.chroma_path, Path)

def test_env_overrides(monkeypatch):
    monkeypatch.setenv("METHODOS_MODEL", "anthropic/claude-3-5-haiku-20241022")
    monkeypatch.setenv("METHODOS_EMBEDDING_PROVIDER", "openai")
    monkeypatch.setenv("METHODOS_TOP_K", "5")
    s = Settings(_env_file=None)
    assert s.model == "anthropic/claude-3-5-haiku-20241022"
    assert s.embedding_provider == "openai"
    assert s.top_k == 5

def test_invalid_embedding_provider_rejected(monkeypatch):
    monkeypatch.setenv("METHODOS_EMBEDDING_PROVIDER", "elasticsearch")
    import pytest
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
```

- [ ] **Step 2: Run, expect failure (ImportError)**

Run: `pytest tests/test_config.py -v`

- [ ] **Step 3: Implement `src/methodos/config.py`**

```python
"""Runtime settings loaded from environment + .env."""
from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All env vars are prefixed `METHODOS_` (e.g., METHODOS_MODEL)."""

    model_config = SettingsConfigDict(
        env_prefix="METHODOS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    model: str = "ollama/llama3.1:8b"
    """Litellm model string in the form '<provider>/<model>'."""

    embedding_provider: Literal["local", "openai"] = "local"
    embedding_model: str = "all-MiniLM-L6-v2"
    """For provider='local': sentence-transformers model name.
    For provider='openai': e.g. 'text-embedding-3-small'."""

    chroma_path: Path = Path("data/chroma")
    feedback_path: Path = Path("data/feedback.jsonl")
    top_k: int = 3
```

- [ ] **Step 4: Run tests, expect pass**

Run: `pytest tests/test_config.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```
git add src/methodos/config.py tests/test_config.py
git commit -m "feat(config): add Settings (pydantic-settings) with env-prefix METHODOS_"
```

---

### Task 5: CI workflow (lint + types + tests + schema drift)

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Write `.github/workflows/ci.yml`**

```yaml
name: ci

on:
  push:
    branches: [main]
  pull_request:

jobs:
  lint-test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip
      - name: Install
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"
      - name: Ruff lint
        run: ruff check src tests scripts
      - name: Ruff format check
        run: ruff format --check src tests scripts
      - name: Mypy
        run: mypy src/methodos
      - name: Schema drift check
        run: |
          python scripts/regenerate_schema.py --out /tmp/schema_check.json
          diff -u schemas/method_schema.json /tmp/schema_check.json
      - name: Tests
        run: pytest -q
      - name: Integration tests parse-only
        run: pytest --collect-only -m integration
```

- [ ] **Step 2: Run all local checks before committing**

Run:
```
ruff check src tests scripts
ruff format src tests scripts
mypy src/methodos
pytest -q
```
Expected: all green.

- [ ] **Step 3: Commit**

```
git add .github/workflows/ci.yml
git commit -m "ci: add lint + types + tests + schema-drift workflow"
```

---

## Chunk 2: Knowledge base (sample methods + validator)

Goal: three real methods committed as JSON + Markdown, plus a standalone validator script and the second CI workflow that gates PRs touching `methods/**`.

### Task 6: Add SWOT method (JSON + Markdown)

**Files:**
- Create: `methods/SWOT.json`
- Create: `methods/SWOT.md`

- [ ] **Step 1: Write `methods/SWOT.json`**

```json
{
  "schema_version": 1,
  "id": "SWOT",
  "name": "SWOT Analysis",
  "category": "strategy",
  "use_case": "A structured framework for evaluating an organization, project, or initiative across four quadrants: internal Strengths and Weaknesses, and external Opportunities and Threats. Best used early in strategic planning when the team needs to surface assumptions and align on the competitive landscape before committing to a direction.",
  "strengths": [
    "widely recognized — minimal explanation needed",
    "simple to facilitate in a 1–2 hour workshop",
    "outputs are immediately actionable as discussion fuel",
    "low complexity barrier — works with mixed-experience groups"
  ],
  "weaknesses": [
    "can be superficial without rigorous evidence behind each cell",
    "no built-in prioritization between items",
    "doesn't model dynamics over time",
    "easily becomes a wishlist rather than an analysis"
  ],
  "complexity_score": 2,
  "estimated_duration": { "min_minutes": 60, "max_minutes": 180 },
  "references": [
    "https://en.wikipedia.org/wiki/SWOT_analysis",
    "https://hbr.org/1982/05/the-strategy-process"
  ]
}
```

- [ ] **Step 2: Write `methods/SWOT.md`**

```markdown
# SWOT Analysis

A structured framework for surfacing assumptions about an organization or
initiative across four quadrants:

- **Strengths** — internal advantages
- **Weaknesses** — internal disadvantages
- **Opportunities** — external favorable trends
- **Threats** — external risks

## When to use

- Strategic planning kickoff for a new project, product, or year
- After a major external change (regulation, competitor move, market shift)
- As a warm-up to a deeper analysis like Porter's Five Forces

## When *not* to use

- When you already know the strategic direction and just need execution detail
- As the *final* word — it's a starting point, not a decision-maker
- For tactical operational decisions (use a DACI matrix instead)

## Facilitation outline (90 min)

1. (10 min) Frame the question. "We're SWOTing *what*, exactly?"
2. (20 min) Silent brainstorm: each participant writes items per quadrant
3. (20 min) Cluster + dedupe per quadrant on a shared whiteboard
4. (20 min) Cross-quadrant pairing: pair Strengths→Opportunities, Weaknesses→Threats
5. (20 min) Identify 2–3 strategic priorities

## Common pitfalls

- Treating "obvious" facts as Strengths (every competitor has them too)
- Filling Threats with hypothetical doomsday scenarios with no evidence
- Skipping the cross-quadrant pairing — that's where insight lives

## See also

- [Porter's Five Forces](Porters_Five_Forces.md) — when SWOT's "Threats" needs a structural view of competition
- [Wikipedia: SWOT analysis](https://en.wikipedia.org/wiki/SWOT_analysis)
```

- [ ] **Step 3: Validate manually**

Run:
```
python -c "import json; from methodos.models import Method; Method.model_validate(json.loads(open('methods/SWOT.json').read())); print('OK')"
```
Expected: `OK`.

- [ ] **Step 4: Commit**

```
git add methods/SWOT.json methods/SWOT.md
git commit -m "feat(methods): add SWOT analysis"
```

---

### Task 7: Add Porter's Five Forces method

**Files:**
- Create: `methods/Porters_Five_Forces.json`
- Create: `methods/Porters_Five_Forces.md`

- [ ] **Step 1: Write `methods/Porters_Five_Forces.json`**

```json
{
  "schema_version": 1,
  "id": "Porters_Five_Forces",
  "name": "Porter's Five Forces",
  "category": "strategy",
  "use_case": "A structural analysis of the competitive intensity and attractiveness of an industry by examining five forces: rivalry among existing competitors, threat of new entrants, threat of substitutes, bargaining power of suppliers, and bargaining power of buyers. Best used when assessing whether to enter a new market, launch a new product line, or evaluate the long-term defensibility of a position.",
  "strengths": [
    "structural — surfaces forces that are easy to overlook",
    "framework is well-known in MBA and consulting contexts",
    "produces a defensible written analysis, not just a brainstorm",
    "links directly to strategic posture decisions (cost leadership, differentiation, focus)"
  ],
  "weaknesses": [
    "static snapshot — doesn't model changes over time well",
    "originally framed for manufacturing; software/network-effect markets need adaptation",
    "requires real industry data, not just a workshop",
    "underweights complementors and the role of platform dynamics"
  ],
  "complexity_score": 4,
  "estimated_duration": { "min_minutes": 240, "max_minutes": 1200 },
  "references": [
    "https://hbr.org/2008/01/the-five-competitive-forces-that-shape-strategy",
    "https://en.wikipedia.org/wiki/Porter%27s_five_forces_analysis"
  ]
}
```

- [ ] **Step 2: Write `methods/Porters_Five_Forces.md`**

```markdown
# Porter's Five Forces

A structural framework (Porter, 1979) for analyzing the competitive intensity
and long-run attractiveness of an industry along five dimensions.

## The five forces

1. **Rivalry among existing competitors** — how aggressively existing firms compete
2. **Threat of new entrants** — how easy it is for outsiders to break in
3. **Threat of substitutes** — alternative products that meet the same need
4. **Bargaining power of suppliers** — how much pricing/terms power inputs hold
5. **Bargaining power of buyers** — how much pricing/terms power customers hold

## When to use

- Considering entering a new industry or market segment
- Evaluating the defensibility of a current position over a 3–10 year horizon
- Pricing strategy decisions in commodity-leaning markets

## When *not* to use

- Highly dynamic, network-effect-driven markets without serious adaptation
  (consider Hax/Wilde Delta Model or Brandenburger/Nalebuff's Value Net instead)
- Tactical short-term decisions
- When you don't have access to real industry data — the analysis becomes guesswork

## Facilitation outline (4–8 hours plus desk research)

1. Define the industry boundary precisely. "Software" is not an industry; "vertical SaaS for dental practices in the EU" might be.
2. For each force, list 5–10 evidence-based observations. Cite sources.
3. Rate each force on a 1–5 scale (1 = weak, 5 = overwhelming).
4. Summarize: industry attractiveness, dominant force, strategic implications.
5. Tie to posture: cost leadership, differentiation, focus.

## Common pitfalls

- Drawing the industry boundary too broad (everything looks attractive) or too narrow (you have a monopoly of one)
- Confusing your *firm's* strengths with the *industry's* attractiveness
- Treating buyer/supplier power as binary instead of analyzing concentration, switching cost, and information asymmetry separately

## See also

- [SWOT Analysis](SWOT.md) — Porter's gives the "Threats" cell rigor
- [Harvard Business Review: The Five Competitive Forces That Shape Strategy](https://hbr.org/2008/01/the-five-competitive-forces-that-shape-strategy)
```

- [ ] **Step 3: Validate manually**

Run: `python -c "import json; from methodos.models import Method; Method.model_validate(json.loads(open('methods/Porters_Five_Forces.json').read())); print('OK')"`
Expected: `OK`.

- [ ] **Step 4: Commit**

```
git add methods/Porters_Five_Forces.json methods/Porters_Five_Forces.md
git commit -m "feat(methods): add Porter's Five Forces"
```

---

### Task 8: Add DACI Matrix method

**Files:**
- Create: `methods/DACI_Matrix.json`
- Create: `methods/DACI_Matrix.md`

- [ ] **Step 1: Write `methods/DACI_Matrix.json`**

```json
{
  "schema_version": 1,
  "id": "DACI_Matrix",
  "name": "DACI Decision-Making Framework",
  "category": "decision-making",
  "use_case": "A role-assignment framework for cross-functional decisions, naming exactly one Driver, one Approver, multiple Contributors, and the Informed for a specific decision. Best used when decisions are stalling because nobody knows who actually owns the call versus who is consulted versus who is just kept in the loop.",
  "strengths": [
    "forces a single Approver — eliminates decision-by-committee drift",
    "trivial to facilitate — one table, one meeting",
    "scales from team-level to org-level decisions",
    "creates an audit trail for retrospectives"
  ],
  "weaknesses": [
    "doesn't help if the disagreement is *substantive* (use a different method first)",
    "tempting to overuse — not every decision needs a DACI",
    "the Approver role can feel autocratic in flat cultures",
    "requires the Driver to be senior enough to push back on the Approver"
  ],
  "complexity_score": 1,
  "estimated_duration": { "min_minutes": 30, "max_minutes": 90 },
  "references": [
    "https://www.atlassian.com/team-playbook/plays/daci",
    "https://en.wikipedia.org/wiki/Responsibility_assignment_matrix"
  ]
}
```

- [ ] **Step 2: Write `methods/DACI_Matrix.md`**

```markdown
# DACI Decision-Making Framework

A four-role assignment for cross-functional decisions.

| Role | Count | Responsibility |
|---|---|---|
| **D**river | 1 | Coordinates the decision-making process; surfaces options; drives to closure |
| **A**pprover | 1 | Makes the final call; can veto |
| **C**ontributors | many | Provide input, expertise, evidence; do not vote |
| **I**nformed | many | Notified of the outcome; not consulted in advance |

## When to use

- A decision has been "in flight" for >2 weeks without resolution
- Multiple teams disagree on direction and need a clean tiebreaker
- High-stakes decisions where post-hoc accountability matters (and "we all decided" is not enough)

## When *not* to use

- The disagreement is substantive (about *what* to decide), not procedural (about *who* decides). Use SWOT or Five Forces first.
- For everyday small decisions inside a single team
- When the right answer is obvious — DACI is overhead, not decoration

## Facilitation outline (30–60 min)

1. (5 min) Write the decision in one sentence: "Should we [verb] [object]?"
2. (10 min) Assign D and A by name, not by role. Get the A's verbal commitment.
3. (15 min) List Contributors and what they will contribute (data, opinion, veto over a sub-area).
4. (5 min) List Informed parties and the channel/cadence of notification.
5. (Async) Driver runs the process; Approver decides; everyone else either contributes once or just gets the memo.

## Common pitfalls

- Assigning "the team" as Approver — defeats the purpose
- Confusing Contributors with Approvers — Contributors don't have veto
- Treating Informed as Contributors — they shouldn't be in the meeting

## See also

- [RACI matrix](https://en.wikipedia.org/wiki/Responsibility_assignment_matrix) — DACI's older cousin; better for ongoing responsibilities than one-shot decisions
- [Atlassian Team Playbook: DACI](https://www.atlassian.com/team-playbook/plays/daci)
```

- [ ] **Step 3: Validate manually + all three at once**

Run:
```
python -c "
import json
from pathlib import Path
from methodos.models import Method
for p in Path('methods').glob('*.json'):
    Method.model_validate(json.loads(p.read_text()))
    print(p.stem, 'OK')
"
```
Expected: `DACI_Matrix OK / Porters_Five_Forces OK / SWOT OK` (any order).

- [ ] **Step 4: Commit**

```
git add methods/DACI_Matrix.json methods/DACI_Matrix.md
git commit -m "feat(methods): add DACI decision-making matrix"
```

---

### Task 9: `validate_methods.py` standalone validator

**Files:**
- Create: `scripts/validate_methods.py`
- Create: `tests/test_validate_methods.py`

- [ ] **Step 1: Failing test**

```python
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent
SCRIPT = REPO / "scripts" / "validate_methods.py"

def test_validates_all_methods_in_repo():
    res = subprocess.run([sys.executable, str(SCRIPT)], cwd=REPO, capture_output=True, text=True)
    assert res.returncode == 0, res.stderr

def test_rejects_methods_with_invalid_id_field(tmp_path):
    # Create a temp methods dir with an invalid file
    bad = tmp_path / "methods"
    bad.mkdir()
    (bad / "lowercase.json").write_text(json.dumps({
        "id": "lowercase",
        "name": "Bad",
        "category": "strategy",
        "use_case": "x" * 50,
        "strengths": ["a"], "weaknesses": ["b"],
        "complexity_score": 1,
        "estimated_duration": {"min_minutes": 5, "max_minutes": 10}
    }))
    res = subprocess.run(
        [sys.executable, str(SCRIPT), "--methods-dir", str(bad)],
        cwd=REPO, capture_output=True, text=True,
    )
    assert res.returncode != 0
    assert "lowercase" in res.stderr or "lowercase" in res.stdout

def test_rejects_filename_id_mismatch(tmp_path):
    bad = tmp_path / "methods"
    bad.mkdir()
    # filename says SWOT, id says SWOT2
    (bad / "SWOT.json").write_text(json.dumps({
        "id": "SWOT2",
        "name": "Wrong",
        "category": "strategy",
        "use_case": "x" * 50,
        "strengths": ["a"], "weaknesses": ["b"],
        "complexity_score": 1,
        "estimated_duration": {"min_minutes": 5, "max_minutes": 10}
    }))
    res = subprocess.run(
        [sys.executable, str(SCRIPT), "--methods-dir", str(bad)],
        cwd=REPO, capture_output=True, text=True,
    )
    assert res.returncode != 0
    output = res.stdout + res.stderr
    assert "SWOT" in output and ("mismatch" in output.lower() or "must equal" in output.lower())
```

- [ ] **Step 2: Run, expect failure**

Run: `pytest tests/test_validate_methods.py -v`

- [ ] **Step 3: Implement `scripts/validate_methods.py`**

```python
"""Validate every method JSON in /methods/ against the Pydantic Method model.

Used by:
  * pre-commit hook (fast local feedback)
  * CI workflow `pr-method-validate.yml` on PRs touching methods/**
  * manual: `python scripts/validate_methods.py`

Exit codes:
  0  — all methods valid
  1  — at least one validation error (all errors printed before exit)
  2  — usage error (e.g. methods/ does not exist)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from methodos.models import Method


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--methods-dir",
        type=Path,
        default=Path("methods"),
        help="Directory containing method JSON files (default: methods/)",
    )
    args = parser.parse_args()

    if not args.methods_dir.is_dir():
        print(f"error: {args.methods_dir} is not a directory", file=sys.stderr)
        return 2

    files = sorted(args.methods_dir.glob("*.json"))
    if not files:
        print(f"warning: no JSON files found in {args.methods_dir}")
        return 0

    errors: list[str] = []
    seen_ids: dict[str, Path] = {}

    for path in files:
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError as e:
            errors.append(f"{path}: invalid JSON: {e}")
            continue

        try:
            method = Method.model_validate(data)
        except ValidationError as e:
            errors.append(f"{path}: {e}")
            continue

        # Filename must match id field.
        if path.stem != method.id:
            errors.append(
                f"{path}: filename stem '{path.stem}' must equal id '{method.id}' (mismatch)"
            )
            continue

        # Companion .md must exist.
        md = path.with_suffix(".md")
        if not md.exists():
            errors.append(f"{path}: missing companion {md.name}")
            continue

        # Duplicate id.
        if method.id in seen_ids:
            errors.append(
                f"{path}: duplicate id '{method.id}' "
                f"(also defined in {seen_ids[method.id]})"
            )
            continue
        seen_ids[method.id] = path

    if errors:
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        print(f"\n{len(errors)} validation error(s)", file=sys.stderr)
        return 1

    print(f"All {len(files)} method(s) valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests, expect pass**

Run: `pytest tests/test_validate_methods.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```
git add scripts/validate_methods.py tests/test_validate_methods.py
git commit -m "feat(scripts): add validate_methods.py with id/filename + companion checks"
```

---

### Task 10: PR-method-validate workflow

**Files:**
- Create: `.github/workflows/pr-method-validate.yml`

- [ ] **Step 1: Write workflow**

```yaml
name: pr-method-validate

on:
  pull_request:
    paths:
      - 'methods/**'
      - 'src/methodos/models.py'
      - 'schemas/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
      - run: pip install -e .
      - name: Validate methods
        run: python scripts/validate_methods.py
      - name: Schema drift
        run: |
          python scripts/regenerate_schema.py --out /tmp/schema_check.json
          diff -u schemas/method_schema.json /tmp/schema_check.json
```

- [ ] **Step 2: Commit**

```
git add .github/workflows/pr-method-validate.yml
git commit -m "ci: add fast PR validator for methods/** changes"
```

---

## Chunk 3: Provider abstraction

Goal: two `Protocol`s in `providers/base.py`, three concrete v1 implementations (`LiteLLMProvider`, `LocalEmbedding`, `OpenAIEmbedding`), `FakeLLM` and `FakeEmbedding` for tests, and factory functions in `providers/__init__.py`.

### Task 11: Provider Protocols + custom errors

**Files:**
- Create: `src/methodos/providers/__init__.py`
- Create: `src/methodos/providers/base.py`
- Create: `tests/test_providers.py`

- [ ] **Step 1: Failing test**

```python
from methodos.providers.base import (
    EmbeddingProvider, LLMProvider, LLMError, EmbeddingError,
)

def test_protocols_are_runtime_checkable():
    class MinimalLLM:
        name = "x"
        def complete(self, system, user, *, max_tokens=1024, temperature=0.2):
            return ""
    class MinimalEmbedding:
        name = "x"; dimensions = 4
        def embed(self, texts):
            return [[0.0, 0.0, 0.0, 0.0] for _ in texts]
    assert isinstance(MinimalLLM(), LLMProvider)
    assert isinstance(MinimalEmbedding(), EmbeddingProvider)

def test_errors_are_distinguishable():
    assert issubclass(LLMError, Exception)
    assert issubclass(EmbeddingError, Exception)
    assert not issubclass(LLMError, EmbeddingError)
```

- [ ] **Step 2: Run, expect failure**

Run: `pytest tests/test_providers.py -v`

- [ ] **Step 3: Implement `src/methodos/providers/base.py`**

```python
"""Provider Protocols — the only seam between application code and SDKs."""
from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable


class LLMError(Exception):
    """Raised by any LLMProvider on backend failure (rate limit, timeout, bad creds, etc.)."""


class EmbeddingError(Exception):
    """Raised by any EmbeddingProvider on backend failure."""


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Turn text into vectors. Implementations should be deterministic for same input."""

    name: str
    """Stable identifier, e.g. 'local:all-MiniLM-L6-v2' or 'openai:text-embedding-3-small'.

    Stored in the Chroma collection metadata; mismatch at query time refuses to
    serve stale results.
    """

    dimensions: int
    """Output vector dimensionality."""

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Return one vector per input text. Implementations should batch internally."""
        ...


@runtime_checkable
class LLMProvider(Protocol):
    """Generate a chat completion. May be non-deterministic; that's by design."""

    name: str
    """Stable identifier, e.g. 'anthropic/claude-3-5-haiku-20241022'."""

    def complete(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> str:
        """Return the assistant's reply. Raise LLMError on failure."""
        ...
```

- [ ] **Step 4: Implement initial `src/methodos/providers/__init__.py` (factories TBD in Task 16)**

```python
"""Provider factories and re-exports."""
from methodos.providers.base import (
    EmbeddingError,
    EmbeddingProvider,
    LLMError,
    LLMProvider,
)

__all__ = ["EmbeddingError", "EmbeddingProvider", "LLMError", "LLMProvider"]
```

- [ ] **Step 5: Run tests, expect pass**

Run: `pytest tests/test_providers.py -v`

- [ ] **Step 6: Commit**

```
git add src/methodos/providers/__init__.py src/methodos/providers/base.py tests/test_providers.py
git commit -m "feat(providers): add Protocols + LLMError/EmbeddingError"
```

---

### Task 12: Test fakes (`FakeLLM`, `FakeEmbedding`) in `conftest.py`

**Files:**
- Create: `tests/conftest.py`
- Modify: `tests/test_providers.py` (extend with conformance tests)

- [ ] **Step 1: Write `tests/conftest.py`**

```python
"""Shared test fixtures: deterministic provider fakes and tmp Chroma."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Sequence

import pytest


class FakeLLM:
    """Deterministic LLM fake. Records calls for assertions."""

    name = "fake-llm"

    def __init__(self, response: str = "stub explanation") -> None:
        self.response = response
        self.calls: list[tuple[str, str]] = []

    def complete(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> str:
        self.calls.append((system, user))
        return self.response


class FakeEmbedding:
    """Deterministic embedding fake.

    Vector = first `dimensions` bytes of sha256(text), normalized to [0, 1].
    Same text → same vector → same Chroma ranking. Used for exact-ordering
    assertions in search tests.
    """

    def __init__(self, dimensions: int = 4) -> None:
        self.name = f"fake-embedding-{dimensions}d"
        self.dimensions = dimensions

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for t in texts:
            h = hashlib.sha256(t.encode("utf-8")).digest()
            out.append([b / 255.0 for b in h[: self.dimensions]])
        return out


@pytest.fixture
def fake_llm() -> FakeLLM:
    return FakeLLM()


@pytest.fixture
def fake_embedding() -> FakeEmbedding:
    return FakeEmbedding(dimensions=8)


@pytest.fixture
def tmp_chroma_path(tmp_path: Path) -> Path:
    """A clean Chroma directory for each test."""
    p = tmp_path / "chroma"
    p.mkdir()
    return p
```

- [ ] **Step 2: Append conformance tests to `tests/test_providers.py`**

```python
def test_fake_llm_satisfies_protocol(fake_llm):
    assert isinstance(fake_llm, LLMProvider)

def test_fake_embedding_satisfies_protocol(fake_embedding):
    assert isinstance(fake_embedding, EmbeddingProvider)

def test_fake_embedding_is_deterministic(fake_embedding):
    a = fake_embedding.embed(["hello"])
    b = fake_embedding.embed(["hello"])
    assert a == b

def test_fake_llm_records_calls(fake_llm):
    fake_llm.complete("S", "U")
    fake_llm.complete("S2", "U2")
    assert fake_llm.calls == [("S", "U"), ("S2", "U2")]
```

- [ ] **Step 3: Run, expect pass**

Run: `pytest tests/test_providers.py -v`
Expected: all (existing 2 + new 4) pass.

- [ ] **Step 4: Commit**

```
git add tests/conftest.py tests/test_providers.py
git commit -m "test: add FakeLLM and FakeEmbedding fixtures"
```

---

### Task 13: `LiteLLMProvider`

**Files:**
- Create: `src/methodos/providers/llm_litellm.py`
- Modify: `tests/test_providers.py`

- [ ] **Step 1: Failing test (mocked, no network)**

```python
from unittest.mock import MagicMock, patch
from methodos.providers.llm_litellm import LiteLLMProvider
from methodos.providers.base import LLMError

def test_litellm_provider_satisfies_protocol():
    p = LiteLLMProvider(model="ollama/llama3.1:8b")
    from methodos.providers.base import LLMProvider
    assert isinstance(p, LLMProvider)
    assert p.name == "ollama/llama3.1:8b"

def test_litellm_provider_passes_messages_correctly():
    fake_response = MagicMock()
    fake_response.choices = [MagicMock(message=MagicMock(content="hi from litellm"))]
    with patch("methodos.providers.llm_litellm.litellm.completion", return_value=fake_response) as m:
        p = LiteLLMProvider(model="anthropic/claude-3-5-haiku-20241022")
        out = p.complete("you are helpful", "say hi", max_tokens=10, temperature=0.5)
    assert out == "hi from litellm"
    args, kwargs = m.call_args
    assert kwargs["model"] == "anthropic/claude-3-5-haiku-20241022"
    assert kwargs["messages"] == [
        {"role": "system", "content": "you are helpful"},
        {"role": "user", "content": "say hi"},
    ]
    assert kwargs["max_tokens"] == 10
    assert kwargs["temperature"] == 0.5

def test_litellm_provider_wraps_exceptions_into_llmerror():
    with patch("methodos.providers.llm_litellm.litellm.completion", side_effect=RuntimeError("boom")):
        p = LiteLLMProvider(model="ollama/llama3.1:8b")
        import pytest
        with pytest.raises(LLMError) as ei:
            p.complete("s", "u")
        assert "boom" in str(ei.value)
```

- [ ] **Step 2: Run, expect failure (ImportError)**

Run: `pytest tests/test_providers.py -v -k litellm`

- [ ] **Step 3: Implement `src/methodos/providers/llm_litellm.py`**

```python
"""litellm-backed LLMProvider — single class for all chat models."""
from __future__ import annotations

from methodos.providers.base import LLMError


class LiteLLMProvider:
    """Wraps litellm.completion behind the LLMProvider Protocol.

    Construction:
        LiteLLMProvider(model="anthropic/claude-3-5-haiku-20241022")
        LiteLLMProvider(model="ollama/llama3.1:8b")
        LiteLLMProvider(model="openai/gpt-4o-mini")

    API keys are read from environment by litellm itself
    (ANTHROPIC_API_KEY, OPENAI_API_KEY, etc.).
    """

    def __init__(self, model: str) -> None:
        self.name = model

    def complete(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> str:
        # Lazy import to keep CLI startup fast and litellm optional in fake-only tests.
        import litellm

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        try:
            resp = litellm.completion(
                model=self.name,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        except Exception as e:
            raise LLMError(f"{type(e).__name__}: {e}") from e

        try:
            content = resp.choices[0].message.content
        except (AttributeError, IndexError, KeyError) as e:
            raise LLMError(f"unexpected response shape: {e}") from e
        if content is None:
            raise LLMError("litellm returned empty content")
        return str(content)
```

- [ ] **Step 4: Run tests, expect pass**

Run: `pytest tests/test_providers.py -v -k litellm`

- [ ] **Step 5: Commit**

```
git add src/methodos/providers/llm_litellm.py tests/test_providers.py
git commit -m "feat(providers): add LiteLLMProvider with LLMError wrapping"
```

---

### Task 14: `LocalEmbedding` (sentence-transformers)

**Files:**
- Create: `src/methodos/providers/embedding_local.py`
- Modify: `tests/test_providers.py`

- [ ] **Step 1: Failing test (mocks the model load — no real model file needed in CI)**

```python
from unittest.mock import MagicMock, patch
from methodos.providers.embedding_local import LocalEmbedding
from methodos.providers.base import EmbeddingProvider, EmbeddingError

def test_local_embedding_lazy_loads_model():
    """Import of sentence_transformers must NOT happen at construction."""
    p = LocalEmbedding(model_name="all-MiniLM-L6-v2")
    assert p.name == "local:all-MiniLM-L6-v2"
    # before .embed() is called, _model is None
    assert getattr(p, "_model", None) is None

def test_local_embedding_calls_underlying_model():
    fake = MagicMock()
    fake.get_sentence_embedding_dimension.return_value = 384
    fake.encode.return_value = [[0.1] * 384, [0.2] * 384]

    with patch("methodos.providers.embedding_local._load_st_model", return_value=fake) as ld:
        p = LocalEmbedding(model_name="all-MiniLM-L6-v2")
        out = p.embed(["a", "b"])

    assert out == [[0.1] * 384, [0.2] * 384]
    assert p.dimensions == 384
    ld.assert_called_once_with("all-MiniLM-L6-v2")

def test_local_embedding_satisfies_protocol():
    assert isinstance(LocalEmbedding(model_name="x"), EmbeddingProvider)

def test_local_embedding_wraps_errors():
    with patch("methodos.providers.embedding_local._load_st_model", side_effect=RuntimeError("model not found")):
        p = LocalEmbedding(model_name="bogus")
        import pytest
        with pytest.raises(EmbeddingError):
            p.embed(["x"])
```

- [ ] **Step 2: Run, expect failure**

Run: `pytest tests/test_providers.py -v -k local_embedding`

- [ ] **Step 3: Implement `src/methodos/providers/embedding_local.py`**

```python
"""Local embeddings via sentence-transformers (CPU-friendly, offline)."""
from __future__ import annotations

from typing import Sequence

from methodos.providers.base import EmbeddingError


def _load_st_model(model_name: str):
    """Indirection so tests can patch this single function."""
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(model_name)


class LocalEmbedding:
    """Lazy-loaded sentence-transformers model.

    The model file (~80MB for all-MiniLM-L6-v2) downloads on first use into
    HuggingFace's standard cache (~/.cache/huggingface/). After that, fully
    offline.

    The `_model` attribute starts as None; populated on first `embed()` call.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.name = f"local:{model_name}"
        self._model_name = model_name
        self._model = None  # lazy
        self._dimensions: int | None = None

    @property
    def dimensions(self) -> int:
        if self._dimensions is None:
            # Force-load to learn dimensionality.
            self._ensure_loaded()
        assert self._dimensions is not None
        return self._dimensions

    def _ensure_loaded(self) -> None:
        if self._model is None:
            try:
                self._model = _load_st_model(self._model_name)
            except Exception as e:
                raise EmbeddingError(f"failed to load {self._model_name}: {e}") from e
            self._dimensions = self._model.get_sentence_embedding_dimension()

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        self._ensure_loaded()
        try:
            vecs = self._model.encode(list(texts), normalize_embeddings=True)
        except Exception as e:
            raise EmbeddingError(f"encode failed: {e}") from e
        # sentence-transformers returns numpy array OR list-of-lists; normalize.
        return [list(map(float, v)) for v in vecs]
```

- [ ] **Step 4: Run tests, expect pass**

Run: `pytest tests/test_providers.py -v -k local_embedding`

- [ ] **Step 5: Commit**

```
git add src/methodos/providers/embedding_local.py tests/test_providers.py
git commit -m "feat(providers): add LocalEmbedding (sentence-transformers, lazy-loaded)"
```

---

### Task 15: `OpenAIEmbedding`

**Files:**
- Create: `src/methodos/providers/embedding_openai.py`
- Modify: `tests/test_providers.py`

- [ ] **Step 1: Failing test**

```python
from unittest.mock import MagicMock, patch
from methodos.providers.embedding_openai import OpenAIEmbedding
from methodos.providers.base import EmbeddingProvider, EmbeddingError

def test_openai_embedding_satisfies_protocol():
    assert isinstance(OpenAIEmbedding(model_name="text-embedding-3-small"), EmbeddingProvider)
    p = OpenAIEmbedding(model_name="text-embedding-3-small")
    assert p.name == "openai:text-embedding-3-small"
    assert p.dimensions == 1536

def test_openai_embedding_uses_client():
    fake_client = MagicMock()
    fake_client.embeddings.create.return_value = MagicMock(
        data=[MagicMock(embedding=[0.1] * 1536), MagicMock(embedding=[0.2] * 1536)]
    )
    with patch("methodos.providers.embedding_openai._client", return_value=fake_client) as gc:
        p = OpenAIEmbedding(model_name="text-embedding-3-small")
        out = p.embed(["a", "b"])
    assert out == [[0.1] * 1536, [0.2] * 1536]
    fake_client.embeddings.create.assert_called_once_with(
        model="text-embedding-3-small", input=["a", "b"]
    )

def test_openai_embedding_wraps_errors():
    fake_client = MagicMock()
    fake_client.embeddings.create.side_effect = RuntimeError("rate limit")
    with patch("methodos.providers.embedding_openai._client", return_value=fake_client):
        p = OpenAIEmbedding(model_name="text-embedding-3-small")
        import pytest
        with pytest.raises(EmbeddingError):
            p.embed(["a"])
```

- [ ] **Step 2: Run, expect failure**

Run: `pytest tests/test_providers.py -v -k openai_embedding`

- [ ] **Step 3: Implement `src/methodos/providers/embedding_openai.py`**

```python
"""OpenAI embeddings — opt-in cloud alternative to LocalEmbedding."""
from __future__ import annotations

from typing import Sequence

from methodos.providers.base import EmbeddingError

# Hard-coded dimensionality for known models — saves a network round-trip on init.
_KNOWN_DIMS: dict[str, int] = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
}


def _client():
    """Lazy-construct the OpenAI client (reads OPENAI_API_KEY from env)."""
    from openai import OpenAI
    return OpenAI()


class OpenAIEmbedding:
    def __init__(self, model_name: str = "text-embedding-3-small") -> None:
        self.name = f"openai:{model_name}"
        self._model_name = model_name
        if model_name not in _KNOWN_DIMS:
            raise ValueError(
                f"Unknown OpenAI embedding model: {model_name}. "
                f"Add its dimension to _KNOWN_DIMS in embedding_openai.py."
            )
        self.dimensions = _KNOWN_DIMS[model_name]

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        try:
            client = _client()
            resp = client.embeddings.create(model=self._model_name, input=list(texts))
        except Exception as e:
            raise EmbeddingError(f"{type(e).__name__}: {e}") from e
        return [list(item.embedding) for item in resp.data]
```

- [ ] **Step 4: Run tests, expect pass**

Run: `pytest tests/test_providers.py -v -k openai_embedding`

- [ ] **Step 5: Commit**

```
git add src/methodos/providers/embedding_openai.py tests/test_providers.py
git commit -m "feat(providers): add OpenAIEmbedding with known-model dimension table"
```

---

### Task 16: Provider factories in `providers/__init__.py`

**Files:**
- Modify: `src/methodos/providers/__init__.py`
- Modify: `tests/test_providers.py`

- [ ] **Step 1: Failing test**

```python
from methodos.config import Settings
from methodos.providers import make_llm, make_embedding
from methodos.providers.llm_litellm import LiteLLMProvider
from methodos.providers.embedding_local import LocalEmbedding

def test_make_llm_returns_litellm_provider(monkeypatch):
    monkeypatch.setenv("METHODOS_MODEL", "ollama/llama3.1:8b")
    s = Settings(_env_file=None)
    llm = make_llm(s)
    assert isinstance(llm, LiteLLMProvider)
    assert llm.name == "ollama/llama3.1:8b"

def test_make_embedding_local_default(monkeypatch):
    for k in ("METHODOS_EMBEDDING_PROVIDER", "METHODOS_EMBEDDING_MODEL"):
        monkeypatch.delenv(k, raising=False)
    s = Settings(_env_file=None)
    e = make_embedding(s)
    assert isinstance(e, LocalEmbedding)
    assert e.name.startswith("local:")

def test_make_embedding_openai(monkeypatch):
    monkeypatch.setenv("METHODOS_EMBEDDING_PROVIDER", "openai")
    monkeypatch.setenv("METHODOS_EMBEDDING_MODEL", "text-embedding-3-small")
    s = Settings(_env_file=None)
    from methodos.providers.embedding_openai import OpenAIEmbedding
    e = make_embedding(s)
    assert isinstance(e, OpenAIEmbedding)
```

- [ ] **Step 2: Run, expect failure**

Run: `pytest tests/test_providers.py -v -k make_`

- [ ] **Step 3: Update `src/methodos/providers/__init__.py`**

```python
"""Provider factories and re-exports."""
from __future__ import annotations

from methodos.config import Settings
from methodos.providers.base import (
    EmbeddingError,
    EmbeddingProvider,
    LLMError,
    LLMProvider,
)


def make_llm(settings: Settings) -> LLMProvider:
    """Construct an LLM provider from settings.

    Currently the only backend is litellm (which itself dispatches to ~100 providers
    via the model string). Replacing this with a hand-rolled SDK wrapper for a
    specific provider is a one-function change.
    """
    from methodos.providers.llm_litellm import LiteLLMProvider
    return LiteLLMProvider(model=settings.model)


def make_embedding(settings: Settings) -> EmbeddingProvider:
    """Construct an embedding provider per settings.embedding_provider."""
    if settings.embedding_provider == "local":
        from methodos.providers.embedding_local import LocalEmbedding
        return LocalEmbedding(model_name=settings.embedding_model)
    if settings.embedding_provider == "openai":
        from methodos.providers.embedding_openai import OpenAIEmbedding
        return OpenAIEmbedding(model_name=settings.embedding_model)
    raise ValueError(f"unknown embedding_provider: {settings.embedding_provider}")


__all__ = [
    "EmbeddingError",
    "EmbeddingProvider",
    "LLMError",
    "LLMProvider",
    "make_embedding",
    "make_llm",
]
```

- [ ] **Step 4: Run tests, expect pass**

Run: `pytest tests/test_providers.py -v`

- [ ] **Step 5: Commit**

```
git add src/methodos/providers/__init__.py tests/test_providers.py
git commit -m "feat(providers): add make_llm/make_embedding factories"
```

---

## Chunk 4: Ingest pipeline

Goal: a working `ingest` that loads `methods/*.json`, validates, embeds, and upserts into Chroma. Always-rebuild semantics. Math-comment block included verbatim per the spec.

### Task 17: `ingest.py` end-to-end

**Files:**
- Create: `src/methodos/ingest.py`
- Create: `tests/test_ingest.py`

- [ ] **Step 1: Failing test**

```python
import json
from pathlib import Path
import pytest

from methodos.ingest import ingest, IngestError
from tests.conftest import FakeEmbedding


def _write_method(dir: Path, id: str, *, use_case_suffix: str = "") -> None:
    payload = {
        "id": id,
        "name": id.replace("_", " "),
        "category": "strategy",
        "use_case": ("a useful method for problems involving " + id + " " + use_case_suffix).ljust(60, "."),
        "strengths": ["s"], "weaknesses": ["w"],
        "complexity_score": 2,
        "estimated_duration": {"min_minutes": 30, "max_minutes": 60},
    }
    (dir / f"{id}.json").write_text(json.dumps(payload))
    (dir / f"{id}.md").write_text(f"# {id}\n")


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

    # Re-ingest is idempotent (always-rebuild — collection wiped + recreated).
    summary2 = ingest(
        methods_dir=methods,
        chroma_path=chroma_path,
        embedding=fake_embedding,
    )
    assert summary2.count == 2


def test_ingest_aborts_on_validation_errors(tmp_path, fake_embedding):
    methods = tmp_path / "methods"
    methods.mkdir()
    (methods / "Bad.json").write_text(json.dumps({"id": "Bad"}))  # missing fields
    (methods / "Bad.md").write_text("# bad")
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
        "strengths": ["s"], "weaknesses": ["w"],
        "complexity_score": 1,
        "estimated_duration": {"min_minutes": 5, "max_minutes": 10},
    }
    (methods / "Wrong.json").write_text(json.dumps(payload))
    (methods / "Wrong.md").write_text("# wrong")
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
```

- [ ] **Step 2: Run, expect failure (ImportError)**

Run: `pytest tests/test_ingest.py -v`

- [ ] **Step 3: Implement `src/methodos/ingest.py`**

```python
"""Ingest /methods/*.json into a ChromaDB collection.

Always-rebuild semantics: the existing 'methods' collection is dropped and
recreated on every run. The collection is a derived artifact — like a build
output — and treating it as cache simplifies the invariant that the index is a
pure function of the JSON files on disk.

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
# sentence-transformers (with normalize_embeddings=True) and OpenAI embedding
# models produce normalized vectors by default, so this assumption holds.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from methodos.models import Method
from methodos.providers.base import EmbeddingProvider


class IngestError(Exception):
    """Raised when ingest cannot complete (validation, IO, etc.)."""


@dataclass(frozen=True)
class IngestSummary:
    count: int
    ids: list[str]
    provider_name: str
    dimensions: int


def _flatten_metadata(method: Method) -> dict:
    return {
        "name": method.name,
        "category": method.category.value,
        "complexity_score": method.complexity_score,
        "duration_min": method.estimated_duration.min_minutes,
        "duration_max": method.estimated_duration.max_minutes,
        "strengths_json": json.dumps(method.strengths),
        "weaknesses_json": json.dumps(method.weaknesses),
        "references_json": json.dumps(method.references),
        "doc_path": method.doc_path,
    }


def _load_and_validate(methods_dir: Path) -> list[Method]:
    """Parse all JSON files, validate, return Method list. Raises IngestError on failure."""
    if not methods_dir.is_dir():
        raise IngestError(f"{methods_dir} is not a directory")

    files = sorted(methods_dir.glob("*.json"))
    if not files:
        return []

    methods: list[Method] = []
    errors: list[str] = []
    seen: dict[str, Path] = {}

    for path in files:
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError as e:
            errors.append(f"{path}: invalid JSON: {e}")
            continue
        try:
            method = Method.model_validate(data)
        except ValidationError as e:
            errors.append(f"{path}: {e}")
            continue
        if path.stem != method.id:
            errors.append(f"{path}: filename stem '{path.stem}' must equal id '{method.id}'")
            continue
        if not path.with_suffix(".md").exists():
            errors.append(f"{path}: missing companion {path.stem}.md")
            continue
        if method.id in seen:
            errors.append(f"{path}: duplicate id '{method.id}' (also in {seen[method.id]})")
            continue
        seen[method.id] = path
        methods.append(method)

    if errors:
        raise IngestError("\n".join(errors))
    return methods


def ingest(
    *,
    methods_dir: Path,
    chroma_path: Path,
    embedding: EmbeddingProvider,
) -> IngestSummary:
    """Rebuild the 'methods' Chroma collection from /methods/*.json.

    Drops any existing collection. Returns a summary of what was ingested.
    Raises IngestError on validation failure (collection is left untouched).
    """
    methods = _load_and_validate(methods_dir)
    if not methods:
        return IngestSummary(count=0, ids=[], provider_name=embedding.name, dimensions=embedding.dimensions)

    # Lazy import — keeps test startup fast and chromadb optional in some unit tests.
    import chromadb

    chroma_path.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(chroma_path))

    # Always-rebuild: drop existing if present.
    try:
        client.delete_collection("methods")
    except Exception:
        pass  # didn't exist — fine.

    collection = client.create_collection(
        name="methods",
        metadata={
            "embedding_provider_name": embedding.name,
            "embedding_dimensions": embedding.dimensions,
            "schema_version": 1,
        },
    )

    use_cases = [m.use_case for m in methods]
    vectors = embedding.embed(use_cases)
    if any(len(v) != embedding.dimensions for v in vectors):
        raise IngestError(
            f"embedding provider returned wrong dimensionality "
            f"(expected {embedding.dimensions})"
        )

    collection.upsert(
        ids=[m.id for m in methods],
        embeddings=vectors,
        documents=use_cases,
        metadatas=[_flatten_metadata(m) for m in methods],
    )

    return IngestSummary(
        count=len(methods),
        ids=[m.id for m in methods],
        provider_name=embedding.name,
        dimensions=embedding.dimensions,
    )
```

- [ ] **Step 4: Run tests, expect pass**

Run: `pytest tests/test_ingest.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```
git add src/methodos/ingest.py tests/test_ingest.py
git commit -m "feat(ingest): implement always-rebuild ingest with math comment block"
```

---

## Chunk 5: Search & prompt template

Goal: `retrieve()` over Chroma + `explain()` via LLM. Both gated behind a single `search()` entry point. Prompt template lives in `src/methodos/prompts/explain.txt`.

### Task 18: Prompt template + loader

**Files:**
- Create: `src/methodos/prompts/__init__.py` (empty)
- Create: `src/methodos/prompts/explain.txt`
- Create: `src/methodos/prompts/loader.py`
- Create: `tests/test_prompts.py`

- [ ] **Step 1: Failing test**

```python
from methodos.prompts.loader import load_prompt, render_explain_prompt

def test_load_prompt_returns_text():
    text = load_prompt("explain")
    assert "SYSTEM:" in text and "USER:" in text

def test_render_explain_prompt_substitutes_query():
    rendered = render_explain_prompt(
        query="enter a new market",
        candidates=[{
            "name": "SWOT", "similarity": 0.87,
            "complexity_score": 2,
            "use_case": "evaluate strengths and weaknesses",
            "strengths": ["a", "b"], "weaknesses": ["c"],
            "duration_min": 60, "duration_max": 180,
        }],
    )
    assert "enter a new market" in rendered
    assert "SWOT" in rendered
    assert "0.87" in rendered
    assert "60" in rendered and "180" in rendered

def test_split_into_system_and_user_sections():
    from methodos.prompts.loader import split_system_user
    rendered = render_explain_prompt(
        query="x", candidates=[{
            "name": "Y", "similarity": 0.5, "complexity_score": 1,
            "use_case": "z", "strengths": ["a"], "weaknesses": ["b"],
            "duration_min": 5, "duration_max": 10,
        }],
    )
    sys_part, user_part = split_system_user(rendered)
    assert "expert management consultant" in sys_part.lower()
    assert "x" in user_part
```

- [ ] **Step 2: Run, expect failure**

- [ ] **Step 3: Write `src/methodos/prompts/explain.txt`**

```
SYSTEM:
You are an expert management consultant helping a user select the right method
for their problem. You have a curated catalog of methods. Given the user's
problem and a list of candidate methods (with descriptions, strengths,
weaknesses, complexity, and duration), explain in 2-4 short paragraphs why
each candidate fits or doesn't fit, and give a final recommendation. Be
specific to the user's problem, not generic. If a method is a poor fit despite
high similarity, say so plainly.

USER:
Problem:
"""
{query}
"""

Candidate methods (ranked by semantic similarity):

{candidates_block}

Now: explain fit, contrast methods, recommend.
```

- [ ] **Step 4: Implement `src/methodos/prompts/loader.py`**

```python
"""Load and render prompt templates."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

PROMPTS_DIR = Path(__file__).parent


def load_prompt(name: str) -> str:
    """Load a prompt template by name (without extension) from prompts/."""
    return (PROMPTS_DIR / f"{name}.txt").read_text(encoding="utf-8")


def split_system_user(text: str) -> tuple[str, str]:
    """Split a rendered prompt into (system_part, user_part) at the SYSTEM:/USER: markers."""
    sys_marker = "SYSTEM:"
    user_marker = "USER:"
    if sys_marker not in text or user_marker not in text:
        raise ValueError("template must contain both SYSTEM: and USER: markers")
    sys_idx = text.index(sys_marker) + len(sys_marker)
    user_idx = text.index(user_marker)
    system_part = text[sys_idx:user_idx].strip()
    user_part = text[user_idx + len(user_marker):].strip()
    return system_part, user_part


def _format_candidate(c: dict[str, Any]) -> str:
    strengths_b = "\n".join(f"  - {s}" for s in c["strengths"])
    weaknesses_b = "\n".join(f"  - {w}" for w in c["weaknesses"])
    return (
        f"### {c['name']}  (similarity: {c['similarity']:.2f}, "
        f"complexity: {c['complexity_score']}/5)\n"
        f"Use case: {c['use_case']}\n"
        f"Strengths:\n{strengths_b}\n"
        f"Weaknesses:\n{weaknesses_b}\n"
        f"Duration: {c['duration_min']}–{c['duration_max']} minutes\n"
        f"---"
    )


def render_explain_prompt(*, query: str, candidates: Sequence[dict[str, Any]]) -> str:
    """Render the explain template with query + candidate list."""
    template = load_prompt("explain")
    candidates_block = "\n".join(_format_candidate(c) for c in candidates)
    return template.format(query=query, candidates_block=candidates_block)
```

- [ ] **Step 5: Run tests, expect pass**

- [ ] **Step 6: Commit**

```
git add src/methodos/prompts/__init__.py src/methodos/prompts/explain.txt src/methodos/prompts/loader.py tests/test_prompts.py
git commit -m "feat(prompts): add explain template + render/split helpers"
```

---

### Task 19: `search.py` (retrieve + explain)

**Files:**
- Create: `src/methodos/search.py`
- Create: `tests/test_search.py`

- [ ] **Step 1: Failing test**

```python
import json
from pathlib import Path
import pytest

from methodos.ingest import ingest
from methodos.search import retrieve, search, StaleIndexError, SearchResult


def _write(dir: Path, id: str, use_case: str) -> None:
    payload = {
        "id": id, "name": id, "category": "strategy",
        "use_case": use_case,
        "strengths": ["s"], "weaknesses": ["w"],
        "complexity_score": 2,
        "estimated_duration": {"min_minutes": 30, "max_minutes": 60},
    }
    (dir / f"{id}.json").write_text(json.dumps(payload))
    (dir / f"{id}.md").write_text(f"# {id}\n")


def _seed(tmp_path: Path, embedding) -> Path:
    methods = tmp_path / "methods"
    methods.mkdir()
    _write(methods, "Alpha", "alpha alpha alpha alpha alpha alpha alpha alpha alpha")
    _write(methods, "Beta",  "beta beta beta beta beta beta beta beta beta beta beta")
    _write(methods, "Gamma", "gamma gamma gamma gamma gamma gamma gamma gamma gamma")
    chroma_path = tmp_path / "chroma"
    ingest(methods_dir=methods, chroma_path=chroma_path, embedding=embedding)
    return chroma_path


def test_retrieve_returns_top_k_sorted_by_similarity(tmp_path, fake_embedding):
    chroma_path = _seed(tmp_path, fake_embedding)
    # The query "alpha alpha alpha" produces a vector closest to the Alpha use_case
    # (because FakeEmbedding is deterministic and similar text → similar bytes).
    results = retrieve(
        query="alpha alpha alpha alpha alpha alpha alpha alpha",
        embedding=fake_embedding,
        chroma_path=chroma_path,
        top_k=3,
    )
    assert len(results) == 3
    # similarities are in [0, 2]; sorted descending
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
    # The LLM was called once with system + user
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
```

- [ ] **Step 2: Run, expect failure**

- [ ] **Step 3: Implement `src/methodos/search.py`**

```python
"""Retrieval + LLM explanation. See ingest.py for the similarity-math comment block."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from methodos.prompts.loader import render_explain_prompt, split_system_user
from methodos.providers.base import EmbeddingProvider, LLMProvider


class StaleIndexError(Exception):
    """The Chroma collection's embedding provider doesn't match the current one."""


@dataclass(frozen=True)
class Candidate:
    id: str
    name: str
    category: str
    complexity_score: int
    use_case: str
    strengths: list[str]
    weaknesses: list[str]
    duration_min: int
    duration_max: int
    doc_path: str
    similarity: float

    def to_render_dict(self) -> dict:
        return {
            "name": self.name,
            "similarity": self.similarity,
            "complexity_score": self.complexity_score,
            "use_case": self.use_case,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "duration_min": self.duration_min,
            "duration_max": self.duration_max,
        }


@dataclass(frozen=True)
class SearchResult:
    candidates: list[Candidate]
    explanation: Optional[str]   # None if --no-llm


def _rehydrate(chroma_id: str, document: str, metadata: dict, distance: float) -> Candidate:
    """Reconstruct a Candidate from Chroma's flat metadata."""
    # Cosine distance → similarity. See ingest.py "Similarity scoring math" block.
    similarity = 1.0 - distance
    return Candidate(
        id=chroma_id,
        name=metadata["name"],
        category=metadata["category"],
        complexity_score=int(metadata["complexity_score"]),
        use_case=document,
        strengths=json.loads(metadata["strengths_json"]),
        weaknesses=json.loads(metadata["weaknesses_json"]),
        duration_min=int(metadata["duration_min"]),
        duration_max=int(metadata["duration_max"]),
        doc_path=metadata["doc_path"],
        similarity=similarity,
    )


def _open_collection(chroma_path: Path, embedding: EmbeddingProvider):
    import chromadb

    if not chroma_path.exists():
        raise StaleIndexError(
            f"chroma path {chroma_path} does not exist — run `methodos ingest` first"
        )
    client = chromadb.PersistentClient(path=str(chroma_path))
    try:
        coll = client.get_collection("methods")
    except Exception as e:
        raise StaleIndexError(f"no 'methods' collection — run `methodos ingest`: {e}") from e

    persisted = coll.metadata.get("embedding_provider_name")
    if persisted != embedding.name:
        raise StaleIndexError(
            f"index was built with provider '{persisted}' but current is "
            f"'{embedding.name}' — run `methodos ingest` to rebuild"
        )
    return coll


def retrieve(
    *,
    query: str,
    embedding: EmbeddingProvider,
    chroma_path: Path,
    top_k: int,
) -> list[Candidate]:
    """Return up to top_k candidates sorted by similarity (descending)."""
    coll = _open_collection(chroma_path, embedding)
    q_vec = embedding.embed([query])[0]

    raw = coll.query(
        query_embeddings=[q_vec],
        n_results=top_k * 2,    # over-fetch — leaves room for a future re-ranker
        include=["metadatas", "documents", "distances"],
    )
    ids = raw["ids"][0]
    docs = raw["documents"][0]
    metas = raw["metadatas"][0]
    dists = raw["distances"][0]

    candidates = [
        _rehydrate(i, d, m, dist)
        for i, d, m, dist in zip(ids, docs, metas, dists)
    ]
    candidates.sort(key=lambda c: c.similarity, reverse=True)
    return candidates[:top_k]


def explain(
    *,
    query: str,
    candidates: list[Candidate],
    llm: LLMProvider,
) -> str:
    """Single LLM call, all candidates in one prompt for coherent comparison."""
    rendered = render_explain_prompt(
        query=query,
        candidates=[c.to_render_dict() for c in candidates],
    )
    system, user = split_system_user(rendered)
    return llm.complete(system, user)


def search(
    *,
    query: str,
    embedding: EmbeddingProvider,
    llm: Optional[LLMProvider],
    chroma_path: Path,
    top_k: int,
) -> SearchResult:
    """End-to-end: retrieve top_k, then optionally LLM-explain.

    Pass llm=None to skip the explanation step (--no-llm).
    """
    candidates = retrieve(
        query=query, embedding=embedding, chroma_path=chroma_path, top_k=top_k
    )
    if llm is None or not candidates:
        return SearchResult(candidates=candidates, explanation=None)
    explanation = explain(query=query, candidates=candidates, llm=llm)
    return SearchResult(candidates=candidates, explanation=explanation)
```

- [ ] **Step 4: Run tests, expect pass**

Run: `pytest tests/test_search.py -v`

- [ ] **Step 5: Commit**

```
git add src/methodos/search.py tests/test_search.py
git commit -m "feat(search): implement retrieve + explain + StaleIndexError"
```

---

## Chunk 6: CLI

Goal: `methodos` console script with subcommands `ingest`, `query`, `list`, `show`, `feedback`, `stats`, `--version`. Rich rendering for query results. TTY detection for the rate-hint footer.

### Task 20: CLI scaffold + `ingest` and `--version`

**Files:**
- Create: `src/methodos/cli.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Failing test**

```python
import json
from pathlib import Path
from typer.testing import CliRunner

runner = CliRunner()


def _seed_methods_fixture(repo_root: Path, dst: Path) -> None:
    """Copy real methods into a temp dir for CLI tests."""
    src = repo_root / "methods"
    dst.mkdir()
    for f in src.iterdir():
        (dst / f.name).write_bytes(f.read_bytes())


def test_version_command():
    from methodos.cli import app
    res = runner.invoke(app, ["--version"])
    assert res.exit_code == 0
    assert "methodos" in res.stdout.lower()


def test_ingest_command_runs(tmp_path, monkeypatch):
    from methodos.cli import app
    repo_root = Path(__file__).parent.parent
    methods = tmp_path / "methods"
    _seed_methods_fixture(repo_root, methods)

    # Force fake embedding via env: not possible since make_embedding picks LocalEmbedding.
    # Instead, point CLI at temp paths and rely on local-embedding being importable in dev install.
    # We'll patch make_embedding to return FakeEmbedding for this test.
    from tests.conftest import FakeEmbedding
    fake = FakeEmbedding(dimensions=8)

    monkeypatch.setenv("METHODOS_CHROMA_PATH", str(tmp_path / "chroma"))

    import methodos.cli as cli_mod
    monkeypatch.setattr(cli_mod, "make_embedding", lambda settings: fake)

    res = runner.invoke(app, ["ingest", "--methods-dir", str(methods)])
    assert res.exit_code == 0, res.stdout
    assert "ingested" in res.stdout.lower()
```

- [ ] **Step 2: Run, expect failure**

- [ ] **Step 3: Implement initial `src/methodos/cli.py`**

```python
"""Methodos CLI — Typer + Rich.

Subcommands:
    ingest                     Build the vector store from /methods
    query "<problem>"          Recommend methods (with LLM explanation)
    list                       Browse the catalog
    show ID                    Print a method's full Markdown
    feedback ID --rating N     Record outcome
    stats                      Aggregated ratings table
    --version                  Show version + active providers
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from methodos import __version__
from methodos.config import Settings
from methodos.providers import make_embedding, make_llm

app = typer.Typer(
    name="methodos",
    help="An expert-level RAG catalog of management methods.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()


def _version_callback(value: bool) -> None:
    if value:
        s = Settings(_env_file=None)
        console.print(
            f"methodos {__version__}\n"
            f"  model:     {s.model}\n"
            f"  embedding: {s.embedding_provider}:{s.embedding_model}\n"
            f"  chroma:    {s.chroma_path}"
        )
        raise typer.Exit()


@app.callback()
def main_callback(
    version: Optional[bool] = typer.Option(
        None, "--version", help="Show version + active providers", callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """Methodos AI: pick the right management method for your problem."""


@app.command()
def ingest(
    methods_dir: Path = typer.Option(
        Path("methods"), "--methods-dir", help="Directory of method JSON files"
    ),
) -> None:
    """Rebuild the local vector store from /methods/*.json."""
    from methodos.ingest import IngestError, ingest as do_ingest
    settings = Settings()
    try:
        embedding = make_embedding(settings)
    except Exception as e:
        console.print(f"[red]Failed to construct embedding provider:[/] {e}")
        raise typer.Exit(code=2)

    try:
        summary = do_ingest(
            methods_dir=methods_dir,
            chroma_path=settings.chroma_path,
            embedding=embedding,
        )
    except IngestError as e:
        console.print(f"[red]Ingest failed:[/]\n{e}")
        raise typer.Exit(code=1)

    if summary.count == 0:
        console.print("[yellow]No methods found — nothing ingested.[/]")
        return
    console.print(
        f"[green]Ingested {summary.count} method(s)[/] "
        f"(provider: {summary.provider_name}, {summary.dimensions}d)"
    )
```

- [ ] **Step 4: Run tests, expect pass**

- [ ] **Step 5: Commit**

```
git add src/methodos/cli.py tests/test_cli.py
git commit -m "feat(cli): scaffold Typer app with --version and ingest"
```

---

### Task 21: `query` command + Rich rendering + TTY hint

**Files:**
- Modify: `src/methodos/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Failing test**

```python
def test_query_no_llm_renders_results(tmp_path, monkeypatch):
    from methodos.cli import app
    repo_root = Path(__file__).parent.parent
    methods = tmp_path / "methods"
    _seed_methods_fixture(repo_root, methods)

    from tests.conftest import FakeEmbedding
    fake = FakeEmbedding(dimensions=8)
    import methodos.cli as cli_mod
    monkeypatch.setattr(cli_mod, "make_embedding", lambda s: fake)
    monkeypatch.setenv("METHODOS_CHROMA_PATH", str(tmp_path / "chroma"))

    runner.invoke(app, ["ingest", "--methods-dir", str(methods)])
    res = runner.invoke(app, ["query", "evaluate strengths and weaknesses", "--no-llm", "-k", "2"])
    assert res.exit_code == 0, res.stdout
    # We should see at least one method name in output.
    assert any(name in res.stdout for name in ("SWOT", "Porter", "DACI"))


def test_query_with_llm_calls_llm(tmp_path, monkeypatch):
    from methodos.cli import app
    repo_root = Path(__file__).parent.parent
    methods = tmp_path / "methods"
    _seed_methods_fixture(repo_root, methods)

    from tests.conftest import FakeEmbedding, FakeLLM
    fake_e = FakeEmbedding(dimensions=8)
    fake_l = FakeLLM(response="canned explanation")

    import methodos.cli as cli_mod
    monkeypatch.setattr(cli_mod, "make_embedding", lambda s: fake_e)
    monkeypatch.setattr(cli_mod, "make_llm", lambda s: fake_l)
    monkeypatch.setenv("METHODOS_CHROMA_PATH", str(tmp_path / "chroma"))

    runner.invoke(app, ["ingest", "--methods-dir", str(methods)])
    res = runner.invoke(app, ["query", "decision making for cross-functional teams", "-k", "2"])
    assert res.exit_code == 0, res.stdout
    assert "canned explanation" in res.stdout
```

- [ ] **Step 2: Run, expect failure**

- [ ] **Step 3: Add `query` command + rendering helpers to `src/methodos/cli.py`**

Append:
```python
from rich.markdown import Markdown
from rich.panel import Panel

def _complexity_dots(score: int) -> str:
    return "●" * score + "○" * (5 - score)


def _render_candidates(candidates) -> None:
    for i, c in enumerate(candidates, 1):
        header = f"#{i}  {c.name}  (sim {c.similarity:.2f})  complexity {_complexity_dots(c.complexity_score)}"
        body_lines = [
            f"[bold]Strengths:[/] " + " · ".join(c.strengths[:3]),
            f"[bold]Duration:[/] {c.duration_min}–{c.duration_max} min",
            f"[bold]Category:[/] {c.category}",
            f"→ [link=file://{c.doc_path}]{c.doc_path}[/link]",
        ]
        console.print(Panel("\n".join(body_lines), title=header, expand=False))


@app.command()
def query(
    text: str = typer.Argument(..., help="Natural-language problem statement"),
    top_k: int = typer.Option(None, "--top-k", "-k", help="Number of methods to recommend"),
    no_llm: bool = typer.Option(False, "--no-llm", help="Skip LLM explanation"),
    model: Optional[str] = typer.Option(None, "--model", help="Override LLM model string"),
) -> None:
    """Recommend methods for a problem."""
    from methodos.search import StaleIndexError, search

    settings = Settings()
    if model is not None:
        settings = settings.model_copy(update={"model": model})
    if top_k is None:
        top_k = settings.top_k

    embedding = make_embedding(settings)
    llm = None if no_llm else make_llm(settings)

    try:
        result = search(
            query=text,
            embedding=embedding,
            llm=llm,
            chroma_path=settings.chroma_path,
            top_k=top_k,
        )
    except StaleIndexError as e:
        console.print(f"[red]Stale index:[/] {e}")
        raise typer.Exit(code=1)

    if not result.candidates:
        console.print("[yellow]No matches.[/]")
        return

    _render_candidates(result.candidates)
    if result.explanation:
        console.print()
        console.print(Markdown(result.explanation))

    # TTY-only rate hint (set up in chunk 7 with actual feedback logging).
    if sys.stdout.isatty() and result.candidates:
        top = result.candidates[0]
        console.print(
            f"\n[dim]─────[/]\n[dim]Rate with: methodos feedback {top.id} -r 1..5[/]"
        )
```

- [ ] **Step 4: Run tests, expect pass**

- [ ] **Step 5: Commit**

```
git add src/methodos/cli.py tests/test_cli.py
git commit -m "feat(cli): add query command with Rich rendering and TTY hint"
```

---

### Task 22: `list` and `show` commands

**Files:**
- Modify: `src/methodos/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Failing test**

```python
def test_list_command_shows_all_methods(monkeypatch):
    from methodos.cli import app
    res = runner.invoke(app, ["list"])
    assert res.exit_code == 0
    assert "SWOT" in res.stdout
    assert "DACI" in res.stdout

def test_list_filters_by_category():
    from methodos.cli import app
    res = runner.invoke(app, ["list", "--category", "decision-making"])
    assert res.exit_code == 0
    assert "DACI" in res.stdout
    assert "SWOT" not in res.stdout

def test_show_renders_markdown():
    from methodos.cli import app
    res = runner.invoke(app, ["show", "SWOT"])
    assert res.exit_code == 0
    # SWOT.md contains the header "SWOT Analysis"
    assert "SWOT" in res.stdout

def test_show_unknown_id_errors():
    from methodos.cli import app
    res = runner.invoke(app, ["show", "Nonexistent"])
    assert res.exit_code == 1
    assert "Nonexistent" in res.stdout
```

- [ ] **Step 2: Run, expect failure**

- [ ] **Step 3: Add commands to `src/methodos/cli.py`**

Append:
```python
import json as _json
from rich.table import Table


def _load_all_methods(methods_dir: Path):
    from methodos.models import Method
    methods = []
    for f in sorted(methods_dir.glob("*.json")):
        methods.append(Method.model_validate(_json.loads(f.read_text())))
    return methods


@app.command("list")
def list_methods(
    category: Optional[str] = typer.Option(None, "--category", "-c"),
    max_complexity: Optional[int] = typer.Option(None, "--max-complexity"),
    methods_dir: Path = typer.Option(Path("methods"), "--methods-dir"),
) -> None:
    """Browse the catalog."""
    methods = _load_all_methods(methods_dir)
    if category:
        methods = [m for m in methods if m.category.value == category]
    if max_complexity is not None:
        methods = [m for m in methods if m.complexity_score <= max_complexity]

    if not methods:
        console.print("[yellow]No methods match.[/]")
        return

    table = Table(title="Methods")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Category", style="magenta")
    table.add_column("Complexity", justify="center")
    table.add_column("Duration (min)", justify="right")
    for m in methods:
        table.add_row(
            m.id, m.name, m.category.value, _complexity_dots(m.complexity_score),
            f"{m.estimated_duration.min_minutes}–{m.estimated_duration.max_minutes}",
        )
    console.print(table)


@app.command()
def show(
    id: str = typer.Argument(..., help="Method id (e.g. SWOT)"),
    methods_dir: Path = typer.Option(Path("methods"), "--methods-dir"),
) -> None:
    """Print a method's full Markdown documentation."""
    md = methods_dir / f"{id}.md"
    if not md.exists():
        console.print(f"[red]No method with id '{id}'[/]")
        raise typer.Exit(code=1)
    console.print(Markdown(md.read_text(encoding="utf-8")))
```

- [ ] **Step 4: Run tests, expect pass**

- [ ] **Step 5: Commit**

```
git add src/methodos/cli.py tests/test_cli.py
git commit -m "feat(cli): add list and show commands"
```

---

## Chunk 7: Feedback loop

Goal: `feedback.py` with append-only JSONL, `feedback` and `stats` CLI commands, ULID query_id minted in `cli.py`, TTY hint upgraded to include the actual `query_id`.

### Task 23: `feedback.py` core (events + log + read + stats)

**Files:**
- Create: `src/methodos/feedback.py`
- Create: `tests/test_feedback.py`

- [ ] **Step 1: Failing test**

```python
import json
from pathlib import Path
import pytest
from methodos.feedback import (
    log_recommendation, log_rating, read_events,
    stats, RatingEvent, RecommendationEvent,
)


def test_log_recommendation_returns_query_id_and_appends(tmp_path):
    fb = tmp_path / "fb.jsonl"
    qid = log_recommendation(
        query="enter new market",
        method_ids=["SWOT", "Porters_Five_Forces"],
        model="anthropic/claude-3-5-haiku-20241022",
        path=fb,
    )
    assert qid and len(qid) == 26  # ULID
    lines = fb.read_text().splitlines()
    assert len(lines) == 1
    obj = json.loads(lines[0])
    assert obj["event"] == "recommendation"
    assert obj["query_id"] == qid
    assert obj["method_ids"] == ["SWOT", "Porters_Five_Forces"]


def test_log_rating_appends(tmp_path):
    fb = tmp_path / "fb.jsonl"
    log_rating(method_id="SWOT", rating=4, note="worked well", query_id="01HX", path=fb)
    log_rating(method_id="DACI_Matrix", rating=5, note=None, query_id=None, path=fb)
    lines = fb.read_text().splitlines()
    assert len(lines) == 2
    a, b = json.loads(lines[0]), json.loads(lines[1])
    assert a["event"] == "rating" and a["rating"] == 4 and a["note"] == "worked well"
    assert b["event"] == "rating" and b["query_id"] is None


def test_log_rating_rejects_out_of_range(tmp_path):
    fb = tmp_path / "fb.jsonl"
    with pytest.raises(ValueError):
        log_rating(method_id="SWOT", rating=0, note=None, query_id=None, path=fb)
    with pytest.raises(ValueError):
        log_rating(method_id="SWOT", rating=6, note=None, query_id=None, path=fb)


def test_read_events_skips_corrupt_lines(tmp_path, capsys):
    fb = tmp_path / "fb.jsonl"
    log_rating(method_id="SWOT", rating=3, note=None, query_id=None, path=fb)
    fb.open("a", encoding="utf-8").write("this-is-not-json\n")
    log_rating(method_id="DACI_Matrix", rating=4, note=None, query_id=None, path=fb)

    events = list(read_events(fb))
    assert len(events) == 2
    assert all(isinstance(e, RatingEvent) for e in events)
    err = capsys.readouterr().err
    assert "skipped" in err.lower() or "corrupt" in err.lower() or "malformed" in err.lower()


def test_stats_aggregates(tmp_path):
    fb = tmp_path / "fb.jsonl"
    log_recommendation(query="q1", method_ids=["SWOT"], model="m", path=fb)
    log_rating(method_id="SWOT", rating=4, note=None, query_id=None, path=fb)
    log_rating(method_id="SWOT", rating=2, note=None, query_id=None, path=fb)
    log_rating(method_id="DACI_Matrix", rating=5, note=None, query_id=None, path=fb)
    s = stats(fb)
    assert s["SWOT"].rating_count == 2
    assert abs(s["SWOT"].avg_rating - 3.0) < 1e-9
    assert s["SWOT"].recommendation_count == 1
    assert s["DACI_Matrix"].rating_count == 1
```

- [ ] **Step 2: Run, expect failure**

- [ ] **Step 3: Implement `src/methodos/feedback.py`**

```python
"""Feedback loop placeholder — append-only JSONL of recommendations and ratings.

Designed to outgrow itself: when volume justifies it, a one-shot import script
turns this file into a SQLite database without changing the writer API. Until
then, JSONL gives us crash-safety, git-friendly diffs, and trivial concurrent
appends.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Literal, Optional, Union

from pydantic import BaseModel, Field
from ulid import ULID


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class RecommendationEvent(BaseModel):
    event: Literal["recommendation"] = "recommendation"
    timestamp: str
    query_id: str
    query: str
    method_ids: list[str]
    model: str


class RatingEvent(BaseModel):
    event: Literal["rating"] = "rating"
    timestamp: str
    query_id: Optional[str]
    method_id: str
    rating: int = Field(ge=1, le=5)
    note: Optional[str] = None


FeedbackEvent = Union[RecommendationEvent, RatingEvent]


def _append_line(path: Path, payload: BaseModel) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = payload.model_dump_json() + "\n"
    # POSIX flock is best-effort; skipped on platforms without fcntl.
    try:
        import fcntl
        with path.open("a", encoding="utf-8") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                f.write(line)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except ImportError:
        with path.open("a", encoding="utf-8") as f:
            f.write(line)


def log_recommendation(
    *, query: str, method_ids: list[str], model: str, path: Path,
) -> str:
    """Append a recommendation event. Returns the freshly-minted query_id (ULID)."""
    qid = str(ULID())
    ev = RecommendationEvent(
        timestamp=_now_iso(),
        query_id=qid,
        query=query,
        method_ids=method_ids,
        model=model,
    )
    _append_line(path, ev)
    return qid


def log_rating(
    *, method_id: str, rating: int, note: Optional[str],
    query_id: Optional[str], path: Path,
) -> None:
    """Append a rating event. Validates rating in [1, 5]."""
    if rating < 1 or rating > 5:
        raise ValueError(f"rating must be 1..5, got {rating}")
    ev = RatingEvent(
        timestamp=_now_iso(),
        query_id=query_id,
        method_id=method_id,
        rating=rating,
        note=note,
    )
    _append_line(path, ev)


def read_events(path: Path) -> Iterator[FeedbackEvent]:
    """Stream events. Lenient: skips malformed lines with a stderr warning."""
    if not path.exists():
        return
    skipped = 0
    with path.open(encoding="utf-8") as f:
        for lineno, raw in enumerate(f, 1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
                kind = obj.get("event")
                if kind == "recommendation":
                    yield RecommendationEvent.model_validate(obj)
                elif kind == "rating":
                    yield RatingEvent.model_validate(obj)
                else:
                    raise ValueError(f"unknown event type: {kind}")
            except Exception as e:
                skipped += 1
                print(f"feedback: skipped malformed line {lineno}: {e}", file=sys.stderr)
    if skipped:
        print(f"feedback: {skipped} line(s) skipped", file=sys.stderr)


@dataclass
class MethodStats:
    method_id: str
    recommendation_count: int = 0
    rating_count: int = 0
    rating_sum: int = 0

    @property
    def avg_rating(self) -> float:
        return self.rating_sum / self.rating_count if self.rating_count else 0.0


def stats(path: Path) -> dict[str, MethodStats]:
    out: dict[str, MethodStats] = defaultdict(lambda: MethodStats(method_id=""))
    for ev in read_events(path):
        if isinstance(ev, RecommendationEvent):
            for mid in ev.method_ids:
                s = out.setdefault(mid, MethodStats(method_id=mid))
                s.method_id = mid
                s.recommendation_count += 1
        elif isinstance(ev, RatingEvent):
            s = out.setdefault(ev.method_id, MethodStats(method_id=ev.method_id))
            s.method_id = ev.method_id
            s.rating_count += 1
            s.rating_sum += ev.rating
    return dict(out)
```

- [ ] **Step 4: Run tests, expect pass**

- [ ] **Step 5: Commit**

```
git add src/methodos/feedback.py tests/test_feedback.py
git commit -m "feat(feedback): add JSONL log + stats with lenient reader"
```

---

### Task 24: Wire feedback into CLI (`feedback`, `stats`, query_id mint)

**Files:**
- Modify: `src/methodos/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Failing test**

```python
def test_feedback_command_appends_rating(tmp_path, monkeypatch):
    from methodos.cli import app
    fb = tmp_path / "fb.jsonl"
    monkeypatch.setenv("METHODOS_FEEDBACK_PATH", str(fb))
    res = runner.invoke(app, ["feedback", "SWOT", "--rating", "4", "--note", "great"])
    assert res.exit_code == 0, res.stdout
    line = fb.read_text().splitlines()[0]
    obj = json.loads(line)
    assert obj["method_id"] == "SWOT"
    assert obj["rating"] == 4
    assert obj["note"] == "great"


def test_feedback_command_validates_rating_range(tmp_path, monkeypatch):
    from methodos.cli import app
    monkeypatch.setenv("METHODOS_FEEDBACK_PATH", str(tmp_path / "fb.jsonl"))
    res = runner.invoke(app, ["feedback", "SWOT", "--rating", "9"])
    assert res.exit_code != 0


def test_query_logs_recommendation_and_prints_query_id(tmp_path, monkeypatch):
    from methodos.cli import app
    repo_root = Path(__file__).parent.parent
    methods = tmp_path / "methods"
    _seed_methods_fixture(repo_root, methods)

    from tests.conftest import FakeEmbedding, FakeLLM
    fake_e = FakeEmbedding(dimensions=8)
    fake_l = FakeLLM(response="ok")
    import methodos.cli as cli_mod
    monkeypatch.setattr(cli_mod, "make_embedding", lambda s: fake_e)
    monkeypatch.setattr(cli_mod, "make_llm", lambda s: fake_l)

    fb = tmp_path / "fb.jsonl"
    monkeypatch.setenv("METHODOS_FEEDBACK_PATH", str(fb))
    monkeypatch.setenv("METHODOS_CHROMA_PATH", str(tmp_path / "chroma"))
    runner.invoke(app, ["ingest", "--methods-dir", str(methods)])
    res = runner.invoke(app, ["query", "decision making for cross-functional teams", "-k", "2"])
    assert res.exit_code == 0
    # one recommendation event written
    lines = fb.read_text().splitlines()
    rec_lines = [l for l in lines if '"event": "recommendation"' in l or '"event":"recommendation"' in l]
    assert len(rec_lines) == 1


def test_stats_command_prints_table(tmp_path, monkeypatch):
    from methodos.cli import app
    fb = tmp_path / "fb.jsonl"
    monkeypatch.setenv("METHODOS_FEEDBACK_PATH", str(fb))
    runner.invoke(app, ["feedback", "SWOT", "--rating", "4"])
    runner.invoke(app, ["feedback", "SWOT", "--rating", "5"])
    res = runner.invoke(app, ["stats"])
    assert res.exit_code == 0
    assert "SWOT" in res.stdout
```

- [ ] **Step 2: Run, expect failure**

- [ ] **Step 3: Add `feedback` and `stats` commands; mint query_id in `query`**

Modify `cli.py`:

1. In the `query` command, after `_render_candidates(...)`, before the LLM rendering and TTY hint:

```python
from methodos.feedback import log_recommendation
qid = log_recommendation(
    query=text,
    method_ids=[c.id for c in result.candidates],
    model=settings.model,
    path=settings.feedback_path,
)
```

And update the TTY hint to use `qid`:
```python
if sys.stdout.isatty() and result.candidates:
    top = result.candidates[0]
    console.print(
        f"\n[dim]─────[/]\n"
        f"[dim]Logged as {qid} · rate with: methodos feedback {top.id} -r 4[/]"
    )
```

2. Append the two new commands:

```python
@app.command()
def feedback(
    method_id: str = typer.Argument(..., help="Method id (e.g. SWOT)"),
    rating: int = typer.Option(..., "--rating", "-r", min=1, max=5),
    note: Optional[str] = typer.Option(None, "--note", "-n"),
    query_id: Optional[str] = typer.Option(None, "--query-id", "-q"),
) -> None:
    """Record an outcome rating for a previously-recommended method."""
    from methodos.feedback import log_rating
    settings = Settings()
    log_rating(
        method_id=method_id,
        rating=rating,
        note=note,
        query_id=query_id,
        path=settings.feedback_path,
    )
    console.print(f"[green]Recorded:[/] {method_id} rated {rating}/5")


@app.command()
def stats_cmd() -> None:  # exposed as `methodos stats`
    """Show aggregated method ratings."""
    from methodos.feedback import stats
    settings = Settings()
    s = stats(settings.feedback_path)
    if not s:
        console.print("[yellow]No feedback yet.[/]")
        return
    table = Table(title="Method ratings")
    table.add_column("Method", style="cyan")
    table.add_column("Recommended", justify="right")
    table.add_column("Rated", justify="right")
    table.add_column("Avg rating", justify="right")
    for mid, stat in sorted(s.items()):
        table.add_row(
            mid, str(stat.recommendation_count), str(stat.rating_count),
            f"{stat.avg_rating:.2f}" if stat.rating_count else "—",
        )
    console.print(table)


# Bind the function to the typer name `stats`
app.command("stats")(stats_cmd.callback if hasattr(stats_cmd, "callback") else stats_cmd)
```

(If the `stats_cmd` rebind line fails Typer-internal sanity checks, drop it and rename the function to `stats` directly with `@app.command("stats")` — pick whichever lints clean.)

- [ ] **Step 4: Run tests, expect pass**

- [ ] **Step 5: Commit**

```
git add src/methodos/cli.py tests/test_cli.py
git commit -m "feat(cli): add feedback + stats commands; mint query_id in query"
```

---

## Chunk 8: Documentation

Goal: a real README, the CLAUDE.md from the spec, CONTRIBUTING.md, and a LICENSE. Demo command works end-to-end.

### Task 25: README.md

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write `README.md`** (concise; use spec section 1 + quickstart)

```markdown
# Methodos AI

An open-source GitHub-based catalog of management methods (SWOT, Porter's Five
Forces, DACI, …) with a CLI RAG tool that recommends the right method for a
problem stated in natural language.

## What's in the box

- **`methods/`** — JSON + Markdown for every method. Adding a method is a PR
  with two files; no Python required.
- **`schemas/method_schema.json`** — generated from a Pydantic model; CI
  enforces freshness.
- **`methodos` CLI** — `query`, `list`, `show`, `feedback`, `stats`.
- **Provider-neutral** — Anthropic, OpenAI, Google, Mistral, Ollama, etc., via
  one `LLMProvider` Protocol (litellm-backed).

## Quickstart

```bash
# 1. Install
git clone https://github.com/Malkreide/methodos-ai
cd methodos-ai
python -m venv .venv && source .venv/bin/activate   # or .venv\Scripts\activate
pip install -e ".[dev,local]"

# 2. (Optional) pick a cloud LLM, e.g. Anthropic Haiku
echo 'METHODOS_MODEL=anthropic/claude-3-5-haiku-20241022' > .env
echo 'ANTHROPIC_API_KEY=sk-ant-...' >> .env

# 3. Build the index
methodos ingest

# 4. Ask
methodos query "we need to enter a new market without burning cash"
```

The default config is **fully offline**: Ollama for the LLM (`ollama/llama3.1:8b`)
and `sentence-transformers/all-MiniLM-L6-v2` for embeddings. One env var
(`METHODOS_MODEL`) swaps the LLM to any cloud provider supported by litellm.

## Recommended cloud LLM

We recommend Anthropic's Haiku family for the explanation step — fast, cheap,
and good at structured comparisons. Set `METHODOS_MODEL=anthropic/<current haiku>`
and `ANTHROPIC_API_KEY=...`. As of this writing, `claude-3-5-haiku-20241022` is
the right choice.

## Add a method (the most common contribution)

1. Pick an `Id_Like_This`. Create `methods/Id.json` and `methods/Id.md`.
2. Validate locally:
   ```bash
   python scripts/validate_methods.py
   ```
3. `methodos ingest && methodos query "<your test problem>"`
4. Open a PR. CI validates the JSON against `schemas/method_schema.json`.

## Improvement potentials (planned)

1. Online learning re-ranker informed by feedback ratings.
2. Cross-encoder re-rank step before the LLM.
3. JSONL → SQLite migration when feedback volume grows.
4. Hybrid search (BM25 over name/category + semantic).
5. Multilingual embeddings.
6. MCP server exposing `methodos query` as a tool.

## License

MIT. See [LICENSE](LICENSE).
```

- [ ] **Step 2: Commit**

```
git add README.md
git commit -m "docs: add README"
```

---

### Task 26: CLAUDE.md

**Files:**
- Create: `CLAUDE.md`

- [ ] **Step 1: Write `CLAUDE.md`** (verbatim from spec section 10, with the worktree-specific working-directory note)

```markdown
# CLAUDE.md — Working with Methodos AI

## Project shape
- src/ layout, Pydantic-everything, Typer CLI, ChromaDB + litellm.
- Methods are data (`methods/*.json` + `*.md`), not code.
- The schema in `schemas/` is *generated*, never hand-edited.

## Commands you'll run constantly
```
make test       # pytest with fast (non-network) tests
make lint       # ruff + mypy
make ingest     # rebuild local Chroma from /methods
make schema     # regenerate schemas/method_schema.json from Pydantic
make demo       # ingest + a sample query, end-to-end smoke
```

## Hard rules (override defaults)
1. NEVER import `openai`, `anthropic`, `sentence_transformers`, etc. at module
   top level. They MUST be lazy-imported inside the provider class.
2. NEVER add a method to /methods without a matching .md companion.
3. NEVER hand-edit schemas/method_schema.json. Run `make schema`.
4. ALWAYS run with `--no-llm` first when debugging retrieval — separates
   ranking issues from LLM issues.

## How to add a new method
1. Create `methods/<Id>.json` + `methods/<Id>.md`
2. `python -m methodos.cli ingest`
3. `methodos query "<test problem>"`

## How to add a new provider
1. Implement the Protocol in `src/methodos/providers/`
2. Wire it in `providers/__init__.py:make_llm` or `make_embedding`
3. Add a test in `test_providers.py` asserting Protocol conformance
4. Lazy-import any heavy deps inside `__init__`

## Architectural principles (priority order)
1. Knowledge layer is data. Code never hard-codes a method.
2. Provider boundary is sacred — only Protocols cross it.
3. Always-rebuild ingest. Chroma is a derived artifact.
4. Determinism in tests. Fakes, not mocks.
5. JSONL feedback is the placeholder. Don't pre-build a SQLite migration.

## Things to leave alone
- The math comment block in `ingest.py` / `search.py` (spec requirement).
- The TTY-only feedback hint (intentional UX choice).
- The over-fetch-then-rerank shape in `search.py` (extension hook).

## Where to find the design
- Spec: `docs/superpowers/specs/2026-05-07-methodos-ai-design.md`
- Plan: `docs/superpowers/plans/2026-05-07-methodos-ai.md`
```

- [ ] **Step 2: Commit**

```
git add CLAUDE.md
git commit -m "docs: add CLAUDE.md for AI-assisted development"
```

---

### Task 27: CONTRIBUTING.md + LICENSE

**Files:**
- Create: `CONTRIBUTING.md`
- Create: `LICENSE`

- [ ] **Step 1: Write `CONTRIBUTING.md`**

```markdown
# Contributing to Methodos AI

Two kinds of contributions, in increasing order of effort:

## 1. Add a method

Create `methods/<Id>.json` and `methods/<Id>.md`. Validate locally with
`python scripts/validate_methods.py`. Open a PR. CI does the rest.

The `<Id>` must match the JSON `id` field and starts with a capital letter.

## 2. Add a provider

Implement the `LLMProvider` or `EmbeddingProvider` Protocol from
`src/methodos/providers/base.py`. Add a test in `tests/test_providers.py`
asserting `isinstance(my_provider, LLMProvider)`. Wire it into
`providers/__init__.py:make_llm` or `make_embedding` if you want it
selectable via env var.

Lazy-import any heavy SDK dependencies inside the provider class. Top-level
imports break the offline-by-default guarantee.

## Development setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,local]"
make test
make lint
```

## Pre-commit checks

Run before pushing:

```bash
ruff format src tests scripts
ruff check src tests scripts
mypy src/methodos
pytest -q
python scripts/validate_methods.py
python scripts/regenerate_schema.py && git diff schemas/  # should be empty
```

## Commit style

Conventional commits: `feat:`, `fix:`, `chore:`, `test:`, `docs:`, `ci:`.
```

- [ ] **Step 2: Write `LICENSE`** (MIT)

```
MIT License

Copyright (c) 2026 Hayal Özkan

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```

- [ ] **Step 3: Commit**

```
git add CONTRIBUTING.md LICENSE
git commit -m "docs: add CONTRIBUTING and MIT LICENSE"
```

---

### Task 28: End-to-end smoke (`make demo`)

**Files:**
- Modify: `Makefile` (already has `demo` target — verify it works)

- [ ] **Step 1: Run `make demo`** in a venv that has `[dev,local]` installed

Run:
```
make demo
```
Expected: ingests three methods, then prints retrieval results for the demo query (with `--no-llm`, so no LLM call needed). Exit code 0.

- [ ] **Step 2: Run the full test suite**

Run: `pytest -q`
Expected: all tests pass (no integration tests run by default).

- [ ] **Step 3: Verify CI fixtures**

Run:
```
ruff check src tests scripts
ruff format --check src tests scripts
mypy src/methodos
python scripts/regenerate_schema.py --out /tmp/check.json && diff -u schemas/method_schema.json /tmp/check.json
python scripts/validate_methods.py
```
Expected: every step exits 0 with no diff.

- [ ] **Step 4: Final commit if anything was tweaked**

If any of the above produced changes (e.g. ruff format auto-fixes), commit them:
```
git add -A
git commit -m "chore: final polish from end-to-end smoke run"
```

---

## End of plan

After all tasks are complete:
- Branch should have ~28 commits, each isolated and reviewable.
- `methodos query "<problem>"` works end-to-end with offline defaults.
- CI passes on lint, types, schema drift, validation, and tests.
- `methodos feedback` + `methodos stats` exercise the placeholder loop.

The spec's improvement potentials (online re-ranker, JSONL→SQLite migration,
cross-encoder re-rank, hybrid search, MCP server) are intentionally out of
scope for v1 — they're listed in README "Improvement potentials" and become
follow-on plans, each with its own spec.
