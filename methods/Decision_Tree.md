# Decision Tree

Draw the decision as it unfolds in time: a square wherever you choose, a circle
wherever something uncertain happens to you, and a value at the end of every
path. Then work from right to left. At each circle, weight the values by how
likely each branch is; at each square, keep the branch with the better result.
What arrives back at the first square is the option that does best on average,
together with the reasons why.

The technique was brought to managers by John Magee's 1964 *Harvard Business
Review* article on choosing the size of a new plant under uncertain demand, and
given its theoretical footing by Howard Raiffa's lectures on decision analysis
(1968). It is taught in management accounting and used in clinical decision
analysis, and the same structure fits any situation where "act now, or wait and
learn more first?" is the real question.

## When to use

- A commitment has to be made before an important uncertainty is resolved, such
  as a pending political decision, uncertain demand or the result of a test
- The group keeps arguing past each other because some treat an uncertain event
  as a choice ("we'll just make sure the merger doesn't happen")
- You are considering a pilot, a study or simply waiting, and need to know
  whether the information it buys is worth its cost and delay
- The decision has two or three stages, not twenty

## When *not* to use

- When the probabilities would be pure invention and the result would hide that
  behind a decimal point. A rough range you trust beats a precise figure you
  don't; if even the range is unknowable, use [Scenario Planning](Scenario_Planning.md)
- Under deep uncertainty, where nobody can list the possible events with
  confidence — decades-long horizons, technology shifts, political upheaval
- When the outcomes matter in ways that do not reduce to one scale (money,
  equity, wellbeing) and the group would not accept trading them off. Compare
  the options on several criteria instead with a
  [Weighted Decision Matrix](Weighted_Decision_Matrix.md)
- When there is no uncertainty in sequence: one option to price is a
  [Cost-Benefit Analysis](Cost_Benefit_Analysis.md); a list of threats to sort
  is a [Risk Matrix](Risk_Matrix.md)
- When the tree would need more than three or four stages; it grows faster than
  anyone can read it, and the analysis belongs in a model, not a workshop

## Facilitation outline (2–3 hours, plus preparation)

1. (15 min) State the decision that has to be taken now, its deadline, and the
   measure of outcome you will use (cost over ten years, pupils served, cases
   avoided). Agree on one measure, or decide this method is the wrong one.
2. (30 min) Draw the tree left to right. List the options at the first square.
   For each, ask "what happens next that we do not control?" and draw a circle
   with its possible results. Add a later square only where the group would
   genuinely get to choose again. Keep the number of branches small.
3. (15 min) Check the order. Every circle must sit where the uncertainty is
   actually resolved, and every square where the decision is actually taken.
   Mixing these up is the most common error.
4. (30 min) Estimate probabilities for each circle, as ranges first. Use
   available evidence and the people closest to it; record who estimated what.
   The branches at each circle must add up to 100%.
5. (20 min) Put a value on every end point, using the measure from step 1.
6. (20 min) Roll back: from the right, compute the weighted average at each
   circle and pick the best branch at each square. Write the results on the tree.
7. (20 min) Test it. Vary the most disputed probability and value across their
   ranges and find the point at which the preferred option changes. Compare
   "decide now" with "learn first, then decide" to see what the extra
   information is worth.
8. (10 min) Decide, and record which estimate the choice hinges on and when it
   should be revisited.

Preparation (cost figures, base rates, earlier pilots) usually takes longer
than the workshop. For a quick first pass, steps 1–3 alone already clarify a
muddled discussion.

## Common pitfalls

- Treating the average result as what will happen; in a one-off decision you
  get one branch, not the average
- Ignoring how badly a rare outcome would hurt. If one branch is ruinous, look
  at it on its own, not only through its weighted contribution
- Anchoring on the first probability someone says aloud — collect estimates
  independently before discussing them
- Leaving out "wait" or "do nothing yet" as an option at the first square
- Adding branches until the tree looks thorough and nobody can check it

## See also

- [Scenario Planning](Scenario_Planning.md) — when the futures are too uncertain to put probabilities on
- [Weighted Decision Matrix](Weighted_Decision_Matrix.md) — several options against several criteria, no sequence of events
- [Cost-Benefit Analysis](Cost_Benefit_Analysis.md) — supplies the money values at the end points
- [Pre-Mortem Analysis](Pre_Mortem.md) — for finding the failure branches nobody has drawn
- [Delphi Method](Delphi_Method.md) — for estimating probabilities from a dispersed expert panel
- [Magee, J. F. (1964). Decision Trees for Decision Making. *Harvard Business Review*, July 1964](https://hbr.org/1964/07/decision-trees-for-decision-making)
- [Raiffa, H. (1968). *Decision Analysis: Introductory Lectures on Choices under Uncertainty*. Addison-Wesley](https://archive.org/details/decisionanalysis0000raif)
- [ACCA: Decision trees](https://www.accaglobal.com/gb/en/student/exam-support-resources/fundamentals-exams-study-resources/f5/technical-articles/decision-trees.html) — worked example including the value of perfect information
- [Bae, J.-M. (2014). The clinical decision analysis using decision tree. *Epidemiology and Health* 36, e2014025](https://pmc.ncbi.nlm.nih.gov/articles/PMC4251295/)
- [Wikipedia: Decision tree](https://en.wikipedia.org/wiki/Decision_tree) and [Expected value of perfect information](https://en.wikipedia.org/wiki/Expected_value_of_perfect_information)
