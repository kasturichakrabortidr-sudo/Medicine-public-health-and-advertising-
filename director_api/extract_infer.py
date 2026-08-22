"""Turn messy brief prose into structured fields.

Client files are almost never YAML. They are titles, tables, labelled lines,
and bullets. This module fills empty ExtractedBrief fields from that prose
without inventing facts.
"""

from __future__ import annotations

import re

from .extract import ExtractedBrief, KNOWN_FIELDS, _as_list, _normalize_key

BRAND_STOP = {
    "confidential",
    "internal",
    "draft",
    "brief",
    "campaign",
    "campaign brief",
    "strategy",
    "title",
    "slide",
    "page",
    "client",
    "agency",
    "medical",
    "affairs",
    "legal",
    "working",
    "file",
    "objective",
    "insights",
    "evidence",
    "market",
    "product",
    "indication",
    "overview",
    "contents",
    "agenda",
    "appendix",
    "references",
    "thank you",
    "strictly confidential",
}

THERAPY_TERMS = (
    "cardiology",
    "oncology",
    "haematology",
    "hematology",
    "neurology",
    "respiratory",
    "pulmonology",
    "immunology",
    "dermatology",
    "endocrinology",
    "diabet",
    "nephrology",
    "gastroenterology",
    "rheumatology",
    "psychiatry",
    "ophthalmology",
    "urology",
    "infectious",
    "vaccine",
    "rare disease",
    "women's health",
    "heart failure",
    "hfref",
    "hfpef",
    "nsclc",
    "sclc",
    "breast cancer",
    "prostate",
    "copd",
    "asthma",
    "psoriasis",
    "rheumatoid",
    "ibd",
    "crohn",
    "ulcerative colitis",
    "ckd",
    "nash",
    "masld",
    "migraine",
    "ms ",
    "multiple sclerosis",
    "hiv",
    "hepatitis",
)

MARKET_RE = re.compile(
    r"\b(India|United Kingdom|United States|USA|U\.S\.A\.|UK|Great Britain|"
    r"EU|Europe|EMEA|APAC|LATAM|China|Brazil|Japan|Germany|France|Italy|"
    r"Spain|Australia|Canada|Mexico|Gulf|GCC|Saudi|UAE|Singapore|"
    r"South Korea|Korea|Taiwan|Thailand|Vietnam|Indonesia|Philippines|"
    r"South Africa|Nigeria|Egypt|Turkey|Poland|Nordics)\b",
    re.I,
)

LABEL_ALIASES = {
    "brand": "brand",
    "brand_name": "brand",
    "campaign": "brand",
    "campaign_name": "brand",
    "asset": "brand",
    "product": "product",
    "product_name": "product",
    "molecule": "product",
    "inn": "product",
    "compound": "product",
    "formulation": "product",
    "therapy": "therapy_area",
    "therapy_area": "therapy_area",
    "ta": "therapy_area",
    "disease_area": "therapy_area",
    "speciality": "therapy_area",
    "specialty_area": "therapy_area",
    "indication": "indication",
    "patient_group": "indication",
    "patients": "indication",
    "population": "indication",
    "market": "market",
    "country": "market",
    "geography": "market",
    "geo": "market",
    "region": "market",
    "business_goal": "business_goal",
    "goal": "business_goal",
    "objective": "business_goal",
    "objectives": "business_goal",
    "ambition": "business_goal",
    "commercial_objective": "business_goal",
    "aim": "business_goal",
    "kpi": "business_goal",
    "target_specialties": "target_specialties",
    "specialties": "target_specialties",
    "specialty": "target_specialties",
    "targets": "target_specialties",
    "target_hcps": "target_specialties",
    "hcp": "target_specialties",
    "hcps": "target_specialties",
    "physicians": "target_specialties",
    "doctors": "target_specialties",
    "audience": "target_specialties",
    "hcp_segments": "hcp_segments",
    "segments": "hcp_segments",
    "segmentation": "hcp_segments",
    "brand_evidence": "brand_evidence",
    "evidence": "brand_evidence",
    "clinical_data": "brand_evidence",
    "trials": "brand_evidence",
    "data": "brand_evidence",
    "existing_evidence": "existing_evidence",
    "independent_evidence": "existing_evidence",
    "evolving_evidence": "evolving_evidence",
    "pipeline_data": "evolving_evidence",
    "guidelines": "guidelines",
    "guideline": "guidelines",
    "guidance": "guidelines",
    "hcp_insights": "hcp_insights",
    "insights": "hcp_insights",
    "insight": "hcp_insights",
    "advisory": "hcp_insights",
    "voc": "hcp_insights",
    "voice_of_customer": "hcp_insights",
    "field_notes": "hcp_insights",
    "competitors": "competitors",
    "competitor": "competitors",
    "competition": "competitors",
    "soc": "competitors",
    "standard_of_care": "competitors",
    "access_and_cost": "access_and_cost",
    "access": "access_and_cost",
    "cost": "access_and_cost",
    "pricing": "access_and_cost",
    "affordability": "access_and_cost",
    "reimbursement": "access_and_cost",
    "constraints": "constraints",
    "constraint": "constraints",
    "mlr": "constraints",
    "compliance": "constraints",
    "ucpmp": "constraints",
    "notes": "notes",
    "context": "notes",
}

