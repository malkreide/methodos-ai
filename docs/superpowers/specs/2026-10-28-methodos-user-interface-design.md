# Methodos user interface — prototype design

Date: 2026-10-28
Status: draft, awaiting approval

## Intent

Methodos today has three surfaces — CLI, MCP server, and an HTTP API whose
browser page (`src/methodos/console.html`) is a developer test console. None of
them is built for the person Methodos exists for.

That person is **stuck**: they face a problem or a next step and do not know how
to approach it. They come to Methodos to get three things:

1. **An answer** — which method fits their problem.
2. **A reason** — why this method, and when it would be the wrong one.
3. **Guidance** — a walk through applying the method, step by step.

This design is a **prototype** of a user-facing interface that delivers those
three things, plus two loops that make Methodos better over time: **feedback**
from users, and a memory of **what the user has already done** so a returning
user does not start from zero.

The prototype exists to find out whether this interface works for real users.
Scaling it (accounts, multi-device history, translation) is deliberately
deferred until the prototype has proven itself — see *Later*.

## Visual direction

Inspired by the DiscoveryRSI "Discovery Arena" dashboard
(foundry-arena.rsi-arena.workers.dev/arena) — **patterns only**: no code,
assets, branding, or copy from that page.

Of three explored layouts (guided wizard / dense dark cockpit / workspace), the
**workspace** was chosen: light and calm, carrying over the strongest Arena
patterns while staying uncluttered for someone who is already overwhelmed.

Patterns taken from the Arena:

- **Ranked list with bars** — rank, method name, bar; best match on top.
- **Reason next to the value** — "Why this method?" sits beside the ranking,
  not below the fold.
- **Stat tiles with a caption** — big value plus a one-line label saying what it
  means (duration, effort, number of steps).
- **Progress track** — a segmented bar showing where the user is while applying
  a method.
- **Monospace micro-labels** for section headings.

Not taken: the dark, dense cockpit look, decorative illustration, playback
controls, live event stream.

Light theme is the default; the page follows `prefers-color-scheme` into dark
mode, as `console.html` already does.

The approved layout mockup lives in the brainstorming session
(`ablauf.html`, variant C); it is a wireframe, not a pixel spec.

## The flow

One page, three stages: **describe the problem → choose a method → apply it.**

### 1. Describe the problem

- A free-text field for the problem (same guidance as today: describe the
  symptom or decision, not a method).
- A second, optional field: **"What I've already done"** — see *History*.
- No developer controls on this page: no `top_k`, no rerank toggle, no
  "test LLM" button, no raw JSON. Those stay in the developer console.

### 2. Choose a method

- **Ranked list** of the returned methods with bars. **No raw scores** in the
  main view (`similarity`, `rerank_score` mean nothing to a stuck user). The bar
  carries the relative fit; a plain-word label (e.g. "strong fit") is optional.
  Raw values are available behind a "Details" disclosure.
- **"Why this method?"** panel beside the list, filled by the LLM explanation
  that `/query` already produces. That explanation is one comparative text
  covering all candidates and ending in a recommendation (one LLM call,
  `prompts/explain.txt`); the prototype shows it **as is** and does not change
  the prompt or ask for per-method output. The LLM's final recommendation may
  differ from rank #1; that is acceptable and is shown honestly. Selecting
  another method in the list does not re-query the LLM: the panel keeps the
  comparative text, and the method-specific facts (use case, strengths,
  "Not a fit when…") come from the method data. If the explain step fails
  (`explanation_error`), the ranking is still shown and the panel says the
  explanation is unavailable — never hide a working ranking behind an LLM
  outage (same rule as the API).
- **Stat tiles** for the selected method: duration (`duration_min`–
  `duration_max`), effort (`complexity_score` as ●○○○○), number of steps.
- **"Not a fit when…"** and **"Consider instead"** for the selected method,
  sourced from the method's Markdown (`When *not* to use`, `See also`).
  Methodos recommends honestly, including saying when not to use something.
