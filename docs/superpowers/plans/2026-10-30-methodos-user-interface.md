# Methodos User Interface Prototype Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A user-facing page at `/` that takes a stuck person from problem → chosen method (with reasons) → checked-off application, with two feedback moments and device-local history.

**Architecture:** The server gains three small capabilities: structured guidance parsed from `methods/*.md` (exposed on `MethodDetail`), an `aspect` on feedback ratings, and an optional "already done" text that reaches the LLM explanation only. The page is one self-contained HTML file, like `console.html`, rendering what the API returns; the developer console moves to `/console`.

**Tech Stack:** Python 3.12, Pydantic v2, FastAPI, Typer, pytest; plain HTML/CSS/JS with no build step.

**Spec:** `docs/superpowers/specs/2026-10-28-methodos-user-interface-design.md`

## Global Constraints

- English throughout — UI copy and method content.
- The page is one file shipped in the package (`src/methodos/app.html`): no build step, no external requests — no `http://`, `https://` or `src=` in the file.
- The page holds no ranking logic; `api.py` and `mcp_server.py` stay thin translators over `mcp_tools`.
- The MCP server never calls the LLM.
- No raw scores (`similarity`, `rerank_score`) in the main view; only behind a "Details" disclosure.
- One `/query` call per problem; never two (each call logs a recommendation).
- Feedback stays in the existing JSONL; no new store. Existing lines without `aspect` read as `"application"`.
- History lives in `localStorage` only; the page must work fully when storage throws.
- The "already done" text reaches the LLM prompt only — never the ranking, never the feedback JSONL.
- `methods/*.json` and `schemas/method_schema.json` are not touched.
- `CLAUDE.md` hard rules apply (lazy imports, `make test` / `make lint` green).

## Review Focus

1. **LLM slow or failing** — user sees the ranking with a calm "explanation unavailable" note, never a blank page or spinner forever. → Task 6, Step 5 (manual) + existing `test_a_failing_llm_leaves_the_ranking_intact`.
2. **Storage unavailable** (private window, blocked site data) — page works, history simply absent. → Task 7, Step 1 (`test_app_reaches_storage_only_through_the_guarded_helper`).
3. **A method's Markdown missing a section or malformed** — `/methods/{id}` still 200, that part empty. → Task 1, Step 1 (`test_missing_sections_degrade_to_empty`).
4. **User text containing markup or template braces** (`<script>`, `{query}`) in problem or already-done — rendered as text, prompt not corrupted. → Task 4, Step 1 (`test_already_done_with_braces_is_inserted_verbatim`) + Task 6, Step 1 (`test_app_escapes_server_text`).
5. **Weak or empty match** (`guidance` set, `matches` empty) — guidance shown prominently; no "Start applying" offered for nothing. → Task 6, Step 5 (manual).

---

### Task 1: Parse method guidance from Markdown

**Files:**
- Create: `src/methodos/guide.py`
- Test: `tests/test_guide.py`

**Interfaces:**
- Produces (all Pydantic `BaseModel`s in `methodos.guide`):
  - `GuideStep(text: str, time_box: str | None)`
  - `SeeAlsoLink(label: str, method_id: str | None, url: str | None, note: str | None)` — exactly one of `method_id` / `url` is set.
  - `MethodGuide(outline_duration: str | None, steps: list[GuideStep], not_a_fit_when: list[str], pitfalls: list[str], see_also: list[SeeAlsoLink])`
  - `parse_guide(markdown: str) -> MethodGuide` — pure, never raises on content.

Source format (identical in all 23 files): sections `## When *not* to use`, `## Facilitation outline (<duration>)`, `## Common pitfalls`, `## See also`. Outline items are `N. ` numbered, optionally starting with a time box `(5 min)`; continuation lines are indented and belong to the previous item. Bullets are `- `. See-also items are `- [Label](Target) — note`; a target ending in `.md` is a method id (strip `.md`), anything else is a URL.

- [ ] **Step 1: Write the failing tests**

