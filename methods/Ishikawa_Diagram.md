# Ishikawa (Fishbone) Diagram

Map every candidate cause of a problem onto a spine of fixed categories, so the
group sees the whole space of explanations before arguing about any one of them.

## The standard categories (6M)

People · Process · Equipment · Materials · Environment · Measurement

Substitute freely — software teams often use Code, Infrastructure, Process,
People, Data, and External Dependencies.

## When to use

- A quality or reliability problem with many plausible contributing factors
- Several teams each confidently blame a different subsystem
- Before collecting data, to decide *what* is worth measuring

## When *not* to use

- When the causal chain is obviously linear — [Five Whys](Five_Whys.md) is faster
- As the final answer: the diagram ranks nothing, it only enumerates
- With a group too large to keep the diagram legible

## Facilitation outline (2 hours)

1. (10 min) Write the problem statement in the fish's head. Be specific and measurable.
2. (10 min) Agree the category labels. Adapt them to your domain.
3. (45 min) Silent brainstorm per branch, then post. Sub-branch causes of causes.
4. (30 min) Dot-vote the branches most likely to matter.
5. (15 min) For the top two or three, name the data that would confirm or kill them.

## Common pitfalls

- Filling every branch out of symmetry, padding the diagram with noise
- Confusing "we have no monitoring here" with "the cause is here"
- Skipping step 5 — an unvalidated diagram is a wall of speculation
- Letting the loudest discipline claim the whole spine

## See also

- [Five Whys](Five_Whys.md) — drill down once you've picked a branch
- [Pre-Mortem Analysis](Pre_Mortem.md) — the same breadth, applied before the failure
- [ASQ: Fishbone diagram](https://asq.org/quality-resources/fishbone)
