"""Four engines direct every pack: Story, Visuals, Copy, Critic.

They always run and leave a kill report. Optional LLMs (OpenAI, Anthropic,
Gemini) may season copy when STRATA_DECK_AI is on and keys exist. Engines
never invent numbers, trials, HRs, or PMIDs.
"""

from __future__ import annotations

import re
from typing import Any

from .deck_ai import ensemble_room
from .deck_visuals import clip_title, cue, is_process, line, listed, sentence

ENGINES = (
    {
        "id": "story",
        "name": "Story",
        "rule": "The deck is one argument in four acts. Every title is a brief-specific conclusion.",
    },
    {
        "id": "visuals",
        "name": "Visuals",
        "rule": "The picture carries the room. Versus and split, not a pasted phase table.",
    },
    {
        "id": "copy",
        "name": "Copy",
        "rule": "One complete line. Never an ellipsis. Never a glued fragment.",
    },
    {
        "id": "critic",
        "name": "Critic",
        "rule": "Kill empty shout, duplicate labels, process notes, and chrome that eats the 16:9.",
    },
)

ENGINE_IDS = tuple(e["id"] for e in ENGINES)

EMPTY_SHOUT = re.compile(r"^supportive(\s*\[\d+[a-z]?\])?\.?$", re.I)
SILENT_CELL = re.compile(r"^silent", re.I)
SCIENCE_IDS = {
    "pico",
    "science-meaning",
    "forest",
    "science-compare",
    "pack",
    "science-execute",
    "stand",
}

JOB_KICKER = {
    "outcome-permission": "Outcome proof",
    "first-eligible-start": "Start feasibility",
    "guideline-cover": "Guideline permission",
    "segment-confidence": "Age is not a veto",
    "local-context": "Local context",
}
JOB_KICKER_ALT = {
    "first-eligible-start": "Timing flexibility",
    "guideline-cover": "Guideline foundation",
    "outcome-permission": "Replicated outcome",
}


def run_room(slides: list[dict], story: dict) -> tuple[list[dict], list[dict]]:
    """Story → visuals → copy → critic. Optional ensemble last."""
    report: list[dict] = []
    slides, rows = _story(slides, story)
    report.extend(rows)
    slides, rows = _visuals(slides, story)
    report.extend(rows)
    slides, rows = _copy(slides, story)
    report.extend(rows)
    slides, rows = _critic(slides, story)
    report.extend(rows)
    slides = ensemble_room(slides, story)
    for slide in slides:
        slide["engines"] = list(ENGINE_IDS)
    return slides, report


def _story(slides: list[dict], story: dict) -> tuple[list[dict], list[dict]]:
    titles = _story_titles(story)
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
    report = []
    brand = story.get("brand") or "Brand"
    for slide in slides:
        sid = slide.get("id")
        before = slide.get("title") or ""
        if sid in titles:
            slide["title"] = titles[sid]
            if before != titles[sid]:
                report.append({"engine": "story", "slide": sid, "action": "titled", "after": titles[sid]})
        if sid == "title":
            n = story.get("n_papers") or 0
            slide["kicker"] = f"{brand}  ·  {n} numbered papers"
            slide["subtitle"] = line(story.get("indication") or brand)
            slide["narrative"] = story.get("why") or story.get("bet") or ""
        act = acts.get(sid)
        if act:
            slide["act"] = act
            kicker = slide.get("kicker") or ""
            if kicker.startswith(("Phase ", "I ·", "II ·", "III ·", "IV ·")):
                rest = kicker.split("·", 1)[-1].strip() if "·" in kicker else kicker
                rest = re.sub(r"^phase\s+\d+\s*", "", rest, flags=re.I).strip(" ·")
                slide["kicker"] = rest
    return slides, report


