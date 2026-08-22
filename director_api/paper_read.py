"""Read PubMed abstracts and pull findings that can drive strategy.

A title list is not science. We fetch the abstract, take numbers and
conclusions that are actually written there, and drop near-duplicate hits.
We never invent a hazard ratio that the abstract does not state.
"""

from __future__ import annotations

import os
import re
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any

HR_RE = re.compile(
    r"\b(?:hazard ratio|HR)\s*(?:of|=|:)?\s*(\d+\.\d+)"
    r"(?:\s*[;(,]?\s*(?:95%\s*CI[:\s]*)(\d+\.\d+)\s*(?:to|[–\-])\s*(\d+\.\d+))?",
    re.I,
)
PASI_RE = re.compile(r"\bPASI\s*(75|90|100)\b", re.I)
PCT_VS_RE = re.compile(
    r"(?<![\d.])(\d{1,2}(?:\.\d+)?)\s*%[^%]{0,70}?(?:versus|vs\.?|compared with)[^%]{0,40}?(?<![\d.])(\d{1,2}(?:\.\d+)?)\s*%",
    re.I | re.S,
)
PCT_AND_RE = re.compile(
    r"(?<![\d.])(\d{1,2}(?:\.\d+)?)\s*%[^%]{0,80}?\band in\b[^%]{0,40}?(?<![\d.])(\d{1,2}(?:\.\d+)?)\s*%",
    re.I | re.S,
)
PASI_PAREN_VS_RE = re.compile(
    r"PASI\s*(75|90|100).{0,180}?\((\d{1,2}(?:\.\d+)?)%\)[^.]*?(?:versus|vs\.?)\s+[^.]*?\((\d{1,2}(?:\.\d+)?)%\)",
    re.I | re.S,
)
PASI_SLASH_RE = re.compile(
    r"(?P<w90>\d{1,2}(?:\.\d+)?)%/(?P<w100>\d{1,2}(?:\.\d+)?)%\s+of patients achieved PASI\s*90/100",
    re.I,
)
PASI_SINGLE_RE = re.compile(
    r"(?<!/)(?P<a>\d{1,2}(?:\.\d+)?)\s*%\s+of patients achieved PASI\s*(?P<lvl1>75|90|100)"
    r"|PASI\s*(?P<lvl2>75|90|100)[^\d%]{0,48}?(?P<b>\d{1,2}(?:\.\d+)?)\s*%",
    re.I,
)
N_RE = re.compile(
    r"\b(?:n\s*=\s*(\d{2,5})|(\d{2,5})\s+patients|randomi[sz]ed\s+(?:n\s*=\s*)?(\d{2,5}))\b",
    re.I,
)
TRIAL_CAMEL_RE = re.compile(r"\b([A-Z]{2,}[a-z]+[A-Za-z0-9-]*)\b")
TRIAL_MIXED_RE = re.compile(r"\b([A-Z][a-z]+[A-Z][a-zA-Z0-9-]+)\b")
TRIAL_HYPHEN_RE = re.compile(r"\b([A-Z]{2,}[A-Z0-9]*(?:-[A-Z0-9]+)+)\b")
GENERIC_TITLE = re.compile(
    r"network meta-analysis|mechanism of action|translational science|"
    r"narrative review|expert opinion|validation study",
    re.I,
)
PRODUCT_STOP = {
    "chronic", "acute", "plaque", "severe", "moderate", "patients", "study",
}


def fetch_abstracts(pmids: list[str]) -> dict[str, dict[str, Any]]:
    """NCBI efetch XML → pmid -> {abstract, sections, pubtypes, pages}."""
    ids = [p for p in pmids if p]
    if not ids:
        return {}
    params = {
        "db": "pubmed",
        "id": ",".join(ids),
        "rettype": "abstract",
        "retmode": "xml",
        "tool": "strata-director",
        "email": "strata-director@local",
    }
    api_key = os.environ.get("NCBI_API_KEY") or os.environ.get("PUBMED_API_KEY")
    if api_key:
        params["api_key"] = api_key
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "STRATA-director/1.0 (https://pubmed.ncbi.nlm.nih.gov/)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=16) as resp:
            raw = resp.read()
    except (urllib.error.URLError, TimeoutError, OSError):
        return {}
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return {}
    out: dict[str, dict[str, Any]] = {}
    for art in root.findall(".//PubmedArticle"):
        pmid_el = art.find(".//MedlineCitation/PMID")
        pmid = (pmid_el.text or "").strip() if pmid_el is not None else ""
        if not pmid:
            continue
        labeled: dict[str, str] = {}
        chunks: list[str] = []
        for node in art.findall(".//Abstract/AbstractText"):
            text = _normalize("".join(node.itertext()).strip())
            if not text:
                continue
            label = (node.get("Label") or "").strip().upper()
            if label:
                labeled[label] = text
                chunks.append(f"{label}: {text}")
            else:
                chunks.append(text)
        pubtypes = [p.text for p in art.findall(".//PublicationType") if p.text]
        pages = (art.findtext(".//MedlinePgn") or "").strip()
        out[pmid] = {
            "abstract": " ".join(chunks),
            "sections": labeled,
            "pubtypes": pubtypes,
            "pages": pages,
        }
    return out


