"""Eleven-phase working file — the strategy is written from this, not from a slide template.

Each phase quotes the brief, names what is sourced, and names what is still missing.
Nothing here invents a trial or an effect size.
"""

from __future__ import annotations

import re
from typing import Any

from .cite import mark
from .extract import ExtractedBrief

PHASE_TITLES = [
    ("01", "What the brief is really asking"),
    ("02", "How we will judge the science"),
    ("03", "Evidence forefront"),
    ("04", "What the doctors believe vs what the papers show"),
    ("05", "The behaviour we have to change"),
    ("06", "Where we are allowed to stand"),
    ("07", "What we will say — and what we will not"),
    ("08", "How we will spend time with these doctors"),
    ("09", "Who we activate first"),
    ("10", "How we will know"),
    ("11", "The page we would take to sign-off"),
]


def build_workfile(brief: ExtractedBrief, doctrine: dict, ledger: dict) -> dict[str, Any]:
    records = ledger.get("records") or []
    gaps = ledger.get("gaps") or []
    lead = ledger.get("lead") or {}
    refs = ledger.get("references") or []
    by_direct = {r.get("directs"): r for r in records}
    phases = [
        _p01(brief, doctrine, records, gaps),
        _p02(brief, records),
        _p03(brief, records, gaps, lead),
        _p04(brief, records, gaps),
        _p05(brief, records, doctrine),
        _p06(brief, records, by_direct),
        _p07(brief, records, doctrine, lead),
        _p08(brief, doctrine),
        _p09(brief, doctrine),
        _p10(brief, doctrine),
        _p11(brief, doctrine, lead, records, gaps),
    ]
    return {
        "howBuilt": (
            f"We started with the brief for {brief.brand or 'this brand'}. "
            "The brief is not expected to contain paper links. "
            f"We searched PubMed for {brief.product or brief.therapy_area or 'this product/indication'} "
            "and numbered every hit with a PMID or DOI. "
            f"{len(records)} paper{'s' if len(records) != 1 else ''} have a number. "
            f"{len(gaps)} line{'s' if len(gaps) != 1 else ''} from the brief still have no PMID or DOI. "
            "Those lines cannot set a claim. Effect sizes are taken only from curated papers, never invented. "
            "The slides are this file, presented."
        ),
        "phases": phases,
        "references": refs,
        "openQuestions": _open_questions(brief, gaps, records),
        "cannotClaim": [c for c in (lead.get("doNotClaim") or []) if c],
        "refCount": len(refs),
        "validatedCount": len(records),
        "gapCount": len(gaps),
    }


def _phase(pid: str, how: str, **body) -> dict[str, Any]:
    title = next(t for i, t in PHASE_TITLES if i == pid)
    return {"id": pid, "title": title, "howBuilt": how, **body}


def _p01(brief, doctrine, records, gaps) -> dict:
    asked = (brief.business_goal or "").strip() or "The brief does not state a business goal."
    insights = brief.hcp_insights or []
    cost = brief.access_and_cost or []
    delay = next((i for i in insights if _looks_like_delay(i)), insights[0] if insights else "")
    money = next((c for c in cost if _looks_like_cost(c)), cost[0] if cost else "")
    need = (
        f"What {brief.brand or 'the brand'} needs is not another reminder that the science is positive. "
        + (f"The doctors already told us: {delay} " if delay else "")
        + (f"And then: {money} " if money else "")
        + f"So the work is {doctrine.get('bet') or 'to change the decision at the eligible moment'}."
    )
    questions = _first_questions(brief, records, gaps)
    assumptions = []
    for raw, why, test in [
        (delay, "If this is not actually the delay, we will spend a year fighting a habit that is not there.",
         "Field capture of first-eligible starts vs 'stabilise first' language in the next 30 calls."),
        (money, "If cost is a veto, a science-only campaign will look clever and sell nothing.",
         "Assistance offered vs initiation in high OOP caseloads."),
        ("Local RWE is required before KOLs will advocate." if any("rwe" in i.lower() or "local" in i.lower() for i in insights) else "",
         "If the KOLs will not move without a DOI we do not have, we cannot put them on a poster.",
         "Retrieve the Indian RWE paper or drop the KOL-advocacy line."),
    ]:
        if raw:
            assumptions.append([_short(raw, 110), why, test])
    known = [
        f"{mark(r)} {r.get('short')}: {r.get('claim_permitted')}"
        for r in records[:6]
    ] or ["No numbered paper on the register yet. PubMed is searched from the product and therapy area; the brief does not need to list papers."]
    unknown = [
        f"{g['stream']}: {g['item']}" for g in gaps[:6]
    ] or ["No uncited brief lines."]
    unknown.append("We do not have an audited first-eligible start rate for this market. Any % on a slide is a planning sketch until then.")
    hypotheses = [
        f"H1. Delay, not disbelief, is the conversion problem — from the insight “{_short(delay or 'not supplied', 90)}”.",
        f"H2. Cost is a veto in tier-2, not a footnote — from “{_short(money or 'not supplied', 90)}”.",
        "H3. In-hospital first-eligible start is the highest-leverage behaviour change, because that is the window the initiation papers actually studied."
        if any(r.get("directs") == "first-eligible-start" for r in records)
        else "H3. We cannot name the initiation window until a timing paper is on the register.",
    ]
    return _phase(
        "01",
        "We separated what the client typed as a goal from what the insight and access lines actually describe. The numbered papers from the register sit under Known. Uncited brief lines sit under Unknown. We did not fill Unknown with a guess.",
        restatedAsk=asked,
        restatedNeed=need.strip(),
        questions=questions,
        assumptions={"headers": ["Assumption in the brief", "If we are wrong", "How we will test it"], "rows": assumptions},
        known=known,
        unknown=unknown,
        hypotheses=hypotheses,
    )


