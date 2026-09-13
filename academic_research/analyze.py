"""Quantitative frequency analysis and qualitative narrative + IPA synthesis."""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict

from .extract import (
    CLAIM_LABELS,
    IPA_CODEBOOK,
    ipa_hits,
    is_named_outcome_trial,
    pick_primary_effect,
    sentences,
    short_study_label,
)
from .models import EvidenceRecord

DESIGN_LABELS = {
    "rct": "Randomised trial",
    "systematic_review": "Systematic review / meta-analysis",
    "guideline": "Clinical practice guideline",
    "observational": "Observational / registry",
    "qualitative": "Qualitative / IPA-eligible",
    "policy_guidance": "UN / NGO policy guidance",
    "trial_registry": "Trial registry record",
    "other": "Other / unclassified",
}

# Heuristic certainty bands labelled as such — not a formal GRADE panel.
GRADE_BANDS = {
    "rct": (
        "High",
        "Outcome RCTs with a parsed 95% CI. Formal GRADE would still require risk-of-bias appraisal of full texts.",
    ),
    "systematic_review": (
        "High–moderate",
        "Systematic reviews and meta-analyses. Certainty still depends on included-study quality.",
    ),
    "guideline": (
        "Moderate",
        "Society or national guidance. Recommendation class/level is taken from the source, not re-graded here.",
    ),
    "observational": (
        "Low",
        "Cohorts, registries, and observational analyses.",
    ),
    "qualitative": (
        "Not for effect sizes",
        "IPA-eligible papers inform meaning and barriers; they do not yield hazard ratios.",
    ),
    "policy_guidance": (
        "Not GRADE-rated",
        "UN/NGO technical packages and fact sheets used for implementation context.",
    ),
    "trial_registry": (
        "Not GRADE-rated",
        "Protocol or registry records; outcomes may be incomplete.",
    ),
    "other": (
        "Ungraded",
        "Insufficient design markers in the abstract.",
    ),
}


def quantitative(records: list[EvidenceRecord]) -> dict:
    n = max(len(records), 1)
    claim_map: dict[str, list[int]] = defaultdict(list)
    for rec in records:
        cid = rec.citation_id or 0
        for claim in rec.claims:
            claim_map[claim].append(cid)
    claim_frequency = []
    for claim, ids in sorted(claim_map.items(), key=lambda kv: -len(kv[1])):
        uniq = sorted(set(ids))
        claim_frequency.append(
            {
                "id": claim,
                "label": CLAIM_LABELS.get(claim, claim),
                "count": len(uniq),
                "percent": round(100.0 * len(uniq) / n, 1),
                "citation_ids": uniq,
            }
        )
    family = Counter(r.source_family for r in records)
    years = Counter(r.year for r in records if r.year)
    designs = Counter(r.study_design or "other" for r in records)
    oa = sum(1 for r in records if r.is_oa)
    return {
        "n_included": len(records),
        "claim_frequency": claim_frequency,
        "by_source_family": [
            {"id": k, "count": v, "percent": round(100.0 * v / n, 1)}
            for k, v in family.most_common()
        ],
        "by_study_design": [
            {
                "id": k,
                "label": DESIGN_LABELS.get(k, k),
                "count": v,
                "percent": round(100.0 * v / n, 1),
            }
            for k, v in designs.most_common()
        ],
        "grade_profile": grade_profile(records),
        "by_year": [
            {"year": y, "count": c} for y, c in sorted(years.items()) if y
        ],
        "oa_vs_paywalled": {
            "open_access": oa,
            "paywalled_or_unclear": len(records) - oa,
        },
        "qualitative_share": {
            "qualitative": sum(1 for r in records if r.is_qualitative),
            "other": sum(1 for r in records if not r.is_qualitative),
        },
        "guideline_share": {
            "guidelines": sum(1 for r in records if r.is_guideline),
            "other": sum(1 for r in records if not r.is_guideline),
        },
        "agency_coverage": agency_coverage(records),
        "geography": geography(records),
    }