```python
FIVE_WHYS_LIKE = """# X

## When *not* to use

- When several causes contributed — use an [Ishikawa diagram](Ishikawa_Diagram.md)
- For problems nobody has first-hand knowledge of

## Facilitation outline (45 min)

1. (5 min) Write the failure as one factual sentence.
2. (25 min) Ask why. Write the answer.
   Each link must be supported with evidence.
3. Assign one owner.

## Common pitfalls

- Ending at "human error"

## See also

- [Ishikawa (Fishbone) Diagram](Ishikawa_Diagram.md) — when the failure has several causes
- [Wikipedia: Five whys](https://en.wikipedia.org/wiki/Five_whys)
"""

def test_steps_keep_time_box_and_join_continuation_lines():
    g = parse_guide(FIVE_WHYS_LIKE)
    assert g.outline_duration == "45 min"
    assert [s.time_box for s in g.steps] == ["5 min", "25 min", None]
    assert g.steps[1].text == "Ask why. Write the answer. Each link must be supported with evidence."
    assert g.steps[2].text == "Assign one owner."

def test_bullet_sections_are_parsed():
    g = parse_guide(FIVE_WHYS_LIKE)
    assert len(g.not_a_fit_when) == 2
    assert g.pitfalls == ['Ending at "human error"']

def test_see_also_separates_methods_from_urls():
    g = parse_guide(FIVE_WHYS_LIKE)
    assert g.see_also[0].method_id == "Ishikawa_Diagram" and g.see_also[0].url is None
    assert g.see_also[0].note == "when the failure has several causes"
    assert g.see_also[1].method_id is None and g.see_also[1].url.startswith("https://")

def test_missing_sections_degrade_to_empty():
    g = parse_guide("# Only a title\n\nSome prose.\n")
    assert g == MethodGuide(outline_duration=None, steps=[], not_a_fit_when=[], pitfalls=[], see_also=[])

def test_every_shipped_method_yields_usable_guidance():
    ids = {p.stem for p in METHODS_DIR.glob("*.json")}
    for md in METHODS_DIR.glob("*.md"):
        g = parse_guide(md.read_text(encoding="utf-8"))
        assert len(g.steps) >= 3, md.name
        assert g.not_a_fit_when and g.pitfalls and g.see_also, md.name
        assert g.outline_duration, md.name
        for link in g.see_also:
            assert link.method_id is None or link.method_id in ids, (md.name, link.method_id)
```

`METHODS_DIR` = repo-root `methods/` resolved from the test file (`Path(__file__).parent.parent / "methods"`).

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_guide.py -v`
Expected: FAIL — `ModuleNotFoundError: methodos.guide`

- [ ] **Step 3: Implement the models and `parse_guide(markdown: str) -> MethodGuide` in `src/methodos/guide.py`**

Split on `^## ` headings with `re`; match the heading by prefix (`When *not* to use`, `Facilitation outline`, `Common pitfalls`, `See also`) so the outline's `(<duration>)` suffix is captured as `outline_duration`. Time box = a leading `(…)` on a step. Whitespace-join continuation lines. Module docstring states the source format above and that parsing never raises.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_guide.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add src/methodos/guide.py tests/test_guide.py
git commit -m "Parse method guidance from the Markdown companions"
```

---

### Task 2: Expose guidance on `MethodDetail`

**Files:**
- Modify: `src/methodos/mcp_tools.py` (`MethodDetail`, `get_method`)
- Test: `tests/test_mcp_tools.py`, `tests/test_api.py`

**Interfaces:**
- Consumes: `parse_guide`, `MethodGuide` from Task 1.
- Produces: `MethodDetail.guide: MethodGuide` (new field, after `documentation`; `documentation` unchanged). Served by `GET /methods/{id}` and the MCP `get_method` tool without further change.

- [ ] **Step 1: Write the failing tests**

In `tests/test_mcp_tools.py`:
```python
def test_get_method_includes_parsed_guide_for_a_shipped_method():
    d = get_method(method_id="Five_Whys", methods_dir=REPO_METHODS)
    assert [s.time_box for s in d.guide.steps] == ["5 min", "25 min", "10 min", "5 min"]
    assert any(l.method_id == "Ishikawa_Diagram" for l in d.guide.see_also)
    assert "Facilitation outline" in d.documentation
