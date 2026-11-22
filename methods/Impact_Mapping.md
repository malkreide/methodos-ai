# Impact Mapping

Draw a tree that runs from one goal to the work that is supposed to serve it,
with two layers in between: the people whose actions decide whether the goal
is reached, and the change in what each of them does. A deliverable earns its
place only if it hangs from such a change. Whatever cannot be connected is a
candidate for cutting, and whatever is connected carries its reason with it.

The map is read through four questions, one per level:

1. **Why?** The goal in the centre: what the organisation wants to achieve,
   with a figure and a date that would show it has been achieved.
2. **Who?** The actors: people or groups who can bring the goal closer, who
   can obstruct it, who use the result, or who are affected by it.
3. **How?** The impacts: for each actor, the change in behaviour that would
   help the goal (or the obstruction that must be prevented). Impacts describe
   what people do, not what the team builds.
4. **What?** The deliverables: features, services or organisational
   activities that could cause each impact.

Gojko Adzic described the technique in his book *Impact Mapping* (2012) and
the companion site impactmapping.org, aimed at software products and
projects. It builds on the "effect mapping" work of Swedish interaction
designers Mijo Balic and Ingrid Ottersten, whose earlier "goal cards" already
linked business goals to usage goals and from there to design steps.

## When to use

- A backlog or requirements catalogue has grown from many stakeholders'
  requests and nobody can explain which items serve the goal
- At the start of a product, project or milestone, to agree what the work is
  for before the scope is fixed
- When a sponsor and a delivery team disagree about what to build and need a
  shared reason for including or dropping items
- Mid-project, to re-check a plan against what has been learned about the
  people it is meant to influence

## When *not* to use

- When the goal itself is still in dispute or cannot be stated with a figure;
  settle that first, for example with [OKR](OKR.md) for a period's outcomes
- To explain how a programme leads to long-term social outcomes and what to
  evaluate along the way: that chain of results and assumptions is a
  [Theory of Change](Theory_of_Change.md)
- To break a question into analysable parts with no actors in it: use an
  [Issue Tree](Issue_Tree.md)
- To ask what customers are trying to get done in the first place: interview
  them with [Jobs to Be Done](Jobs_To_Be_Done.md) and bring the findings to the
  map as actors and impacts
- To decide the order of items that already all serve the goal under a fixed
  deadline: use [MoSCoW](MoSCoW_Method.md)

## Facilitation outline (2 hours)

Invite the sponsor or someone who can speak for the goal, people from the
delivery team, and at least one person who knows the actors first-hand.
Work on a large whiteboard or an online board, with the goal in the middle.

1. (20 min) **Goal.** Write one goal for the next milestone. Ask how you would
   know in six or twelve months that it has been reached, and attach the
   figure. If two goals compete, draw two maps.
2. (20 min) **Actors.** Brainstorm everyone who could help or hinder: users,
   customers, colleagues in other units, partners, regulators. Group
   duplicates. Keep internal staff on the map; they often decide the outcome.
3. (30 min) **Impacts.** For each actor, ask how their behaviour should change
   to help the goal, and how they could get in its way. Phrase each impact as
   something an observer could see the person do ("files the return online
   without calling the hotline"), not as a feature.
4. (25 min) **Deliverables.** Only now list what the team or organisation
   could build or do for each impact. Place every existing request from the
   backlog on the map; requests that fit nowhere are set aside in a separate
   column.
5. (20 min) **Prune.** Mark the one or two impacts that matter most for the
   goal. Drop or park deliverables that serve only minor impacts or none, and
   record why. Agree how the chosen impacts will be observed after delivery.
6. (5 min) **Close.** Photograph or save the map, name an owner, and set a
   date to revisit it once the first deliverables are in use.

## Common pitfalls

- A goal without a figure, such as "improve the customer experience": every
  deliverable can claim to serve it, and nothing gets cut
- Impacts that are features in disguise ("uses the new portal"); ask what the
  person will do differently, and why that matters for the goal
- Jumping from goal straight to deliverables, which removes the layer that
  makes the reasoning open to challenge
- Leaving out actors who can block the goal, such as staff whose workload
  rises or partners whose interests differ
- Treating the map as finished: the links are assumptions, and observed
  behaviour after delivery should change it

## See also

- [Theory of Change](Theory_of_Change.md) — causal pathway from activities to long-term outcomes, with assumptions to evaluate
- [Stakeholder Map](Stakeholder_Map.md) — who has power and interest around an initiative, rather than whose behaviour serves a goal
- [OKR](OKR.md) — setting a period's measurable outcomes; a key result can become an impact map's goal
- [Issue Tree](Issue_Tree.md) — splitting a question into parts
- [MoSCoW Method](MoSCoW_Method.md) — negotiating scope against a fixed date
- [impactmapping.org](https://www.impactmapping.org/) — overview, how to draw a map, examples (CC BY 4.0)
- [How to make an impact map](https://www.impactmapping.org/drawing.html)
- Gojko Adzic, *Impact Mapping: Making a big impact with software products and projects*, Provoking Thoughts, 2012, ISBN 978-0-9556836-4-0 ([book page](https://www.impactmapping.org/book.html))
- [Gojko Adzic: Impact Mapping (Votito)](https://www.votito.com/methods/impact-mapping/) — summary by the author, including the method's history and tips on goals and impacts
- [Open impact mapping workshop materials](https://github.com/impactmapping/open-impact-mapping-workshop) (CC BY 4.0)
- Balic, Berndtsson, Ottersten, Aldman: [From Business to Buttons](https://www.designsociety.org/download-publication/29623/From+Business+to+Buttons), DESIGN 2002 — the goal-card precursor
