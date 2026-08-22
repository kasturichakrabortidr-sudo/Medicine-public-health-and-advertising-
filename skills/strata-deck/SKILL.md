---
name: strata-deck
description: >
  Build professional STRATA strategy decks from a working file. Use when
  generating slides, PPTX, or reviewing deck layout. Visuals interpret the
  plan. Never paste phases and never clip sentences with ellipses.
---

# STRATA deck craft

Four engines run inside generate, not only in this folder:

- **story** — four acts, every title a brief-specific conclusion
- **visuals** — versus and split carry the room
- **copy** — complete sentences, never `…`
- **critic** — kill empty shout, process notes, and duplicate labels

See `strata-deck-story`, `strata-deck-visuals`, `strata-deck-copy`,
and `strata-deck-ai`. The room lives in `director_api/deck_engines.py`.

The working file is the plan. The deck is a visual argument. If a slide
could be a screenshot of Phase 07, it is wrong. If a line ends in an
ellipsis, it is wrong.

Every pack must also show the strategy spine, not only the science:

- **cohort** — named insights classified Spend / Amplify / Park (table)
- **barriers** — COM-B table from the brief, not a invented map
- **gaps** — uncited brief lines, no effect sizes
- **message** — one market line versus the habit
- **direction** — bet → stand → moves → 30-day ask (flowchart)
- **who** — activation-order bar chart (order, not an impact score)

## After a change

`python -m pytest -q tests/test_deck_craft.py tests/test_generate.py tests/test_pptx_export.py`
