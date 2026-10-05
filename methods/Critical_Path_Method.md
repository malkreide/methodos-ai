# Critical Path Method (CPM)

In a project with a fixed finish date, most tasks could run a little late
without anyone noticing at the end. A few could not: they form an unbroken
chain of dependent work, and every day lost on any of them is a day lost on the
finish. The Critical Path Method finds that chain. You list the tasks, how long
each takes and what each has to wait for, then calculate the longest route
through the resulting network. That route is the critical path; its length is
the earliest possible finish. Every task off it has *float* (also called
slack): the number of days it can slip before it joins the critical path and
starts moving the end date.

The method was developed in the late 1950s by James E. Kelley Jr. (Remington
Rand) and Morgan R. Walker (DuPont) and published as "Critical-path planning
and scheduling" (1959). At almost the
same time the US Navy's Special Projects Office, with Booz Allen Hamilton and
Lockheed, developed PERT for the Polaris missile programme. PERT works on the
same kind of network but uses three time estimates per task (optimistic, most
likely, pessimistic) instead of one. Today the two are often taught together,
and project scheduling software commonly computes a critical path underneath
its Gantt chart.

## A worked example

A school must be teaching in its new building in 29 working days.

| Task | Duration | Waits for |
|---|---|---|
| A — builder finishes and hands over | 15 days | — |
| B — furniture ordered and delivered | 20 days | — |
| C — network and IT installed | 6 days | A |
| D — furniture installed | 4 days | A, B |
| E — old classrooms packed | 5 days | — |
| F — boxes moved | 2 days | D, E |
| G — teachers unpack and set up rooms | 3 days | C, F |

Working forward, each task starts when its last predecessor ends: D can start
on day 20 (when the furniture arrives, not when the builder leaves), F on day
24, G on day 26, finish on day 29. Working backward from day 29 gives the latest
start each task can have without delaying that finish. The difference between
latest and earliest start is the float:

| Task | Float |
|---|---|
| B, D, F, G | 0 — the critical path (20 + 4 + 2 + 3 = 29 days) |
| A, C | 5 days |
| E | 19 days |

Everyone was watching the builder. The calculation says the builder could hand
over five days late without consequence, while a one-day delay in the furniture
delivery costs the opening date. Packing can start almost three weeks later than
people feared. The numbers are illustrative; the shift of attention is the point.

## When to use

- A one-off project with a date that cannot move: moving into a building before
  term, a system go-live fixed by law or contract, an event, a merger day
- Many tasks depend on each other and nobody can say which delays matter
- A project is late and someone proposes adding people or money: only tasks on
  the critical path will bring the finish forward if they are shortened
- A supplier or another department announces a delay and you need to know
  quickly whether it touches the end date

## When *not* to use

- **When durations are genuinely uncertain.** Basic CPM takes one estimate per
  task and adds them up, so the finish date it produces is the date when
  everything goes as estimated. With research, novel technology or untested
  suppliers, use three-point estimates as in PERT, run a schedule risk analysis
  (the US GAO guide below treats it as a separate best practice), or protect the
  finish with explicit buffers as in critical chain project management.
- **When the real constraint is people or equipment.** The basic calculation
  assumes every task can start the moment its predecessors are done. If two
  tasks on different paths need the same caretaker, the same IT specialist or
  the same crane, the schedule is not feasible as drawn. Resource levelling, or
  the critical chain approach, handles this; plain CPM does not.
- **For small projects.** A dozen tasks that one person can hold in their head
  do not need a network calculation. A dated checklist is enough.
- **For iterative work where scope keeps changing.** When the task list itself
  is rewritten every few weeks, as in agile product development, the network is
  out of date before it is finished. Fix the date and adjust scope instead, for
  example with [MoSCoW](MoSCoW_Method.md).
- **To decide which work is worth doing.** CPM schedules a set of tasks that are
  already committed. It does not choose between them.

## Facilitation outline (2–4 hours for a first network)

1. (20 min) Agree the end point: what exactly has to be true on the finish date.
   Then list every task needed to get there, at a level where each has one owner
   and lasts days rather than months.