LIST_FIELDS = {
    "target_specialties",
    "hcp_segments",
    "brand_evidence",
    "existing_evidence",
    "evolving_evidence",
    "guidelines",
    "hcp_insights",
    "competitors",
    "access_and_cost",
    "constraints",
}


def fill_from_prose(brief: ExtractedBrief) -> ExtractedBrief:
    """Fill any empty fields from raw_text. Never overwrite a filled field."""
    blob = brief.raw_text or ""
    if not blob.strip():
        return brief
    _apply_labelled_blocks(brief, blob)
    _apply_table_rows(brief, blob)
    if not brief.brand:
        brief.brand = _guess_brand(blob)
    if not brief.product:
        brief.product = _labelled_line(blob, ("product", "molecule", "inn", "compound")) or _guess_product(blob)
    if not brief.therapy_area:
        brief.therapy_area = _labelled_line(blob, ("therapy area", "therapy_area", "ta", "disease area")) or _guess_therapy(blob)
    if not brief.indication:
        brief.indication = _labelled_line(blob, ("indication", "patient group", "population"))
    if not brief.market:
        brief.market = _labelled_line(blob, ("market", "country", "geography", "region", "geo")) or _guess_market(blob)
    if not brief.business_goal:
        brief.business_goal = _labelled_line(blob, ("objective", "objectives", "goal", "ambition", "kpi", "aim")) or _guess_goal(blob)
    for field, needles in (
        ("target_specialties", ("target", "specialty", "specialties", "hcp", "physician", "doctor", "audience")),
        ("hcp_insights", ("insight", "advisory", "field note", "voc", "belief")),
        ("brand_evidence", ("evidence", "trial", "rct", "data", "study")),
        ("guidelines", ("guideline", "guidance", "nice", "esc", "acc", "who ")),
        ("competitors", ("competitor", "competition", "standard of care", "soc")),
        ("access_and_cost", ("access", "cost", "price", "afford", "reimburs", "oop")),
        ("constraints", ("mlr", "compliance", "ucpmp", "constraint", "code")),
        ("hcp_segments", ("segment", "kol", "tier-2", "metro")),
    ):
        if not getattr(brief, field):
            setattr(brief, field, _section_bullets(blob, needles))
    if not brief.notes:
        brief.notes = _labelled_line(blob, ("notes", "context", "background")) or ""
    return brief


def _apply_labelled_blocks(brief: ExtractedBrief, blob: str) -> None:
    current = None
    bucket: list[str] = []

    def flush():
        nonlocal current, bucket
        if current:
            _put(brief, current, bucket)
        current = None
        bucket = []

    for raw_line in blob.splitlines():
        line = raw_line.strip().lstrip("•-*").strip()
        if not line or re.match(r"^(page|slide)\s+\d+\b", line, re.I):
            continue
        key, rest = _line_label(line)
        if not key:
            pipe = re.match(r"^(.{2,40}?)\s*\|\s*(.+)$", line)
            if pipe:
                mapped = LABEL_ALIASES.get(_normalize_key(pipe.group(1)))
                if mapped in KNOWN_FIELDS:
                    key, rest = mapped, pipe.group(2).strip()
        if key:
            flush()
            current = key
            if rest:
                bucket.append(rest)
            continue
        if current:
            bucket.append(line)
    flush()


def _apply_table_rows(brief: ExtractedBrief, blob: str) -> None:
    for line in blob.splitlines():
        s = line.strip()
        m = re.match(r"^(.{2,40}?)\s*\|\s*(.+)$", s)
        if not m:
            m = re.match(r"^(.{2,40}?)\t+(.+)$", s)
        if not m:
            continue
        key = LABEL_ALIASES.get(_normalize_key(m.group(1)))
        if key in KNOWN_FIELDS:
            _put(brief, key, m.group(2))


def _line_label(line: str) -> tuple[str | None, str]:
    m = re.match(r"^([A-Za-z][A-Za-z0-9 /_&-]{1,42})\s*[:\-–]\s*(.*)$", line)
    if m:
        key = LABEL_ALIASES.get(_normalize_key(m.group(1)))
        if key in KNOWN_FIELDS:
            return key, m.group(2).strip()
    compact = re.sub(r"\s+", " ", line).strip(" :")
    key = LABEL_ALIASES.get(_normalize_key(compact))
    if key in KNOWN_FIELDS and len(compact.split()) <= 4:
        return key, ""
    return None, ""


