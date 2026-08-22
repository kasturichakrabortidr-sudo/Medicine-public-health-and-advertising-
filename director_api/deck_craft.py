"""STRATA deck-craft skill — interpret the working file, do not paste it.

The working file is the plan. The deck is a visual argument for a room.
Each slide answers one question with one picture. Tables of the plan,
duplicate slides, and stacked chart+table+bullets are out of craft.
"""

from __future__ import annotations

from typing import Any

from .cite import mark
from .deck_ai import polish_story
from .deck_visuals import (
    clip,
    compare_rows,
    forest_rows,
    people_rows,
    phase,
    reference_slides,
    spine_rows,
)
from .extract import ExtractedBrief
from .molecule import science_name
from .paper_read import paper_jobs

# One question per slide. The visual, not the paragraph, carries the room.
STORY_ARC = (
    "open",
    "tension",
    "prize",
    "pack",
    "forest",
    "compare",
    "pillars",
    "execute",
    "moves",
    "ask",
    "references",
)


def interpret_plan(
    brief: ExtractedBrief,
    doctrine: dict,
    ledger: dict,
    work: dict,
    interventions: list[dict],
) -> dict[str, Any]:
    """Read the working file and decide what the room must see — not what the file contains."""
    records = ledger.get("records") or []
    lead = ledger.get("lead") or {}
    p01 = phase(work, "01")
    p05 = phase(work, "05")
    p07 = phase(work, "07")
    p11 = phase(work, "11")
    jobs = paper_jobs(records, brief)
    insight = (brief.hcp_insights or [""])[0] or (p01.get("restatedNeed") or "")
    molecule = science_name(brief)
    primary = (lead.get("citations") or jobs or records or [{}])[0]
    prize = primary.get("claim_permitted") or primary.get("finding") or ""
    story = {
        "headline": clip(doctrine.get("bet") or "Change the decision, not the reprint.", 72),
        "enemy": clip(doctrine.get("enemy") or insight or "Hesitation at the pen", 72),
        "tension": clip(
            p01.get("restatedNeed")
            or (f"They still do this: {insight}" if insight else "The brief names a growth goal, not a behaviour."),
            160,
        ),
        "they_do": clip(insight or p05.get("current") or "The habit is not named.", 90),
        "papers_allow": clip(prize or "No numbered finding yet.", 90),
        "molecule": molecule,
        "brand": brief.brand or "This brand",
        "indication": brief.indication or brief.therapy_area or "the indicated population",
        "n_papers": len(records),
        "theme": clip(p07.get("theme") or doctrine.get("name") or "", 80),
        "ask": [clip(a, 90) for a in (p11.get("ask") or [])[:3]]
        or [
            "Sign the bet.",
            "Number every load-bearing line.",
            "Park gaps as research, not copy.",
        ],
        "moves": interventions[:3],
        "jobs": jobs[:4],
        "house": _house_cards(p07, jobs),
        "skill": "strata-deck",
    }
    return polish_story(story, brief, doctrine)


def build_deck(
    brief: ExtractedBrief,
    doctrine: dict,
    ledger: dict,
    work: dict,
    interventions: list[dict],
) -> list[dict]:
    """Visual-first slide list. Interprets the plan; never dumps the eleven phases."""
    story = interpret_plan(brief, doctrine, ledger, work, interventions)
    records = ledger.get("records") or []
    lead = ledger.get("lead") or {}
    people = people_rows(records)[:1]
    compare = compare_rows(records)[:1]
    forest = forest_rows(records)
    spine = spine_rows(records, interventions)
    slides: list[dict] = [_title_slide(story, doctrine, brief, records)]
    slides.append(_tension_slide(story, lead))
    if people:
        slides.append(_prize_slide(people[0], story))
    if forest:
        slides.append(_forest_slide(forest, records))
    if compare:
        slides.append(_compare_slide(compare[0]))
    slides.append(_pack_slide(story, records, lead))
    slides.append(_pillars_slide(story, doctrine))
    if spine:
        slides.append(_execute_slide(spine))
    slides.append(_moves_slide(story))
    slides.append(_ask_slide(story, doctrine, brief))
    slides.extend(reference_slides(ledger.get("references") or work.get("references") or []))
    return [_one_visual(s) for s in slides]


