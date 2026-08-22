"""STRATA deck craft — the working file, told as pictures.

Skills in director_api/deck_skills.py run here. Copy is complete sentences.
Visuals carry the room. The eleven phases all have a beat.
"""

from __future__ import annotations

import re
from typing import Any

from .cite import mark
from .deck_ai import polish_story
from .deck_skills import BEATS, SKILL_IDS
from .deck_visuals import (
    compare_rows,
    cue,
    forest_rows,
    goal_stat,
    line,
    need_line,
    people_rows,
    phase,
    reference_slides,
    rows_of,
    sentence,
    spine_rows,
)
from .extract import ExtractedBrief
from .molecule import science_name
from .paper_read import paper_jobs


def interpret_plan(
    brief: ExtractedBrief,
    doctrine: dict,
    ledger: dict,
    work: dict,
    interventions: list[dict],
) -> dict[str, Any]:
    """Read every phase. Decide what the room must see. Do not paste the file."""
    records = ledger.get("records") or []
    lead = ledger.get("lead") or {}
    p01 = phase(work, "01")
    p02 = phase(work, "02")
    p04 = phase(work, "04")
    p05 = phase(work, "05")
    p06 = phase(work, "06")
    p07 = phase(work, "07")
    p08 = phase(work, "08")
    p09 = phase(work, "09")
    p10 = phase(work, "10")
    p11 = phase(work, "11")
    jobs = paper_jobs(records, brief)
    molecule = science_name(brief)
    insights = brief.hcp_insights or []
    insight = insights[0] if insights else ""
    primary = (lead.get("citations") or jobs or records or [{}])[0]
    asked_stat, asked = goal_stat(p01.get("restatedAsk") or brief.business_goal or "The brief does not state a goal.")
    need_stat, need = need_line(insights, doctrine)
    story = {
        "headline": line(doctrine.get("name") or "Change the decision, not the reprint"),
        "bet": sentence(doctrine.get("bet") or ""),
        "enemy": sentence(doctrine.get("enemy") or insight or "Hesitation at the pen."),
        "why": sentence(doctrine.get("whyNovel") or ""),
        "asked": asked,
        "asked_stat": asked_stat,
        "need": need,
        "need_stat": need_stat,
        "current": sentence(cue(p05.get("current") or insight or "The habit is not named.")),
        "required": sentence(p05.get("required") or doctrine.get("bet") or ""),
        "they_do": sentence(cue(insight or p05.get("current") or "The habit is not named.")),
        "papers_allow": sentence(primary.get("claim_permitted") or "No numbered finding yet."),
        "molecule": molecule,
        "brand": brief.brand or "This brand",
        "indication": sentence(brief.indication or brief.therapy_area or "The indicated population."),
        "n_papers": len(records),
        "pico": rows_of(p02.get("pico")),
        "discord": rows_of(p04.get("discord")),
        "concord": rows_of(p04.get("concord")),
        "silent": rows_of(p04.get("silent")),
        "fourway": rows_of(p06.get("fourway")),
        "position": sentence(p06.get("position") or ""),
        "house": rows_of(p07.get("house")),
        "objections": rows_of(p07.get("objections")),
        "stages": rows_of(p08.get("stages")),
        "who": rows_of(p09.get("grid")),
        "kpis": rows_of(p10.get("kpis")),
        "ask": [sentence(a) for a in (p11.get("ask") or [])[:3]]
        or [
            "Sign the bet.",
            "Number every load-bearing line.",
            "Park gaps as research, not copy.",
        ],
        "moves": interventions[:3],
        "jobs": jobs[:4],
        "lead_why": sentence(lead.get("why") or ""),
        "science_lead": sentence(doctrine.get("scienceLead") or lead.get("statement") or ""),
        "skills": list(SKILL_IDS),
    }
    return polish_story(story, brief, doctrine)