```
`REPO_METHODS = Path(__file__).parent.parent / "methods"` (reuse if the file already defines one).
In `tests/test_api.py`, extend `test_methods_endpoints_serve_the_catalog_and_the_markdown`:
```python
    assert detail["guide"]["steps"] == []  # tmp fixture docs have no sections
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_mcp_tools.py tests/test_api.py -v -k "guide or methods_endpoints"`
Expected: FAIL — `MethodDetail` has no attribute `guide` / `KeyError: 'guide'`

- [ ] **Step 3: Add `guide: MethodGuide = Field(description=...)` to `MethodDetail` and fill it in `get_method` from the text already read for `documentation`**

Read the file once; pass the same string to both fields. Field description: "Steps, not-a-fit-when, pitfalls and see-also parsed from `documentation`; empty where a section is missing."

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_mcp_tools.py tests/test_api.py tests/test_mcp_server.py -v`
Expected: all pass

- [ ] **Step 5: Commit**

```bash
git add src/methodos/mcp_tools.py tests/test_mcp_tools.py tests/test_api.py
git commit -m "Expose parsed method guidance on MethodDetail"
```

---

### Task 3: Feedback aspect (recommendation vs application)

**Files:**
- Modify: `src/methodos/feedback.py`, `src/methodos/api.py` (`FeedbackRequest`, `MethodStatsEntry`, `feedback`, `stats`), `src/methodos/cli.py` (`feedback`, `stats_cmd`)
- Test: `tests/test_feedback.py`, `tests/test_api.py`, `tests/test_cli.py`

**Interfaces:**
- Produces:
  - `feedback.Aspect = Literal["recommendation", "application"]`
  - `RatingEvent.aspect: Aspect = "application"`
  - `log_rating(*, method_id, rating, note, query_id, path, aspect: Aspect = "application") -> None`
  - `MethodStats`: `rating_count` / `rating_sum` / `avg_rating` now count **application** ratings only; new `recommendation_rating_count: int = 0`, `recommendation_rating_sum: int = 0`, property `avg_recommendation_rating: float` (0.0 when none).
  - `FeedbackRequest.aspect: Aspect = "application"`; `FeedbackResponse` shape unchanged.
  - `MethodStatsEntry` adds `recommendation_rating_count: int` and `avg_recommendation_rating: float | None` (null until rated).
  - CLI: `methodos feedback ID -r N --aspect {recommendation|application}` (default `application`); `stats` table adds columns "Fit rated" and "Avg fit".

- [ ] **Step 1: Write the failing tests**

