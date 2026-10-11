# Kepner-Tregoe Problem Analysis (Is / Is Not)

When something has gone wrong and nobody knows why, describe the problem
precisely before guessing at causes. For each of four dimensions (what, where,
when and how much) write down what the problem *is* and, next to it, what it
*could* be but *is not*: the comparable site that still works, the product line
that is unaffected, the days on which nothing happens. The contrast between the
two columns is the clue. Look for what is distinctive about the affected cases
and what has changed there, derive possible causes from those differences, and
keep only a cause that explains every entry on both sides. Confirm it in
practice before acting on it.

Charles Kepner and Benjamin Tregoe, who had worked together at the RAND
Corporation, founded a consulting firm in 1958 on their research into how
managers solve problems and make decisions. They published the approach in
*The Rational Manager* (1965) and revised it in *The New Rational Manager*
(1981). Problem Analysis is one of four linked processes in their system,
alongside Situation Appraisal, Decision Analysis and Potential Problem Analysis.
A 1992 root-cause guidance document of the US Department of
Energy lists it among the standard methods for investigating occurrences, the US
Agency for Healthcare Research and Quality describes a simplified "is / is not"
matrix for health-care teams, and Tregoe later co-wrote a book applying the
processes to school leadership (Richetti and Tregoe, 2001).

## When to use

- Something that used to work has stopped working, or works in some places and
  not in others, and the cause is unknown
- Rival explanations are circulating and each camp wants its own fix
- The problem shows a pattern in place, time, items or scale that could be
  compared, for example only some sites, only after a certain date, only one
  product type
- A fix would be expensive, disruptive or hard to undo, so a wrong guess costs
  a lot
- Several quick fixes have already been tried without lasting effect

## When *not* to use

- When there is no standard to deviate from: designing something new, choosing
  a strategy, or a general feeling that things could be better. Use
  [Issue Tree](Issue_Tree.md) to structure a broad question instead.
- When the facts about where and when the problem occurs are not available and
  cannot be gathered. The method compares facts; without them the "is not"
  column fills up with assumptions.
- When a quick answer is good enough. A single, well-understood failure is
  usually served faster by [Five Whys](Five_Whys.md).
- When several causes interact, or the problem grows through feedback over
  time. The logic looks for one cause that explains the whole pattern, and an
  outcome produced by several factors together can pass every test only
  partly. Map such problems with an [Ishikawa diagram](Ishikawa_Diagram.md) or a
  [Causal Loop Diagram](Causal_Loop_Diagram.md).
- Before anything has failed. To find weak points in a process ahead of time,
  use [FMEA](FMEA.md).
- If you need independent evidence of effectiveness. The full procedure and
  worksheets are taught through the originators' commercial training, and what
  is published about results comes mostly from practitioners and the firm
  itself rather than from controlled studies.

## Facilitation outline (2 hours, facts gathered beforehand)

Before the session, one person collects what is known: logs, dates, locations,
batch or version numbers, and a list of recent changes.

1. (10 min) State the deviation in one sentence: what should happen, what
   happens instead, on which object. No causes yet. If the group describes
   several problems, split them and analyse one at a time.
2. (35 min) Fill a four-row table with two columns, *is* and *is not*:
   - **What**: which object or item is affected, and what exactly is wrong with
     it; which similar items could be affected but are not.
   - **Where**: on which sites, machines, teams or parts of the object; where
     it could occur but does not.
   - **When**: when it was first seen, since when, at what time of day or point
     in a process; when it could occur but does not.
   - **Extent**: how many items, how often, how severe, and whether it is
     growing or stable; what a larger or smaller extent would look like.
   Every "is not" must be a close comparison that could plausibly be affected,
   not just anything that is not the problem. Mark gaps in the facts instead of
   filling them with opinion.
3. (20 min) For each row, ask what is distinctive about the *is* side compared
   with the *is not* side. Then ask what has changed in or around each
   distinction, and when.
4. (20 min) From the distinctions and changes, write possible causes as
   statements: "the change X produced the effect Y by way of Z." Include the
   theories people arrived with, but treat them the same way.
5. (25 min) Test each possible cause against every line of the table: does it
   explain why the problem *is* here and *is not* there? Discard causes that
   fail a line, or note the assumption they need to survive. The most probable
   cause is the one that fits all facts with the fewest assumptions.
6. (10 min) Plan how to confirm that cause in reality (a check, a controlled
   trial, reversing a change, an inspection) and name an owner. Only then
   decide on the fix.

## Common pitfalls

- Starting with causes and filling the table to support a favourite theory
- Writing "is not" entries that nobody would ever expect to be affected, which
  makes every cause look plausible
- Treating a missing fact as a negative fact; mark it and go and find out
- Merging two different problems into one table, so no single cause can fit
- Explaining away a line that does not fit, instead of discarding the cause
- Acting on the best candidate without confirming it, then finding the problem
  comes back

## See also

- [Five Whys](Five_Whys.md): a single chain of "why" questions from one known
  failure, quicker but less rigorous
- [Ishikawa (Fishbone) Diagram](Ishikawa_Diagram.md): gathers every possible
  cause by category; the Is / Is Not table then tests which of them fits
- [Pareto Analysis](Pareto_Analysis.md): shows which few problem types account
  for most cases, to choose which one to analyse
- [Issue Tree](Issue_Tree.md): splits a broad question into parts without
  needing a deviation from a standard
- [FMEA](FMEA.md): looks for failures before they happen
- [Causal Loop Diagram](Causal_Loop_Diagram.md): for problems driven by feedback
  between several factors
- [After Action Review](After_Action_Review.md): learning from a completed
  event rather than diagnosing an unexplained fault
- Kepner, C. H. and Tregoe, B. B. (1965). *The Rational Manager: A Systematic
  Approach to Problem Solving and Decision Making*. New York: McGraw-Hill.
  [Internet Archive record](https://archive.org/details/rationalmanagers0000kepn)
- Kepner, C. H. and Tregoe, B. B. (1981). *The New Rational Manager*.
  Princeton, NJ: Princeton Research Press.
- [US Department of Energy (1992). DOE-NE-STD-1004-92, Root Cause Analysis Guidance Document](https://www.energy.gov/ehss/articles/doe-ne-std-1004-92):
  lists Kepner-Tregoe among the root-cause methods and notes that it requires
  formal training
- [AHRQ: Kepner-Tregoe Matrix](https://digital.ahrq.gov/health-it-tools-and-resources/evaluation-resources/workflow-assessment-health-it-toolkit/all-workflow-tools/kepner-tregoe-matrix):
  a simplified is / is not worksheet for health-care teams
- [CREATE handbook (University of Udine): Kepner and Tregoe methods](https://create-labgest.uniud.it/Handbook/techniques/List/Kepner.php)
- [Richetti, C. T. and Tregoe, B. B. (2001). *Analytic Processes for School Leaders*. ASCD](https://www.ascd.org/books/analytic-processes-for-school-leaders)
- [Wikipedia: Benjamin Tregoe](https://en.wikipedia.org/wiki/Benjamin_Tregoe)
