# Keeping the catalog current

One owner, a growing catalog, and agents doing the legwork. The split:

| Step | Who | How |
|---|---|---|
| Find what needs work | script | `scripts/audit_catalog.py` — deterministic, reproducible |
| Fix existing entries | agent | `.claude/agents/method-curator.md` |
| Add proposed methods | agent | `.claude/agents/method-author.md`, fed by the "Propose a method" issue form |
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

## Why the owner stays in the loop

- **Provenance.** The catalog is public and commercially used; copied prose or
  a wrong attribution is a liability the owner carries, not the agent.
- **Search quality.** A new `use_cases` line can pull queries away from a
  neighbouring method. The probes catch the pinned cases, not all of them.
- **`last_reviewed` has to mean something.** It is set by the agent and made
  true by the merge.