2. (30 min) For each task, ask *what must be finished before this can start?*
   Write each task on a card and draw the arrows on a wall or whiteboard. Ask the
   people who will do the work; dependencies are where planners' assumptions are
   most often wrong.
3. (30 min) Estimate durations in working days, from the people doing the task.
   Note where an estimate is a guess and where it is a supplier's commitment.
4. (30 min) Forward pass: earliest start and finish of each task, from the
   start. Backward pass: latest start and finish, from the end date. Float is
   the difference. Software does this instantly; on paper it is still quick for
   up to about fifty tasks.
5. (20 min) Read the critical path aloud. Check it against intuition: if it
   surprises people, look first for a missing or wrong dependency.
6. (20 min) Decide what to do with it: owners for each critical task, early
   warnings for tasks with little float, and where shortening or overlapping
   tasks would actually help. Agree how often the network will be updated.

## Common pitfalls

- Forgetting tasks that are not "real work": approvals, procurement lead times,
  permits, holidays. They are often on the critical path.
- Fixing dates on tasks by hand instead of deriving them from dependencies, which
  hides the real path; the US GAO guide warns against exactly this
- Treating the critical path as permanent; when a task with little float slips,
  the path moves, and a second, *near-critical* path deserves almost as much care
- Spending float early: a task with a week of float that starts a week late has
  none left when something goes wrong
- Crashing (adding resources to shorten) tasks that are not on the critical path,
  which costs money and moves nothing
- Presenting the calculated finish date as a promise rather than as the date
  that holds if every estimate holds

## Relation to neighbouring methods

- [Value Stream Mapping](Value_Stream_Mapping.md) follows a *recurring* process
  to find where items sit waiting. CPM plans a *one-off* project to find which
  tasks determine its finish date.
- [Cost of Delay / WSJF](Cost_of_Delay_WSJF.md) sequences independent work items
  by what is lost while each waits. CPM sequences tasks that depend on each
  other, where the order is largely dictated by the dependencies.
- [Pre-Mortem](Pre_Mortem.md) and the [Risk Matrix](Risk_Matrix.md) find and rate
  what could go wrong. They pair well with CPM: a risk that hits a critical task
  matters more than the same risk on a task with weeks of float.
- [Eisenhower Matrix](Eisenhower_Matrix.md) sorts one person's tasks by urgency
  and importance; it has no notion of one task waiting for another.

## See also

- James E. Kelley Jr. and Morgan R. Walker, "Critical-path planning and
  scheduling", *Proceedings of the Eastern Joint Computer Conference*, 1959,
  pp. 160–173, [doi:10.1145/1460299.1460318](https://doi.org/10.1145/1460299.1460318)
- D. G. Malcolm, J. H. Roseboom, C. E. Clark and W. Fazar, "Application of a
  Technique for Research and Development Program Evaluation", *Operations
  Research* 7(5), 1959, [doi:10.1287/opre.7.5.646](https://doi.org/10.1287/opre.7.5.646)
  — the first published description of PERT
- F. K. Levy, G. L. Thompson and J. D. Wiest, "The ABCs of the Critical Path
  Method", *Harvard Business Review*, September 1963,
  [hbr.org](https://hbr.org/1963/09/the-abcs-of-the-critical-path-method)
- US Government Accountability Office,
  [*Schedule Assessment Guide: Best Practices for Project Schedules*](https://www.gao.gov/products/gao-16-89g)
  (GAO-16-89G, 2015) — public-sector guidance on dependencies, critical path,
  float and schedule risk analysis
- [Wikipedia: Critical path method](https://en.wikipedia.org/wiki/Critical_path_method)
- [Wikipedia: Program evaluation and review technique](https://en.wikipedia.org/wiki/Program_evaluation_and_review_technique)
- [Wikipedia: Critical chain project management](https://en.wikipedia.org/wiki/Critical_chain_project_management)
  — buffers and resource constraints, introduced by Eliyahu M. Goldratt (1997)
