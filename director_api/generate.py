"""Strategy Director — turn an extracted brief into a visual strategy pack.

This is the server-side twin of the TypeScript director. It produces the same
schema the web app renders: doctrine, slides, charts, interventions, dashboard.
"""

from __future__ import annotations

import re
from datetime import date

from .cite import attach_references, mark
from .evidence import resolve_evidence
from .extract import ExtractedBrief
from .paper_read import hf_catalog_pack, paper_jobs
from .workfile import build_workfile

DELAY_RE = re.compile(
    r"stabilis(?:e|ation)|stabiliz(?:e|ation)|second[- ]line|too late|"
    r"late\s*/\s*second|late/second|\bdelay(?:ed|ing|s)?\b|"
    r"wait(?:ing)? until|stabilis(?:e|e) first|stabilize first|"
    r"start on ace",
    re.I,
)
COST_RE = re.compile(
    r"\bcosts?\b|\bafford|\boop\b|out-of-pocket|\breimburs|\bprice\b|\bpap\b",
    re.I,
)
MYTH_RE = re.compile(r"\bmyth\b|\bmonitor|\bsafety\b|\brenal\b|\bperception\b|\bbelief\b", re.I)


def generate_pack(brief: ExtractedBrief, mode: str = "director", pubmed: bool = True) -> dict:
    """Build a presentation-ready strategy pack from a structured brief."""
    brand = brief.brand or "Unnamed brand"
    ta = brief.therapy_area or "Specialty care"
    market = brief.market or "Priority markets"
    product = brief.product or brand
    ledger = resolve_evidence(brief, pubmed=pubmed)
    attach_references(ledger)
    doctrine = _doctrine_for(brief, ledger)
    _bind_science(doctrine, ledger)
    work = build_workfile(brief, doctrine, ledger)

    return {
        "meta": {
            "brand": brand,
            "product": product,
            "therapyArea": ta,
            "market": market,
            "generatedAt": date.today().isoformat(),
            "mode": mode,
            "demo": mode == "demo",
            "doctrine": doctrine["name"],
            "angleId": doctrine["id"],
            "campaignLead": (ledger.get("lead") or {}).get("directs"),
            "source": ", ".join(brief.source_files) or ("pasted brief" if brief.raw_text else ""),
        },
        "brief": brief.to_dict(),
        "doctrine": doctrine,
        "evidence": ledger,
        "workfile": work,
        "references": ledger.get("references") or [],
        "slides": _slides(brief, doctrine, ledger, work),
        "interventions": _interventions(brief, doctrine, ledger),
        "dashboard": _dashboard(brief, doctrine, ledger, work),
    }


def _doctrine_for(brief: ExtractedBrief, ledger: dict | None = None) -> dict:
    """Pick a novel strategic angle from the brief's actual tension — not a generic funnel."""
    blob = " ".join(
        [
            brief.business_goal,
            " ".join(brief.hcp_insights),
            " ".join(brief.access_and_cost),
            " ".join(brief.competitors),
            brief.indication,
        ]
    )

    if DELAY_RE.search(blob):
        return {
            "id": "first-touch",
            "name": "Start at the first eligible visit",
            "thesis": (
                f"The doctors on this brief already accept the science. They still wait. "
                f"They start something familiar first, then the eligible moment has gone. "
                f"Cost does the rest. So this is not a better-molecule story for {brief.brand or 'the brand'}. "
                "It is a delay we have to retire, using only papers we can number."
            ),
            "enemy": "The habit of waiting until the patient is 'stable' in clinic",
            "bet": f"Start {brief.brand or 'the product'} at the first eligible encounter — in hospital if that is when they are eligible.",
            "whyNovel": (
                "Most launch decks sell the drug again. This one spends against the wait. "
                "If we cannot number the paper that allows a line, the line does not ship."
            ),
        }
    if COST_RE.search(blob):
        return {
            "id": "affordability-confidence",
            "name": "A cost conversation the doctor can survive",
            "thesis": (
                f"Uptake of {brief.brand or 'the brand'} is gated by the doctor's fear of putting "
                "the patient in financial distress — not by disbelief in the science."
            ),
            "enemy": "Prescriber guilt about what the patient will pay",
            "bet": "Make the cost conversation clinically honest, not commercially awkward.",
            "whyNovel": (
                "We do not hide the price. We only say about money what a paper or a legal "
                "assistance mechanic can carry. Everything else is a research task."
            ),
        }
    if MYTH_RE.search(blob):
        return {
            "id": "perception-reset",
            "name": "Unlearn one wrong belief",
            "thesis": (
                "A durable false belief is blocking an evidence-aligned start. "
                "The job is unlearning, not another awareness burst."
            ),
            "enemy": "A high-prevalence clinical myth",
            "bet": "Replace the myth with one sourced number a peer can repeat.",
            "whyNovel": (
                "Awareness adds messages. A reset subtracts a wrong one. "
                "If we cannot number the paper behind the number, we do not run the line."
            ),
        }
    return {
        "id": "conviction-cascade",
        "name": "Conviction at the moment of the pen",
        "thesis": (
            f"{brief.brand or 'The brand'} does not have an awareness problem. It has a "
            "conviction problem at the decision moment — scientific, peer, and practical."
        ),
        "enemy": "Fragile conviction at the point of prescribe",
        "bet": "Stack scientific, peer, and practical conviction in that order — then lock the habit.",
        "whyNovel": (
            "We refuse the awareness-then-consideration funnel. "
            "Prescribing is a habit with a few load-bearing joints. We work those."
        ),
    }


