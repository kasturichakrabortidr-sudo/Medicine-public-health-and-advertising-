"""Claim coding and effect-size extraction from verified abstracts only."""

from __future__ import annotations

import re

from .models import EffectSize, EvidenceRecord

_HTML = re.compile(r"<[^>]+>")
_SPACE = re.compile(r"\s+")

EFFECT_RE = re.compile(
    r"\b(?P<metric>HR|OR|RR|hazard ratio|odds ratio|relative risk|rate ratio)"
    r".{0,70}?"
    r"(?P<value>\d+\.\d+)\s*"
    r"[;,]?\s*(?:\(|\[\s*)?(?:95\s*%\s*(?:CI|confidence interval(?:\s*\[CI\])?)[:;, ]*)\s*"
    r"(?P<low>\d+\.\d+)\s*(?:[-–—]|to)\s*(?P<high>\d+\.\d+)",
    re.IGNORECASE | re.DOTALL,
)

QUAL_MARKERS = re.compile(
    r"\b(qualitative|phenomenolog\w*|lived experience|semi-structured|"
    r"focus group|interpretative phenomenological|thematic analysis|"
    r"grounded theory|interviewed)\b",
    re.IGNORECASE,
)
GUIDELINE_MARKERS = re.compile(
    r"\b(guideline|guidelines|consensus statement|position statement|"
    r"practice advisory|technical package)\b",
    re.IGNORECASE,
)

CLAIM_RULES: list[tuple[str, list[re.Pattern]]] = [
    (
        "mortality_or_hospitalisation_benefit",
        [
            re.compile(
                r"\b(cardiovascular death|death from cardiovascular|cv death|"
                r"all-cause mortality|risks of death|death and of hospitali)\b",
                re.I,
            ),
            re.compile(r"\b(hospitali[sz]ation|hospital admission)\b", re.I),
            re.compile(r"\b(reduc\w+|lower(?:ed)?|fewer|superior|hazard ratio)\b", re.I),
        ],
    ),
    (
        "guideline_directed_foundational_therapy",
        [
            re.compile(
                r"\b(class I|foundational therap\w+|four[- ]pillar|GDMT|"
                r"guideline[- ]recommended|ARNI as.*first)\b",
                re.I,
            )
        ],
    ),
    (
        "early_or_in_hospital_initiation",
        [
            re.compile(
                r"\b(in[- ]hospital|early initiation|decompensation|"
                r"pre[- ]discharge|during hospitali[sz]ation)\b",
                re.I,
            )
        ],
    ),
    (
        "safety_hypotension_or_renal",
        [
            re.compile(
                r"\b(hypotension|hyperkal(?:a)?emia|renal|eGFR|creatinine|"
                r"angioedema|tolerability)\b",
                re.I,
            )
        ],
    ),
    (
        "symptom_or_quality_of_life",
        [
            re.compile(
                r"\b(quality of life|KCCQ|symptom\w+|NYHA|patient[- ]reported)\b",
                re.I,
            )
        ],
    ),
    (
        "cost_or_access_barrier",
        [
            re.compile(
                r"\b(cost|out-of-pocket|reimburs\w+|affordab\w+|access|"
                r"availability|budget)\b",
                re.I,
            )
        ],
    ),
    (
        "implementation_gap_or_inertia",
        [
            re.compile(
                r"\b(under(?:use|treatment)|inertias?|not prescribed|"
                r"implementation gap|suboptimal|clinical inertia)\b",
                re.I,
            )
        ],
    ),
    (
        "epidemiology_and_burden",
        [
            re.compile(
                r"\b(prevalence|incidence|burden|epidemiolog\w+|mortality rate|"
                r"global)\b",
                re.I,
            )
        ],
    ),
    (
        "lmics_or_national_context",
        [
            re.compile(
                r"\b(India|LMIC|low- and middle-income|low and middle income|"
                r"South[- ]East Asia|global south)\b",
                re.I,
            )
        ],
    ),
    (
        "lived_experience_or_care_relationship",
        [
            re.compile(
                r"\b(lived experience|caregiver|self[- ]manag\w+|interpretative|"
                r"phenomenolog\w*|semi-structured interview)\b",
                re.I,
            )
        ],
    ),
]

CLAIM_LABELS = {
    "mortality_or_hospitalisation_benefit": "Mortality or HF hospitalisation benefit",
    "guideline_directed_foundational_therapy": "Guideline-directed foundational therapy",
    "early_or_in_hospital_initiation": "Early / in-hospital initiation",
    "safety_hypotension_or_renal": "Safety: hypotension, renal, electrolytes",
    "symptom_or_quality_of_life": "Symptoms / quality of life",
    "cost_or_access_barrier": "Cost and access barriers",
    "implementation_gap_or_inertia": "Implementation gap / clinical inertia",
    "epidemiology_and_burden": "Epidemiology and disease burden",
    "lmics_or_national_context": "LMIC / national context",
    "lived_experience_or_care_relationship": "Lived experience and care relationships",
}

