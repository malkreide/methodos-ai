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
- **HTTP API + browser console** — `docker compose up`, then ask, read and rate
  at `http://localhost:8000`. See [Deploy](#deploy-http--docker).
- **MCP server** — the catalog as three read-only tools for Claude Desktop or
  any other MCP client.
- **Provider-neutral** — Anthropic, OpenAI, Google, Mistral, Ollama, etc., via
  one `LLMProvider` Protocol (litellm-backed).

## Quickstart

```bash
# 1. Install
git clone https://github.com/Malkreide/methodos-ai
cd methodos-ai
python -m venv .venv && source .venv/bin/activate   # or .venv\Scripts\activate
pip install -e ".[dev,local]"

# 2. (Optional) pick a cloud LLM, e.g. Anthropic
echo 'METHODOS_MODEL=anthropic/claude-opus-5' > .env
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

Anthropic for the explanation step: set `METHODOS_MODEL` and `ANTHROPIC_API_KEY`.

| Model | When |
|---|---|
| `anthropic/claude-opus-5` | Default. Best at the comparison itself — weighing three methods against one problem and against each other. |
| `anthropic/claude-haiku-4-5` | Cheapest and fastest, at some cost in the quality of the prose. Worth it for high query volume. |

Only the explain step is affected. Retrieval, ranking and the MCP server never
call an LLM, so the model choice cannot change which methods come back — only
how the ranking is described.

> Earlier revisions of this README recommended `claude-3-5-haiku-20241022`.
> That model was retired in February 2026 and now returns 404; the ids above
> replace it.

**Embeddings are a separate question.** Anthropic has no embedding endpoint, so
a cloud LLM does not remove the local sentence-transformers dependency — the
`local` extra is still what powers retrieval and reranking. Dropping it means
switching `METHODOS_EMBEDDING_PROVIDER=openai`, which trades one local model for
a second API key.

## Deploy (HTTP + Docker)

```bash
cp .env.example .env        # set ANTHROPIC_API_KEY
docker compose up --build   # http://localhost:8000
```

The image ships the sentence-transformers weights, so a started container needs
no egress except to Anthropic. The Chroma index is *not* shipped: `methods/` is
bind-mounted and the entrypoint re-ingests on every start, so editing a method
and running `docker compose restart methodos` is the whole edit loop. Feedback
survives restarts in a named volume.

| Endpoint | |
|---|---|
| `GET /` | Browser console — ask, read the explanation, rate a method |
| `GET /docs` | OpenAPI, with every field documented |
| `POST /query` | `{problem, top_k, category, explain, rerank}` → matches + explanation + `query_id` |
| `GET /health` | Config, provider names, index size. No LLM call — backs the container health check |
| `POST /llm/check` | One real completion. **This is the yes/no on whether your key and model work.** |
| `GET /methods`, `GET /methods/{id}` | The catalog and one method's full Markdown |
| `POST /feedback`, `GET /stats` | The same JSONL loop the CLI writes |

`/query` returns the MCP server's payload — `ranking_basis`, `guidance`,
`total_in_scope` — plus the explanation. It carries the same meaning here, and
[What the results tell you](#what-the-results-tell-you) applies unchanged.

**A failing LLM does not fail a query.** Retrieval and explanation are
independent, so a rejected key returns HTTP 200 with the matches intact and the
provider's error in `explanation_error` — hiding a working ranking behind an LLM
outage would be the worse failure. `POST /llm/check` is the endpoint that fails
loudly, and `"explain": false` is the API's `--no-llm`.

Without Docker:

```bash
pip install -e ".[dev,local,api]"
methodos ingest && make serve      # the server reads the index, it does not build one
```

One-off CLI against the same data as a running server:

```bash
docker compose run --rm cli query "our release keeps slipping" --no-llm
docker compose run --rm cli stats
```

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

## Known gaps

**The LLM explain path has never been verified against a live backend** ([#22]).
The `METHODOS_INTEGRATION_LLM=1` tests exist and are opt-in, but they were
written where no model was reachable — they have never passed, only failed at
the litellm call with everything upstream holding. That covers both whether the
call works at all and, more interestingly, whether a real model honours the
`ranking_basis` sentence instead of re-sorting the candidates by similarity.
`scripts/verify_explain.py` is the tool for answering the second one against
whatever model you deploy.

The HTTP deployment does not close this gap, but it makes it cheap to close,
in that order:

```bash
docker compose up -d
curl -sX POST localhost:8000/llm/check   # does the key/model work at all?
docker compose run --rm --entrypoint python cli scripts/verify_explain.py
```

The first is a yes/no. The second prints the reranked order next to the model's
prose and a verdict line, for a human to judge — there is no threshold at which
an explanation is "correct", which is why it is a script and not a test.

[#22]: https://github.com/malkreide/methodos-ai/issues/22

## License

MIT. See [LICENSE](LICENSE).