def geography(records: list[EvidenceRecord]) -> list[dict]:
    """Heuristic region tags from title, abstract, and issuing body — never guessed countries."""
    groups: dict[str, list[int]] = defaultdict(list)
    for rec in records:
        blob = f"{rec.title} {rec.abstract} {rec.issuing_body} {rec.venue or ''}".lower()
        if any(t in blob for t in ("india", "indian", "trivandrum", "icmr", "nhm.gov", "mohfw")):
            tag = "India"
        elif any(t in blob for t in ("ethiopia", "africa", "afro", "sub-saharan")):
            tag = "Africa"
        elif any(t in blob for t in ("south-east asia", "southeast asia", "searo")):
            tag = "South-East Asia"
        elif any(t in blob for t in ("australia", "new zealand", "nhfa", "csanz", "western pacific", "wpro")):
            tag = "Western Pacific"
        elif any(t in blob for t in ("canada", "ccs/chfs", "canadian cardiovascular")):
            tag = "North America"
        elif any(t in blob for t in ("eastern mediterranean", "emro")):
            tag = "Eastern Mediterranean"
        elif any(t in blob for t in ("paho", "americas", "latin america")):
            tag = "Americas"
        elif any(
            t in blob
            for t in (
                "world health",
                "united nations",
                "world bank",
                "unicef",
                "unaids",
                "who iris",
                "sdg 3",
                "sustainable development goal 3",
            )
        ):
            tag = "Global / UN system"
        elif any(t in blob for t in ("nice", "esc guideline", "europe", "united kingdom", "nhs")):
            tag = "Europe"
        elif any(t in blob for t in ("american heart", "aha/acc", "acc/aha", "united states")):
            tag = "North America"
        else:
            tag = "Multi-country / unspecified"
        if rec.citation_id:
            groups[tag].append(rec.citation_id)
    n = max(len(records), 1)
    order = [
        "India",
        "Africa",
        "South-East Asia",
        "Western Pacific",
        "Eastern Mediterranean",
        "Americas",
        "Europe",
        "North America",
        "Global / UN system",
        "Multi-country / unspecified",
    ]
    rows = []
    for tag in order:
        ids = sorted(set(groups.get(tag) or []))
        if not ids:
            continue
        rows.append(
            {
                "id": tag,
                "count": len(ids),
                "percent": round(100.0 * len(ids) / n, 1),
                "citation_ids": ids,
            }
        )
    return rows


def connector_yield(log: list[dict]) -> list[dict]:
    """Hits per live connector, parsed from the harvest log (zeros kept for quiet APIs)."""
    skip = {"harvest", "dedupe", "screen", "validate"}
    rows = []
    for entry in log or []:
        step = entry.get("step") or ""
        if step in skip:
            continue
        detail = entry.get("detail") or ""
        match = re.search(r"(\d+)\s+hits", detail)
        rows.append(
            {
                "connector": step,
                "query": (detail.split(":")[0] if ":" in detail else ""),
                "hits": int(match.group(1)) if match else 0,
                "ok": "FAILED" not in detail,
            }
        )
    rows.sort(key=lambda r: (-r["hits"], r["connector"]))
    return rows[:24]


def agency_coverage(records: list[EvidenceRecord]) -> list[dict]:
    """Counts of UN/NGO/guideline issuing bodies in the included corpus."""
    interesting = {
        "un_agency",
        "ngo",
        "international_guideline",
        "national_guideline",
        "policy_guidance",
    }
    bodies = Counter()
    for rec in records:
        if rec.source_family in interesting:
            body = (rec.issuing_body or rec.venue or "Institutional author").strip()
            if body:
                bodies[body] += 1
    return [{"body": name, "count": n} for name, n in bodies.most_common(16)]


def grade_profile(records: list[EvidenceRecord]) -> list[dict]:
    groups: dict[str, list[int]] = defaultdict(list)
    for rec in records:
        design = rec.study_design or "other"
        if rec.citation_id:
            groups[design].append(rec.citation_id)
    rows = []
    for design, ids in groups.items():
        uniq = sorted(set(ids))
        band, note = GRADE_BANDS.get(design, GRADE_BANDS["other"])
        rows.append(
            {
                "id": design,
                "label": DESIGN_LABELS.get(design, design),
                "band": band,
                "note": note,
                "count": len(uniq),
                "citation_ids": uniq[:12],
            }
        )
    order = [
        "rct",
        "systematic_review",
        "guideline",
        "observational",
        "qualitative",
        "policy_guidance",
        "trial_registry",
        "other",
    ]
    rows.sort(key=lambda r: order.index(r["id"]) if r["id"] in order else 99)
    return rows