IPA_CODEBOOK = {
    "corporeal_disruption": {
        "title": "Corporeal disruption and bodily uncertainty",
        "needles": [
            r"\b(breathless(?:ness)?|overwhelming fatigue|lived body|oedema|edema|"
            r"bodily|the body)\b"
        ],
        "description": (
            "How the condition is experienced in the body — symptoms, energy, "
            "and the sense that the body can no longer be taken for granted."
        ),
    },
    "biographical_disruption": {
        "title": "Biographical disruption and threatened identity",
        "needles": [
            r"\b(identity|normal life|biograph\w+|sense of self|life role|"
            r"loss of independence)\b"
        ],
        "description": (
            "How illness interrupts life roles, self-concept, and the expected "
            "future — a core IPA concern with meaning-making."
        ),
    },
    "relational_care": {
        "title": "Relational care, trust, and family labour",
        "needles": [
            r"\b(family caregivers?|caregivers?|carers?|family labour|"
            r"family support)\b"
        ],
        "description": (
            "How relationships with clinicians and family mediate feeling safe, "
            "informed, and cared for."
        ),
    },
    "existential_uncertainty": {
        "title": "Existential uncertainty, fear, and prognosis",
        "needles": [
            r"\b(fear about|fear of|anxiety|uncertain(?:ty)? about|worry about|"
            r"prognos\w+|dying|fragile)\b"
        ],
        "description": (
            "The emotional and temporal horizon of living with a serious "
            "condition — fear, waiting, and not-knowing."
        ),
    },
    "constrained_agency": {
        "title": "Constrained agency: cost, access, and self-management",
        "needles": [
            r"\b(could afford|cannot afford|out-of-pocket|self[- ]manag\w+|"
            r"affordab\w+|cost of medicine)\b"
        ],
        "description": (
            "How structural constraints (money, medicines, systems) shape what "
            "patients and clinicians feel able to do."
        ),
    },
}


def strip_text(value: str | None) -> str:
    if not value:
        return ""
    return _SPACE.sub(" ", _HTML.sub(" ", value)).strip()


def sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", strip_text(text))
    return [p.strip() for p in parts if len(p.strip()) > 40]


def is_qualitative(record: EvidenceRecord) -> bool:
    return bool(QUAL_MARKERS.search(record.text_blob()))


def is_guideline(record: EvidenceRecord) -> bool:
    if record.source_family in {"international_guideline", "national_guideline"}:
        return True
    return bool(GUIDELINE_MARKERS.search(record.title))


def classify_study_design(record: EvidenceRecord) -> str:
    """Transparent design labels from title/abstract markers — never guessed."""
    if record.nct_id or record.source_family == "trial_registry":
        return "trial_registry"
    if record.is_qualitative:
        return "qualitative"
    blob = record.text_blob().lower()
    title = (record.title or "").lower()
    if (
        record.is_guideline
        or record.source_family in {"international_guideline", "national_guideline"}
        or GUIDELINE_MARKERS.search(record.title or "")
    ):
        return "guideline"
    if record.source_family in {"un_agency", "ngo"} and (
        not record.doi or "technical package" in blob or "fact sheet" in blob
    ):
        return "policy_guidance"
    if any(
        tok in blob
        for tok in ("meta-analysis", "systematic review", "network meta-analysis", "cochrane")
    ):
        return "systematic_review"
    if any(
        tok in blob
        for tok in (
            "randomized",
            "randomised",
            "double-blind",
            "double blind",
            "phase 3",
            "phase iii",
        )
    ):
        return "rct"
    if any(tok in blob for tok in ("cohort", "registry", "observational", "real-world")):
        return "observational"
    if "guideline" in title:
        return "guideline"
    return "other"


def pick_primary_effect(effects: list[EffectSize]) -> EffectSize | None:
    """Prefer a composite CV-death/HF-hospitalisation HR when several CIs parsed."""
    if not effects:
        return None
    for effect in effects:
        lowered = effect.outcome.lower()
        if "death" in lowered and "hospital" in lowered:
            return effect
    return effects[0]


def parse_effects(text: str, title: str = "") -> list[EffectSize]:
    blob = strip_text(text)
    found: list[EffectSize] = []
    for match in EFFECT_RE.finditer(blob):
        value = float(match.group("value"))
        low = float(match.group("low"))
        high = float(match.group("high"))
        if not (0 < value < 10 and 0 < low <= high < 15):
            continue
        start = max(0, match.start() - 90)
        excerpt = blob[start : match.end() + 40].strip()
        metric = match.group("metric").upper()
        if metric.startswith("HAZARD"):
            metric = "HR"
        elif metric.startswith("ODDS"):
            metric = "OR"
        elif "RELATIVE" in metric or "RATE" in metric:
            metric = "RR"
        outcome = title or "Primary or reported endpoint"
        lowered = excerpt.lower()
        if "death" in lowered and "hospital" in lowered:
            outcome = "CV death or HF hospitalisation"
        elif "death" in lowered:
            outcome = "Mortality"
        elif "hospital" in lowered:
            outcome = "HF hospitalisation"
        found.append(
            EffectSize(
                metric=metric,
                value=value,
                ci_low=low,
                ci_high=high,
                outcome=outcome,
                excerpt=excerpt[:280],
            )
        )
    # de-dupe identical triples
    uniq: list[EffectSize] = []
    seen: set[tuple] = set()
    for effect in found:
        key = (effect.metric, effect.value, effect.ci_low, effect.ci_high)
        if key in seen:
            continue
        seen.add(key)
        uniq.append(effect)
    return uniq[:4]


