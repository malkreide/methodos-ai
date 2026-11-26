# Work Breakdown Structure (WBS)

A work breakdown structure takes everything a project has to produce and splits
it into a tree. The top element is the project as a whole. Below it sit the
major deliverables; below each of those, the parts it is made of; and so on,
until the lowest elements are small enough that someone can estimate them with
confidence, take responsibility for them and say plainly whether they are done.
Those lowest elements are usually called *work packages*.

One rule holds the tree together, often called the 100% rule: the elements
under any parent describe all of that parent's work and nothing more. Add up
the children and you get exactly the parent; add up the whole tree and you get
exactly the agreed scope. Work that does not appear anywhere in the tree is,
by definition, not part of the project. A second rule follows from the first:
no piece of work may sit under two parents, or it will be estimated, paid for
and perhaps done twice.

The idea grew out of US defence and space programmes around 1960, when the
Navy's PERT planning for the Polaris missile and a joint Defense
Department–NASA cost guide grouped work by the products it delivered. The
Defense Department made the approach mandatory for its programmes in 1968
(MIL-STD-881, still maintained), and NASA publishes its own handbook. The
Project Management Institute carried it into general project management; its
*Practice Standard for Work Breakdown Structures* (3rd edition, 2019) is the
usual reference. The same thinking appears under other names: PRINCE2 starts
planning with a *product breakdown structure* listing every output before any
task is named, and the Swiss federal project method HERMES plans a phase in
work packages, each assigned to one responsible person and producing one or
more defined outcomes.

## What it looks like

A municipality is building a small sports hall. Part of its tree might read:

```
1  Sports hall
1.1  Project management (plans, reports, meetings with the council)
1.2  Planning and permits
     1.2.1  Architectural design
     1.2.2  Building permit
1.3  Building
     1.3.1  Foundations and structure
     1.3.2  Roof and facade
     1.3.3  Building services (heating, ventilation, electrics)
1.4  Fit-out (sports equipment, changing rooms, signage)
1.5  Handover (acceptance, keys, user training, documentation)
```

Each element is named as a *thing that will exist* — a permit, a roof,
trained caretakers — rather than an activity such as "coordinate" or
"support". The numbering shows at a glance where each piece belongs, and the
same numbers can later label budget lines, contract lots and progress reports.
For each work package a short entry in a *WBS dictionary* records what is
included, what is excluded, what counts as finished and who owns it.

## When to use

- At the start of a project whose scope has to be estimated, budgeted,
  tendered or split among teams or contractors
- When earlier projects of the same kind ran over because work turned up that
  no one had planned for
- When a long task list has lost any visible connection to the results the
  project is meant to deliver
- Before building a schedule: the work packages are what a timeline or a
  critical-path network is then made of
- When a funder, a client or a public tender asks for costs and deliverables
  per package

## When *not* to use

- When the question is analytical rather than a scope to deliver, such as why
  costs are rising: split the question with an [Issue Tree](Issue_Tree.md)
- When the scope is known and the open question is order and timing; that is
  the job of the [Critical Path Method](Critical_Path_Method.md), which takes
  the work packages as its input
- For a continuous stream of incoming requests rather than one project with a
  defined end; manage that flow with a [Kanban Board](Kanban_Board.md)
- When it is still unclear which deliverables would serve the goal at all:
  settle that first with an [Impact Map](Impact_Mapping.md), then break down
  what survives
- For open exploration where the outcome cannot yet be described; there, keep
  the tree to two levels and refine it as you learn

## Facilitation outline (2–3 hours for a medium-sized project)

Bring the project mandate, any contract or tender text, and the people who
know the different kinds of work involved. Work on a wall with sticky notes or
in a shared outline document.

1. (10 min) Write the project's end result as the top element, together with
   one sentence on what is explicitly out of scope.
2. (25 min) Agree the second level: the five to nine major deliverables that
   together make up the result. Include management, testing, training and
   handover, which are the elements most often forgotten. Decide whether the
   level is organised by product or by phase, and keep it consistent.
3. (60 min) Break each second-level element down, in small groups if the
   project is large. Name every element as a noun — a deliverable — not as an
   activity. Stop splitting a branch once its pieces can be estimated, owned by
   one person or team, and finished within roughly one reporting period.
4. (20 min) Check the 100% rule branch by branch: does anything under this
   parent fall outside it? Is anything belonging to it missing? Does any piece
   appear twice?
5. (15 min) Walk through the tree once from the point of view of someone who
   will use or operate the result, asking what they will need on day one that
   is not yet in it.
6. (20 min) Number the elements, name a provisional owner for each work
   package and list the ones whose content still needs a dictionary entry.

Afterwards, write the short dictionary entries, estimate each work package,
and only then build the schedule and the budget from the packages.

## Common pitfalls

- Copying the organisation chart into the tree: departments are not
  deliverables, and work that lies between departments disappears
- Mixing products and activities on the same level, which breaks the 100%
  rule because activities overlap
- Leaving out the "invisible" deliverables: project management, quality
  checks, documentation, training, decommissioning the old solution
- Splitting too finely: elements of a few hours each turn the tree into a task
  list that nobody maintains
- Treating the tree as a schedule. It has no order and no dates; the sequence
  comes afterwards
- Changing scope without changing the tree, so the two drift apart and the
  tree stops being the reference for what is in and out

## See also

- [Critical Path Method](Critical_Path_Method.md) — sequences and times the work packages once they exist
- [Issue Tree](Issue_Tree.md) — the same tree shape, applied to a question instead of a scope of work
- [RACI Matrix](RACI_Matrix.md) — once the packages exist, records who does, approves and is consulted on each
- [Impact Mapping](Impact_Mapping.md) — tests whether a deliverable serves the goal before it enters the tree
- [Kanban Board](Kanban_Board.md) — for an ongoing flow of work items rather than a bounded project
- [Mind Mapping](Mind_Mapping.md) — free association around a topic; useful for gathering raw material, but without the 100% rule
- [NASA Work Breakdown Structure (WBS) Handbook, NASA/SP-20210023927 (2021)](https://www.nasa.gov/wp-content/uploads/2023/08/nasa-work-breakdown-structure-handbook.pdf)
- [GAO Cost Estimating and Assessment Guide, GAO-20-195G (2020)](https://www.gao.gov/products/gao-20-195g) — the work breakdown structure as a step in cost estimating
- [HERMES project management: planning with work packages](https://hermes.admin.ch/en/project-management/user-information/planning.html) — Swiss Federal Chancellery
- [Wikipedia: Work breakdown structure](https://en.wikipedia.org/wiki/Work_breakdown_structure)
- [Wikipedia: Product breakdown structure](https://en.wikipedia.org/wiki/Product_breakdown_structure) — the PRINCE2 variant
- [Wikipedia: Work package](https://en.wikipedia.org/wiki/Work_package)
- Project Management Institute (2019). *Practice Standard for Work Breakdown Structures*, 3rd ed. Newtown Square, PA: PMI. ISBN 978-1-62825-619-2.
