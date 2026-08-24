"""Client strategy deck — one idea per 16:9 slide.

The working file stays in the Working file tab. This module only builds the
boardroom narrative: problem, bet, what the papers mean, the moves, the ask,
then Vancouver references. No process slides, no invented funnels.
"""

from __future__ import annotations

from .cite import mark
from .extract import ExtractedBrief


def build_client_deck(
    brief: ExtractedBrief,
    doctrine: dict,
    ledger: dict,
    work: dict,
    interventions: list[dict],
) -> list[dict]:
    brand = brief.brand or "Brand"
    ta = brief.therapy_area or "the therapy area"
    market = brief.market or "the market"
    goal = brief.business_goal or "Grow clinically appropriate adoption with a number we can audit."
    specialties = brief.target_specialties or ["Target specialists", "Referring physicians"]
    lead = ledger.get("lead") or {}
    records = ledger.get("records") or []
    gaps = ledger.get("gaps") or []
    references = ledger.get("references") or work.get("references") or []
    p01 = _phase(work, "01")
    p04 = _phase(work, "04")
    p10 = _phase(work, "10")
    p11 = _phase(work, "11")
    people = people_rows(records)
    compare = compare_rows(records)
    spine = spine_rows(records, interventions)
    primary = (lead.get("citations") or [None])[0] or {}

    slides = [
        _title_slide(brand, ta, market, doctrine, brief),
        _problem_slide(doctrine, p01, goal),
        _bet_slide(doctrine, lead, primary),
        _science_lead_slide(lead, primary),
    ]
    if people:
        slides.append(_meaning_slide(people))
    if compare:
        slides.append(_compare_slide(compare))
    slides.append(_register_slide(records, gaps))
    slides.append(_belief_slide(p04, brief.hcp_insights or []))
    if spine:
        slides.append(_execute_slide(spine))
    slides.append(_moves_slide(interventions))
    slides.append(_who_slide(specialties, interventions))
    slides.append(_measure_slide(goal, p10, interventions))
    slides.append(_close_slide(brand, doctrine, p11))
    slides.extend(reference_slides(references))
    return slides


def people_rows(records: list[dict]) -> list[dict]:
    rows = []
    for r in records:
        if r.get("control_event") is None or r.get("treat_event") is None:
            continue
        if r.get("nnt") is None:
            continue
        control = r["control_event"]
        treat = r["treat_event"]
        arr = r.get("arr")
        if arr is None:
            arr = round(float(control) - float(treat), 1)
        rows.append({
            "name": f"{mark(r)} {r.get('short') or r.get('trial')}",
            "control": control,
            "treat": treat,
            "arr": arr,
            "nnt": r["nnt"],
            "horizon": r.get("horizon") or "",
            "unit": r.get("visual_unit") or "events per 100",
            "pmid": r.get("pmid") or "",
            "ref": r.get("ref") or "",
            "control_label": "Comparator",
            "treat_label": r.get("trial") or "Intervention",
            "claim": r.get("claim_permitted") or "",
        })
    return rows


def compare_rows(records: list[dict]) -> list[dict]:
    rows = []
    ordered = [r for r in records if r.get("directs") == "first-eligible-start"] + [
        r for r in records if r.get("directs") != "first-eligible-start"
    ]
    for r in ordered:
        if r.get("control_event") is None or r.get("treat_event") is None:
            continue
        if r.get("nnt") is not None:
            continue
        rows.append({
            "name": f"{mark(r)} {r.get('short') or r.get('trial')}",
            "left": r["control_event"],
            "right": r["treat_event"],
            "left_label": "Comparator",
            "right_label": r.get("trial") or "Intervention",
            "delta": r.get("arr") if r.get("arr") is not None else "",
            "unit": r.get("visual_unit") or "",
            "pmid": r.get("pmid") or "",
            "ref": r.get("ref") or "",
            "claim": r.get("claim_permitted") or "",
            "horizon": r.get("horizon") or "",
        })
    return rows


