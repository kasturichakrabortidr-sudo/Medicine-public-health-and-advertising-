"""Evidence ledger: catalog matches plus a live literature review.

The brief is a starting brief, not the literature. We always search PubMed
for this product and indication. Catalog rows with published effect sizes
attach only when this brief names that trial, molecule, PMID, or DOI — we
will not paste KEYNOTE onto a different brand as *its* pivotal.

If the brief named an INN (lumenolol, sacubitril, pembrolizumab), keep that
molecule's papers and drop another catalog molecule's pivotal.

If the brief is brand + therapy area only (HelixOne in NSCLC), run an
indication review: landmark RCTs, meta-analyses, and society guidelines of
the disease are in play, labelled Independent / indication landscape — not
a trial of this brand. Cross-therapy-area papers still stay off.

Effect sizes are copied only when the paper states them; they are never invented.
"""

from __future__ import annotations

import html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from .extract import ExtractedBrief

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
        "aliases": (
            "paradigm-hf",
            "paradigm hf",
            "sacubitril",
            "entresto",
            "lcz696",
            "arni",
            "neprilysin",
        ),
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
        "aliases": (
            "pioneer-hf",
            "pioneer hf",
            "sacubitril",
            "entresto",
            "lcz696",
            "arni",
        ),
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
        "aliases": (
            "transition 2019",
            "sacubitril",
            "entresto",
            "lcz696",
            "arni",
        ),
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
        "aliases": (
            "jhund",
            "paradigm-hf",
            "sacubitril",
            "entresto",
            "lcz696",
            "arni",
        ),
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
        "aliases": (
            "esc 2021",
            "esc hf",
            "esc heart failure",
            "esc guidelines",
            "esc guideline",
        ),
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
        "aliases": (
            "aha/acc/hfsa",
            "acc/aha/hfsa",
            "acc/aha",
            "aha acc hfsa",
            "hfsa 2022",
            "four-pillar",
            "four pillar",
        ),
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
        "aliases": ("trivandrum", "harikrishnan"),
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
        "aliases": (
            "keynote-189",
            "keynote 189",
            "pembrolizumab",
            "keytruda",
        ),
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
        "aliases": (
            "keynote-024",
            "keynote 024",
            "pembrolizumab",
            "keytruda",
        ),
        "directs": "outcome-permission",
    },
]