def _title_slide(story: dict, doctrine: dict, brief: ExtractedBrief, records: list[dict]) -> dict:
    return {
        "id": "title",
        "section": "Open",
        "kicker": f"{brief.market or 'Confidential'}  ·  {story['n_papers']} numbered papers",
        "title": story["brand"],
        "subtitle": story["headline"],
        "narrative": clip(doctrine.get("whyNovel") or doctrine.get("thesis") or "", 180),
        "layout": "title",
        "board": {
            "cards": [
                {"kicker": "Molecule", "title": story["molecule"] or "Indication-led", "body": story["indication"]},
                {"kicker": "The bet", "title": clip(doctrine.get("name") or "Doctrine", 28), "body": story["headline"]},
                {"kicker": "The pack", "title": f"{story['n_papers']} papers", "body": "One paper is not a case."},
            ]
        },
        "refs": [r.get("ref") for r in records[:6] if r.get("ref")],
    }


def _tension_slide(story: dict, lead: dict) -> dict:
    return {
        "id": "tension",
        "section": "Tension",
        "kicker": "What the room is actually fighting",
        "title": "They wait. The papers do not.",
        "narrative": story["tension"],
        "layout": "stat",
        "stat": {
            "items": [
                {"kicker": "In the room", "value": "Wait", "label": story["they_do"]},
                {
                    "kicker": "On the register",
                    "value": str(story.get("n_papers") or 0),
                    "label": story["papers_allow"],
                },
            ]
        },
        "refs": [c.get("ref") for c in (lead.get("citations") or [])[:3] if c.get("ref")],
    }


def _prize_slide(row: dict, story: dict) -> dict:
    tag = mark({"ref": row.get("ref")}) if row.get("ref") else ""
    return {
        "id": "science-meaning",
        "section": "Science",
        "kicker": "The prize, in a clinic of 100",
        "title": "Read the dots, not the hazard ratio",
        "subtitle": f"{row.get('name')} · PMID {row.get('pmid') or '—'}",
        "narrative": clip(
            f"{row.get('claim')} {tag} Treat {row.get('nnt')} to prevent 1 event"
            + (f" over {row.get('horizon')}" if row.get("horizon") else "")
            + ".",
            180,
        ),
        "layout": "visual",
        "chart": {
            "kind": "people",
            "title": f"{row.get('name')}: {row.get('unit')}",
            "note": f"Published rates. PMID {row.get('pmid')}.",
            "unit": row.get("unit"),
            "data": [row],
        },
        "refs": [row.get("ref")] if row.get("ref") else [],
    }


def _forest_slide(forest: list[dict], records: list[dict]) -> dict:
    return {
        "id": "forest",
        "section": "Science",
        "kicker": "The pack on one axis",
        "title": "Agreement is the case, not one HR",
        "narrative": "Only numbered papers with a published interval. We do not invent a forest.",
        "layout": "visual",
        "chart": {
            "kind": "forest",
            "title": "Published hazard ratios",
            "note": "Copied from the cited papers. Superscripts are Vancouver numbers.",
            "data": forest,
        },
        "refs": [r.get("ref") for r in records if r.get("hr") is not None and r.get("ref")],
    }


def _compare_slide(row: dict) -> dict:
    return {
        "id": "science-compare",
        "section": "Science",
        "kicker": "A second paper, a different job",
        "title": clip(str(row.get("name") or "Published rates"), 72),
        "narrative": clip(row.get("claim") or "", 160),
        "layout": "visual",
        "chart": {
            "kind": "compare",
            "title": f"{row.get('name')}: {row.get('unit')}",
            "note": f"PMID {row.get('pmid')}. {row.get('horizon') or ''}".strip(),
            "unit": row.get("unit"),
            "data": [row],
        },
        "refs": [row.get("ref")] if row.get("ref") else [],
    }


def _pack_slide(story: dict, records: list[dict], lead: dict) -> dict:
    cards = []
    for rec in story["jobs"][:4]:
        cards.append({
            "kicker": rec.get("roleLabel") or rec.get("role") or "Sourced",
            "title": clip(rec.get("short") or rec.get("trial") or f"PMID {rec.get('pmid')}", 32),
            "body": clip(rec.get("claim_permitted") or rec.get("finding") or "", 110),
            "ref": mark(rec) if rec.get("ref") else "",
        })
    if not cards:
        cards = [{"kicker": "Gap", "title": "No pack yet", "body": "Do not lock a scientific lead on a blank register."}]
    return {
        "id": "pack",
        "section": "Science",
        "kicker": "The pack — each paper a job",
        "title": "One paper is not enough to convince",
        "narrative": clip((lead.get("why") or "") or f"{story['n_papers']} numbered papers carry the science.", 140),
        "layout": "board",
        "board": {"cards": cards},
        "refs": [r.get("ref") for r in records[:4] if r.get("ref")],
    }