def _story_titles(story: dict) -> dict[str, str]:
    brand = story.get("brand") or "Brand"
    molecule = story.get("molecule") or line(str(story.get("indication") or "").rstrip("."), 4) or "the molecule"
    need_stat = story.get("need_stat") or "Need"
    asked_stat = story.get("asked_stat") or "the goal"
    if str(asked_stat).lower() in {"grow", "goal", "need"}:
        asked_stat = "the goal"
    n = int(story.get("n_papers") or 0)
    house_n = len(story.get("house") or []) or 3
    house_word = {1: "One", 2: "Two", 3: "Three", 4: "Four"}.get(house_n, str(house_n))
    habit = cue(story.get("current") or story.get("they_do") or "They wait")
    silent = " ".join(str((row or [""])[0]) for row in (story.get("fourway") or []) if _is_silent(row))
    nnt = story.get("lead_nnt")
    meaning = f"Treat {nnt} to prevent one event." if nnt else "What the lead paper means in clinic"
    stand = "Stand only where the columns agree."
    if re.search(r"cost", silent, re.I):
        stand = "Shout the start. Stay silent on cost."
    elif story.get("position"):
        stand = clip_title(story.get("position"), stand)
    return {
        "title": clip_title(story.get("headline") or "", brand),
        "need": clip_title(f"{need_stat} is the job.", f"{need_stat} is the job."),
        "tension": clip_title(habit or "They wait. We start now.", "They wait. We start now."),
        "belief": clip_title(
            f"They agree. {habit}" if habit else "They agree. They still wait.",
            "They agree. They still wait.",
        ),
        "pico": clip_title(f"Judge {molecule} only in this frame", "Judge the molecule only in this frame"),
        "science-meaning": clip_title(meaning, "What the lead paper means in clinic"),
        "forest": "The numbered papers agree on one axis" if n >= 2 else "One numbered paper is not a forest.",
        "science-compare": "The next paper has a different job",
        "pack": clip_title(f"Each of {n} papers has one job." if n else "No pack yet. Do not invent one."),
        "stand": clip_title(stand, "Stand only where the columns agree."),
        "house": clip_title(f"{house_word} numbered lines we will say"),
        "objections": "Answer cost and wait without dodging.",
        "sequence": "Build the pathway before the campaign.",
        "who": "Start with the rooms we can fund.",
        "science-execute": "From the finding to the move",
        "interventions": clip_title(f"Three {brand} moves that ship", "Three moves that ship."),
        "measure": clip_title(f"If {asked_stat} is flat, kill the rest.", "If the parent metric is flat, kill the rest."),
        "close": clip_title(f"Sign {brand}. Number every claim.", "Sign the bet. Number the claims."),
    }