def _p02(brief, records) -> dict:
    pop = brief.indication or brief.therapy_area or "the indicated population"
    product = brief.product or brief.brand or "the product"
    pico = [
        ["Population", pop, "Taken from the brief. We will not widen it."],
        ["Intervention", f"{product} at the first eligible encounter", "Eligible as labelled — not 'all comers'."],
        ["Comparator", "Habitual ACEI/ARB or SoC delay" if records else "Standard of care named in the brief", "The comparator is the current habit, not a straw man."],
        ["Outcomes we may use", _outcome_line(records), "Only endpoints published in numbered papers."],
        ["Setting", brief.market or "markets named in the brief", "Local label and code still govern."],
    ]
    return _phase(
        "02",
        "PICO is the contract for every later claim. If a line in the brief is not in this table, it is not yet a claim.",
        pico={"headers": ["PICO", "Working definition", "Rule"], "rows": pico},
        hierarchy=[
            "A — RCT or society guideline with PMID/DOI on the register",
            "B — pre-specified subgroup, open-label timing, or well-described registry",
            "C — uncited brief item, local RWE without a paper, ongoing study — research task, not a lead",
        ],
        include="Peer-reviewed papers and society guidelines with a PMID or DOI. HFrEF/indication must match the brief.",
        exclude="Invented HRs, congress rumours, competitor claims without a source, and papers that do not match this product/indication.",
    )


def _p03(brief, records, gaps, lead) -> dict:
    rows = []
    for r in records:
        effect = _effect(r)
        rows.append([
            mark(r),
            r.get("short") or "",
            r.get("stream") or "",
            f"{r.get('design') or '—'} · n={r.get('n') or '—'}",
            effect,
            r.get("grade") or "",
            (r.get("claim_permitted") or "")[:140],
            (r.get("caveat") or "")[:110],
        ])
    assets = [
        f"{mark(c)} {c.get('short')}: {c.get('claim')}"
        for c in (lead.get("citations") or [])[:5]
    ] or ["No validated asset yet."]
    gap_rows = [
        [g["stream"], g["item"], g.get("needed") or "Retrieve the primary paper."]
        for g in gaps[:8]
    ]
    return _phase(
        "03",
        "Every row is a paper we can put a number on. We searched PubMed from the product and therapy area; the brief is not the source of the links. Brief lines without a number stay in the gap table. We did not give them an effect size.",
        forefront={
            "headers": ["Ref", "Source", "Stream", "Design / N", "Published finding", "Grade", "What we may say", "Caveat"],
            "rows": rows,
        },
        assets=assets,
        gaps={"headers": ["Stream", "From the brief", "Needed before it can lead"], "rows": gap_rows or [["—", "No uncited brief items.", "—"]]},
        leadStatement=lead.get("statement") or "No scientific lead yet.",
    )