def build_deck(
    brief: ExtractedBrief,
    doctrine: dict,
    ledger: dict,
    work: dict,
    interventions: list[dict],
) -> list[dict]:
    """Walk the story beats. Skip optional visuals only when the register is empty."""
    story = interpret_plan(brief, doctrine, ledger, work, interventions)
    records = ledger.get("records") or []
    lead = ledger.get("lead") or {}
    people = people_rows(records)[:1]
    compare = compare_rows(records)[:1]
    forest = forest_rows(records)
    spine = spine_rows(records, interventions)
    makers = {
        "title": lambda: _title_slide(story, doctrine, brief, records),
        "need": lambda: _need_slide(story, lead),
        "tension": lambda: _tension_slide(story, lead),
        "belief": lambda: _belief_slide(story, records),
        "pico": lambda: _pico_slide(story),
        "science-meaning": lambda: _prize_slide(people[0]) if people else None,
        "forest": lambda: _forest_slide(forest, records) if forest else None,
        "science-compare": lambda: _compare_slide(compare[0]) if compare else None,
        "pack": lambda: _pack_slide(story, records),
        "stand": lambda: _stand_slide(story),
        "house": lambda: _pillars_slide(story),
        "objections": lambda: _objections_slide(story),
        "sequence": lambda: _sequence_slide(story),
        "who": lambda: _who_slide(story),
        "science-execute": lambda: _execute_slide(spine) if spine else None,
        "interventions": lambda: _moves_slide(story),
        "measure": lambda: _measure_slide(story),
        "close": lambda: _ask_slide(story, brief),
        "references": lambda: None,
    }
    slides: list[dict] = []
    for beat in BEATS:
        if beat["id"] == "references":
            for ref in reference_slides(ledger.get("references") or work.get("references") or []):
                slides.append(_stamp(ref, beat))
            continue
        made = makers[beat["id"]]()
        if not made:
            continue
        slides.append(_stamp(_one_visual(made), beat))
    return slides


def story_map(slides: list[dict]) -> list[dict]:
    seen = []
    for s in slides:
        item = {"phase": s.get("phase") or "", "slide": s.get("id") or "", "question": s.get("question") or ""}
        if item not in seen:
            seen.append(item)
    return seen


def _stamp(slide: dict, beat: dict) -> dict:
    slide["phase"] = beat["phase"]
    slide["question"] = beat["question"]
    slide["skill"] = "story"
    return slide


def _title_slide(story: dict, doctrine: dict, brief: ExtractedBrief, records: list[dict]) -> dict:
    n = story["n_papers"]
    pack_line = "One paper is not a case." if n == 1 else f"{n} numbered papers, each with a job."
    return {
        "id": "title",
        "section": "Open",
        "kicker": f"{brief.market or 'Confidential'}  ·  {n} numbered papers",
        "title": story["brand"],
        "subtitle": story["headline"],
        "narrative": story["why"] or story["bet"],
        "layout": "title",
        "board": {
            "cards": [
                {"kicker": "Molecule", "title": story["molecule"] or "Indication-led", "body": story["indication"]},
                {"kicker": "The bet", "title": story["headline"], "body": story["bet"]},
                {"kicker": "The pack", "title": f"{n} papers" if n else "No pack yet", "body": pack_line},
            ]
        },
        "refs": [r.get("ref") for r in records[:6] if r.get("ref")],
    }


def _need_slide(story: dict, lead: dict) -> dict:
    return {
        "id": "need",
        "section": "Need",
        "kicker": "Phase 01 · the real job",
        "title": "The goal is not the job.",
        "narrative": story["need"],
        "layout": "stat",
        "stat": {
            "items": [
                {"kicker": "The brief asked", "value": story["asked_stat"], "label": story["asked"]},
                {"kicker": "The file restates", "value": story["need_stat"], "label": story["need"]},
            ]
        },
        "refs": [c.get("ref") for c in (lead.get("citations") or [])[:3] if c.get("ref")],
    }


def _tension_slide(story: dict, lead: dict) -> dict:
    return {
        "id": "tension",
        "section": "Tension",
        "kicker": "Phase 05 · the behaviour",
        "title": "Current habit versus required start.",
        "narrative": story["enemy"],
        "layout": "stat",
        "stat": {
            "items": [
                {"kicker": "What they do", "value": "Wait", "label": story["current"]},
                {"kicker": "What must change", "value": "Start", "label": story["required"]},
            ]
        },
        "refs": [c.get("ref") for c in (lead.get("citations") or [])[:3] if c.get("ref")],
    }