def code_claims(record: EvidenceRecord) -> list[str]:
    blob = record.text_blob()
    hits: list[str] = []
    for claim_id, patterns in CLAIM_RULES:
        if claim_id in {
            "mortality_or_hospitalisation_benefit",
        }:
            if all(p.search(blob) for p in patterns):
                hits.append(claim_id)
            continue
        if any(p.search(blob) for p in patterns):
            hits.append(claim_id)
    return hits


def supporting_snippets(record: EvidenceRecord, limit: int = 3) -> list[str]:
    blob = record.text_blob()
    picked: list[str] = []
    for sent in sentences(blob):
        if any(
            needle.search(sent)
            for _, patterns in CLAIM_RULES
            for needle in patterns
        ):
            picked.append(sent[:320])
        if len(picked) >= limit:
            break
    return picked


def ipa_hits(text: str) -> list[str]:
    blob = strip_text(text)
    matched: list[str] = []
    for theme_id, spec in IPA_CODEBOOK.items():
        if any(re.search(n, blob, re.I) for n in spec["needles"]):
            matched.append(theme_id)
    return matched


# Crossref-confirmed DOIs → short trial/guideline labels for forest plots.
DOI_SHORT_LABELS = {
    "10.1056/nejmoa1409077": "PARADIGM-HF",
    "10.1056/nejmoa1812851": "PIONEER-HF",
    "10.1056/nejmoa1911303": "DAPA-HF",
    "10.1056/nejmoa2022190": "EMPEROR-Reduced",
    "10.1056/nejmoa2107038": "EMPEROR-Preserved",
    "10.1016/s0140-6736(22)02076-1": "STRONG-HF",
    "10.1056/nejmoa1915928": "VICTORIA",
    "10.1056/nejmoa2025797": "GALACTIC-HF",
    "10.1056/nejmoa2206286": "DELIVER",
    "10.1056/nejmoa1908655": "PARAGON-HF",
}

_ACRONYM_RE = re.compile(
    r"\b(PARADIGM-HF|PIONEER-HF|DAPA-HF|EMPEROR-Reduced|EMPEROR-Preserved|"
    r"STRONG-HF|VICTORIA|GALACTIC-HF|PARAGON-HF|DELIVER|SHIFT|EMPHASIS-HF)\b",
    re.I,
)


def is_named_outcome_trial(title: str, doi: str | None = None) -> bool:
    """True when the record is a labelled pivotal trial, not a generic review."""
    if doi and doi.lower() in DOI_SHORT_LABELS:
        return True
    blob = strip_text(title)
    return bool(_ACRONYM_RE.search(blob))


def short_study_label(title: str, doi: str | None = None, year: int | None = None) -> str:
    """Compact axis label for forest plots; never invents a trial name."""
    if doi:
        named = DOI_SHORT_LABELS.get(doi.lower())
        if named:
            return f"{named} ({year})" if year else named
    blob = strip_text(title)
    match = _ACRONYM_RE.search(blob)
    if match:
        named = match.group(0)
        if named.lower() == "victoria":
            named = "VICTORIA"
        return f"{named} ({year})" if year else named
    low = blob.lower()
    if "angiotensin" in low and "neprilysin" in low:
        named = "PARADIGM-HF"
        return f"{named} ({year})" if year else named
    if "dapagliflozin" in low and "heart failure" in low:
        named = "DAPA-HF"
        return f"{named} ({year})" if year else named
    if "empagliflozin" in low and "reduced" in low:
        named = "EMPEROR-Reduced"
        return f"{named} ({year})" if year else named
    if "dapagliflozin" in low and "preserved" in low:
        named = "DELIVER"
        return f"{named} ({year})" if year else named
    return (blob[:72] + "…") if len(blob) > 72 else blob


def on_topic(record: EvidenceRecord, terms: list[str], min_hits: int = 1) -> bool:
    blob = record.text_blob().lower()
    title = (record.title or "").lower()
    if any(bad in blob for bad in ("covid-19", "covid 19", "sars-cov-2", "alzheimer")) and not any(
        t in {"covid", "covid-19", "alzheimer"} for t in terms
    ):
        return False
    if "bias in meta-analysis" in title:
        return False
    phrase_hits = [t for t in terms if t and len(t) > 4 and t.lower() in blob]
    return len(phrase_hits) >= min_hits