def spine_rows(records: list[dict], interventions: list[dict]) -> list[dict]:
    mapping = {
        "first-eligible-start": "first-touch",
        "outcome-permission": "habit-lock",
        "guideline-cover": "peer-cascade",
        "segment-confidence": "myth-reset",
        "local-context": "afford-kit",
    }
    rows = []
    for r in records:
        means = r.get("spine_means")
        if not means:
            continue
        short = r.get("short") or ""
        execute = r.get("spine_execute") or ""
        iv = next((i for i in interventions if i["name"] and i["name"] in execute), None)
        if iv is None:
            iv = next((i for i in interventions if short and short in (i.get("evidenceAnchor") or "")), None)
        if iv is None:
            want = mapping.get(r.get("directs") or "")
            iv = next((i for i in interventions if i["id"] == want), None) if want else None
        rows.append({
            "name": f"{mark(r)} {r.get('short') or r.get('trial') or ''}",
            "science": (r.get("claim_permitted") or "")[:140],
            "means": means,
            "barrier": r.get("spine_barrier") or "",
            "execute": r.get("spine_execute") or (iv["name"] if iv else ""),
            "measure": r.get("spine_measure") or (iv["kill"] if iv else ""),
            "pmid": r.get("pmid") or "",
            "ref": r.get("ref") or "",
            "move": iv["name"] if iv else (r.get("spine_execute") or ""),
        })
    preferred = [r for r in rows if r.get("move") and "First-Touch" in str(r.get("move"))]
    rest = [r for r in rows if r not in preferred]
    ordered = preferred + rest
    return ordered[:4]


def stream_mix(records: list[dict], brief: ExtractedBrief) -> list[dict]:
    counts: dict[str, int] = {}
    for r in records:
        key = (r.get("stream") or "Other").split("/")[0].strip()
        counts[key] = counts.get(key, 0) + 1
    if not counts:
        return [
            {"name": "Uncited brief items", "value": max(1, len(brief.brand_evidence) + len(brief.guidelines))},
        ]
    return [{"name": k, "value": v} for k, v in counts.items()]


def reference_slides(references: list[dict]) -> list[dict]:
    if not references:
        return [{
            "id": "references",
            "section": "References",
            "kicker": "Numbered sources",
            "title": "References",
            "narrative": "This brief has not matched a PMID or DOI. We will not invent a reference list.",
            "layout": "statement",
            "bullets": ["Retrieve primary papers before anyone writes a claim."],
        }]
    slides = []
    chunk = 6
    total = (len(references) + chunk - 1) // chunk
    for i in range(0, len(references), chunk):
        part = references[i:i + chunk]
        page = i // chunk + 1
        slides.append({
            "id": "references" if page == 1 else f"references-{page}",
            "section": "References",
            "kicker": f"Vancouver  ·  {page} of {total}",
            "title": "References",
            "narrative": "Superscripts in the deck are these numbers.",
            "layout": "references",
            "table": {
                "headers": ["No.", "Citation"],
                "rows": [[str(r.get("n")), r.get("citation") or ""] for r in part],
            },
            "refs": [r.get("n") for r in part],
        })
    return slides


def _title_slide(brand: str, ta: str, market: str, doctrine: dict, brief: ExtractedBrief) -> dict:
    return {
        "id": "title",
        "section": "Open",
        "kicker": f"{market}  ·  {ta}",
        "title": brand,
        "subtitle": doctrine.get("bet") or "",
        "narrative": "",
        "layout": "title",
        "footnote": brief.product or brand,
    }


def _problem_slide(doctrine: dict, p01: dict, goal: str) -> dict:
    enemy = (doctrine.get("enemy") or "").strip()
    title = enemy[0].upper() + enemy[1:] if enemy else "What this brief is actually asking us to change"
    if title and not title.endswith("."):
        title = title
    return {
        "id": "problem",
        "section": "Problem",
        "kicker": "The problem",
        "title": title,
        "narrative": p01.get("restatedNeed") or doctrine.get("thesis") or "",
        "layout": "statement",
        "subtitle": f"What the brief asked: {_clip(goal, 140)}",
    }


def _bet_slide(doctrine: dict, lead: dict, primary: dict) -> dict:
    refs = [c.get("ref") for c in (lead.get("citations") or []) if c.get("ref")]
    slide = {
        "id": "the-bet",
        "section": "Bet",
        "kicker": "The bet",
        "title": doctrine.get("bet") or "",
        "narrative": doctrine.get("whyNovel") or "",
        "layout": "statement",
        "refs": refs,
    }
    if doctrine.get("scienceAnchor") or primary:
        slide["callout"] = {
            "label": "We only lead with a numbered paper",
            "text": doctrine.get("scienceAnchor") or "No numbered paper yet — do not lock a lead.",
        }
    return slide


def _science_lead_slide(lead: dict, primary: dict) -> dict:
    tag = mark(primary) if primary.get("ref") else ""
    claim = primary.get("claim") or lead.get("statement") or "No DOI/PMID-backed row matched this brief."
    return {
        "id": "science-lead",
        "section": "Science",
        "kicker": "The paper we lead with",
        "title": claim,
        "subtitle": f"{tag} {primary.get('short')} · PMID {primary.get('pmid')}" if primary.get("short") else "No validated lead yet",
        "narrative": lead.get("statement") or primary.get("citation") or "Retrieve a primary paper before lock.",
        "layout": "statement",
        "refs": [c.get("ref") for c in (lead.get("citations") or []) if c.get("ref")],
    }