In `tests/test_feedback.py`:
```python
def test_lines_without_aspect_read_as_application(tmp_path):
    fb = tmp_path / "fb.jsonl"
    fb.write_text('{"event":"rating","timestamp":"2026-01-01T00:00:00Z","query_id":null,'
                  '"method_id":"SWOT","rating":4,"note":null}\n', encoding="utf-8")
    (ev,) = list(read_events(fb))
    assert ev.aspect == "application"

def test_stats_keep_the_two_aspects_apart(tmp_path):
    fb = tmp_path / "fb.jsonl"
    log_rating(method_id="SWOT", rating=2, note=None, query_id=None, path=fb)
    log_rating(method_id="SWOT", rating=5, note=None, query_id=None, path=fb, aspect="recommendation")
    s = stats(fb)["SWOT"]
    assert (s.rating_count, s.avg_rating) == (1, 2.0)
    assert (s.recommendation_rating_count, s.avg_recommendation_rating) == (1, 5.0)
```
In `tests/test_api.py`:
```python
def test_recommendation_feedback_is_reported_separately(env):
    client = env["client"]
    qid = client.post("/query", json={"problem": "alpha"}).json()["query_id"]
    assert client.post("/feedback", json={"method_id": "Alpha", "rating": 4, "query_id": qid,
                                          "aspect": "recommendation"}).status_code == 200
    e = {x["method_id"]: x for x in client.get("/stats").json()["entries"]}["Alpha"]
    assert e["recommendation_rating_count"] == 1 and e["avg_recommendation_rating"] == 4.0
    assert e["rating_count"] == 0 and e["avg_rating"] is None

def test_unknown_aspect_is_rejected(env):
    assert env["client"].post("/feedback", json={"method_id": "Alpha", "rating": 3,
                                                 "aspect": "vibes"}).status_code == 422
```
In `tests/test_cli.py`: `feedback SWOT -r 4 --aspect recommendation` writes a line with `"aspect": "recommendation"`; without `--aspect` the line has `"aspect": "application"`. Follow the file's existing invocation pattern for `feedback`.

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_feedback.py tests/test_api.py tests/test_cli.py -v -k "aspect or recommendation"`
Expected: FAIL

- [ ] **Step 3: Implement the interfaces above**

Thread `aspect` from `FeedbackRequest` and the CLI option into `log_rating`. CLI help text for `feedback` changes from "Record an outcome rating" to say both moments.

- [ ] **Step 4: Run the full fast suite**

Run: `pytest`
Expected: all pass (existing `test_feedback_round_trip_reaches_stats` and `test_stats_aggregates` unchanged and green)

- [ ] **Step 5: Commit**

```bash
git add src/methodos/feedback.py src/methodos/api.py src/methodos/cli.py tests/test_feedback.py tests/test_api.py tests/test_cli.py
git commit -m "Record whether a rating is about the recommendation or the application"
```

---

### Task 4: "Already done" reaches the explanation, nothing else

**Files:**
- Modify: `src/methodos/prompts/explain.txt`, `src/methodos/prompts/loader.py` (`render_explain_prompt`), `src/methodos/search.py` (`explain`), `src/methodos/api.py` (`QueryRequest`, `query`)
- Test: `tests/test_prompts.py`, `tests/test_api.py`

**Interfaces:**
- Produces:
  - `render_explain_prompt(*, query, candidates, already_done: str | None = None) -> str`
  - `explain(*, query, candidates, llm, already_done: str | None = None) -> str`
  - `QueryRequest.already_done: str | None = Field(default=None, max_length=2000, description=...)`
  - Template placeholder `{already_done_block}` in `explain.txt`, on its own line between the problem block and "Candidate methods".

Block text when set (exact copy):
```
What the user has already done:
"""
<already_done>
"""
Take this into account: do not recommend repeating it without a reason, and say when a candidate is a sensible next step after it.
```
When `None` or blank, the placeholder renders as an empty string.

- [ ] **Step 1: Write the failing tests**

In `tests/test_prompts.py`:
```python
def test_no_already_done_block_when_absent():
    out = render_explain_prompt(query="q", candidates=[CAND])
    assert "already done" not in out and "{already_done_block}" not in out

def test_already_done_with_braces_is_inserted_verbatim():
    out = render_explain_prompt(query="q", candidates=[CAND], already_done="Ran Five_Whys {query}")
    assert "What the user has already done:" in out
    assert "Ran Five_Whys {query}" in out
```
(`CAND` = the candidate dict the file already uses; reuse it.)

In `tests/test_api.py`:
```python
def test_already_done_reaches_the_llm_but_not_the_ranking_or_the_log(env):
    client, llm = env["client"], env["llm"]
    plain = client.post("/query", json={"problem": "alpha beta"}).json()
    ctx = client.post("/query", json={"problem": "alpha beta",
                                      "already_done": "Ran SECRET_MARKER last week"}).json()
    assert [m["id"] for m in ctx["matches"]] == [m["id"] for m in plain["matches"]]
    assert "SECRET_MARKER" in llm.calls[-1][1]
    assert "SECRET_MARKER" not in env["settings"].feedback_path.read_text(encoding="utf-8")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_prompts.py tests/test_api.py -v -k "already_done"`
Expected: FAIL

- [ ] **Step 3: Implement the interfaces above**

Use `.replace` as the loader already does (format-injection safe). In `api.query`, pass `req.already_done` to `explain` only.

- [ ] **Step 4: Run the full fast suite**

Run: `pytest`
Expected: all pass

- [ ] **Step 5: Commit**

```bash
git add src/methodos/prompts/ src/methodos/search.py src/methodos/api.py tests/test_prompts.py tests/test_api.py
git commit -m "Let the user's prior work inform the explanation"
```

---

### Task 5: Routes — new page at `/`, console at `/console`

**Files:**
- Create: `src/methodos/app.html` (placeholder: valid self-contained page titled `Methodos`, body "Coming soon" — Task 6 replaces it)
- Modify: `src/methodos/api.py` (add `APP_HTML`, routes), `README.md` (endpoint table)
- Test: `tests/test_api.py`

**Interfaces:**
- Produces: `GET /` → `APP_HTML = Path(__file__).parent / "app.html"`; `GET /console` → existing `CONSOLE_HTML`. Both `include_in_schema=False`.

- [ ] **Step 1: Write the failing tests**

Rename `test_console_is_served_and_self_contained` to request `/console`, unchanged assertions. Add:
```python
def test_app_is_served_at_root_and_self_contained(env):
    html = env["client"].get("/").text
    assert "<title>Methodos</title>" in html
    assert "http://" not in html and "https://" not in html
    assert "src=" not in html
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_api.py -v -k "console or app_is"`
Expected: FAIL (`/console` 404; `/` returns the console title)

- [ ] **Step 3: Add the placeholder page and both routes; update the README table**

README rows: `GET /` → "The Methodos page — describe a problem, pick a method, apply it step by step"; `GET /console` → the old console description.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_api.py -v`
Expected: all pass

