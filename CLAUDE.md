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
make serve      # HTTP API + browser console on :8000 (needs `make ingest` first)
make docker-up  # the same thing containerised, ingest included
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
1. Create `methods/<Id>.json` + `methods/<Id>.md` (fields: `docs/method-format.md`)
2. Add an English probe to `PROBES` and a German one to `PROBES_DE` in `tests/test_integration.py`
3. `python -m methodos.cli ingest`
4. `methodos query "<test problem>"`, then `pytest -m integration`

## Curating the catalog
- `scripts/audit_catalog.py` lists what needs work; the `method-curator` and
  `method-author` agents in `.claude/agents/` do it as draft PRs.
- The owner's merge is the review. Agents never merge. See `docs/curation.md`.

## How to add a new provider
1. Implement the Protocol in `src/methodos/providers/`
2. Wire it in `providers/__init__.py:make_llm`, `make_embedding` or `make_reranker`
3. Add a test in `test_providers.py` asserting Protocol conformance
4. Lazy-import any heavy deps inside `__init__`

## Architectural principles (priority order)
1. Knowledge layer is data. Code never hard-codes a method.
2. Provider boundary is sacred — only Protocols cross it.
3. Always-rebuild ingest. Chroma is a derived artifact.
4. Determinism in tests. Fakes, not mocks.
5. JSONL feedback is the placeholder. Don't pre-build a SQLite migration.
6. The repository is public. Premium assets are referenced by `url`, never
   committed (the model enforces it).

## Surfaces, and what each one may do
| | LLM call? | Why |
|---|---|---|
| CLI `query` | yes | Nothing else would write the explanation. |
| HTTP `/query` | yes | Same — plus it is the surface that exists to exercise the explain path. |
| HTTP `/proposals/extract` | only with `draft` on | Turns an uploaded file's text into a form draft. The file itself never reaches the LLM; audio and video are transcribed locally (`TranscriptionProvider`). |
| MCP server | **never** | The caller already is a model with the user's context. |

`api.py` and `mcp_server.py` are both thin translators over `mcp_tools`. Ranking
decisions — `guidance`, `ranking_basis`, the scope totals — belong in
`mcp_tools.recommend_with_candidates` so the two surfaces cannot drift apart.

## Things to leave alone
- The math comment block in `ingest.py` / `search.py` (spec requirement).
- The TTY-only feedback hint (intentional UX choice).
- The over-fetch-then-rerank shape in `search.py` — now occupied by the
  cross-encoder reranker. `retrieve()` keeps working with `reranker=None`;
  don't collapse the two paths.

## Where to find the design
- Spec: `docs/superpowers/specs/2026-05-07-methodos-ai-design.md`
- Plan: `docs/superpowers/plans/2026-05-07-methodos-ai.md`
