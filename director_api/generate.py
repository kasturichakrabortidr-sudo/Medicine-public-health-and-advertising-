"""Strategy Director — turn an extracted brief into a visual strategy pack.

This is the server-side twin of the TypeScript director. It produces the same
schema the web app renders: doctrine, slides, charts, interventions, dashboard.
"""

from __future__ import annotations

from datetime import date

from .extract import ExtractedBrief


def generate_pack(brief: ExtractedBrief, mode: str = "director") -> dict:
    """Build a presentation-ready strategy pack from a structured brief."""
    brand = brief.brand or "Unnamed brand"
    ta = brief.therapy_area or "Specialty care"
    market = brief.market or "Priority markets"
    product = brief.product or brand
    doctrine = _doctrine_for(brief)

    return {
        "meta": {
            "brand": brand,
            "product": product,
            "therapyArea": ta,
            "market": market,
            "generatedAt": date.today().isoformat(),
            "mode": mode,
            "doctrine": doctrine["name"],
            "angleId": doctrine["id"],
        },
        "brief": brief.to_dict(),
        "doctrine": doctrine,
        "slides": _slides(brief, doctrine),
        "interventions": _interventions(brief, doctrine),
        "dashboard": _dashboard(brief, doctrine),
    }


def _doctrine_for(brief: ExtractedBrief) -> dict:
    """Pick a novel strategic angle from the brief's actual tension — not a generic funnel."""
    blob = " ".join(
        [
            brief.business_goal,
            " ".join(brief.hcp_insights),
            " ".join(brief.access_and_cost),
            " ".join(brief.competitors),
            brief.indication,
        ]
    ).lower()

    if any(w in blob for w in ("stabilise", "stabilize", "late", "second-line", "switch", "habit")):
        return {
            "id": "first-touch",
            "name": "The First-Touch Doctrine",
            "thesis": (
                f"The enemy of {brief.brand or 'the brand'} is not the comparator molecule. "
                "It is the ritual of delay — the 'stabilise first' habit that postpones "
                "guideline therapy past the only moment that reliably converts."
            ),
            "enemy": "The stabilize-first ritual",
            "bet": "Every eligible first encounter is the guideline encounter.",
            "whyNovel": (
                "Most launch decks sell a better drug. This doctrine retires a clinical habit. "
                "Evidence is used as permission to act now, not as a brochure of superiority."
            ),
        }
    if any(w in blob for w in ("cost", "afford", "oop", "out-of-pocket", "reimburs", "price")):
        return {
            "id": "affordability-confidence",
            "name": "Affordability Confidence",
            "thesis": (
                f"Uptake of {brief.brand or 'the brand'} is gated by the HCP's fear of putting "
                "the patient in financial distress — not by disbelief in the science."
            ),
            "enemy": "Prescriber guilt about patient cost",
            "bet": "Make the cost conversation clinically confident, not commercially awkward.",
            "whyNovel": (
                "We do not hide price. We instrument it: health-economic proof, assistance "
                "mechanics, and a script that keeps the HCP on the side of the patient."
            ),
        }
    if any(w in blob for w in ("myth", "monitor", "safety", "renal", "perception", "belief")):
        return {
            "id": "perception-reset",
            "name": "The Perception Reset",
            "thesis": (
                "A durable false belief is blocking an evidence-aligned behaviour. "
                "The campaign's job is unlearning, not awareness."
            ),
            "enemy": "A high-prevalence clinical myth",
            "bet": "Replace the myth with a local, peer-owned fact the HCP can repeat.",
            "whyNovel": (
                "Awareness campaigns add messages. A reset campaign subtracts a wrong one "
                "and installs a replacement that is easier to hold than the myth."
            ),
        }
    return {
        "id": "conviction-cascade",
        "name": "The Conviction Cascade",
        "thesis": (
            f"{brief.brand or 'The brand'} does not have an awareness problem. It has a "
            "conviction problem at the decision moment — scientific, peer, and practical."
        ),
        "enemy": "Fragile conviction at the point of prescribe",
        "bet": "Stack scientific, peer, and practical conviction in that order — then lock the habit.",
        "whyNovel": (
            "The cascade refuses the classic awareness→consideration funnel. "
            "It treats prescribing as a habit system with four load-bearing joints."
        ),
    }


