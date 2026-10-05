# Cost of Delay / WSJF (Weighted Shortest Job First)

When everything is "urgent", the word stops carrying information. Cost of Delay
asks a sharper question of each item: *what do we lose for every week this is
not delivered?* Sequencing by that loss divided by how long the item ties up the
team — Weighted Shortest Job First — puts first the work whose waiting is most
expensive relative to its length.

```
                 cost of delay  (value lost per week of waiting)
CD3 / WSJF  =  ─────────────────────────────────────────────────
                 duration       (weeks the item occupies the team)
```

Cost of Delay as a decision tool was championed by Don Reinertsen, most fully in
*The Principles of Product Development Flow* (2009), where it is the economic
quantity that lets queues, batch sizes and capacity be traded against each
other. Dividing it by duration is often called CD3 (Cost of Delay Divided by
Duration). The Scaled Agile Framework (SAFe) later made a simplified,
relative-score version widely known under the name WSJF; see *When not to use*.

## Why the division matters

Three items, one team, value lost until each one ships:

| Item | Cost of delay | Duration | CoD ÷ duration |
|---|---|---|---|
| A — new reporting module | 10,000 / week | 4 weeks | 2.5 |
| B — fix a failing data import | 4,000 / week | 1 week | 4.0 |
| C — form needed for a funding round | 6,000 / week | 2 weeks | 3.0 |

Doing the most valuable item first (A, B, C) loses 40k + 20k + 42k = 102k while
items wait. Doing the highest ratio first (B, C, A) loses 4k + 18k + 70k = 92k.
Short, time-sensitive work done early stops bleeding sooner, and the large item
loses comparatively little by starting a few weeks later. The numbers are
illustrative; the shape of the result is the point.

## When to use

- Many requests compete for one team or budget and each sponsor calls theirs urgent
- Some items have a real clock — a legal deadline, a season, a contract penalty,
  expiring funding — and others do not, but the queue treats them alike
- Public bodies and schools too: change requests tied to a law entering into
  force or to the first day of term lose value in a way that can be stated
- A portfolio keeps starting large projects first and wants to test whether
  finishing short, time-critical work earlier would lose less overall

## When *not* to use

- **When the inputs are pure guesswork.** Cost of delay is an estimate of value
  over time and duration is an estimate of effort over time. A ratio of two
  guesses looks precise and is not. Use it when people can at least state the
  basis of their numbers; otherwise a coarser method such as
  [MoSCoW](MoSCoW_Method.md) is more honest.
- **When scoring will be gamed.** Relative-point variants (each factor scored
  1–20 against the other items) are quick, but every sponsor learns that a
  higher number moves them up. Without a stated basis per score, the exercise
  becomes negotiation in arithmetic form.
- **When you think you are doing Reinertsen but are doing the simplified
  formula.** The widely taught SAFe version adds three relative scores — business
  value, time criticality, and risk reduction or opportunity enablement — and
  divides by relative job size. Practitioner critics (see Black Swan Farming
  below) point out that adding the terms lets an item with no value score well
  just for being time-critical, and that relative points throw away the
  money-per-week figure that makes the method economic. If you use the shortcut,
  say so, and do not present the result as a calculated loss.
- **When the constraint is not team time.** If the real bottleneck is a
  specialist, an approval board or a supplier, sequencing by team duration
  optimises the wrong thing. Map the flow first, for example with
  [Value Stream Mapping](Value_Stream_Mapping.md).
- **For hard dependencies and fixed scope-by-date problems.** The ratio does not
  know that B must precede A, or that a release has a non-negotiable date.

## Facilitation outline (2–3 hours)

1. (15 min) Agree the unit: money per week if at all possible; relative points
   only if money is impossible, and then on a written scale.
2. (20 min) For each item, ask *what happens if this ships three months later?*
   Note whether value decays gradually, collapses at a fixed date, or barely
   changes. This alone often reshuffles the "urgent" pile.
3. (45 min) Estimate cost of delay per item. The sponsor states the basis —
   revenue, penalties, hours of staff time lost, risk exposure — and the room
   challenges it. Write ranges, not single points, where people disagree.
4. (20 min) Estimate duration: how long the team will be occupied, not total
   effort across the organisation.
5. (15 min) Divide, sort, and read the sequence aloud.
6. (20 min) Check the result against dependencies and hard dates; record any
   manual override and why. Agree when the numbers will be revisited — cost of
   delay changes as dates approach.

## Common pitfalls

- Letting "urgent" stand in for a number instead of asking what is lost per week
- Scoring every item high on every factor, which flattens the ranking
- Using total effort instead of duration, which misprices work that is short but
  needs several people at once
- Re-scoring only the items you want to move
- Treating the ranking as fixed; a deadline coming closer changes the cost of delay

## Relation to neighbouring methods

- [RICE Scoring](RICE_Scoring.md) ranks a pool of ideas by how many people they
  reach and how much they help, per unit of effort. It has no notion of time
  running out. Use RICE to choose *which* ideas are worth doing; use cost of
  delay to decide *in what order* committed work should go when waiting is costly.
- [Eisenhower Matrix](Eisenhower_Matrix.md) separates urgent from important for
  one person's task list; cost of delay puts a figure on urgency for a team's queue.
- [MoSCoW Prioritization](MoSCoW_Method.md) decides what is in or out of a fixed
  release; cost of delay orders what is in.
- [Weighted Decision Matrix](Weighted_Decision_Matrix.md) chooses one option
  among several against criteria; it does not sequence a queue.

## See also

- Donald G. Reinertsen, *The Principles of Product Development Flow: Second
  Generation Lean Product Development* (Celeritas Publishing, 2009),
  ISBN 978-1-935401-00-1
- [Wikipedia: Cost of delay](https://en.wikipedia.org/wiki/Cost_of_delay)
- Black Swan Farming, [Cost of Delay](https://blackswanfarming.com/cost-of-delay/)
  and [CD3: Cost of Delay Divided by Duration](https://blackswanfarming.com/cost-of-delay-divided-by-duration/)
  — practitioner guides with a worked sequencing example
- Black Swan Farming, [SAFe and Weighted Shortest Job First](https://blackswanfarming.com/safe-and-weighted-shortest-job-first-wsjf/)
  — critique of the additive, relative-score formula
- Scaled Agile, [WSJF](https://framework.scaledagile.com/wsjf) — the SAFe definition