def _visuals(slides: list[dict], story: dict) -> tuple[list[dict], list[dict]]:
    report = []
    for slide in slides:
        sid = slide.get("id")
        if sid == "need":
            slide["narrative"] = ""
            slide["layout"] = "versus"
            slide["versus"] = {
                "mode": "hero",
                "rows": [{
                    "delta": "≠",
                    "left": {"kicker": "The brief asked", "value": story.get("asked_stat") or "Goal", "text": story.get("asked") or ""},
                    "right": {"kicker": "The file restates", "value": story.get("need_stat") or "Need", "text": story.get("need") or ""},
                }],
            }
            slide.pop("stat", None)
            report.append({"engine": "visuals", "slide": sid, "action": "versus"})
        elif sid == "tension":
            slide["narrative"] = ""
            slide["layout"] = "versus"
            slide["versus"] = {
                "mode": "hero",
                "rows": [{
                    "delta": "→",
                    "left": {"kicker": "What they do", "value": "Wait", "text": story.get("current") or ""},
                    "right": {"kicker": "What must change", "value": "Start", "text": story.get("required") or ""},
                }],
            }
            slide.pop("stat", None)
            report.append({"engine": "visuals", "slide": sid, "action": "versus"})
        elif sid == "stand":
            shout, silent = _stand_groups(story)
            slide["layout"] = "split"
            slide["split"] = {
                "heroLabel": "We may shout",
                "railLabel": "We stay silent",
                "heroes": shout[:2] or [{
                    "kicker": "Stand",
                    "title": "Numbered ground only",
                    "body": story.get("position") or "We stand only where the papers agree.",
                }],
                "rail": silent[:2] or [{
                    "kicker": "Silent",
                    "title": "No silent ground named",
                    "body": "Every territory the brief tested is numbered.",
                }],
            }
            slide.pop("board", None)
            slide["narrative"] = ""
            report.append({"engine": "visuals", "slide": sid, "action": "split"})
        elif sid == "pack":
            cards = _pack_cards(slide, story)
            hero, rest = (cards[0], cards[1:]) if cards else (None, [])
            if hero:
                slide["layout"] = "split"
                slide["split"] = {
                    "heroLabel": "Lead job",
                    "railLabel": "The rest of the pack",
                    "heroes": [hero],
                    "rail": rest,
                }
                slide.pop("board", None)
                report.append({"engine": "visuals", "slide": sid, "action": "split"})
        elif sid == "who":
            cards = _who_cards(story)
            slide["layout"] = "split"
            slide["split"] = {
                "heroLabel": "First",
                "railLabel": "Then it inherits",
                "heroes": cards[:1],
                "rail": cards[1:3],
            }
            slide.pop("board", None)
            report.append({"engine": "visuals", "slide": sid, "action": "split"})
        elif sid == "house":
            cards = (slide.get("board") or {}).get("cards") or []
            steps = [
                {"n": str(i), "title": c.get("title") or f"Line {i}", "body": c.get("body") or "", "ref": c.get("ref") or ""}
                for i, c in enumerate(cards, start=1)
            ]
            slide["layout"] = "flow"
            slide["flow"] = {"steps": steps[:3]}
            slide.pop("board", None)
            slide["narrative"] = ""
            report.append({"engine": "visuals", "slide": sid, "action": "flow"})
        elif sid == "measure":
            cards = (slide.get("board") or {}).get("cards") or []
            for i, card in enumerate(cards):
                if i < 3:
                    card["kicker"] = ("Parent", "Lead", "Kill")[i]
            slide["layout"] = "split"
            slide["split"] = {
                "heroLabel": "Parent metric",
                "railLabel": "Leading signals",
                "heroes": cards[:1] or [{
                    "kicker": "Parent",
                    "title": "The brief's own goal",
                    "body": "If this does not move, the rest is decoration.",
                }],
                "rail": cards[1:3],
            }
            slide.pop("board", None)
            report.append({"engine": "visuals", "slide": sid, "action": "split"})
        elif sid == "belief":
            cards = (slide.get("board") or {}).get("cards") or []
            labels = ("They still wait", "They still fear", "They still stall")
            for i, card in enumerate(cards):
                card["kicker"] = labels[i] if i < len(labels) else "They still do this"
            slide["layout"] = "split"
            slide["split"] = {
                "heroLabel": "Still true",
                "railLabel": "Also still true",
                "heroes": cards[:1],
                "rail": cards[1:3],
            }
            slide.pop("board", None)
            report.append({"engine": "visuals", "slide": sid, "action": "split"})
        elif sid == "objections":
            cards = (slide.get("board") or {}).get("cards") or []
            slide["layout"] = "versus"
            slide["versus"] = {
                "mode": "compact",
                "rows": [
                    {
                        "delta": "↔",
                        "left": {"kicker": "They will say", "text": c.get("title") or ""},
                        "right": {"kicker": "We answer", "text": c.get("body") or "", "ref": c.get("ref") or ""},
                    }
                    for c in cards[:3]
                ],
            }
            slide.pop("board", None)
            slide["narrative"] = ""
            report.append({"engine": "visuals", "slide": sid, "action": "versus"})
        elif sid == "interventions":
            cards = (slide.get("board") or {}).get("cards") or []
            slide["layout"] = "split"
            slide["split"] = {
                "heroLabel": "Move 1",
                "railLabel": "Also ships",
                "heroes": cards[:1],
                "rail": cards[1:3],
            }
            slide.pop("board", None)
            report.append({"engine": "visuals", "slide": sid, "action": "split"})
        elif sid == "title":
            cards = (slide.get("board") or {}).get("cards") or []
            bet = next((c for c in cards if (c.get("kicker") or "").lower() in {"the bet", "the strategy"}), cards[1] if len(cards) > 1 else None)
            others = [c for c in cards if c is not bet]
            if bet:
                slide["split"] = {"heroLabel": "The bet", "railLabel": "The brief", "heroes": [bet], "rail": others}
                slide.pop("board", None)
                report.append({"engine": "visuals", "slide": sid, "action": "split"})
        elif sid == "close":
            slide["layout"] = "close"
            report.append({"engine": "visuals", "slide": sid, "action": "close"})
        elif sid == "pico":
            cards = (slide.get("board") or {}).get("cards") or []
            for card in cards:
                if (card.get("kicker") or "").lower().startswith("outcome"):
                    bits = [b.strip() for b in re.split(r";", card.get("body") or "") if b.strip()]
                    if len(bits) >= 2:
                        card["body"] = listed(bits)
    return slides, report


