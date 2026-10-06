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
- **Multilingual** — ask in German (or ~50 other languages), get the right method.
- **Agent-curated** — an audit script and two Claude Code agents keep the
  catalog current as reviewable pull requests ([docs/curation.md](docs/curation.md)).

Access tiers and the path to a paid offering are in
[docs/strategie-zugang-monetarisierung.md](docs/strategie-zugang-monetarisierung.md) (German).

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

The default config is **fully offline** and **multilingual**: Ollama for the LLM
(`ollama/llama3.1:8b`), `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
for embeddings, and the multilingual cross-encoder
`cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` as a rerank step on the shortlist.
Ask in German, get the right English method — see [Languages](#languages). One env var
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

The image ships the sentence-transformers weights and runs with
`HF_HUB_OFFLINE=1`, so a started container needs no egress except to Anthropic.
(Without that flag it would still HEAD huggingface.co on every model load and
fail to start when that request fails — set `HF_HUB_OFFLINE=0` only when you
have overridden `METHODOS_EMBEDDING_MODEL` or `METHODOS_RERANK_MODEL` to a model
that is not baked in.) The Chroma index is *not* shipped: `methods/` is
bind-mounted and the entrypoint re-ingests on every start, so editing a method
and running `docker compose restart methodos` is the whole edit loop. Feedback
survives restarts in a named volume.

| Endpoint | |
|---|---|
| `GET /` | Browser console — ask, read the explanation, rate a method, propose one. German or English, by browser language; `?lang=de` / `?lang=en` forces one |
| `GET /docs` | OpenAPI, with every field documented |
| `POST /query` | `{problem, top_k, category, explain, rerank}` → matches + explanation + `query_id` |
| `GET /health` | Config, provider names, index size. No LLM call — backs the container health check |
| `POST /llm/check` | One real completion. **This is the yes/no on whether your key and model work.** |
| `GET /methods`, `GET /methods/{id}` | The catalog and one method's full Markdown |
| `POST /feedback`, `GET /stats` | The same JSONL loop the CLI writes |
| `POST /proposals` | Propose a missing method: name, problem, sources and links → stored in `proposals.jsonl`, with the closest existing methods and a prefilled GitHub issue link. Publishes nothing — see [docs/curation.md](docs/curation.md) |
| `POST /proposals/extract` | Multipart upload of a PDF, Word (.docx), text, audio or video file → its text, and optionally an LLM draft that prefills the proposal form. Stores nothing; see [Uploads](#uploads) |

`/query` returns the MCP server's payload — `ranking_basis`, `guidance`,
`total_in_scope` — plus the explanation. It carries the same meaning here, and
[What the results tell you](#what-the-results-tell-you) applies unchanged.

**A failing LLM does not fail a query.** Retrieval and explanation are
independent, so a rejected key returns HTTP 200 with the matches intact and the
provider's error in `explanation_error` — hiding a working ranking behind an LLM
outage would be the worse failure. `POST /llm/check` is the endpoint that fails
loudly, and `"explain": false` is the API's `--no-llm`.

### Uploads

The console's *Propose a method* tab can start from a file. What happens to it:

1. The file is written to a temporary directory and **deleted before the
   response is sent**. Its name is not kept.
2. PDF (`pypdf`), Word `.docx` (standard library) and `.txt`/`.md` are read
   in-process. Scanned PDFs (no text layer), legacy `.doc` and images are
   refused with a message saying what to do instead.
3. Audio and video are transcribed **on this server** with faster-whisper
   (the `transcribe` extra; the image bakes in the `small` model). Video is
   reduced to its audio track. The recording never leaves the machine.
4. With *Draft with the LLM* on, the extracted **text** — not the file — goes
   to the configured model, which returns a draft for the form. The person
   edits it and submits as usual; only what they submit is stored, plus the
   kind of file it started from (`extracted_from`).

Limits: `METHODOS_UPLOAD_MAX_MB` (default 50, checked against Content-Length
before the body is read) and `METHODOS_MEDIA_MAX_MINUTES` (default 20, checked
from the file header before decoding). Transcription runs inside the request:
on a 4-core CPU the `small` model needs very roughly a quarter of the
recording's length, and about 1 GB of RAM while it runs. Behind a reverse
proxy, raise its body-size limit to match and its read timeout to several
minutes, or long recordings will fail at the proxy rather than here.
`docker build --build-arg WHISPER_MODEL=base .` makes a smaller image with a
weaker German transcript.

Without the `transcribe` extra the server still starts and reads documents;
`/health` lists what it accepts in `upload_suffixes`.

Without Docker:

```bash
pip install -e ".[dev,local,api,transcribe]"
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
4. Add one English and one German probe to `tests/test_integration.py` and run
   `pytest -m integration`.
