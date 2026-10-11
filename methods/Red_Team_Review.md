# Red Team Review

Before a plan is approved, hand it to a small group that had no part in writing
it and give them one job: find out why it is wrong. They test the assumptions it
rests on, look for what its authors left out, and build the best case for a
different course. The decision-maker hears that case alongside the plan, and
decides with both in front of them.

The idea is old. The Catholic Church appointed an official to argue against
candidates for sainthood; military staffs have long assigned officers to
play the enemy in planning exercises. In management research the same impulse
was studied from the late 1960s onward as *devil's advocacy* (one person or group
critiques the plan) and *dialectical inquiry* (a group builds a counter-plan on
opposite assumptions, after Richard Mason's and Ian Mitroff's work on strategic
planning). Today the best-documented practical guides come from defence: the UK
Ministry of Defence's *Red Teaming Handbook* and the US Army's *Red Team
Handbook*, taught at its University of Foreign Military and Cultural Studies
(UFMCS) as part of what it calls "applied critical thinking". The UK handbook
is explicitly written for civilian as well as military readers.

## When to use

- A significant, hard-to-reverse commitment is coming up — a budget, a
  restructuring, an acquisition, a policy, a school merger
- The plan was written by people who are invested in it, and the sponsor has
  already made their preference known
- People lower down will not contradict the senior person in the room
- The alternatives were dismissed early and nobody has looked at them since
- There is still enough time, and willingness, to change or drop the plan

## When *not* to use

- When the findings cannot change anything: the contract is signed, the money is
  spent, or the leader has said the decision is final. A review then only
  produces resentment and false reassurance.
- Without a sponsor who will protect the reviewers. If challenging the boss's
  plan can damage a red team member's career, you will get a polite report.
- When you cannot find reviewers who are genuinely independent of the plan and
  credible to the people who wrote it — a red team made of the authors'
  subordinates is the same team with a new name.
- For small or easily reversible decisions; the cost in people and time is out
  of proportion. A [Pre-Mortem](Pre_Mortem.md) with the plan's own team is far
  cheaper.
- As a routine stamp on every project. Once it becomes a ritual, a plan that
  "passed the red team" looks tested when it was not.
- As a promise of better outcomes. Laboratory and classroom studies compared
  devil's advocacy and dialectical inquiry with seeking consensus or relying on
  an expert, and found the structured dissent produced better recommendations
  (Schweiger, Sandberg & Ragan, 1986; Schwenk's meta-analysis, 1990). Evidence
  from real organisations is mostly case reports and practitioner accounts.

## Facilitation outline (one-day review)

A large review runs over several weeks with the same shape; the times below
are for a compact version on a plan of moderate size.

Before the day: the **sponsor** — the person who will make the decision —
writes the brief: which plan, which question the red team must answer, what is
out of scope, the date the decision will be taken, and a written promise that
the findings will be heard before it is. The red team (about four to eight
people, mixing subject experts with sharp outsiders) receives the plan and its
supporting material a few days in advance.

1. (30 min) **Briefing.** The plan's authors present it and answer factual
   questions only. No defending, no debate. Then they leave.
2. (60 min) **Assumptions.** Each red team member writes down, alone, every
   assumption the plan needs to be true — stated or unstated. Pool them, then
   sort by two questions: how sure are we that this holds, and what happens to
   the plan if it does not?
3. (90 min) **Attack.** For the shakiest load-bearing assumptions: what evidence
   supports them, what would show them false, and how would the plan fare? Take
   the view of whoever the plan affects or opposes — a competitor, the
   citizens it is for, the staff who must run it.
4. (90 min) **Strongest alternative.** Build the best case for a different
   course: an option the authors rejected, doing nothing, or a new one. Argue it
   as its advocates would, not as a straw man.
5. (60 min) **Findings.** Agree three to five findings, each with its evidence
   and what would resolve it. Criticise the plan, never the people.
6. (60 min) **Read-out.** The red team presents to the sponsor and the plan's
   authors together. The authors respond; the sponsor decides what changes, and
   records which findings were accepted, rejected and why.

## Common pitfalls

- Choosing reviewers for their loyalty or their hostility. Both distort the
  result; the aim is independence and credibility.
- An unclear brief. Without a defined question the red team either reviews
  everything superficially or chases its own interests.
- Letting the read-out become a trial. Plan owners who feel prosecuted defend
  rather than listen; keep the findings about the plan.
- A sponsor who commissions the review and then ignores it. Next time nobody
  will bother — and the flawed plan now carries a seal of approval.
- Using a standing red team for everything. Reviewers who see every plan become
  predictable and, over time, part of the establishment they are meant to test.

## See also

- [Pre-Mortem Analysis](Pre_Mortem.md) — the plan's own team imagines it has
  failed; cheap and fast, but not independent
- [Six Thinking Hats](Six_Thinking_Hats.md) — everyone takes the critical view
  in turn, instead of a separate group holding it
- [Risk Matrix](Risk_Matrix.md) and [FMEA](FMEA.md) — rate known risks and
  failure points once the plan itself is accepted
- [Weighted Decision Matrix](Weighted_Decision_Matrix.md) — compare options on
  agreed criteria; a red team questions whether the criteria and options are right
- [Consent Decision-Making](Consent_Decision_Making.md) — a group decides
  together; a red team informs one decision-maker
- UK Ministry of Defence, [Red Teaming Handbook, 3rd edition](https://www.gov.uk/government/publications/a-guide-to-red-teaming)
  (2021) — red team set-up, sponsor role, principles and techniques
- TRADOC G-2 / UFMCS, [The Red Team Handbook, version 9.0](https://home.army.mil/hawaii/7517/5978/4767/Red_Team_Handbook.pdf)
  — the US Army's guide, including Team A / Team B analysis
- TRADOC G-2, [The Applied Critical Thinking Handbook 7.0](https://nsiteam.com/social/the-applied-critical-thinking-handbook-7-0/) (2015)
- Schwenk, C. R. (1990). [Effects of devil's advocacy and dialectical inquiry on decision making: A meta-analysis](https://doi.org/10.1016/0749-5978(90)90051-A).
  *Organizational Behavior and Human Decision Processes* 47(1), 161–176
- Schweiger, D. M., Sandberg, W. R. & Ragan, J. W. (1986). [Group approaches for improving strategic decision making](https://doi.org/10.2307/255859).
  *Academy of Management Journal* 29(1), 51–71
- Mason, R. O. (1969). [A dialectical approach to strategic planning](https://doi.org/10.1287/mnsc.15.8.B403).
  *Management Science* 15(8), B403–B414
