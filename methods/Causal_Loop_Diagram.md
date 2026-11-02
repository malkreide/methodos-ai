# Causal Loop Diagram

Draw the variables that matter in a situation and the arrows by which each one
pushes another up or down, until the arrows close into circles. Those circles
are feedback loops. Some amplify whatever is happening (reinforcing loops),
others pull the system back towards a limit or a target (balancing loops), and
many contain a delay between an action and its effect. Seeing the loops
explains a pattern that no list of causes can: why the problem returns, or
grows, *because* of what people do about it.

The notation comes from system dynamics, the field Jay Forrester founded at MIT
in the 1950s and 1960s. Peter Senge brought it to a management audience in
*The Fifth Discipline* (1990), together with a small set of recurring loop
structures he called systems archetypes. John Sterman's textbook *Business
Dynamics* (2000) is the standard reference for drawing the diagrams carefully
and for turning them into simulation models when that is worth the effort.

## When to use

- A problem keeps coming back, or gets worse, despite repeated and sincere
  efforts to solve it
- An intervention worked at first and then the situation drifted back, or
  overshot in the other direction
- Different groups each blame another for behaviour that the shared structure
  is actually producing
- Before a policy or programme decision whose side effects will take months or
  years to show

## When *not* to use

- To trace one concrete failure back to a fixable cause — a straight chain is
  enough, use [Five Whys](Five_Whys.md)
- To lay out the many candidate contributors to a defect before collecting
  data — use an [Ishikawa diagram](Ishikawa_Diagram.md)
- When the group cannot yet agree what *kind* of problem it faces — classify
  it first with the [Cynefin framework](Cynefin_Framework.md)
- To plan how a programme is meant to produce its intended outcomes; a causal
  loop diagram is for understanding behaviour that is already happening
- Under time pressure in a live incident: stabilise first, map later

## Notation in brief

- **Variables** are nouns that can rise or fall: "backlog", "staff fatigue",
  "trust in management". Not actions, not events.
- **Arrows** point from cause to effect. Mark each with *s* (or +) when both
  move in the same direction, *o* (or −) when they move in opposite
  directions.
- **Delays** are marked with a double stroke across the arrow.
- **Loops** are labelled *R* (reinforcing) or *B* (balancing). A loop with an
  even number of *o* links, including none, is reinforcing; an odd number makes
  it balancing. Give each loop a short name a newcomer would understand.

## Facilitation outline (120 min)

1. (10 min) Agree the behaviour over time you want to explain. Sketch it as a
   rough graph: what has risen, fallen or oscillated, and over what period.
2. (15 min) List the variables involved. Phrase each as a quantity, and keep
   the list to the ten or so that matter most.
3. (30 min) Start from the variable the group cares about and ask what drives
   it and what it drives. Draw arrows and polarities one at a time; challenge
   each link — "if this goes up, does that really go up, all else equal?"
4. (20 min) Find the closed loops, label each R or B and name it. Mark the
   delays. Check whether the loops reproduce the graph from step 1; if they do
   not, something is missing.
5. (15 min) Compare the picture with the common archetypes — fixes that
   backfire, shifting the burden to a quick remedy, limits to growth,
   escalation, success to the successful, a shared resource overused. A match
   suggests where leverage usually lies.
6. (20 min) Mark candidate intervention points: weakening a reinforcing loop
   that hurts, strengthening a balancing one, shortening a delay, or changing
   the goal a loop is steering towards. Note what evidence would test each.
7. (10 min) Record the diagram with its loop names and the open questions, and
   assign owners for checking the most doubtful links against data.

## Common pitfalls

- Drawing every conceivable connection; a readable diagram with three loops
  beats a complete one nobody can follow
- Using actions or events as variables ("hire people") instead of quantities
  ("headcount"), which makes polarities meaningless
- Skipping delays, so the diagram cannot explain why the fix looked like it
  worked
- Treating the diagram as proven; each link is a hypothesis until data or
  experience supports it
- Building it alone and presenting it; the shared understanding comes from
  drawing it together

## See also

- [Five Whys](Five_Whys.md) — a single chain from failure to cause
- [Ishikawa (Fishbone) Diagram](Ishikawa_Diagram.md) — many causes, one effect, no loops
- [Cynefin Framework](Cynefin_Framework.md) — deciding what kind of problem it is
- [Force Field Analysis](Force_Field_Analysis.md) — the forces for and against a planned change
- [Value Stream Mapping](Value_Stream_Mapping.md) — where time is lost in a linear flow of work
- [Wikipedia: Causal loop diagram](https://en.wikipedia.org/wiki/Causal_loop_diagram)
- [Wikipedia: System archetype](https://en.wikipedia.org/wiki/System_archetype)
- [Wikipedia: *The Fifth Discipline*](https://en.wikipedia.org/wiki/The_Fifth_Discipline) — Senge, 1990
- [System Dynamics Society: What is system dynamics?](https://systemdynamics.org/what-is-system-dynamics/)
- [Sterman, J. D. (2001). System dynamics modeling: tools for learning in a complex world. *California Management Review* 43(4), 8–25](https://doi.org/10.2307/41166098)
- [Kim, D. H. Guidelines for drawing causal loop diagrams. *The Systems Thinker*](https://thesystemsthinker.com/guidelines-for-drawing-causal-loop-diagrams-2/)
- [UK Government Office for Science: Systems thinking for civil servants](https://www.gov.uk/government/publications/systems-thinking-for-civil-servants)