- [ ] **Step 5: Commit**

```bash
git add src/methodos/app.html src/methodos/api.py README.md tests/test_api.py
git commit -m "Serve the user page at / and move the developer console to /console"
```

---

### Task 6: The page — describe and choose

**Files:**
- Modify: `src/methodos/app.html`
- Test: `tests/test_api.py`

**Interfaces:**
- Consumes: `POST /query` (`problem`, `already_done`; `top_k` fixed at 5; `explain: true`), response fields `matches`, `guidance`, `explanation`, `explanation_error`, `query_id`; `GET /methods/{id}` → `guide`; `POST /feedback` with `aspect: "recommendation"`.
- Produces (DOM ids Task 7 relies on): `#problem`, `#already-done`, `#results`, `#method` (selected-method panel), `#apply` (empty container Task 7 fills), `#history` (empty container Task 7 fills). JS globals: `state = { queryId, matches, selectedId, guide }`, `esc(s)`, `api(path, opts)` (same contract as in `console.html`), `selectMethod(id)`.

No developer controls on this page: no `top_k` input, no rerank toggle, no LLM test button, no raw JSON. Layout per spec "Visual direction" and flow stages 1–2: workspace, light default with `prefers-color-scheme` dark tokens, monospace micro-labels, ranked list with bars (bar width = rank-relative; raw `similarity`/`rerank_score` only inside a `<details>` "Details"), "Why this method?" panel with the explanation text (escaped, newlines → `<br>`), stat tiles for the selected method (duration `duration_min–duration_max min`, effort `●○○○○` from `complexity_score`, number of steps from `guide.steps.length`), "Not a fit when…" and "Consider instead" (internal `see_also` links call `selectMethod` only if that id is in `state.matches`, else render as plain text with the label), "Does this fit your problem?" 1–5 → `/feedback` with the **selected** method id and `aspect: "recommendation"`, then replaced by "Thanks". A calm waiting state ("Finding methods for your problem… this can take a few seconds") while `/query` runs; submit disabled meanwhile. `guidance` shown above the list as a prominent note. If `explanation_error`, the panel reads "The explanation is unavailable right now — the ranking above is complete." If `matches` is empty, no method panel and no "Start applying".

- [ ] **Step 1: Write the failing tests**

```python
def test_app_talks_to_the_api_contract(env):
    html = env["client"].get("/").text
    for needle in ['"/query"', "/methods/", '"/feedback"', '"recommendation"',
                   'id="problem"', 'id="already-done"', 'id="apply"', 'id="history"']:
        assert needle in html, needle

def test_app_escapes_server_text(env):
    html = env["client"].get("/").text
    assert "function esc(" in html or "const esc" in html
```
Every server- or user-supplied string inserted via `innerHTML` goes through `esc()`; the manual check in Step 5 confirms it.

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_api.py -v -k "app_talks or app_escapes"`
Expected: FAIL

- [ ] **Step 3: Build stages 1–2 in `app.html`**

Header comment in the same voice as `console.html`'s: one self-contained file, no egress, no ranking logic.

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_api.py -v`
Expected: all pass

- [ ] **Step 5: Verify in a browser**

