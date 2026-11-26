# Gantt Chart

A Gantt chart lays a project's tasks out against a calendar. Each task gets a
row; time runs from left to right; a bar starts on the day the task is meant to
begin and is as long as the task is meant to last. Milestones (dates on which
something must be true, such as a permit granted or a hall handed back) appear
as diamonds or markers on their day. Arrows between bars show that one task
cannot start until another has finished. A vertical line for today's date, and
bars shaded by how much of each task is done, turn the plan into a progress
report: any bar whose shading stops short of the today line is behind.

The chart answers a plain question that many projects cannot answer: *what is
supposed to be happening in which week, and are we where we said we would be?*
It does not decide which tasks are needed or calculate which ones determine the
finish date. It displays a schedule so that a team, a board or the public can
read it at a glance.

## Origins

Henry L. Gantt (1861–1919), an American engineer who had worked with Frederick
W. Taylor at Midvale and Bethlehem Steel, developed a family of charts between
about 1910 and 1915 to compare the work planned for each period with the work
actually done. His colleague Wallace Clark described them in *The Gantt Chart:
A Working Tool of Management* (1922). In Clark's account a space on the chart
stands both for a stretch of time and for the work scheduled in it, and lines
drawn inside the space show how much of that work was done. Gantt's own charts
were mostly about machines, workers and production orders; the bar chart of a
project's tasks that carries his name today grew out of them over the following
decades, and arrows linking dependent tasks became common only later.

Earlier, the Polish engineer Karol Adamiecki (1866–1933) had devised what he
called a *harmonogram* (from 1896): a date scale running down the side, a
column per activity, and paper strips whose position and length showed each
activity's start and duration, with its predecessors and successors noted at
the head of the column. Because he published mainly in Polish and Russian, and
his best-known article appeared only in 1931, his work had little influence in
the West. Historians such as Patrick Weaver point out that the harmonogram's
predecessor logic is closer to the later [Critical Path Method](Critical_Path_Method.md)
than to Gantt's charts.

## When to use

- A one-off project with tens to a few hundred tasks over weeks or months,
  where people need to know when their part begins and what it waits for
- Reporting progress to a board, a council, a funder or residents: the chart
  shows what is done, what is under way and what is late without a briefing
- Spotting clashes before they happen: two deliveries in the same week, the
  same few people booked on parallel tasks, work planned over the holidays
- Tracking slippage: keeping the approved dates as a baseline and comparing
  each week's actual progress against it
- Several projects sharing people or rooms, shown on one calendar

## When *not* to use

- **To find out what work the project contains.** A Gantt chart needs a task
  list. If nobody yet knows what has to be produced, break the scope down first
  (a [Work Breakdown Structure](Work_Breakdown_Structure.md) does exactly
  that) and put the resulting packages on the calendar afterwards.
- **To find the tasks that determine the end date.** The chart shows
  dependencies but does not compute the longest chain or each task's leeway.
  For that, run the [Critical Path Method](Critical_Path_Method.md); most
  scheduling software computes the critical path and then draws it as a Gantt
  chart.
- **For a continuous flow of requests without fixed dates.** A service desk or
  an editorial team handling incoming work is better served by a
  [Kanban Board](Kanban_Board.md), which tracks flow and limits work in
  progress instead of planning dates.
- **When the task list changes every few weeks.** In iterative work the chart
  is out of date before it is finished. Fix short cycles and adjust scope
  instead.
- **To protect one person's concentration.** Booking fixed slots in your own
  calendar is [Timeboxing](Timeboxing.md), not project scheduling.
- **For goals decades away.** Working back from a distant target to what must
  start now is [Backcasting](Backcasting.md); a Gantt chart begins once the
  route is known.

## Facilitation outline (about 2–3 hours for a first chart)

1. (15 min) Agree the frame: the project's start, its fixed dates (deadline,
   holidays, council meetings, exam periods) and the time unit, usually weeks.
   Draw the calendar along the top of a wall, a whiteboard or a spreadsheet.
2. (30 min) List the tasks, one per row, each small enough to have one owner
   and to last days or weeks rather than months. Group them under headings
   (phases or work areas) so the chart stays readable.