5. Open a PR. CI validates the JSON against `schemas/method_schema.json`.

Every field — including the optional ones for further use cases, contexts,
formats and assets — is described in [docs/method-format.md](docs/method-format.md).

## Cross-encoder reranking (optional)

Retrieval compares a query vector against document vectors that were embedded
independently. A cross-encoder instead feeds the query and each candidate
through one model together — much more accurate, far too slow to run over a
whole corpus. So it runs on the shortlist only:

```
Chroma returns top_k × overfetch_factor methods
  →  cross-encoder scores every text of each (use_case + use_cases)
  →  each method keeps its best score  →  top_k
```

Scoring every text, rather than only the one the embedding found nearest, is
what makes adding a use case safe: a method can only gain from another text,
never lose. Under nearest-text scoring a loosely phrased use case that sat
closer to a query than the canonical description could replace it in front of
the cross-encoder and drag the method down — measured on RICE, one added use
case cut its English probe margin from 16.8 to 6.4 and its German one from 4.0
to 1.7. With best-text scoring the same addition changes nothing, and a better
one lifts the German probe from 4.0 to 6.1. The price is fairer competition:
rivals are scored on their best text too, so margins over the runner-up fell
on 16 of 48 probes (at most 2.8, all still first).

**On by default.** Turn it off per query or permanently:

```bash
methodos query "..." --no-rerank
# or
echo 'METHODOS_RERANK_PROVIDER=none' >> .env
```

It reuses sentence-transformers from the `local` extra and downloads
`cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` (~470MB) on first use. Cost
grows with the number of texts on the shortlist — about 48 for the default
9-method shortlist of the current 59-method catalog, up from 6 when only one
text per method was scored.

If sentence-transformers is not installed — an OpenAI-embeddings setup, say —
queries do **not** fail. Reranking is a quality enhancement, so it degrades to
embedding-only ranking and says so. An explicit `--rerank` still errors, because
silently ignoring a direct request would be worse.

With the multilingual models the reranker is no longer optional polish — it
does the ordering. The embedding alone ranks 20 of 23 English and 19 of 23
German probes first, but puts the right method within the top four every time;
the cross-encoder then ranks all 46 first. Turning reranking off still works
and still degrades gracefully, but expect noticeably worse ordering.

