"""Turn a client brief into structured PICO questions and search strings."""

from __future__ import annotations

import re

THERAPY_SYNONYMS: dict[str, list[str]] = {
    "heart failure": [
        "HFrEF",
        "HFpEF",
        "chronic heart failure",
        "ARNI",
        "sacubitril",
        "valsartan",
        "cardiomyopathy",
        "GDMT",
        "heart failure",
    ],
    "cardiology": [
        "cardiovascular",
        "heart failure",
        "hypertension",
        "ischemic heart",
    ],
    "diabetes": ["T2DM", "glycaemic", "SGLT2", "insulin", "diabetes"],
    "oncology": ["cancer", "tumour", "tumor", "chemotherapy"],
    "hiv": ["antiretroviral", "UNAIDS", "AIDS", "HIV"],
}

STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "chronic",
    "adult",
    "adults",
    "class",
    "fixed",
    "dose",
    "combination",
    "illustrative",
    "example",
    "failure",  # too generic alone (hepatic failure, treatment failure)
    "area",
    "market",
    "india",  # country is for search, not screening
    "metro",
    "tier",
}


def sanitize(text: str | None) -> str:
    if not text:
        return ""
    cleaned = re.sub(r"\(.*?\)", " ", str(text))
    cleaned = cleaned.split(",")[0]
    return re.sub(r"\s+", " ", cleaned).strip()


def short_concept(brief: dict) -> str:
    indication = sanitize(brief.get("indication"))
    therapy = sanitize(brief.get("therapy_area"))
    if indication:
        return indication
    return therapy or "public health"


def product_concept(brief: dict) -> str:
    return sanitize(brief.get("product") or brief.get("brand"))


def expand_terms(brief: dict) -> list[str]:
    blob = " ".join(
        str(brief.get(k) or "")
        for k in ("therapy_area", "indication", "product", "brand")
    )
    lowered = blob.lower()
    terms: list[str] = []
    for field in (brief.get("indication"), brief.get("product"), brief.get("brand")):
        s = sanitize(field)
        if s:
            terms.append(s)
    for stem, extras in THERAPY_SYNONYMS.items():
        if stem in lowered:
            terms.append(stem)
            terms.extend(extras)
    # keep longer tokens only
    for tok in re.split(r"[^A-Za-z0-9+/.-]+", blob):
        if len(tok) >= 5 and tok.lower() not in STOPWORDS:
            terms.append(tok)
    seen: set[str] = set()
    out: list[str] = []
    for t in terms:
        key = t.lower()
        if key in STOPWORDS or key in seen:
            continue
        seen.add(key)
        out.append(t)
    return out


def pico(brief: dict) -> dict:
    population = sanitize(brief.get("indication")) or sanitize(brief.get("therapy_area")) or "target cohort"
    intervention = product_concept(brief) or "index intervention"
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
    product = product_concept(brief)
    indication = short_concept(brief)
    therapy = sanitize(brief.get("therapy_area"))
    market = sanitize(re.split(r"[,(]", str(brief.get("market") or ""))[0])
    disease = indication if indication.lower() != therapy.lower() else indication
    # Prefer a human disease phrase for title searches
    disease_phrase = "heart failure" if "heart failure" in f"{therapy} {indication}".lower() else disease
    core = " ".join(x for x in (product, disease_phrase) if x)

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
            "europe_pmc": f'(TITLE:guideline OR TITLE:"consensus statement" OR TITLE:"position statement") AND ("{disease_phrase}")',
            "openalex": f"{disease_phrase} guideline heart failure" if disease_phrase else f"{therapy} guideline",
        },
        {
            "id": "qualitative",
            "purpose": "Lived experience / IPA-eligible qualitative literature",
            "europe_pmc": (
                f'TITLE:"{disease_phrase}" AND '
                f'("lived experience" OR phenomenological OR "qualitative study" '
                f'OR "qualitative research" OR "semi-structured")'
            ),
            "openalex": f'"{disease_phrase}" "lived experience" qualitative',
        },
        {
            "id": "burden_access",
            "purpose": "Epidemiology, cost, and access",
            "europe_pmc": f'("{disease_phrase}") AND (epidemiology OR burden OR cost OR access OR out-of-pocket)',
            "openalex": f"{disease_phrase} burden cost access",
        },
        {
            "id": "systematic_reviews",
            "purpose": "Cochrane and other systematic reviews",
            "europe_pmc": f'("{disease_phrase}") AND (systematic review OR meta-analysis OR Cochrane)',
            "openalex": f"{disease_phrase} systematic review meta-analysis",
        },
        {
            "id": "un_ncd",
            "purpose": "UN-system and NCD / UHC framing",
            "openalex": f"{disease_phrase} noncommunicable cardiovascular HEARTS",
            "who": disease_phrase,
        },
    ]
    if market:
        queries.append(
            {
                "id": "national",
                "purpose": f"National guidance and regional evidence ({market})",
                "europe_pmc": f'("{disease_phrase}") AND ({market})',
                "openalex": f"{disease_phrase} {market}",
            }
        )
    return queries


def relevance_terms(brief: dict) -> list[str]:
    return [t.lower() for t in expand_terms(brief)]