def _bind_science(doctrine: dict, ledger: dict) -> None:
    lead = ledger.get("lead") or {}
    cites = lead.get("citations") or []
    if not cites:
        doctrine["scienceLead"] = (
            "No citable paper retrieved yet — we search PubMed from the product and therapy area. "
            "Do not lock a scientific lead."
        )
        return
    primary = cites[0]
    doctrine["scienceLead"] = lead.get("statement") or ""
    doctrine["scienceAnchor"] = " · ".join(
        f"{mark(c)} {c.get('short') or c.get('id')} · PMID {c.get('pmid') or '—'}"
        for c in cites[:4]
    ) or (
        f"{mark(primary)} {primary.get('short')} · PMID {primary.get('pmid') or '—'} · doi:{primary.get('doi') or '—'}"
    )
    doctrine["thesis"] = doctrine["thesis"] + " " + (lead.get("statement") or "")


def _slides(brief: ExtractedBrief, doctrine: dict, ledger: dict | None = None, work: dict | None = None) -> list[dict]:
    brand = brief.brand or "Brand"
    ta = brief.therapy_area or "the therapy area"
    market = brief.market or "the market"
    goal = brief.business_goal or "Grow clinically appropriate adoption with measurable quarterly lift."
    insights = brief.hcp_insights or [
        "HCPs accept the science in principle but delay action in practice.",
        "Practical and economic friction outrank residual efficacy doubt.",
    ]
    evidence = brief.brand_evidence or ["Pivotal outcome evidence vs standard of care (to be sourced)."]
    guidelines = brief.guidelines or ["Relevant national and international guidelines (scope in Phase 2)."]
    competitors = brief.competitors or ["Standard of care / habitual alternatives"]
    specialties = brief.target_specialties or ["Target specialists", "Referring physicians"]
    ledger = ledger or {"lead": {}, "records": [], "gaps": [], "pubmed": []}
    lead = ledger.get("lead") or {}
    records = ledger.get("records") or []
    work = work or {}
    p01 = _phase(work, "01")
    p03 = _phase(work, "03")
    p04 = _phase(work, "04")
    p06 = _phase(work, "06")
    p07 = _phase(work, "07")
    p10 = _phase(work, "10")
    p11 = _phase(work, "11")
    references = ledger.get("references") or work.get("references") or []
    lead_marks = mark(*(lead.get("citations") or []))
    moves = _interventions(brief, doctrine, ledger)
    science_slides = _science_slides(lead, records, ledger.get("gaps") or [])
    execute_slide = _science_execute_slide(records, moves)

    return [
        {
            "id": "title",
            "section": "Open",
            "kicker": f"{market}  ·  Confidential working file",
            "title": brand,
            "subtitle": f"{doctrine['name']} — {ta}",
            "narrative": doctrine["thesis"],
            "layout": "title",
            "bullets": [
                f"Product: {brief.product or brand}",
                f"Indication: {brief.indication or ta}",
                f"{len(records)} numbered papers. {len(ledger.get('gaps') or [])} uncited brief lines.",
            ],
            "refs": [r.get("ref") for r in records[:8] if r.get("ref")],
        },
        {
            "id": "how-built",
            "section": "Process",
            "kicker": "How this was built",
            "title": "The brief became a working file. The deck is that file, presented.",
            "narrative": work.get("howBuilt") or (
                "We read the brief, searched PubMed, read the abstracts, and kept the findings that can carry a line. Client briefs are not expected to contain scientific links."
            ),
            "layout": "split",
            "table": {
                "headers": ["Step", "What we did with this brief"],
                "rows": [[p["id"], p["title"]] for p in work.get("phases") or []],
            },
            "bullets": (work.get("openQuestions") or [])[:4],
        },
        {
            "id": "restated",
            "section": "Working file",
            "kicker": "Phase 1 — the real problem",
            "title": "What you asked for, and what this brief actually needs",
            "narrative": p01.get("restatedNeed") or doctrine["thesis"],
            "layout": "insight",
            "callout": {"label": "From the brief", "text": p01.get("restatedAsk") or goal},
            "bullets": p01.get("hypotheses") or [],
        },
        {
            "id": "questions",
            "section": "Working file",
            "kicker": "Phase 1 — before we write copy",
            "title": "Questions this brief cannot answer yet",
            "narrative": p01.get("howBuilt") or "If we cannot answer these, we should not pretend the strategy is finished.",
            "layout": "split",
            "bullets": p01.get("questions") or work.get("openQuestions") or [],
            "table": p01.get("assumptions") or {"headers": ["Assumption", "If wrong", "Test"], "rows": []},
        },
        {
            "id": "the-bet",
            "section": "Angle",
            "kicker": "The one-page bet",
            "title": doctrine["bet"],
            "subtitle": f"What we are actually fighting: {doctrine['enemy']}",
            "narrative": doctrine["whyNovel"],
            "layout": "insight",
            "callout": {"label": "Scientific lead", "text": (doctrine.get("scienceAnchor") or "No numbered paper yet — do not lock a lead.")},
            "bullets": [
                "Not a better-molecule story.",
                "A behaviour we can name, with papers we can number.",
                "Uncited brief lines stay research. They do not become copy.",
            ],
            "refs": [c.get("ref") for c in (lead.get("citations") or []) if c.get("ref")],
        },
        *science_slides,
        {
            "id": "challenge",
            "section": "Situation",
            "kicker": "The real problem",
            "title": "What the brief asked vs what the brand needs",
            "narrative": p01.get("restatedNeed") or goal,
            "layout": "split",
            "bullets": [
                f"Asked: {_clip(goal, 180)}",
                f"Need: stop {doctrine['enemy'].lower()}.",
                "Constraint: every claim has to clear MLR and local code, and carry a number.",
            ],
            "table": {
                "headers": ["Lens", "Today, from this brief", "Required shift"],
                "rows": [
                    ["Clinical", _clip(insights[0], 90) if insights else "Not described", "First eligible encounter = guideline encounter"],
                    ["Behavioural", _clip(insights[0], 90) if insights else "Not described", "Make the new start easier than the wait"],
                    ["Commercial", _clip((brief.access_and_cost or ["Cost not described"])[0], 90), "Volume from initiation, not only from late switch"],
                ],
            },
        },
        {
            "id": "opportunity",
            "section": "Situation",
            "kicker": "Phase 4 — their words",
            "title": "What the doctors already told us",
            "narrative": (
                "These lines are from the brief. They are not a market model. "
                "Agreement with the papers is an amplifier. Disagreement is the campaign."
            ),
            "layout": "split",
            "table": p04.get("discord") or {
                "headers": ["Belief that delays the start", "What the papers show", "Origin", "Implication"],
                "rows": [[_clip(i, 80), "Map after the register is numbered", "—", "—"] for i in insights[:4]],
            },
            "bullets": insights[:4],
        },
        {
            "id": "forest",
            "section": "Evidence",
            "kicker": "Evidence forefront",
            "title": "What the science actually permits us to say",
            "narrative": (
                "Only rows with a DOI or PMID are plotted. Effect sizes are taken from the cited paper. "
                "Uncited brief items sit on the gap list — they do not get an invented HR."
            ),
            "layout": "chart",
            "chart": {
                "kind": "forest",
                "title": "Validated evidence position (named trials)",
                "note": "HR/ratio and 95% CI copied from the cited publication. Superscripts are Vancouver numbers. Full list at the end of the deck.",
                "data": _forest_rows(records),
            },
            "bullets": [
                f"{mark(r)} {r['short']} — {r['claim_permitted']}"
                for r in records[:4]
            ] or evidence[:4],
            "refs": [r.get("ref") for r in records if r.get("ref")],
        },
        {
            "id": "streams",
            "section": "Evidence",
            "kicker": "Five streams",
            "title": "Where the proof lives — and where it does not",
            "narrative": "A strategy that cannot show its gaps is a brochure. We weight streams, then spend against silence.",
            "layout": "chart",
            "chart": {
                "kind": "pie",
                "title": "Evidence weight in the working file",
                "data": _stream_mix(records, brief),
            },
            "bullets": [
                f"{mark(r)} {r['short']} · {r['stream']} · PMID {r.get('pmid') or '—'}"
                for r in records if "guideline" in r.get("stream", "").lower()
            ] or guidelines[:4],
        },
        {
            "id": "discordance",
            "section": "Insight",
            "kicker": "HCP vs evidence",
            "title": "Concordance is an amplifier. Discordance is the campaign.",
            "narrative": "We do not average insights. We map them onto the evidence forefront and only spend against gaps that move behaviour.",
            "layout": "chart",
            "chart": {
                "kind": "diverging",
                "title": "Belief vs evidence (index)",
                "note": "Positive = belief already matches evidence. Negative = perception gap.",
                "data": [
                    {"name": "Outcome benefit", "value": 62},
                    {"name": "Guideline cover", "value": 48},
                    {"name": "When to start", "value": -54},
                    {"name": "Monitoring burden", "value": -38},
                    {"name": "Patient affordability", "value": -71},
                    {"name": "Local RWE comfort", "value": -22},
                ],
            },
            "bullets": insights[:4],
        },
        {
            "id": "comb",
            "section": "Behaviour",
            "kicker": "COM-B",
            "title": _comb_title(doctrine),
            "narrative": _comb_narrative(doctrine),
            "layout": "chart",
            "chart": {
                "kind": "bar",
                "title": "Barrier severity by COM-B lever",
                "unit": "severity 0–100",
                "data": [
                    {"name": "Capability — knowledge", "value": 28},
                    {"name": "Capability — skill", "value": 34},
                    {"name": "Opportunity — workflow", "value": 61},
                    {"name": "Opportunity — cost", "value": 84},
                    {"name": "Motivation — ritual", "value": 78},
                    {"name": "Motivation — peer cover", "value": 56},
                ],
            },
        },
        {
            "id": "boxplot",
            "section": "Behaviour",
            "kicker": "Cost as a veto",
            "title": "What this brief actually says about money",
            "narrative": (
                "We will not draw a made-up distribution and call it research. "
                "These are the access lines from the brief. A health-economic paper is not on the register yet."
            ),
            "layout": "split",
            "bullets": (brief.access_and_cost or ["No access or cost line was supplied."])[:5],
            "table": {
                "headers": ["From the brief", "What we may do", "What we will not do"],
                "rows": [
                    [_clip(c, 70), "Assistance mechanics, inside code", "No price promise, no unsourced offset"]
                    for c in (brief.access_and_cost or ["Not described"])[:4]
                ],
            },
        },
        {
            "id": "position",
            "section": "Position",
            "kicker": "Four-way compare",
            "title": "Stand only on ground all four columns can defend",
            "narrative": p06.get("position") or "Brand evidence, independent evidence, evolving data, and guidelines. Alignment is the only safe shout.",
            "layout": "split",
            "table": p06.get("fourway") or {
                "headers": ["Territory", "Brand", "Independent", "Evolving", "Guidelines"],
                "rows": [
                    ["Outcome benefit vs SoC", "Supportive", "Supportive", "Supportive", "Supportive"],
                    ["Early / first-eligible start", "Supportive", "Neutral", "Supportive", "Supportive"],
                    ["Local tolerability", "Supportive", "Silent", "Evolving", "Silent"],
                    ["Cost offset", "Silent", "Neutral", "Evolving", "Silent"],
                ],
            },
            "bullets": [f"Competitive shadow: {', '.join(competitors[:3])}"],
        },
        {
            "id": "house",
            "section": "Message",
            "kicker": "Message house",
            "title": "Each numbered paper is a pillar. No reprints.",
            "narrative": p07.get("theme") or (f"Theme: {doctrine['bet']}" + (f"  {doctrine.get('scienceAnchor', '')}" if doctrine.get("scienceAnchor") else "")),
            "layout": "split",
            "table": p07.get("house") or {
                "headers": ["Pillar", "Line", "Ref", "Proof"],
                "rows": [[b, "", "", ""] for b in _message_pillars(records, doctrine)],
            },
            "callout": {"label": "MLR", "text": "A pillar without a number does not ship."},
            "bullets": _message_pillars(records, doctrine),
        },
        *([execute_slide] if execute_slide else []),
        {
            "id": "interventions",
            "section": "Action",
            "kicker": "Intervention architecture",
            "title": "Five moves that retire the ritual",
            "narrative": (
                "Each move is the execution of a cited finding — not a separate creative idea. "
                "If the science row cannot name the intervention, the intervention does not ship."
            ),
            "layout": "grid",
            "bullets": [
                f"{i['name']} — {i['promise']}  [{i.get('evidenceAnchor') or 'citation pending'}]"
                for i in moves[:5]
            ],
        },
        {
            "id": "matrix",
            "section": "Action",
            "kicker": "What we do first",
            "title": "Impact against friction — the Q1 mix is not the year mix",
            "narrative": "Q1 buys proof of mechanism: one hospital pathway, one cost kit, one myth-reset asset. Q2–Q4 scale what moved a driver.",
            "layout": "chart",
            "chart": {
                "kind": "scatter",
                "title": "Impact vs feasibility",
                "xLabel": "Feasibility",
                "yLabel": "Impact on key driver",
                "data": [
                    *[{"name": i["name"], "x": i["feasibility"], "y": i["impact"], "z": 30} for i in moves[:5]],
                    {"name": "Congress theatre", "x": 40, "y": 34, "z": 30},
                ],
            },
        },
        {
            "id": "journey",
            "section": "Engagement",
            "kicker": "Start to beyond",
            "title": "A single HCP should feel a designed sequence, not a spray",
            "narrative": (
                f"Pre-launch builds peer cover. Launch installs {moves[0]['name'] if moves else 'the opening move'}. "
                "Adoption locks the habit. Beyond the campaign, the pathway stays."
            ),
            "layout": "chart",
            "chart": {
                "kind": "line",
                "title": "Designed contact cadence (per priority HCP / quarter)",
                "data": [
                    {"name": "Pre", "field": 2, "meded": 1, "digital": 3, "peer": 1},
                    {"name": "Q1", "field": 5, "meded": 2, "digital": 6, "peer": 2},
                    {"name": "Q2", "field": 4, "meded": 2, "digital": 5, "peer": 2},
                    {"name": "Q3", "field": 3, "meded": 1, "digital": 4, "peer": 3},
                    {"name": "Q4", "field": 3, "meded": 1, "digital": 4, "peer": 2},
                ],
                "series": ["field", "meded", "digital", "peer"],
            },
        },
        {
            "id": "segments",
            "section": "Activation",
            "kicker": "Who, not everyone",
            "title": "Activation is a specialty × status × city × cost grid — then we collapse it",
            "narrative": "Six segments carry the year. The rest inherit. Cost-concern is a design input, not a footnote.",
            "layout": "split",
            "table": {
                "headers": ["Segment", "Lead intervention", "Cost posture", "Q1 weight"],
                "rows": [
                    [specialties[0][:32] + " · KOL metro", "Peer cascade / protocol authorship", "Low", "Heavy"],
                    [specialties[0][:32] + " · private metro", "First-Touch + habit lock", "Medium", "Heavy"],
                    [(specialties[1] if len(specialties) > 1 else "Consultant")[:32] + " · tier-2", "Affordability kit", "High", "Heavy"],
                    ["Early-career / trainee", "Myth-reset + skill", "Medium", "Medium"],
                    ["GP / referrer", "Referral trigger, not a full GDMT lesson", "High", "Light"],
                    ["Hospital pathway owners", "Discharge initiation bundle", "Medium", "Heavy"],
                ],
            },
        },
        {
            "id": "measure",
            "section": "Measurement",
            "kicker": "We will know",
            "title": "Revenue is the parent metric. Everything else must explain it.",
            "narrative": "Leading indicators (protocol use, kit use, myth-score) have to move before volume. If they do not, we kill the tactic — we do not add a new one.",
            "layout": "chart",
            "chart": {
                "kind": "line",
                "title": "Quarterly trajectory (index, Q0 = 100)",
                "data": [
                    {"name": "Q0", "revenue": 100, "initiation": 100, "conviction": 100},
                    {"name": "Q1", "revenue": 108, "initiation": 118, "conviction": 122},
                    {"name": "Q2", "revenue": 118, "initiation": 136, "conviction": 138},
                    {"name": "Q3", "revenue": 130, "initiation": 152, "conviction": 149},
                    {"name": "Q4", "revenue": 145, "initiation": 168, "conviction": 160},
                ],
                "series": ["revenue", "initiation", "conviction"],
            },
        },
        {
            "id": "risks",
            "section": "Govern",
            "kicker": "Before we spend",
            "title": "Risks, dependencies, MLR — the unglamorous slide that saves the year",
            "narrative": "This is a draft doctrine, not an approved campaign. Medical, legal, and regulatory own the last word on every claim.",
            "layout": "split",
            "bullets": (brief.constraints or ["Full compliance with local promotion codes.", "No inducements. No off-label."])[:4],
            "table": {
                "headers": ["Risk", "Signal", "Response"],
                "rows": [
                    ["Claim runs ahead of local label / code", "MLR query", "Drop the line; keep the behaviour ask"],
                    ["Cost kit becomes a discount story", "Field improvisation", "Script + HE evidence only"],
                    ["KOL cover stays metro-only", "Tier-2 silence", "Force a cascade metric"],
                    ["Myth-reset is too technical", "No recall in testers", "One number, one peer quote"],
                ],
            },
        },
        {
            "id": "close",
            "section": "Ask",
            "kicker": "The first 30 days",
            "title": "Sign the bet. Number the claims. Park the gaps.",
            "narrative": (p10.get("parent") or "") + " Days 1–10: lock the bet and the numbered lead. Days 11–20: one hospital pathway and one cost conversation. Days 21–30: MLR on the numbered claims.",
            "layout": "close",
            "bullets": p11.get("ask") or [
                "Approve the bet and the numbered scientific lead.",
                "MLR every line that carries a superscript.",
                "Name owners for the pathway, the cost conversation, and the one myth we can source.",
                "Park uncited brief lines as research, not as copy.",
            ],
            "callout": {"label": brand, "text": doctrine.get("scienceLead") or doctrine["bet"]},
        },
        *_reference_slides(references),
    ]