- **One call, then wait.** The page makes a single `/query` call and shows
  ranking and explanation together when it returns. A user waiting several
  seconds for the LLM is accepted for the prototype; the page shows a clear,
  calm waiting state meanwhile. No new endpoint, no streaming, and never two
  `/query` calls for one problem (that would log two recommendations).
- `guidance` from the API (e.g. low-confidence warnings) is shown prominently.
- The user can select any method in the list, not only the top one.

### 3. Apply the method (check-off guidance)

- The method's steps are shown as a **checklist**, one step at a time or all
  visible with the current one highlighted — builder's choice.
- Each step shows its text and its time box where the source gives one.
- A **progress track** (Arena pattern) shows done / current / remaining.
- The actual work happens **outside the tool** (paper, whiteboard, meeting).
  The prototype does **not** capture the user's results per step.
- Common pitfalls (`## Common pitfalls`) are available alongside the steps.
- Finishing (or leaving) a method creates a **history entry** (see below).

## Data: where the guidance comes from

All 23 method companions (`methods/*.md`) have the same three sections, in the
same form:

- `## When *not* to use`
- `## Facilitation outline (<duration>)` — a numbered list; most steps start
  with a time box like `(5 min)`.
- `## See also` — links to other methods (`[Name](Id.md)`) and external pages.

`GET /methods/{method_id}` already returns the full Markdown as
`documentation`. The prototype needs these sections as **structured data**, not
as Markdown the page must parse.

- **Parse server-side**, in `mcp_tools` (next to `get_method`), and extend
  `MethodDetail` with structured fields: steps (text + optional time box),
  outline duration label, not-a-fit-when items, see-also links (internal method
  ids distinguished from external URLs), common pitfalls. Keep `documentation`
  unchanged.
- **Do not** copy these texts into `methods/*.json`. The Markdown stays the
  single source; `schemas/method_schema.json` is not touched.
- Parsing must be tested against all 23 real files, and must degrade
  gracefully: a method whose section is missing or malformed still renders,
  with that part omitted.

## Feedback

Feedback stays in the existing append-only JSONL (`feedback.py`). Architectural
principle 5 holds: no SQLite, no new store.

Two moments, both tied to the recommendation by `query_id`:

1. **After the recommendation** — "Does this fit my problem?" Rates the
   *ranking* for this problem.
2. **After applying** — "Did the method help? What was unclear or missing?"
   Rates the *method and its guidance*. Free-text note encouraged.

The returning-user prompt (see *History*) is the natural place to collect
moment 2: "How did Five Whys go?"

Change to the data model: `RatingEvent` gets a field saying which moment the
rating belongs to (`aspect: "recommendation" | "application"`). Details:

- **Both moments use the existing 1–5 scale** and the existing optional `note`.
  The two aspects are never averaged together.
- **A recommendation rating attaches to the method the user selected** (the
  one they go on to apply), with the `query_id` of that recommendation.
- **Existing lines without `aspect` read as `"application"`.** That is what the
  CLI's "Record outcome" ratings and the console's "Did it help?" have always
  meant, so old data is not misfiled.
- **`/stats` stays backward compatible:** the existing per-method fields keep
  their meaning, now counting application ratings only; per-method count and
  average for recommendation ratings are added as new fields. The console and
  existing tests keep working. Extend `FeedbackRequest` and the CLI's
  `feedback` command with the optional `aspect`, defaulting to
  `"application"`.

Feedback is **not tied to a person** — there is no user identity in the
prototype.

## History ("what I've already done")

Both ways must work:

- **Typed by the user** — the optional "What I've already done" field, always
  present, nothing stored.
- **Remembered by Methodos** — on a return visit the page shows recent entries
  (method, date, steps checked, whether feedback was given) and the user can
  take them over into the field, edit them, or delete them.

Both paths end in the same field, so downstream there is one input, regardless
of where it came from.

**Storage: the user's own browser only** (`localStorage`). No accounts, no
server-side history. Consequences accepted for the prototype: history is per
device and browser, and clearing site data loses it. Every read and write must
tolerate storage being unavailable (private mode, blocked storage) — the page
must work fully without it.