def resolve_evidence(brief: ExtractedBrief, *, pubmed: bool = True) -> dict[str, Any]:
    """Catalog matches (named only) plus a live literature review for this brief."""
    blob = _brief_blob(brief)
    folded = _fold(blob)
    matched: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in CATALOG:
        if _matches(entry, brief, blob, folded):
            rec = _record(entry, status="validated", matched_from="catalog")
            matched.append(rec)
            seen.add(entry["id"])

    gaps = _uncited_brief_items(brief, matched)
    search_terms = _pubmed_terms(brief) if pubmed else []
    display_terms = [_display_query(t) for t in search_terms]
    pubmed_hits: list[dict[str, Any]] = []
    if pubmed:
        pubmed_hits = _pubmed_enrich(brief, seen)
        catalog_pmids = {r.get("pmid") for r in matched}
        for hit in pubmed_hits:
            if hit.get("pmid") in catalog_pmids:
                continue
            rec = _pubmed_as_record(hit, brief)
            matched.append(rec)
            catalog_pmids.add(hit.get("pmid"))

    review = _review_note(brief, matched, display_terms)
    lead = _campaign_lead(brief, matched, review)
    return {
        "lead": lead,
        "records": matched,
        "gaps": gaps,
        "pubmed": pubmed_hits,
        "searchTerms": display_terms,
        "review": review,
        "validatedCount": sum(1 for r in matched if r.get("matchedFrom") == "catalog"),
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


def _fold(text: str) -> str:
    """Lowercase and turn dashes/slashes into spaces so PARADIGM-HF matches PARADIGM HF."""
    lowered = (text or "").lower()
    lowered = re.sub(r"[–—−\-_/]+", " ", lowered)
    lowered = re.sub(r"\s+", " ", lowered).strip()
    return f" {lowered} "


def _alias_in(folded_blob: str, alias: str) -> bool:
    needle = _fold(alias).strip()
    if len(needle) < 3:
        return False
    return f" {needle} " in folded_blob


def _entry_aliases(entry: dict[str, Any]) -> list[str]:
    names = [str(a) for a in (entry.get("aliases") or ()) if a]
    pmid = str(entry.get("pmid") or "").strip()
    if pmid:
        names.append(pmid)
    doi = str(entry.get("doi") or "").strip()
    if doi:
        names.append(doi)
    trial = str(entry.get("trial") or "").strip()
    # Bare English words ("TRANSITION") are too common to auto-match.
    if trial and ("-" in trial or "/" in trial or any(ch.isdigit() for ch in trial)):
        names.append(trial)
    return names


def _matches(entry: dict[str, Any], brief: ExtractedBrief, blob: str, folded: str | None = None) -> bool:
    """Attach a catalog row only when the brief names that paper or molecule.

    Therapy area is a negative filter (do not put KEYNOTE on a cardiology brief)
    and is never enough on its own. NSCLC does not inherit pembrolizumab; HFrEF
    does not inherit sacubitril.
    """
    tags = entry.get("tags") or ()
    family = _catalog_family(tags)
    brief_family = _brief_family(brief, blob)
    if family and brief_family and family != brief_family:
        return False
    hay = folded if folded is not None else _fold(blob)
    return any(_alias_in(hay, alias) for alias in _entry_aliases(entry))


def _catalog_family(tags) -> str:
    if any(t in tags for t in ("hfref", "arni", "cardiology")):
        return "cardiology"
    if any(t in tags for t in ("nsclc", "oncology")):
        return "oncology"
    if any(t in tags for t in ("diabetes", "obesity", "glp1", "glp-1", "endocrinology")):
        return "endocrinology"
    return ""


def _brief_family(brief: ExtractedBrief, blob: str) -> str:
    stated = f"{brief.therapy_area} {brief.indication} {brief.product}".lower()
    hay = f"{stated} {brief.brand} {blob}".lower()
    if any(k in stated for k in ("endocrin", "diabetes", "t2d", "obesity", "glp-1", "glp1", "semaglutide")):
        return "endocrinology"
    if any(k in stated for k in ("nsclc", "lung cancer", "oncology", "pembrolizumab", "keynote")):
        return "oncology"
    if any(k in stated for k in ("hfref", "heart failure", "cardiology", "arni", "sacubitril", "paradigm")):
        return "cardiology"
    if any(k in hay for k in ("endocrin", "diabetes", "t2d", "obesity", "glp-1", "glp1", "semaglutide")):
        return "endocrinology"
    if any(k in hay for k in ("nsclc", "lung cancer", "oncology", "pembrolizumab", "keynote")):
        return "oncology"
    if any(k in hay for k in ("hfref", "heart failure", "cardiology", "arni", "sacubitril", "paradigm")):
        return "cardiology"
    if any(k in stated for k in ("respirat", "copd", "asthma", "nebulis", "nebuliz")):
        return "respiratory"
    if any(k in hay for k in ("respirat", "copd", "asthma", "nebulis", "nebuliz")):
        return "respiratory"
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


def _first_sentences(text: str, n: int = 2) -> str:
    blob = re.sub(r"\s+", " ", (text or "").strip())
    if not blob:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", blob)
    return " ".join(parts[:n]).strip()


_METHODS_OPEN = re.compile(
    r"^(abstract:|background:|objective:|methods?:|"
    r"we (evaluated|aimed|assessed|investigated|conducted|performed|sought|compared)|"
    r"this (pooled |post hoc )?(study|trial|analysis)|patients were )",
    re.I,
)
_FINDING_HINT = re.compile(
    r"\b(improv|reduc|lower(?:ed|ing)?|fewer|versus|vs\.?|significan|benefit|"
    r"superior|non-inferior|rate ratio|hazard|exacerbat|surviv)",
    re.I,
)
_PK_PAPER = re.compile(r"pharmacokinet|bioequivalence|\bc[\s-]?max\b|\bauc\b", re.I)
_CLINICAL_OUTCOME = re.compile(
    r"exacerbat|fev\d|lung function|hospital|mortal|death|quality of life|"
    r"symptom|versus dual|composite|heart failure|surviv|progression",
    re.I,
)


_BACKGROUND = re.compile(
    r"^(chronic obstructive|copd is\b|heart failure is\b|background:|"
    r".{0,60}\bis a (progressive|chronic|common|leading)\b)",
    re.I,
)


def _result_clause(text: str) -> str:
    """Prefer the verb-and-number clause so a dose preamble does not become the headline."""
    blob = re.sub(r"\s+", " ", (text or "").strip())
    if not blob:
        return ""
    m = re.search(
        r"((?:[A-Z]{2,8}\s+)?(?i:was estimated to have benefits|reduced the annual rate|"
        r"reduc(?:ed|es)|improv(?:ed|es)|lower(?:ed))\b[^.]{8,160})",
        blob,
    )
    if not m:
        return blob
    clause = m.group(1).strip(" ,;")
    if clause[:1].islower():
        clause = clause[:1].upper() + clause[1:]
    return clause


def _finding_from_abstract(abstract: str, title: str = "") -> str:
    """A result sentence, not the methods opener PubMed puts first."""
    blob = re.sub(r"\s+", " ", (abstract or "").strip())
    parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", blob) if len(p.strip()) > 24]
    findings = [
        p for p in parts
        if _FINDING_HINT.search(p)
        and not _METHODS_OPEN.search(p)
        and not _BACKGROUND.search(p)
        and not _is_pk_only(p)
    ]
    if findings:
        conclusion = findings[-1]
        if len(conclusion) <= 240:
            return _result_clause(conclusion)
        return _result_clause(findings[0])
    for part in parts:
        if _METHODS_OPEN.search(part) or _BACKGROUND.search(part) or _is_pk_only(part):
            continue
        if _FINDING_HINT.search(part):
            return _result_clause(part)
    titled = _first_sentences(title, 1)
    if titled and _FINDING_HINT.search(titled) and not _BACKGROUND.search(titled) and not _is_pk_only(titled):
        return _result_clause(titled)
    return ""


def _is_pk_only(text: str) -> bool:
    blob = text or ""
    return bool(_PK_PAPER.search(blob) and not _CLINICAL_OUTCOME.search(blob))


def _is_clinical_finding(text: str) -> bool:
    blob = text or ""
    if not blob or _BACKGROUND.search(blob) or _is_pk_only(blob):
        return False
    return bool(_FINDING_HINT.search(blob) and _CLINICAL_OUTCOME.search(blob))


def _strategy_implication(brief: ExtractedBrief, records: list[dict]) -> str:
    brand = brief.brand or "the brand"
    indication = brief.indication or brief.therapy_area or "this indication"
    insights = " ".join(brief.hcp_insights or []).lower()
    cost = " ".join(brief.access_and_cost or []).lower()
    science = " ".join(
        f"{r.get('title') or ''} {r.get('abstract') or ''} {r.get('claim_permitted') or ''}"
        for r in records
    ).lower()
    landscape = any(r.get("independence") == "indication-landscape" for r in records)
    landscape_note = (
        f" Landmark papers of other agents describe the {indication} standard — "
        f"they are not trials of {brand}."
        if landscape
        else ""
    )
    start_lit = any(w in science for w in ("initiat", "first-line", "guideline", "in-hospital", "early"))
    outcome_lit = any(w in science for w in ("surviv", "mortality", "hazard", "efficacy", "outcome"))
    habit = any(w in insights for w in ("wait", "late", "stabil", "second", "habit"))
    if start_lit and habit:
        return (
            f"The papers already cover when to start in {indication}. {brand} is not missing science — "
            f"the doctors described in the brief still wait. That delay is the campaign.{landscape_note}"
        )
    if start_lit and not insights:
        return (
            f"The literature for {indication} already defines when to start. "
            "This brief did not describe the current habit — capturing it is the first research task. "
            f"Until then the scientific bet is first-eligible start, not a restated upload.{landscape_note}"
        )
    if start_lit:
        return (
            f"The literature for {indication} defines when to start. "
            f"Spend {brand} against the delay the field still practices, not against a restated brief.{landscape_note}"
        )
    if outcome_lit and any(w in cost for w in ("cost", "oop", "price", "afford", "reimburs")):
        return (
            "Outcome literature is on the register. Conversion is gated by cost and access, "
            f"not by another reminder that the class works.{landscape_note}"
        )
    if outcome_lit:
        return (
            f"Numbered papers are permission to stand somewhere specific for {brand} in {indication}. "
            f"The campaign is the gap between those findings and the current start.{landscape_note}"
        )
    return (
        f"Numbered papers are permission to stand somewhere specific for {brand}. "
        f"Spend against the behaviour in the field, not against a generic funnel.{landscape_note}"
    )


def _infer_directs(records: list[dict], brief: ExtractedBrief) -> str:
    science = " ".join(
        f"{r.get('title') or ''} {r.get('abstract') or ''}" for r in records
    ).lower()
    insights = " ".join(brief.hcp_insights or []).lower()
    if any(w in science for w in ("initiat", "in-hospital", "first-line", "early start")):
        return "first-eligible-start"
    if any(w in science for w in ("guideline", "consensus", "recommendation")):
        return "guideline-cover"
    if any(w in insights for w in ("myth", "renal", "monitor", "safety")):
        return "segment-confidence"
    return "outcome-permission"


def _scientific_synthesis(brief: ExtractedBrief, records: list[dict]) -> str:
    papers = [r for r in records if r.get("pmid") or r.get("doi")]
    if not papers:
        return (
            "No paper with a PMID or DOI is on the register yet. "
            "The brief is not the literature — we still need a retrieved paper before a scientific lead."
        )
    bits = []
    for row in papers[:4]:
        finding = _first_sentences(
            row.get("abstract") or row.get("claim_permitted") or row.get("title") or "",
            1,
        )
        label = row.get("short") or row.get("title") or "Paper"
        bits.append(f"{label} (PMID {row.get('pmid') or '—'}): {finding}")
    implication = _strategy_implication(brief, papers)
    return (
        f"Literature review retrieved {len(papers)} numbered paper"
        f"{'s' if len(papers) != 1 else ''} for "
        f"{brief.product or brief.brand or 'this brand'} in "
        f"{brief.indication or brief.therapy_area or 'the named indication'}. "
        "The upload did not have to list these. "
        + " ".join(bits)
        + " "
        + implication
    )


def _review_note(brief: ExtractedBrief, matched: list[dict], terms: list[str]) -> dict[str, Any]:
    independent_n = sum(1 for r in matched if r.get("independence") == "indication-landscape")
    if _brief_has_named_inn(brief):
        excluded = (
            "Dropped papers that name another molecule's catalog pivotal — "
            "this brief named a different INN."
        )
    elif independent_n:
        excluded = (
            f"Kept {independent_n} indication-landmark paper"
            f"{'s' if independent_n != 1 else ''} as independent landscape — "
            "not trials of this brand. Dropped cross-therapy-area papers."
        )
    else:
        excluded = (
            "Cross-therapy-area papers stay off this register. "
            "Indication landmarks remain in play when they belong to this disease."
        )
    findings = []
    for row in matched[:6]:
        findings.append({
            "short": row.get("short"),
            "pmid": row.get("pmid"),
            "finding": _first_sentences(
                row.get("abstract") or row.get("claim_permitted") or row.get("title") or "",
                1,
            ),
        })
    return {
        "searched": terms,
        "paperCount": len(matched),
        "excluded": excluded,
        "findings": findings,
        "synthesis": _scientific_synthesis(brief, matched),
    }


def _lead_priority(row: dict) -> tuple:
    """Campaign lead: clinical result clause first, guideline-recommend last, PK never."""
    claim = str(row.get("claim_permitted") or "")
    abstract = str(row.get("abstract") or "")
    title = str(row.get("title") or "")
    finding = _finding_from_abstract(abstract, title)
    blob = f"{finding} {claim} {title}".lower()
    guideline = 1 if re.search(r"guideline[s] recommend|japanese guidelines|practice guideline", blob) else 0
    pk = 1 if _is_pk_only(blob) else 0
    named = 0 if re.search(r"\b(kronos|ethos|tribute|trilog|impact|bgf)\b", blob) else 1
    clinical = 0 if _has_published_finding(row) else 1
    return (pk, guideline, clinical, named, -(row.get("year") or 0))


def _has_published_finding(row: dict) -> bool:
    """True when the paper states a clinical result, not a disease definition or PK Cmax."""
    claim = str(row.get("claim_permitted") or "")
    if claim.lower().startswith("retrieved from pubmed"):
        claim = ""
    claim = re.sub(r"^Independent / indication landscape — not a trial of [^.]+.\s*", "", claim)
    finding = _finding_from_abstract(row.get("abstract") or "", row.get("title") or "")
    return _is_clinical_finding(finding or claim)


def _campaign_lead(brief: ExtractedBrief, matched: list[dict], review: dict | None = None) -> dict[str, Any]:
    catalog = [r for r in matched if r.get("matchedFrom") != "pubmed"]
    retrieved = [r for r in matched if r.get("matchedFrom") == "pubmed"]
    if not catalog and not retrieved:
        return {
            "statement": "No validated citation matched this brief yet. Do not lock a scientific lead.",
            "why": "The working file has no DOI/PMID-backed row. Strategy stays behavioural until science is sourced.",
            "directs": "none",
            "citations": [],
            "doNotClaim": ["Any efficacy, safety, or guideline class statement"],
        }
    if not catalog and retrieved:
        ranked = sorted(retrieved, key=_lead_priority)
        with_finding = [r for r in ranked if _has_published_finding(r)]
        primary = (with_finding or ranked)[0]
        implication = _strategy_implication(brief, retrieved)
        directs = _infer_directs(retrieved, brief)
        synthesis = (review or {}).get("synthesis") or _scientific_synthesis(brief, retrieved)
        return {
            "statement": synthesis,
            "why": (
                f"We searched PubMed for this product and indication instead of waiting for the brief "
                f"to paste a bibliography. Lead source: {primary.get('short')} "
                f"(PMID {primary.get('pmid') or '—'}). {implication}"
            ),
            "directs": directs,
            "primaryId": primary.get("id"),
            "citations": [
                {
                    "id": c.get("id"),
                    "short": c.get("short"),
                    "pmid": c.get("pmid"),
                    "doi": c.get("doi"),
                    "citation": c.get("citation"),
                    "claim": c.get("claim_permitted"),
                }
                for c in ([primary] + [r for r in retrieved if r is not primary])[:6]
            ],
            "doNotClaim": [
                "An effect size the abstract did not state",
                "Another molecule's pivotal trial as if it belonged to this brand",
            ],
        }

    by_id = {r["id"]: r for r in catalog}
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
        anchors = sorted(catalog, key=lambda r: (0 if r.get("grade") == "A" else 1, r.get("year") or 0))

    primary = anchors[0]
    support = anchors[1:4]
    if primary["id"] in {"pioneer-hf-2019", "transition-2019"} and "paradigm-hf-2014" in by_id:
        statement = (
            f"Lead the campaign with first-eligible / in-hospital initiation. "
            f"{primary['trial']} ({primary['year']}) shows that starting after haemodynamic "
            f"stabilisation is feasible; ESC/ACC Class I plus PARADIGM-HF are the outcome permission — "
            f"not a reason to wait for a second clinic visit."
        )
        directs = "first-eligible-start"
    elif primary["id"].startswith("keynote"):
        statement = (
            f"Lead with the first-line survival evidence in {primary['trial']} "
            f"(PMID {primary['pmid']}). Cost is an access problem sitting on top of settled science, "
            f"not a reason to soften the efficacy lead."
        )
        directs = "outcome-permission"
    else:
        statement = (
            f"Lead with {primary['short']}: {primary['claim_permitted']}"
        )
        directs = primary.get("directs") or "outcome-permission"

    citations = [primary, *support]
    extra = ""
    if retrieved:
        extra = (
            f" Independently retrieved {len(retrieved)} further paper"
            f"{'s' if len(retrieved) != 1 else ''} for this indication that the brief did not list."
        )
    return {
        "statement": statement + extra,
        "why": (
            f"Highest-leverage validated row is {primary['short']} "
            f"({primary['journal']} {primary['year']}; PMID {primary.get('pmid') or '—'})."
            + (f" Plus {len(retrieved)} PubMed hits for this indication." if retrieved else "")
        ),
        "directs": directs,
        "primaryId": primary["id"],
        "citations": [
            {
                "id": c["id"],
                "short": c["short"],
                "pmid": c.get("pmid"),
                "doi": c.get("doi"),
                "citation": c["citation"],
                "claim": c["claim_permitted"],
            }
            for c in citations
        ],
        "doNotClaim": list(dict.fromkeys(
            [primary.get("caveat") or "", *(c.get("caveat") or "" for c in support)]
        )),
    }


_FOREIGN_MOLECULES = (
    "sacubitril",
    "entresto",
    "lcz696",
    "pembrolizumab",
    "keytruda",
    "semaglutide",
    "ozempic",
    "liraglutide",
    "paradigm-hf",
    "pioneer-hf",
    "keynote-189",
    "keynote-024",
    "neprilysin",
)


def _paper_short_label(title: str, abstract: str = "") -> str:
    """A slide label, not a truncated methods title ending in 'versus'."""
    blob = f"{title} {abstract}"
    trials: list[str] = []
    for name in ("KRONOS", "ETHOS", "TRIBUTE", "TRILOGY"):
        if re.search(rf"\b{name}\b", blob, re.I) and name not in trials:
            trials.append(name)
    if len(trials) >= 2:
        return f"{' + '.join(trials)} · BGF versus dual"
    if trials:
        return trials[0]
    t = re.sub(r"\s+", " ", title or "").strip().rstrip(".")
    if len(t) <= 72:
        return t
    cut = t[:72].rsplit(" ", 1)[0]
    dangling = {"versus", "vs", "vs.", "with", "for", "and", "of", "the", "a", "in", "to"}
    while cut and cut.split()[-1].lower() in dangling:
        cut = cut.rsplit(" ", 1)[0]
    return cut


def _pubmed_as_record(hit: dict[str, Any], brief: ExtractedBrief) -> dict[str, Any]:
    title = hit.get("title") or "PubMed retrieval"
    abstract = hit.get("abstract") or ""
    brand = brief.brand or brief.product or "this brand"
    independent = hit.get("independence") == "indication-landscape" or _hit_is_independent_landscape(
        brief, f"{title} {abstract}"
    )
    claim = _finding_from_abstract(abstract, title)
    if not claim:
        claim = f"Retrieved from PubMed: {title.rstrip('.')}."
    if independent:
        claim = (
            f"Independent / indication landscape — not a trial of {brand}. {claim}"
        )
    return {
        "id": hit.get("id") or f"pubmed-{hit.get('pmid')}",
        "stream": "Independent / indication landscape" if independent else "Independent / retrieved",
        "trial": "",
        "short": _paper_short_label(title, abstract),
        "title": title,
        "authors": hit.get("authors") or "",
        "year": hit.get("year"),
        "journal": hit.get("journal") or "",
        "pages": "",
        "doi": hit.get("doi") or "",
        "pmid": hit.get("pmid") or "",
        "design": hit.get("pubtype") or "PubMed retrieval",
        "n": None,
        "population": "",
        "endpoint": "",
        "effect_metric": None,
        "hr": hit.get("hr"),
        "low": hit.get("low"),
        "high": hit.get("high"),
        "grade": "B" if abstract else "C",
        "claim_permitted": claim,
        "caveat": (
            f"Indication landscape only. Do not present this as a trial of {brand}."
            if independent
            else "Retrieved literature. Not a substitute for reading the paper."
        ),
        "mlr": "Do not quote an effect size unless it appears in the abstract or full text.",
        "directs": hit.get("directs") or "outcome-permission",
        "abstract": abstract,
        "citation": hit.get("citation") or "",
        "url": hit.get("url") or "",
        "status": "pubmed-retrieved",
        "matchedFrom": "pubmed",
        "independence": "indication-landscape" if independent else "of-this-indication",
        "spine_means": _first_sentences(abstract or title, 1),
        "spine_barrier": "A paper on the register that the field never uses is not a campaign.",
        "spine_execute": "Put this finding in the first-eligible conversation, not in an appendix.",
        "spine_measure": "Share of calls that use this numbered paper vs a generic efficacy line.",
    }


def _pmids_in_brief(brief: ExtractedBrief) -> list[str]:
    blob = _brief_blob(brief)
    found = re.findall(r"pmid[:\s#]*([1-9]\d{6,8})", blob, re.I)
    return list(dict.fromkeys(found))


def _named_search_molecules(brief: ExtractedBrief) -> list[str]:
    """INNs / trial names the brief actually used — never inferred from therapy area."""
    blob = _brief_blob(brief)
    folded = _fold(blob)
    named: list[str] = []
    for entry in CATALOG:
        for alias in entry.get("aliases") or ():
            token = str(alias).strip()
            if len(token) < 4:
                continue
            if _alias_in(folded, token) and token.lower() not in {n.lower() for n in named}:
                named.append(token)
    product = re.sub(r"[^A-Za-z0-9 +/()-]+", " ", brief.product or "").strip()
    if 5 <= len(product) <= 80 and _looks_like_inn(product) and product.lower() not in {n.lower() for n in named}:
        named.append(product)
    hay = f"{brief.product or ''} {brief.raw_text or ''}"[:2500]
    for token in re.findall(r"[A-Za-z][A-Za-z0-9-]{4,}", hay):
        if _looks_like_inn(token) and token.lower() not in {n.lower() for n in named}:
            named.append(token)
        if len(named) >= 4:
            break
    return named


def _looks_like_inn(product: str) -> bool:
    """True for generic/INN-like strings, not trade names like HelixOne."""
    if not product or len(product) < 5:
        return False
    low = product.lower().strip()
    if "/" in product:
        return True
    tokens = [part for part in re.split(r"[\s,;]+", low) if part]
    suffix = re.compile(
        r"(mab|nib|tide|glutide|gliflozin|sartan|pril|olol|umab|ciclib|fenib|parib|terol|onium|sonide|tropium)$"
    )
    return any(suffix.search(token) for token in tokens)


_CATALOG_INNS = (
    "sacubitril",
    "pembrolizumab",
    "semaglutide",
    "liraglutide",
    "entresto",
    "keytruda",
    "ozempic",
    "lcz696",
)


def _brief_has_named_inn(brief: ExtractedBrief) -> bool:
    if _looks_like_inn(brief.product or ""):
        return True
    blob = _brief_blob(brief)
    return any(m in blob for m in _CATALOG_INNS)


def _disease_phrases(brief: ExtractedBrief) -> list[str]:
    raw = f"{brief.indication or ''} {brief.therapy_area or ''} {(brief.raw_text or '')[:2000]}"
    cleaned = re.sub(r"[^A-Za-z0-9 +/()-]+", " ", raw)
    low = cleaned.lower()
    out: list[str] = []

    def add(*phrases: str) -> None:
        for phrase in phrases:
            if phrase and phrase.lower() not in {x.lower() for x in out}:
                out.append(phrase)

    if re.search(r"\bcopd\b|obstructive pulmonary", low):
        add("COPD", "chronic obstructive pulmonary disease")
    if re.search(r"\bnsclc\b|non-small cell lung|lung cancer", low):
        add("NSCLC", "non-small cell lung cancer")
    if re.search(r"\bhfref\b|reduced ejection", low):
        add("HFrEF", "heart failure with reduced ejection fraction")
    if re.search(r"\bhfpef\b|preserved ejection", low):
        add("HFpEF", "heart failure with preserved ejection fraction")
    if re.search(r"\bheart failure\b", low) and not out:
        add("heart failure")
    if re.search(r"\bt2dm\b|type 2 diabetes|type 2 dm", low):
        add("type 2 diabetes")
    if re.search(r"\basthma\b", low) and "copd" not in low:
        add("asthma")

    ta = (brief.therapy_area or "").strip()
    if ta and len(ta) < 80:
        m = re.search(r"\b(COPD|NSCLC|HFrEF|HFpEF|T2DM|CKD)\b", ta, re.I)
        if m:
            add(m.group(1))
        elif not out:
            add(ta)

    indication = (brief.indication or "").strip()
    if indication and len(indication) < 80:
        add(indication)

    return out[:4]


def _display_query(term: str) -> str:
    cleaned = re.sub(r"\s+NOT\s+\S+", "", term, flags=re.I)
    return re.sub(r"\s+", " ", cleaned).strip()


def _pubmed_not_clause(brief: ExtractedBrief) -> str:
    """Exclude other molecules from the query when this brief named an INN.

    Brand-only indication reviews must still find same-family landmarks
    (KEYNOTE on an NSCLC brand, PARADIGM on an unnamed HF brand). Cross-family
    exclusions always stay on (no sacubitril on NSCLC).
    """
    blob = _brief_blob(brief)
    brief_fam = _brief_family(brief, blob)
    named_inn = _brief_has_named_inn(brief)
    parts = []
    for mol in _FOREIGN_MOLECULES:
        if mol.lower() in blob:
            continue
        mol_fam = _text_family(mol)
        if not named_inn and mol_fam and brief_fam and mol_fam == brief_fam:
            continue
        parts.append(f"NOT {mol}[ti]")
        if len(parts) >= 4:
            break
    return " ".join(parts)


def _pubmed_terms(brief: ExtractedBrief) -> list[str]:
    """Search this brief's studies and molecule — never a substitute catalog drug."""
    terms: list[str] = []
    named = _named_search_molecules(brief)
    diseases = _disease_phrases(brief)
    primary_disease = diseases[0] if diseases else ""
    not_clause = _pubmed_not_clause(brief)

    if named:
        extra = primary_disease or ""
        terms.append(f"{named[0]} {extra} randomized controlled trial".strip())
        if len(named) >= 2:
            terms.append(f"{' '.join(named[:3])} {extra} randomized".strip())

    fam = _brief_family(brief, _brief_blob(brief))
    if fam == "respiratory" or "copd" in (primary_disease or "").lower():
        terms.extend(
            [
                "KRONOS ETHOS budesonide glycopyrrolate formoterol COPD",
                "ETHOS trial COPD triple therapy exacerbation",
                "ICS LABA LAMA triple therapy COPD randomized",
            ]
        )

    product = re.sub(r"[^A-Za-z0-9 +/()-]+", " ", brief.product or "").strip()
    brand = (brief.brand or "").strip()
    if product and product.lower() != brand.lower() and 5 <= len(product) <= 80:
        terms.append(f"{product} {primary_disease} randomized".strip())

    brief_fam = _brief_family(brief, _brief_blob(brief))
    for item in (
        *(brief.brand_evidence or []),
        *(brief.existing_evidence or []),
        *(brief.evolving_evidence or []),
        *(brief.guidelines or []),
    ):
        cleaned = re.sub(r"[^A-Za-z0-9 +/()-]+", " ", item).strip()
        if 12 <= len(cleaned) <= 140 and not cleaned[:1].isdigit():
            low = cleaned.lower()
            if any(
                w in low
                for w in (
                    "no data",
                    "expected q",
                    "signal only",
                    "data on file",
                    "in press",
                    "no guideline",
                    "not attached",
                    "emerging interest",
                    "no dedicated",
                    "interim analysis",
                    "follow-up expected",
                )
            ):
                continue
            if "cardiovascular" in low and brief_fam != "cardiology":
                continue
            terms.append(cleaned[:140])

    if primary_disease and len(primary_disease) >= 4:
        terms.append(f"{primary_disease} randomized controlled trial {not_clause}".strip())
        terms.append(f"{primary_disease} AND (guideline[pt] OR practice guideline[pt])")
        terms.append(f"{primary_disease} meta-analysis {not_clause}".strip())
        terms.append(f"{primary_disease} first-line treatment randomized {not_clause}".strip())
        terms.append(f"{primary_disease} epidemiology")
        fam = _brief_family(brief, _brief_blob(brief))
        if fam == "oncology" and not _brief_has_named_inn(brief):
            terms.append(f"{primary_disease} immunotherapy chemotherapy randomized")
        if fam == "cardiology" and not _brief_has_named_inn(brief):
            terms.append(f"{primary_disease} guideline class I randomized")
        if fam == "respiratory" or "copd" in primary_disease.lower():
            terms.append("COPD GOLD guideline")
            terms.append("ICS LABA LAMA triple therapy COPD randomized")
            terms.append("COPD exacerbation reduction randomized")
        if len(diseases) > 1:
            terms.append(f"{diseases[1]} randomized controlled trial {not_clause}".strip())

    uniq: list[str] = []
    seen = set()
    for term in terms:
        key = re.sub(r"\s+", " ", term.lower()).strip()
        if key in seen or len(key) < 8:
            continue
        if _term_smuggles_foreign_molecule(brief, key):
            continue
        if len(term) > 220:
            continue
        seen.add(key)
        uniq.append(term)
    return uniq[:12]


def _term_smuggles_foreign_molecule(brief: ExtractedBrief, term: str) -> bool:
    blob = _fold(_brief_blob(brief))
    cleaned = re.sub(r"\bnot\s+[a-z0-9\-]+(?:\[ti\])?", " ", term, flags=re.I)
    folded = _fold(cleaned)
    for mol in _FOREIGN_MOLECULES:
        if _alias_in(folded, mol) and not _alias_in(blob, mol):
            return True
    return False


def _pubmed_term(brief: ExtractedBrief) -> str:
    terms = _pubmed_terms(brief)
    return terms[0] if terms else ""


def _pubmed_enrich(brief: ExtractedBrief, already: set[str]) -> list[dict[str, Any]]:
    terms = _pubmed_terms(brief)
    pmids = _pmids_in_brief(brief)
    for term in terms:
        try:
            pmids.extend(_esearch(term, retmax=12))
            time.sleep(0.12)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, ValueError):
            continue
    pmids = list(dict.fromkeys(p for p in pmids if p))
    if not pmids:
        return []
    try:
        summaries = _esummary(pmids[:40])
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, ValueError):
        return []
    try:
        abstracts = _efetch_abstracts(list(summaries.keys())[:28])
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, ValueError):
        abstracts = {}

    hits = []
    catalog_pmids = {e.get("pmid") for e in CATALOG}
    named_pmids = set(_pmids_in_brief(brief))
    named_inn = _brief_has_named_inn(brief)
    for pmid, doc in summaries.items():
        title = doc.get("title") or ""
        abstract = abstracts.get(pmid) or ""
        if not _pubmed_hit_belongs(brief, title, abstract):
            continue
        # Named INN: do not sneak another molecule's catalog pivotal in via PubMed.
        # Disease guidelines in the catalog may still enter as independent pubmed rows.
        # Brand-only: keep same-family landmarks as independent landscape, not catalog rows.
        if pmid in catalog_pmids and pmid not in named_pmids:
            entry = next((e for e in CATALOG if str(e.get("pmid") or "") == str(pmid)), None)
            stream = str((entry or {}).get("stream") or "").lower()
            if named_inn and "guideline" not in stream:
                continue
        journal = doc.get("fulljournalname") or doc.get("source") or ""
        year = _year(doc.get("pubdate") or "")
        authors = _author_line(doc.get("authors") or [])
        doi = _doi_from(doc)
        pubtypes = ", ".join(str(x) for x in (doc.get("pubtype") or [])[:3])
        hr, low, high = _hr_from_text(f"{title} {abstract}")
        independence = (
            "indication-landscape"
            if _hit_is_independent_landscape(brief, f"{title} {abstract}")
            else "of-this-indication"
        )
        hits.append({
            "pmid": pmid,
            "title": title,
            "abstract": abstract,
            "authors": authors,
            "year": year,
            "journal": journal,
            "doi": doi,
            "pubtype": pubtypes,
            "hr": hr,
            "low": low,
            "high": high,
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            "citation": f"{authors} {title} {journal}. {year}." + (f" doi:{doi}" if doi else f" PMID {pmid}"),
            "status": "pubmed-retrieved",
            "note": "Independent PubMed hit — confirm against the full text before promotional use.",
            "independence": independence,
            "directs": _infer_directs(
                [{"title": title, "abstract": abstract}],
                brief,
            ),
        })
    hits.sort(key=lambda h: _pubmed_score(h, brief), reverse=True)
    return hits[:12]