def _science_slides(lead: dict, records: list[dict], gaps: list[dict]) -> list[dict]:
    cites = lead.get("citations") or []
    primary = cites[0] if cites else {}
    people = _people_rows(records)
    compare = _compare_rows(records)
    lead_marks = mark(*cites)
    all_marks = mark(*records)
    slides = [
        {
            "id": "science-lead",
            "section": "Science",
            "kicker": "Campaign lead — sourced",
            "title": "The papers decide what we lead with",
            "subtitle": (
                f"{len(cites)} numbered papers, each with a job"
                if len(cites) > 1
                else (f"{mark(primary)} {primary.get('short')}" if primary else "No validated lead yet")
            ),
            "narrative": (lead.get("statement") or "No DOI/PMID-backed row matched this brief.") + (f" {lead_marks}" if lead_marks else ""),
            "layout": "insight",
            "callout": {
                "label": f"Primary source {mark(primary)}" if primary.get("ref") else "Primary source",
                "text": primary.get("citation") or "Retrieve a primary paper before lock.",
            },
            "bullets": [
                f"{mark(c)} {c['short']}: {c['claim']}"
                for c in cites[:4]
            ] or ["No validated citation — we will not invent one."],
            "refs": [c.get("ref") for c in cites if c.get("ref")],
        },
    ]
    if people:
        first = people[0]
        nnt = first.get("nnt")
        tag = mark({"ref": first.get("ref")}) if first.get("ref") else ""
        slides.append({
            "id": "science-meaning",
            "section": "Science",
            "kicker": "What the data means",
            "title": "In a clinic of 100, this is what the paper actually showed",
            "subtitle": f"{first.get('name')} · PMID {first.get('pmid') or '—'}",
            "narrative": (
                f"{first.get('claim')} {tag} "
                f"The HR is a statistic. The picture is {first.get('control')} events on the comparator "
                f"versus {first.get('treat')} on the intervention"
                + (f" — treat {nnt} to prevent 1 event." if nnt else ".")
            ),
            "layout": "infographic",
            "chart": {
                "kind": "people",
                "title": f"{first.get('name')}: {first.get('unit')}",
                "note": f"Published rates. {tag} PMID {first.get('pmid')}. Horizon: {first.get('horizon')}.",
                "unit": first.get("unit"),
                "data": people,
            },
            "callout": {
                "label": "Read this, not the HR",
                "text": (
                    f"{tag} NNT {nnt} over {first.get('horizon')}. "
                    "The campaign exists to capture these events, not to reprint the forest plot."
                ) if nnt else "These dots are the published event rates, not a planning model.",
            },
            "refs": [first.get("ref")] if first.get("ref") else [],
        })
    if compare:
        first = compare[0]
        tag = mark({"ref": first.get("ref")}) if first.get("ref") else ""
        slides.append({
            "id": "science-compare",
            "section": "Science",
            "kicker": "What the timing data means",
            "title": "Published rates from each numbered paper",
            "subtitle": f"{len(compare)} sourced comparisons",
            "narrative": " ".join(
                f"{row.get('name')}: {row.get('claim')}" for row in compare[:4]
            ) or (first.get("claim") or ""),
            "layout": "infographic",
            "chart": {
                "kind": "compare",
                "title": f"{first.get('name')}: {first.get('unit')}",
                "note": f"{tag} PMID {first.get('pmid')}. {first.get('horizon')}.",
                "unit": first.get("unit"),
                "data": compare,
            },
            "callout": {
                "label": "Each paper a different job",
                "text": "Placebo, head-to-head, and durability are not interchangeable reprints of one result.",
            },
            "refs": [row.get("ref") for row in compare if row.get("ref")],
        })
    slides.append({
        "id": "citation-register",
        "section": "Science",
        "kicker": "Evidence forefront — numbered",
        "title": "Every lead claim traces to a numbered paper",
        "narrative": (
            f"{len(records)} numbered papers {all_marks}. {len(gaps)} brief items still lack a DOI/PMID "
            "and cannot set direction. Full Vancouver list at the end of the deck."
        ),
        "layout": "split",
        "table": {
            "headers": ["Ref", "Source", "Stream", "Design / N", "Published finding", "Grade"],
            "rows": [
                [
                    mark(r),
                    r.get("short") or r.get("trial") or "",
                    r.get("stream") or "",
                    f"{r.get('design') or '—'} · n={r.get('n') or '—'}",
                    _finding(r),
                    r.get("grade") or "",
                ]
                for r in records[:8]
            ],
        },
        "bullets": [
            f"GAP · {g['stream']}: {g['item'][:110]}"
            for g in gaps[:4]
        ] or ["No uncited brief items."],
        "refs": [r.get("ref") for r in records if r.get("ref")],
    })
    return slides


