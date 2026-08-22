---
name: strata-deck-ai
description: >
  Optional LLM polish for STRATA slide headlines. Use when wiring STRATA_DECK_AI,
  choosing a deck model, or reviewing whether copy invents numbers. Never let a
  model write claims, HRs, or PMIDs.
---

# STRATA deck AI polish

The craft engine (`director_api/deck_craft.py`) already interprets the working
file into a visual argument. An LLM is optional seasoning, not the author.

## When it runs

`director_api/deck_ai.polish_story` fires only when **both** are true:

- `STRATA_DECK_AI` is `1`, `on`, or `true`
- `OPENAI_API_KEY` is set (`OPENAI_BASE_URL` and `STRATA_DECK_MODEL` optional)

Otherwise it returns the interpreted story unchanged. Tests stay deterministic.

## What the model may do

- Shorten `headline` and `tension` (under 12 words / two short sentences)
- Keep the doctrine name and enemy as given

## What the model must not do

- Invent numbers, trial names, HRs, NNTs, or PMIDs
- Add a paper that is not on the register
- Rewrite the story arc or add slides
- Paste working-file phases onto slides

If the JSON parse fails or the request times out, keep the pre-LLM story.

## After changing polish behaviour

Run `python -m pytest -q tests/test_deck_craft.py`. Assert that with the env
flag off, headlines equal `interpret_plan` output.
