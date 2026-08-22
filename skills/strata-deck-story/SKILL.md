---
name: strata-deck-story
description: >
  Map all eleven working-file phases onto a visual story arc. Use when
  generating or reviewing STRATA decks. Every required beat must appear;
  none may be a pasted phase table.
---

# Story skill

The working file is the plan. The deck is the argument the room watches.
If a slide could be a screenshot of a phase, it is wrong. If a phase has
no beat, the deck is incomplete.

## Arc (do not skip)

| Phase | Beat | Visual |
| 01 | Why we are here, then the real job | Title chips, then asked vs need |
| 02 | How we judge science | PICO chips |
| 03 | What the papers show | Clinic-of-100, forest, pack jobs |
| 04 | Belief vs papers | Discord cards |
| 05 | Current habit vs required start | Two-stat tension |
| 06 | Where we may stand | Shout vs silent |
| 07 | What we say, what they say back | Pillars, then objections |
| 08 | How contact feels | Sequence flow, then three moves |
| 09 | Who first | Audience cards |
| 10 | How we know | Parent / lead / kill cards |
| 11 | What we need signed | 30-day flow |

References close the pack. Do not add how-built, a questions dump, or
invented revenue charts.

## After a change

`python -m pytest -q tests/test_deck_craft.py` — `storyMap` must list phases 01–11.