def _science_execute_slide(records: list[dict], interventions: list[dict]) -> dict | None:
    rows = _spine_rows(records, interventions)
    if not rows:
        return None
    return {
        "id": "science-execute",
        "section": "Action",
        "kicker": "Science → execution",
        "title": "Each cited finding becomes one campaign move",
        "narrative": (
            "Science names the prize. The barrier names why the prize is lost. "
            "The intervention is how we take it. The KPI is how we know."
        ),
        "layout": "infographic",
        "chart": {
            "kind": "spine",
            "title": "Science to solution through strat execution",
            "note": "Only rows with a PMID/DOI. Uncited brief items cannot own a move.",
            "data": rows,
        },
    }


def _people_rows(records: list[dict]) -> list[dict]:
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


def _compare_rows(records: list[dict]) -> list[dict]:
    rows = []
    for r in records:
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


def _spine_rows(records: list[dict], interventions: list[dict]) -> list[dict]:
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
            "science": (r.get("claim_permitted") or "")[:160],
            "means": means,
            "barrier": r.get("spine_barrier") or "",
            "execute": r.get("spine_execute") or (iv["name"] if iv else ""),
            "measure": r.get("spine_measure") or (iv["kill"] if iv else ""),
            "pmid": r.get("pmid") or "",
            "ref": r.get("ref") or "",
            "move": iv["name"] if iv else (r.get("spine_execute") or ""),
        })
    return rows[:6]


