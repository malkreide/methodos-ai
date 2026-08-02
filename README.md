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

The default config is **fully offline**: Ollama for the LLM (`ollama/llama3.1:8b`),
`sentence-transformers/all-MiniLM-L6-v2` for embeddings, and a cross-encoder
rerank step on the shortlist. One env var
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

## Cross-encoder reranking (optional)

Retrieval compares a query vector against document vectors that were embedded
independently. A cross-encoder instead feeds the query and each candidate
through one model together — much more accurate, far too slow to run over a
whole corpus. So it runs on the shortlist only:

```
Chroma returns top_k × overfetch_factor  →  cross-encoder rescores  →  top_k
```

**On by default.** Turn it off per query or permanently:

```bash
methodos query "..." --no-rerank
# or
echo 'METHODOS_RERANK_PROVIDER=none' >> .env
```

It reuses sentence-transformers from the `local` extra and downloads
`cross-encoder/ms-marco-MiniLM-L-6-v2` (~80MB) on first use. Costs roughly
66 ms per query over the default 6-candidate shortlist.

If sentence-transformers is not installed — an OpenAI-embeddings setup, say —
queries do **not** fail. Reranking is a quality enhancement, so it degrades to
embedding-only ranking and says so. An explicit `--rerank` still errors, because
silently ignoring a direct request would be worse.

Measured against the 23-method catalog: all 23 pinned retrieval probes keep
ranking correctly, and it additionally resolves problem statements that
embedding-only retrieval cannot separate — for example *"internal strengths
and weaknesses vs external opportunities and threats"*, which the embedding
ranks 0.004 **behind** Porter's Five Forces and the reranker puts SWOT
15.3 ahead of.

`METHODOS_OVERFETCH_FACTOR` controls the shortlist length (default 2, i.e.
`top_k × 2`). On the current 23-method catalog, raising it buys nothing —
factors 2, 3, 4 and 6 all score 23/23 on the pinned probes — while cost grows
linearly (66 → 200 ms). It becomes worth raising as the catalog grows and the
right answer starts landing further down the embedding ranking.

## MCP server

Exposes the catalog to an MCP client (Claude Desktop, Claude Code, any other)
as three read-only tools:

| Tool | What it does |
|---|---|
| `recommend_methods` | Semantic search over the indexed catalog |
| `list_methods` | The complete catalog — no search, no truncation |
| `get_method` | One method's full Markdown documentation |

```bash
pip install -e ".[mcp,local]"
methodos ingest          # the server reads the index, it does not build one
```

```jsonc
// claude_desktop_config.json
{
  "mcpServers": {
    "methodos": {
      "command": "methodos-mcp",
      "env": { "METHODOS_METHODS_DIR": "/abs/path/to/methods",
               "METHODOS_CHROMA_PATH": "/abs/path/to/data/chroma" }
    }
  }
}
```

Both paths are worth setting explicitly: a client launches the server from an
arbitrary working directory, where the relative defaults resolve to nothing.

**Retrieval only — the server never calls an LLM.** `methodos query` runs a
completion to explain its ranking, but here the caller already *is* a model
holding the user's full context. A second model explaining the ranking to the
first would cost an extra call and an API key to produce a worse explanation.

**`ingest` is deliberately not a tool.** It mutates state and can disturb a
running instance; it stays a CLI command.

### What the results tell you

A vector search answers *every* query with its nearest neighbours and never
returns an empty list — so "no results" never appears, and a bad question comes
back looking exactly like a good one. Three fields exist so the calling model
can tell the difference rather than guess:

- **`returned` / `total_in_scope` / `total_indexed`** — a caller shown 3 methods
  cannot otherwise tell a 3-method catalog from a truncated view of 23.
- **`ranking_basis`** — `cross-encoder` means `similarity` is *not* the sort
  key and a lower-similarity method may rank above a higher one on purpose.
  Without the `local` extra the reranker degrades to nothing, and this field is
  how the caller learns the order changed meaning.
- **`guidance`** — set when the best match falls below 0.25, with a concrete
  next step. That floor is measured, not guessed: the weakest of the 23 pinned
  integration probes scores 0.321, while questions the catalog genuinely does
  not cover reach 0.127 at most (*"how do I fix my bicycle chain"* → Five Whys
  at 0.106). Weak matches are still returned — `guidance` is a caveat, never a
  filter, because an empty list is what a model fills in from memory.

## Improvement potentials (planned)

1. Online learning re-ranker informed by feedback ratings.
2. JSONL → SQLite migration when feedback volume grows.
4. Hybrid search (BM25 over name/category + semantic).
5. Multilingual embeddings.

## License

MIT. See [LICENSE](LICENSE).
