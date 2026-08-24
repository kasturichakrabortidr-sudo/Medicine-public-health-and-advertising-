"""Turn a client brief into structured PICO questions and search strings."""

from __future__ import annotations

import re

THERAPY_SYNONYMS: dict[str, list[str]] = {
    "heart failure": [
        "HFrEF",
        "HFpEF",
        "chronic heart failure",
        "CHF",
        "ARNI",
        "sacubitril",
        "valsartan",
        "cardiomyopathy",
        "GDMT",
    ],
    "cardiology": [
        "cardiovascular",
        "heart failure",
        "hypertension",
        "ischemic heart",
        "NCD",
    ],
    "diabetes": ["T2DM", "glycaemic", "SGLT2", "insulin"],
    "oncology": ["cancer", "tumour", "tumor", "chemotherapy"],
    "hiv": ["antiretroviral", "UNAIDS", "AIDS"],
}


def _clean_terms(text: str) -> list[str]:
    parts = re.split(r"[^A-Za-z0-9+/.-]+", text or "")
    return [p for p in parts if len(p) >= 3]


def expand_terms(brief: dict) -> list[str]:
    blob = " ".join(
        str(brief.get(k) or "")
        for k in ("therapy_area", "indication", "product", "brand", "market")
    )
    terms = _clean_terms(blob)
    lowered = blob.lower()
    for stem, extras in THERAPY_SYNONYMS.items():
        if stem in lowered:
            terms.extend(extras)
    # de-dupe preserving order
    seen: set[str] = set()
    out: list[str] = []
    for t in terms:
        key = t.lower()
        if key not in seen:
            seen.add(key)
            out.append(t)
    return out


def pico(brief: dict) -> dict:
    population = brief.get("indication") or brief.get("therapy_area") or "target cohort"
    intervention = brief.get("product") or brief.get("brand") or "index intervention"
    goal = (brief.get("business_goal") or "").strip()
    outcome = (
        "clinical outcomes, guideline concordance, access/cost, and lived experience"
    )
    if "prescription" in goal.lower() or "initiation" in goal.lower():
        outcome = (
            "morbidity/mortality, hospitalisation, quality of life, "
            "guideline-directed uptake, and access barriers"
        )
    return {
        "population": population,
        "intervention": intervention,
        "comparator": "standard of care / incumbent therapy as reported in sources",
        "outcomes": outcome,
        "setting": brief.get("market") or "international plus national guidelines",
        "question": (
            f"In {population}, what validated evidence, guidelines, and "
            f"UN/NGO guidance describe the effects, implementation, and "
            f"lived experience of {intervention}?"
        ),
    }


def build_queries(brief: dict) -> list[dict]:
    product = (brief.get("product") or brief.get("brand") or "").strip()
    indication = (brief.get("indication") or brief.get("therapy_area") or "").strip()
    therapy = (brief.get("therapy_area") or "").strip()
    market = (brief.get("market") or "").strip()
    core = " ".join(x for x in (product, indication) if x)
    if not core:
        core = therapy or "public health"
    market_term = ""
    if market:
        # first token often the country
        market_term = re.split(r"[,(]", market)[0].strip()

    queries = [
        {
            "id": "primary_evidence",
            "purpose": "Pivotal and independent clinical evidence",
            "europe_pmc": f"({core}) AND (trial OR cohort OR meta-analysis OR systematic)",
            "openalex": core,
        },
        {
            "id": "guidelines",
            "purpose": "International and national guidelines",
            "europe_pmc": f'(TITLE:guideline OR TITLE:"consensus statement") AND ({therapy or indication})',
            "openalex": f"{therapy or indication} guideline",
        },
        {
            "id": "qualitative",
            "purpose": "Lived experience / IPA-eligible qualitative literature",
            "europe_pmc": (
                f'TITLE:("{indication or therapy}") AND '
                f'("lived experience" OR phenomenological OR "qualitative study" '
                f'OR "qualitative research" OR "semi-structured")'
            ),
            "openalex": f"{indication or therapy} lived experience qualitative",
        },
        {
            "id": "burden_access",
            "purpose": "Epidemiology, cost, and access",
            "europe_pmc": f"({indication or therapy}) AND (epidemiology OR burden OR cost OR access OR out-of-pocket)",
            "openalex": f"{indication or therapy} burden cost access",
        },
        {
            "id": "un_ncd",
            "purpose": "UN-system and NCD / UHC framing",
            "openalex": f"{therapy or indication} noncommunicable cardiovascular",
            "who": f"{indication or therapy}",
        },
    ]
    if market_term:
        queries.append(
            {
                "id": "national",
                "purpose": f"National guidance and regional evidence ({market_term})",
                "europe_pmc": f"({indication or therapy}) AND ({market_term})",
                "openalex": f"{indication or therapy} {market_term}",
            }
        )
    return queries


def relevance_terms(brief: dict) -> list[str]:
    return [t.lower() for t in expand_terms(brief)]