Run `make ingest` then `make serve`; open `http://127.0.0.1:8000/`. Check:
- "tickets take six weeks end to end but the actual work is only a few hours" → ranked list with bars, no raw numbers outside "Details".
- With no LLM key configured: ranking shows, explanation panel shows the unavailable note (Review Focus 1).
- "how do I fix my bicycle chain" → guidance note visible above a weak list (Review Focus 5).
- Problem text `<b>x</b>` renders literally.
- Clicking another method updates tiles, not-a-fit and consider-instead without a new `/query` (network tab: one `/query`).
- Rating "Does this fit" → the configured feedback JSONL (`Settings.feedback_path`) gains a line with `"aspect":"recommendation"` and the selected method id.

- [ ] **Step 6: Commit**

```bash
git add src/methodos/app.html tests/test_api.py
git commit -m "Build the describe-and-choose stages of the user page"
```

---

### Task 7: The page — apply, history, outcome feedback

**Files:**
- Modify: `src/methodos/app.html`
- Test: `tests/test_api.py`

**Interfaces:**
- Consumes: Task 6's DOM ids, `state`, `esc`, `api`, `selectMethod`; `POST /feedback` with `aspect: "application"`; `GET /methods/{id}` for the latest history entry's `guide.see_also`.
- Produces: storage helpers `loadHistory() -> Entry[]` and `saveHistory(entries)`, the **only** code that touches `localStorage`, each wrapped in `try/catch` returning `[]` / no-op on failure. Key `"methodos.history.v1"`. `Entry = { queryId, methodId, methodName, date /* ISO */, problem, stepsDone /* number[] of step indexes */, stepsTotal, feedbackGiven /* bool */ }`. Keep the newest 20; show the newest 3.

Behaviour per spec stage 3 and "History":
- "Start applying" on the selected method → `#apply` shows `guide.steps` as a checklist (all visible, current step highlighted), each with its `time_box`, a segmented progress track (done / current / remaining), and pitfalls in a `<details>`. Starting creates a history entry; each check updates `stepsDone`.
- After the last step (or a "Finish" button), show "Did the method help?" 1–5 plus an optional note → `/feedback` with `aspect: "application"`, the entry's `queryId` and `methodId`; set `feedbackGiven`.
- On load, `#history` shows recent entries with "Use this" (fills `#already-done` with e.g. `"Ran Five Whys on 2026-10-30 (3 of 4 steps): <problem>"`) and "Remove". If the newest entry has `feedbackGiven === false`, show "How did <methodName> go?" with the same 1–5 + note form first.
- "Possible next steps": internal `see_also` links of the newest entry's method (from `GET /methods/{methodId}`), shown as labels near the problem field.

- [ ] **Step 1: Write the failing tests**

```python
def test_app_reaches_storage_only_through_the_guarded_helper(env):
    html = env["client"].get("/").text
    assert html.count("localStorage") == 2  # one getItem in loadHistory, one setItem in saveHistory
    assert "methodos.history.v1" in html
    assert html.count("try") >= 2

def test_app_sends_outcome_feedback(env):
    assert '"application"' in env["client"].get("/").text
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_api.py -v -k "storage or outcome"`
Expected: FAIL

- [ ] **Step 3: Build stage 3 and history in `app.html`**

- [ ] **Step 4: Run the fast suite and lint**

Run: `pytest` then `make lint` (on Windows without make: `ruff check src tests scripts`, `ruff format --check src tests scripts`, `mypy src/methodos`)
Expected: all pass, no lint errors

- [ ] **Step 5: Verify in a browser**

With `make serve` running:
- Choose a method, "Start applying", check two steps → progress track reflects it; reload → the history entry shows "2 of N steps".
- Finish → outcome form → JSONL gains `"aspect":"application"` with the same `query_id` as the recommendation line.
- Reload → no "How did … go?" prompt for that entry. Start another method and reload without finishing → the prompt appears.
- "Use this" fills the already-done field; submitting sends `already_done` (network tab) and the ranking order is identical to a query without it.
- DevTools → block site data / private window → page loads, querying and applying work, history section is simply empty (Review Focus 2).

- [ ] **Step 6: Commit**

```bash
git add src/methodos/app.html tests/test_api.py
git commit -m "Add guided application, device-local history and outcome feedback"
```
