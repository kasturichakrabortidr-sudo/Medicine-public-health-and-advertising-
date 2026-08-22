"""Strategy Director — turn an extracted brief into a visual strategy pack.

This is the server-side twin of the TypeScript director. It produces the same
schema the web app renders: doctrine, slides, charts, interventions, dashboard.
"""

from __future__ import annotations

import re
from datetime import date

from .cite import attach_references, mark
from .deck_craft import build_deck, story_map
from .deck_skills import SKILL_IDS
from .deck_visuals import compare_rows, people_rows, spine_rows
from .evidence import resolve_evidence
from .extract import ExtractedBrief
from .molecule import science_name
from .paper_read import brief_has_delay, hf_catalog_pack, paper_jobs
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
    molecule = science_name(brief)
    ledger = resolve_evidence(brief, pubmed=pubmed)
    attach_references(ledger)
    doctrine = _doctrine_for(brief, ledger)
    _bind_science(doctrine, ledger)
    work = build_workfile(brief, doctrine, ledger)
    interventions = _interventions(brief, doctrine, ledger)
    slides = build_deck(brief, doctrine, ledger, work, interventions)

    return {
        "meta": {
            "brand": brand,
            "product": product,
            "molecule": molecule,
            "therapyArea": ta,
            "market": market,
            "generatedAt": date.today().isoformat(),
            "mode": mode,
            "demo": mode == "demo",
            "doctrine": doctrine["name"],
            "angleId": doctrine["id"],
            "campaignLead": (ledger.get("lead") or {}).get("directs"),
            "source": ", ".join(brief.source_files) or ("pasted brief" if brief.raw_text else ""),
            "deckSkill": "strata-deck",
            "deckSkills": list(SKILL_IDS),
            "storyMap": story_map(slides),
        },
        "brief": brief.to_dict(),
        "doctrine": doctrine,
        "evidence": ledger,
        "workfile": work,
        "references": ledger.get("references") or [],
        "slides": slides,
        "interventions": interventions,
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
            "No citable paper retrieved yet — we search PubMed from the INN and therapy area, not the brand. "
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
        "meaning": people_rows((ledger or {}).get("records") or []),
        "compare": compare_rows((ledger or {}).get("records") or []),
        "spine": spine_rows((ledger or {}).get("records") or [], _interventions(brief, doctrine, ledger)),
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

