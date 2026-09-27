# MoSCoW Prioritization

Sort requirements into four buckets so that meeting a fixed date is a decision
made in advance, not a scramble discovered in the final week.

| Bucket | Meaning |
|---|---|
| **M**ust have | the release is worthless or non-compliant without it |
| **S**hould have | painful to omit, but there is a workaround |
| **C**ould have | genuine value, first to go under pressure |
| **W**on't have *(this time)* | explicitly out of scope, and recorded as such |

## When to use

- Fixed deadline, variable scope, and a wish list bigger than the budget
- Stakeholder workshops where "everything is critical" needs testing
- Before a time-boxed delivery, so descoping later is a plan rather than a failure

## When *not* to use

- When you need an execution order — MoSCoW gives buckets, not a sequence
- When cost matters as much as desirability; use [RICE](RICE_Scoring.md)
- With no deadline pressure at all: the forcing function disappears

## Facilitation outline (90 min)

1. (10 min) State the deadline and the capacity. Both numbers, out loud.
2. (30 min) First pass: every item into a bucket, fast, no debate.
3. (30 min) Cap the Musts. DSDM's guidance is to keep Must-have work at or
   below about 60% of the estimated effort, and to hold around 20% as
   Could-haves: that pool is the contingency you give up first. Agree here how
   a Should is told apart from a Could (people affected, value at stake), so
   the boundary is not re-argued item by item.
4. (20 min) Read the Won't-have list aloud and get explicit acknowledgement.
   This step is the whole point; skipping it wastes the exercise.

## Common pitfalls

- Every item becoming a Must because nobody enforces the cap
- Treating Won't-have as "later" — it means *not in this delivery*
- Bucketing without the capacity number, which makes the exercise a wish list
- Letting the sponsor re-bucket privately after the workshop
- Bucketing once and never again: revisit the priorities at the end of every
  timebox or increment, and check that new work does not push the Musts past the cap

## See also

- [RICE Scoring](RICE_Scoring.md) — when you need a ranked order, not buckets
- [SWOT Analysis](SWOT.md) — for the strategic framing that precedes scoping
- [Agile Business Consortium: What is MoSCoW Prioritization?](https://www.agilebusiness.org/resource/what-is-moscow-prioritization/) — the DSDM source of the technique
- [Wikipedia: MoSCoW method](https://en.wikipedia.org/wiki/MoSCoW_method)