def _stand_groups(story: dict) -> tuple[list[dict], list[dict]]:
    shout, silent = [], []
    for row in story.get("fourway") or []:
        title = line(row[0]) if row else "Territory"
        cell = row[1] if len(row) > 1 else ""
        if _is_silent(row):
            silent.append({
                "kicker": "Stay silent",
                "title": title or "Silent ground",
                "body": "No numbered paper owns this. We do not shout it.",
            })
        else:
            shout.append({
                "kicker": "We may shout" if not shout else "Also shout",
                "title": title or "Numbered ground",
                "body": _stand_body(cell, story, title),
                "ref": _marks(cell),
            })
    return shout, silent


def _pack_cards(slide: dict, story: dict) -> list[dict]:
    cards = (slide.get("board") or {}).get("cards") or []
    used: set[str] = set()
    jobs = story.get("jobs") or []
    for i, card in enumerate(cards):
        rec = jobs[i] if i < len(jobs) else {}
        role = rec.get("directs") or rec.get("role") or ""
        label = rec.get("roleLabel") or JOB_KICKER.get(role) or card.get("kicker") or "Also sourced"
        if label.lower() in used or label.lower() in {"this paper's job", "sourced", "point"} or label.lower() == (card.get("title") or "").lower():
            label = JOB_KICKER_ALT.get(role) or JOB_KICKER.get(role) or f"Also sourced"
        if label.lower() in used:
            label = f"Also sourced"
        card["kicker"] = label
        used.add(label.lower())
    return cards


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


def _copy(slides: list[dict], story: dict) -> tuple[list[dict], list[dict]]:
    report = []
    brand = (story.get("brand") or "").strip()
    molecule = story.get("molecule") or ""
    for slide in slides:
        sid = slide.get("id")
        title = clip_title(slide.get("title") or "")
        slide["title"] = title
        nar = slide.get("narrative") or ""
        if nar and (is_process(nar) or _same_line(nar, title)):
            slide["narrative"] = ""
            report.append({"engine": "copy", "slide": sid, "action": "cleared narrative", "rule": "process-or-echo"})
        else:
            slide["narrative"] = (nar or "").replace("…", "").replace("...", "")
        sub = slide.get("subtitle") or ""
        if sub and (_same_line(sub, title) or _same_line(sub, brand) or _same_line(sub, slide.get("kicker") or "")):
            slide["subtitle"] = line(story.get("indication") or "") if sid == "title" else ""
        if sid in SCIENCE_IDS and brand and molecule:
            slide["title"] = slide["title"].replace(brand, molecule)
            if slide.get("narrative"):
                slide["narrative"] = slide["narrative"].replace(brand, molecule)
        for card in _cards(slide):
            card["title"] = line(card.get("title") or "")
            card["body"] = _clean_body(card.get("body") or "")
            if EMPTY_SHOUT.match(card.get("body") or ""):
                card["body"] = story.get("papers_allow") or "The numbered pack supports this territory."
            if sid in SCIENCE_IDS and brand and molecule:
                card["title"] = card["title"].replace(brand, molecule)
                card["body"] = (card.get("body") or "").replace(brand, molecule)
        for step in (slide.get("flow") or {}).get("steps") or []:
            step["title"] = line(step.get("title") or "")
            step["body"] = _clean_body(step.get("body") or "")
        for row in (slide.get("versus") or {}).get("rows") or []:
            for side in ("left", "right"):
                pole = row.get(side) or {}
                if pole.get("text"):
                    pole["text"] = _clean_body(pole["text"]) if len((pole.get("text") or "").split()) > 8 else line(pole["text"])
                if pole.get("value"):
                    pole["value"] = line(pole["value"])
    return slides, report


