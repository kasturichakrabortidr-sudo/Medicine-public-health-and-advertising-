"""Four engines direct every pack: Story, Visuals, Copy, Critic.

They always run. Optional LLMs (OpenAI, Anthropic, Gemini) may season
headlines when STRATA_DECK_AI is on and keys exist. Engines never invent
numbers, trials, HRs, or PMIDs.
"""

from __future__ import annotations

import re
from typing import Any

from .deck_ai import ensemble_titles
from .deck_visuals import line, sentence

ENGINES = (
    {
        "id": "story",
        "name": "Story",
        "rule": "The deck is one argument in four acts. Every title is a conclusion.",
    },
    {
        "id": "visuals",
        "name": "Visuals",
        "rule": "The picture carries the room. Contrast, not a pasted phase table.",
    },
    {
        "id": "copy",
        "name": "Copy",
        "rule": "One complete line. Never an ellipsis. Never a glued fragment.",
    },
    {
        "id": "critic",
        "name": "Critic",
        "rule": "Kill empty shout, duplicate labels, and chrome that eats the 16:9.",
    },
)

ENGINE_IDS = tuple(e["id"] for e in ENGINES)

EMPTY_SHOUT = re.compile(r"^supportive(\s*\[\d+[a-z]?\])?\.?$", re.I)
SILENT_CELL = re.compile(r"^silent", re.I)


def run_room(slides: list[dict], story: dict) -> tuple[list[dict], list[dict]]:
    """Story → visuals → copy → critic. Optional ensemble last."""
    report = [dict(e) for e in ENGINES]
    slides = _story(slides, story)
    slides = _visuals(slides, story)
    slides = _copy(slides, story)
    slides = _critic(slides, story)
    slides = ensemble_titles(slides, story)
    for slide in slides:
        slide["engines"] = list(ENGINE_IDS)
    return slides, report


def _story(slides: list[dict], story: dict) -> list[dict]:
    need_stat = story.get("need_stat") or "Need"
    brand = story.get("brand") or "Brand"
    titles = {
        "title": story.get("headline") or brand,
        "need": f"{need_stat} is the job.",
        "tension": "They wait. The papers start now.",
        "belief": "They agree in principle. They still wait.",
        "pico": "If it is not in this frame, it is not a claim.",
        "science-meaning": "Read the dots, not the hazard ratio.",
        "forest": "Agreement is the case, not one HR.",
        "science-compare": "This paper is not a reprint of the first.",
        "pack": "One paper is not enough to convince.",
        "stand": "Shout where the columns agree.",
        "house": "Three lines. Each one numbered.",
        "objections": "Answer the objection. Do not dodge it.",
        "sequence": "A doctor should feel an order.",
        "who": "A few rooms. The rest inherit.",
        "science-execute": "The paper names the move.",
        "interventions": "Three moves. The rest inherit.",
        "measure": "If the parent metric is flat, kill the rest.",
        "close": "Sign the bet. Number the claims.",
    }
    acts = {
        "title": "I · Open",
        "need": "I · Open",
        "tension": "I · Open",
        "belief": "I · Open",
        "pico": "II · Proof",
        "science-meaning": "II · Proof",
        "forest": "II · Proof",
        "science-compare": "II · Proof",
        "pack": "II · Proof",
        "stand": "III · Stand",
        "house": "III · Stand",
        "objections": "III · Stand",
        "sequence": "IV · Move",
        "who": "IV · Move",
        "science-execute": "IV · Move",
        "interventions": "IV · Move",
        "measure": "IV · Move",
        "close": "IV · Move",
        "references": "Sources",
    }
    for slide in slides:
        sid = slide.get("id")
        if sid in titles:
            slide["title"] = titles[sid]
        if sid == "title":
            n = story.get("n_papers") or 0
            slide["kicker"] = f"{brand}  ·  {n} numbered papers"
            slide["subtitle"] = brand
            slide["narrative"] = story.get("why") or story.get("bet") or ""
        act = acts.get(sid)
        if act:
            kicker = slide.get("kicker") or ""
            if "Phase" in kicker or sid == "title":
                rest = kicker.split("·", 1)[-1].strip() if "·" in kicker and sid != "title" else kicker
                if sid == "title":
                    slide["kicker"] = f"{act}  ·  {kicker}"
                else:
                    slide["kicker"] = f"{act}  ·  {rest}"
            slide["act"] = act
    return slides