def forest_rows(records: list[EvidenceRecord]) -> list[dict]:
    rows = []
    seen_stem: set[str] = set()
    seen_doi: set[str] = set()
    for rec in records:
        effect = pick_primary_effect(rec.effects)
        if not effect:
            continue
        if (effect.ci_high - effect.ci_low) > 1.2:
            continue
        if rec.study_design in {
            "systematic_review",
            "observational",
            "qualitative",
            "policy_guidance",
            "guideline",
            "trial_registry",
        } and not is_named_outcome_trial(rec.title, rec.doi):
            continue
        label = short_study_label(rec.title, rec.doi, rec.year)
        stem = label.split("(")[0].strip().lower()
        doi_key = (rec.doi or "").lower()
        if stem in seen_stem or (doi_key and doi_key in seen_doi):
            continue
        seen_stem.add(stem)
        if doi_key:
            seen_doi.add(doi_key)
        rows.append(
            {
                "citation_id": rec.citation_id,
                "label": label,
                "year": rec.year,
                "metric": effect.metric,
                "value": effect.value,
                "ci_low": effect.ci_low,
                "ci_high": effect.ci_high,
                "outcome": effect.outcome,
                "excerpt": effect.excerpt,
                "doi": rec.doi,
            }
        )
    rows.sort(key=lambda r: (r["value"], r["year"] or 0))
    return rows[:18]


def pooled_effects(forest: list[dict]) -> dict | None:
    """Inverse-variance summary of already-parsed named-trial CIs.

    This is a transparency calculation on the forest rows, not a de-novo
    full-text meta-analysis. Missing CIs are never filled in.
    """
    weights: list[float] = []
    logs: list[float] = []
    funnel: list[dict] = []
    for row in forest or []:
        metric = str(row.get("metric") or "HR").upper()
        if metric != "HR":
            continue
        try:
            value = float(row["value"])
            lo = float(row["ci_low"])
            hi = float(row["ci_high"])
        except (KeyError, TypeError, ValueError):
            continue
        if value <= 0 or lo <= 0 or hi <= lo:
            continue
        se = (math.log(hi) - math.log(lo)) / (2 * 1.96)
        if se <= 0:
            continue
        weight = 1.0 / (se * se)
        log_hr = math.log(value)
        weights.append(weight)
        logs.append(log_hr)
        funnel.append(
            {
                "citation_id": row.get("citation_id"),
                "label": row.get("label"),
                "value": round(value, 4),
                "log_effect": round(log_hr, 4),
                "se": round(se, 4),
                "precision": round(1.0 / se, 4),
                "weight": round(weight, 4),
            }
        )
    if not weights:
        return None
    total_w = sum(weights)
    pooled_log = sum(w * x for w, x in zip(weights, logs)) / total_w
    se_p = math.sqrt(1.0 / total_w)
    q = sum(w * (x - pooled_log) ** 2 for w, x in zip(weights, logs))
    k = len(weights)
    i2 = 0.0
    if q > 0 and k > 1:
        i2 = max(0.0, (q - (k - 1)) / q * 100.0)
    return {
        "method": (
    "Fixed-effect inverse-variance of parsed named-trial hazard-ratio 95% CIs. "
            "Not a de-novo full-text meta-analysis; CIs are never invented."
        ),
        "n_trials": k,
        "metric": "HR",
        "value": round(math.exp(pooled_log), 3),
        "ci_low": round(math.exp(pooled_log - 1.96 * se_p), 3),
        "ci_high": round(math.exp(pooled_log + 1.96 * se_p), 3),
        "i_squared": round(i2, 1),
        "q": round(q, 2),
        "funnel": funnel,
    }


