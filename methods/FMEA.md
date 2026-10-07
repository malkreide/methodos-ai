# FMEA (Failure Mode and Effects Analysis)

Take a process — or the parts of a product or service — one step at a time and
ask, for each step: how could this go wrong (the *failure mode*), what would
that lead to (the *effect*), why would it happen (the *cause*), and what do we
already have in place that would prevent it or catch it (the *current
controls*)? Each line is then rated for how serious the effect is, how often
the cause is likely to occur and how likely it is that the failure is caught
before it does harm. The ratings point the group to the weak points that need
action first; actions get an owner and a date, and the lines are rated again
once the actions are in place.

The method is old and comes from engineering. The US armed forces described
the procedure in MIL-P-1629 in 1949 (later MIL-STD-1629A, 1980); NASA's
contractors used it in the 1960s on Apollo and later space programmes; Ford
brought it into car manufacturing in the 1970s, for designs and for production
processes ("process FMEA"). It is standardised internationally in IEC 60812
(third edition, 2018). In the automotive industry the joint AIAG–VDA handbook
(2019) replaced the classic *risk priority number* — severity × occurrence ×
detection — with *action priority*, a table that maps each combination of the
three ratings to high, medium or low instead of multiplying them. Health care
adopted the method for clinical processes: the US Veterans Health
Administration's National Center for Patient Safety developed Healthcare FMEA
(HFMEA), a five-step version that combines a hazard score with a decision tree
(DeRosier et al., 2002), and the Institute for Healthcare Improvement offers a
free worksheet.

FMEA works *forward* from a process that has not failed yet. Root-cause methods
such as [Five Whys](Five_Whys.md) and the [Ishikawa diagram](Ishikawa_Diagram.md)
work *backward* from a problem that already happened.

## When to use

- Before a new or changed process goes live and a single slip would be costly:
  a registration or enrolment procedure, an exam logistics chain, a payroll
  changeover, a medication round
- When the process has many hand-overs between people, offices or systems, and
  nobody has looked at all of them together
- When a regulator, customer or accreditation body expects a documented,
  step-level analysis (common in automotive, medical devices and hospitals)
- After an incident elsewhere, to check whether the same kind of failure could
  happen in your own version of the process

## When *not* to use

- **When the process is not yet understood or still changing weekly.** FMEA
  needs a stable map of the steps. Map the process first, or try it out small
  with a [PDCA cycle](PDCA_Cycle.md).
- **When you need a quick overview of threats to a whole project.** Rating a
  list of project-level threats on likelihood and impact is faster and enough:
  use a [Risk Matrix](Risk_Matrix.md). FMEA goes step by step and takes far
  longer.
- **When the worry is that the whole plan is wrong, not that a step will
  slip.** A [Pre-Mortem](Pre_Mortem.md) surfaces strategic and political doubts
  that a step-level worksheet never reaches.
- **When something has already gone wrong.** Investigate that failure with
  [Five Whys](Five_Whys.md) or an [Ishikawa diagram](Ishikawa_Diagram.md).
- **When the problem is slowness and waste rather than failure.** That is a job
  for [Value Stream Mapping](Value_Stream_Mapping.md).
- **When the scores would be the decision.** The risk priority number
  multiplies three ordinal ratings; that arithmetic is unsound and can rank a
  rare but catastrophic failure below a frequent, trivial one. A study in two
  UK hospitals (Shebl, Franklin & Barber, 2012) also found that the teams'
  severity and frequency ratings did not match the incident data, and that
  staff outside the team named failures the team had missed. Use the ratings
  to steer the discussion, and treat any line with a very severe effect as a
  candidate for action whatever its total.
- **When failures arise from combinations or from how people and departments
  work together.** FMEA looks at one failure at a time. Interacting failures
  call for fault tree analysis or a systems view such as a
  [causal loop diagram](Causal_Loop_Diagram.md).
- **When nobody has time to act on the results.** A worksheet completed to
  satisfy an auditor and then filed is paperwork, not safety.

## Facilitation outline (3 sessions of about 2½ hours)

Preparation: choose a clear scope (one process, with a defined start and end)
and invite four to eight people who actually do the steps, plus one person from
outside the process who can ask naive questions. Agree the three rating scales
in advance (typically 1–10 or 1–5), with concrete anchors for each level, and
decide whether you will use a risk priority number, an action-priority table or
simply "severity first".

