"""Validated, cited evidence that sets the campaign lead.

Client briefs never contain paper links. Science is sourced from (1) a curated
catalog when the product/class in the brief matches a published trial, and
(2) a live PubMed search on the product, indication, and therapy area.
Uncited brief items stay gaps. PubMed hits become numbered records with PMID/DOI
but never receive an invented effect size.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from .extract import ExtractedBrief
from .paper_read import apply_reading, assign_paper_jobs, fetch_abstracts, select_papers

# Curated, published anchors. Effect sizes are taken from the cited paper.
# Do not add a row here unless DOI or PMID is real.
CATALOG: list[dict[str, Any]] = [
    {
        "id": "paradigm-hf-2014",
        "stream": "Brand / pivotal",
        "trial": "PARADIGM-HF",
        "short": "PARADIGM-HF 2014",
        "title": "Angiotensin–neprilysin inhibition versus enalapril in heart failure",
        "authors": "McMurray JJV, Packer M, Desai AS, et al.",
        "year": 2014,
        "journal": "N Engl J Med",
        "pages": "371:993-1004",
        "doi": "10.1056/NEJMoa1409077",
        "pmid": "25176015",
        "design": "RCT, double-blind",
        "n": 8442,
        "population": "HFrEF, NYHA II–IV, vs enalapril",
        "endpoint": "CV death or HF hospitalisation",
        "effect_metric": "HR",
        "hr": 0.80,
        "low": 0.73,
        "high": 0.87,
        "grade": "A",
        "claim_permitted": "ARNI reduced the primary composite vs ACE inhibitor in HFrEF.",
        "caveat": "Run-in design; hypotension and angioedema require labelled monitoring.",
        "mlr": "Use only inside local label. Quote the composite, not a cherry-picked arm.",
        "tags": ("hfref", "arni", "sacubitril", "valsartan", "cardiology", "heart failure", "paradigm"),
        "directs": "outcome-permission",
        "control_event": 26.5,
        "treat_event": 21.8,
        "arr": 4.7,
        "nnt": 21,
        "horizon": "median 27 months",
        "visual_unit": "CV death or HF hospitalisation per 100 patients",
        "spine_means": "Treat 21 patients like these to prevent 1 death or HF hospitalisation over ~27 months — that is the clinical prize.",
        "spine_barrier": "The prize is lost if start waits until the outpatient clinic.",
        "spine_execute": "First-Touch Protocol: initiate at first-eligible, not first-available.",
        "spine_measure": "Share of eligible starts inside 48 hours of first-eligible.",
    },
    {
        "id": "pioneer-hf-2019",
        "stream": "Evolving / initiation",
        "trial": "PIONEER-HF",
        "short": "PIONEER-HF 2019",
        "title": "Angiotensin–neprilysin inhibition in acute decompensated heart failure",
        "authors": "Velazquez EJ, Morrow DA, DeVore AD, et al.",
        "year": 2019,
        "journal": "N Engl J Med",
        "pages": "380:539-548",
        "doi": "10.1056/NEJMoa1812851",
        "pmid": "30415601",
        "design": "RCT, in-hospital initiation",
        "n": 881,
        "population": "HFrEF stabilised after acute decompensation",
        "endpoint": "Time-averaged proportional change in NT-proBNP",
        "effect_metric": "ratio",
        "hr": 0.71,
        "low": 0.63,
        "high": 0.81,
        "grade": "A",
        "claim_permitted": "In-hospital initiation after haemodynamic stabilisation is feasible and lowers NT-proBNP vs ACE inhibitor.",
        "caveat": "Primary endpoint is a biomarker, not mortality. Safety was comparable.",
        "mlr": "Do not imply a new mortality claim from PIONEER-HF alone.",
        "tags": ("hfref", "arni", "sacubitril", "in-hospital", "early", "initiation", "pioneer", "cardiology"),
        "directs": "first-eligible-start",
        "control_event": 100,
        "treat_event": 71,
        "arr": 29,
        "nnt": None,
        "horizon": "in-hospital window",
        "visual_unit": "NT-proBNP remaining vs ACEI baseline (=100)",
        "spine_means": "In-hospital start is a larger decongestive effect, not a later-clinic convenience.",
        "spine_barrier": "Ward-to-clinic handoff delays the only window that showed the NT-proBNP drop.",
        "spine_execute": "First-Touch Protocol + 48-hour eligible-start KPI.",
        "spine_measure": "NT-proBNP delta at 8 weeks among in-hospital starters vs clinic starters.",
    },
    {
        "id": "transition-2019",
        "stream": "Evolving / initiation",
        "trial": "TRANSITION",
        "short": "TRANSITION 2019",
        "title": "Initiation of sacubitril/valsartan in hospital or early after discharge",
        "authors": "Wachter R, Senni M, Belohlavek J, et al.",
        "year": 2019,
        "journal": "Eur J Heart Fail",
        "pages": "21:998-1007",
        "doi": "10.1002/ejhf.1498",
        "pmid": "31134724",
        "design": "RCT, open-label timing",
        "n": 1002,
        "population": "HFrEF after acute decompensation",
        "endpoint": "Proportion achieving target dose at 10 weeks",
        "effect_metric": "risk difference",
        "hr": 0.95,
        "low": 0.88,
        "high": 1.03,
        "grade": "B",
        "claim_permitted": "Pre-discharge and early post-discharge initiation both reach target dose; the 'wait to start' ritual is not required for titration success.",
        "caveat": "Open-label; primary was dose attainment, not outcomes.",
        "mlr": "Use as feasibility evidence, not as an outcomes claim.",
        "tags": ("hfref", "arni", "transition", "discharge", "early", "cardiology"),
        "directs": "first-eligible-start",
        "spine_means": "Waiting until the clinic is not required for titration success.",
        "spine_barrier": "The start-after-discharge habit still treats in-hospital initiation as optional.",
        "spine_execute": "First-Touch Protocol: pre-discharge start is a designed default.",
        "spine_measure": "Share of eligible patients leaving hospital on the foundational ARNI.",
    },
    {
        "id": "jhund-age-2015",
        "stream": "Brand / post-hoc",
        "trial": "PARADIGM-HF age analysis",
        "short": "Jhund 2015 age",
        "title": "Efficacy and safety of LCZ696 (sacubitril-valsartan) according to age",
        "authors": "Jhund PS, Fu M, Bayram E, et al.",
        "year": 2015,
        "journal": "Eur Heart J",
        "pages": "36:2576-2584",
        "doi": "10.1093/eurheartj/ehv330",
        "pmid": "26231885",
        "design": "Pre-specified subgroup of RCT",
        "n": 8442,
        "population": "PARADIGM-HF by age decade",
        "endpoint": "Primary composite, consistent across age",
        "effect_metric": "HR",
        "hr": 0.81,
        "low": 0.74,
        "high": 0.89,
        "grade": "B",
        "claim_permitted": "Benefit vs enalapril was consistent in older patients; age alone is not a reason to delay.",
        "caveat": "Subgroup analysis; hypotension more frequent in the elderly.",
        "mlr": "Flag as post-hoc/subgroup. Do not invent an elderly-only indication.",
        "tags": ("hfref", "arni", "elderly", "age", "cardiology"),
        "directs": "segment-confidence",
        "spine_means": "Age is not a reason to withhold the outcome benefit.",
        "spine_barrier": "Older patients are left on ACEI 'to be safe'.",
        "spine_execute": "Myth-Reset Asset: one wrong belief, one number, one peer voice.",
        "spine_measure": "Unaided 'too old / too frail to start' prevalence in the next insight wave.",
    },
    {
        "id": "esc-hf-2021",
        "stream": "Guideline",
        "trial": "ESC HF 2021",
        "short": "ESC 2021 Class I",
        "title": "2021 ESC Guidelines for the diagnosis and treatment of acute and chronic heart failure",
        "authors": "McDonagh TA, Metra M, Adamo M, et al.",
        "year": 2021,
        "journal": "Eur Heart J",
        "pages": "42:3599-3726",
        "doi": "10.1093/eurheartj/ehab368",
        "pmid": "34447992",
        "design": "Society guideline",
        "n": None,
        "population": "HFrEF",
        "endpoint": "Class I recommendation for ARNI as foundational therapy",
        "effect_metric": "class",
        "hr": None,
        "low": None,
        "high": None,
        "grade": "A",
        "claim_permitted": "ESC gives Class I cover for ARNI in HFrEF. Early foundational therapy is the guideline position, not a brand slogan.",
        "caveat": "Local label and national adaptation (e.g. CSI) still govern promotion.",
        "mlr": "Quote recommendation class, not a promotional paraphrase.",
        "tags": ("hfref", "arni", "guideline", "esc", "cardiology", "heart failure"),
        "directs": "guideline-cover",
        "spine_means": "Class I is cover to start now, not a poster to quote after a delay.",
        "spine_barrier": "Guideline awareness without a pathway still produces late starts.",
        "spine_execute": "Peer Cascade: KOLs author the first-eligible protocol the guideline already permits.",
        "spine_measure": "Share of priority KOLs who have signed the first-eligible protocol.",
    },
    {
        "id": "aha-acc-hfsa-2022",
        "stream": "Guideline",
        "trial": "AHA/ACC/HFSA 2022",
        "short": "AHA/ACC/HFSA 2022",
        "title": "2022 AHA/ACC/HFSA Guideline for the Management of Heart Failure",
        "authors": "Heidenreich PA, Bozkurt B, Aguilar D, et al.",
        "year": 2022,
        "journal": "Circulation",
        "pages": "145:e895-e1032",
        "doi": "10.1161/CIR.0000000000001063",
        "pmid": "35363499",
        "design": "Society guideline",
        "n": None,
        "population": "HFrEF — four-pillar GDMT",
        "endpoint": "ARNI (or ACEI/ARB) as one of four foundational pillars",
        "effect_metric": "class",
        "hr": None,
        "low": None,
        "high": None,
        "grade": "A",
        "claim_permitted": "US guideline places ARNI in foundational four-pillar therapy, not as a late switch after 'stabilisation theatre'.",
        "caveat": "Pillar choice still follows label, tolerance, and access.",
        "mlr": "Do not imply all four pillars must start on day one if the label sequences them.",
        "tags": ("hfref", "arni", "guideline", "acc", "aha", "hfsa", "four-pillar", "cardiology"),
        "directs": "guideline-cover",
        "spine_means": "ARNI sits in foundational four-pillar therapy, not as a late switch.",
        "spine_barrier": "Four-pillar talk without a first-touch pathway still sequences ARNI last.",
        "spine_execute": "Peer Cascade + First-Touch: the pathway is how a Class I line becomes a start.",
        "spine_measure": "Share of hospital pathways that name ARNI at first-eligible, not at switch.",
    },
    {
        "id": "trivandrum-hf-2015",
        "stream": "Independent / epidemiology",
        "trial": "Trivandrum HF Registry",
        "short": "Trivandrum HFR 2015",
        "title": "Clinical presentation, management, in-hospital and 90-day outcomes of heart failure patients in Trivandrum, Kerala, India",
        "authors": "Harikrishnan S, Sanjay G, Anees T, et al.",
        "year": 2015,
        "journal": "Eur J Heart Fail",
        "pages": "17:794-800",
        "doi": "10.1002/ejhf.283",
        "pmid": "26011246",
        "design": "Prospective registry",
        "n": 1205,
        "population": "Indian HF admissions; younger onset than Western cohorts",
        "endpoint": "In-hospital and 90-day outcomes; GDMT underuse",
        "effect_metric": None,
        "hr": None,
        "low": None,
        "high": None,
        "grade": "B",
        "claim_permitted": "Indian HF presents younger and with incomplete GDMT — local epidemiology supports a first-touch, not a Western 'wait and see', posture.",
        "caveat": "Single-region registry; not a product trial.",
        "mlr": "Epidemiology only. No product claim.",
        "tags": ("india", "registry", "hf", "epidemiology", "cardiology", "indian"),
        "directs": "local-context",
    },
    {
        "id": "keynote-189-2018",
        "stream": "Independent / pivotal class",
        "trial": "KEYNOTE-189",
        "short": "KEYNOTE-189 2018",
        "title": "Pembrolizumab plus chemotherapy in metastatic non–small-cell lung cancer",
        "authors": "Gandhi L, Rodríguez-Abreu D, Gadgeel S, et al.",
        "year": 2018,
        "journal": "N Engl J Med",
        "pages": "378:2078-2092",
        "doi": "10.1056/NEJMoa1801005",
        "pmid": "29658856",
        "design": "RCT",
        "n": 616,
        "population": "Metastatic nonsquamous NSCLC, first-line, no EGFR/ALK",
        "endpoint": "Overall survival",
        "effect_metric": "HR",
        "hr": 0.49,
        "low": 0.38,
        "high": 0.64,
        "grade": "A",
        "claim_permitted": "First-line PD-1 plus platinum pemetrexed improved OS vs chemo alone.",
        "caveat": "IO-chemo cost and toxicity are the access problem, not the OS signal.",
        "mlr": "Stay inside the exact labelled combination and line of therapy.",
        "tags": ("nsclc", "oncology", "lung", "pembrolizumab", "io", "keynote"),
        "directs": "outcome-permission",
        "control_event": 50.6,
        "treat_event": 30.8,
        "arr": 19.8,
        "nnt": 5,
        "horizon": "12-month OS complement (published OS 69.2% vs 49.4%)",
        "visual_unit": "deaths per 100 patients at 12 months",
        "spine_means": "About 1 in 5 extra patients is alive at 12 months versus chemo alone.",
        "spine_barrier": "PD-L1-first sequencing can withhold the combination that produced the OS gain.",
        "spine_execute": "Biomarker-last sequencing so combination is not delayed for a test result.",
        "spine_measure": "Share of eligible patients starting combination before a PD-L1 wait.",
    },
    {
        "id": "keynote-024-2016",
        "stream": "Independent / pivotal class",
        "trial": "KEYNOTE-024",
        "short": "KEYNOTE-024 2016",
        "title": "Pembrolizumab versus chemotherapy for PD-L1–positive non–small-cell lung cancer",
        "authors": "Reck M, Rodríguez-Abreu D, Robinson AG, et al.",
        "year": 2016,
        "journal": "N Engl J Med",
        "pages": "375:1823-1833",
        "doi": "10.1056/NEJMoa1606774",
        "pmid": "27718847",
        "design": "RCT",
        "n": 305,
        "population": "NSCLC, PD-L1 TPS ≥50%, first-line",
        "endpoint": "Progression-free survival",
        "effect_metric": "HR",
        "hr": 0.50,
        "low": 0.37,
        "high": 0.68,
        "grade": "A",
        "claim_permitted": "Pembrolizumab monotherapy improved PFS vs platinum chemo in high PD-L1 first-line NSCLC.",
        "caveat": "Restricted to TPS ≥50%.",
        "mlr": "Do not generalise to all-comer first-line.",
        "tags": ("nsclc", "oncology", "lung", "pembrolizumab", "pd-l1", "keynote"),
        "directs": "outcome-permission",
    },
]


def resolve_evidence(brief: ExtractedBrief, *, pubmed: bool = True) -> dict[str, Any]:
    """Find citable papers for this brief. The brief is not expected to list them."""
    blob = _brief_blob(brief)
    matched: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in CATALOG:
        if _matches(entry, brief, blob):
            rec = _record(entry, status="validated", matched_from="catalog")
            matched.append(rec)
            seen.add(entry["id"])

    pubmed_hits: list[dict[str, Any]] = []
    if pubmed:
        pubmed_hits = _pubmed_enrich(brief, seen)
        if len(matched) < 3:
            pmids = [str(h.get("pmid") or "") for h in pubmed_hits if h.get("pmid")]
            readings = fetch_abstracts(pmids) if pmids else {}
            chosen = select_papers(pubmed_hits, brief, readings, limit=4)
            catalog_pmids = {str(r.get("pmid") or "") for r in matched}
            for hit in chosen:
                pmid = str(hit.get("pmid") or "")
                if pmid and pmid in catalog_pmids:
                    continue
                rec = _pubmed_as_record(hit)
                rec = apply_reading(rec, readings.get(pmid), brief)
                matched.append(rec)
                if pmid:
                    catalog_pmids.add(pmid)

    assign_paper_jobs(matched, brief)
    gaps = _uncited_brief_items(brief, matched)
    lead = _campaign_lead(brief, matched)
    return {
        "lead": lead,
        "records": matched,
        "gaps": gaps,
        "pubmed": pubmed_hits,
        "validatedCount": sum(1 for r in matched if r.get("status") == "validated"),
        "gapCount": len(gaps),
    }


def _brief_blob(brief: ExtractedBrief) -> str:
    parts = [
        brief.brand,
        brief.product,
        brief.therapy_area,
        brief.indication,
        brief.market,
        brief.business_goal,
        brief.raw_text,
        " ".join(brief.brand_evidence),
        " ".join(brief.existing_evidence),
        " ".join(brief.evolving_evidence),
        " ".join(brief.guidelines),
        " ".join(brief.hcp_insights),
    ]
    return " ".join(p for p in parts if p).lower()


GENERIC_TAGS = {
    "india",
    "indian",
    "registry",
    "guideline",
    "early",
    "initiation",
    "age",
    "elderly",
    "discharge",
    "epidemiology",
    "cardiology",
}

CLASS_TOKENS = {
    "hf": (
        "arni",
        "sacubitril",
        "valsartan",
        "paradigm",
        "pioneer",
        "lcz696",
        "entresto",
        "transition",
    ),
    "oncology": (
        "pembrolizumab",
        "keynote",
        "pd-l1",
        "pd-1",
        "nsclc",
        "immuno",
    ),
}


def _contains_term(term: str, blob: str) -> bool:
    """Whole-term match so 'late' does not fire inside 'related' / 'template'."""
    term = (term or "").lower().strip()
    blob = blob or ""
    if not term:
        return False
    if " " in term or "/" in term or "-" in term:
        return term in blob
    return bool(re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", blob))


def _matches(entry: dict[str, Any], brief: ExtractedBrief, blob: str) -> bool:
    """Attach a catalog paper only when this brief is actually about that science.

    Geography tags like 'india' and the word 'cardiology' are not enough to hang
    PARADIGM-HF on an unrelated upload. The CardioShield demo still matches
    because its product and evidence lines name ARNI / sacubitril / PARADIGM.
    """
    tags = tuple(str(t).lower() for t in (entry.get("tags") or ()))
    family = _catalog_family(tags)
    brief_family = _brief_family(brief, blob)
    if family and brief_family != family:
        return False

    trial = (entry.get("trial") or "").lower()
    if len(trial) >= 6 and trial in blob:
        return True
    pmid = str(entry.get("pmid") or "")
    if pmid and pmid in blob:
        return True
    doi = (entry.get("doi") or "").lower()
    if doi and doi in blob:
        return True

    if entry.get("directs") == "local-context" and family and family == brief_family:
        market = (brief.market or "").lower()
        return any(_contains_term(g, blob) or _contains_term(g, market) for g in ("india", "indian"))

    class_tokens = CLASS_TOKENS.get(family or "", ())
    class_hit = any(_contains_term(t, blob) for t in class_tokens)
    distinctive = [t for t in tags if t not in GENERIC_TAGS and len(t) >= 4]
    tag_hits = sum(1 for t in distinctive if _contains_term(t, blob))
    if class_hit and tag_hits >= 1:
        return True

    if family and family == brief_family:
        societies = ("esc", "acc", "aha", "hfsa", "csi")
        if any(_contains_term(name, blob) for name in societies if name in tags):
            return class_hit or _contains_term("heart failure", blob) or _contains_term("nsclc", blob)
    return False


def _catalog_family(tags) -> str:
    tagset = {str(t).lower() for t in tags}
    joined = " ".join(tagset)
    if tagset & {"hfref", "arni", "paradigm", "pioneer", "hf"} or "heart failure" in joined:
        return "hf"
    if tagset & {"nsclc", "oncology", "pembrolizumab", "keynote"}:
        return "oncology"
    if "cardiology" in tagset:
        return "hf"
    return ""


def _brief_family(brief: ExtractedBrief, blob: str) -> str:
    ta = f"{brief.therapy_area} {brief.indication} {brief.product} {blob}".lower()
    if any(
        _contains_term(k, ta)
        for k in ("hfref", "arni", "sacubitril", "paradigm")
    ) or "heart failure" in ta:
        return "hf"
    if any(
        _contains_term(k, ta)
        for k in ("nsclc", "pembrolizumab", "keynote")
    ) or "lung cancer" in ta or _contains_term("oncology", ta):
        return "oncology"
    return ""


def _record(entry: dict[str, Any], *, status: str, matched_from: str) -> dict[str, Any]:
    doi = entry.get("doi") or ""
    pmid = str(entry.get("pmid") or "")
    url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else (f"https://doi.org/{doi}" if doi else "")
    citation = (
        f"{entry['authors']} {entry['title']}. {entry['journal']}. {entry['year']};{entry['pages']}. "
        f"doi:{doi}" + (f". PMID {pmid}" if pmid else "")
    )
    return {
        **{k: entry.get(k) for k in (
            "id", "stream", "trial", "short", "title", "authors", "year", "journal",
            "pages", "doi", "pmid", "design", "n", "population", "endpoint",
            "effect_metric", "hr", "low", "high", "grade", "claim_permitted",
            "caveat", "mlr", "directs", "control_event", "treat_event", "arr",
            "nnt", "horizon", "visual_unit", "spine_means", "spine_barrier",
            "spine_execute", "spine_measure",
        )},
        "citation": citation,
        "url": url,
        "status": status,
        "matchedFrom": matched_from,
    }


def _uncited_brief_items(brief: ExtractedBrief, matched: list[dict]) -> list[dict[str, Any]]:
    """Brief-only items that did not resolve to a DOI/PMID stay as research gaps."""
    cited_blob = " ".join(
        f"{r.get('trial', '')} {r.get('short', '')} {r.get('title', '')}".lower()
        for r in matched
    )
    gaps = []
    for stream, items in (
        ("Brand-generated", brief.brand_evidence),
        ("Independent", brief.existing_evidence),
        ("Evolving", brief.evolving_evidence),
        ("Guideline", brief.guidelines),
    ):
        for item in items:
            key = item.lower()
            if any(token in cited_blob for token in _tokens(key) if len(token) > 4):
                continue
            if any(token in key for token in ("paradigm", "pioneer", "transition", "esc", "acc/aha", "hfsa", "keynote")):
                continue
            gaps.append({
                "stream": stream,
                "item": item,
                "status": "unvalidated",
                "needed": "Retrieve the primary paper or registry report; do not promote until a DOI/PMID is on the ledger.",
            })
    return gaps


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9-]{3,}", text.lower())


def _campaign_lead(brief: ExtractedBrief, matched: list[dict]) -> dict[str, Any]:
    if not matched:
        return {
            "statement": (
                "No citable paper was retrieved for this product/indication yet. "
                "Do not lock a scientific lead. The brief is not expected to contain paper links — "
                "we search PubMed from the product and therapy area."
            ),
            "why": "The working file has no DOI/PMID-backed row. Strategy stays behavioural until science is sourced.",
            "directs": "none",
            "citations": [],
            "doNotClaim": ["Any efficacy, safety, or guideline class statement"],
        }

    catalog = [r for r in matched if r.get("matchedFrom") == "catalog" or r.get("status") == "validated"]
    pubmed_recs = [r for r in matched if r.get("matchedFrom") == "pubmed"]
    catalog_core = [r for r in catalog if r.get("directs") != "local-context"]
    pool = catalog_core or pubmed_recs or catalog or matched
    by_id = {r["id"]: r for r in pool}
    preferred = [
        "pioneer-hf-2019",
        "transition-2019",
        "esc-hf-2021",
        "paradigm-hf-2014",
        "aha-acc-hfsa-2022",
        "keynote-189-2018",
        "keynote-024-2016",
    ]
    anchors = [by_id[i] for i in preferred if i in by_id]
    if not anchors:
        ranked = sorted(pool, key=_lead_sort_key)
        usable = [r for r in ranked if _usable_finding(r)]
        anchors = usable or ranked
    if not catalog_core:
        role_rank = {
            "placebo-controlled": 0,
            "first-eligible-start": 0,
            "head-to-head": 1,
            "durability": 2,
            "guideline-cover": 3,
            "replication": 4,
        }
        anchors = sorted(
            anchors,
            key=lambda r: (role_rank.get(r.get("role") or "", 8), _lead_sort_key(r)),
        )

    primary = anchors[0]
    support = anchors[1:4]
    if catalog_core and primary["id"] in {"pioneer-hf-2019", "transition-2019"} and "paradigm-hf-2014" in {r["id"] for r in catalog}:
        statement = (
            f"Lead the campaign with first-eligible / in-hospital initiation. "
            f"{primary['trial']} ({primary['year']}) shows that starting after haemodynamic "
            f"stabilisation is feasible; ESC/ACC Class I plus PARADIGM-HF are the outcome permission — "
            f"not a reason to wait for a second clinic visit."
        )
        directs = "first-eligible-start"
    elif catalog_core and primary["id"].startswith("keynote"):
        statement = (
            f"Lead with the first-line survival evidence in {primary['trial']} "
            f"(PMID {primary['pmid']}). Cost is an access problem sitting on top of settled science, "
            f"not a reason to soften the efficacy lead."
        )
        directs = "outcome-permission"
    elif not catalog_core:
        tension = (brief.hcp_insights or brief.access_and_cost or [brief.business_goal] or [""])[0]
        bits = []
        for rec in anchors[:4]:
            finding = rec.get("finding") or rec.get("claim_permitted") or rec.get("title") or ""
            label = rec.get("roleLabel") or rec.get("trial") or rec.get("short") or "Paper"
            bits.append(
                f"{label} — {_clip_lead(finding, 180)} (PMID {rec.get('pmid') or '—'})."
            )
        statement = " ".join(bits) if bits else (
            f"{primary.get('finding') or primary.get('claim_permitted') or primary.get('title') or ''} "
            f"(PMID {primary.get('pmid') or '—'})."
        )
        statement += " Each numbered paper owns one line — we do not reprint the same finding."
        if tension:
            statement += (
                f" The brief's conversion problem is “{_clip_lead(tension)}”. "
                "We spend against that behaviour, using the set."
            )
        directs = primary.get("directs") or "outcome-permission"
    else:
        statement = (
            f"Lead with {primary['short']}: {primary['claim_permitted']}"
        )
        directs = primary.get("directs") or "outcome-permission"

    citations = [primary, *support]
    return {
        "statement": statement,
        "why": (
            f"{len(citations)} numbered paper{'s' if len(anchors[:4]) != 1 else ''} carry the science"
            + (f", led by {primary.get('short')}" if primary.get("short") else "")
            + f" (PMID {primary.get('pmid') or '—'})."
        ),
        "directs": directs,
        "primaryId": primary["id"],
        "citations": [
            {
                "id": c["id"],
                "short": c.get("short") or c.get("title") or c["id"],
                "pmid": c.get("pmid"),
                "doi": c.get("doi"),
                "citation": c.get("citation") or "",
                "claim": c.get("claim_permitted") or c.get("claim") or "",
            }
            for c in citations
        ],
        "doNotClaim": list(dict.fromkeys(
            [c for c in (
                primary.get("caveat") or "",
                *(s.get("caveat") or "" for s in support),
                "Do not add a number that is not in the cited abstract or full text.",
            ) if c]
        )),
    }


def _clip_lead(text: str, limit: int = 160) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _usable_finding(row: dict) -> bool:
    claim = (row.get("finding") or row.get("claim_permitted") or "").strip()
    if not claim or claim.startswith("Abstract retrieved"):
        return False
    if row.get("hr") is not None or row.get("treat_event") is not None:
        return True
    title = re.sub(r"[^a-z0-9]+", " ", (row.get("title") or "").lower()).strip()
    body = re.sub(r"[^a-z0-9]+", " ", claim.lower()).strip()
    return bool(body) and body != title and len(claim) > 40


def _lead_sort_key(row: dict) -> tuple:
    numeric = 0 if (row.get("hr") is not None or row.get("treat_event") is not None) else 1
    paired = 0 if (row.get("treat_event") is not None and row.get("control_event") is not None) else 1
    title = f"{row.get('title') or ''} {row.get('design') or ''}".lower()
    ole = 1 if "extension" in title or "open-label" in title else 0
    grade = 0 if row.get("grade") == "A" else 1
    return (paired, numeric, ole, grade, -(row.get("year") or 0))


def _pubmed_as_record(hit: dict[str, Any]) -> dict[str, Any]:
    pmid = str(hit.get("pmid") or "")
    title = (hit.get("title") or "").rstrip(".")
    return {
        "id": hit.get("id") or (f"pmid-{pmid}" if pmid else f"pubmed-{abs(hash(title)) % 10**8}"),
        "stream": "Independent / PubMed",
        "trial": hit.get("trial") or "",
        "short": (title[:88] + ("…" if len(title) > 88 else "")) or f"PMID {pmid}",
        "title": hit.get("title") or "",
        "authors": hit.get("authors") or "",
        "year": hit.get("year"),
        "journal": hit.get("journal") or "",
        "pages": hit.get("pages") or "",
        "doi": hit.get("doi") or "",
        "pmid": pmid,
        "design": hit.get("design") or "PubMed record",
        "n": None,
        "population": "",
        "endpoint": "",
        "effect_metric": None,
        "hr": None,
        "low": None,
        "high": None,
        "grade": "retrieved",
        "claim_permitted": (hit.get("title") or "").rstrip(".") + ".",
        "caveat": hit.get("note") or (
            "Abstract not yet read. Confirm full text and local label before promotional use."
        ),
        "mlr": "Full-text and label check required before promotional use.",
        "directs": "pubmed-retrieved",
        "citation": hit.get("citation") or "",
        "url": hit.get("url") or (f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""),
        "status": "retrieved",
        "matchedFrom": "pubmed",
    }


def _pubmed_enrich(brief: ExtractedBrief, already: set[str]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    seen_pmids: set[str] = {str(e.get("pmid") or "") for e in CATALOG}
    for term in _pubmed_queries(brief):
        if len(hits) >= 8:
            break
        try:
            ids = _esearch(term, retmax=8)
            if not ids:
                continue
            summaries = _esummary(ids)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, ValueError):
            continue
        for pmid, doc in summaries.items():
            if pmid in seen_pmids:
                continue
            seen_pmids.add(pmid)
            title = doc.get("title") or ""
            journal = doc.get("fulljournalname") or doc.get("source") or ""
            year = _year(doc.get("pubdate") or "")
            authors = _author_line(doc.get("authors") or [])
            doi = _doi_from(doc)
            pubtypes = doc.get("pubtype") or []
            design = pubtypes[0] if pubtypes else "PubMed record"
            hits.append({
                "pmid": pmid,
                "title": title,
                "authors": authors,
                "year": year,
                "journal": journal,
                "doi": doi,
                "design": design,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                "citation": (
                    f"{authors} {title} {journal}. {year}."
                    + (f" doi:{doi}" if doi else f" PMID {pmid}")
                ),
                "status": "pubmed-retrieved",
                "note": (
                    "Independent PubMed hit for this product/indication. "
                    "Confirm against the full text before it can become a promotional claim."
                ),
            })
        if hits:
            break
    if not hits:
        return []
    product_tokens = [t for t in re.findall(r"[a-z0-9-]{5,}", (brief.product or "").lower())]
    if product_tokens:
        product_hits = [h for h in hits if any(t in (h.get("title") or "").lower() for t in product_tokens)]
        if product_hits:
            return product_hits[:8]
    relevant = [h for h in hits if _title_matches_brief(h.get("title") or "", brief)]
    return (relevant or hits)[:8]


def _pubmed_queries(brief: ExtractedBrief) -> list[str]:
    product = _clean_query_bit(brief.product)
    indication = _clean_query_bit(brief.indication)
    ta = _clean_query_bit(brief.therapy_area)
    brand = _clean_query_bit(brief.brand)
    focus = product or brand
    disease = indication or ta
    if not focus and not disease:
        return []
    core = " ".join(p for p in (focus, disease) if p).strip()
    if len(core) < 5:
        return []
    typed = (
        f"({core}) AND ("
        "randomized controlled trial[pt] OR clinical trial[pt] OR "
        "guideline[pt] OR meta-analysis[pt] OR systematic review[pt]"
        ")"
    )
    loose = f"({core}) AND (trial OR randomized OR guideline)"
    queries = []
    if product:
        queries.append(
            f"{product}[Title] AND ({disease or 'therapy'}) AND "
            "(randomized OR trial OR guideline OR meta-analysis)"
        )
    queries.append(typed)
    queries.append(loose)
    if product and disease and product.lower() not in disease.lower():
        queries.append(f"{product} {disease} randomized")
    out: list[str] = []
    for q in queries:
        if q not in out:
            out.append(q)
    return out


def _clean_query_bit(text: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9 +/()-]+", " ", text or "")
    return re.sub(r"\s+", " ", cleaned).strip()


def _title_matches_brief(title: str, brief: ExtractedBrief) -> bool:
    blob = title.lower()
    stop = {
        "chronic", "acute", "area", "therapy", "care", "disease", "the", "and",
        "for", "with", "from", "specialty", "launch", "campaign", "brief",
        "first", "line", "plus", "versus", "patients",
    }
    tokens = []
    for field in (brief.product, brief.indication, brief.therapy_area):
        tokens.extend(re.findall(r"[a-z0-9-]{4,}", (field or "").lower()))
    tokens = [t for t in tokens if t not in stop]
    if not tokens:
        return True
    return any(t in blob for t in tokens)


def _pubmed_term(brief: ExtractedBrief) -> str:
    queries = _pubmed_queries(brief)
    return queries[0] if queries else ""


def _ncbi_json(url: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "STRATA-director/1.0 (https://pubmed.ncbi.nlm.nih.gov/)"},
    )
    with urllib.request.urlopen(req, timeout=12) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _esearch(term: str, retmax: int = 8) -> list[str]:
    params = {
        "db": "pubmed",
        "retmode": "json",
        "retmax": str(retmax),
        "term": term,
        "sort": "relevance",
        "tool": "strata-director",
        "email": "strata-director@local",
    }
    api_key = os.environ.get("NCBI_API_KEY") or os.environ.get("PUBMED_API_KEY")
    if api_key:
        params["api_key"] = api_key
    data = _ncbi_json(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?{urllib.parse.urlencode(params)}")
    return list(data.get("esearchresult", {}).get("idlist") or [])


def _esummary(pmids: list[str]) -> dict[str, dict]:
    if not pmids:
        return {}
    params = {
        "db": "pubmed",
        "retmode": "json",
        "id": ",".join(pmids),
        "tool": "strata-director",
        "email": "strata-director@local",
    }
    api_key = os.environ.get("NCBI_API_KEY") or os.environ.get("PUBMED_API_KEY")
    if api_key:
        params["api_key"] = api_key
    data = _ncbi_json(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?{urllib.parse.urlencode(params)}")
    result = data.get("result") or {}
    return {pmid: result[pmid] for pmid in pmids if pmid in result}


def _author_line(authors: list) -> str:
    names = []
    for a in authors[:3]:
        name = a.get("name") if isinstance(a, dict) else str(a)
        if name:
            names.append(name)
    if len(authors) > 3:
        names.append("et al.")
    return ", ".join(names)


def _year(pubdate: str) -> int | None:
    m = re.search(r"(19|20)\d{2}", pubdate or "")
    return int(m.group(0)) if m else None


def _doi_from(doc: dict) -> str:
    for art in doc.get("articleids") or []:
        if art.get("idtype") == "doi":
            return art.get("value") or ""
    eloc = doc.get("elocationid") or ""
    if eloc.lower().startswith("doi:"):
        return eloc.split(":", 1)[1].strip()
    return ""
