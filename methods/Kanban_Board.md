# Kanban Board with WIP Limits

A shared board shows every piece of work the team has accepted, one card per
item, in columns for the stages it passes through: for example *Requested*,
*In progress*, *Waiting for sign-off*, *Done*. The decisive part is not the
board but the agreement that goes with it: each working column has a maximum
number of cards, its work-in-progress (WIP) limit. When a column is full, nobody
starts anything new there; people help to finish, unblock or hand on what is
already in it, and only then pull the next card in. The short form the Kanban
community uses for this is "stop starting, start finishing".

The word *kanban* is Japanese for "signboard" or "card". At Toyota, kanban
cards travelling between production steps authorised a step to make or move
only what the next one had used up, so that stock could not pile up between
them (Sugimori et al., 1977; Lean Enterprise Institute lexicon). David J.
Anderson carried the idea over to knowledge work, first in software and IT
teams at Microsoft and Corbis in the mid-2000s, and described it in *Kanban:
Successful Evolutionary Change for Your Technology Business* (2010). His
Kanban Method treats the board and the limits as a way to change how a team
works gradually, starting from the process it already has rather than
replacing it. Two guides describe today's practice: the Kanban University
guide lists visualising work, limiting WIP, managing flow, explicit policies,
feedback loops and experimental improvement; the Kanban Guide published by
ProKanban.org reduces it to three practices (define and visualise the workflow,
actively manage the items in it, improve the workflow) and four measures (WIP,
throughput, the age of unfinished items and cycle time).

## When to use

- When a team has many items open at once, most of them half done, and
  finished work arrives slowly or unpredictably
- When work lives in personal inboxes and lists, so nobody, including the team
  lead, can see who holds what and which step an item is waiting at
- When requests arrive continuously and in no fixed rhythm, as at a service
  desk, in a school's administration or in a communications team, and planning
  in fixed periods does not fit
- When items repeatedly wait for something outside the team (a signature, a
  reply, a review) and that waiting is invisible
- For one person's own workload, with a small personal limit of two or three
  items in progress

## When *not* to use

- Without limits. A board that only shows work, with no agreed maximum per
  column, is a shared to-do list. It improves visibility but leaves the main
  problem in place: people keep starting new things because nothing stops
  them. If the team is not willing to hold back new work when a column is full,
  say so openly rather than calling the board kanban.
- When the team cannot refuse or defer incoming work. If a manager or another
  department pushes requests in regardless, the limits are broken from the
  first day. Agree with whoever sends the work how full columns are handled
  before starting.
- To decide what matters most. The board shows the queue; it does not order it.
  Use the [Eisenhower Matrix](Eisenhower_Matrix.md) or
  [Cost of Delay / WSJF](Cost_of_Delay_WSJF.md) to agree priorities.
- To schedule a project with fixed dependencies and a deadline; that is the
  job of the [Critical Path Method](Critical_Path_Method.md).
- To find out once, in depth, why an end-to-end process takes so long. A
  [Value Stream Map](Value_Stream_Mapping.md) analyses the whole process and
  its delays; a kanban board then keeps the daily flow under control.
- Expect practitioner evidence. Dos Santos et al. (2018) synthesised 20
  primary studies from software engineering: the benefits found with most
  confidence were visibility of work, control over tasks, smoother flow and
  shorter delivery times, while organisational culture was the main obstacle.
  They also note that most studies are observational and qualitative and that
  negative results are almost never published. Evidence from offices, schools
  and public services is case reports, such as the GOV.UK publishing platform
  team's account, not controlled studies.

## Facilitation outline (first set-up, 2 hours)

1. (15 min) Collect every item the team is currently working on or has
   promised, one per card. Include the small things and the work that is
   waiting on someone else. Do not sort or judge yet.
2. (25 min) Agree the stages an item really passes through, from "accepted" to
   "done", and draw one column per stage. Add a column for items waiting on
   people outside the team if that is common. Keep it to four to six columns.
3. (20 min) Place every card in its column and mark who is working on it. Look
   together at the picture: how many items are open per person, and where they
   pile up. This count is often the moment the problem becomes undeniable.
4. (25 min) Set a first WIP limit for each working column. A simple start is
   slightly fewer items than there are people working in that stage, or two per
   person for the whole board. Agree what happens when a column is full:
   help finish, chase the blocker or swarm on the oldest card, but do not pull
   new work.
5. (20 min) Write down the few rules that go with the board: what has to be
   true for a card to move to the next column, who may add new items, and how
   urgent work is handled (for example one express lane with a limit of one).
6. (15 min) Agree when the board is looked at (a short look together several
   times a week is typical) and when the team reviews the limits themselves,
   for example every two to four weeks.

## Running it

- Move your own cards as soon as the work moves; a board updated once a week
  is history, not a picture of the work.
- When a column is full, look at the oldest card in it first. Items that have
  waited longest are usually the ones blocked by something nobody has named.
- At each review, check which column was most often full, how long items took
  from start to done, and whether the limits should go up or down. Change one
  thing at a time.

## Common pitfalls

- Setting limits so high that they are never reached; they then change nothing
- Quietly exceeding a limit "just this once" until nobody respects it
- Treating the board as a reporting tool for the manager instead of a working
  tool for the team
- Too many columns and colours, so that the board becomes hard to read and
  nobody keeps it up to date
- Using the board to count individual output, which encourages people to start
  easy items rather than finish the blocked ones

## See also

- [Daily Stand-up](Daily_Standup.md): a short daily meeting often held in front
  of the board; the board and its limits work without it, and the meeting
  without them
- [Timeboxing](Timeboxing.md): protects time for a single task; the board
  limits how many tasks are open at once
- [Eisenhower Matrix](Eisenhower_Matrix.md): decides which request to take
  first
- [Value Stream Mapping](Value_Stream_Mapping.md): a one-off analysis of where
  a process loses time
- [Five S](Five_S.md): the related lean practice for physical and digital
  workspaces
- [Kanban University: The Official Guide to the Kanban Method](https://kanban.university/kanban-guide/)
- [The Kanban Guide (2025 edition, ProKanban.org)](https://www.prokanban.org/the-kanban-guide)
- [Lean Enterprise Institute lexicon: Kanban](https://www.lean.org/lexicon-terms/kanban/)
- [Wright, A. (2017). How we use kanban on the GOV.UK Publishing Platform team. Inside GOV.UK blog](https://insidegovuk.blog.gov.uk/2017/02/15/how-we-use-kanban-on-the-gov-uk-publishing-platform-team/)
- [dos Santos, P. S. M., Beltrão, A. C., de Souza, B. P. and Travassos, G. H. (2018). On the benefits and challenges of using kanban in software engineering: a structured synthesis study. *Journal of Software Engineering Research and Development* 6, 13](https://doi.org/10.1186/s40411-018-0057-1)
- Anderson, D. J. (2010). *Kanban: Successful Evolutionary Change for Your
  Technology Business*. Sequim, WA: Blue Hole Press.
- Sugimori, Y., Kusunoki, K., Cho, F. and Uchikawa, S. (1977). Toyota production
  system and Kanban system: materialization of just-in-time and
  respect-for-human system. *International Journal of Production Research*
  15(6), 553–564.