def _meaning_slide(people: list[dict]) -> dict:
    first = people[0]
    tag = mark({"ref": first.get("ref")}) if first.get("ref") else ""
    nnt = first.get("nnt")
    return {
        "id": "science-meaning",
        "section": "Science",
        "kicker": "What the science means",
        "title": "In a clinic of 100, this is what the paper showed",
        "subtitle": f"{tag} {first.get('name', '').replace(tag, '').strip()} · PMID {first.get('pmid') or '—'}",
        "narrative": (
            f"{first.get('claim')} {tag} "
            f"{first.get('control')} events on the comparator versus {first.get('treat')} on the intervention"
            + (f" — treat {nnt} to prevent 1 event." if nnt else ".")
        ),
        "layout": "infographic",
        "chart": {
            "kind": "people",
            "title": f"{first.get('name')}: {first.get('unit')}",
            "note": f"Published rates. {tag} PMID {first.get('pmid')}. Horizon: {first.get('horizon')}.",
            "unit": first.get("unit"),
            "data": people[:1],
        },
        "refs": [first.get("ref")] if first.get("ref") else [],
    }


def _compare_slide(compare: list[dict]) -> dict:
    first = compare[0]
    tag = mark({"ref": first.get("ref")}) if first.get("ref") else ""
    return {
        "id": "science-compare",
        "section": "Science",
        "kicker": "What the timing data means",
        "title": "The comparator is the delayed habit, not another molecule",
        "subtitle": f"{tag} {first.get('name', '').replace(tag, '').strip()} · PMID {first.get('pmid') or '—'}",
        "narrative": f"{first.get('claim') or ''} {tag}",
        "layout": "infographic",
        "chart": {
            "kind": "compare",
            "title": f"{first.get('name')}: {first.get('unit')}",
            "note": f"{tag} PMID {first.get('pmid')}. {first.get('horizon')}.",
            "unit": first.get("unit"),
            "data": compare[:1],
        },
        "refs": [first.get("ref")] if first.get("ref") else [],
    }


def _register_slide(records: list[dict], gaps: list[dict]) -> dict:
    all_marks = mark(*records) if records else ""
    gap_note = (
        f"{len(gaps)} brief item(s) still lack a DOI/PMID and cannot set direction."
        if gaps else "No uncited brief items on this working file."
    )
    return {
        "id": "citation-register",
        "section": "Science",
        "kicker": "Evidence forefront",
        "title": "Every lead claim traces to a numbered paper",
        "narrative": (
            f"{len(records)} numbered papers{(' ' + all_marks) if all_marks else ''}. {gap_note} "
            "Full Vancouver list at the end."
        ),
        "layout": "table",
        "table": {
            "headers": ["Ref", "Source", "Published finding", "Grade"],
            "rows": [
                [
                    mark(r),
                    r.get("short") or r.get("trial") or "",
                    _finding(r),
                    r.get("grade") or "",
                ]
                for r in records[:8]
            ] or [["—", "No numbered paper yet", "Do not lock a lead", "—"]],
        },
        "refs": [r.get("ref") for r in records if r.get("ref")],
    }


def _belief_slide(p04: dict, insights: list[str]) -> dict:
    discord = p04.get("discord") or {
        "headers": ["Belief that delays the start", "What the papers show", "Implication"],
        "rows": [[_clip(i, 90), "Map after the register is numbered", "—"] for i in insights[:4]],
    }
    headers = discord.get("headers") or []
    rows = discord.get("rows") or []
    # Keep three columns so the type can breathe on a laptop.
    if len(headers) > 3:
        keep = [0, 1, -1]
        headers = [headers[i] for i in keep]
        rows = [[row[i] if i < len(row) else "" for i in keep] for row in rows]
    return {
        "id": "opportunity",
        "section": "Insight",
        "kicker": "What the doctors already told us",
        "title": "Agreement is an amplifier. Disagreement is the campaign.",
        "narrative": "These lines are from the brief, mapped onto numbered papers. They are not a market model.",
        "layout": "table",
        "table": {"headers": headers, "rows": rows[:5]},
    }