def _belief_slide(story: dict, records: list[dict]) -> dict:
    cards = []
    for row in story.get("discord") or []:
        cards.append({
            "kicker": "They still do this",
            "title": cue(row[0]) or "Named delay",
            "body": sentence(row[1] if len(row) > 1 else ""),
            "ref": _cite_ref(row[2] if len(row) > 2 else ""),
        })
        if len(cards) >= 3:
            break
    if not cards:
        for rec in story.get("jobs") or []:
            cards.append({
                "kicker": rec.get("roleLabel") or "Sourced",
                "title": line(rec.get("short") or rec.get("trial") or "Paper"),
                "body": sentence(rec.get("claim_permitted") or ""),
                "ref": mark(rec) if rec.get("ref") else "",
            })
            if len(cards) >= 3:
                break
    if not cards:
        cards = [{"kicker": "Gap", "title": "No discord mapped yet", "body": "Do not invent a belief the brief did not name."}]
    return {
        "id": "belief",
        "section": "Belief",
        "kicker": "Phase 04 · belief versus papers",
        "title": "Agreement is not the campaign.",
        "narrative": "Disagreement is where we spend. Silence is research, not copy.",
        "layout": "board",
        "board": {"cards": cards[:3]},
        "refs": [r.get("ref") for r in records[:4] if r.get("ref")],
    }


def _pico_slide(story: dict) -> dict:
    cards = []
    for row in story.get("pico") or []:
        name = line(row[0]) or "PICO"
        definition = row[1] if len(row) > 1 else ""
        rule = row[2] if len(row) > 2 else ""
        if name.lower().startswith("outcome"):
            title = "Published endpoints only"
            body = sentence(definition)
        elif len(str(definition).split()) <= 12:
            title = line(definition) or name
            body = sentence(rule or definition)
        else:
            title = name
            body = sentence(definition)
        cards.append({
            "kicker": name,
            "title": title,
            "body": body,
        })
    if not cards:
        cards = [{"kicker": "PICO", "title": "Contract pending", "body": "If a line is not in this frame, it is not yet a claim."}]
    return {
        "id": "pico",
        "section": "Contract",
        "kicker": "Phase 02 · how we judge the science",
        "title": "If it is not in this frame, it is not a claim.",
        "narrative": "Population, intervention, comparator, outcomes, setting. That is the contract.",
        "layout": "board",
        "board": {"cards": cards[:5]},
    }


