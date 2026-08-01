# Wardley Mapping

Anchor on a user need, draw the chain of components it depends on, then place
each component by how evolved it is. The vertical axis is visibility to the
user; the horizontal axis is evolution.

```
visible   │ user need
          │   └── component
          │         └── component
invisible │               └── commodity
          └─────────────────────────────────
            genesis  custom  product  commodity
```

## When to use

- Build versus buy versus outsource, argued with a picture instead of opinions
- Several teams appear to be reinventing the same capability
- The roadmap keeps funding components the market already commoditised

## When *not* to use

- Short-horizon or single-team decisions; the overhead will not pay back
- Without someone who has drawn maps before — a first map is usually wrong
- As a one-off artifact; unmaintained maps mislead as components evolve

## Facilitation outline (a day, expect to redraw)

1. (30 min) Name the user and the need. Not the system, the *need*.
2. (90 min) Chain the components each need depends on, down to the invisible ones.
3. (90 min) Place each component on the evolution axis. Argue. The argument is the value.
4. (60 min) Mark movement: which components are evolving right, and how fast.
5. (60 min) Decide per component: build, buy, or outsource. Record the reasoning.

## Common pitfalls

- Mapping the org chart instead of the value chain
- Treating the evolution axis as a maturity score for your own implementation
- Stopping at the picture without step 5
- Defending a first map instead of redrawing it

## See also

- [Business Model Canvas](Business_Model_Canvas.md) — the commercial logic the map serves
- [Scenario Planning](Scenario_Planning.md) — for uncertainty the evolution axis doesn't capture
- [Learn Wardley Mapping](https://learnwardleymapping.com/)
