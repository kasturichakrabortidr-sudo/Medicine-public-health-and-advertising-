---
name: strata-deck-ai
description: >
  Four-engine STRATA deck room, plus optional multi-provider title ensemble.
  Use when wiring STRATA_DECK_AI or reviewing whether copy invents numbers.
---

# STRATA deck engines

`director_api/deck_engines.py` always runs Story, Visuals, Copy, and Critic
after the craft walk. That is the author.

`director_api/deck_ai.ensemble_titles` is optional seasoning. It fans out
to OpenAI, Anthropic, and Gemini in parallel only when **both** are true:

- `STRATA_DECK_AI` is `1`, `on`, or `true`
- at least one of `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`

Otherwise the directed pack is unchanged. Tests stay deterministic.

## What engines may do

- Write conclusion titles
- Contrast asked vs need, wait vs start, shout vs silent
- Split glued fragments into complete sentences

## What they must not do

- Invent numbers, trial names, HRs, NNTs, or PMIDs
- Add a paper that is not on the register
- Paste working-file phases onto slides
- Clip with `…`

## After a change

`python -m pytest -q tests/test_deck_craft.py`