def _pillars_slide(story: dict, doctrine: dict) -> dict:
    cards = story.get("house") or []
    return {
        "id": "house",
        "section": "Message",
        "kicker": "What we will say",
        "title": clip(story.get("theme") or "Three lines. No reprints.", 72),
        "narrative": "A pillar without a number does not ship.",
        "layout": "board",
        "board": {"cards": cards[:4] or [{"kicker": "Theme", "title": doctrine.get("name") or "Bet", "body": story["headline"]}]},
        "refs": [],
    }


def _execute_slide(rows: list[dict]) -> dict:
    return {
        "id": "science-execute",
        "section": "Action",
        "kicker": "Science becomes a move",
        "title": "The paper names the move",
        "narrative": "One cited finding, one execution. We do not invent a second campaign beside the papers.",
        "layout": "visual",
        "chart": {
            "kind": "spine",
            "title": "From the paper to the room",
            "data": rows[:2],
        },
        "refs": [r.get("ref") for r in rows if r.get("ref")],
    }


def _moves_slide(story: dict) -> dict:
    cards = []
    for i, move in enumerate(story.get("moves") or [], 1):
        cards.append({
            "kicker": f"Move {i}",
            "title": clip(move.get("name") or f"Move {i}", 28),
            "body": clip(move.get("promise") or "", 120),
            "ref": clip(move.get("evidenceAnchor") or "", 80),
        })
    return {
        "id": "interventions",
        "section": "Action",
        "kicker": "What we actually do",
        "title": "Three moves. The rest inherit.",
        "narrative": "If a move cannot name a numbered paper, it does not ship.",
        "layout": "board",
        "board": {"cards": cards[:3]},
    }


def _ask_slide(story: dict, doctrine: dict, brief: ExtractedBrief) -> dict:
    steps = []
    labels = ("Days 1–10", "Days 11–20", "Days 21–30")
    for i, line in enumerate(story.get("ask") or []):
        steps.append({"n": str(i + 1), "title": labels[i] if i < 3 else f"Step {i+1}", "body": line})
    return {
        "id": "close",
        "section": "Ask",
        "kicker": "The first 30 days",
        "title": "Sign the bet. Number the claims.",
        "narrative": clip(doctrine.get("scienceLead") or story["headline"], 160),
        "layout": "flow",
        "flow": {"steps": steps[:3]},
        "callout": {"label": brief.brand or "Brand", "text": story["headline"]},
    }


def _house_cards(p07: dict, jobs: list[dict]) -> list[dict]:
    rows = ((p07.get("house") or {}).get("rows") or [])[:4]
    cards = []
    for row in rows:
        if not isinstance(row, (list, tuple)) or not row:
            continue
        title = clip(row[0], 28)
        if title.lower() == "the pack":
            continue
        body = clip(row[1] if len(row) > 1 else "", 110)
        ref = row[2] if len(row) > 2 else ""
        cards.append({"kicker": "Pillar", "title": title, "body": body, "ref": str(ref or "")})
    if len(cards) >= 2:
        return cards[:3]
    for rec in jobs[:3]:
        cards.append({
            "kicker": rec.get("roleLabel") or "Pillar",
            "title": clip(rec.get("short") or rec.get("trial") or "Paper", 28),
            "body": clip(rec.get("claim_permitted") or "", 110),
            "ref": mark(rec) if rec.get("ref") else "",
        })
    return cards[:3]


def _one_visual(slide: dict) -> dict:
    """Craft rule: never stack a chart, a table, and a bullet list."""
    has_visual = bool(slide.get("chart") or slide.get("board") or slide.get("flow") or slide.get("stat"))
    if has_visual:
        slide.pop("table", None)
        if slide.get("layout") in {"visual", "board", "flow", "stat", "infographic"}:
            slide["bullets"] = []
    bullets = slide.get("bullets") or []
    if len(bullets) > 4:
        slide["bullets"] = bullets[:4]
    if slide.get("chart") and slide.get("table"):
        slide.pop("table")
    return slide