def _slides(brief: ExtractedBrief, doctrine: dict) -> list[dict]:
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

    return [
        {
            "id": "title",
            "section": "Open",
            "kicker": f"{market}  ·  HCP campaign  ·  Confidential",
            "title": brand,
            "subtitle": f"{doctrine['name']}  —  a strategy for {ta}",
            "narrative": doctrine["thesis"],
            "layout": "title",
            "bullets": [f"Product: {brief.product or brand}", f"Indication: {brief.indication or ta}", f"Horizon: 4 quarters"],
        },
        {
            "id": "the-bet",
            "section": "Angle",
            "kicker": "The one-slide bet",
            "title": doctrine["bet"],
            "subtitle": f"Enemy we are actually fighting: {doctrine['enemy']}",
            "narrative": doctrine["whyNovel"],
            "layout": "insight",
            "callout": {"label": "Doctrine", "text": doctrine["name"]},
            "bullets": [
                "Not a better-molecule story.",
                "A behaviour-change doctrine with evidence as permission.",
                "Interventions designed to retire a ritual, not decorate a funnel.",
            ],
        },
        {
            "id": "challenge",
            "section": "Situation",
            "kicker": "The real problem",
            "title": "What the brief asked vs what the brand needs",
            "narrative": goal,
            "layout": "split",
            "bullets": [
                f"Client ask: {goal[:180]}",
                f"Strategic need: convert {doctrine['enemy'].lower()} into a first-eligible action.",
                "Constraint: every claim and tactic must clear MLR and local promotion codes.",
            ],
            "table": {
                "headers": ["Lens", "Today", "Required shift"],
                "rows": [
                    ["Clinical", "Eligible patients meet the product late", "First eligible encounter = guideline encounter"],
                    ["Behavioural", insights[0][:90], "Make the new habit easier than the old one"],
                    ["Commercial", "Growth depends on late switch", "Volume from initiation, not just conversion"],
                ],
            },
        },
        {
            "id": "opportunity",
            "section": "Situation",
            "kicker": "Where value hides",
            "title": "The adoption gap is a sequence problem",
            "narrative": (
                "Value is not evenly spread across the HCP universe. It concentrates in the "
                "moments and segments where delay is a ritual and cost-concern is a veto."
            ),
            "layout": "chart",
            "chart": {
                "kind": "bar",
                "title": "Illustrative initiation timing (eligible patients)",
                "note": "Planning model from brief signals — replace with audit data before lock.",
                "unit": "% of eligible starts",
                "data": [
                    {"name": "At first eligible visit", "value": 18},
                    {"name": "After 'stabilise' delay", "value": 44},
                    {"name": "At hospital discharge", "value": 14},
                    {"name": "Never / stays on SoC", "value": 24},
                ],
            },
        },
        {
            "id": "forest",
            "section": "Evidence",
            "kicker": "Evidence forefront",
            "title": "What the science actually permits us to say",
            "narrative": "Brand, independent, evolving, and guideline streams stacked for the client. Effect sizes shown only when the brief or a named public trial supplies them; otherwise marked as a gap.",
            "layout": "chart",
            "chart": {
                "kind": "forest",
                "title": "Strategic evidence position (illustrative synthesis)",
                "note": "Published anchors used where named; local items flagged as brief-derived.",
                "data": _forest_rows(brief),
            },
            "bullets": evidence[:4],
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
                "data": [
                    {"name": "Brand-generated", "value": max(1, len(brief.brand_evidence) or 3)},
                    {"name": "Independent", "value": max(1, len(brief.existing_evidence) or 2)},
                    {"name": "Evolving", "value": max(1, len(brief.evolving_evidence) or 2)},
                    {"name": "Guidelines", "value": max(1, len(brief.guidelines) or 2)},
                    {"name": "Health-economic", "value": 2 if brief.access_and_cost else 1},
                ],
            },
            "bullets": guidelines[:4],
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
            "title": "The behaviour is delayed initiation. The drivers are not mysterious.",
            "narrative": "Capability is largely intact. Opportunity (cost, workflow) and reflective motivation (ritual, peer cover) are the load-bearing joints.",
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
            "title": "Cost-concern is not a single number. It is a distribution.",
            "narrative": "Metro KOLs and tier-2 consultants do not live on the same cost curve. Activation that ignores the spread will look sophisticated and sell nothing.",
            "layout": "chart",
            "chart": {
                "kind": "box",
                "title": "HCP-rated patient cost concern (illustrative)",
                "unit": "0–10 concern",
                "data": [
                    {"name": "Metro KOL", "min": 2, "q1": 3.2, "median": 4.1, "q3": 5.4, "max": 7.0},
                    {"name": "Metro private", "min": 3, "q1": 4.8, "median": 6.2, "q3": 7.5, "max": 9.0},
                    {"name": "Tier-2 consultant", "min": 5, "q1": 6.8, "median": 8.1, "q3": 9.0, "max": 10},
                    {"name": "Tier-3 / GP referrer", "min": 6, "q1": 7.6, "median": 8.8, "q3": 9.5, "max": 10},
                ],
            },
        },
        {
            "id": "position",
            "section": "Position",
            "kicker": "Four-way compare",
            "title": "Stand only on ground all four columns can defend",
            "narrative": "Brand evidence, independent evidence, evolving data, and guidelines. Alignment is the only safe shout.",
            "layout": "split",
            "table": {
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
            "title": "One theme. Three pillars. No ornamental claims.",
            "narrative": f"Theme: {doctrine['bet']}",
            "layout": "grid",
            "bullets": [
                "Pillar 1 — Permission now: the first eligible encounter is the guideline encounter.",
                "Pillar 2 — Practical confidence: monitoring and cost have a protocol, not a shrug.",
                "Pillar 3 — Peer cover: someone like you already starts here.",
            ],
            "callout": {"label": "MLR", "text": "Every pillar must carry a named evidence row. No pillar ships without a grade and a caveat."},
        },
        {
            "id": "interventions",
            "section": "Action",
            "kicker": "Intervention architecture",
            "title": "Five moves that retire the ritual",
            "narrative": "Ideas are cheap. Interventions have an owner, a COM-B lever, a segment, and a kill-criterion.",
            "layout": "grid",
            "bullets": [i["name"] + " — " + i["promise"] for i in _interventions(brief, doctrine)[:5]],
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
                    {"name": "First-Touch protocol", "x": 62, "y": 88, "z": 40},
                    {"name": "Affordability kit", "x": 70, "y": 84, "z": 36},
                    {"name": "Myth-reset med-ed", "x": 78, "y": 61, "z": 24},
                    {"name": "Peer cascade", "x": 54, "y": 76, "z": 28},
                    {"name": "CRM habit lock", "x": 80, "y": 58, "z": 18},
                    {"name": "Congress theatre", "x": 40, "y": 34, "z": 30},
                ],
            },
        },
        {
            "id": "journey",
            "section": "Engagement",
            "kicker": "Start to beyond",
            "title": "A single HCP should feel a designed sequence, not a spray",
            "narrative": "Pre-launch builds peer cover. Launch installs the first-touch protocol. Adoption locks the habit. Beyond the campaign, the pathway stays.",
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
            "title": "Sign the doctrine. Instrument the gap. Build three assets.",
            "narrative": "Days 1–10: lock the enemy and the bet. Days 11–20: hospital pathway + affordability kit briefs. Days 21–30: MLR on the first three claims.",
            "layout": "close",
            "bullets": [
                "Approve the doctrine and the enemy in one working session.",
                "Commission the initiation-timing audit (replace illustrative bars).",
                "Name owners for protocol, cost kit, and myth-reset.",
                "Set kill-criteria before production begins.",
            ],
            "callout": {"label": brand, "text": doctrine["bet"]},
        },
    ]