3. (30 min) For each task, ask the person who will do it how long it takes
   and what has to be finished before it can begin. Note which estimates are
   firm (a supplier's confirmed delivery) and which are guesses.
4. (30 min) Place the bars, earliest possible start first, and draw the
   arrows for dependencies. Add milestones as markers on their dates. Look for
   weeks where too much lands on the same people and move bars that have room.
5. (15 min) Read the chart aloud together. Ask: does anything surprise you?
   Which bars are you not sure of? Missing approvals, ordering times and
   holidays usually turn up here.
6. (15 min) Freeze a copy as the baseline. Agree who updates the chart, how
   often (weekly or fortnightly) and how progress is marked: shading of each
   bar against a line for today's date.
7. (Each update, 10–20 min) Shade progress, move the today line, compare with
   the baseline and talk only about the bars that have fallen behind it.

## Common pitfalls

- Drawing bars at the dates someone wishes for instead of deriving them from
  durations and dependencies; the chart then looks fine until it suddenly
  is not
- Too much detail: a chart with four hundred rows is read by nobody. Show
  summary bars to the board and the detailed rows to the people doing the work
- Overwriting the original dates at every update, so that the chart always
  looks on time and nobody can see how far the project has drifted
- Forgetting work that is not "doing": approvals, procurement, waiting for a
  committee meeting, holidays and illness
- Reading a bar's length as effort. A two-week bar may be two hours of work and
  ten days of waiting; check who is booked on what at the same time
- Treating the chart as a promise. It shows the dates that hold if every
  estimate holds; say so when you present it

## Relation to neighbouring methods

- [Critical Path Method](Critical_Path_Method.md) calculates the longest chain
  of dependent tasks and the float of every other task. A Gantt chart
  *displays* a schedule and is often drawn from that calculation; the two are
  complements, not alternatives.
- [Work Breakdown Structure](Work_Breakdown_Structure.md) breaks a
  project's scope into deliverables and work packages with no time axis. A
  Gantt chart takes those packages and puts them on a calendar.
- [Kanban Board](Kanban_Board.md) visualises the flow of work through stages
  and limits work in progress, without dates. Use it for a stream of
  requests; use a Gantt chart for a project with a planned end.
- [Timeboxing](Timeboxing.md) fixes slots in one person's or a team's calendar
  to protect focused work. It plans attention, not a project.
- [Backcasting](Backcasting.md) works back from a long-term target to the
  steps that must start now. Once those steps are agreed and dated, a Gantt
  chart can show them.
- [RACI Matrix](RACI_Matrix.md) settles who is responsible for each task; the
  Gantt chart shows when each task happens. They are often kept side by side.

## See also

- Wallace Clark, *The Gantt Chart: A Working Tool of Management*, New York:
  Ronald Press, 1922, [archive.org](https://archive.org/details/ganttchartworkin00clar)
  — the first book on Gantt's charts, by one of his colleagues
- Joana Geraldi and Thomas Lechter, "Gantt charts revisited: A critical analysis
  of its roots and implications to the management of projects today",
  *International Journal of Managing Projects in Business* 5(4), 2012,
  pp. 578–594, [doi:10.1108/17538371211268889](https://doi.org/10.1108/17538371211268889)
- Patrick Weaver, ["Henry Gantt vs Karol Adamiecki"](https://mosaicprojects.wordpress.com/2024/09/13/henry-gantt-vs-karol-adamiecki/),
  Mosaic Projects blog, 2024 — on the harmonogram and how it differs from
  Gantt's charts
- James M. Wilson, "Gantt charts: A centenary appreciation", *European Journal
  of Operational Research* 149(2), 2003, pp. 430–437
- Edward R. Marsh, "The Harmonogram of Karol Adamiecki", *Academy of
  Management Journal* 18(2), 1975, pp. 358–364
- [Wikipedia: Gantt chart](https://en.wikipedia.org/wiki/Gantt_chart)
- [Wikipedia: Henry Gantt](https://en.wikipedia.org/wiki/Henry_Gantt)
- [Wikipedia: Karol Adamiecki](https://en.wikipedia.org/wiki/Karol_Adamiecki)
