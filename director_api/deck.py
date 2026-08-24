"""Client strategy deck — visual 16:9 narrative.

Every content slide carries a figure: forest plot, people-grid, comparison,
table, flowchart, message house, scatter, or trajectory. Working-file process
stays in its own tab. Effect sizes come from numbered papers; planning
charts are labelled as planning, not as research.
"""

from __future__ import annotations

import re

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
    p07 = _phase(work, "07")
    p08 = _phase(work, "08")
    p10 = _phase(work, "10")
    p11 = _phase(work, "11")
    people = people_rows(records)
    compare = compare_rows(records)
    spine = spine_rows(records, interventions)
    forest = forest_rows(records)
    primary = (lead.get("citations") or [None])[0] or {}

    slides = [
        _title_slide(brand, ta, market, doctrine, brief),
        _problem_slide(doctrine, p01, goal, brief),
        _bet_slide(doctrine, lead, primary),
        _science_lead_slide(lead, primary, records),
    ]
    if forest:
        slides.append(_forest_slide(forest, records))
    if people:
        slides.append(_meaning_slide(people))
    if compare:
        slides.append(_compare_slide(compare))
    slides.append(_register_slide(records, gaps))
    slides.append(_belief_slide(p04, brief.hcp_insights or []))
    slides.append(_house_slide(p07, doctrine, records))
    if spine:
        slides.append(_execute_slide(spine))
    slides.append(_moves_slide(interventions))
    slides.append(_matrix_slide(interventions))
    slides.append(_who_slide(specialties, interventions, brief))
    slides.append(_journey_slide(p08, brand))
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
    return (preferred + rest)[:4]


def forest_rows(records: list[dict]) -> list[dict]:
    rows = []
    for r in records:
        if r.get("hr") is None:
            continue
        rows.append({
            "name": f"{mark(r)} {r.get('short') or r.get('trial')}",
            "stream": r.get("stream"),
            "hr": r["hr"],
            "low": r.get("low") if r.get("low") is not None else r["hr"],
            "high": r.get("high") if r.get("high") is not None else r["hr"],
            "grade": r.get("grade"),
            "pmid": r.get("pmid") or "",
            "note": f"{mark(r)} PMID {r.get('pmid') or '—'} · doi:{r.get('doi') or '—'}",
        })
    return rows[:6]


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
        "subtitle": _complete(doctrine.get("bet") or "Start at the first eligible encounter."),
        "narrative": "",
        "layout": "title",
        "chart": {
            "kind": "flow",
            "title": "How this deck is built",
            "data": [
                {"name": "Number the papers", "detail": "Only a DOI or PMID can set campaign direction."},
                {"name": "Name the wait", "detail": _complete(doctrine.get("enemy") or "The behaviour that loses the eligible moment")},
                {"name": "Five sourced moves", "detail": "Each move executes one cited finding."},
            ],
        },
        "footnote": brief.product or brand,
    }


def _problem_slide(doctrine: dict, p01: dict, goal: str, brief: ExtractedBrief) -> dict:
    delay = (brief.hcp_insights or ["The brief does not describe what doctors do at the eligible moment."])[0]
    cost = (brief.access_and_cost or ["Cost is not described in this brief."])[0]
    return {
        "id": "problem",
        "section": "Problem",
        "kicker": "The problem",
        "title": "Doctors already accept the science. They still wait to start.",
        "narrative": "",
        "layout": "split",
        "bullets": [
            _complete(f"What the brief asked us to grow: {goal.strip()}"),
            _complete(f"What doctors actually do: {delay}"),
            _complete(f"What money does next: {cost}"),
        ],
        "chart": {
            "kind": "flow",
            "title": "How the eligible moment is lost",
            "data": [
                {"name": "Patient is eligible", "detail": "The guideline encounter is already on the table."},
                {"name": "Start the familiar first", "detail": _complete(delay)},
                {"name": "Cost finishes the delay", "detail": _complete(cost)},
                {"name": "The window is gone", "detail": _complete(doctrine.get("enemy") or "The wait becomes the protocol")},
            ],
        },
    }


def _bet_slide(doctrine: dict, lead: dict, primary: dict) -> dict:
    refs = [c.get("ref") for c in (lead.get("citations") or []) if c.get("ref")]
    slide = {
        "id": "the-bet",
        "section": "Bet",
        "kicker": "The bet",
        "title": _complete(doctrine.get("bet") or "Start at the first eligible encounter"),
        "narrative": _complete(doctrine.get("whyNovel") or "This is not a better-molecule story"),
        "layout": "split",
        "chart": {
            "kind": "flow",
            "title": "What we are actually fighting",
            "data": [
                {"name": "Enemy", "detail": doctrine.get("enemy") or "Unnamed delay"},
                {"name": "The bet", "detail": doctrine.get("bet") or ""},
                {"name": "Scientific lead", "detail": doctrine.get("scienceAnchor") or "No numbered paper yet — do not lock a lead."},
            ],
        },
        "refs": refs,
    }
    if doctrine.get("scienceAnchor") or primary:
        slide["callout"] = {
            "label": "We only lead with a numbered paper",
            "text": doctrine.get("scienceAnchor") or "No numbered paper yet — do not lock a lead.",
        }
    return slide