def _p04(brief, records, gaps) -> dict:
    insights = brief.hcp_insights or ["No HCP insight was supplied. We will not invent an advisory board."]
    concord, discord, silent = [], [], []
    start = next((r for r in records if r.get("directs") == "first-eligible-start"), None)
    outcome = next((r for r in records if r.get("directs") == "outcome-permission"), None)
    guide = next((r for r in records if r.get("directs") == "guideline-cover"), None)
    for ins in insights:
        low = ins.lower()
        if _looks_like_delay(ins) and start:
            discord.append([
                _short(ins, 120),
                f"The initiation papers do not require a clinic wait. {mark(start)} {start.get('short')}.",
                "Habit / handover theatre",
                "This is the campaign. Not a reminder of efficacy.",
            ])
        elif any(w in low for w in ("agree", "principle", "accept")) and (outcome or guide):
            src = outcome or guide
            concord.append([
                _short(ins, 120),
                f"Belief already matches {mark(src)} {src.get('short')}.",
                "Do not spend awareness money here. Use these doctors as cover.",
            ])
        elif any(w in low for w in ("cost", "price", "afford", "oop")):
            silent.append([
                _short(ins, 120),
                "The register has no health-economic paper with a PMID. Cost is an access problem sitting on top of the science.",
            ])
        elif any(w in low for w in ("renal", "monitor", "myth", "safety")):
            discord.append([
                _short(ins, 120),
                "We do not have a renal-burden RCT on the register. Treat this as a belief to measure, not a claim to rebut with a made-up number.",
                "Old teaching / monitoring fear",
                "Myth-reset only with a sourced number. If we cannot source it, we do not run the line.",
            ])
        elif any(w in low for w in ("rwe", "local", "indian", "india")):
            silent.append([
                _short(ins, 120),
                next((f"GAP: {g['item']}" for g in gaps if "rwe" in g["item"].lower() or "local" in g["item"].lower() or "indian" in g["item"].lower()),
                     "Local RWE is in the brief and not on the register."),
            ])
        else:
            silent.append([_short(ins, 120), "Logged. Not yet mapped to a numbered paper."])
    return _phase(
        "04",
        "We mapped each insight line onto the numbered papers. Agreement is an amplifier. Disagreement is the campaign. Silence is a research task.",
        inventory=insights,
        concord={"headers": ["What they already believe", "What the papers show", "What we do"], "rows": concord or [["None yet", "—", "—"]]},
        discord={"headers": ["Belief that delays the start", "What the papers actually show", "Likely origin", "Implication"], "rows": discord or [["None mapped", "—", "—", "—"]]},
        silent={"headers": ["Insight or evidence that has no partner", "What that means"], "rows": silent or [["—", "—"]]},
    )


def _p05(brief, records, doctrine) -> dict:
    insights = brief.hcp_insights or []
    cost = brief.access_and_cost or []
    current = delay = next((i for i in insights if _looks_like_delay(i)), "Start is later than first-eligible. The brief does not describe the current habit in so many words.")
    start = next((r for r in records if r.get("directs") == "first-eligible-start"), None)
    required = (
        f"Start {brief.brand or 'the product'} at the first eligible encounter"
        + (f" — the window studied in {mark(start)} {start.get('short')}" if start else "")
        + "."
    )
    concerns = []
    if any(_looks_like_cost(c) for c in cost) or any(_looks_like_cost(i) for i in insights):
        concerns.append(["Economic", next((c for c in cost if _looks_like_cost(c)), "Cost concern named in the brief"), "Opportunity — cost", "Do not hide price. Give the doctor a legal way to stay on the patient's side."])
    if any(_looks_like_delay(i) for i in insights):
        concerns.append(["Practical / ritual", delay, "Motivation — old habit", "The new start has to be easier than waiting."])
    if any("monitor" in i.lower() or "renal" in i.lower() for i in insights):
        concerns.append(["Clinical myth", next(i for i in insights if "monitor" in i.lower() or "renal" in i.lower()), "Capability / motivation", "One sourced number, or we drop the line."])
    if any("rwe" in i.lower() or "local" in i.lower() for i in insights):
        concerns.append(["Professional", next(i for i in insights if "rwe" in i.lower() or "local" in i.lower()), "Motivation — peer cover", "KOLs do not go on a poster until the local paper exists."])
    drivers = [
        ["First-eligible start", mark(start) if start else "citation pending", "The wait", "Hospital pathway, not a leave-behind"],
        ["Cost conversation the doctor can survive", "HE paper not on the register" if not any("he" in (g.get("item") or "").lower() or "cost" in (g.get("item") or "").lower() for g in []) else "see gaps", "Prescriber guilt", "Assistance kit, inside code"],
        ["Peer cover that travels down", next((mark(r) for r in records if r.get("directs") == "guideline-cover"), "guideline pending"), "Metro-only KOLs", "Protocol authorship, then tier-2 demonstration"],
        ["A belief we can unlearn", next((i for i in insights if "monitor" in i.lower() or "renal" in i.lower()), "not named"), "The myth", "One number, one peer voice"],
    ]
    return _phase(
        "05",
        "COM-B on the actual insight and access lines. Capability is mostly intact. Opportunity (cost, ward workflow) and motivation (the wait, peer cover) are doing the damage.",
        current=current,
        required=required,
        enemy=doctrine.get("enemy") or "",
        concerns={"headers": ["Kind", "What the brief actually says", "COM-B lever", "What that asks of us"], "rows": concerns or [["—", "Brief is thin on concerns.", "—", "Ask the field before we spend."]]},
        drivers={"headers": ["Driver", "Rests on", "Barrier it has to beat", "How we pull it"], "rows": drivers},
    )


