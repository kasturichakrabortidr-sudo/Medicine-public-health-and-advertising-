"""Craft skills the generator actually runs — not comments on the side.

Each skill is a contract. `build_deck` walks the story beats, `sentence`
refuses ellipses, and the Deck tab shows which skill owns the current slide.
"""

from __future__ import annotations

# Ids the web app and /api/deck-skills expose.
SKILL_IDS = ("story", "visuals", "copy", "layout")

SKILLS = {
    "story": {
        "id": "story",
        "name": "Story",
        "rule": "Every working-file phase has a beat. The deck is the argument, in order.",
    },
    "visuals": {
        "id": "visuals",
        "name": "Visuals",
        "rule": "The picture carries the room. A slide without a visual is a failed beat.",
    },
    "copy": {
        "id": "copy",
        "name": "Copy",
        "rule": "Complete sentences only. Never an ellipsis. Never a cut clause.",
    },
    "layout": {
        "id": "layout",
        "name": "Layout",
        "rule": "One visual owns the 16:9. Refs sit in the flow. Nothing overlaps.",
    },
}

# phase → the question the room is about to ask, and the visual that answers it.
BEATS = (
    {"id": "title", "phase": "01", "question": "Why are we in the room?", "visual": "board"},
    {"id": "need", "phase": "01", "question": "What is the real job?", "visual": "stat"},
    {"id": "tension", "phase": "05", "question": "What do they do versus what must change?", "visual": "stat"},
    {"id": "belief", "phase": "04", "question": "Where does belief fight the papers?", "visual": "board"},
    {"id": "pico", "phase": "02", "question": "How will we judge the science?", "visual": "board"},
    {"id": "science-meaning", "phase": "03", "question": "What did the lead paper show in a clinic of 100?", "visual": "people", "optional": True},
    {"id": "forest", "phase": "03", "question": "Do the numbered papers agree?", "visual": "forest", "optional": True},
    {"id": "science-compare", "phase": "03", "question": "What does the next paper add?", "visual": "compare", "optional": True},
    {"id": "pack", "phase": "03", "question": "Why is one paper not a case?", "visual": "board"},
    {"id": "stand", "phase": "06", "question": "Where may we stand, and where are we silent?", "visual": "board"},
    {"id": "house", "phase": "07", "question": "What will we say?", "visual": "board"},
    {"id": "objections", "phase": "07", "question": "What will they say back?", "visual": "board"},
    {"id": "sequence", "phase": "08", "question": "How does contact feel over time?", "visual": "flow"},
    {"id": "who", "phase": "09", "question": "Who do we activate first?", "visual": "board"},
    {"id": "science-execute", "phase": "05", "question": "How does a finding become a move?", "visual": "spine", "optional": True},
    {"id": "interventions", "phase": "08", "question": "What do we actually do?", "visual": "board"},
    {"id": "measure", "phase": "10", "question": "How will we know?", "visual": "board"},
    {"id": "close", "phase": "11", "question": "What do we need signed in 30 days?", "visual": "flow"},
    {"id": "references", "phase": "03", "question": "Where are the PMIDs?", "visual": "table"},
)


def catalog() -> dict:
    return {
        "skills": [SKILLS[i] for i in SKILL_IDS],
        "beats": [
            {
                "id": b["id"],
                "phase": b["phase"],
                "question": b["question"],
                "visual": b["visual"],
            }
            for b in BEATS
        ],
        "rule": "Interpret the working file. Do not paste it. Do not clip it.",
    }