def _science_lead_slide(lead: dict, primary: dict, records: list[dict]) -> dict:
    tag = mark(primary) if primary.get("ref") else ""
    claim = primary.get("claim") or lead.get("statement") or "No DOI or PMID matched this brief."
    n = primary.get("n") or next((r.get("n") for r in records if r.get("id") == primary.get("id")), "—")
    return {
        "id": "science-lead",
        "section": "Science",
        "kicker": "The paper we lead with",
        "title": "We lead with a numbered paper, not with a slogan.",
        "bullets": [
            _complete(lead.get("statement") or claim),
            "A line without a PMID does not lock.",
        ],
        "subtitle": f"{tag} {primary.get('short') or 'No validated lead'} · PMID {primary.get('pmid') or '—'}",
        "narrative": "",
        "layout": "split",
        "cards": [
            {
                "title": primary.get("short") or "No lead paper",
                "body": primary.get("citation") or "Retrieve the primary paper before lock.",
                "meta": f"{tag} PMID {primary.get('pmid') or '—'}",
            },
            {
                "title": "What the paper showed",
                "body": claim,
                "meta": "Inside local label and code",
            },
            {
                "title": "So the campaign leads here",
                "body": "We spend against the delay in the window this paper actually studied — not against a later clinic visit.",
                "meta": f"n = {n}",
            },
        ],
        "refs": [c.get("ref") for c in (lead.get("citations") or []) if c.get("ref")],
    }


def _forest_slide(forest: list[dict], records: list[dict]) -> dict:
    return {
        "id": "forest",
        "section": "Science",
        "kicker": "Evidence figure",
        "title": "These are the published effect sizes. We will not invent a missing hazard ratio.",
        "narrative": "Only rows with a DOI or PMID are plotted. Uncited brief items stay off this figure.",
        "layout": "chart",
        "chart": {
            "kind": "forest",
            "title": "Validated evidence position (named trials)",
            "note": "HR or ratio and 95% CI copied from the cited publication. Superscripts are Vancouver numbers.",
            "data": forest,
        },
        "refs": [r.get("ref") for r in records if r.get("hr") is not None and r.get("ref")],
    }


