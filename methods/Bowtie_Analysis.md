# Bowtie Analysis

Pick one event you never want to happen and put it in the middle of a page.
To its left, draw the separate ways it could come about; to its right, the
harm that could follow once it has happened. On each route, mark the measures
that are supposed to interrupt it: on the left the ones meant to stop the
event, on the right the ones meant to limit the damage afterwards. The finished
drawing narrows towards the centre from both sides, which gives the method its
name.

The vocabulary varies between sources, but the parts are the same. The
**hazard** is the thing that can cause harm (personal data, a group of children
away from school, a flammable store). The **top event** is the moment control
over it is lost: the data has left the organisation, the child is no longer
with the group. **Threats** are the direct causes of that moment, and
**consequences** its results. **Preventive barriers** sit on the threat side,
**mitigating or recovery barriers** on the consequence side. **Escalation
factors**, called degradation factors in the newer process-safety terminology,
are the conditions that make a barrier fail: a broken sensor, a substitute
teacher who does not know the head-count routine, an out-of-date contact list.

The diagram grew out of fault-tree and event-tree analysis. Its first
appearance is often traced to ICI course notes from the late 1970s, though the
attribution is disputed; Royal Dutch Shell is usually credited as the first
company to build it into everyday risk management, in the early 1990s. It
spread from oil and gas to chemicals, aviation, defence, health care and
information security. The UK Civil Aviation Authority promotes it for safety
management systems, IEC 31010:2019 lists it among recognised risk assessment
techniques, and in 2018 the Center for Chemical Process Safety and the Energy
Institute published a joint book (*Bow Ties in Risk Management: A Concept Book
for Process Safety*, Wiley) to give the method common terms and rules.

## When to use

- A single event would be serious enough that it deserves a picture of its
  own, and people disagree or simply do not know what protects against it
- A procedure lists many safety measures and nobody can say which of them
  would actually stop the event
- You need to show a regulator, data-protection officer, board or school
  authority what is in place for a specific scenario and who maintains it
- Planning both sides at once: how to prevent the event and how to respond if
  it happens anyway
- After an incident or near miss, to check which barriers held, which failed
  and which were never there (alongside, not instead of, a cause analysis)

## When *not* to use

- **To survey or rank many risks.** A bowtie covers one top event. For a
  register of everything that could go wrong, use a
  [Risk Matrix](Risk_Matrix.md) and draw bowties only for the few entries that
  matter most.
- **To walk through a process step by step.** If the question is where in a
  sequence of tasks something could fail, [FMEA](FMEA.md) is built for that.
- **To find out why something already went wrong.** Use the
  [Ishikawa Diagram](Ishikawa_Diagram.md) or [Five Whys](Five_Whys.md); a
  bowtie describes defences, not the root cause of a past failure.
- **To imagine how a whole project could fail.** A [Pre-Mortem](Pre_Mortem.md)
  is faster and generates threats more freely.
- **When you need a number.** A bowtie is qualitative. It says nothing about
  how likely the event is or how much each barrier reduces it unless it is
  linked to quantified fault and event trees.
- **When nobody will check the barriers.** A measure written on the diagram is
  a claim, not a fact. If no one will test whether the barriers exist and work,
  the diagram is likely to give false reassurance, and the more boxes it has,
  the stronger that false impression.
- **When causes interact in loops.** The straight lines cannot show causes
  that combine or reinforce each other; a
  [Causal Loop Diagram](Causal_Loop_Diagram.md) fits that better.

## Facilitation outline (3 hours)

