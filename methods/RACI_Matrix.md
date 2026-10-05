# RACI Matrix (Responsibility Assignment Matrix)

A table that ties every task of a process or project to the people who carry
it. Tasks run down the rows, people or units across the columns, and each cell
holds at most one letter:

| Letter | Role | How many per task |
|---|---|---|
| **R** | Responsible: does the work | at least one |
| **A** | Accountable: answers for the task being finished properly, delegates it and accepts the result | exactly one |
| **C** | Consulted: asked for expertise *before* or during the work; two-way | as few as possible |
| **I** | Informed: told about progress or the outcome; one-way | as many as need it |

On a small task the same person can be both R and A. What the matrix must never
show is a task with no A or with two.

## Origin

Charts that cross tasks with people are older than the acronym: project and
matrix organisations used "linear responsibility charts" for this, and Beckhard
and Harris described responsibility charting as a tool for managing change in
their 1977 book *Organizational Transitions*. The four-letter form became the
common one, and the PMI's *Guide to the Project Management Body of Knowledge*
lists the RACI chart as one kind of responsibility assignment matrix. Many
variants add a role, such as **S** for support (RASCI) or **V** for verifier.
Public bodies use the form in their own process design; the UK Civil Service's
HR design principles, for instance, assign RACI roles to each HR process step
and require a single accountable party per task.

## RACI and its neighbours

The method is easiest to place by what it is *not*:

- **[DACI](DACI_Matrix.md)** assigns roles for **one decision**: who drives it,
  who approves it, who contributes and who hears the result. RACI assigns roles
  for **many tasks** that make up a process or project, most of which are work
  rather than decisions. If the problem is one stalled call, use DACI; if it is
  a process whose steps keep falling through the cracks, use RACI.
- **[Stakeholder Map](Stakeholder_Map.md)** asks who has power over and
  interest in an initiative, to plan how to engage them. It says nothing about
  who performs which task.
- **[Customer Journey Map](Customer_Journey_Map.md)** follows a service from
  the user's side. It often shows *where* a hand-off fails; RACI then settles
  *who inside* owns that step.
- **[Critical Path Method](Critical_Path_Method.md)** and
  **[Value Stream Mapping](Value_Stream_Mapping.md)** deal with order, time and
  waiting in the work, not with who is answerable for it.

## When to use

- A recurring process involves several units and tasks are regularly done
  twice or not at all
- A project is starting, or entering a new phase, with partners who have not
  worked together before
- Work is moving between units: a shared service takes over, two teams merge,
  a task is outsourced
- New staff keep asking "who does this here?" and nobody can point to an answer

## When *not* to use

- **The question is one decision.** Who gets the final say on a single matter
  is what [DACI](DACI_Matrix.md) is for; a one-row RACI is a DACI with less
  precise labels.
- **Nobody will maintain it.** A matrix drawn up once and never revised after
  the next reorganisation is worse than none, because people trust it.
- **The organisation already consults too much.** If every task gains five Cs,
  the matrix formalises the bottleneck instead of removing it.
- **The roles themselves are disputed.** The matrix records an agreement; it
  does not produce one. When two managers both claim the same task, settle that
  first (with whoever has the authority to settle it), then write it down.
- **The work is small and stable.** A team of four with routines that work does
  not need a table.

## Facilitation outline (about 2 hours for a first version)

Invite someone who actually does the work from each unit involved, plus the
person who can confirm the final assignments.

1. **(15 min) Fix the scope.** Name the process or project and where it starts
   and ends. List the units or roles that take part; use roles ("enrolment
   clerk, district office") rather than whole departments.
2. **(25 min) List the tasks.** Ten to thirty rows at a level where one person
   could finish the task. Verbs first: "send confirmation letter", not
   "letters".
3. **(40 min) Fill the cells, task by task.** For each row agree the A first,
   then the Rs, then the Cs and Is. Record disagreements in a separate list
   rather than arguing them out in the cell.
4. **(20 min) Read the matrix both ways.**
   - Down each row: no A, more than one A, no R, or a long line of Cs?
   - Down each column: a role with A on most rows (overload), a role with
     nothing but Is (should they be here?), a role nobody consulted that will
     later object?
5. **(15 min) Close the gaps.** Fix what the room can fix; hand the open
   disputes to the person with authority to decide, with a date. Name an owner
   for the matrix itself and a review date, ideally the next cycle of the
   process.
6. **(Afterwards)** Share the table with everyone named in it, and check it
   against the next real run of the process.

## Common pitfalls

- Putting two letters A in a row "to be fair": the point of the method is lost
- Writing "the department" or "IT" in a cell: name a role someone can be asked
  about
- Using C as a courtesy, so that every change waits on people who had nothing
  to add
- Treating the finished table as the outcome; the outcome is the behaviour on
  the next run of the process
- Filling the matrix from the organisation chart instead of from how the work
  is actually done
- Never looking at it again; real-world examples drift quickly (even published
  school samples sometimes list two accountable people for one task)

## See also

- [DACI Decision-Making Framework](DACI_Matrix.md): roles within one decision
- [Stakeholder Mapping](Stakeholder_Map.md): who has power and interest, not who does the work
- [Customer Journey Map](Customer_Journey_Map.md): where the service fails from the user's side
- [Consent Decision-Making](Consent_Decision_Making.md): when a group has to agree the assignments together
- [Project Management Institute (2017). *A Guide to the Project Management Body of Knowledge (PMBOK Guide)*, 6th ed. Newtown Square, PA: PMI](https://books.google.com/books?vid=ISBN9781628251845)
- [Beckhard, R. and Harris, R. T. (1977). *Organizational Transitions: Managing Complex Change*. Reading, MA: Addison-Wesley](https://archive.org/details/organizationaltr00beck)
- [UK Civil Service: Global HR Design Principles 2024](https://www.gov.uk/government/publications/global-hr-design/global-hr-design-principles-2024-html): RACI applied to public HR processes
- [Network for College Success, University of Chicago: RACI Matrix for a Counseling Department (PDF)](https://ncs.uchicago.edu/sites/default/files/uploads/tools/NCS_PS_Toolkit_BST_Set_A_RACIMatrix.pdf): a worked school example
- [Wikipedia: Responsibility assignment matrix](https://en.wikipedia.org/wiki/Responsibility_assignment_matrix)
