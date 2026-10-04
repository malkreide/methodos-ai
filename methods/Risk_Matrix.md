# Risk Matrix and Risk Register

Rate each identified threat on two scales — how likely it is to happen and how
bad the consequences would be — and place it on a grid with likelihood on one
axis and severity on the other. The cells in the high-likelihood, high-severity
corner mark the threats that get attention and money first. Every threat that
matters is then written into a register with a named owner, an agreed response
(avoid, reduce, transfer or accept) and a date when it will be looked at again.

The grid is often called a probability–impact matrix or heat map. It appears in
the risk assessment techniques catalogued in IEC 31010, supports the risk
analysis and evaluation steps of the ISO 31000 process, and is described in
PMI's project management guidance as a tool for qualitative risk analysis.
Public bodies use it widely; the UK government's *Orange Book* on risk
management, for example, expects departments to keep risk registers with owners.

The matrix *assesses and ranks* threats someone has already named. It is not a
way of discovering them: a [Pre-Mortem](Pre_Mortem.md) or a
[PESTEL scan](PESTEL_Analysis.md) is better at that, and its output can be fed
straight into the register.

## When to use

- A project or programme has a pile of concerns and nobody can say which ones
  are being dealt with, or by whom
- A limited contingency budget has to be spread across many possible threats
- An auditor, board, council or funder asks for evidence that the main threats
  are known, rated consistently and owned
- Several departments or workstreams report threats in different ways and need
  one common scale to compare them
- Planning trips, events or operations where hazards to people must be recorded
  and precautions assigned

## When *not* to use

- **When the dangerous threats are rare and catastrophic.** A one-in-a-thousand
  event with ruinous consequences lands in a "low likelihood" cell and is easily
  coloured amber or green. For those, model the consequences directly or use
  [Scenario Planning](Scenario_Planning.md); do not let a colour decide.
- **When the decision depends on fine differences.** Cox (2008) showed that
  ordinal grids compress very different threats into the same cell, can rank a
  smaller threat above a larger one, and that multiplying the two ordinal ratings
  into a "risk score" is arithmetic on labels, not on quantities. If the choice
  between two mitigations depends on which threat is larger, estimate the
  numbers instead.
- **When nobody has listed the threats yet.** Run a discovery exercise first
  ([Pre-Mortem](Pre_Mortem.md), [PESTEL](PESTEL_Analysis.md)); rating an empty
  or one-person list produces false comfort.
- **When the situation is novel and poorly understood.** Likelihood ratings are
  guesses dressed as data when there is no experience to draw on — see
  [Cynefin](Cynefin_Framework.md) for telling such situations apart.
- **As a substitute for acting.** A colourful grid in a board pack is not a
  mitigation.

## Facilitation outline (2 hours)

Preparation: agree the two scales *before* the session. Use three to five
levels each, and give every level a concrete anchor — for likelihood, a
frequency or rough percentage ("more than once a year", "about a 10 % chance
during the project"); for severity, a description per dimension that matters
(money, time, safety, reputation, service to the public). Decide in advance
which cells count as "act now", "monitor" and "accept".

1. (15 min) Gather the threats. Bring in the existing list, outputs of earlier
   workshops, incident logs. Write each as a cause–event–consequence sentence:
   "Because *X*, *Y* may happen, which would lead to *Z*." Merge duplicates.
2. (40 min) Rate each threat. Participants rate likelihood and severity
   silently first, then compare. Where ratings differ by more than one level,
   discuss the reasons — the disagreement is often more informative than the
   average. Record the worst credible severity, not the worst imaginable one.
3. (15 min) Place the threats on the grid. Step back and check whether the
   picture matches the group's judgement. Flag anything with catastrophic
   severity regardless of its likelihood cell.
4. (35 min) For each threat in the "act now" zone, agree one owner (a person,
   not a team), a response, the next concrete step and a review date. Note the
   expected rating *after* the response.
5. (15 min) Decide how often the register will be reviewed, by whom, and what
   triggers an unscheduled review (a threat materialising, a new phase, a
   change in scope).

## Common pitfalls

- Vague scale words: "likely" means very different things to different
  people. Anchor each level with numbers or examples.
- Treating the product of two ratings as a measurement and ranking by it to
  one decimal place
- Labelling levels 1 to 5 when each level is really about ten times the one
  below it; readers then compare cells as if the steps were equal. Showing the
  levels' actual ranges, or labelling them geometrically, helps (Sutherland
  et al., 2022)
- Ignoring the low-likelihood, high-severity corner because it is not red
- Assigning ownership to a committee or a department, so nobody acts
- Writing vague threats ("budget", "staffing") instead of specific events
  that can be rated and mitigated
- Filling in the register once for an approval gate and never opening it again
- Letting the most senior person's rating anchor everyone else's

## See also

- [Pre-Mortem Analysis](Pre_Mortem.md) — to bring hidden threats to the surface before rating them
- [Scenario Planning](Scenario_Planning.md) — when the uncertainty is too deep for a likelihood rating
- [PESTEL Analysis](PESTEL_Analysis.md) — a structured scan of external sources of threat
- [Eisenhower Matrix](Eisenhower_Matrix.md) — a different two-by-two, for prioritising one's own tasks
- [ISO 31000:2018 Risk management — Guidelines](https://www.iso.org/standard/65694.html)
- [IEC 31010:2019 Risk management — Risk assessment techniques](https://www.iso.org/standard/72140.html)
- [PMI: The PMBOK Guide](https://www.pmi.org/pmbok-guide-standards/foundational/pmbok)
- [Hillson, D. & Hulett, D. (2004). Assessing risk probability: alternative approaches. PMI Global Congress](https://www.pmi.org/learning/library/assessing-risk-probability-impact-alternative-approaches-8444)
- [Cox, L. A. (2008). What's wrong with risk matrices? *Risk Analysis* 28(2), 497–512](https://doi.org/10.1111/j.1539-6924.2008.01030.x)
- [Duijm, N. J. (2015). Recommendations on the use and design of risk matrices. *Safety Science* 76, 21–31](https://doi.org/10.1016/j.ssci.2015.02.014)
- [Sutherland, H. et al. (2022). How people understand risk matrices, and how matrix design can improve their use. *Risk Analysis* 42(5), 1023–1041](https://doi.org/10.1111/risa.13822)
- [HM Treasury: The Orange Book — Management of Risk](https://www.gov.uk/government/publications/orange-book)
- [Wikipedia: Risk matrix](https://en.wikipedia.org/wiki/Risk_matrix)
