# Contributing to Methodos AI

Two kinds of contributions, in increasing order of effort:

## 1. Add a method

Create `methods/<Id>.json` and `methods/<Id>.md`. Validate locally with
`python scripts/validate_methods.py`. Open a PR. CI does the rest.

The `<Id>` must match the JSON `id` field and starts with a capital letter.

## 2. Add a provider

Implement the `LLMProvider`, `EmbeddingProvider` or `RerankProvider` Protocol
from `src/methodos/providers/base.py`. Add a test in `tests/test_providers.py`
asserting `isinstance(my_provider, LLMProvider)`. Wire it into
`providers/__init__.py:make_llm`, `make_embedding` or `make_reranker` if you
want it selectable via env var.

Lazy-import any heavy SDK dependencies inside the provider class. Top-level
imports break the offline-by-default guarantee.

## Development setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,local]" -c constraints.txt
make test
make lint
```

`constraints.txt` pins the dev environment to the same versions CI uses, so a
dependency release can't break your branch on its own. `pyproject.toml` keeps
open ranges — the pins are for this repo, not for people installing methodos.
Dependabot opens monthly PRs to move them; refresh instructions are in the
file's header.

Add `mcp` to the extras (`".[dev,local,mcp]"`) to work on the MCP server.
Without it `tests/test_mcp_server.py` skips — but `tests/test_mcp_tools.py`,
which holds the actual tool contract, runs either way, because it imports no
`mcp` package at all. CI installs `".[dev,mcp]"` (mypy type-checks
`mcp_server.py` and needs the SDK to do it), so both suites run there; the
split exists so the contract would still be verified if that ever changed.

## Integration tests

`make test` runs the offline suite only — tests marked `integration` are
deselected by default. They exercise the query path with the real embedding
model against the real `methods/` catalog, so they catch a `use_case` that has
stopped matching the problems it should match:

```bash
pytest -m integration                        # needs the `local` extra
METHODOS_INTEGRATION_LLM=1 pytest -m integration   # also hits a real LLM
```

Without the `local` extra they skip rather than fail, so CI (which installs
`[dev,mcp]` — not `local`, torch is too heavy for a lint job) still collects
them as a parse check. Run them after changing a method's `use_case`, the
ingest pipeline, or the retrieval math.

### The LLM half has never actually run — see #22

`METHODOS_INTEGRATION_LLM=1` is opt-in for a reason beyond cost. Both tests
behind it were written in an environment with no reachable model, so they have
never passed — only failed at the litellm call, with retrieval and the
rerank/similarity precondition holding right up to it.

Treat a first green run as new information rather than a formality. The order
assertion encodes a claim about *model behaviour* — that a model introduces
the reranked top before the candidate the embedding preferred — and that is a
property of the model you configure, not of this repo. It needs re-checking
whenever the model changes, which is what `scripts/verify_explain.py` is for:

```bash
python scripts/verify_explain.py --model ollama/llama3.1:8b --model openai/gpt-4o-mini
```

It prints the ranking beside each model's explanation instead of asserting, so
you can judge the prose. Nothing here asserts wording; it is not reliably
assertable.

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
