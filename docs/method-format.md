# Method file format

Every method is two files in `methods/`: `<Id>.json` (structured, validated) and
`<Id>.md` (the human guide). The JSON Schema in `schemas/method_schema.json` is
generated from `src/methodos/models.py` — change the model, then `make schema`.

## Required fields

| Field | Notes |
|---|---|
| `id` | `Capitalised_With_Underscores`, equal to the file name |
| `name` | Display name |
| `category` | `strategy`, `decision-making`, `analysis`, `prioritization`, `retrospective`, `facilitation`, `change-management` |
| `use_case` | ≥ 40 characters. The canonical problem description, **embedded for search** |
| `strengths`, `weaknesses` | 1–12 entries each |
| `complexity_score` | 1–5 |
| `estimated_duration` | `{min_minutes, max_minutes}` |

## Optional fields

All optional, all non-breaking: a file without them is exactly as valid as it
was before they existed.

| Field | Type | What it is for |
|---|---|---|
| `use_cases` | up to 20 strings, ≥ 40 chars each | Further situations the method answers. **Each is embedded as its own vector**; a query only needs to be close to one of them. This is where contexts live for search — "a school leadership team…", "an executive board…". |
| `contexts` | `business`, `public-sector`, `education`, `nonprofit`, `personal` | Kind of organisation it has been shown to work in. Filter with `methodos list --context`, `GET /methods?context=` or the MCP `list_methods` tool. |
| `formats` | `in-person`, `hybrid`, `remote`, `async` | How it can be run |
| `group_size` | `{min_people, max_people}` | |
| `audience` | up to 12 strings | Free text: "school leadership", "product team" |
| `language` | ISO 639-1, default `en` | Language of this JSON and its `.md` |
| `assets` | list, see below | Templates, boards, slides |
| `owner` | string | Who maintains the entry |
| `last_reviewed` | ISO date | When the owner last checked it; `scripts/audit_catalog.py` flags stale entries |

### `use_case` vs. `use_cases`

Write `use_case` as the general description. Put each *distinct* situation into
`use_cases` — different context, different audience, different trigger. Do not
paraphrase `use_case` there: near-duplicates add vectors without adding reach.
Search reports which text matched (`matched_use_case`), and the reranker scores
that text, so each entry should stand on its own.

### Assets

```json
"assets": [
  {"title": "Canvas (A3)", "kind": "template", "path": "canvas-a3.pdf", "license": "CC-BY-SA-4.0"},
  {"title": "Facilitation kit", "kind": "slides", "access": "premium", "url": "https://…"}
]
```

- `kind`: `template`, `worksheet`, `slides`, `board`, `checklist`, `video`, `other`
- Exactly one of `path` and `url`.
- `path` is relative to `methods/assets/<Id>/`. Ingest and CI fail if the file is
  missing. Keep files small and in open formats (PDF, SVG, PNG, Markdown); binary
  office files belong behind a `url`.
- `access: premium` **must** use `url`. The repository is public, so anything in
  it is open by definition; premium material is only ever referenced.
- Assets are never embedded — search runs on `use_case` and `use_cases` only.