def _p06(brief, records, by_direct) -> dict:
    start = by_direct.get("first-eligible-start")
    outcome = by_direct.get("outcome-permission")
    guide = by_direct.get("guideline-cover")
    local = by_direct.get("local-context")
    def cell(r, extra=""):
        if not r:
            return "Silent — not on the register"
        return f"Supportive {mark(r)} {extra}".strip()
    rows = [
        ["Outcome vs SoC", cell(outcome), cell(outcome), "Supportive where evolving rows exist" if any("Evolving" in (r.get("stream") or "") for r in records) else "Silent", cell(guide)],
        ["First-eligible / in-hospital start", cell(start), "Neutral / not the pivotal claim", cell(start, "timing papers"), cell(guide)],
        ["Local RWE / Indian patient", "Cited in the brief, no PMID", cell(local) if local else "Registry epidemiology only" + (f" {mark(local)}" if local else ""), "Evolving — HE study ongoing (uncited)", "Silent"],
        ["Cost offset", "Silent", "Silent", "Ongoing HE study is a gap", "Silent"],
    ]
    competitors = brief.competitors or ["Standard of care"]
    position = (
        f"We stand only where the columns agree. Outcome permission {mark(outcome) if outcome else '[pending]'} "
        f"plus guideline class {mark(guide) if guide else '[pending]'} plus initiation feasibility {mark(start) if start else '[pending]'}. "
        "Cost and local RWE are silent. We will not shout there."
    )
    return _phase(
        "06",
        "Four columns: brand / independent / evolving / guideline. Alignment is the only safe shout. Silence is a boundary.",
        fourway={"headers": ["Territory", "Brand", "Independent", "Evolving", "Guidelines"], "rows": rows},
        competitors=competitors,
        position=position,
        roadmap=[
            "Retrieve DOI/PMID for the Indian RWE the brief mentions — or take it off the KOL script.",
            "Retrieve the CSI position paper if we want a national-guideline line.",
            "Do not lead with the ongoing HE study until it exists as a paper.",
        ],
    )


def _p07(brief, records, doctrine, lead) -> dict:
    start = next((r for r in records if r.get("directs") == "first-eligible-start"), None)
    outcome = next((r for r in records if r.get("directs") == "outcome-permission"), None)
    guide = next((r for r in records if r.get("directs") == "guideline-cover"), None)
    theme = doctrine.get("bet") or "Start at the first eligible visit."
    pillars = [
        [
            "Start now",
            f"First eligible encounter is a guideline encounter, not a later clinic." + (f" {mark(start)}" if start else " [citation pending]"),
            mark(start) if start else "—",
            (start.get("claim_permitted") if start else "Do not write this line until a timing paper is numbered."),
        ],
        [
            "The outcome is already earned",
            f"We are not arguing efficacy from scratch." + (f" {mark(outcome)}" if outcome else ""),
            mark(outcome) if outcome else "—",
            (outcome.get("claim_permitted") if outcome else "No outcome paper on the register."),
        ],
        [
            "Cover exists",
            f"Class I / four-pillar language is permission, not a poster after the wait." + (f" {mark(guide)}" if guide else ""),
            mark(guide) if guide else "—",
            (guide.get("claim_permitted") if guide else "No guideline PMID on the register."),
        ],
    ]
    objections = [
        ["I stabilise on ACEI first", "The initiation papers studied start after haemodynamic stability — not after a second clinic.", mark(start) if start else "pending", "Do not say 'start everyone on day one'."],
        ["The patient cannot afford this", "Stay on their side. Assistance mechanics, no price promise. No HE claim until that paper is numbered.", "gap", "Do not imply a cost-offset we have not sourced."],
        ["They are too old / too frail", next((r.get("claim_permitted") for r in records if r.get("directs") == "segment-confidence"), "No age paper on the register — do not run an elderly line."),
         mark(next((r for r in records if r.get("directs") == "segment-confidence"), None)) or "pending",
         "Do not invent an elderly-only indication."],
    ]
    return _phase(
        "07",
        "One theme. Three pillars. Each pillar carries a number or it does not ship. The objection grid says what we will not say.",
        theme=theme,
        scienceLead=(lead.get("statement") or "") + (" " + mark(*(lead.get("citations") or [])) if lead.get("citations") else ""),
        house={"headers": ["Pillar", "Line", "Ref", "Proof we are allowed to use"], "rows": pillars},
        objections={"headers": ["What they will say", "What we say", "Ref", "What we will not say"], "rows": objections},
    )