def _hr_from_text(text: str) -> tuple[float | None, float | None, float | None]:
    """Copy a hazard ratio out of an abstract only when the abstract states it."""
    m = re.search(
        r"\bHR\s*(?:of|=|:)?\s*(0\.\d{2,3})\s*(?:\(|,|\s)*(?:95%\s*CI[:\s]*)?(0\.\d{2,3})\s*[-–to]+\s*(0\.\d{2,3})",
        text or "",
        re.I,
    )
    if not m:
        return None, None, None
    try:
        return float(m.group(1)), float(m.group(2)), float(m.group(3))
    except ValueError:
        return None, None, None


def _efetch_abstracts(pmids: list[str]) -> dict[str, str]:
    if not pmids:
        return {}
    q = urllib.parse.urlencode(
        {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
            "rettype": "abstract",
            "tool": "strata-director",
            "email": "strata-director@local",
        }
    )
    xml = _ncbi_get(
        f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?{q}",
        timeout=20,
    ).decode("utf-8", errors="replace")
    out: dict[str, str] = {}
    for block in re.findall(r"<PubmedArticle>(.*?)</PubmedArticle>", xml, re.S):
        pmid_m = re.search(r"<PMID[^>]*>(\d+)</PMID>", block)
        texts = re.findall(r"<AbstractText[^>]*>(.*?)</AbstractText>", block, re.S)
        if not pmid_m or not texts:
            continue
        joined = " ".join(_strip_xml(t) for t in texts)
        if joined.strip():
            out[pmid_m.group(1)] = joined.strip()
    return out


