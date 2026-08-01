# Value Stream Mapping

Draw every step from request to delivery, and write two numbers on each: time
spent working, and time spent waiting. The gap between them is the finding.

```
process time     Σ hands-on work
──────────── =   ───────────────   typically 5–15% in knowledge work
  lead time      request → delivery
```

## When to use

- Lead time is the complaint: "this takes six weeks and it's four hours of work"
- Work crosses several teams and nobody owns the end-to-end duration
- Before automating a step — you may be speeding up something that isn't the bottleneck

## When *not* to use

- Inside a single team with an already-short cycle time
- To find *why* a step is slow; that is [Five Whys](Five_Whys.md) or [Ishikawa](Ishikawa_Diagram.md)
- Without access to real timing data; a mapped guess is worse than no map

## Facilitation outline (1–2 days)

1. Pick one work item type and follow real instances of it. Not the idealised process.
2. Walk the flow physically or through the ticket history. Record every hand-off.
3. Write process time and waiting time on each step, from data, not memory.
4. Compute total lead time and the process-time ratio.
5. Mark the largest queues. Those, not the slowest steps, are the target.
6. Draw a future-state map and name the one change worth making first.

## Common pitfalls

- Mapping the documented process rather than what actually happens
- Optimising a step that has no queue in front of it
- Treating the map as permanent when the process changes monthly
- Stopping at the current-state map without step 6

## See also

- [Ishikawa (Fishbone) Diagram](Ishikawa_Diagram.md) — for why a specific step is slow
- [RICE Scoring](RICE_Scoring.md) — to rank the improvements the map surfaces
- [Lean Enterprise Institute: Value-Stream Mapping](https://www.lean.org/lexicon-terms/value-stream-mapping/)