def _meaning_slide(people: list[dict]) -> dict:
    first = people[0]
    tag = mark({"ref": first.get("ref")}) if first.get("ref") else ""
    nnt = first.get("nnt")
    return {
        "id": "science-meaning",
        "section": "Science",
        "kicker": "What the science means",
        "title": "In a clinic of 100 patients, this is what the paper actually showed.",
        "subtitle": f"{tag} {first.get('name', '').replace(tag, '').strip()} · PMID {first.get('pmid') or '—'}",
        "narrative": (
            f"{first.get('claim')} {tag} "
            f"{first.get('control')} events on the comparator versus {first.get('treat')} on the intervention"
            + (f" — treat {nnt} to prevent one event." if nnt else ".")
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
        "title": "The comparator is the delayed habit, not another molecule.",
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
        f"{len(gaps)} brief items still lack a DOI or PMID and cannot set direction."
        if gaps else "No uncited brief items on this working file."
    )
    return {
        "id": "citation-register",
        "section": "Science",
        "kicker": "Evidence forefront",
        "title": "Every lead claim traces to a numbered paper.",
        "narrative": (
            f"{len(records)} numbered papers{(' ' + all_marks) if all_marks else ''}. {gap_note} "
            "The full Vancouver list is at the end of the deck."
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
        "rows": [[_clip(i, 110), "Map after the register is numbered", "—"] for i in insights[:4]],
    }
    headers = discord.get("headers") or []
    rows = discord.get("rows") or []
    if len(headers) > 3:
        keep = [0, 1, -1]
        headers = [headers[i] for i in keep]
        rows = [[row[i] if i < len(row) else "" for i in keep] for row in rows]
    concord = p04.get("concord") or {}
    n_discord = len(rows)
    n_concord = len((concord.get("rows") or []))
    return {
        "id": "opportunity",
        "section": "Insight",
        "kicker": "What the doctors already told us",
        "title": "Agreement is an amplifier. Disagreement is the campaign.",
        "narrative": "These lines are from the brief, mapped onto numbered papers. They are not a market model.",
        "layout": "table",
        "table": {"headers": headers, "rows": rows[:5]},
        "chart": {
            "kind": "bar",
            "title": "Mapped insight lines from this brief",
            "unit": "lines",
            "note": "Counts from this brief, not a survey index.",
            "data": [
                {"name": "Agrees with papers", "value": n_concord},
                {"name": "Disagrees — the campaign", "value": max(n_discord, 1)},
            ],
        },
    }


def _house_slide(p07: dict, doctrine: dict, records: list[dict]) -> dict:
    house = p07.get("house") or {"headers": ["Pillar", "Line", "Ref", "Proof"], "rows": []}
    rows = house.get("rows") or []
    data = [
        {
            "name": row[0] if row else "Pillar",
            "line": row[1] if len(row) > 1 else "",
            "ref": row[2] if len(row) > 2 else "",
            "proof": row[3] if len(row) > 3 else "",
        }
        for row in rows[:3]
    ]
    if not data:
        data = [{"name": "Permission now", "line": doctrine.get("bet") or "", "ref": "—", "proof": "Citation pending"}]
    return {
        "id": "house",
        "section": "Message",
        "kicker": "Message house",
        "title": "One theme. Three pillars. A pillar without a number does not ship.",
        "narrative": p07.get("theme") or doctrine.get("bet") or "",
        "layout": "infographic",
        "chart": {
            "kind": "house",
            "title": _complete(p07.get("theme") or doctrine.get("bet") or "Start at the first eligible visit"),
            "data": data,
        },
        "refs": [r.get("ref") for r in records[:3] if r.get("ref")],
    }


def _execute_slide(spine: list[dict]) -> dict:
    return {
        "id": "science-execute",
        "section": "Action",
        "kicker": "Science → execution",
        "title": "Each cited finding becomes one campaign move.",
        "narrative": "Science names the prize. The barrier names why it is lost. The intervention is how we take it.",
        "layout": "infographic",
        "chart": {
            "kind": "spine",
            "title": "Science to solution through execution",
            "note": "Only rows with a PMID or DOI. Uncited brief items cannot own a move.",
            "data": spine,
        },
    }


def _moves_slide(interventions: list[dict]) -> dict:
    return {
        "id": "interventions",
        "section": "Action",
        "kicker": "Five moves",
        "title": "Five moves that retire the wait, each anchored to a numbered paper.",
        "narrative": "Each move is the execution of a cited finding, not a separate creative idea.",
        "layout": "cards",
        "cards": [
            {
                "title": i["name"],
                "body": _first_sentence(i["promise"]),
                "meta": i.get("evidenceAnchor") or "citation pending",
            }
            for i in interventions[:5]
        ],
        "bullets": [
            f"{i['name']} — {i['promise']}  [{i.get('evidenceAnchor') or 'citation pending'}]"
            for i in interventions[:5]
        ],
    }


def _matrix_slide(interventions: list[dict]) -> dict:
    return {
        "id": "matrix",
        "section": "Action",
        "kicker": "Where we spend first",
        "title": "Q1 buys proof of mechanism. We do not spend the year on congress theatre.",
        "narrative": "Impact versus feasibility for this architecture. These are design scores, not a market survey.",
        "layout": "chart",
        "chart": {
            "kind": "scatter",
            "title": "Impact vs feasibility of the five moves",
            "xLabel": "Feasibility",
            "yLabel": "Impact on the key driver",
            "note": "Architecture scores for this mix. Not research.",
            "data": [
                {"name": i["name"], "x": i.get("feasibility") or 50, "y": i.get("impact") or 50, "z": 28}
                for i in interventions[:5]
            ] + [{"name": "Congress theatre", "x": 40, "y": 34, "z": 18}],
        },
    }


def _who_slide(specialties: list[str], interventions: list[dict], brief: ExtractedBrief) -> dict:
    lead = specialties[0] if specialties else "Specialist"
    second = specialties[1] if len(specialties) > 1 else "Consultant"
    names = [i["name"] for i in interventions[:5]]
    rows = [
        [f"{lead} · KOL metro", names[3] if len(names) > 3 else "Peer cascade", "Low", "Heavy"],
        [f"{lead} · private metro", names[0] if names else "First-Touch", "Medium", "Heavy"],
        [f"{second} · tier-2", names[1] if len(names) > 1 else "Affordability kit", "High", "Heavy"],
        ["Hospital pathway owners", names[0] if names else "Discharge initiation", "Medium", "Heavy"],
        ["Early-career / trainee", names[2] if len(names) > 2 else "Myth-reset", "Medium", "Medium"],
        ["GP / referrer", "Referral trigger, not a full lesson", "High", "Light"],
    ]
    return {
        "id": "segments",
        "section": "Who",
        "kicker": "Who first",
        "title": "Four rooms carry the year. Everyone else inherits.",
        "narrative": "Activation is a specialty × city × cost grid that we then collapse. Cost-concern is a design input, not a footnote.",
        "layout": "table",
        "table": {
            "headers": ["Segment", "Lead intervention", "Cost posture", "Q1 weight"],
            "rows": rows,
        },
    }


def _journey_slide(p08: dict, brand: str) -> dict:
    stages = (p08.get("stages") or {}).get("rows") or [
        ["Before launch", "Pathway owners write the first-eligible protocol", "Medical leads"],
        ["First quarter", "One hospital live, one cost kit, one sourced myth", "Field + medical"],
        ["Adoption", "The second prescription is designed", "CRM through MLR"],
        ["After the burst", "The pathway stays when the campaign money stops", "Handover"],
    ]
    return {
        "id": "journey",
        "section": "Engagement",
        "kicker": "The sequence",
        "title": "A doctor should feel a designed sequence, not a spray of assets.",
        "narrative": p08.get("rule") or f"If a contact cannot name a numbered paper or a behaviour we are changing, it does not go on the {brand} plan.",
        "layout": "infographic",
        "chart": {
            "kind": "flow",
            "title": "Campaign sequence",
            "data": [
                {"name": _complete(row[0]), "detail": _complete(row[1])}
                for row in stages[:4]
            ],
        },
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
                "body": interventions[0]["kill"] if interventions else "Name a week-8 kill criterion.",
                "meta": "Do not add a tactic",
            },
        ]
    series = _qoq_from_goal(goal)
    slide = {
        "id": "measure",
        "section": "Measurement",
        "kicker": "How we will know",
        "title": "The parent metric is the goal written in the brief.",
        "subtitle": _complete(parent),
        "narrative": "This line is a planning target from the brief. It is not an audited baseline.",
        "layout": "chart" if series else "cards",
        "cards": cards,
    }
    if series:
        slide["chart"] = {
            "kind": "line",
            "title": "Planning target taken from the brief’s stated QoQ goal",
            "note": "Index, Q0 = 100. This is the brief’s own ambition, not an audited baseline.",
            "series": ["target"],
            "data": series,
        }
    return slide


def _close_slide(brand: str, doctrine: dict, p11: dict) -> dict:
    asks = (p11.get("ask") or [])[:4]
    steps = [
        {"name": "Days 1–10", "detail": "Lock the bet and the numbered scientific lead."},
        {"name": "Days 11–20", "detail": "Stand up one hospital pathway and one cost conversation."},
        {"name": "Days 21–30", "detail": "Clear MLR on every line that carries a superscript."},
    ]
    if asks:
        steps = [{"name": f"Ask {i + 1}", "detail": _first_sentence(a)} for i, a in enumerate(asks[:4])]
    return {
        "id": "close",
        "section": "Ask",
        "kicker": "The first 30 days",
        "title": "Sign the bet. Number the claims. Park the gaps.",
        "narrative": _complete(p11.get("warn") or "Draft for medical, legal, and regulatory"),
        "layout": "close",
        "chart": {
            "kind": "flow",
            "title": "What we need signed in the room",
            "data": steps,
        },
        "callout": {"label": brand, "text": _complete(doctrine.get("scienceLead") or doctrine.get("bet") or "")},
    }


def _qoq_from_goal(goal: str) -> list[dict] | None:
    match = re.search(r"(\d+(?:\.\d+)?)\s*%", goal or "")
    if not match:
        return None
    rate = float(match.group(1)) / 100.0
    value = 100.0
    rows = [{"name": "Q0", "target": 100}]
    for q in range(1, 5):
        value *= 1 + rate
        rows.append({"name": f"Q{q}", "target": round(value)})
    return rows


def _phase(work: dict, pid: str) -> dict:
    for phase in work.get("phases") or []:
        if phase.get("id") == pid:
            return phase
    return {}


def _clip(text, n: int) -> str:
    text = " ".join(str(text or "").split())
    if len(text) <= n:
        return text
    cut = text[: n - 1].rsplit(" ", 1)[0]
    return (cut or text[: n - 1]).rstrip(".,;:") + "…"


def _complete(text) -> str:
    text = " ".join(str(text or "").split())
    if not text:
        return ""
    if text[-1] in ".?!":
        return text
    return text + "."


def _first_sentence(text) -> str:
    text = " ".join(str(text or "").split())
    if not text:
        return ""
    for sep in (". ", "? ", "! "):
        if sep in text:
            return _complete(text.split(sep)[0])
    return _complete(text)


def _finding(row: dict) -> str:
    if row.get("nnt"):
        return f"{row.get('control_event')} vs {row.get('treat_event')} per 100; NNT {row['nnt']}"
    if row.get("hr") is not None:
        return f"{row.get('effect_metric') or 'HR'} {row['hr']} ({row.get('low')}–{row.get('high')})"
    return (row.get("claim_permitted") or row.get("endpoint") or "—")[:110]