def _visuals(slides: list[dict], story: dict) -> list[dict]:
    for slide in slides:
        sid = slide.get("id")
        if sid == "need":
            slide["narrative"] = ""
            slide["stat"] = {
                "items": [
                    {"kicker": "The brief asked", "value": story.get("asked_stat") or "Goal", "label": story.get("asked") or ""},
                    {"kicker": "The file restates", "value": story.get("need_stat") or "Need", "label": story.get("need") or ""},
                ]
            }
        elif sid == "tension":
            slide["narrative"] = ""
            slide["stat"] = {
                "items": [
                    {"kicker": "What they do", "value": "Wait", "label": story.get("current") or ""},
                    {"kicker": "What must change", "value": "Start", "label": story.get("required") or ""},
                ]
            }
        elif sid == "stand":
            slide["board"] = {"cards": _stand_cards(story)}
            slide["narrative"] = "Silence is a boundary, not a slogan to fill."
        elif sid == "pack":
            cards = (slide.get("board") or {}).get("cards") or []
            for card in cards:
                if (card.get("kicker") or "").lower() == (card.get("title") or "").lower():
                    card["kicker"] = "This paper's job"
        elif sid == "house":
            cards = (slide.get("board") or {}).get("cards") or []
            for i, card in enumerate(cards, 1):
                card["kicker"] = f"Line {i}"
        elif sid == "who":
            slide["board"] = {"cards": _who_cards(story)}
        elif sid == "belief":
            cards = (slide.get("board") or {}).get("cards") or []
            labels = ("They still wait", "They still fear", "They still stall")
            for i, card in enumerate(cards):
                card["kicker"] = labels[i] if i < len(labels) else "They still do this"
        elif sid == "measure":
            cards = (slide.get("board") or {}).get("cards") or []
            labels = ("Parent", "Lead", "Kill")
            for i, card in enumerate(cards):
                if i < 3:
                    card["kicker"] = labels[i]
    return slides


def _stand_cards(story: dict) -> list[dict]:
    shout, silent = [], []
    for row in story.get("fourway") or []:
        title = line(row[0]) if row else "Territory"
        cell = row[1] if len(row) > 1 else ""
        blob = " ".join(str(c) for c in row[1:])
        if SILENT_CELL.search(str(cell)) or ("silent" in blob.lower() and "supportive" not in blob.lower()):
            silent.append({
                "kicker": "Stay silent",
                "title": title or "Silent ground",
                "body": "No numbered paper owns this. We do not shout it.",
            })
        else:
            shout.append({
                "kicker": "We may shout",
                "title": title or "Numbered ground",
                "body": _stand_body(cell, story, title),
                "ref": _marks(cell),
            })
    cards = shout[:2] + silent[:1]
    if not cards:
        cards = [{
            "kicker": "Stand",
            "title": "Numbered ground only",
            "body": story.get("position") or "We stand only where the papers agree.",
        }]
    return cards[:3]


def _stand_body(cell, story: dict, title: str = "") -> str:
    text = str(cell or "").strip()
    low = title.lower()
    jobs = story.get("jobs") or []
    pick = None
    if "outcome" in low or "soc" in low:
        pick = next((j for j in jobs if j.get("directs") == "outcome-permission"), None)
    elif "first" in low or "hospital" in low or "eligible" in low:
        pick = next((j for j in jobs if j.get("directs") == "first-eligible-start"), None)
    if pick and (pick.get("claim_permitted") or pick.get("finding")):
        return sentence(pick.get("claim_permitted") or pick.get("finding"), 1)
    if EMPTY_SHOUT.match(text) or text.lower().startswith("supportive"):
        allow = story.get("papers_allow") or ""
        if allow and "no numbered finding" not in allow.lower():
            return allow
        return "The numbered pack supports this territory."
    return sentence(text, 2)


