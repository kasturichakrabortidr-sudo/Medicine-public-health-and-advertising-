"""Resolve the INN / molecule used for science and PubMed.

Brand names belong on the campaign. Papers, queries, and claims use the
compound name. Fictional trade names (Velmecor, Cardiava, CardioShield)
never go into a PubMed query.
"""

from __future__ import annotations

import re
from typing import Any

# Trade name → INN. Keys are lowercase, whole-token match.
BRAND_TO_INN: dict[str, str] = {
    "entresto": "sacubitril/valsartan",
    "lcz696": "sacubitril/valsartan",
    "jardiance": "empagliflozin",
    "synjardy": "empagliflozin",
    "farxiga": "dapagliflozin",
    "forxiga": "dapagliflozin",
    "xigduo": "dapagliflozin",
    "qtern": "dapagliflozin",
    "steglatro": "ertugliflozin",
    "inpefa": "sotagliflozin",
    "kerendia": "finerenone",
    "ozempic": "semaglutide",
    "wegovy": "semaglutide",
    "rybelsus": "semaglutide",
    "mounjaro": "tirzepatide",
    "zepbound": "tirzepatide",
    "keytruda": "pembrolizumab",
    "opdivo": "nivolumab",
    "skyrizi": "risankizumab",
    "cosentyx": "secukinumab",
    "tremfya": "guselkumab",
    "taltz": "ixekizumab",
    "siliq": "brodalumab",
    "ilumya": "tildrakizumab",
    "humira": "adalimumab",
    "stelara": "ustekinumab",
    "enbrel": "etanercept",
    "dupixent": "dupilumab",
}

# Suffixes that mark an INN even when the brief wrapped it in a brand line.
# Stem is {1,} so short INNs like valsartan (val + sartan) still match.
INN_RE = re.compile(
    r"\b(sacubitril|"
    r"[A-Za-z][A-Za-z0-9-]{1,}(?:mab|nib|tide|sartan|gliptin|gliflozin|"
    r"olol|pril|statin|parin|xaban|fenone|glutide|ciclib|parib))\b",
    re.I,
)

INN_STOP = {
    "fictional", "illustrative", "example", "placeholder", "dummy",
    "brand", "once", "daily", "oral", "therapy", "tablet", "capsule",
    "product", "drug", "dose", "strength", "film", "coated",
    "chronic", "acute", "plaque", "severe", "moderate", "patients", "study",
}

LABELLED_INN_RE = re.compile(
    r"(?im)(?:molecule|inn|compound|generic(?:\s*name)?)\s*[:\-–]\s*"
    r"([A-Za-z][A-Za-z0-9®™/-]{2,80})"
)


def inn_from_text(text: str) -> str:
    """Return an INN from a product/brand string, or empty if only a trade name."""
    if not text:
        return ""
    mapped = _mapped_inns(text)
    if mapped:
        return _prefer_combo(mapped)
    found = [m.group(1).lower() for m in INN_RE.finditer(text)]
    found = [t for t in found if t not in INN_STOP]
    if not found:
        return ""
    return _prefer_combo(found)


def science_name(brief: Any) -> str:
    """Molecule used for PubMed and claims. Never a campaign brand."""
    product = getattr(brief, "product", "") or ""
    brand = getattr(brief, "brand", "") or ""
    raw = getattr(brief, "raw_text", "") or ""
    for text in (product, brand):
        name = inn_from_text(text)
        if name:
            return name
    labelled = LABELLED_INN_RE.search(raw)
    if labelled:
        name = inn_from_text(labelled.group(1)) or inn_from_text(labelled.group(0))
        if name:
            return name
    return ""


def pubmed_term(name: str) -> str:
    """Boolean-safe PubMed fragment for an INN (handles sacubitril/valsartan)."""
    if not name:
        return ""
    parts = [p.strip() for p in name.split("/") if p.strip()]
    if len(parts) == 1:
        return parts[0]
    return "(" + " AND ".join(parts) + ")"
    """Tokens to look for in paper titles (sacubitril, valsartan, …)."""
    name = science_name(brief)
    if not name:
        return []
    return [t for t in re.findall(r"[a-z][a-z0-9-]{3,}", name.lower()) if t not in INN_STOP]


def _mapped_inns(text: str) -> list[str]:
    low = text.lower()
    found: list[str] = []
    for brand, inn in BRAND_TO_INN.items():
        if re.search(rf"(?<![a-z0-9]){re.escape(brand)}(?![a-z0-9])", low):
            if inn not in found:
                found.append(inn)
    return found


def _prefer_combo(names: list[str]) -> str:
    lower = [n.lower() for n in names]
    if "sacubitril" in lower and "valsartan" in lower:
        return "sacubitril/valsartan"
    if any("/" in n for n in lower):
        return next(n for n in lower if "/" in n)
    return lower[0]
