# Usability Testing (Think-Aloud)

Give a few people from the real audience the thing you have made, whether an
online form, a website, an app, a letter or a set of signs, ask each of them to
do the tasks people actually come to do, and watch while they say aloud what
they are looking at, what they expect and what puzzles them. You do not explain,
help or defend. Where several participants stumble at the same spot, you have
found a problem worth fixing; what they said while stumbling usually tells you
why. Fix the worst problems, then test again with new people.

The thinking-aloud technique entered interface design through Clayton Lewis at
IBM in the early 1980s and draws on the protocol-analysis work of Ericsson and
Simon in cognitive psychology. Jakob Nielsen made the case for small, cheap,
frequent tests ("discount usability"), arguing that about five participants
from one user group expose most of the problems a design has, and that several
small rounds with fixes in between beat one large study. Steve Krug's *Rocket
Surgery Made Easy* (2010) turned this into a do-it-yourself guide for teams
without usability specialists, with an emphasis on a regular, short testing
rhythm and on deciding which problems to fix. Krug stresses that the approach
is not limited to websites: forms, instructions and other everyday material
can be tested the same way.

## When to use

- A form, website, app, letter, leaflet or signage system is live and the help
  desk, counter or secretariat keeps answering the same "how do I…" questions
- Something is about to launch and the team that built it can no longer judge
  whether a newcomer would understand it
- The team argues about what is wrong with a design and wants observation in
  place of opinion
- After a redesign, to check that the fixes worked and did not create new
  problems
- At an early stage, with a paper sketch or a clickable mock-up, while changes
  are still cheap

## When *not* to use

- To find out whether people want or need the service at all. A test shows
  whether they can use it; whether enough of them will take it up calls for
  [Build–Measure–Learn](Build_Measure_Learn.md), and why they turn to it in the
  first place for [Jobs To Be Done](Jobs_To_Be_Done.md).
- When people simply do not act although the form is easy, for example most of
  those entitled never apply. That is a question of how the request reaches
  them; see [Choice Architecture](Choice_Architecture.md).
- When the trouble lies between several offices or channels rather than in one
  product. To follow the whole sequence of contacts, use a
  [Customer Journey Map](Customer_Journey_Map.md).
- To design menus and headings from scratch. How users group content is what
  [Card Sorting](Card_Sorting.md) finds out; a usability test then checks the
  result.
- When you need figures, such as the share of users who complete a task or a
  comparison of two versions. That takes a larger quantitative study or an
  analysis of real usage data, not five sessions.
- For safety-critical systems where an error can hurt someone. Krug himself
  says his informal approach makes things easier to use, not foolproof.

## How it differs from a Design Sprint test day

A [Design Sprint](Design_Sprint.md) also ends with a handful of one-to-one
interviews, but it is a five-day decision process about whether to back a new
idea, with the decision-maker in the room and a mock-up built for the purpose.
A usability test is a standalone, repeatable check of something that exists or
is nearly finished, run by whoever looks after it, as often as needed.

## Facilitation outline

**Preparation (one to two weeks, a few hours of work)**

1. Agree with the team what you want to learn and which parts of the product
   matter most. Pick three to six tasks that reflect why people really come:
   "Register your child for after-school care starting in August", not "Click
   on Services".
2. Word each task as a goal in everyday language, without the labels or button
   names on the screen, so the task does not give away the answer.
3. Recruit four to six participants from the real audience: residents,
   parents, patients, customers, staff from another unit. Avoid the project
   team, its friends and anyone who already knows the product well. If you
   serve clearly different groups, include a few from each.
4. Write a short script: welcome, consent to take notes or record, the tasks,
   closing questions. Try it once with a colleague and fix confusing tasks.
5. Invite observers, ideally the people who will have to fix things. Give them
   a sheet to note the three biggest problems they see in each session.

**Each session (30 to 60 min per participant)**

1. (5 min) Welcome. Explain that you are testing the product, not them, that
   nothing they do can be wrong, and that you will mostly stay quiet. Ask them
   to say aloud what they are looking at, thinking and trying to do.