A history entry holds: method id and name, date, the problem text it came from,
steps checked, the `query_id`, and whether application feedback was given.

**How history affects recommendations (prototype):** the "already done" text is
sent with the query as a separate field and given to the **LLM explanation**,
so the explanation can account for it (e.g. suggest a follow-up). It does
**not** change the ranking itself. The UI may additionally surface the
`See also` methods of the most recent history entry as "possible next steps".
Any change to ranking would belong in `mcp_tools.recommend_with_candidates`
and is out of scope here.

The history text must not be logged into the feedback JSONL beyond what
`/query` already logs.

## Constraints

- **Language:** English throughout the prototype — UI and method content.
- **Same build shape as `console.html`:** one self-contained HTML file shipped
  inside the Python package, no build step, no external requests (fonts,
  scripts, CDNs), so it works in the Docker container with no egress.
- **Served by the existing FastAPI app.** The new page takes `/`; the developer
  console moves to `/console` and keeps working unchanged.
- **Thin page:** the page holds no ranking logic. It renders what the API
  returns. `api.py` and `mcp_server.py` stay thin translators over `mcp_tools`.
- **MCP server never calls the LLM** — unchanged; the structured method fields
  are available to it like any other `mcp_tools` output.
- **Hard rules in `CLAUDE.md` apply** (lazy imports, no hand-editing the
  schema, etc.).

## Goals

- A stuck user can go from problem to a chosen method to a checked-off
  application without help and without seeing developer vocabulary.
- Every recommendation shows why, and when not to use it.
- Both feedback moments are easy enough that users actually give them.
- A returning user sees what they did last time and can build on it.

## Non-goals (prototype)

- Accounts, login, multi-device or team history.
- Capturing the user's work inside each step (forms per method).
- Translation into German or other languages.
- Changing how methods are ranked.
- Replacing or redesigning the developer console.
- Analytics dashboards over the feedback.

## Anti-goals

- Overwhelming the user: Arena-level density, raw scores, developer toggles.
- A recommendation that hides its uncertainty or never says "not a fit".
- Storing personal problem descriptions centrally beyond what `/query` already
  logs today.
- A page that breaks when the LLM, storage, or a method's Markdown section is
  unavailable.

## Later (planned in the repo once the prototype succeeds)

- Server-side history with identity; multi-device and team use; retention and
  deletion rules appropriate for school/administration data.
- German UI and translated method content.
- Capturing results per step.
- Using history in ranking (in `mcp_tools`).
- Migrating feedback from JSONL to SQLite when volume justifies it.
- Showing the ranking before the explanation (a separate explain step keyed
  by `query_id`, or streaming), if the wait proves to be a problem in testing.

## Decided by the product owner

- Workspace layout (variant C) with Arena patterns.
- Two feedback moments: recommendation fit and method outcome.
- History both typed and remembered; remembered on the device only for now.
- Multi-device tracking deferred, to be planned later in the repo.
- Check-off guidance, no per-step data capture.
- English for the prototype.
- One blocking `/query` call is fine; waiting for the explanation is accepted.

## Calls made by the designer (check these)

- New page at `/`, developer console moved to `/console`.
- Section parsing done server-side in `mcp_tools`, exposed via `MethodDetail`.
- No raw scores in the main view; raw values behind "Details".
- History feeds the LLM explanation, not the ranking.
- `aspect` field added to `RatingEvent`, optional for backward compatibility;
  old lines count as `"application"`; recommendation ratings attach to the
  selected method; `/stats` adds recommendation fields alongside the existing
  ones.
- The "Why this method?" panel shows the existing comparative LLM
  explanation unchanged; no prompt change, no per-method LLM output.

## Left to the builder

- Exact visual design within the direction above (spacing, colors, type).
- One-step-at-a-time vs. full checklist with highlighted current step.
- Wording of labels and prompts.
- Name of the new request field for "already done" and of the new
  `MethodDetail` fields.
- How many history entries to show and keep.
