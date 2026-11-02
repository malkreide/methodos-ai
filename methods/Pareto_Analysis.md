# Pareto Analysis (Pareto Chart)

Count how often each kind of problem occurs, sort the kinds from most to least
frequent, and add a line showing the running share of the total. In many data
sets a few kinds turn out to account for most of the occurrences; those are
where improvement effort is likely to pay off first.

The pattern is named after the economist Vilfredo Pareto, who observed a
highly unequal distribution of income. Joseph Juran carried the idea into
quality management from the 1940s onwards and described it as separating the
"vital few" from the rest, which he called the "trivial many" and later
preferred to call the "useful many", so that the remaining causes would not be
dismissed as worthless. The Pareto chart is one of the seven basic tools of quality
associated with Kaoru Ishikawa, alongside the cause-and-effect diagram, check
sheet, histogram, scatter diagram, control chart and stratification. It is
widely used in manufacturing, health-care improvement and public services.

## When to use

- A team is spreading its effort across many kinds of complaints, errors or
  requests and wants evidence about which kinds dominate
- The organisation already logs incidents, tickets, defects or complaints with
  a type or reason attached
- Opinions differ about which problem is "the big one" and a count would settle
  the argument
- Before a root-cause analysis, to decide which problem type deserves one
- After a change, to show whether the dominant categories have actually shrunk

## When *not* to use

- When severity matters more than frequency. A rare patient-safety event, data
  breach or injury can sit in the smallest bar and still be the most urgent
  thing on the chart. Weight the counts by cost or harm, or handle such events
  separately.
- When the categories are vague, overlapping or coded differently by different
  people. A large "other" bar or a bar split across near-duplicate labels means
  the classification needs fixing first.
- With very few observations. Improvement guidance commonly suggests at least
  around thirty records; below that, chance can reorder the bars.
- To explain *why* a problem happens. A category tells you where to look, not
  what causes it — follow up with an [Ishikawa diagram](Ishikawa_Diagram.md) or
  [Five Whys](Five_Whys.md).
- To rank ideas, projects or tasks that have no counted history. Pareto works on
  observed occurrences; for judgement-based ordering see
  [RICE Scoring](RICE_Scoring.md) or the [Eisenhower Matrix](Eisenhower_Matrix.md).
- As proof of an exact 80/20 split. The ratio is a rule of thumb; real data may
  be 60/40 or 95/5, and a flat chart is itself a finding.

## Facilitation outline (90 min, data prepared beforehand)

Before the session, one person extracts the records for a defined period (for
example, the last three months) with the problem type for each.

1. (10 min) Agree the question and the measure: count of occurrences, or cost,
   time lost or harm if those are recorded. Confirm the time window.
2. (20 min) Review the categories. Merge duplicates, split catch-alls that hide
   distinct problems, and keep "other" small. Re-tally if the categories change.
3. (15 min) Sort the categories from largest to smallest. Compute each one's
   share of the total and the cumulative percentage. Draw bars for the counts
   and a line for the cumulative share.
4. (20 min) Read the chart together. Where does the cumulative line flatten? Do
   a few bars carry most of the total, or is the distribution flat? Does the
   result match what people expected?
5. (15 min) Check for severe but rare items and for data-quality doubts before
   drawing conclusions.
6. (10 min) Pick the one or two categories to work on, name an owner for the
   follow-up cause analysis, and agree when to redraw the chart with fresh data.

## Common pitfalls

- Treating the most frequent category as the most important without asking
  about severity or cost
- Letting "other" or "miscellaneous" become one of the largest bars
- Comparing charts from different periods or with changed categories as if they
  were the same measure
- Stopping at the chart: knowing which category is largest is not the same as
  knowing what to change
- Forcing the data to show 80/20 and distrusting it when it does not
- Never redrawing the chart, so nobody learns whether the action worked

## See also

- [Ishikawa (Fishbone) Diagram](Ishikawa_Diagram.md) — map the possible causes of the category you chose
- [Five Whys](Five_Whys.md) — drill into a single recurring failure
- [Value Stream Mapping](Value_Stream_Mapping.md) — when the issue is flow and waiting time across a process
- [Issue Tree](Issue_Tree.md) — break down a problem logically when there is no count to start from
- [Wikipedia: Pareto chart](https://en.wikipedia.org/wiki/Pareto_chart)
- [Wikipedia: Pareto principle](https://en.wikipedia.org/wiki/Pareto_principle)
- [Juran Institute: A guide to the Pareto principle and Pareto analysis](https://www.juran.com/blog/a-guide-to-the-pareto-principle-80-20-rule-pareto-analysis/)
- [IHI: Pareto Chart](https://www.ihi.org/library/tools/pareto-chart) — health-care template and instructions
- [NHS England: Quality, Service Improvement and Redesign tools — Pareto (PDF)](https://aqua.nhs.uk/wp-content/uploads/2023/07/qsir-pareto.pdf)
- [NHS Education for Scotland: Pareto chart](https://learn.nes.nhs.scot/2348/quality-improvement-zone/qi-tools/pareto-chart)
- [Wikipedia: Seven basic tools of quality](https://en.wikipedia.org/wiki/Seven_basic_tools_of_quality)
- Juran, J. M. and De Feo, J. A. (eds.) *Juran's Quality Handbook*. McGraw-Hill.