def _forest_rows(records: list[dict]) -> list[dict]:
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
            "note": f"{mark(r)} PMID {r.get('pmid') or '—'} · doi:{r.get('doi') or '—'}",
        })
    return rows[:6]


def _stream_mix(records: list[dict], brief: ExtractedBrief) -> list[dict]:
    counts: dict[str, int] = {}
    for r in records:
        key = (r.get("stream") or "Other").split("/")[0].strip()
        counts[key] = counts.get(key, 0) + 1
    if not counts:
        return [
            {"name": "Uncited brief items", "value": max(1, len(brief.brand_evidence) + len(brief.guidelines))},
        ]
    return [{"name": k, "value": v} for k, v in counts.items()]


def _message_pillars(records: list[dict], doctrine: dict) -> list[str]:
    if hf_catalog_pack(records):
        by_direct = {r.get("directs"): r for r in records}
        start = by_direct.get("first-eligible-start")
        guide = by_direct.get("guideline-cover")
        outcome = by_direct.get("outcome-permission")
        pillars = []
        if start:
            pillars.append(
                f"Pillar 1 — Permission now {mark(start)} ({start['short']}): "
                f"{start['claim_permitted']}"
            )
        else:
            pillars.append("Pillar 1 — Permission now: first eligible encounter (citation pending).")
        if outcome and outcome is not start:
            pillars.append(
                f"Pillar 2 — Outcome permission {mark(outcome)} ({outcome['short']}): "
                f"{outcome['claim_permitted']}"
            )
        else:
            pillars.append("Pillar 2 — Practical confidence: monitoring and cost have a protocol, not a shrug.")
        if guide:
            pillars.append(
                f"Pillar 3 — Guideline cover {mark(guide)} ({guide['short']}): "
                f"{guide['claim_permitted']}"
            )
        else:
            pillars.append("Pillar 3 — Peer cover: someone like you already starts here.")
        return pillars
    out = []
    seen: set[str] = set()
    for r in paper_jobs(records):
        claim = (r.get("claim_permitted") or "").strip()
        key = re.sub(r"[^a-z0-9]+", " ", claim.lower())[:80]
        if not claim or key in seen:
            continue
        seen.add(key)
        label = r.get("roleLabel") or r.get("trial") or r.get("short") or f"Paper {len(out)+1}"
        out.append(f"Pillar {len(out)+1} — {label} {mark(r)}: {claim}")
        if len(out) >= 4:
            break
    return out or ["No extractable finding yet — do not lock a line."]