def _p08(brief, doctrine) -> dict:
    specialties = brief.target_specialties or ["the named specialists"]
    stages = [
        ["Before launch", "A handful of hospital pathway owners write the first-eligible protocol", "Medical leads. Commercial listens."],
        ["First quarter", "One hospital live, one cost conversation kit in the bag, one myth we can actually source", "Field + medical huddle weekly."],
        ["Adoption", "The second prescription is designed. Repeat among trialists is the tell.", "CRM is promotional. It goes through MLR."],
        ["After the burst", "The pathway stays when the campaign money stops", "Handover into the next cycle's working file."],
    ]
    return _phase(
        "08",
        "A doctor should feel a sequence, not a spray. We have not invented a 14-touch cadence. We have named the jobs in order.",
        stages={"headers": ["When", "Job", "Who owns it"], "rows": stages},
        rule="If a contact cannot name a numbered paper or a behaviour we are trying to change, it does not go on the plan.",
        who=f"Priority: {', '.join(specialties[:3])}.",
    )


def _p09(brief, doctrine) -> dict:
    specialties = brief.target_specialties or ["Target specialists"]
    segments = brief.hcp_segments or []
    rows = []
    specs = specialties[:3]
    names = segments[:4] or [
        f"{specs[0]} · KOL metro" if specs else "KOL metro",
        f"{specs[0]} · private metro" if specs else "Private metro",
        (specs[1] if len(specs) > 1 else "Consultant") + " · tier-2",
        "Hospital pathway owners",
    ]
    moves = [
        ("Peer cascade — they author the protocol", "Low", "Cover has to travel down"),
        ("First-eligible pathway + habit lock", "Medium", "This is where volume lives"),
        ("Affordability conversation kit", "High", "Cost is the veto"),
        ("Discharge initiation bundle", "Medium", "The window the papers studied"),
    ]
    for name, move in zip(names, moves):
        rows.append([name, move[0], move[1], move[2]])
    return _phase(
        "09",
        "We collapsed specialty × status × city × cost to the few groups this brief can actually fund. Everyone else inherits.",
        grid={"headers": ["Who", "Lead move", "Cost posture", "Why them first"], "rows": rows},
        note="Q1 is one hospital, one kit, one sourced myth. Not a national theatre.",
    )


def _p10(brief, doctrine) -> dict:
    qoq = _qoq(brief)
    goal = (brief.business_goal or "").strip() or "No numeric goal in the brief."
    kpis = [
        ["Parent", "Quarterly volume / revenue vs the brief", goal, "Sales / IQVIA equivalent", "If this does not move, the rest is decoration"],
        ["Lead", "Share of eligible starts inside 48 hours of first-eligible", "Audit the baseline first. Then set a target.", "Hospital pathway log", "Kill the protocol if this is flat at week 8 in the pilot"],
        ["Lead", "Assistance offered in eligible high-OOP starts", "Brief says the PAP is under-used.", "CRM", "If mention rises and starts do not, the kit is a pamphlet"],
        ["Lead", "Unaided prevalence of the named myth", next((i for i in brief.hcp_insights if "40%" in i or "renal" in i.lower()), "Only if the myth is in the brief"), "Insight wave", "No drop, no second burst"],
        ["Govern", "Assets with a numbered citation that have cleared MLR", "0 until medical says otherwise", "MLR log", "No number, no ship"],
    ]
    return _phase(
        "10",
        "The brief's own goal is the parent metric. Everything else has to explain it. We will not put a made-up funnel % on a slide and call it research.",
        parent=goal,
        qoq=qoq,
        kpis={"headers": ["Kind", "Metric", "From the brief / rule", "Source", "Kill / govern"], "rows": kpis},
        caveat="Any initiation % we later put on a dashboard is a planning target until the audit exists.",
    )