def _critic(slides: list[dict], story: dict) -> tuple[list[dict], list[dict]]:
    report = []
    seen_titles: set[str] = set()
    brand = (story.get("brand") or "").strip()
    molecule = story.get("molecule") or ""
    for slide in slides:
        sid = slide.get("id")
        if is_process(slide.get("narrative") or ""):
            slide["narrative"] = ""
            report.append({"engine": "critic", "slide": sid, "action": "killed narrative", "rule": "process-speak"})
        title_key = _norm(slide.get("title") or "")
        if title_key and title_key in seen_titles:
            report.append({"engine": "critic", "slide": sid, "action": "duplicate title", "rule": "unique-titles"})
        seen_titles.add(title_key)
        used: dict[str, int] = {}
        for card in _cards(slide):
            body = (card.get("body") or "").strip()
            if SILENT_CELL.match(body) or body.lower() in {"silent.", "silent"}:
                card["body"] = "No numbered paper owns this. We do not shout it."
                report.append({"engine": "critic", "slide": sid, "action": "filled silent", "rule": "empty-shout"})
            kick = (card.get("kicker") or "").strip()
            if kick and kick.lower() == (card.get("title") or "").lower() and card.get("body"):
                card["kicker"] = "Point"
            key = kick.lower()
            if key:
                used[key] = used.get(key, 0) + 1
                if used[key] > 1:
                    alt = line(card.get("title") or "", 3) or f"{kick} {used[key]}"
                    card["kicker"] = alt
                    report.append({"engine": "critic", "slide": sid, "action": "deduped kicker", "rule": "unique-kickers"})
            if sid in SCIENCE_IDS and brand and molecule:
                blob = f"{card.get('title')} {card.get('body')}"
                if brand in blob:
                    card["title"] = (card.get("title") or "").replace(brand, molecule)
                    card["body"] = (card.get("body") or "").replace(brand, molecule)
                    report.append({"engine": "critic", "slide": sid, "action": "stripped brand", "rule": "inn-not-brand"})
        if slide.get("layout") in {"versus", "stat"} and slide.get("narrative"):
            labels = " ".join(
                [i.get("label") or "" for i in (slide.get("stat") or {}).get("items") or []]
                + [((r.get("left") or {}).get("text") or "") + ((r.get("right") or {}).get("text") or "")
                   for r in (slide.get("versus") or {}).get("rows") or []]
            )
            if _same_line(slide["narrative"], labels) or slide["narrative"] in labels:
                slide["narrative"] = ""
    return slides, report


def _cards(slide: dict) -> list[dict]:
    out = list((slide.get("board") or {}).get("cards") or [])
    split = slide.get("split") or {}
    out.extend(split.get("heroes") or [])
    out.extend(split.get("rail") or [])
    return out


def _clean_body(text: str) -> str:
    text = " ".join(str(text or "").split()).replace("…", "").replace("...", "")
    return sentence(text, 2) if text else ""


def _same_line(a: str, b: str) -> bool:
    na, nb = _norm(a), _norm(b)
    return bool(na) and bool(nb) and (na == nb or na in nb or nb in na)


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def _marks(text) -> str:
    found = re.findall(r"\[\d+[a-z]?\]", str(text or ""))
    return " ".join(found)


def _is_silent(row) -> bool:
    if not row:
        return False
    cell = row[1] if len(row) > 1 else ""
    blob = " ".join(str(c) for c in row[1:])
    return bool(SILENT_CELL.search(str(cell))) or ("silent" in blob.lower() and "supportive" not in blob.lower())