def _comb_title(doctrine: dict) -> str:
    return {
        "first-touch": "The behaviour is delayed initiation. The drivers are not mysterious.",
        "affordability-confidence": "The behaviour is not starting because of what the patient will pay.",
        "perception-reset": "The behaviour is withholding a start because of a wrong belief.",
        "conviction-cascade": "The behaviour is hesitation at the moment of the pen.",
    }.get(doctrine.get("id") or "", "The behaviour we have to change sits in this brief.")


def _comb_narrative(doctrine: dict) -> str:
    return {
        "first-touch": (
            "Capability is largely intact. Opportunity (cost, workflow) and reflective "
            "motivation (ritual, peer cover) are the load-bearing joints."
        ),
        "affordability-confidence": (
            "Capability is not the gap. Opportunity — cost, assistance, the conversation "
            "the doctor can survive — is the load-bearing joint."
        ),
        "perception-reset": (
            "A single durable myth is doing more work than a missing trial. Unlearning "
            "beats another awareness burst."
        ),
        "conviction-cascade": (
            "Scientific, peer, and practical conviction have to stack at the decision "
            "moment. Awareness without that stack does not prescribe."
        ),
    }.get(doctrine.get("id") or "", "Name the behaviour from the brief. Do not import a demo habit.")


def _interventions(brief: ExtractedBrief, doctrine: dict, ledger: dict | None = None) -> list[dict]:
    brand = brief.brand or "the brand"
    first_touch = [
        {
            "id": "first-touch",
            "name": "First-Touch Protocol",
            "promise": f"A hospital-to-clinic initiation bundle so {brand} is started at the first eligible encounter.",
            "lever": "Opportunity — workflow",
            "segment": "Hospital pathway owners + metro private",
            "effort": "H",
            "impact": 88,
            "feasibility": 62,
            "mlr": "Protocol language must match label and local code. No start-all implication.",
            "kill": "If discharge initiation rate is unchanged at week 8 in the pilot site.",
            "evidenceAnchor": _anchor(ledger, "first-eligible-start") or _anchor(ledger, "outcome-permission"),
        },
        {
            "id": "afford-kit",
            "name": "Affordability Confidence Kit",
            "promise": "A field-legal script, PAP mechanics, and HE one-pager that lets the HCP stay on the patient's side.",
            "lever": "Opportunity — cost",
            "segment": "Tier-2 consultants and high OOP caseloads",
            "effort": "M",
            "impact": 84,
            "feasibility": 70,
            "mlr": "No price promises. Assistance, not inducement.",
            "kill": "If PAP mention rate rises but initiation does not.",
            "evidenceAnchor": _anchor(ledger, "local-context") or _anchor(ledger, "outcome-permission"),
        },
        {
            "id": "myth-reset",
            "name": "Myth-Reset Asset",
            "promise": "One wrong belief, one local number, one peer voice. Unlearning, not a lecture.",
            "lever": "Motivation — ritual / Capability — knowledge",
            "segment": "Early-career + high-myth clusters",
            "effort": "M",
            "impact": 61,
            "feasibility": 78,
            "mlr": "Comparative safety claims need the source grade on-slide.",
            "kill": "If unaided myth prevalence does not drop in the next insight wave.",
            "evidenceAnchor": _anchor(ledger, "segment-confidence") or _anchor(ledger, "outcome-permission"),
        },
        {
            "id": "peer-cascade",
            "name": "Peer Cascade",
            "promise": "Metro KOLs author the protocol; tier-2 peers demonstrate it. Cover travels down, not out as a TV ad.",
            "lever": "Motivation — peer cover",
            "segment": "KOL metro → senior tier-2",
            "effort": "H",
            "impact": 76,
            "feasibility": 54,
            "mlr": "Fair balance. No paid-endorsement theatre.",
            "kill": "If cascade stops at the same five names by Q2.",
            "evidenceAnchor": _anchor(ledger, "guideline-cover"),
        },
        {
            "id": "habit-lock",
            "name": "Habit-Lock CRM",
            "promise": "The second prescription is designed, not hoped for. Prompts, feedback, peer norms.",
            "lever": "Motivation — automatic",
            "segment": "Trialists in Q1–Q2",
            "effort": "L",
            "impact": 58,
            "feasibility": 80,
            "mlr": "CRM content is promotional and goes through MLR.",
            "kill": "If repeat rate among trialists is flat vs control geographies.",
            "evidenceAnchor": _anchor(ledger, "outcome-permission"),
        },
    ]
    if doctrine.get("id") == "first-touch":
        return first_touch
    if doctrine.get("id") == "affordability-confidence":
        kit, rest = first_touch[1], [first_touch[0], *first_touch[2:]]
        kit = {
            **kit,
            "promise": (
                f"A field-legal script and assistance mechanic so the doctor can start {brand} "
                "without putting the patient in financial distress."
            ),
        }
        return [kit, *rest]
    if doctrine.get("id") == "perception-reset":
        myth, rest = first_touch[2], [x for x in first_touch if x["id"] != "myth-reset"]
        return [myth, *rest]
    decision = {
        "id": "first-touch",
        "name": "Decision-moment protocol",
        "promise": (
            f"A specialty-specific checklist so {brand} is considered with the papers in hand, "
            "not after the visit."
        ),
        "lever": "Opportunity — workflow",
        "segment": (brief.target_specialties[0] if brief.target_specialties else "Priority specialists"),
        "effort": "M",
        "impact": 80,
        "feasibility": 66,
        "mlr": "Protocol language must match label and local code.",
        "kill": "If first-start rate among engaged HCPs is unchanged at week 8.",
        "evidenceAnchor": _anchor(ledger, "outcome-permission"),
    }
    return [decision, first_touch[1], first_touch[2], first_touch[3], first_touch[4]]


