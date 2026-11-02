# Card Sorting

Write each piece of content on its own card, hand a stack of cards to people
who actually use the website, intranet or handbook, and ask them to sort the
cards into groups that make sense to them. Across enough participants, the
patterns show which items users expect to find together and what they would
call each group. That is the raw material for menus, headings and folders that
follow the users' logic instead of the organisation chart.

The technique comes from knowledge elicitation in psychology and expert-systems
research (Rugg and McGeorge, 1997, give a tutorial overview) and became a
standard information-architecture method in web design from the 1990s onwards.
Donna Spencer's *Card Sorting: Designing Usable Categories* (Rosenfeld Media,
2009) is the book-length practitioner guide.

## Variants

| Variant | What participants do | Use it to |
|---|---|---|
| Open sort | Form their own groups and give each group a name | Discover how users think about the content and what words they use |
| Closed sort | Place cards into categories you have defined | Check whether a proposed set of categories works and where items are contested |
| Hybrid sort | Use your categories but may add their own | Test a draft while leaving room for missing groups; the given names tend to anchor people, so read new groups carefully |

Sorts can be moderated (in person or on a video call, participant thinks aloud)
or unmoderated (an online tool, many participants, no conversation). Moderated
sessions explain *why* people group things; unmoderated ones give numbers.

## When to use

- Before restructuring a website, intranet, portal or document collection whose
  current menus mirror internal units or jargon
- When a new service catalogue or information site is being planned and nobody
  knows what headings the audience would expect
- When staff and users argue about where something "belongs" and you want
  evidence instead of opinions
- To check a proposed set of categories (closed sort) before the menus are built

## When *not* to use

- To find out whether people can actually locate things in a given structure.
  Card sorting is generative; it suggests groupings. Test the resulting
  navigation with a findability test such as tree testing, where participants
  look for specific items in a bare text menu.
- With only a handful of participants. Jakob Nielsen, drawing on a study by
  Tullis and Wood, recommends about fifteen people for an open sort; with five,
  the groupings correlate poorly with those from a larger sample.
- For designing the sequence of steps in a process or form; that is about task
  flow, not grouping. To see what people go through over time, use a
  [Customer Journey Map](Customer_Journey_Map.md).
- When the content is so large or varied (hundreds of items across very
  different audiences) that no single stack is representative; split it first.
- When you cannot write cards in the users' own words. Cards that repeat
  internal titles invite participants to match words rather than meaning.

## Facilitation outline

**Preparation (half a day to a day)**

1. Choose 30 to 60 items that represent the content: frequent visitor
   requests, search logs, the most-read pages, and a few awkward cases. Keep
   them at the same level of detail.
2. Write each card in plain language, as a user would say it. Avoid the words
   that are candidate group names, so participants are not led to them.
3. Recruit participants from the real audience: parents, residents, staff,
   not the project team. Aim for about fifteen for an open sort, more for a
   quantitative closed sort. Run one pilot session and fix confusing cards.

**Each session (20 to 45 min per participant or pair)**

1. (3 min) Explain that there are no right answers and that a pile of cards
   they do not understand is a useful result too.
2. (15–30 min) Participants sort. In an open sort they then name each group.
   If moderated, ask them to think aloud and note hesitations.
3. (5 min) Ask about the hardest cards and the groups they felt unsure of.

**Analysis (2 to 4 hours)**

1. Build a similarity matrix: for each pair of cards, the share of
   participants who placed them in the same group. Online tools do this
   automatically; a spreadsheet works for small studies.
2. Look at a dendrogram (a cluster tree derived from the matrix) to see
   which items form stable clusters and which drift between groups.
3. Compare participants' group names; repeated words are candidates for
   headings.
4. List the contested items. They need clearer names, cross-links or a
   place in more than one group.
5. Draft the structure, then test it with a findability test before building.

## Common pitfalls

- Treating the most common grouping as the answer without checking whether
  people can find things in it
- Recruiting colleagues instead of the actual audience
- Cards that are too vague, too detailed, or that mix topics with tasks
- Reading meaning into clusters from very few participants
- Ignoring the comments of moderated sessions, which explain the numbers
- Copying participants' group names verbatim when several of them are vague
  ("general", "other", "miscellaneous")

## See also

- [Customer Journey Map](Customer_Journey_Map.md) — what people go through over time, across touchpoints; card sorting is about how they group content
- [Jobs To Be Done](Jobs_To_Be_Done.md) — why people turn to a service at all, before deciding how to organise it
- [Issue Tree](Issue_Tree.md) — breaking a question into logical sub-questions; the hierarchy there is the analyst's, not the users'
- [Double Diamond](Double_Diamond.md) — the wider design process in which card sorting is one research tool
- [Nielsen Norman Group: Card Sorting: Uncover Users' Mental Models](https://www.nngroup.com/articles/card-sorting-definition/) (Tankala and Sherwin, 2024)
- [Nielsen Norman Group: Card Sorting: How Many Users to Test](https://www.nngroup.com/articles/card-sorting-how-many-users-to-test/) (Nielsen, 2004)
- [Nielsen Norman Group: Open vs. Closed Card Sorting](https://www.nngroup.com/videos/open-vs-closed-card-sorting/) (video, Whitenton, 2018)
- [Nielsen Norman Group: Tree Testing: Evaluate Menu Labels and Categories](https://www.nngroup.com/articles/tree-testing/) (Laubheimer, 2023) — the evaluative follow-up
- [Spencer, D. and Warfel, T. (2004). Card Sorting: A Definitive Guide. *Boxes and Arrows*](https://boxesandarrows.com/card-sorting-a-definitive-guide/)
- [Digital.gov (US GSA): Open-source information architecture design, card sorting and tree testing with the tools you have](https://digital.gov/2022/01/06/open-source-information-architecture-design-using-the-tools-you-have-to-conduct-card-sorting-and-tree-testing/) (McHarg, Faied and Goldstein, 2022) — a government case
- [Wikipedia: Card sorting](https://en.wikipedia.org/wiki/Card_sorting)
- Spencer, D. (2009). *Card Sorting: Designing Usable Categories*. Rosenfeld Media. ISBN 978-1-933820-02-6.
- Rugg, G. and McGeorge, P. (1997). The sorting techniques: a tutorial paper on card sorts, picture sorts and item sorts. *Expert Systems* 14(2), 80–93. doi:10.1111/1468-0394.00045