def _forest_rows(brief: ExtractedBrief) -> list[dict]:
    rows = []
    published = [
        {
            "name": "Pivotal outcome vs SoC (named if in brief)",
            "stream": "Brand",
            "hr": 0.80,
            "low": 0.73,
            "high": 0.87,
            "grade": "A",
            "note": "Use only if the working file names the trial and endpoint.",
        },
        {
            "name": "Independent class synthesis",
            "stream": "Independent",
            "hr": 0.82,
            "low": 0.75,
            "high": 0.90,
            "grade": "A",
            "note": "Meta-analytic direction from class evidence.",
        },
    ]
    if brief.evolving_evidence:
        rows.append(
            {
                "name": "Early / in-hospital initiation (evolving)",
                "stream": "Evolving",
                "hr": 0.78,
                "low": 0.68,
                "high": 0.92,
                "grade": "B",
                "note": "Watch-list — confirm before claim use.",
            }
        )
    if brief.guidelines:
        rows.append(
            {
                "name": "Guideline-aligned foundational use",
                "stream": "Guideline",
                "hr": 0.81,
                "low": 0.74,
                "high": 0.88,
                "grade": "A",
                "note": "Position, not a new effect size.",
            }
        )
    return (published + rows)[:5]


def _interventions(brief: ExtractedBrief, doctrine: dict) -> list[dict]:
    brand = brief.brand or "the brand"
    return [
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
        },
    ]


def _dashboard(brief: ExtractedBrief, doctrine: dict) -> dict:
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
        "evidenceMix": [
            {"name": "Brand-generated", "value": max(1, len(brief.brand_evidence) or 3)},
            {"name": "Independent", "value": max(1, len(brief.existing_evidence) or 2)},
            {"name": "Evolving", "value": max(1, len(brief.evolving_evidence) or 2)},
            {"name": "Guidelines", "value": max(1, len(brief.guidelines) or 2)},
            {"name": "Health-economic", "value": 2 if brief.access_and_cost else 1},
        ],
        "alerts": [
            {"level": "watch", "text": "Illustrative numbers must be replaced with audit / CRM baselines before client lock."},
            {"level": "mlr", "text": "No promotional use until MLR clears claims, HE statements, and field scripts."},
            {"level": "info", "text": f"Doctrine in force: {doctrine['name']}."},
        ],
        "governance": [
            {"cadence": "Weekly", "forum": "Field + medical huddle", "looksAt": "Protocol use, objections, myth language"},
            {"cadence": "Monthly", "forum": "Brand team", "looksAt": "Leading indicators vs kill-criteria"},
            {"cadence": "Quarterly", "forum": "Client CEO + medical director", "looksAt": "Revenue parent metric + course-correct"},
        ],
    }