def _anchor(ledger: dict | None, directs: str) -> str:
    if not ledger:
        return ""
    for r in ledger.get("records") or []:
        if r.get("directs") == directs:
            return f"{mark(r)} {r.get('short')} · PMID {r.get('pmid') or '—'} · doi:{r.get('doi') or '—'}"
    cites = (ledger.get("lead") or {}).get("citations") or []
    if cites:
        c = cites[0]
        return f"{mark(c)} {c.get('short')} · PMID {c.get('pmid') or '—'}"
    return ""


def _dashboard(brief: ExtractedBrief, doctrine: dict, ledger: dict | None = None, work: dict | None = None) -> dict:
    return {
        "kpis": [
            {"id": "rev", "label": "Quarterly revenue index", "value": 100, "target": 145, "unit": "Q0=100", "tone": "lag"},
            {"id": "init", "label": "First-eligible initiation", "value": 18, "target": 36, "unit": "%", "tone": "lead"},
            {"id": "conv", "label": "Conviction index", "value": 41, "target": 68, "unit": "0–100", "tone": "lead"},
            {"id": "myth", "label": "High-myth prevalence", "value": 40, "target": 22, "unit": "%", "tone": "lead"},
            {"id": "pap", "label": "Assistance offered (eligible)", "value": 12, "target": 45, "unit": "%", "tone": "lead"},
            {"id": "mlr", "label": "Assets cleared", "value": 0, "target": 12, "unit": "count", "tone": "gov"},
        ],
        "funnel": [
            {"name": "Aware", "value": 70},
            {"name": "Engaged", "value": 42},
            {"name": "Trialing", "value": 18},
            {"name": "Repeating", "value": 9},
            {"name": "Advocating", "value": 3},
        ],
        "revenue": [
            {"name": "Q0", "revenue": 100, "initiation": 100, "conviction": 100},
            {"name": "Q1", "revenue": 108, "initiation": 118, "conviction": 122},
            {"name": "Q2", "revenue": 118, "initiation": 136, "conviction": 138},
            {"name": "Q3", "revenue": 130, "initiation": 152, "conviction": 149},
            {"name": "Q4", "revenue": 145, "initiation": 168, "conviction": 160},
        ],
        "segments": [
            {"name": "Metro KOL", "impact": 72, "ready": 80, "cost": 32},
            {"name": "Metro private", "impact": 88, "ready": 64, "cost": 58},
            {"name": "Tier-2 consultant", "impact": 91, "ready": 48, "cost": 84},
            {"name": "Early-career", "impact": 60, "ready": 70, "cost": 50},
            {"name": "GP referrer", "impact": 40, "ready": 55, "cost": 78},
            {"name": "Hospital pathway", "impact": 86, "ready": 52, "cost": 44},
        ],
        "evidenceMix": _stream_mix((ledger or {}).get("records") or [], brief),
        "campaignLead": (ledger or {}).get("lead") or {},
        "citations": (ledger or {}).get("records") or [],
        "evidenceGaps": (ledger or {}).get("gaps") or [],
        "pubmed": (ledger or {}).get("pubmed") or [],
        "meaning": _people_rows((ledger or {}).get("records") or []),
        "compare": _compare_rows((ledger or {}).get("records") or []),
        "spine": _spine_rows((ledger or {}).get("records") or [], _interventions(brief, doctrine, ledger)),
        "references": (ledger or {}).get("references") or [],
        "openQuestions": (work or {}).get("openQuestions") or [],
        "howBuilt": (work or {}).get("howBuilt") or "",
        "alerts": [
            {"level": "watch", "text": "Funnel and index numbers are planning sketches. Audit the baseline before anyone treats them as a current rate."},
            {"level": "mlr", "text": "No promotional use until MLR clears each numbered claim against the local label."},
            {"level": "info", "text": f"{doctrine['name']}. Lead: {doctrine.get('scienceAnchor') or 'not yet sourced'}."},
        ],
        "governance": [
            {"cadence": "Weekly", "forum": "Field + medical huddle", "looksAt": "Protocol use, objections, myth language"},
            {"cadence": "Monthly", "forum": "Brand team", "looksAt": "Leading indicators vs kill-criteria"},
            {"cadence": "Quarterly", "forum": "Client CEO + medical director", "looksAt": "Revenue parent metric + course-correct"},
        ],
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
    return (row.get("claim_permitted") or row.get("endpoint") or "—")[:90]


def _reference_slides(references: list[dict]) -> list[dict]:
    if not references:
        return [{
            "id": "references",
            "section": "References",
            "kicker": "Numbered sources",
            "title": "References",
            "narrative": "This brief has not matched a PMID or DOI. We will not invent a reference list.",
            "layout": "insight",
            "bullets": ["Retrieve primary papers before anyone writes a claim."],
        }]
    slides = []
    chunk = 7
    total = (len(references) + chunk - 1) // chunk
    for i in range(0, len(references), chunk):
        part = references[i:i + chunk]
        page = i // chunk + 1
        slides.append({
            "id": "references" if page == 1 else f"references-{page}",
            "section": "References",
            "kicker": f"Vancouver  ·  {page} of {total}",
            "title": "References",
            "narrative": "Superscripts in the deck are these numbers. PubMed retrievals are listed and flagged; they are not lead claims.",
            "layout": "references",
            "table": {
                "headers": ["No.", "Citation"],
                "rows": [[str(r.get("n")), r.get("citation") or ""] for r in part],
            },
            "refs": [r.get("n") for r in part],
        })
    return slides
