# Value Stream Mapping

Draw every step from request to delivery, and write two numbers on each: time
spent working, and time spent waiting. The gap between them is the finding.

```
process time     Σ hands-on work
──────────── =   ───────────────   often a small fraction where work queues between teams
  lead time      request → delivery
```

## When to use

- Lead time is the complaint: "this takes six weeks and it's four hours of work"
- Work crosses several teams and nobody owns the end-to-end duration
- Before automating a step — you may be speeding up something that isn't the bottleneck
- Public services and administration: permit applications or enforcement cases that
  take months between desks. Agencies run it as a two-to-four-day mapping event (EPA)
- Student-facing processes in schools and universities, such as admissions or academic
  advising, where requests stall between offices

## When *not* to use

- Inside a single team with an already-short cycle time
- To find *why* a step is slow; that is [Five Whys](Five_Whys.md) or [Ishikawa](Ishikawa_Diagram.md)
- When nobody can observe the real flow or pull timings from ticket history.
  Rough figures are enough (hours versus days); invented ones are not

## Facilitation outline (1–2 days)

1. Pick one work item type and follow real instances of it. Not the idealised process.
2. Walk the flow physically or through the ticket history. Record every hand-off.
3. Write process time and waiting time on each step, from observation or records, not
   memory. Order-of-magnitude precision is enough; don't stall the map chasing exact numbers.
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
- [DORA: Value stream mapping for software delivery](https://dora.dev/guides/value-stream-management/) — commit-to-production maps, wait times and hand-offs
- [US EPA: Lean Government Methods Guide (PDF)](https://www.epa.gov/sites/default/files/2014-01/documents/lean-methods-guide.pdf) — value stream mapping events in government agencies
- [US EPA and ECOS: Lean in Air Permitting Guide (PDF)](https://www.epa.gov/sites/default/files/2013-11/documents/lean-in-air-permitting-guide_0.pdf) — current- and future-state maps of state permit processes
- [Fisher, Barman and Killingsworth (2011)](https://www.inderscience.com/info/inarticle.php?artid=37919), International Journal of Information and Operations Management Education 4(1), doi:10.1504/IJIOME.2011.037919 — mapping academic advising
- [M State: Value Stream Mapping the Admissions Process](https://www.minnesota.edu/about/institutional-effectiveness/project-charters/value-stream-mapping-admissions-process-prospect) — a college's admissions pipeline
