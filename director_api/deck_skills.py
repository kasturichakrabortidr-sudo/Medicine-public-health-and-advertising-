"""Craft skills the generator actually runs — not comments on the side.

Four engines in director_api/deck_engines.py direct every pack.
"""

from __future__ import annotations

from .deck_engines import ENGINE_IDS, ENGINES

SKILL_IDS = ENGINE_IDS
SKILLS = {e["id"]: e for e in ENGINES}

# phase → the question the room is about to ask, and the visual that answers it.
BEATS = (
    {"id": "title", "phase": "01", "question": "Why are we in the room?", "visual": "board", "rail": "Open"},
    {"id": "need", "phase": "01", "question": "What is the real job?", "visual": "stat", "rail": "Job"},
    {"id": "tension", "phase": "05", "question": "What do they do versus what must change?", "visual": "stat", "rail": "Habit"},
    {"id": "belief", "phase": "04", "question": "Where does belief fight the papers?", "visual": "board", "rail": "Belief"},
    {"id": "pico", "phase": "02", "question": "How will we judge the science?", "visual": "board", "rail": "PICO"},
    {"id": "science-meaning", "phase": "03", "question": "What did the lead paper show in a clinic of 100?", "visual": "people", "optional": True, "rail": "Prize"},
    {"id": "forest", "phase": "03", "question": "Do the numbered papers agree?", "visual": "forest", "optional": True, "rail": "Forest"},
    {"id": "science-compare", "phase": "03", "question": "What does the next paper add?", "visual": "compare", "optional": True, "rail": "Second"},
    {"id": "pack", "phase": "03", "question": "Why is one paper not a case?", "visual": "board", "rail": "Pack"},
    {"id": "stand", "phase": "06", "question": "Where may we stand, and where are we silent?", "visual": "board", "rail": "Stand"},
    {"id": "house", "phase": "07", "question": "What will we say?", "visual": "board", "rail": "Lines"},
    {"id": "objections", "phase": "07", "question": "What will they say back?", "visual": "board", "rail": "Pushback"},
    {"id": "sequence", "phase": "08", "question": "How does contact feel over time?", "visual": "flow", "rail": "Order"},
    {"id": "who", "phase": "09", "question": "Who do we activate first?", "visual": "board", "rail": "Who"},
    {"id": "science-execute", "phase": "05", "question": "How does a finding become a move?", "visual": "spine", "optional": True, "rail": "Spine"},
    {"id": "interventions", "phase": "08", "question": "What do we actually do?", "visual": "board", "rail": "Moves"},
    {"id": "measure", "phase": "10", "question": "How will we know?", "visual": "board", "rail": "Score"},
    {"id": "close", "phase": "11", "question": "What do we need signed in 30 days?", "visual": "flow", "rail": "Ask"},
    {"id": "references", "phase": "03", "question": "Where are the PMIDs?", "visual": "table", "rail": "Refs"},
)


def catalog() -> dict:
    return {
        "skills": [SKILLS[i] for i in SKILL_IDS],
        "engines": list(ENGINES),
        "beats": [
            {
                "id": b["id"],
                "phase": b["phase"],
                "question": b["question"],
                "visual": b["visual"],
                "rail": b.get("rail") or b["id"],
            }
            for b in BEATS
        ],
        "rule": "Four engines direct the pack. Story writes brief-specific titles. Visuals use versus and split.",
    }