def extract_finding(
    title: str,
    abstract: str,
    product: str = "",
    sections: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Pull a claim, numbers, and trial name that are written in the abstract."""
    title = _normalize(title or "")
    abstract = _normalize(abstract or "")
    sections = {k.upper(): _normalize(v) for k, v in (sections or {}).items()}
    blob = f"{title}. {abstract}".strip()
    results = (
        _section_from(sections, ("RESULTS", "FINDINGS", "OUTCOMES"))
        or _sectionish(abstract, ("RESULTS", "FINDINGS", "OUTCOMES"))
    )
    conclusions = (
        _section_from(sections, ("CONCLUSIONS", "CONCLUSION", "INTERPRETATION"))
        or _sectionish(abstract, ("CONCLUSIONS", "CONCLUSION", "INTERPRETATION"))
    )
    methods = (
        _section_from(sections, ("METHODS", "METHOD"))
        or _sectionish(abstract, ("METHODS", "METHOD"))
    )
    number_text = results or blob

    hr = low = high = None
    m = HR_RE.search(number_text) or HR_RE.search(blob)
    if m:
        hr = float(m.group(1))
        if m.group(2) and m.group(3):
            low, high = float(m.group(2)), float(m.group(3))

    n = None
    nm = N_RE.search(methods or "") or N_RE.search(blob)
    if nm:
        n = int(next(g for g in nm.groups() if g))

    pasi = PASI_RE.search(number_text) or PASI_RE.search(blob)
    treat_pct, control_pct, endpoint_hint, comparator = _rate_pair(number_text, blob, pasi, hr)

    trial = _trial_name(title, abstract, product)
    endpoint = ""
    if pasi:
        endpoint = f"PASI {pasi.group(1)}"
        week = re.search(r"week\s+(\d+)", number_text or blob, re.I)
        if week:
            endpoint += f" at week {week.group(1)}"
        if endpoint_hint:
            endpoint = endpoint_hint
    elif hr is not None:
        endpoint = f"HR {hr}" + (f" (95% CI {low}–{high})" if low is not None else "")

    claim = _claim_sentence(
        conclusions, results, title, product, trial, endpoint,
        treat_pct, control_pct, hr, comparator,
    )
    numeric = hr is not None or treat_pct is not None
    return {
        "trial": trial,
        "finding": claim,
        "claim": claim,
        "hr": hr,
        "low": low,
        "high": high,
        "n": n,
        "endpoint": endpoint,
        "treat_event": treat_pct,
        "control_event": control_pct,
        "comparator": comparator,
        "effect_metric": "HR" if hr is not None else ("% response" if treat_pct is not None else None),
        "numeric": numeric,
        "title_only": (not numeric) and _is_title_claim(claim, title),
    }


def select_papers(
    hits: list[dict[str, Any]],
    brief: Any,
    readings: dict[str, dict[str, Any]],
    *,
    limit: int = 4,
) -> list[dict[str, Any]]:
    """Keep a short, non-duplicate set of load-bearing papers."""
    product = getattr(brief, "product", "") or ""
    parsed_map: dict[str, dict[str, Any]] = {}
    scored: list[tuple[int, dict, dict]] = []
    for hit in hits:
        pmid = str(hit.get("pmid") or "")
        reading = readings.get(pmid) or {}
        parsed = extract_finding(
            hit.get("title") or "",
            reading.get("abstract") or "",
            product,
            sections=reading.get("sections"),
        )
        parsed_map[pmid] = parsed
        score = _score(hit, product, reading, parsed)
        scored.append((score, hit, parsed))
    scored.sort(key=lambda row: -row[0])

    any_numeric = any(row[2].get("numeric") for row in scored if row[0] > 0)
    chosen: list[dict] = []
    seen_keys: set[str] = set()
    seen_roles: set[str] = set()
    pending: list[tuple[int, dict, dict]] = []
    for score, hit, parsed in scored:
        if score < 1:
            continue
        if any_numeric and not parsed.get("numeric") and chosen:
            continue
        if not _mentions_product(hit.get("title") or "", (readings.get(str(hit.get("pmid") or "")) or {}).get("abstract") or "", product):
            continue
        key = _dedupe_key(hit, parsed)
        if key in seen_keys:
            continue
        role = guess_role(hit, parsed)
        if chosen and role in seen_roles:
            pending.append((score, hit, parsed))
            continue
        seen_keys.add(key)
        seen_roles.add(role)
        chosen.append(hit)
        if len(chosen) >= limit:
            break
    for score, hit, parsed in pending:
        if len(chosen) >= limit:
            break
        key = _dedupe_key(hit, parsed)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        chosen.append(hit)
    if not chosen:
        for score, hit, parsed in scored:
            key = _dedupe_key(hit, parsed)
            if key in seen_keys or score < 0:
                continue
            seen_keys.add(key)
            chosen.append(hit)
            if len(chosen) >= min(2, limit):
                break
    return chosen


def apply_reading(
    record: dict[str, Any],
    reading: dict[str, Any] | None,
    brief: Any,
) -> dict[str, Any]:
    """Write extracted findings onto a PubMed record and tie them to the brief."""
    title = record.get("title") or ""
    abstract = (reading or {}).get("abstract") or ""
    product = getattr(brief, "product", "") or ""
    parsed = extract_finding(title, abstract, product, sections=(reading or {}).get("sections"))
    pages = (reading or {}).get("pages") or record.get("pages") or ""
    pubtypes = (reading or {}).get("pubtypes") or []
    design = record.get("design") or (pubtypes[0] if pubtypes else "PubMed record")

    record["trial"] = parsed["trial"] or record.get("trial") or ""
    if parsed["trial"]:
        year = record.get("year") or ""
        record["short"] = f"{parsed['trial']} ({year})".strip() if year else parsed["trial"]
    record["finding"] = parsed["finding"]
    record["claim_permitted"] = parsed["claim"]
    record["endpoint"] = parsed["endpoint"]
    record["n"] = parsed["n"] or record.get("n")
    record["pages"] = pages
    record["design"] = design
    record["abstract"] = abstract[:1200]
    record["numeric"] = parsed["numeric"]
    if parsed["hr"] is not None:
        record["hr"] = parsed["hr"]
        record["low"] = parsed["low"]
        record["high"] = parsed["high"]
        record["effect_metric"] = "HR"
    if parsed["treat_event"] is not None:
        record["treat_event"] = parsed["treat_event"]
        if parsed["control_event"] is not None:
            record["control_event"] = parsed["control_event"]
            if parsed["hr"] is not None and parsed["hr"] < 1:
                arr = round(parsed["control_event"] - parsed["treat_event"], 1)
                if arr > 0:
                    record["arr"] = arr
                    record["nnt"] = max(1, round(100 / arr))
                    record["visual_unit"] = "events per 100 patients (from abstract)"
            else:
                record["visual_unit"] = "response rate (%) from abstract"
        else:
            record["visual_unit"] = "response rate (%) from abstract"
    record["grade"] = _grade(design, parsed)
    record["directs"] = _directs(title, abstract, design)
    record["comparator"] = parsed.get("comparator") or record.get("comparator") or ""
    record["spine_barrier"] = _barrier(brief)
    record["spine_means"] = parsed["claim"]
    record["spine_execute"] = _execute_for(record["directs"], brief)
    record["spine_measure"] = (
        f"Unaided recall of the sourced finding ({parsed['endpoint'] or 'the numbered result'})"
    )
    record["caveat"] = (
        "Finding taken from the PubMed abstract. Confirm the full text and local label "
        "before promotional use. Do not add numbers that are not in the abstract."
    )
    record["mlr"] = "Abstract-sourced finding. Full-text and label check required."
    return record


def _normalize(text: str) -> str:
    if not text:
        return ""
    text = (
        text.replace("\u00b7", ".")
        .replace("\u2219", ".")
        .replace("\u2022", ".")
        .replace("\u2212", "-")
        .replace("\u2013", "-")
        .replace("\u2014", "-")
    )
    text = re.sub(r"[\u00a0\u202f\u2007\u2009\u200a]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _section_from(sections: dict[str, str], labels: tuple[str, ...]) -> str:
    for label in labels:
        if sections.get(label):
            return sections[label]
    return ""


def _sectionish(abstract: str, labels: tuple[str, ...]) -> str:
    if not abstract:
        return ""
    for label in labels:
        m = re.search(
            rf"{label}\s*:\s*(.+?)(?=(?:BACKGROUND|OBJECTIVE|OBJECTIVES|METHODS|METHOD|RESULTS|FINDINGS|CONCLUSIONS|CONCLUSION|INTERPRETATION|FUNDING)\s*:|$)",
            abstract,
            re.I | re.S,
        )
        if m:
            return m.group(1).strip()
    return ""


def _rate_pair(results: str, blob: str, pasi, hr) -> tuple[float | None, float | None, str, str]:
    text = results or blob
    endpoint_hint = ""
    comparator = "the comparator"

    paren = PASI_PAREN_VS_RE.search(text) or PASI_PAREN_VS_RE.search(blob)
    if paren and not re.search(r"\band\b.{0,40}patients", paren.group(0).split("%")[0], re.I):
        lvl, a, b = paren.group(1), float(paren.group(2)), float(paren.group(3))
        treat, control = (a, b) if a >= b else (b, a)
        window = text[paren.start(): min(len(text), paren.end() + 48)]
        comparator = _comparator_label(window)
        week = re.search(r"week\s+(\d+)", window, re.I)
        endpoint_hint = f"PASI {lvl}" + (f" at week {week.group(1)}" if week else "")
        return treat, control, endpoint_hint, comparator

    pairs: list[tuple[float, float, float, str, str, str]] = []
    for m in PCT_VS_RE.finditer(text):
        a, b = float(m.group(1)), float(m.group(2))
        if a > 100 or b > 100:
            continue
        if pasi and a < 15 and b < 15:
            continue
        window = m.group(0)
        lead_in = text[max(0, m.start() - 24):m.start()].lower()
        if "difference of" in lead_in or "difference" in lead_in:
            continue
        side = _pair_endpoint(text, m)
        if pasi and side == "spga":
            continue
        if pasi and side == "dlqi":
            continue
        context = text[max(0, m.start() - 80): min(len(text), m.end() + 48)]
        pairs.append((abs(a - b), a, b, _comparator_label(context), window, side))
    if not pairs:
        alt = PCT_AND_RE.search(text)
        if alt:
            a, b = float(alt.group(1)), float(alt.group(2))
            if not (pasi and a < 15 and b < 15):
                pairs.append((abs(a - b), a, b, _comparator_label(alt.group(0)), alt.group(0), "unknown"))
    if pairs:
        if pasi and any(p[-1] == "pasi" for p in pairs):
            pairs = [p for p in pairs if p[-1] == "pasi"]
        pairs.sort(key=lambda row: -row[0])
        _, a, b, comparator, window, _side = pairs[0]
        if hr is not None and hr < 1:
            treat, control = (a, b) if a <= b else (b, a)
        else:
            treat, control = (a, b) if a >= b else (b, a)
        week = re.search(r"week\s+(\d+)", window, re.I)
        if pasi:
            endpoint_hint = f"PASI {pasi.group(1)}" + (f" at week {week.group(1)}" if week else "")
        return treat, control, endpoint_hint, comparator

    if pasi:
        slash = PASI_SLASH_RE.search(text) or PASI_SLASH_RE.search(blob)
        if slash:
            week = re.search(r"week\s+(\d+)", (slash.group(0) + " " + text[:240]), re.I)
            endpoint_hint = "PASI 90" + (f" at week {week.group(1)}" if week else "")
            return float(slash.group("w90")), None, endpoint_hint, ""
        single = PASI_SINGLE_RE.search(text) or PASI_SINGLE_RE.search(blob)
        if single:
            pct = single.group("a") or single.group("b")
            lvl = single.group("lvl1") or single.group("lvl2") or pasi.group(1)
            week = re.search(r"week\s+(\d+)", (single.group(0) + " " + text[:200]), re.I)
            endpoint_hint = f"PASI {lvl}" + (f" at week {week.group(1)}" if week else "")
            return float(pct), None, endpoint_hint, ""
    return None, None, endpoint_hint, comparator


def _pair_endpoint(text: str, match: re.Match) -> str:
    after = text[match.end(): match.end() + 72].lower()
    before = text[max(0, match.start() - 160): match.start()].lower()
    if re.search(r"achieved\s+(a\s+)?spga", after) or re.search(r"\bspga\b", before):
        return "spga"
    if re.search(r"\bdlqi\b", after) or re.search(r"\bdlqi\b", before):
        return "dlqi"
    if re.search(r"achieved\s+(a\s+)?pasi", after) or re.search(r"pasi\s*(75|90|100)", before + after):
        return "pasi"
    return "unknown"


def _comparator_label(window: str) -> str:
    low = (window or "").lower()
    for name in (
        "placebo", "ustekinumab", "secukinumab", "adalimumab", "etanercept",
        "guselkumab", "ixekizumab", "enalapril", "comparator",
    ):
        if name in low:
            return name
    return "the comparator"


def _claim_sentence(
    conclusions: str,
    results: str,
    title: str,
    product: str,
    trial: str,
    endpoint: str,
    treat_pct,
    control_pct,
    hr,
    comparator: str = "the comparator",
) -> str:
    who = product or "the intervention"
    prefix = f"{trial}: " if trial else ""
    if hr is not None:
        extra = ""
        if treat_pct is not None and control_pct is not None:
            extra = f"; {treat_pct:g}% vs {control_pct:g}%"
        return _clip(
            f"{prefix}{who}: hazard ratio {hr} versus {comparator}{extra}.",
            320,
        )
    if endpoint and treat_pct is not None and control_pct is not None:
        return _clip(
            f"{prefix}{who} achieved {endpoint}: {treat_pct:g}% vs {control_pct:g}% ({comparator}).",
            320,
        )
    if endpoint and treat_pct is not None:
        return _clip(f"{prefix}{treat_pct:g}% achieved {endpoint} with {who}.", 320)
    if conclusions:
        sent = _first_sentences(conclusions, 2)
        if len(sent) > 40 and not _is_title_claim(sent, title):
            return _clip((prefix + sent) if trial and trial not in sent else sent, 320)
    if results:
        sent = _first_sentences(results, 2)
        if len(sent) > 40:
            return _clip(sent, 320)
    title = (title or "").rstrip(".")
    if title:
        return _clip(title + ".", 280)
    return "Abstract retrieved; quote only what the paper states."


def _is_title_claim(claim: str, title: str) -> bool:
    a = re.sub(r"[^a-z0-9]+", " ", (claim or "").lower()).strip()
    b = re.sub(r"[^a-z0-9]+", " ", (title or "").lower()).strip()
    return bool(a) and bool(b) and (a == b or a.rstrip(".") == b)


def _first_sentences(text: str, n: int) -> str:
    parts = re.split(r"(?<=[.!?])\s+", (text or "").strip())
    return " ".join(p.strip() for p in parts[:n] if p.strip())


def _clip(text: str, n: int) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    if len(text) <= n:
        return text
    return text[: n - 1].rstrip() + "…"


def _trial_name(title: str, abstract: str, product: str) -> str:
    blob = f"{title} {abstract}"
    skip = {
        "PASI", "PMID", "NCBI", "USA", "HR", "CI", "THE", "AND", "FOR",
        "IL", "TNF", "COVID", "HIV", "WHO", "FDA", "EMA", "DLQI", "TEAE",
        "TEAES", "NCT", "METHODS", "RESULTS", "Patients", "Psoriasis",
        "Risankizumab", "Background", "Objective", "Objectives",
    }
    prod = (product or "").lower()
    for rx in (TRIAL_HYPHEN_RE, TRIAL_CAMEL_RE, TRIAL_MIXED_RE):
        for m in rx.finditer(blob):
            token = m.group(1)
            if token in skip or token.upper() in skip or len(token) < 5:
                continue
            if prod and token.lower() == prod:
                continue
            if token.lower().startswith("clinicaltrial"):
                continue
            if re.match(r"NCT\d+", token, re.I):
                continue
            if rx is TRIAL_CAMEL_RE and token.lower() in {"patients", "psoriasis", "methods", "results"}:
                continue
            return token
    return ""


def _title_stem(title: str) -> str:
    t = (title or "").lower()
    t = re.sub(r"\ba network meta-analysis\b.*", "", t)
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()[:90]


def _dedupe_key(hit: dict[str, Any], parsed: dict[str, Any]) -> str:
    trial = (parsed.get("trial") or hit.get("trial") or "").lower()
    trial = re.sub(r"[-_]?\d+$", "", trial)
    if len(trial) >= 5:
        return "trial:" + trial
    return "stem:" + _title_stem(hit.get("title") or "")


def _mentions_product(title: str, abstract: str, product: str) -> bool:
    if not product:
        return True
    blob = f"{title} {abstract}".lower()
    tokens = [t for t in re.findall(r"[a-z][a-z0-9-]{3,}", product.lower()) if t not in PRODUCT_STOP]
    if not tokens:
        return True
    return any(t in blob for t in tokens)


def _score(hit: dict[str, Any], product: str, reading: dict[str, Any], parsed: dict[str, Any]) -> int:
    title = (hit.get("title") or "").lower()
    types = " ".join([hit.get("design") or "", *(reading.get("pubtypes") or [])]).lower()
    abstract = (reading.get("abstract") or "").lower()
    s = 0
    if not _mentions_product(hit.get("title") or "", reading.get("abstract") or "", product):
        return -8
    if parsed.get("treat_event") is not None and parsed.get("control_event") is not None:
        s += 10
    elif parsed.get("hr") is not None:
        s += 9
    elif parsed.get("treat_event") is not None:
        s += 4
    elif parsed.get("numeric"):
        s += 3
    else:
        s -= 2
    if "randomized" in types:
        s += 6
    elif "guideline" in types:
        s += 5
    elif "clinical trial" in types:
        s += 4
    elif "meta-analysis" in types:
        s += 2
    if product and product.lower() in title:
        s += 5
    if GENERIC_TITLE.search(title):
        s -= 4
    if "network meta-analysis" in title:
        s -= 3
    if "open-label extension" in title or "open-label extension" in abstract:
        s -= 4
    if "placebo" in abstract:
        s += 3
    year = hit.get("year") or 0
    if isinstance(year, int) and year >= 2018:
        s += min(3, (year - 2017) // 2)
    return s


def _grade(design: str, parsed: dict) -> str:
    d = (design or "").lower()
    if "randomized" in d and (parsed.get("hr") is not None or parsed.get("treat_event") is not None):
        return "A"
    if "guideline" in d:
        return "A"
    if "randomized" in d or "clinical trial" in d:
        return "B"
    return "retrieved"


def _directs(title: str, abstract: str, design: str) -> str:
    blob = f"{title} {abstract} {design}".lower()
    if any(w in blob for w in ("guideline", "class i", "recommendation")):
        return "guideline-cover"
    if any(w in blob for w in ("in-hospital", "pre-discharge", "early after discharge", "early post-discharge")):
        return "first-eligible-start"
    if any(w in blob for w in ("elderly", "older patient", "according to age")):
        return "segment-confidence"
    return "outcome-permission"


def _barrier(brief: Any) -> str:
    insights = list(getattr(brief, "hcp_insights", None) or [])
    costs = list(getattr(brief, "access_and_cost", None) or [])
    if insights:
        return insights[0]
    if costs:
        return costs[0]
    goal = getattr(brief, "business_goal", "") or ""
    if goal:
        return goal
    return "Conviction at the decision moment is fragile."


ROLE_LABELS = {
    "placebo-controlled": "Vs placebo",
    "head-to-head": "Vs the current choice",
    "durability": "It holds",
    "replication": "A second RCT",
    "supporting": "Also sourced",
    "outcome-permission": "The outcome",
    "first-eligible-start": "Start now",
    "guideline-cover": "Cover exists",
    "segment-confidence": "Age is not a veto",
    "local-context": "Local context",
}

ACTIVE_COMPARATORS = {
    "ustekinumab", "secukinumab", "adalimumab", "etanercept", "guselkumab",
    "ixekizumab", "brodalumab", "tildrakizumab", "enalapril",
}


def guess_role(hit: dict[str, Any], parsed: dict[str, Any] | None = None) -> str:
    parsed = parsed or {}
    blob = f"{hit.get('title') or ''} {hit.get('design') or ''} {hit.get('trial') or ''} {(parsed.get('trial') or '')}".lower()
    abstract = ((hit.get("abstract") or "") + " " + (parsed.get("claim") or "")).lower()
    if any(w in blob for w in ("open-label extension", "long-term", "limmitless", "extension study")):
        return "durability"
    if any(w in blob for w in ("in-hospital", "pre-discharge", "early after discharge")):
        return "first-eligible-start"
    if "guideline" in blob:
        return "guideline-cover"
    comp = (parsed.get("comparator") or hit.get("comparator") or "").lower()
    if comp in ACTIVE_COMPARATORS or (comp and comp not in ("placebo", "the comparator", "")):
        return "head-to-head"
    if parsed.get("control_event") is not None and (comp == "placebo" or "placebo" in abstract or "placebo" in blob):
        return "placebo-controlled"
    if parsed.get("control_event") is not None:
        return "head-to-head"
    if parsed.get("treat_event") is not None and parsed.get("control_event") is None:
        return "durability"
    return "outcome-permission"


def assign_paper_jobs(records: list[dict[str, Any]], brief: Any) -> list[dict[str, Any]]:
    """Give each paper a distinct job so strategy does not reprint one finding."""
    used: set[str] = set()
    for rec in records:
        if rec.get("matchedFrom") == "catalog":
            role = rec.get("directs") or "outcome-permission"
            rec["role"] = role
            rec["roleLabel"] = ROLE_LABELS.get(role, rec.get("short") or "Sourced")
            used.add(role)
            continue
        role = guess_role(rec, {
            "trial": rec.get("trial"),
            "claim": rec.get("claim_permitted"),
            "comparator": rec.get("comparator"),
            "treat_event": rec.get("treat_event"),
            "control_event": rec.get("control_event"),
        })
        if role in used:
            role = {
                "placebo-controlled": "replication",
                "head-to-head": "supporting",
                "durability": "supporting",
            }.get(role, "supporting")
            if role in used:
                role = "supporting"
        rec["role"] = role
        rec["roleLabel"] = ROLE_LABELS.get(role, rec.get("trial") or rec.get("short") or "Sourced")
        used.add(role)
        rec["spine_means"] = _means_for(rec)
        rec["spine_execute"] = _execute_for_role(role, brief)
        rec["spine_measure"] = (
            f"Unaided recall of {rec.get('endpoint') or 'this paper\'s finding'} "
            f"({rec.get('trial') or rec.get('short') or 'this paper'})"
        )
        rec["spine_barrier"] = _barrier(brief)
    return records


def _means_for(rec: dict[str, Any]) -> str:
    role = rec.get("role") or ""
    claim = rec.get("claim_permitted") or rec.get("finding") or ""
    if role == "placebo-controlled":
        return "Permission versus untreated disease — that is this paper's job, not a slogan."
    if role == "head-to-head":
        return "When they name the competitor, this paper is the answer — not a reprint of the placebo RCT."
    if role == "durability":
        return "Clearance that holds is this paper's job. Do not spend it as another week-16 reprint."
    if role == "replication":
        return "A second RCT, a second number. Not a paraphrase of the first."
    return claim


def _execute_for_role(role: str, brief: Any) -> str:
    if role in ("placebo-controlled", "outcome-permission"):
        return "Bag the vs-placebo number. That is permission to start, not the whole campaign."
    if role == "head-to-head":
        return "When they stay on the competitor, quote this head-to-head finding — one number, one paper."
    if role == "durability":
        return "The 'will it last' objection gets this durability number, not another efficacy reprint."
    if role == "replication":
        return "A second RCT in the bag so the first number is not a one-study story."
    if role == "first-eligible-start":
        return "First-Touch Protocol: initiate at first-eligible, not first-available."
    if role == "guideline-cover":
        return "Peer Cascade: KOLs author the protocol the guideline already permits."
    return _execute_for(role, brief)


def _execute_for(directs: str, brief: Any) -> str:
    costs = " ".join(getattr(brief, "access_and_cost", None) or [])
    insights = " ".join(getattr(brief, "hcp_insights", None) or [])
    blob = f"{costs} {insights} {getattr(brief, 'business_goal', '') or ''}".lower()
    if directs == "first-eligible-start":
        return "First-Touch Protocol: initiate at first-eligible, not first-available."
    if directs == "guideline-cover":
        return "Peer Cascade: KOLs author the protocol the guideline already permits."
    if "cost" in blob or "oop" in blob or "afford" in blob:
        return "A cost conversation the doctor can survive — assistance inside code."
    return "Conviction at the moment of the pen: one sourced finding a peer can repeat."
