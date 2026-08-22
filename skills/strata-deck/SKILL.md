---
name: strata-deck
description: >
  Build professional STRATA strategy decks from a working file. Use when
  generating slides, PPTX, or reviewing deck layout. Visuals interpret the
  plan. Never paste phases and never clip sentences with ellipses.
---

# STRATA deck craft

Four skills run inside generate, not only in this folder:

- **story** — all eleven phases become beats
- **visuals** — the picture carries the room
- **copy** — complete sentences, never `…`
- **layout** — one visual, refs in flow, nothing overlaps

See `strata-deck-story`, `strata-deck-visuals`, `strata-deck-copy`,
and `strata-deck-ai`. The generator loads `director_api/deck_skills.py`.

The working file is the plan. The deck is a visual argument. If a slide
could be a screenshot of Phase 07, it is wrong. If a line ends in an
ellipsis, it is wrong.

## After a change

`python -m pytest -q tests/test_deck_craft.py tests/test_generate.py tests/test_pptx_export.py`