**Session 1 — the map (2½ h)**

1. (15 min) State the scope and the purpose: what must this process reliably
   achieve, and for whom?
2. (60 min) Draw the process as a sequence of steps on a wall or shared board.
   Walk it with the people who do it, not with the procedure manual. Number the
   steps.
3. (60 min) For each step, collect failure modes: how could this step not
   happen, happen late, happen twice, happen to the wrong person or produce the
   wrong result? One sticky note per failure mode.
4. (15 min) Check for gaps: are there steps nobody spoke for? Who should be
   asked before the next session?

**Session 2 — effects, causes, controls and ratings (2½ h)**

1. (60 min) For each failure mode, write down its effect on the person at the
   end of the process, its most likely causes and the controls that exist today.
   Enter the lines into the worksheet.
2. (75 min) Rate severity, occurrence and detection, silently first, then
   compare. Where ratings differ by more than one level, discuss why — the
   difference often reveals that people do the step differently.
3. (15 min) Sort the lines. Look first at every line with a very high severity,
   then at the rest by your agreed scheme.

**Session 3 — actions (2½ h)**

1. (90 min) For the lines selected, agree actions that remove the cause, make
   the failure impossible, or catch it earlier. Prefer design changes over
   "be more careful". Give each action one owner and a date.
2. (30 min) Re-rate the lines as they would be once the actions are in place.
3. (30 min) Decide when the worksheet will be revisited: after go-live, after
   any incident, and when the process changes.

For a small process the three sessions can be squeezed into one long workshop;
for a large one, split the process and run several teams.

## Common pitfalls

- Analysing the documented procedure instead of how the work is actually done
- Writing causes as "human error" or "staff not careful" — ask what makes the
  slip easy and fix that
- Spending most of the time arguing about whether a rating is a 6 or a 7
- Letting the risk priority number decide, so that a catastrophic but rare
  failure ends up below the threshold
- Running it with managers only; the people who do the steps know the failures
- Treating the worksheet as finished; it is meant to be updated as the process
  changes and incidents occur

## See also

- [Risk Matrix and Risk Register](Risk_Matrix.md) — rates a list of
  project-level threats on likelihood and impact, without going step by step
- [Pre-Mortem](Pre_Mortem.md) — imagines that a whole plan has failed and tells
  the story of why
- [Five Whys](Five_Whys.md) and [Ishikawa (Fishbone) Diagram](Ishikawa_Diagram.md)
  — causes of a problem that has already occurred
- [Value Stream Mapping](Value_Stream_Mapping.md) — finds waste and waiting in a
  process rather than ways it can fail
- [Wikipedia: Failure mode and effects analysis](https://en.wikipedia.org/wiki/Failure_mode_and_effects_analysis)
- [IEC 60812:2018, Failure modes and effects analysis (FMEA and FMECA)](https://webstore.iec.ch/en/publication/26359)
- [AIAG & VDA FMEA Handbook (2019)](https://www.aiag.org/training-and-resources/manuals/details/FMEAAV-1)
- [IHI: Failure Modes and Effects Analysis (FMEA) Tool](https://www.ihi.org/library/tools/failure-modes-and-effects-analysis-fmea-tool) — health-care worksheet
- [VA National Center for Patient Safety: Healthcare FMEA](https://www.patientsafety.va.gov/professionals/onthejob/hfmea.asp)
- [DeRosier, J., Stalhandske, E., Bagian, J. P. & Nudell, T. (2002). Using Health Care Failure Mode and Effect Analysis: the VA National Center for Patient Safety's prospective risk analysis system. *Joint Commission Journal on Quality Improvement* 28(5), 248–267](https://doi.org/10.1016/S1070-3241(02)28025-6)
- [Shebl, N. A., Franklin, B. D. & Barber, N. (2012). Failure mode and effects analysis outputs: are they valid? *BMC Health Services Research* 12, 150](https://pmc.ncbi.nlm.nih.gov/articles/PMC3405478/)
- [Liu, H.-C., Liu, L. & Liu, N. (2013). Risk evaluation approaches in failure mode and effects analysis: a literature review. *Expert Systems with Applications* 40(2), 828–838](https://doi.org/10.1016/j.eswa.2012.08.010) — alternatives to the risk priority number
