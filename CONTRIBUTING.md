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
