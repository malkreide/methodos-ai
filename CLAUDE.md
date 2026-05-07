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

On Windows without `make`: run the inner commands directly (`pytest`, `ruff check src tests scripts`, etc.).

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