`METHODOS_OVERFETCH_FACTOR` controls the shortlist length (default 3, i.e.
`top_k × 3`). It was 2 until the catalog reached 39 methods: by then two pinned
probes found their method only 6th by embedding — the last slot of a 6-method
shortlist — and three independent authoring runs had pushed one of them out
with a single new method. At 3 all 78 probes still rank first, and the
reranker scores about 48 texts instead of 32, roughly 15% more time per query.
Cost grows linearly with the shortlist; raise it again when the right answer
starts landing near the end of it.

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
- **`guidance`** — set when the best match falls below 0.33, with a concrete
  next step. That floor is measured, not guessed: the weakest of the 118 pinned
  integration probes (English and German) scores 0.380, while questions the
  catalog genuinely does not cover reach 0.291 at most (*"Rezept für Zürcher
  Geschnetzeltes"*). Weak matches are still returned — `guidance` is a caveat, never a
  filter, because an empty list is what a model fills in from memory.

## Languages

The catalog is written in English; questions can be asked in any of the ~50
languages the models cover. Measured on the 23 pinned problems, phrased once in
English and once in Swiss-German usage:

| | English | German |
|---|---|---|
| previous default (`all-MiniLM-L6-v2`, English-only) | 23/23 | 7/23 |
| multilingual embedding + multilingual reranker | 23/23 | 23/23 |

The LLM explanation answers in the language of the question. The switch costs
image size (model weights ~160MB → ~930MB) and about 40 ms per query.

**Existing installs must re-ingest** after upgrading: the index records which
model built it, and a query against an index from the old model fails with a
`StaleIndexError` naming both, rather than returning nonsense.

To go back to the English-only models:

```bash
METHODOS_EMBEDDING_MODEL=all-MiniLM-L6-v2
METHODOS_RERANK_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2
```

## Improvement potentials (planned)

1. Online learning re-ranker informed by feedback ratings.
2. JSONL → SQLite migration when feedback volume grows.
4. Hybrid search (BM25 over name/category + semantic).

## Privacy

What leaves the user's hands, and where it goes:

| Data | Stored | Sent elsewhere |
|---|---|---|
| The question (`/query`, `methodos query`) | verbatim in `feedback.jsonl`, with a timestamp | to the LLM provider when the explanation runs |
| Rating note (`/feedback`, `--note`) | verbatim in `feedback.jsonl` | no |
| Method proposal (`/proposals`) | verbatim in `proposals.jsonl`, with a timestamp | no — the GitHub link is opened, and submitted, by the person themselves |
| Uploaded file (`/proposals/extract`) | no — a temporary file for the length of the request, then deleted | no — audio and video are transcribed locally |
| Text extracted from an upload | no — returned to the browser only | to the LLM provider when the draft runs |
| Client IP | not by Methodos; uvicorn's access log prints it to stdout | depends on your log shipping |

The MCP server logs nothing and calls no LLM.

Recordings are the sensitive case: a workshop or a lesson carries the voices
of people who did not choose to be in a catalog's inbox. Transcription is
local by contract (`TranscriptionProvider` in `providers/base.py`), and the
console asks people not to upload recordings of others without their
consent — but the transcript does reach the LLM provider when the draft is
on, and a name spoken in a recording becomes a name in that text.

The console, the OpenAPI field descriptions and the CLI help all tell the person
typing to leave out personal data. That is a notice, not a filter: nothing
scrubs names out of free text. If you operate a public instance you are the one
processing that data, so publish a privacy notice that names the LLM provider,
set a retention period for `feedback.jsonl` and `proposals.jsonl`, and run uvicorn with
`--no-access-log` if you do not need IPs.

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

**The upload draft has been run against Llama 3.1 8B only, not against the
model the container uses.** `scripts/verify_draft.py` runs five fixed cases
through the real draft path. With `ollama/llama3.1:8b` the format held every
time, but the model obeyed an instruction planted in the document, and in
individual runs answered in the wrong language or named a misheard word as the
source. Prompt changes fixed the language; the rest is caught after the fact by
`check_draft`, which flags copied passages, instruction-like text in the
document, sources the document does not contain and drafts in the wrong
language, and the console shows those warnings. Before relying on the draft
with your production model, run
`python scripts/verify_draft.py --model <METHODOS_MODEL>`.

[#22]: https://github.com/malkreide/methodos-ai/issues/22

## License

- **Code** (everything outside `methods/`): MIT, see [LICENSE](LICENSE).
- **Method catalog** (`methods/`, including assets): CC BY-SA 4.0, see
  [methods/LICENSE](methods/LICENSE). Reuse it commercially if you like, with
  attribution, and share your changes under the same licence.

Releases up to 0.5.0 shipped the catalog under MIT as well; those copies keep
those terms.