def _strip_xml(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = text.replace("&#xa0;", " ").replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", text).strip()


def _pubmed_score(hit: dict[str, Any], brief: ExtractedBrief | None = None) -> int:
    blob = f"{hit.get('title') or ''} {hit.get('pubtype') or ''} {hit.get('abstract') or ''} {hit.get('journal') or ''}".lower()
    score = 0
    if any(w in blob for w in ("randomiz", "randomis", "rct", "phase 3", "phase iii")):
        score += 4
    if "guideline" in blob or "practice guideline" in blob:
        score += 4
    if "meta-analysis" in blob or "systematic review" in blob:
        score += 3
    if hit.get("abstract"):
        score += 2
    if hit.get("hr") is not None:
        score += 2
    journal = (hit.get("journal") or "").lower()
    if any(
        name in journal
        for name in (
            "n engl j med",
            "lancet",
            "jama",
            "j clin oncol",
            "circulation",
            "eur heart",
            "ann oncol",
            "j natl compr",
        )
    ):
        score += 2
    if hit.get("independence") == "of-this-indication":
        score += 1
    if "triple" in blob or "ics/lama/laba" in blob or "ics/laba/lama" in blob:
        score += 3
    if "gold" in blob and ("copd" in blob or "obstructive" in blob):
        score += 3
    if any(w in blob for w in ("kronos", "ethos", "tribute", "trilogy", "impact trial")):
        score += 5
    if any(w in blob for w in ("narrative review", "mini-review", "editorial", "commentary")):
        score -= 8
    if _FINDING_HINT.search(hit.get("abstract") or ""):
        score += 3
    if _BACKGROUND.search((hit.get("abstract") or "")[:180]) and not _FINDING_HINT.search(hit.get("abstract") or ""):
        score -= 5
    if brief:
        named = [n.lower() for n in _named_search_molecules(brief)]
        hits_n = sum(1 for n in named if n in blob)
        if hits_n >= 2:
            score += 4
        elif hits_n == 1:
            score += 1
        product = (brief.product or "").lower()
        if "nebul" in product and "nebul" in blob:
            score += 2
    if any(w in blob for w in ("pharmacokinet", "bioequivalence", "c max", "cmax", "ethnic pharmacokinetic")):
        score -= 12
    if "cost-effectiveness" in blob or "cost effectiveness" in blob:
        score -= 6
    if re.search(r"(reduc\w*|lower rate).{0,80}exacerbat|exacerbat.{0,40}(reduc|lower)", blob):
        score += 5
    if any(w in blob for w in ("telerehab", "biologic", "monoclonal", "dupilumab", "benralizumab")):
        score -= 4
    return score


def _unmentioned_catalog_markers(brief: ExtractedBrief) -> list[str]:
    """Other catalog molecules/trials this brief did not name.

    Guideline *names* (ESC, ACC) are not foreign molecules — disease guidelines
    still belong on a named-INN brief. Pivotals of another INN do not.
    """
    blob = _fold(_brief_blob(brief))
    markers: list[str] = []
    for entry in CATALOG:
        stream = str(entry.get("stream") or "").lower()
        if "guideline" in stream:
            continue
        for alias in entry.get("aliases") or ():
            token = str(alias).strip()
            if len(token) < 5:
                continue
            if _alias_in(blob, token):
                continue
            markers.append(token)
        trial = str(entry.get("trial") or "")
        if trial and ("-" in trial or any(ch.isdigit() for ch in trial)):
            if not _alias_in(blob, trial):
                markers.append(trial)
    markers.extend(m for m in _FOREIGN_MOLECULES if not _alias_in(blob, m))
    return list(dict.fromkeys(markers))


def _hit_mentions_unmentioned_molecule(brief: ExtractedBrief, text: str) -> bool:
    folded = _fold(text)
    return any(_alias_in(folded, marker) for marker in _unmentioned_catalog_markers(brief))


def _hit_is_independent_landscape(brief: ExtractedBrief, text: str) -> bool:
    if _brief_has_named_inn(brief):
        return False
    return _hit_mentions_unmentioned_molecule(brief, text)


def _text_family(text: str) -> str:
    hay = (text or "").lower()
    if any(k in hay for k in ("nsclc", "lung cancer", "oncology", "pembrolizumab", "keynote", "keytruda")):
        return "oncology"
    if any(
        k in hay
        for k in (
            "hfref",
            "heart failure",
            "cardiology",
            "arni",
            "sacubitril",
            "paradigm",
            "neprilysin",
            "entresto",
            "pioneer-hf",
        )
    ):
        return "cardiology"
    if any(
        k in hay
        for k in (
            "diabetes",
            "obesity",
            "glp-1",
            "glp1",
            "semaglutide",
            "endocrin",
            "ozempic",
            "liraglutide",
        )
    ):
        return "endocrinology"
    if any(k in hay for k in ("copd", "asthma", "nebulis", "nebuliz", "glycopyrronium", "formoterol")):
        return "respiratory"
    return ""


def _families_mismatch(brief: ExtractedBrief, text: str) -> bool:
    brief_fam = _brief_family(brief, _brief_blob(brief))
    hit_fam = _text_family(text)
    return bool(brief_fam and hit_fam and brief_fam != hit_fam)


def _pubmed_hit_belongs(brief: ExtractedBrief, title: str, extra: str = "") -> bool:
    hay = f"{title or ''} {extra or ''}"
    if not (title or "").strip():
        return False
    if _families_mismatch(brief, hay):
        return False
    if _brief_family(brief, _brief_blob(brief)) == "respiratory":
        need = (
            "copd",
            "asthma",
            "obstructive pulmonary",
            "glycopyrronium",
            "formoterol",
            "budesonide",
            "triple therap",
            "nebulis",
            "nebuliz",
            "gold ",
            "lama",
            "laba",
        )
        if not any(k in hay.lower() for k in need):
            return False
    # Named INN: drop another catalog molecule's pivotal when that molecule is in the TITLE.
    # Abstracts of disease guidelines mention standard-of-care drugs; those still belong.
    # Brand-only: keep same-family landmarks as independent landscape.
    if _brief_has_named_inn(brief) and _hit_mentions_unmentioned_molecule(brief, title or ""):
        return False
    return True


def _ncbi_get(url: str, timeout: int = 12) -> bytes:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "STRATA-director/1.0 (literature-review; strata-director@local)"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _esearch(term: str, retmax: int = 4) -> list[str]:
    q = urllib.parse.urlencode(
        {
            "db": "pubmed",
            "retmode": "json",
            "retmax": str(retmax),
            "term": term,
            "sort": "relevance",
            "tool": "strata-director",
            "email": "strata-director@local",
        }
    )
    data = json.loads(
        _ncbi_get(
            f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?{q}",
            timeout=12,
        ).decode("utf-8")
    )
    return list(data.get("esearchresult", {}).get("idlist") or [])


def _esummary(pmids: list[str]) -> dict[str, dict]:
    q = urllib.parse.urlencode(
        {
            "db": "pubmed",
            "retmode": "json",
            "id": ",".join(pmids),
            "tool": "strata-director",
            "email": "strata-director@local",
        }
    )
    data = json.loads(
        _ncbi_get(
            f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?{q}",
            timeout=12,
        ).decode("utf-8")
    )
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