2. (2 min) A brief warm-up: a few questions about how they normally deal with
   this kind of thing.
3. (20–45 min) Hand over one task at a time. Watch and listen. If they fall
   silent, prompt neutrally ("What are you thinking now?"). Do not explain,
   hint or rescue unless they are completely stuck, and note when you did.
   Answer questions with questions ("What would you expect?").
4. (5 min) Ask what was hardest, what surprised them, and anything they want to
   add. Thank them and explain what happens with their input.
5. Leave at least 15 minutes between sessions for notes.

**Debrief (60 to 90 min, the same day)**

1. (20 min) Each observer names the problems they saw. Collect them on one
   board, merging duplicates and noting how many participants hit each.
2. (20 min) Agree on the handful of most serious problems: those that stopped
   people from completing a task or misled several of them.
3. (20–40 min) For each, agree the smallest change likely to remove it, and who
   makes it before the next round. Prefer tweaks over redesigns.
4. Schedule the next round with new participants to check the fixes.

## Common pitfalls

- Helping participants or explaining the design to them, which hides exactly
  the problems you came to find
- Tasks that name the labels on the screen, turning the test into a word-match
- Testing with colleagues because recruiting real users seemed like too much
  effort
- Treating one participant's comment or preference as a finding; look for
  what several of them did
- Asking people what they would like instead of watching what they do
- Writing a long report nobody reads instead of a same-day debrief with the
  people who will fix things
- Testing once and never again, so nobody checks whether the fixes worked

## See also

- [Design Sprint](Design_Sprint.md) — a week-long decision process that ends in a few tests of a mock-up; usability testing is the stand-alone, repeatable check
- [Card Sorting](Card_Sorting.md) — how people group content and name the groups; usability testing checks whether they then find their way
- [Customer Journey Map](Customer_Journey_Map.md) — the whole sequence of contacts across offices and channels; usability testing zooms in on one form, page or sign
- [Personas](Personas.md) — who the users are; useful for recruiting the right participants
- [Double Diamond](Double_Diamond.md) — the wider design process in which testing is one step
- [Build–Measure–Learn](Build_Measure_Learn.md) — whether people will take it up at all, measured by what they do
- [Gemba Walk](Gemba_Walk.md) — leaders watching staff do their own work, rather than users trying a product
- [Nielsen Norman Group: Thinking Aloud, the #1 Usability Tool](https://www.nngroup.com/articles/thinking-aloud-the-1-usability-tool/) (Nielsen, 2012)
- [Nielsen Norman Group: Why You Only Need to Test with 5 Users](https://www.nngroup.com/articles/why-you-only-need-to-test-with-5-users/) (Nielsen, 2000)
- [Nielsen Norman Group: Usability Testing 101](https://www.nngroup.com/articles/usability-testing-101/) (Moran, 2019)
- [GOV.UK Service Manual: Using moderated usability testing](https://www.gov.uk/service-manual/user-research/using-moderated-usability-testing) — government guidance on planning and running sessions
- [Steve Krug: Rocket Surgery Made Easy](https://sensible.com/rocket-surgery-made-easy/), with a [sample chapter](https://sensible.com/Downloads/rsme-samplechapter.pdf) and free [test scripts, consent form and observer handouts](https://sensible.com/downloads/)
- [Wikipedia: Usability testing](https://en.wikipedia.org/wiki/Usability_testing)
- [Wikipedia: Think aloud protocol](https://en.wikipedia.org/wiki/Think_aloud_protocol)
- Krug, S. (2010). *Rocket Surgery Made Easy: The Do-It-Yourself Guide to Finding and Fixing Usability Problems*. New Riders. ISBN 978-0-321-65729-9.
- Nielsen, J. (1993). *Usability Engineering*. Academic Press.
- Lewis, C. (1982). *Using the "thinking-aloud" method in cognitive interface design*. IBM Research Report RC 9265.
- Ericsson, K. A. and Simon, H. A. (1980). Verbal reports as data. *Psychological Review* 87(3), 215–251.
