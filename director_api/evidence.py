"""Validated, cited evidence that sets the campaign lead.

Catalog entries are published sources with DOI/PMID. Brief mentions are matched
to those records. Uncited brief items stay on the ledger as gaps — they are
never given an invented effect size. Optional PubMed lookup adds recent
independent hits without letting them silently become the lead claim.
"""

from __future__ import annotations

import json
import re
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
        "directs": "outcome-permission",
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
    """Match the brief to cited records, list gaps, and name the campaign lead."""
    blob = _brief_blob(brief)
    matched: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in CATALOG:
        if _matches(entry, brief, blob):
            rec = _record(entry, status="validated", matched_from="catalog")
            matched.append(rec)
            seen.add(entry["id"])

    gaps = _uncited_brief_items(brief, matched)
    pubmed_hits: list[dict[str, Any]] = []
    if pubmed:
        pubmed_hits = _pubmed_enrich(brief, seen)

    lead = _campaign_lead(brief, matched)
    return {
        "lead": lead,
        "records": matched,
        "gaps": gaps,
        "pubmed": pubmed_hits,
        "validatedCount": len(matched),
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


def _matches(entry: dict[str, Any], brief: ExtractedBrief, blob: str) -> bool:
    tags = entry.get("tags") or ()
    hits = sum(1 for tag in tags if tag in blob)
    if hits >= 2:
        return True
    # Therapy-area gate: cardiology catalog should not leak into oncology briefs.
    ta = f"{brief.therapy_area} {brief.indication} {brief.product}".lower()
    if "cardiology" in tags or "hfref" in tags or "arni" in tags:
        return any(k in ta or k in blob for k in ("hfref", "heart failure", "cardiology", "arni", "sacubitril", "paradigm"))
    if "nsclc" in tags or "oncology" in tags:
        return any(k in ta or k in blob for k in ("nsclc", "lung", "oncology", "pembrolizumab", "io"))
    return hits >= 1


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
            "caveat", "mlr", "directs",
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
            "statement": "No validated citation matched this brief yet. Do not lock a scientific lead.",
            "why": "The working file has no DOI/PMID-backed row. Strategy stays behavioural until science is sourced.",
            "directs": "none",
            "citations": [],
            "doNotClaim": ["Any efficacy, safety, or guideline class statement"],
        }

    by_id = {r["id"]: r for r in matched}
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
        anchors = sorted(matched, key=lambda r: (0 if r.get("grade") == "A" else 1, r.get("year") or 0))

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
    return {
        "statement": statement,
        "why": (
            f"Highest-leverage validated row is {primary['short']} "
            f"({primary['journal']} {primary['year']}; PMID {primary.get('pmid') or '—'})."
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


def _pubmed_enrich(brief: ExtractedBrief, already: set[str]) -> list[dict[str, Any]]:
    term = _pubmed_term(brief)
    if not term:
        return []
    try:
        ids = _esearch(term, retmax=4)
        if not ids:
            return []
        summaries = _esummary(ids)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, ValueError):
        return []

    hits = []
    known_pmids = {e.get("pmid") for e in CATALOG}
    for pmid, doc in summaries.items():
        if pmid in known_pmids:
            continue
        title = doc.get("title") or ""
        journal = doc.get("fulljournalname") or doc.get("source") or ""
        year = _year(doc.get("pubdate") or "")
        authors = _author_line(doc.get("authors") or [])
        doi = _doi_from(doc)
        hits.append({
            "pmid": pmid,
            "title": title,
            "authors": authors,
            "year": year,
            "journal": journal,
            "doi": doi,
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            "citation": f"{authors} {title} {journal}. {year}." + (f" doi:{doi}" if doi else f" PMID {pmid}"),
            "status": "pubmed-retrieved",
            "note": "Independent PubMed hit — confirm against the full text before it can become a lead claim.",
        })
    return hits[:4]


def _pubmed_term(brief: ExtractedBrief) -> str:
    product = brief.product or ""
    indication = brief.indication or brief.therapy_area or ""
    bits = []
    if "sacubitril" in (product + indication).lower() or "hfref" in indication.lower() or "heart failure" in (brief.therapy_area or "").lower():
        bits.append("sacubitril valsartan HFrEF")
    elif "nsclc" in (indication + (brief.therapy_area or "")).lower() or "oncology" in (brief.therapy_area or "").lower():
        bits.append("pembrolizumab NSCLC first-line randomized")
    else:
        token = re.sub(r"[^A-Za-z0-9 +/()-]+", " ", f"{product} {indication}").strip()
        if len(token) < 8:
            return ""
        bits.append(f"{token} randomized")
    return " ".join(bits)


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
    with urllib.request.urlopen(
        f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?{q}",
        timeout=8,
    ) as resp:
        data = json.loads(resp.read().decode("utf-8"))
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
    with urllib.request.urlopen(
        f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?{q}",
        timeout=8,
    ) as resp:
        data = json.loads(resp.read().decode("utf-8"))
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
