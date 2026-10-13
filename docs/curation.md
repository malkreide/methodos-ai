# Keeping the catalog current

One owner, a growing catalog, and agents doing the legwork. The split:

| Step | Who | How |
|---|---|---|
| Find what needs work | script | `scripts/audit_catalog.py` — deterministic, reproducible |
| Find where search misses | script | `scripts/audit_search.py` — everyday problems against the shipped ranking |
| Fix existing entries | agent | `.claude/agents/method-curator.md` |
| Add proposed methods | agent | `.claude/agents/method-author.md`, fed by the "Propose a method" issue form or the console's proposal inbox |
| Review and publish | owner | merge the draft PR — **the merge is the review** |

The agents never merge. Everything they do arrives as a small draft pull
request with its sources listed, validated by the same tests a human
contribution has to pass, including the English and German retrieval probes.

## Audit findings

```bash
python scripts/audit_catalog.py                 # Markdown table
python scripts/audit_catalog.py --json          # what the agent reads
python scripts/audit_catalog.py --check-links   # also checks every reference URL
```

`low-rating` > `never-reviewed` / `stale` (older than 365 days) > `broken-link` >
`unclassified` > `single-use-case` > `no-owner`. Rating signals are read from
`data/feedback.jsonl` when it exists; point `--feedback` at a production log to
use real ratings.

## Search gaps

```bash
python scripts/audit_search.py              # one line per problem, top-1 / top-3 at the end
python scripts/audit_search.py --diagnose   # where each miss sits, by embedding and by reranker
```

`scripts/search_queries.json` holds problems phrased the way a school leader
or an office would type them, each with the methods that would be a right
answer. A miss whose method is *in* the shortlist but demoted by the reranker
means its texts do not describe that problem: add a `use_cases` line in the
problem's words, then run the script again and confirm that nothing else moved.
Write a second phrasing you did not use while writing the line, and check that
too — the first one is no longer a fair test.

`scripts/search_queries_holdout.json` is that second phrasing, kept for the
whole catalog: problems written before any use case aimed at them. Never write
a use case while looking at it; report its numbers next to the main file's, and
treat a gain on the main file that the holdout does not share as tuning to the
test. Once a holdout entry has been used to shape a text, move it to the main
file and write a fresh one.

Both of those files were still written by the people who write the use cases.
`scripts/search_queries_holdout_log.json` is not: it holds problems people
actually typed into the console, taken from `feedback.jsonl` with
`scripts/holdout_from_log.py` in two steps, with a person in between.

```bash
python scripts/holdout_from_log.py extract /data/feedback.jsonl /tmp/draft.json
# a person edits the draft: anonymises, fills acceptable and goal, sets keep
python scripts/holdout_from_log.py add /tmp/draft.json
python scripts/audit_search.py --queries scripts/search_queries_holdout_log.json
```

The repository is public and the log is not, so the person reviewing rewrites
every problem until nobody can be recognised; `add` refuses e-mail addresses,
phone numbers, links and salutations with a name, and asks for
`names_checked: true` where it suspects a name. They fill `acceptable` from the
catalog, not from the ranking — the draft deliberately leaves out what search
returned, or the benchmark would measure the ranking against itself. The same
rule applies as for the other holdout: never write a use case while looking at
it.

What has worked: a short use case in the voice of the person with the problem
("We keep starting new projects but rarely finish or stop any…"). The longer
third-person scenarios that most entries carry describe the method's setting
well, but the reranker matches a typed problem to a stated problem.

## Running the agents

Locally, in Claude Code:

```
> Use the method-curator agent to work through the audit.
> Use the method-author agent on issue #42.
```

Unattended, as a Claude Code routine on claude.ai (weekly is plenty for one
reviewer). The prompt only has to name the agent; the agent file carries the
rules:

```
Run the method-curator agent on this repository and open its draft PR.
```

A new "Propose a method" issue can be handed to `method-author` the same way.

## Proposals from the console

Most people who know a good method have no GitHub account. The console's
*Propose a method* tab (`POST /proposals`) takes the same fields as the issue
form — name, problem, how it works, sources, links, contexts — and:

- appends them to `proposals.jsonl` next to `feedback.jsonl`
  (`METHODOS_PROPOSALS_PATH`; `/data/proposals.jsonl` in the container),
  together with the three closest methods the search found at the time;
- hands back a prefilled link to the issue form, for whoever does have an
  account (`METHODOS_ISSUE_REPO`, empty to turn it off). The server holds no
  GitHub token and never posts anything itself.

The tab can also start from a file — a PDF handout, a Word document, a
recording of a workshop (`POST /proposals/extract`). The file is read or
transcribed on the server, deleted, and its text turned into a draft that
prefills the form; see [Uploads](../README.md#uploads). The proposal that
arrives in the inbox then carries `extracted_from` (`pdf`, `docx`, `text`,
`audio`, `video`). Read those with extra care: names and sources went through
a speech or PDF reader and an LLM before the person checked them.

Nothing is published: links point to the source, the inbox is read by the
owner, and the catalog changes only through the same draft PR as above.

```
> Use the method-author agent on proposal 01M46PM47V7B0AW5J0FQV2HDC7 from data/proposals.jsonl.
```

In the container the inbox lives in the `methodos-data` volume:
`docker compose cp methodos:/data/proposals.jsonl data/`.

## Why the owner stays in the loop

- **Provenance.** The catalog is public and commercially used; copied prose or
  a wrong attribution is a liability the owner carries, not the agent.
- **Search quality.** A new `use_cases` line can pull queries away from a
  neighbouring method. The probes catch the pinned cases, not all of them.
- **`last_reviewed` has to mean something.** It is set by the agent and made
  true by the merge.
