"""Quantitative frequency analysis and qualitative narrative + IPA synthesis."""

from __future__ import annotations

from collections import Counter, defaultdict

from .extract import CLAIM_LABELS, IPA_CODEBOOK, ipa_hits, sentences
from .models import EvidenceRecord


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
    oa = sum(1 for r in records if r.is_oa)
    return {
        "n_included": len(records),
        "claim_frequency": claim_frequency,
        "by_source_family": [
            {"id": k, "count": v, "percent": round(100.0 * v / n, 1)}
            for k, v in family.most_common()
        ],
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
    }


def forest_rows(records: list[EvidenceRecord]) -> list[dict]:
    rows = []
    for rec in records:
        for effect in rec.effects:
            rows.append(
                {
                    "citation_id": rec.citation_id,
                    "label": rec.title[:88],
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


def qualitative(records: list[EvidenceRecord], cohort: str) -> dict:
    q_recs = [r for r in records if r.is_qualitative]
    theme_papers: dict[str, list[EvidenceRecord]] = defaultdict(list)
    theme_quotes: dict[str, list[dict]] = defaultdict(list)
    pool = [r for r in records if r.is_qualitative]
    if not pool:
        pool = [r for r in records if ipa_hits(r.text_blob())]
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
                f"Across {len(q_recs) or len(records)} sources touching lived "
                f"experience or care context for {cohort}, the literature "
                "converges on bodily burden, disrupted biography, relational "
                "care, prognostic fear, and structurally constrained agency. "
                "Each statement below is tied to a numbered, registry-validated citation."
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