def qualitative(records: list[EvidenceRecord], cohort: str) -> dict:
    q_recs = [r for r in records if r.is_qualitative]
    theme_papers: dict[str, list[EvidenceRecord]] = defaultdict(list)
    theme_quotes: dict[str, list[dict]] = defaultdict(list)
    # IPA is applied only to papers with qualitative method markers.
    # Trial/guideline abstracts are never mined for "lived experience".
    pool = q_recs
    for rec in pool:
        blob = rec.text_blob()
        themes = ipa_hits(blob)
        for theme in themes:
            theme_papers[theme].append(rec)
            for sent in sentences(blob)[:8]:
                if any(
                    __import__("re").search(n, sent, __import__("re").I)
                    for n in IPA_CODEBOOK[theme]["needles"]
                ):
                    theme_quotes[theme].append(
                        {
                            "citation_id": rec.citation_id,
                            "text": sent[:280],
                        }
                    )
                    break
    superordinate = []
    for theme_id, spec in IPA_CODEBOOK.items():
        papers = theme_papers.get(theme_id) or []
        quotes = (theme_quotes.get(theme_id) or [])[:5]
        if not papers and not quotes:
            continue
        ids = sorted({p.citation_id for p in papers if p.citation_id})
        superordinate.append(
            {
                "id": theme_id,
                "title": spec["title"],
                "description": spec["description"],
                "n_papers": len({p.key for p in papers}),
                "citation_ids": ids,
                "evidence_extracts": quotes,
                "analytic_memo": (
                    f"Second-order IPA construct for {cohort}: {spec['title'].lower()}. "
                    "Extracts are verbatim clauses from validated abstracts, not invented quotes."
                ),
            }
        )
    superordinate.sort(key=lambda t: -t["n_papers"])

    narrative_papers = q_recs[:12] or records[:8]
    bullets = []
    for rec in narrative_papers:
        snip = rec.snippets[0] if rec.snippets else (sentences(rec.abstract)[:1] or [rec.title])
        bullets.append(
            {
                "citation_id": rec.citation_id,
                "title": rec.title,
                "point": snip[0] if isinstance(snip, list) else snip,
            }
        )
    return {
        "method_note": (
            "Qualitative synthesis uses two layers. (1) Narrative review of "
            "on-topic qualitative and mixed-methods papers retrieved from the "
            "live search. (2) IPA-informed coding of experiential language in "
            "those papers: first-order (authors' wording in abstracts) and "
            "second-order (superordinate themes). IPA is applied only to "
            "validated sources; no interview transcripts were fabricated."
        ),
        "n_qualitative_papers": len(q_recs),
        "narrative_review": {
            "summary": (
                f"Across {len(q_recs)} qualitative sources (of {len(records)} "
                f"validated records) for {cohort}, themes are coded only from "
                "papers with qualitative method markers. Trial and guideline "
                "abstracts are excluded from IPA. Each statement below is tied "
                "to a numbered, registry-validated citation."
                if q_recs
                else (
                    f"No qualitative method papers survived screening for {cohort}. "
                    "IPA themes are therefore empty rather than inferred from RCTs "
                    "or guidelines. Each narrative point below is still a numbered, "
                    "registry-validated citation."
                )
            ),
            "points": bullets,
        },
        "ipa": {
            "superordinate_themes": superordinate,
        },
    }


def insights(records: list[EvidenceRecord], quantitative_block: dict, brief: dict) -> dict:
    freq = quantitative_block.get("claim_frequency") or []
    top = freq[:5]
    cohort = brief.get("indication") or brief.get("therapy_area") or "the target cohort"
    benefits = [
        c
        for c in freq
        if c["id"]
        in {
            "mortality_or_hospitalisation_benefit",
            "guideline_directed_foundational_therapy",
            "symptom_or_quality_of_life",
            "early_or_in_hospital_initiation",
        }
    ]
    barriers = [
        c
        for c in freq
        if c["id"]
        in {
            "cost_or_access_barrier",
            "implementation_gap_or_inertia",
            "safety_hypotension_or_renal",
            "lived_experience_or_care_relationship",
        }
    ]
    gaps = []
    present = {c["id"] for c in freq}
    if "lmics_or_national_context" not in present:
        gaps.append(
            "National / LMIC evidence is thin relative to high-income guideline literature."
        )
    if "cost_or_access_barrier" not in present:
        gaps.append(
            "Cost and access are under-represented in the retrieved abstracts; "
            "health-economic retrieval should be expanded."
        )
    if quantitative_block.get("qualitative_share", {}).get("qualitative", 0) < 3:
        gaps.append(
            "Few IPA-eligible qualitative papers survived screening; patient/HCP "
            "voice should be commissioned or searched in specialist journals."
        )
    return {
        "cohort": cohort,
        "prevalent_supporting_facts": top,
        "prevalent_benefits": benefits[:4],
        "prevalent_barriers": barriers[:4],
        "novel_angles": [
            "Cross-walk UN/WHO NCD packages with specialty-society GDMT to locate "
            "primary-care vs specialist implementation gaps.",
            "Treat cost/access and lived-experience themes as equally evidential "
            "as effect sizes when designing HCP behaviour-change campaigns.",
            "Use only registry-validated citations in the evidence deck so MLR "
            "review starts from a defensible reference list.",
        ],
        "gaps": gaps,
    }
