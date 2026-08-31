"""Client medical-strategy deck.

The working file is the source of truth. These slides present that file in the
visual language of a medicomarketing strategy presentation: orange section
kickers, one headline, two giant facts, a so-what line, and a source.
Process notes stay in the Working file tab — they do not belong on slides.
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
    """A 12-slide client strategy deck. The working file holds the dump."""
    brand = brief.brand or "Brand"
    ta = brief.therapy_area or "the therapy area"
    market = brief.market or "the market"
    goal = brief.business_goal or "Grow clinically appropriate adoption with a number we can audit."
    lead = ledger.get("lead") or {}
    records = ledger.get("records") or []
    gaps = ledger.get("gaps") or []
    references = ledger.get("references") or work.get("references") or []
    p01 = _phase(work, "01")
    p03 = _phase(work, "03")
    p05 = _phase(work, "05")
    p07 = _phase(work, "07")
    p08 = _phase(work, "08")
    p10 = _phase(work, "10")
    p11 = _phase(work, "11")
    people = people_rows(records)
    spine = spine_rows(records, interventions)
    forest = forest_rows(records)
    primary = (lead.get("citations") or [None])[0] or {}

    slides = [
        _title_slide(brand, ta, market, doctrine, brief, records),
        _problem_slide(doctrine, p01, goal, brief, records, gaps),
        _idea_slide(doctrine, p05, p07, lead),
        _science_lead_slide(lead, primary, records, p03, doctrine, forest if people else []),
    ]
    if people:
        slides.append(_meaning_slide(people))
    elif forest:
        slides.append(_forest_slide(forest, records))
    slides.extend(
        [
            _house_slide(p07, doctrine, records, brief),
            _execute_slide(spine) if spine else _execute_from_drivers(p05, interventions),
            _moves_slide(interventions, doctrine),
            _journey_slide(p08, brand, doctrine),
            _measure_slide(goal, p10, interventions, records),
            _close_slide(brand, doctrine, p11, p07),
        ]
    )
    refs = reference_slides(references)[:1]
    if refs:
        refs[0]["id"] = "references"
        refs[0]["kicker"] = "Appendix"
    return _paginate(slides[:11] + refs)


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
            "science": _first_sentence(r.get("claim_permitted") or ""),
            "means": _complete(means),
            "barrier": _complete(r.get("spine_barrier") or ""),
            "execute": _complete(r.get("spine_execute") or (iv["name"] if iv else "")),
            "measure": _complete(r.get("spine_measure") or (iv["kill"] if iv else "")),
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
            "section": "Appendix",
            "kicker": "Appendix",
            "title": "References",
            "narrative": "This brief has not matched a PMID or DOI. We will not invent a reference list.",
            "layout": "statement",
            "bullets": ["Retrieve primary papers before anyone writes a claim."],
            "cards": [{"title": "No numbered paper", "body": "Retrieve primary papers before anyone writes a claim.", "meta": "Working file 03"}],
            "source": "Working file 03 — evidence forefront. Nothing invented.",
        }]
    slides = []
    chunk = 6
    total = (len(references) + chunk - 1) // chunk
    for i in range(0, len(references), chunk):
        part = references[i:i + chunk]
        page = i // chunk + 1
        slides.append({
            "id": "references" if page == 1 else f"references-{page}",
            "section": "Appendix",
            "kicker": "Appendix" if total == 1 else f"Appendix  ·  {page} of {total}",
            "title": "References",
            "narrative": "Superscripts in the deck are these numbers.",
            "layout": "references",
            "table": {
                "headers": ["No.", "Citation"],
                "rows": [[str(r.get("n")), r.get("citation") or ""] for r in part],
            },
            "refs": [r.get("n") for r in part],
            "source": "Vancouver list from the working-file register. Only PMID/DOI rows.",
        })
    return slides


def _title_slide(brand: str, ta: str, market: str, doctrine: dict, brief: ExtractedBrief, records: list[dict]) -> dict:
    bet = _line(doctrine.get("bet") or "Start at the first eligible encounter.", 110)
    return {
        "id": "title",
        "section": "Open",
        "kicker": f"MEDICAL STRATEGY DECK  ·  {_line(brand, 40).rstrip('.')}",
        "title": _line(brand, 42).rstrip("."),
        "subtitle": _line(doctrine.get("name") or bet, 72),
        "narrative": "",
        "layout": "title",
        "cards": [
            {"title": _line(market, 36).rstrip("."), "body": _line(ta, 80), "meta": "Market"},
            {
                "title": _line(brief.indication or ta, 40).rstrip("."),
                "body": _line(brief.product or brand, 90),
                "meta": "Indication",
            },
            {
                "title": _line(doctrine.get("name") or "The bet", 40).rstrip("."),
                "body": bet,
                "meta": "The bet",
            },
        ],
        "source": f"Internal medical affairs use  ·  {_line(brief.product or brand, 48).rstrip('.')}",
    }


def _problem_slide(doctrine: dict, p01: dict, goal: str, brief: ExtractedBrief, records: list[dict], gaps: list[dict]) -> dict:
    delay = (brief.hcp_insights or [""])[0]
    cost = (brief.access_and_cost or [""])[0]
    goal_stat = _pull_stat(goal)
    cost_stat = _pull_stat(cost)
    stats = [
        _stat(
            goal_stat or "The wait",
            _line(goal or "The brief does not name a growth number.", 110),
            "blue",
        ),
        _stat(
            cost_stat or "The ritual",
            _line(cost or delay or "The brief does not name the cost objection.", 110),
            "orange",
        ),
    ]
    headline = _enemy_headline(doctrine, p01)
    narrative = _line(
        delay
        or f"What the brief asked us to grow: {_first_sentence(goal)}",
        140,
    )
    so_what = _line(doctrine.get("bet") or "Change the decision at the eligible moment.", 110)
    return {
        "id": "problem",
        "section": "Context",
        "kicker": "Market context",
        "title": headline,
        "narrative": narrative,
        "layout": "insight",
        "stats": stats,
        "cards": _cards_from_stats(stats),
        "soWhat": so_what,
        "source": "Working file 01 — the behaviour in this brief, not a restated upload.",
    }


def _landscape_slide(p04: dict, brief: ExtractedBrief) -> dict:
    discord = p04.get("discord") or {
        "headers": ["Belief that delays the start", "What the papers show", "Implication"],
        "rows": [],
    }
    concord = p04.get("concord") or {"rows": []}
    silent = p04.get("silent") or {"rows": []}
    d_rows = [r for r in (discord.get("rows") or []) if r and r[0] not in {"None mapped", "—"}]
    c_rows = [r for r in (concord.get("rows") or []) if r and r[0] not in {"None yet", "—"}]
    s_rows = [r for r in (silent.get("rows") or []) if r and r[0] not in {"—", ""}]
    insights = brief.hcp_insights or []
    stats = [
        _stat(
            str(len(c_rows) or "Agree"),
            _complete((c_rows[0][0] if c_rows else "Belief that already matches the papers is an amplifier, not a spend.")),
            "blue",
        ),
        _stat(
            str(len(d_rows) or "The campaign"),
            _complete((d_rows[0][0] if d_rows else (insights[0] if insights else "No HCP insight was supplied."))),
            "orange",
        ),
    ]
    headers = discord.get("headers") or []
    rows = discord.get("rows") or []
    if len(headers) > 3:
        keep = [0, 1, -1]
        headers = [headers[i] for i in keep]
        rows = [[row[i] if i < len(row) else "" for i in keep] for row in rows]
    return {
        "id": "opportunity",
        "section": "Context",
        "kicker": "HCP landscape",
        "title": (
            "The literature already moved. The field has not."
            if d_rows
            else "Agreement is an amplifier. Disagreement is the campaign."
        ),
        "narrative": _complete(
            "Numbered papers versus the habit the brief actually described. "
            "If the brief named no habit, capturing it is a research task — not a reason to restate the upload."
        ),
        "layout": "insight",
        "stats": stats,
        "cards": _cards_from_stats(stats),
        "soWhat": _complete(
            f"{len(d_rows)} disagreement line{'s' if len(d_rows) != 1 else ''} set the campaign. "
            f"{len(s_rows)} line{'s' if len(s_rows) != 1 else ''} are still silent on the register."
        ),
        "source": "Working file 04 — what the doctors already told us, mapped to numbered papers.",
        "table": {"headers": headers, "rows": rows[:5]},
    }


def _barriers_slide(p05: dict, brief: ExtractedBrief, doctrine: dict) -> dict:
    concerns = (p05.get("concerns") or {}).get("rows") or []
    live = [r for r in concerns if r and r[0] not in {"—", ""}]
    delay = p05.get("current") or (brief.hcp_insights[0] if brief.hcp_insights else "The brief does not name the current habit.")
    cost = (brief.access_and_cost or ["Cost is not described in this brief."])[0]
    left = live[0] if live else ["Practical / ritual", delay, "", ""]
    right = live[1] if len(live) > 1 else ["Economic", cost, "", ""]
    left_stat = _pull_stat(str(left[1])) or _short_label(left[0])
    right_stat = _pull_stat(str(right[1])) or _short_label(right[0])
    stats = [
        _stat(left_stat, _complete(left[1] if len(left) > 1 else delay), "orange"),
        _stat(right_stat, _complete(right[1] if len(right) > 1 else cost), "blue"),
    ]
    return {
        "id": "barriers",
        "section": "Context",
        "kicker": "The behaviour we change",
        "title": _headline(p05.get("required") or doctrine.get("bet") or "Change the decision at the eligible moment."),
        "narrative": _complete(p05.get("current") or delay),
        "layout": "insight",
        "stats": stats,
        "cards": _cards_from_stats(stats),
        "soWhat": _complete(
            f"Strategic answer: {doctrine.get('bet') or p05.get('required') or 'retire the wait at the first eligible encounter'}."
        ),
        "source": "Working file 05 — COM-B on the actual insight and access lines.",
    }


def _idea_slide(doctrine: dict, p05: dict, p07: dict, lead: dict) -> dict:
    drivers = (p05.get("drivers") or {}).get("rows") or []
    cards = []
    for i, row in enumerate(drivers[:4]):
        cards.append({
            "title": row[0] if row else "Driver",
            "body": _line(row[3] if len(row) > 3 else (row[1] if len(row) > 1 else ""), 110),
            "meta": row[1] if len(row) > 1 else "",
            "accent": "blue" if i % 2 == 0 else "orange",
        })
    if not cards:
        cards = [
            {"title": "The bet", "body": _line(doctrine.get("bet") or "", 110), "meta": "Doctrine", "accent": "blue"},
            {"title": "The enemy", "body": _line(doctrine.get("enemy") or "", 110), "meta": "Doctrine", "accent": "orange"},
            {"title": "Scientific lead", "body": _line(doctrine.get("scienceAnchor") or "No numbered paper yet.", 110), "meta": "Working file 03", "accent": "blue"},
            {"title": "What we will say", "body": _line(p07.get("theme") or doctrine.get("bet") or "", 110), "meta": "Working file 07", "accent": "orange"},
        ]
    refs = [c.get("ref") for c in (lead.get("citations") or []) if c.get("ref")]
    return {
        "id": "the-bet",
        "section": "Idea",
        "kicker": "The strategic idea",
        "title": _line(doctrine.get("name") or doctrine.get("bet") or "Start at the first eligible encounter", 56),
        "subtitle": _line(doctrine.get("bet") or doctrine.get("whyNovel") or "", 110),
        "narrative": "",
        "layout": "idea",
        "cards": cards,
        "refs": refs,
        "source": "Working file 05–07 — drivers and the signed bet. Not a slogan board.",
        "callout": {
            "label": "The bet",
            "text": _line(doctrine.get("bet") or doctrine.get("scienceAnchor") or "Sign the bet before anyone writes copy.", 140),
        },
    }


def _usable_finding(primary: dict, rec: dict) -> str:
    """A published finding, never a methods opener or abstract dump."""
    raw = (
        rec.get("claim_permitted")
        or primary.get("claim")
        or rec.get("abstract")
        or primary.get("short")
        or rec.get("title")
        or ""
    )
    raw = re.sub(r"^Independent / indication landscape — not a trial of [^.]+.\s*", "", str(raw))
    raw = re.sub(r"^Abstract:\s*", "", raw, flags=re.I)
    raw = re.sub(r"\s*Confirm full text before promotional use\.?\s*$", "", raw, flags=re.I)
    raw = re.sub(r"^PubMed record:\s*", "", raw, flags=re.I)
    if rec.get("abstract"):
        from .evidence import _finding_from_abstract

        raw = _finding_from_abstract(rec.get("abstract") or raw, rec.get("title") or primary.get("short") or "")
    from .evidence import _is_clinical_finding, _result_clause

    raw = re.sub(r"^Retrieved from PubMed:\s*", "", str(raw), flags=re.I)
    if not raw or not _is_clinical_finding(raw):
        return ""
    return _result_clause(raw.strip())


def _science_lead_slide(
    lead: dict,
    primary: dict,
    records: list[dict],
    p03: dict,
    doctrine: dict | None = None,
    forest: list[dict] | None = None,
) -> dict:
    tag = mark(primary) if primary.get("ref") else ""
    rec = next((r for r in records if r.get("id") == primary.get("id")), {}) or {}
    finding = _usable_finding(primary, rec)
    claim = _line(finding, 72) if finding else _line(
        (doctrine or {}).get("name") or "Lead with a numbered paper, not a slogan.",
        56,
    )
    nnt = rec.get("nnt")
    hr = rec.get("hr")
    n = primary.get("n") or rec.get("n") or "—"
    pmid = primary.get("pmid") or rec.get("pmid") or "—"
    stats = []
    if nnt is not None:
        stats.append(_stat(str(nnt), _line(f"Treat {nnt} to prevent one event. {tag} PMID {pmid}.", 110), "blue"))
    if hr is not None:
        stats.append(_stat(
            f"HR {hr}",
            _line(f"{rec.get('low')}–{rec.get('high')}  ·  n = {n}.", 80),
            "orange",
        ))
    if not stats:
        label = "BGF" if re.search(r"\bBGF\b|budesonide/glycopyr", f"{primary.get('short') or ''} {rec.get('title') or ''}", re.I) else "Lead"
        stats = [
            _stat(
                label,
                _line(f"PMID {pmid}." if pmid != "—" else "No numbered lead yet.", 40),
                "blue",
            ),
            _stat(
                str(rec.get("year") or (str(n) if n != "—" else "Lead")),
                _line(
                    rec.get("journal")
                    or ("Patients in the lead paper." if n != "—" else "Numbered paper. Read full text before a promotional line."),
                    90,
                ),
                "orange",
            ),
        ]
    paper = primary.get("short") or rec.get("short") or rec.get("title") or ""
    narrative = _line(
        f"{tag} {paper} · PMID {pmid}.".strip() if finding else "No DOI or PMID matched this brief. The working file keeps the search.",
        110,
    )
    slide = {
        "id": "science-lead",
        "section": "Evidence",
        "kicker": "Clinical evidence",
        "title": claim,
        "subtitle": _line(f"{tag} {primary.get('short') or 'No validated lead'} · PMID {pmid}", 90),
        "narrative": narrative,
        "layout": "insight",
        "stats": stats[:2],
        "cards": [
            {
                "title": _line(primary.get("short") or "No lead paper", 48).rstrip("."),
                "body": _line(finding or "No numbered paper yet.", 140),
                "meta": f"{tag} PMID {pmid}",
            },
            {
                "title": "So the campaign",
                "body": _line((doctrine or {}).get("bet") or "We lead with a numbered paper, not with a slogan.", 110),
                "meta": f"n = {n}",
            },
        ],
        "soWhat": _line((doctrine or {}).get("bet") or "We lead with a numbered paper, not with a slogan.", 110),
        "source": _source_line(primary, rec),
        "refs": [c.get("ref") for c in (lead.get("citations") or []) if c.get("ref")],
    }
    if forest:
        slide["chart"] = {
            "kind": "forest",
            "title": "Published effect sizes on the register",
            "note": "HR or ratio and 95% CI copied from the cited publication.",
            "data": forest,
        }
        slide["id"] = "science-lead"
    return slide


def _literature_slide(ledger: dict, brief: ExtractedBrief) -> dict:
    review = ledger.get("review") or {}
    terms = review.get("searched") or ledger.get("searchTerms") or []
    records = ledger.get("records") or []
    rows = []
    for r in records[:8]:
        finding = (r.get("abstract") or r.get("claim_permitted") or r.get("title") or "")[:180]
        rows.append([
            mark(r) or "—",
            r.get("short") or r.get("title") or "",
            f"PMID {r.get('pmid') or '—'}",
            _complete(finding),
        ])
    if not rows:
        rows = [["—", "No hit yet", "—", "PubMed returned nothing we could keep after molecule filters."]]
    return {
        "id": "literature-review",
        "section": "Evidence",
        "kicker": "Literature review",
        "title": "We searched PubMed for this product and indication. The brief did not have to bring a bibliography.",
        "narrative": _complete(
            review.get("synthesis")
            or f"Queries run against NCBI for {brief.product or brief.brand or 'this brand'}."
        ),
        "layout": "table",
        "table": {
            "headers": ["Ref", "Paper", "PMID", "What the abstract actually says"],
            "rows": rows,
        },
        "cards": [
            {
                "title": "What we searched",
                "body": _complete("; ".join(terms[:4]) or "No query built from this brief."),
                "meta": f"{len(terms)} PubMed quer{'ies' if len(terms) != 1 else 'y'}",
            },
            {
                "title": "What we refused",
                "body": _complete(review.get("excluded") or "Another molecule's catalog pivotal stays off this register."),
                "meta": "Molecule isolation",
            },
        ],
        "soWhat": _complete(
            "Strategy starts from these papers versus the behaviour in the brief — not from restating the upload."
        ),
        "source": "NCBI PubMed eutils + catalog rows this brief actually named.",
        "refs": [r.get("ref") for r in records if r.get("ref")],
    }


def _forest_slide(forest: list[dict], records: list[dict]) -> dict:
    return {
        "id": "forest",
        "section": "Evidence",
        "kicker": "Clinical evidence",
        "title": "These are the published effect sizes. We will not invent a missing hazard ratio.",
        "narrative": "Only rows with a DOI or PMID are plotted. Uncited brief items stay off this figure.",
        "layout": "chart",
        "chart": {
            "kind": "forest",
            "title": "Validated evidence position (named trials)",
            "note": "HR or ratio and 95% CI copied from the cited publication. Superscripts are Vancouver numbers.",
            "data": forest,
        },
        "source": "Working file 03 — numbered papers only.",
        "refs": [r.get("ref") for r in records if r.get("hr") is not None and r.get("ref")],
    }


def _meaning_slide(people: list[dict]) -> dict:
    first = people[0]
    tag = mark({"ref": first.get("ref")}) if first.get("ref") else ""
    nnt = first.get("nnt")
    return {
        "id": "science-meaning",
        "section": "Evidence",
        "kicker": "Clinical evidence",
        "title": _line(
            f"Treat {nnt} to prevent one event." if nnt else "In a clinic of 100, this is what the paper showed.",
            72,
        ),
        "subtitle": f"{tag} {first.get('name', '').replace(tag, '').strip()} · PMID {first.get('pmid') or '—'}",
        "narrative": _line(
            f"{first.get('claim') or ''} {tag} "
            f"{first.get('control')} events on the comparator versus {first.get('treat')} on the intervention"
            + (f" — treat {nnt} to prevent one event" if nnt else ""),
            160,
        ),
        "layout": "infographic",
        "soWhat": _line(f"Treat {nnt} to prevent one event over {first.get('horizon') or 'the published horizon'}." if nnt else first.get("claim") or "", 140),
        "source": f"{tag} PMID {first.get('pmid')}. Horizon: {first.get('horizon') or 'as published'}.",
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
        "section": "Evidence",
        "kicker": "Timing evidence",
        "title": "The comparator is the delayed habit, not another molecule.",
        "subtitle": f"{tag} {first.get('name', '').replace(tag, '').strip()} · PMID {first.get('pmid') or '—'}",
        "narrative": _complete(f"{first.get('claim') or ''} {tag}"),
        "layout": "infographic",
        "soWhat": _complete("A long-term or early-start frame only holds if this paper numbered the window."),
        "source": f"{tag} PMID {first.get('pmid')}. {first.get('horizon') or 'As published'}.",
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
        "section": "Evidence",
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
                    _complete(_finding(r)),
                    r.get("grade") or "",
                ]
                for r in records[:8]
            ] or [["—", "No numbered paper yet", "Do not lock a lead", "—"]],
        },
        "source": "Working file 03 — every row is a paper we can put a number on.",
        "refs": [r.get("ref") for r in records if r.get("ref")],
    }


def _house_slide(p07: dict, doctrine: dict, records: list[dict], brief: ExtractedBrief) -> dict:
    house = p07.get("house") or {"headers": ["Pillar", "Line", "Ref", "Proof"], "rows": []}
    rows = list(house.get("rows") or [])
    if len(rows) == 3 and (brief.access_and_cost or []):
        rows.append([
            "Stay on their side",
            _complete(f"Cost is a veto, not a footnote. {(brief.access_and_cost or [''])[0]}"),
            "gap",
            "No health-economic claim until that paper is numbered.",
        ])
    data = [
        {
            "name": row[0] if row else "Pillar",
            "line": _complete(row[1] if len(row) > 1 else ""),
            "ref": row[2] if len(row) > 2 else "",
            "proof": _first_sentence(row[3] if len(row) > 3 else ""),
        }
        for row in rows[:4]
    ]
    if not data:
        data = [{"name": "Permission now", "line": doctrine.get("bet") or "", "ref": "—", "proof": "Citation pending"}]
    return {
        "id": "house",
        "section": "Message",
        "kicker": "Messaging architecture",
        "title": "One theme. Pillars without a number do not ship.",
        "narrative": _line(p07.get("theme") or doctrine.get("bet") or "One theme. Pillars without a number do not ship.", 140),
        "layout": "infographic",
        "soWhat": _line(p07.get("theme") or doctrine.get("bet") or "Start at the first eligible visit", 140),
        "source": "Working file 07 — one theme, sourced pillars, objection grid in the working file.",
        "chart": {
            "kind": "house",
            "title": _line(p07.get("theme") or doctrine.get("bet") or "Start at the first eligible visit", 90),
            "data": data,
        },
        "refs": [r.get("ref") for r in records[:3] if r.get("ref")],
    }


def _execute_slide(spine: list[dict]) -> dict:
    return {
        "id": "science-execute",
        "section": "Action",
        "kicker": "Science to solution",
        "title": "Science names the prize. The field takes it.",
        "narrative": "Each cited finding becomes one campaign move.",
        "layout": "infographic",
        "source": "Working file 03 × 08 — only rows with a PMID or DOI. Uncited brief items cannot own a move.",
        "chart": {
            "kind": "spine",
            "title": "Science to solution through execution",
            "note": "Only rows with a PMID or DOI. Uncited brief items cannot own a move.",
            "data": spine,
        },
    }


def _execute_from_drivers(p05: dict, interventions: list[dict]) -> dict:
    drivers = (p05.get("drivers") or {}).get("rows") or []
    data = []
    for row, iv in zip(drivers[:4], interventions or [{}] * 4):
        data.append({
            "name": row[0] if row else "Driver",
            "science": _complete(row[1] if len(row) > 1 else "Citation pending"),
            "means": _complete(row[0] if row else ""),
            "barrier": _complete(row[2] if len(row) > 2 else ""),
            "execute": _complete((iv or {}).get("name") or (row[3] if len(row) > 3 else "")),
            "measure": _complete((iv or {}).get("kill") or ""),
            "move": (iv or {}).get("name") or "",
            "pmid": "",
        })
    if not data:
        data = [{
            "name": "No spine yet",
            "science": "No numbered paper matched this brief.",
            "means": "Do not lock a move.",
            "barrier": "Uncited lines cannot own execution.",
            "execute": "Retrieve the primary paper.",
            "measure": "Kill any line without a PMID.",
            "move": "",
            "pmid": "",
        }]
    return {
        "id": "science-execute",
        "section": "Action",
        "kicker": "Science to solution",
        "title": "Science names the prize. The field takes it.",
        "narrative": "Until a paper is numbered, the driver table is a planning sketch, not a claim.",
        "layout": "infographic",
        "source": "Working file 05 — drivers only. No invented effect sizes.",
        "chart": {
            "kind": "spine",
            "title": "Science to solution through execution",
            "note": "Planning rows from the working file. Not research.",
            "data": data,
        },
    }


def _moves_slide(interventions: list[dict], doctrine: dict | None = None) -> dict:
    did = (doctrine or {}).get("id")
    if did == "first-line-not-rescue":
        headline = "Five moves that make triple first-line, not rescue."
    elif did == "affordability-confidence":
        headline = "Five moves that make the cost conversation survivable."
    elif did == "perception-reset":
        headline = "Five moves that unlearn one wrong belief."
    else:
        headline = "Five moves that retire the wait."
    bullets = [
        f"{i['name']} · {i.get('evidenceAnchor') or 'citation pending'}"
        for i in interventions[:5]
        if i.get("name")
    ]
    return {
        "id": "interventions",
        "section": "Action",
        "kicker": "Five strategic moves",
        "title": headline,
        "narrative": "Each move executes a cited finding. None of them is a separate creative idea.",
        "layout": "cards",
        "source": "Working file 08–09 — each move executes one cited finding.",
        "bullets": bullets,
        "cards": [
            {
                "title": i["name"],
                "body": _line(i["promise"], 110),
                "meta": i.get("evidenceAnchor") or "citation pending",
                "accent": "blue" if n % 2 == 0 else "orange",
            }
            for n, i in enumerate(interventions[:5])
        ],
        "chart": {
            "kind": "scatter",
            "title": "Impact vs feasibility of the five moves",
            "xLabel": "Feasibility",
            "yLabel": "Impact on the key driver",
            "note": "Architecture scores for this mix. Not research.",
            "data": [
                {"name": i["name"], "x": i.get("feasibility") or 50, "y": i.get("impact") or 50, "z": 28}
                for i in interventions[:5]
            ],
        },
    }


def _matrix_slide(interventions: list[dict]) -> dict:
    return {
        "id": "matrix",
        "section": "Action",
        "kicker": "Where we spend first",
        "title": "Q1 buys proof of mechanism. We do not spend the year on congress theatre.",
        "narrative": "Impact versus feasibility for this architecture. These are design scores, not a market survey.",
        "layout": "chart",
        "source": "Working file 09 — architecture scores for this mix. Not research.",
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


def _who_slide(specialties: list[str], interventions: list[dict], brief: ExtractedBrief, p09: dict) -> dict:
    grid = p09.get("grid") or {}
    if grid.get("rows"):
        headers = grid.get("headers") or ["Who", "Lead move", "Cost posture", "Why them first"]
        rows = grid.get("rows")
    else:
        lead = specialties[0] if specialties else "Specialist"
        second = specialties[1] if len(specialties) > 1 else "Consultant"
        names = [i["name"] for i in interventions[:5]]
        headers = ["Segment", "Lead intervention", "Cost posture", "Q1 weight"]
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
        "kicker": "Who we activate first",
        "title": "Four rooms carry the year. Everyone else inherits.",
        "narrative": _complete(p09.get("note") or "Activation is a specialty × city × cost grid that we then collapse. Cost-concern is a design input, not a footnote."),
        "layout": "table",
        "table": {"headers": headers, "rows": rows},
        "source": "Working file 09 — collapsed to the few groups this brief can actually fund.",
    }


def _journey_slide(p08: dict, brand: str, doctrine: dict | None = None) -> dict:
    stages = (p08.get("stages") or {}).get("rows") or [
        ["Before launch", "Pathway owners write the first-eligible protocol", "Medical leads"],
        ["First quarter", "One hospital live, one cost kit, one sourced myth", "Field + medical"],
        ["Adoption", "The second prescription is designed", "CRM through MLR"],
        ["After the burst", "The pathway stays when the campaign money stops", "Handover"],
    ]
    if (doctrine or {}).get("id") == "first-line-not-rescue":
        journey_title = _line(f"First-line {brand.split()[0]}, then mix, then stay.", 72)
    else:
        journey_title = "A doctor should feel a designed sequence, not a spray of assets."
    return {
        "id": "journey",
        "section": "Engagement",
        "kicker": "The sequence",
        "title": journey_title,
        "narrative": _line(
            p08.get("rule")
            or f"If a contact cannot name a numbered paper or a behaviour we are changing, it does not go on the {brand} plan.",
            140,
        ),
        "layout": "infographic",
        "source": "Working file 08 — jobs in order. Not a 14-touch cadence we invented.",
        "chart": {
            "kind": "flow",
            "title": "Campaign sequence",
            "data": [
                {"name": _complete(row[0]), "detail": _complete(row[1])}
                for row in stages[:4]
            ],
        },
    }


def _measure_slide(goal: str, p10: dict, interventions: list[dict], records: list[dict]) -> dict:
    parent = p10.get("parent") or goal
    kpi_block = p10.get("kpis") or {}
    rows = kpi_block.get("rows") or []
    cards = []
    for row in rows[:4]:
        cards.append({
            "title": _line(row[1] if len(row) > 1 else "Metric", 40).rstrip("."),
            "body": _line(row[2] if len(row) > 2 else "", 110),
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
    rate = _pull_stat(parent or goal)
    measure_title = _line(
        f"{rate} quarterly growth is the parent metric." if rate else "We kill the plan if this number does not move.",
        72,
    )
    slide = {
        "id": "measure",
        "section": "Measurement",
        "kicker": "How we will know",
        "title": measure_title,
        "subtitle": _line(parent, 110),
        "narrative": _complete(p10.get("caveat") or "This line is a planning target from the brief. It is not an audited baseline."),
        "layout": "chart" if series or _papers_by_year(records) else "cards",
        "cards": cards,
        "source": "Working file 10 — the brief’s own goal is the parent metric. Not an audited baseline.",
    }
    if series:
        slide["chart"] = {
            "kind": "line",
            "title": "Planning target taken from the brief’s stated QoQ goal",
            "note": "Index, Q0 = 100. This is the brief’s own ambition, not an audited baseline.",
            "series": ["target"],
            "data": series,
        }
    else:
        years = _papers_by_year(records)
        if years:
            slide["chart"] = {
                "kind": "line",
                "title": "Numbered papers on the register by publication year",
                "note": "Counts from the working-file register. Not a market forecast.",
                "series": ["papers"],
                "data": years,
            }
    return slide


def _close_slide(brand: str, doctrine: dict, p11: dict, p07: dict) -> dict:
    asks = (p11.get("ask") or [])[:4]
    pillars = (p07.get("house") or {}).get("rows") or []
    chips = [{"title": row[0], "body": _first_sentence(row[1] if len(row) > 1 else ""), "meta": row[2] if len(row) > 2 else ""} for row in pillars[:4]]
    if not chips:
        chips = [{"title": f"Ask {i + 1}", "body": _first_sentence(a), "meta": brand} for i, a in enumerate(asks[:4])]
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
        "kicker": "Strategic summary",
        "title": _close_headline(doctrine),
        "narrative": _line(p11.get("warn") or "Draft for medical, legal, and regulatory", 110),
        "layout": "close",
        "cards": chips,
        "source": "Working file 11 — the page we would take into the room. Draft for MLR.",
        "chart": {
            "kind": "flow",
            "title": "What we need signed in the room",
            "data": steps,
        },
        "callout": {"label": brand, "text": _line(doctrine.get("bet") or doctrine.get("name") or "", 140)},
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


def _papers_by_year(records: list[dict]) -> list[dict]:
    counts: dict[int, int] = {}
    for r in records:
        year = r.get("year")
        try:
            year = int(year)
        except (TypeError, ValueError):
            continue
        counts[year] = counts.get(year, 0) + 1
    if len(counts) < 2:
        return []
    return [{"name": str(y), "papers": counts[y]} for y in sorted(counts)]


def _phase(work: dict, pid: str) -> dict:
    for phase in work.get("phases") or []:
        if phase.get("id") == pid:
            return phase
    return {}


def _paginate(slides: list[dict]) -> list[dict]:
    for i, slide in enumerate(slides, 1):
        slide["page"] = f"{i:02d}"
    return slides


def _stat(value, caption: str, accent: str) -> dict:
    return {"value": str(value), "caption": caption, "accent": accent}


def _cards_from_stats(stats: list[dict]) -> list[dict]:
    return [
        {"title": s["value"], "body": s["caption"], "meta": s.get("accent") or "", "accent": s.get("accent")}
        for s in stats
    ]


def _headline(text) -> str:
    return _line(text, 56)


def _enemy_headline(doctrine: dict, p01: dict | None = None) -> str:
    named = {
        "first-line-not-rescue": "Triple sits as rescue. Free-mix is the ritual.",
        "first-touch": "They wait until the patient is 'stable' in clinic.",
        "affordability-confidence": "Cost guilt, not disbelief, blocks the start.",
        "perception-reset": "One wrong belief is blocking the start.",
        "conviction-cascade": "Conviction fails at the moment of the pen.",
    }
    if doctrine.get("id") in named:
        return named[doctrine["id"]]
    return _line(
        doctrine.get("enemy")
        or (p01 or {}).get("restatedNeed")
        or "The conversion problem is delay, not disbelief.",
        56,
    )


def _close_headline(doctrine: dict) -> str:
    if doctrine.get("id") == "first-line-not-rescue":
        return "Sign first-line maintenance. Park the rest."
    if doctrine.get("id") == "first-touch":
        return "Sign first-eligible start. Number the claims."
    return "Sign the bet. Number the claims. Park the gaps."


def _line(text, limit: int = 90) -> str:
    """One slide-worthy sentence. Never dump an abstract onto a headline."""
    text = _complete(_first_sentence(text))
    if not text:
        return ""
    if len(text) <= limit:
        return text
    cut = text[: max(limit - 1, 8)].rsplit(" ", 1)[0].rstrip(".,;: ")
    filler = {
        "if", "the", "a", "an", "in", "to", "for", "and", "or", "of", "as", "at", "by", "on",
        "is", "are", "was", "were", "be", "been", "being", "with", "from", "that",
        "versus", "vs", "vs.", "than",
    }
    while cut:
        last = cut.split()[-1].lower()
        dangling = last in filler or ("-" in last and not re.search(r"\d", last))
        if not dangling:
            break
        cut = cut.rsplit(" ", 1)[0].rstrip(".,;: ")
    if not cut:
        cut = text[: limit - 1].rstrip()
    return _complete(cut)


def _short_label(text) -> str:
    text = " ".join(str(text or "").split())
    if not text:
        return "—"
    return text.split("/")[0].split("—")[0].strip()[:18] or text[:18]


def _pull_stat(text: str) -> str:
    raw = str(text or "")
    match = re.search(r"(\d+\s*[-–]\s*\d+\s*[x×])|(\d+(?:\.\d+)?\s*%)|(\d+(?:\.\d+)?\s*[x×])", raw, re.I)
    if not match:
        return ""
    return re.sub(r"\s+", "", match.group(0))


def _source_line(primary: dict, rec: dict) -> str:
    citation = primary.get("citation") or rec.get("citation") or ""
    pmid = primary.get("pmid") or rec.get("pmid") or ""
    if citation:
        return citation
    if pmid:
        return f"PMID {pmid}."
    return "Working file 03 — no numbered lead yet."


def _complete(text) -> str:
    text = " ".join(str(text or "").split()).replace("…", "").replace("...", "")
    text = text.rstrip(" ,;:")
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
    from .evidence import _finding_from_abstract

    finding = _finding_from_abstract(row.get("abstract") or "", row.get("title") or "")
    if finding:
        return finding[:140]
    return (row.get("claim_permitted") or row.get("endpoint") or "—")[:140]