def _who_cards(story: dict) -> list[dict]:
    order = ("First", "Then", "Also")
    cards = []
    for i, row in enumerate(story.get("who") or []):
        title = _audience(row[0] if row else "Audience")
        job = line(row[1]) if len(row) > 1 else ""
        why = line(row[3]) if len(row) > 3 else ""
        if job and why and why.lower() not in job.lower():
            body = sentence(f"{job}. {why}")
        else:
            body = sentence(job or why or "This group inherits last.")
        cards.append({
            "kicker": order[i] if i < 3 else "Also",
            "title": title,
            "body": body,
        })
        if len(cards) >= 3:
            break
    return cards or [{
        "kicker": "First",
        "title": "Priority specialists",
        "body": "Everyone else inherits. We do not fund a national theatre.",
    }]


def _audience(text) -> str:
    raw = line(text)
    if "(" in raw and len(raw.split()) > 5:
        raw = raw.split("(", 1)[0].strip()
    return raw or "Audience"


def _copy(slides: list[dict], story: dict) -> list[dict]:
    for slide in slides:
        title = line(slide.get("title") or "").replace("…", "").replace("...", "")
        slide["title"] = title
        nar = slide.get("narrative") or ""
        labels = [i.get("label") for i in (slide.get("stat") or {}).get("items") or []]
        if nar and (any(_same_line(nar, lab or "") for lab in labels) or _same_line(nar, title)):
            slide["narrative"] = ""
        slide["narrative"] = (slide.get("narrative") or "").replace("…", "").replace("...", "")
        for card in (slide.get("board") or {}).get("cards") or []:
            card["title"] = line(card.get("title") or "")
            card["body"] = _clean_body(card.get("body") or "")
            if EMPTY_SHOUT.match(card.get("body") or ""):
                card["body"] = story.get("papers_allow") or "The numbered pack supports this territory."
        for step in (slide.get("flow") or {}).get("steps") or []:
            step["title"] = line(step.get("title") or "")
            step["body"] = _clean_body(step.get("body") or "")
    return slides


def _critic(slides: list[dict], story: dict) -> list[dict]:
    seen_titles = set()
    for slide in slides:
        for card in (slide.get("board") or {}).get("cards") or []:
            body = (card.get("body") or "").strip()
            if SILENT_CELL.match(body) or body.lower() in {"silent.", "silent"}:
                card["body"] = "No numbered paper owns this. We do not shout it."
            if (card.get("kicker") or "").lower() == (card.get("title") or "").lower() and card.get("body"):
                card["kicker"] = "Point"
            key = (slide.get("id"), card.get("title"))
            if key in seen_titles and card.get("body"):
                card["title"] = line(card.get("body")).split(".")[0][:48] or card["title"]
            seen_titles.add(key)
        # Stat slides: the visual is the copy.
        if slide.get("layout") == "stat" and slide.get("narrative"):
            labels = " ".join(i.get("label") or "" for i in (slide.get("stat") or {}).get("items") or [])
            if _same_line(slide["narrative"], labels) or slide["narrative"] in labels:
                slide["narrative"] = ""
    return slides


def _clean_body(text: str) -> str:
    text = " ".join(str(text or "").split()).replace("…", "").replace("...", "")
    return sentence(text, 2) if text else ""


def _same_line(a: str, b: str) -> bool:
    def norm(s: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", (s or "").lower())
    na, nb = norm(a), norm(b)
    return bool(na) and bool(nb) and (na == nb or na in nb or nb in na)


def _marks(text) -> str:
    found = re.findall(r"\[\d+[a-z]?\]", str(text or ""))
    return " ".join(found)
