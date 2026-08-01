# RICE Scoring

Rank competing items by a single computed score, so the ordering can be
inspected and argued with rather than asserted.

```
        Reach × Impact × Confidence
RICE =  ──────────────────────────
                 Effort
```

| Term | Unit | Meaning |
|---|---|---|
| **R**each | people or events per period | how many are affected, in a real counted unit |
| **I**mpact | 3 / 2 / 1 / 0.5 / 0.25 | massive → minimal, per affected person |
| **C**onfidence | 100% / 80% / 50% | how much evidence stands behind Reach and Impact |
| **E**ffort | person-months | total across every discipline, not just engineering |

## When to use

- More candidate work than capacity, and stakeholders each favour their own item
- The ordering will be questioned later and needs to be reconstructable
- Comparing items of genuinely different shapes and sizes

## When *not* to use

- Strategic bets whose value is not countable — the score will be theatre
- Work with hard dependencies or sequencing constraints; RICE ignores order
- Small teams with three obvious priorities; the overhead outweighs the insight

## Facilitation outline (2–4 hours)

1. (20 min) Agree the Reach unit and the time period. Write them down.
2. (60 min) Score each item together. Whoever proposes a number states its basis.
3. (30 min) Sort by score. Read the ordering aloud.
4. (30 min) Ask where the order feels wrong — that usually means a hidden factor
   the model doesn't capture. Record it rather than quietly fudging a number.

## Common pitfalls

- Estimating Reach in different units across items, making scores incomparable
- Setting Confidence to 100% because the item is a favourite
- Counting only engineering in Effort, so design- and support-heavy work looks cheap
- Treating the resulting order as binding when step 4 raised a real objection

## See also

- [MoSCoW Prioritization](MoSCoW_Method.md) — when the constraint is a deadline, not a ranking
- [DACI Decision-Making Framework](DACI_Matrix.md) — for who decides once the scores are in
- [Intercom: RICE](https://www.intercom.com/blog/rice-simple-prioritization-for-product-managers/)
