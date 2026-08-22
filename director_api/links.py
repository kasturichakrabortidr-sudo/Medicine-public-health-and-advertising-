"""Resolve a paper row to an https URL that actually opens."""

from __future__ import annotations


def paper_href(row: dict | None) -> str:
    """Prefer an existing http(s) URL, then PubMed, then doi.org."""
    if not row:
        return ""
    url = str(row.get("url") or "").strip()
    if url.startswith("http://") or url.startswith("https://"):
        return url
    if url.startswith("//"):
        return "https:" + url
    pmid = "".join(ch for ch in str(row.get("pmid") or "") if ch.isdigit())
    if pmid:
        return f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
    doi = str(row.get("doi") or "").strip()
    if doi.lower().startswith("doi:"):
        doi = doi.split(":", 1)[1].strip()
    if doi:
        return f"https://doi.org/{doi}"
    return url
