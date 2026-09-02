"""Strategy Director — turn an extracted brief into a visual strategy pack.

This is the server-side twin of the TypeScript director. It produces the same
schema the web app renders: doctrine, slides, charts, interventions, dashboard.
"""

from __future__ import annotations

import re

from .cite import mark
from .deck import (
    compare_rows,
    people_rows,
    spine_rows,
    stream_mix,
)
from .extract import ExtractedBrief


def generate_pack(
    brief: ExtractedBrief,
    mode: str = "director",
    pubmed: bool = True,
    emit=None,
    llm=None,
) -> dict:
    """Think, then execute, through the director workflow. Returns a pack."""
    from .agent import run_director

    return run_director(brief, mode=mode, pubmed=pubmed, emit=emit, llm=llm)


def _doctrine_for(brief: ExtractedBrief, ledger: dict | None = None) -> dict:
    """Pick the angle from retrieved literature first, then the brief's described behaviour."""
    records = (ledger or {}).get("records") or []
    science = " ".join(
        f"{r.get('title') or ''} {r.get('abstract') or ''} {r.get('claim_permitted') or ''}"
        for r in records
    ).lower()
    blob = " ".join(
        [
            brief.business_goal,
            " ".join(brief.hcp_insights),
            " ".join(brief.access_and_cost),
            " ".join(brief.competitors),
            brief.indication,
            brief.notes or "",
        ]
    ).lower()
    insights = " ".join(brief.hcp_insights).lower()
    implication = ""
    if records:
        from .evidence import _strategy_implication

        implication = _strategy_implication(brief, records)
    paper = next((r.get("short") for r in records if r.get("short")), "")
    pmid = next((str(r.get("pmid")) for r in records if r.get("pmid")), "")
    indication = brief.therapy_area or _short_indication(brief.indication) or "this indication"
    brand = (brief.brand or "the brand").split(";")[0].strip()[:48]
    cite = f" — {paper} (PMID {pmid}) is on the register" if pmid else ""
    paper_start = records and any(
        w in science for w in ("initiat", "first-line", "in-hospital", "early", "guideline", "delay")
    )
    paper_outcome = records and any(
        w in science for w in ("surviv", "mortality", "overall survival", "progression", "hazard", "efficacy")
    )
    brief_wait = any(
        w in insights or w in (brief.business_goal or "").lower()
        for w in (
            "stabilis",
            "stabiliz",
            "second-line",
            "start late",
            "wait until",
            "first-eligible",
            "early initiation",
            "eligible visit",
        )
    )
    parity = any(
        w in insights or w in blob
        for w in (
            "similar",
            "same efficacy",
            "interchangeable",
            "clutter",
            "all the cough",
            "all brands",
            "another cough",
            "not the first recalled",
            "no differentiation",
            "low involvement",
        )
    )
    step_up = any(
        w in blob
        for w in (
            "step-up",
            "step up",
            "when dual",
            "first-line maintenance",
            "triple is what",
            "rescue or step-up",
        )
    )
    free_mix = any(w in blob for w in ("free-mix", "free mix", "mix it myself", "mix myself"))

    if step_up:
        enemy = (
            "The habit of saving triple until dual has already failed"
            if not free_mix
            else "Triple as rescue, plus the belief that free-mix is finer and cheaper"
        )
        return {
            "id": "first-line-not-rescue",
            "name": "First-line maintenance, not a late step-up",
            "thesis": (
                f"Doctors on this brief already know the class. They still use triple as step-up. "
                f"{implication or 'The literature and GOLD already describe first-line triple in exacerbators.'} "
                f"{brand} is not a better-molecule story — it is a first-line vs rescue story."
            ),
            "enemy": enemy,
            "bet": (
                f"Start {brand} as first-line maintenance in the labelled exacerbator, "
                "not after dual has failed, and not as a hospital-only rescue."
            ),
            "whyNovel": (
                "The brief's own dipstick says triple is what they move to when dual stops working. "
                "The campaign spends against that ritual, using retrieved papers, not a restated upload."
            ),
        }

    if parity:
        enemy = (brief.hcp_insights or ["Doctors treat every brand in the category as interchangeable."])[0]
        return {
            "id": "perception-reset",
            "name": f"Name {brand}, do not look like the clutter",
            "thesis": (
                f"The brief already said the category looks the same. "
                f"{implication or 'The job is a distinctive choice, not another hospital-start template.'} "
                f"{brand} has a recall and differentiation problem, not a first-eligible-visit problem."
            ),
            "enemy": enemy[:180],
            "bet": (
                f"Make {brand} the named choice — the expert they can defend — "
                "not a habit prescription in a cluttered set."
            ),
            "whyNovel": (
                "We do not import a heart-failure first-touch playbook. "
                "The spend is against interchangeability, using the brief's own belief lines."
            ),
        }

    if paper_start or (records and brief_wait):
        thesis = (
            f"The literature for {indication} already moved{cite}. "
            f"{implication or 'The scientific bet is first-eligible start, not a restated upload.'} "
            f"This is not a better-molecule story for {brand}."
        )
        return {
            "id": "first-touch",
            "name": "Start at the first eligible visit",
            "thesis": thesis,
            "enemy": "The habit of waiting until the patient is 'stable' in clinic",
            "bet": f"Start {brand} at the first eligible encounter — in hospital if that is when they are eligible.",
            "whyNovel": (
                "Most launch decks resell the label. This one spends against the wait, "
                "using papers we actually retrieved rather than a restated brief."
            ),
        }
    if not records and brief_wait:
        thesis = (
            f"The literature for {indication} is not yet on the register{cite}. "
            f"The doctors on this brief still wait. "
            f"This is not a better-molecule story for {brand}."
        )
        return {
            "id": "first-touch",
            "name": "Start at the first eligible visit",
            "thesis": thesis,
            "enemy": "The habit of waiting until the patient is 'stable' in clinic",
            "bet": f"Start {brand} at the first eligible encounter — in hospital if that is when they are eligible.",
            "whyNovel": (
                "Most launch decks resell the label. This one spends against the wait."
            ),
        }
    if paper_outcome:
        return {
            "id": "conviction-cascade",
            "name": "Conviction at the moment of the pen",
            "thesis": (
                f"The literature for {indication} is already on the register{cite}. "
                f"{implication or 'Conversion is the gap between those findings and the current start.'} "
                f"{brand} does not have an awareness problem."
            ),
            "enemy": "Fragile conviction at the point of prescribe",
            "bet": "Stack scientific, peer, and practical conviction in that order — then lock the habit.",
            "whyNovel": (
                "We refuse the awareness-then-consideration funnel. "
                "Prescribing is a habit with a few load-bearing joints. We work those."
            ),
        }
    if any(w in blob for w in ("cost", "afford", "oop", "out-of-pocket", "reimburs", "price")):
        return {
            "id": "affordability-confidence",
            "name": "A cost conversation the doctor can survive",
            "thesis": (
                f"Uptake of {brand} is gated by the doctor's fear of putting "
                "the patient in financial distress — not by disbelief in the science. "
                + (implication or "Literature is on the register; cost is the conversion problem.")
            ),
            "enemy": "Prescriber guilt about what the patient will pay",
            "bet": "Make the cost conversation clinically honest, not commercially awkward.",
            "whyNovel": (
                "We do not hide the price. We only say about money what a paper or a legal "
                "assistance mechanic can carry."
            ),
        }
    if any(w in blob for w in ("myth", "monitor", "safety", "renal", "perception", "belief")):
        return {
            "id": "perception-reset",
            "name": "Unlearn one wrong belief",
            "thesis": (
                "A durable false belief is blocking an evidence-aligned start. "
                + (implication or "The job is unlearning, not another awareness burst.")
            ),
            "enemy": "A high-prevalence clinical myth",
            "bet": "Replace the myth with one sourced number a peer can repeat.",
            "whyNovel": (
                "Awareness adds messages. A reset subtracts a wrong one."
            ),
        }
    return {
        "id": "conviction-cascade",
        "name": "Conviction at the moment of the pen",
        "thesis": (
            f"{brand} does not have an awareness problem. It has a "
            "conviction problem at the decision moment. "
            + (implication or "Stack scientific, peer, and practical conviction in that order.")
        ),
        "enemy": (brief.hcp_insights[0][:180] if brief.hcp_insights else "Fragile conviction at the point of prescribe"),
        "bet": "Stack scientific, peer, and practical conviction in that order — then lock the habit.",
        "whyNovel": (
            "We refuse the awareness-then-consideration funnel. "
            "Prescribing is a habit with a few load-bearing joints. We work those."
        ),
    }