def _p11(brief, doctrine, lead, records, gaps) -> dict:
    cites = lead.get("citations") or []
    ask = [
        f"Sign the bet: {doctrine.get('bet')}",
        f"Sign the scientific lead, with numbers: " + (", ".join(f"{mark(c)} {c.get('short')}" for c in cites[:4]) or "none yet — do not lock"),
        "Name owners for the hospital pathway, the cost conversation, and the one myth we can source.",
        f"Park {len(gaps)} uncited brief line(s) as research, not as copy.",
        "MLR on the numbered claims before anyone builds an asset.",
    ]
    return _phase(
        "11",
        "This is the page we would actually take into the room. It is a working recommendation, not an approved campaign.",
        bet=doctrine.get("bet") or "",
        lead=lead.get("statement") or "",
        ask=ask,
        warn="Draft for medical, legal, and regulatory. Local code has the last word.",
    )


def _first_questions(brief, records, gaps) -> list[str]:
    qs = []
    if not brief.business_goal:
        qs.append("What does success look like in numbers we can audit?")
    else:
        qs.append("What is the current first-eligible start rate? The brief has a growth goal and no baseline.")
    if not any(r.get("directs") == "first-eligible-start" for r in records):
        qs.append("Which paper, with a PMID, allows us to talk about when to start?")
    if any("rwe" in (g.get("item") or "").lower() or "local" in (g.get("item") or "").lower() for g in gaps) or not brief.brand_evidence:
        qs.append("Where is the DOI for the local RWE the brief wants KOLs to hold?")
    if brief.access_and_cost:
        qs.append("What may we actually say about cost, assistance, and health economics — in this code, with a paper?")
    if not brief.hcp_insights:
        qs.append("What do these doctors currently do at the eligible moment? We have no insight line.")
    qs.append("Which hospital will run the first pathway, and who owns the 48-hour log?")
    qs.append("What will we kill in week 8 if the lead indicator has not moved?")
    return qs[:10]


def _open_questions(brief, gaps, records) -> list[str]:
    qs = _first_questions(brief, records, gaps)
    for g in gaps[:4]:
        qs.append(f"Uncited: {g['item']}")
    # unique, preserve order
    seen = set()
    out = []
    for q in qs:
        if q not in seen:
            seen.add(q)
            out.append(q)
    return out[:12]


def _effect(r: dict) -> str:
    if r.get("nnt"):
        return (
            f"{r.get('effect_metric') or 'HR'} {r.get('hr')} "
            f"({r.get('low')}–{r.get('high')}); "
            f"{r.get('control_event')} vs {r.get('treat_event')} per 100; "
            f"NNT {r.get('nnt')} ({r.get('horizon')})"
        )
    if r.get("hr") is not None:
        return f"{r.get('effect_metric') or 'HR'} {r.get('hr')} ({r.get('low')}–{r.get('high')})"
    return r.get("endpoint") or "—"


def _outcome_line(records) -> str:
    bits = []
    for r in records:
        if r.get("endpoint"):
            bits.append(f"{r['endpoint']} {mark(r)}")
    return "; ".join(bits[:4]) or "Only endpoints we can number."


def _qoq(brief) -> int | None:
    m = re.search(r"(\d+)\s*%", brief.business_goal or "")
    return int(m.group(1)) if m else None


def _looks_like_delay(text: str) -> bool:
    return bool(re.search(
        r"stabilis(?:e|ation)|stabiliz(?:e|ation)|second[- ]line|too late|"
        r"late\s*/\s*second|late/second|\bdelay(?:ed|ing|s)?\b|"
        r"wait(?:ing)? until|start on ace",
        text or "",
        re.I,
    ))


def _looks_like_cost(text: str) -> bool:
    low = text.lower()
    return any(w in low for w in ("cost", "afford", "oop", "out-of-pocket", "price", "reimburs", "pap", "assistance"))


def _short(text: str, n: int) -> str:
    text = " ".join(text.split())
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"
