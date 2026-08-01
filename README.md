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

## Cross-encoder reranking (optional)

Retrieval compares a query vector against document vectors that were embedded
independently. A cross-encoder instead feeds the query and each candidate
through one model together — much more accurate, far too slow to run over a
whole corpus. So it runs on the shortlist only:

```
Chroma returns top_k × overfetch_factor  →  cross-encoder rescores  →  top_k
```

Off by default. Turn it on per query or in `.env`:

```bash
methodos query "..." --rerank
# or
echo 'METHODOS_RERANK_PROVIDER=cross-encoder' >> .env
```

Needs the `local` extra (it reuses sentence-transformers) and downloads
`cross-encoder/ms-marco-MiniLM-L-6-v2` (~80MB) on first use. Costs roughly
120 ms per query over a 12-candidate shortlist, plus a one-off model load.

Measured against the 23-method catalog: all 23 pinned retrieval probes keep
ranking correctly, and it additionally resolves problem statements that
embedding-only retrieval cannot separate — for example *"internal strengths
and weaknesses vs external opportunities and threats"*, which the embedding
ranks 0.004 **behind** Porter's Five Forces and the reranker puts SWOT
15.3 ahead of.

Raise `METHODOS_OVERFETCH_FACTOR` to give the reranker a longer shortlist;
cost grows linearly with it.

## Improvement potentials (planned)

1. Online learning re-ranker informed by feedback ratings.
2. JSONL → SQLite migration when feedback volume grows.
4. Hybrid search (BM25 over name/category + semantic).
5. Multilingual embeddings.
6. MCP server exposing `methodos query` as a tool.

## License

MIT. See [LICENSE](LICENSE).