def _short_indication(text: str) -> str:
    line = re.sub(r"\s+", " ", (text or "").strip())
    if not line:
        return ""
    return line[:120].rsplit(" ", 1)[0] if len(line) > 120 else line


def _bind_science(doctrine: dict, ledger: dict) -> None:
    lead = ledger.get("lead") or {}
    cites = lead.get("citations") or []
    if not cites:
        doctrine["scienceLead"] = "No validated citation yet — do not lock a scientific lead."
        return
    primary = cites[0]
    from .deck import _line
    from .evidence import _FINDING_HINT, _finding_from_abstract

    rec_claim = primary.get("claim") or ""
    finding = _finding_from_abstract(rec_claim, primary.get("short") or "")
    if not finding and _FINDING_HINT.search(rec_claim) and not rec_claim.lower().startswith("retrieved from pubmed"):
        finding = rec_claim
    if finding:
        doctrine["scienceLead"] = _line(finding, 160)
    doctrine["scienceAnchor"] = (
        f"{mark(primary)} {primary.get('short')} · PMID {primary.get('pmid') or '—'} · doi:{primary.get('doi') or '—'}"
    )



def _interventions(brief: ExtractedBrief, doctrine: dict, ledger: dict | None = None) -> list[dict]:
    brand = (brief.brand or "the brand").split(";")[0].strip()[:48]
    specialists = ", ".join((brief.target_specialties or [])[:3]) or "the named specialists"
    if doctrine.get("id") == "perception-reset":
        rival = (brief.competitors or ["the clutter"])[0]
        return [
            {
                "id": "myth-reset",
                "name": f"{brand} is not the category",
                "promise": (
                    f"Kill 'they all work the same' with one proof a peer can repeat for {brand}, "
                    f"not a hospital-start protocol copied from another brief."
                ),
                "lever": "Motivation — ritual / Capability — knowledge",
                "segment": specialists,
                "effort": "M",
                "impact": 88,
                "feasibility": 70,
                "mlr": "No superiority claim the papers did not state.",
                "kill": "If unaided 'all brands similar' does not drop in the next insight wave.",
                "evidenceAnchor": _anchor(ledger, "segment-confidence") or _anchor(ledger, "outcome-permission"),
            },
            {
                "id": "peer-cascade",
                "name": "First-recalled expert",
                "promise": f"Put {brand} in the first slot, not as a relationship refill after {rival}.",
                "lever": "Motivation — peer cover",
                "segment": specialists,
                "effort": "H",
                "impact": 84,
                "feasibility": 58,
                "mlr": "Fair balance. No paid-endorsement theatre.",
                "kill": "If first-mention stays behind the clutter brands at week 8.",
                "evidenceAnchor": _anchor(ledger, "guideline-cover") or _anchor(ledger, "outcome-permission"),
            },
            {
                "id": "first-touch",
                "name": "Patient-profile range",
                "promise": f"Make the range and the patient picture the reason to write {brand}, not a generic cough script.",
                "lever": "Opportunity — workflow",
                "segment": specialists,
                "effort": "M",
                "impact": 76,
                "feasibility": 72,
                "mlr": "Stay inside the approved indication and claims.",
                "kill": "If profiled patients are still written a rival by default.",
                "evidenceAnchor": _anchor(ledger, "local-context") or _anchor(ledger, "outcome-permission"),
            },
            {
                "id": "afford-kit",
                "name": "Visible proof in the clutter",
                "promise": "Match the rival's visibility with one distinctive proof, not more of the same reminder.",
                "lever": "Opportunity — salience",
                "segment": specialists,
                "effort": "M",
                "impact": 71,
                "feasibility": 66,
                "mlr": "No disparagement. Named rivals stay as the clutter, not as a smear.",
                "kill": "If share keeps slipping in the named states.",
                "evidenceAnchor": _anchor(ledger, "local-context"),
            },
            {
                "id": "habit-lock",
                "name": "Repeat among trialists",
                "promise": f"The second {brand} write is designed. Taste, relief, and trust have to show up in the next visit.",
                "lever": "Motivation — automatic",
                "segment": "Trialists in Q1–Q2",
                "effort": "L",
                "impact": 64,
                "feasibility": 80,
                "mlr": "CRM content is promotional and goes through MLR.",
                "kill": "If repeat among trialists is flat vs control geographies.",
                "evidenceAnchor": _anchor(ledger, "outcome-permission"),
            },
        ]
    if doctrine.get("id") == "first-line-not-rescue":
        first = {
            "id": "first-touch",
            "name": "First-line maintenance protocol",
            "promise": (
                f"A labelled-exacerbator start so {brand} is first-line maintenance, "
                "not the thing they add after dual has already failed."
            ),
            "lever": "Motivation — old ritual",
            "segment": "Pulmonologists + consultant physicians, metro and tier-1",
            "effort": "H",
            "impact": 88,
            "feasibility": 62,
            "mlr": "No superiority vs free-mix. Stay inside the approved indication.",
            "kill": "If 'triple after dual' language is unchanged at week 8 in the pilot.",
            "evidenceAnchor": _anchor(ledger, "guideline-cover") or _anchor(ledger, "outcome-permission"),
        }
        return [
            first,
            {
                "id": "afford-kit",
                "name": "Free-mix cost script",
                "promise": (
                    f"A field-legal comparison of {brand} versus free-mix cost that stays "
                    "inside MLR: no superiority, no price promise."
                ),
                "lever": "Opportunity — cost",
                "segment": "Tier-2 consultants and high OOP caseloads",
                "effort": "M",
                "impact": 84,
                "feasibility": 70,
                "mlr": "No superiority vs free-mix. Assistance, not inducement.",
                "kill": "If cost is still the first objection and first-line starts do not move.",
                "evidenceAnchor": _anchor(ledger, "local-context") or _anchor(ledger, "outcome-permission"),
            },
            {
                "id": "myth-reset",
                "name": "One-device unlearning",
                "promise": "Kill 'I mix it myself for finer control' with device and adherence facts, not a lecture.",
                "lever": "Motivation — ritual / Capability — knowledge",
                "segment": "Consultants who still free-mix at the point of care",
                "effort": "M",
                "impact": 61,
                "feasibility": 78,
                "mlr": "No comparative efficacy claim against free-mix.",
                "kill": "If unaided free-mix preference does not drop in the next insight wave.",
                "evidenceAnchor": _anchor(ledger, "segment-confidence") or _anchor(ledger, "outcome-permission"),
            },
            {
                "id": "peer-cascade",
                "name": "GOLD first-line cascade",
                "promise": "Metro KOLs author the first-line protocol; tier-2 peers demonstrate it. Cover travels down.",
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
                "name": "Hospital-to-home lock",
                "promise": "Nebulised triple continues at home. The second fill is designed, not hoped for.",
                "lever": "Motivation — automatic",
                "segment": "Discharge and first follow-up",
                "effort": "L",
                "impact": 58,
                "feasibility": 80,
                "mlr": "CRM content is promotional and goes through MLR.",
                "kill": "If home continuation among trialists is flat vs control geographies.",
                "evidenceAnchor": _anchor(ledger, "outcome-permission"),
            },
        ]
    if doctrine.get("id") != "first-touch":
        return [
            {
                "id": "decision",
                "name": f"Write {brand} at the decision",
                "promise": (
                    f"Stack scientific, peer, and practical cover so {brand} is written "
                    "at the decision — not a hospital-start protocol copied from another brief."
                ),
                "lever": "Motivation — decision",
                "segment": specialists,
                "effort": "H",
                "impact": 88,
                "feasibility": 62,
                "mlr": "No start-all implication. Stay inside the papers and the label.",
                "kill": "If unaided preference does not move in the next insight wave.",
                "evidenceAnchor": _anchor(ledger, "outcome-permission") or _anchor(ledger, "local-context"),
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
    first = {
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
    }
    return [
        first,
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


def _dashboard(
    brief: ExtractedBrief,
    doctrine: dict,
    ledger: dict | None = None,
    work: dict | None = None,
    moves: list[dict] | None = None,
) -> dict:
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
        "evidenceMix": stream_mix((ledger or {}).get("records") or [], brief),
        "campaignLead": (ledger or {}).get("lead") or {},
        "citations": (ledger or {}).get("records") or [],
        "evidenceGaps": (ledger or {}).get("gaps") or [],
        "pubmed": (ledger or {}).get("pubmed") or [],
        "review": (ledger or {}).get("review") or {},
        "searchTerms": (ledger or {}).get("searchTerms") or [],
        "meaning": people_rows((ledger or {}).get("records") or []),
        "compare": compare_rows((ledger or {}).get("records") or []),
        "spine": spine_rows(
            (ledger or {}).get("records") or [],
            moves or _interventions(brief, doctrine, ledger),
        ),
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