def _prize_slide(row: dict) -> dict:
    claim = sentence(row.get("claim") or "")
    horizon = f" over {row.get('horizon')}" if row.get("horizon") else ""
    prize = f"Treat {row.get('nnt')} to prevent one event{horizon}."
    return {
        "id": "science-meaning",
        "section": "Science",
        "kicker": "Phase 03 · the prize, in a clinic of 100",
        "title": "Read the dots, not the hazard ratio.",
        "subtitle": f"{row.get('name')} · PMID {row.get('pmid') or '—'}",
        "narrative": " ".join(p for p in (claim, prize) if p),
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
        "kicker": "Phase 03 · the pack on one axis",
        "title": "Agreement is the case, not one HR.",
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
        "kicker": "Phase 03 · a second paper, a different job",
        "title": "This paper is not a reprint of the first.",
        "subtitle": line(str(row.get("name") or "Published rates")),
        "narrative": sentence(row.get("claim") or ""),
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


def _pack_slide(story: dict, records: list[dict]) -> dict:
    cards = []
    for rec in story["jobs"][:4]:
        cards.append({
            "kicker": rec.get("roleLabel") or rec.get("role") or "Sourced",
            "title": line(rec.get("short") or rec.get("trial") or f"PMID {rec.get('pmid')}"),
            "body": sentence(rec.get("claim_permitted") or rec.get("finding") or ""),
            "ref": mark(rec) if rec.get("ref") else "",
        })
    if not cards:
        cards = [{"kicker": "Gap", "title": "No pack yet", "body": "Do not lock a scientific lead on a blank register."}]
    return {
        "id": "pack",
        "section": "Science",
        "kicker": "Phase 03 · each paper a job",
        "title": "One paper is not enough to convince.",
        "narrative": story["lead_why"] or "Load-bearing lines quote the pack, not a single PMID.",
        "layout": "board",
        "board": {"cards": cards},
        "refs": [r.get("ref") for r in records[:4] if r.get("ref")],
    }


def _stand_slide(story: dict) -> dict:
    shout, silent = [], []
    for row in story.get("fourway") or []:
        title = line(row[0]) if row else ""
        rest = " ".join(str(c) for c in row[1:])
        low = rest.lower()
        item = {"kicker": "Territory", "title": title or "Territory", "body": sentence(row[1] if len(row) > 1 else rest)}
        if "silent" in low and "supportive" not in low:
            item["kicker"] = "Silent"
            silent.append(item)
        else:
            item["kicker"] = "We may stand"
            shout.append(item)
    cards = (shout[:2] + silent[:2]) or [
        {"kicker": "Stand", "title": "Numbered ground only", "body": story["position"] or "We stand only where the papers agree."}
    ]
    return {
        "id": "stand",
        "section": "Ground",
        "kicker": "Phase 06 · shout versus silence",
        "title": "We shout only where the columns agree.",
        "narrative": story["position"] or "Silence is a boundary, not a gap to fill with a slogan.",
        "layout": "board",
        "board": {"cards": cards[:4]},
    }


def _pillars_slide(story: dict) -> dict:
    cards = []
    for row in story.get("house") or []:
        title = line(row[0]) if row else ""
        if not title:
            continue
        cards.append({
            "kicker": "We will say",
            "title": title,
            "body": sentence(row[1] if len(row) > 1 else ""),
            "ref": _cite_ref(row[2] if len(row) > 2 else ""),
        })
    if not cards:
        cards = [{"kicker": "Theme", "title": story["headline"], "body": story["bet"]}]
    return {
        "id": "house",
        "section": "Message",
        "kicker": "Phase 07 · what we will say",
        "title": "Three lines. Each one numbered.",
        "narrative": "A pillar without a number does not ship.",
        "layout": "board",
        "board": {"cards": cards[:4]},
        "refs": [],
    }


def _objections_slide(story: dict) -> dict:
    cards = []
    for row in story.get("objections") or []:
        cards.append({
            "kicker": "They will say",
            "title": line(row[0]) or "Objection",
            "body": sentence(row[1] if len(row) > 1 else "", 2),
            "ref": _cite_ref(row[2] if len(row) > 2 else ""),
        })
        if len(cards) >= 3:
            break
    if not cards:
        cards = [{"kicker": "Objection", "title": "None mapped yet", "body": "Do not write an answer the papers cannot carry."}]
    return {
        "id": "objections",
        "section": "Message",
        "kicker": "Phase 07 · what they say back",
        "title": "Answer the objection. Do not dodge it.",
        "narrative": "What we will not say sits in the working file. It does not become a slogan.",
        "layout": "board",
        "board": {"cards": cards[:3]},
    }


def _sequence_slide(story: dict) -> dict:
    steps = []
    for i, row in enumerate(story.get("stages") or [], 1):
        steps.append({
            "n": str(i),
            "title": line(row[0]) or f"Stage {i}",
            "body": sentence(row[1] if len(row) > 1 else ""),
        })
    if not steps:
        steps = [
            {"n": "1", "title": "Before first call", "body": "Bag each numbered paper as a job."},
            {"n": "2", "title": "In the room", "body": "Use the paper that matches the objection they actually heard."},
            {"n": "3", "title": "After the burst", "body": "Recall of each job, not of a mash-up number."},
        ]
    return {
        "id": "sequence",
        "section": "Contact",
        "kicker": "Phase 08 · a sequence, not a spray",
        "title": "A doctor should feel an order.",
        "narrative": "If a contact cannot name a numbered paper, it does not go on the plan.",
        "layout": "flow",
        "flow": {"steps": steps[:4]},
    }


def _who_slide(story: dict) -> dict:
    cards = []
    for row in story.get("who") or []:
        cards.append({
            "kicker": "First",
            "title": line(row[0]) or "Audience",
            "body": sentence((row[1] if len(row) > 1 else "") + (f" {row[3]}" if len(row) > 3 and row[3] else "")),
        })
        if len(cards) >= 3:
            break
    if not cards:
        cards = [{"kicker": "Who", "title": "Priority specialists", "body": "Everyone else inherits. We do not fund a national theatre."}]
    return {
        "id": "who",
        "section": "Audience",
        "kicker": "Phase 09 · who we activate first",
        "title": "A few rooms. The rest inherit.",
        "narrative": "We collapsed specialty, city, and cost to the groups this brief can actually fund.",
        "layout": "board",
        "board": {"cards": cards[:3]},
    }


def _execute_slide(rows: list[dict]) -> dict:
    return {
        "id": "science-execute",
        "section": "Action",
        "kicker": "Phase 05 · science becomes a move",
        "title": "The paper names the move.",
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
            "title": line(move.get("name") or f"Move {i}"),
            "body": sentence(move.get("promise") or ""),
            "ref": _cite_ref(move.get("evidenceAnchor") or ""),
        })
    return {
        "id": "interventions",
        "section": "Action",
        "kicker": "Phase 08 · what we actually do",
        "title": "Three moves. The rest inherit.",
        "narrative": "If a move cannot name a numbered paper, it does not ship.",
        "layout": "board",
        "board": {"cards": cards[:3]},
    }


