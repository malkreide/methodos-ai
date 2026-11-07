# Decision Log

A decision log is a running record of the significant decisions a team or body
has taken, one short entry per decision. Each entry is dated and says what the
situation was, which options were on the table, what was decided and by whom,
why, what the group expects to follow from it and when it will look at the
decision again. Entries are not rewritten once accepted: when a decision
changes, a new entry replaces it and the old one is marked as superseded, so a
reader can follow how the position developed.

The idea has two roots. Councils, boards and associations have long kept
minutes and registers of resolutions, whose main job is to record what was
decided rather than what was said. In software, Michael Nygard's 2011 post
"Documenting Architecture Decisions" proposed the *architecture decision
record*: a one- or two-page text per decision with a title, context, decision,
status and consequences, kept next to the code and numbered in sequence. His
motivation is the one this method addresses everywhere: people who arrive later
either accept a decision they do not understand or overturn it without knowing
what it was protecting. Tyree and Akerman (2005) had earlier proposed a fuller
tabular template for the same purpose, and the format has since been taken up
in public guidance such as the UK Government Digital Service's engineering
standards and Microsoft's Azure Well-Architected Framework.

## What it is not

| | Answers the question |
|---|---|
| [DACI](DACI_Matrix.md) / [RACI](RACI_Matrix.md) | Who drives, approves, contributes, is informed? |
| [Consent Decision-Making](Consent_Decision_Making.md) | How does the group reach the decision? |
| [Weighted Decision Matrix](Weighted_Decision_Matrix.md) | Which option scores best against agreed criteria? |
| [Team Charter](Team_Charter.md) | How will this team work together in general? |
| [After Action Review](After_Action_Review.md) | What can we learn from an event that is over? |
| **Decision Log** | What did we decide, why, and is it still valid? |

The log sits after the others: it keeps the result of whichever decision
procedure was used, so that it can be found, understood and revisited.

## When to use

- The same questions come back again and again, and nobody can show what was
  agreed or which options were already ruled out
- People change often: rotating boards, new school leaders, staff turnover,
  consultants who leave at the end of a contract
- Decisions that are expensive to reverse: technology platforms, suppliers,
  organisational structures, policies affecting many people
- Bodies that have to account for decisions afterwards, for example public
  administrations whose delegated decisions must be recorded with reasons and
  rejected alternatives (in England, regulation 7 of the Openness of Local
  Government Bodies Regulations 2014 requires exactly that for many officer
  decisions)
- Long programmes where early choices constrain later work and the people who
  made them may no longer be around

## When *not* to use

- For small, everyday choices that are easy to undo; logging them is
  bureaucracy, and the noise hides the entries that matter
- When nobody will maintain it. A log that stops being updated misleads
  readers into treating stale entries as current; agree an owner or do not start
- As a cure for poor decisions: the log captures reasoning, it does not test
  it. If the trouble is how decisions are made, use a decision procedure first
- When the real problem is unclear authority. If decisions are reopened because
  nobody knows who may decide, a role framework such as DACI helps more
- In public bodies, check first what freedom-of-information, archiving and
  data-protection rules apply. Entries may be disclosable and should record
  roles and reasons, not personal details or opinions about individuals
- Be aware that the evidence is mostly practitioner experience, much of it from
  software teams; there is little controlled research on its effect

## What an entry contains

1. **Number and title**: a sequential number that is never reused, and a short
   phrase naming the decision ("12: Single learning platform for all classes")
2. **Date and status**: proposed, accepted, superseded (with a link to the
   entry that replaces it)
3. **Context**: the situation and the forces at the time, including
   constraints, deadlines and pressures, written neutrally
4. **Options considered**: including the ones rejected, with one line on why
5. **Decision**: in plain sentences ("We will…"), and who took it
6. **Consequences**: expected effects, good and bad, and how confident the
   group was
7. **Review**: a date or a trigger ("when the contract is renewed") for
   looking at the decision again

Keep each entry to a page. Supporting material can be linked rather than
copied.

## Facilitation outline

### Setting up the log (60 min, once)

1. (10 min) Agree what counts as significant. A useful test: costly to undo,
   affects people outside the group, or likely to be questioned later.
2. (10 min) Agree the template above, adapted to your vocabulary, and where the
   log lives: one shared folder, page or repository that everyone can read.
3. (10 min) Name an owner who makes sure entries are written and statuses kept
   current. Writing can rotate; ownership should not.
4. (25 min) Write entries for two or three past decisions that are still being
   questioned, from whatever records and memories exist. Mark them as
   reconstructed.
5. (5 min) Fix the routine: for example, the last five minutes of each meeting
   check whether a decision was taken that needs an entry.

### Writing one entry (15 to 30 min)

1. (5 min) Straight after the decision, the person who prepared it drafts the
   entry while the reasons are fresh.
2. (5 to 15 min) Those involved read the draft and correct the context and
   the reasons, especially the doubts and trade-offs.
3. (5 min) Mark it accepted, set the review date and link any entry it
   supersedes.

### When a decision is questioned

Open the entry. Ask whether the context it describes has changed or the
expected consequences failed to appear. If so, write a new entry; if not, the
existing one is the answer.

## Common pitfalls

- Recording only the decision and dropping the context and rejected options,
  which are the parts later readers need most
- Editing accepted entries to reflect a new view instead of superseding them,
  which erases the history the log exists to keep
- Writing entries weeks later, when the reasoning has already been tidied up
- Letting review dates pass unnoticed; put them in the calendar
- Logging so much that the significant entries cannot be found

## See also

- [DACI Decision-Making Framework](DACI_Matrix.md) — settles who decides; the log records what they decided
- [Consent Decision-Making](Consent_Decision_Making.md) — a way to decide, with review dates the log can carry
- [Weighted Decision Matrix](Weighted_Decision_Matrix.md) — its criteria and scores make a good "options considered" section
- [Team Charter](Team_Charter.md) — the team's general working agreement, including how it decides
- [After Action Review](After_Action_Review.md) — looks back at an event; the log looks back at a decision
- [Nygard, M. (2011). Documenting Architecture Decisions. Cognitect blog](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
- [ADR GitHub organisation: Architectural Decision Records](https://adr.github.io/) — templates and further reading
- [Microsoft Azure Well-Architected Framework: Maintain an architecture decision record](https://learn.microsoft.com/en-us/azure/well-architected/architect-role/architecture-decision-record)
- [The GDS Way: Documenting architecture decisions](https://gds-way.digital.cabinet-office.gov.uk/standards/architecture-decisions.html) — UK Government Digital Service
- [The Openness of Local Government Bodies Regulations 2014, regulation 7](https://www.legislation.gov.uk/uksi/2014/2095/regulation/7/made) — statutory record of officer decisions in England
- [Wikipedia: Minutes](https://en.wikipedia.org/wiki/Minutes)
- [Tyree, J., & Akerman, A. (2005). Architecture Decisions: Demystifying Architecture. *IEEE Software* 22(2), 19–27](https://doi.org/10.1109/MS.2005.27)
