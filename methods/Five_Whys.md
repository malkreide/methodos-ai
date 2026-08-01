# Five Whys

Ask "why did that happen?" against one observed failure, repeatedly, until the
answer names something you can actually change. Five is a rule of thumb, not a
quota — stop when you reach a cause, keep going if you haven't.

## When to use

- Straight after an incident, outage, or escaped defect
- When the same problem keeps recurring despite being "fixed" each time
- As a drill-down inside a retrospective that surfaced a repeating theme

## When *not* to use

- When several causes plausibly contributed at once — use an [Ishikawa diagram](Ishikawa_Diagram.md)
- For problems nobody in the room has first-hand knowledge of
- As a substitute for evidence: a chain of guesses is still guesswork

## Facilitation outline (45 min)

1. (5 min) Write the failure as one factual sentence. No causes yet, no blame.
2. (25 min) Ask why. Write the answer. Ask why of *that answer*. Repeat.
   Each link must be something a participant can support with evidence.
3. (10 min) Stop when the answer names a process, system, or decision you
   control. If it names a person, you stopped one step too early.
4. (5 min) Assign one owner to the countermeasure at that final link.

## Common pitfalls

- Ending at "human error" — that is a restatement of the failure, not a cause
- Accepting a link because it sounds plausible instead of checking it
- Running it while the outage is still live; people reconstruct badly under pressure
- Treating the fifth answer as authoritative just because you asked five times

## See also

- [Ishikawa (Fishbone) Diagram](Ishikawa_Diagram.md) — when the failure has several parallel causes
- [Start, Stop, Continue](Start_Stop_Continue.md) — the retrospective that often feeds this
- [Wikipedia: Five whys](https://en.wikipedia.org/wiki/Five_whys)