def _measure_slide(story: dict) -> dict:
    cards = []
    labels = ("Parent", "Lead", "Kill")
    for i, row in enumerate(story.get("kpis") or []):
        kind = line(row[0]) if row else labels[min(i, 2)]
        cards.append({
            "kicker": kind or labels[min(i, 2)],
            "title": line(row[1]) if len(row) > 1 else "Metric",
            "body": sentence((row[4] if len(row) > 4 else "") or (row[2] if len(row) > 2 else "")),
        })
        if len(cards) >= 3:
            break
    if not cards:
        cards = [{"kicker": "Parent", "title": "The brief's own goal", "body": "If this does not move, the rest is decoration."}]
    return {
        "id": "measure",
        "section": "Proof",
        "kicker": "Phase 10 · how we will know",
        "title": "The brief's goal is the parent metric.",
        "narrative": "Lead indicators are recall of each paper's job, not a mash-up number. Rates stay sketches until the audit exists.",
        "layout": "board",
        "board": {"cards": cards[:3]},
    }


def _ask_slide(story: dict, brief: ExtractedBrief) -> dict:
    labels = ("Days 1 to 10", "Days 11 to 20", "Days 21 to 30")
    steps = []
    for i, body in enumerate(story.get("ask") or []):
        steps.append({"n": str(i + 1), "title": labels[i] if i < 3 else f"Step {i + 1}", "body": body})
    return {
        "id": "close",
        "section": "Ask",
        "kicker": "Phase 11 · the page we take to sign-off",
        "title": "Sign the bet. Number the claims.",
        "narrative": story["science_lead"] or story["bet"],
        "layout": "flow",
        "flow": {"steps": steps[:3]},
        "callout": {"label": brief.brand or "Brand", "text": story["headline"]},
    }


def _cite_ref(value) -> str:
    text = str(value or "").strip()
    marks = re.findall(r"\[\d+[a-z]?\]", text)
    pmid = re.search(r"PMID\s+\d+", text, re.I)
    parts = list(marks)
    if pmid:
        parts.append(pmid.group(0))
    return " · ".join(parts)


def _one_visual(slide: dict) -> dict:
    has_visual = bool(slide.get("chart") or slide.get("board") or slide.get("flow") or slide.get("stat"))
    if has_visual:
        slide.pop("table", None)
        if slide.get("layout") in {"visual", "board", "flow", "stat", "infographic"}:
            slide["bullets"] = []
    if slide.get("chart") and slide.get("table"):
        slide.pop("table")
    return slide