def _execute_slide(spine: list[dict]) -> dict:
    return {
        "id": "science-execute",
        "section": "Action",
        "kicker": "Science → execution",
        "title": "Each cited finding becomes one campaign move",
        "narrative": "",
        "layout": "infographic",
        "chart": {
            "kind": "spine",
            "title": "Science to solution through execution",
            "note": "Only rows with a PMID/DOI. Uncited brief items cannot own a move.",
            "data": spine,
        },
    }


def _moves_slide(interventions: list[dict]) -> dict:
    cards = [
        {
            "title": i["name"],
            "body": i["promise"],
            "meta": i.get("evidenceAnchor") or "citation pending",
        }
        for i in interventions[:5]
    ]
    return {
        "id": "interventions",
        "section": "Action",
        "kicker": "Five moves",
        "title": "Five moves that retire the ritual",
        "narrative": "Each move is the execution of a cited finding — not a separate creative idea.",
        "layout": "cards",
        "cards": cards,
        "bullets": [
            f"{i['name']} — {i['promise']}  [{i.get('evidenceAnchor') or 'citation pending'}]"
            for i in interventions[:5]
        ],
    }


def _who_slide(specialties: list[str], interventions: list[dict]) -> dict:
    lead = specialties[0][:28] if specialties else "Specialist"
    second = (specialties[1][:28] if len(specialties) > 1 else "Consultant")
    names = [i["name"] for i in interventions[:5]]
    cards = [
        {"title": f"{lead} · KOL metro", "body": names[3] if len(names) > 3 else "Peer cascade", "meta": "Q1 heavy · low cost-friction"},
        {"title": f"{lead} · private metro", "body": names[0] if names else "First-Touch", "meta": "Q1 heavy · the eligible visit"},
        {"title": f"{second} · tier-2", "body": names[1] if len(names) > 1 else "Affordability kit", "meta": "Q1 heavy · cost is the veto"},
        {"title": "Hospital pathway owners", "body": names[0] if names else "Discharge initiation", "meta": "Q1 heavy · 48-hour log"},
    ]
    return {
        "id": "segments",
        "section": "Who",
        "kicker": "Who first",
        "title": "Four rooms. Not a year-long spray.",
        "narrative": "Everyone else inherits. Cost-concern is a design input, not a footnote.",
        "layout": "cards",
        "cards": cards,
    }


def _measure_slide(goal: str, p10: dict, interventions: list[dict]) -> dict:
    parent = p10.get("parent") or goal
    kpi_block = p10.get("kpis") or {}
    rows = kpi_block.get("rows") or []
    cards = []
    for row in rows[:4]:
        cards.append({
            "title": row[1] if len(row) > 1 else "Metric",
            "body": row[2] if len(row) > 2 else "",
            "meta": row[4] if len(row) > 4 else (row[0] if row else ""),
        })
    if not cards:
        cards = [
            {"title": "Parent metric", "body": parent, "meta": "From this brief"},
            {
                "title": "Kill if unchanged",
                "body": interventions[0]["kill"] if interventions else "Name a week-8 kill.",
                "meta": "Do not add a tactic",
            },
        ]
    return {
        "id": "measure",
        "section": "Measurement",
        "kicker": "How we will know",
        "title": "The brief’s own goal is the parent metric. Everything else has to explain it.",
        "subtitle": parent,
        "narrative": p10.get("caveat") or "We will not put a made-up funnel on a slide and call it research.",
        "layout": "cards",
        "cards": cards,
    }


def _close_slide(brand: str, doctrine: dict, p11: dict) -> dict:
    return {
        "id": "close",
        "section": "Ask",
        "kicker": "The first 30 days",
        "title": "Sign the bet. Number the claims. Park the gaps.",
        "narrative": p11.get("warn") or "Draft for medical, legal, and regulatory. Local code has the last word.",
        "layout": "close",
        "bullets": (p11.get("ask") or [])[:4],
        "callout": {"label": brand, "text": doctrine.get("scienceLead") or doctrine.get("bet") or ""},
    }


def _phase(work: dict, pid: str) -> dict:
    for phase in work.get("phases") or []:
        if phase.get("id") == pid:
            return phase
    return {}


def _clip(text, n: int) -> str:
    text = " ".join(str(text or "").split())
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def _finding(row: dict) -> str:
    if row.get("nnt"):
        return f"{row.get('control_event')} vs {row.get('treat_event')} per 100; NNT {row['nnt']}"
    if row.get("hr") is not None:
        return f"{row.get('effect_metric') or 'HR'} {row['hr']} ({row.get('low')}–{row.get('high')})"
    return (row.get("claim_permitted") or row.get("endpoint") or "—")[:110]