Preparation: choose the one top event in advance, phrased as the moment control
is lost ("a pupil is not with the group and staff do not know where", not "a
child is harmed" and not "poor supervision"). Invite people who do the work,
not only those who wrote the procedures.

1. (15 min) Agree the hazard and the top event. Check that the event is a
   single, recognisable moment and that it can still be recovered from; if it
   is already the final harm, move it one step earlier.
2. (30 min) Collect threats: every distinct way the event could come about.
   Each threat must be able to cause the event on its own. Merge overlapping
   ones; four to eight is typical.
3. (25 min) Collect consequences: what could follow once the event has
   happened, from the likely to the worst credible.
4. (40 min) Place the preventive barriers on each threat line. For every
   candidate, ask whether it could stop this threat on its own, whether it is
   independent of the threat and of the other barriers on that line, and
   whether anyone could check that it is in place. Training, supervision and
   general policies usually support barriers rather than being barriers;
   record them separately.
5. (30 min) Place the recovery barriers on each consequence line in the same
   way: what would detect the event, who would decide what to do, and what
   action would limit the harm.
6. (20 min) For the barriers the group relies on most, list the escalation
   factors that could defeat them (staff absence, a dead phone battery, a
   system update) and what keeps those in check.
7. (20 min) Mark each barrier as working, weak, or not verified, and write one
   named owner next to it. Agree actions for the gaps: lines with no barrier,
   lines resting on one weak barrier, and barriers nobody owns.

Afterwards, review the diagram at fixed intervals or when something changes:
new threats, a barrier temporarily out of service, a near miss.

## Common pitfalls

- A top event that is really a cause ("staff shortage") or a final outcome
  ("pupil injured"), which scrambles the two sides
- Twenty or more "barriers" per line; a list that long nearly always mixes
  real barriers with training, audits and good intentions, and suggests more
  protection than exists
- Drawing only the preventive side; teams new to the method tend to neglect
  detection and response
- Treating the finished diagram as the outcome; risk falls only when a weak
  barrier is repaired or a missing one is added
- Barriers owned by "the school" or "IT" instead of a person who can be asked
  whether it works today
- Scoring barriers with elaborate numerical systems that absorb the time
  needed for checking them
- Drawing many bowties at once before the group has learned from two or three

## See also

- [Risk Matrix and Risk Register](Risk_Matrix.md) — to rate and rank many risks and choose which deserve a bowtie
- [FMEA](FMEA.md) — failure modes of each step in a process
- [Pre-Mortem Analysis](Pre_Mortem.md) — imagining how a project or plan could fail
- [Ishikawa (Fishbone) Diagram](Ishikawa_Diagram.md) — the causes of a problem that has already occurred
- [Scenario Planning](Scenario_Planning.md) — when the uncertainty is about the future environment, not one event
- [Johnson, M., Manton, M., Cowley, C. & Scanlon, M. (2018). Bow ties in risk management: using the new CCPS-EI book to avoid pitfalls. IChemE Hazards 28, Symposium Series 163](https://www.icheme.org/media/16937/hazards-28-paper-31.pdf)
- [UK Civil Aviation Authority: Introduction to bowtie](https://caa.co.uk/Safety-initiatives-and-resources/Working-with-industry/Bowtie/About-Bowtie/Introduction-to-bowtie)
- [UK Civil Aviation Authority: Where did bowtie come from?](https://www.caa.co.uk/safety-initiatives/working-with-industry/bowtie/about-bowtie/where-did-bowtie-come-from/)
- [UK Ministry of Defence, ASEMS toolkit: Bow-tie diagram](https://www.asems.mod.uk/node/28)
- [Abdi, Z. et al. (2016). Application of Bow-tie methodology to improve patient safety. *International Journal of Health Care Quality Assurance* 29(4), 425–440](https://doi.org/10.1108/IJHCQA-10-2015-0121)
- [Meland, P. H. et al. (2019). An experimental evaluation of bow-tie analysis for security. *Information and Computer Security* 27(4), 536–561](https://doi.org/10.1108/ICS-11-2018-0132)
- [Wikipedia: Bow-tie diagram](https://en.wikipedia.org/wiki/Bow-tie_diagram)
- CCPS & Energy Institute (2018). *Bow Ties in Risk Management: A Concept Book for Process Safety*. Hoboken, NJ: Wiley. ISBN 978-1-119-49039-5
- IEC 31010:2019, *Risk management — Risk assessment techniques*