def _put(brief: ExtractedBrief, key: str, value) -> None:
    if key not in KNOWN_FIELDS:
        return
    if key in LIST_FIELDS:
        items = _as_list(value)
        existing = list(getattr(brief, key) or [])
        for item in items:
            if item and item not in existing:
                existing.append(item)
        if existing and not getattr(brief, key):
            setattr(brief, key, existing)
        elif existing:
            setattr(brief, key, existing)
        return
    text = value if isinstance(value, str) else "; ".join(_as_list(value))
    text = _clean_scalar(text)
    if text and not getattr(brief, key):
        setattr(brief, key, text)


def _clean_scalar(text: str) -> str:
    text = re.sub(r"\s+", " ", (text or "")).strip(" -–|:;")
    if len(text) > 400:
        text = text[:397].rstrip() + "…"
    return text


def _labelled_line(blob: str, labels: tuple[str, ...]) -> str:
    for label in labels:
        m = re.search(rf"(?im)^\s*{re.escape(label)}\s*[:\-–]\s*(.+)$", blob)
        if m:
            return _clean_scalar(m.group(1))
    return ""


def _guess_brand(blob: str) -> str:
    m = re.search(
        r"(?im)(?:brand(?:\s*name)?|campaign(?:\s*name)?)\s*[:\-–]\s*"
        r"([A-Z][A-Za-z0-9®™\-]{1,40}(?:\s+[A-Z][A-Za-z0-9®™\-]{1,20}){0,3})",
        blob,
    )
    if m and not _is_stop(m.group(1)):
        return _clean_scalar(m.group(1))
    m = re.search(
        r"(?im)(?:campaign brief|brand brief)\s+([A-Z][A-Za-z0-9®™\-]{2,40})\b",
        blob,
    )
    if m and not _is_stop(m.group(1)):
        return _clean_scalar(m.group(1))
    for line in blob.splitlines()[:25]:
        s = line.strip().lstrip("#").strip()
        if re.match(r"^(page|slide)\s+\d+", s, re.I):
            continue
        if "|" in s or len(s) > 48 or len(s) < 2:
            continue
        if s.isupper() and 2 <= len(s.split()) <= 3 and not _is_stop(s):
            return _title_brand(s)
        if re.fullmatch(r"[A-Z][A-Za-z0-9®™\-]+(?:\s+[A-Z][A-Za-z0-9®™\-]+){0,2}", s) and not _is_stop(s):
            if s.lower() not in THERAPY_TERMS and "brief" not in s.lower():
                return s
    return ""


def _guess_product(blob: str) -> str:
    m = re.search(
        r"\b([a-z]{5,}(?:mab|nib|tide|sartan|gliptin|gliflozin|olol|pril|statin|parin))\b",
        blob,
        re.I,
    )
    return m.group(1) if m else ""


def _guess_therapy(blob: str) -> str:
    low = blob.lower()
    for term in THERAPY_TERMS:
        if term in low:
            m = re.search(rf"(.{{0,20}}{re.escape(term)}.{{0,40}})", blob, re.I)
            if m:
                return _clean_scalar(m.group(1))
    return ""


def _guess_market(blob: str) -> str:
    found = MARKET_RE.findall(blob)
    if not found:
        return ""
    # Preserve first distinct mention, keep original casing from the match
    seen = []
    for item in found:
        if item.lower() not in {s.lower() for s in seen}:
            seen.append(item)
    return ", ".join(seen[:4])


def _guess_goal(blob: str) -> str:
    for line in blob.splitlines():
        s = line.strip().lstrip("•-*").strip()
        if re.search(r"\b(grow|increase|launch|share|qoq|prescription|uptake|switch)\b", s, re.I):
            if 20 <= len(s) <= 280:
                return _clean_scalar(s)
    return ""


def _section_bullets(blob: str, needles: tuple[str, ...]) -> list[str]:
    lines = blob.splitlines()
    out: list[str] = []
    capture = False
    for line in lines:
        s = line.strip()
        low = s.lower()
        if any(n in low for n in needles) and (s.endswith(":") or len(s.split()) <= 6):
            capture = True
            rest = re.sub(r"^[^:]+:\s*", "", s).strip()
            if rest and rest.lower() not in needles:
                out.append(_clean_scalar(rest))
            continue
        if capture:
            if not s:
                if out:
                    break
                continue
            if _line_label(s)[0]:
                break
            pipe = re.match(r"^(.{2,40}?)\s*\|\s*(.+)$", s)
            if pipe and LABEL_ALIASES.get(_normalize_key(pipe.group(1))) in KNOWN_FIELDS:
                break
            if s.startswith(("#", "##")) and len(s.split()) <= 6:
                break
            cleaned = s.lstrip("•-*").strip()
            if cleaned:
                out.append(_clean_scalar(cleaned))
            if len(out) >= 8:
                break
    return out


def _is_stop(text: str) -> bool:
    return re.sub(r"\s+", " ", text or "").strip().lower() in BRAND_STOP


def _title_brand(text: str) -> str:
    return " ".join(w.capitalize() if w.isupper() else w for w in text.split())
