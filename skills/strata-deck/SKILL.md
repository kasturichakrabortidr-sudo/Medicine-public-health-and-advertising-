---
name: strata-deck
description: >
  Build professional STRATA strategy decks from a working file. Use when
  generating slides, PPTX, or reviewing deck layout. Interpret the plan
  visually — never paste working-file phases onto slides.
---

# STRATA deck craft

The working file is the plan. The deck is a visual argument for a room of
marketers, medical, and the client. If a slide could be a screenshot of
Phase 07, it is wrong.

## Non-negotiables

1. **Interpret, do not transcribe.** Each slide answers one question the
   room is about to ask. Titles are conclusions, not section headers.
2. **One visual owns the slide.** People-grid, forest, compare bars, spine,
   board of cards, or a 30-day flow. Not a chart plus a table plus bullets.
3. **No overlapping layout.** 16:9, flex column, refs in the document flow
   (never `position: absolute` over the visual). Max 4 cards. Spine max 2 rows.
   People-grid: one paper per slide.
4. **Science uses the INN**, not the brand. Numbers come from numbered papers.
   Do not invent COM-B scores, revenue indexes, or hazard ratios.
5. **One paper is not a case.** The pack slide shows distinct jobs.

## Story arc (in this order)

| Beat | Question the slide answers | Visual |
| open | Why are we in the room? | Title + three chips |
| tension | What do they do vs what is settled? | Two cards |
| prize | What did the paper actually show? | Clinic-of-100 dots |
| forest | Do the papers agree? | Forest plot |
| compare | What does the next paper add? | Compare bars |
| pack | Why not one reprint? | Paper-job cards |
| pillars | What may we say? | Three message cards |
| execute | How does a finding become a move? | Spine (≤2 rows) |
| moves | What do we do first? | Three move cards |
| ask | What do we need in 30 days? | Three-step flow |
| references | Where are the PMIDs? | Vancouver list |

Do **not** add: how-the-file-was-built, a dump of open questions,
duplicate “what the brief asked”, fake cadence line charts, or
box-plots of unsourced cost.

## Copy limits

- Title ≤ 8 words
- Narrative ≤ 2 sentences
- Card body ≤ ~20 words
- No slide with both `chart` and `table`

## After a change

Run `python -m pytest -q tests/test_deck_craft.py tests/test_generate.py tests/test_pptx_export.py`.
A content slide without a visual (`chart`, `board`, `flow`, or `stat`) is a
craft failure unless it is `title`, `close`, or `references`.
