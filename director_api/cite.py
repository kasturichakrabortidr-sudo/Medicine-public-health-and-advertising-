"""Numbered Vancouver citations for the working file and the deck."""

from __future__ import annotations

from typing import Any


def attach_references(ledger: dict[str, Any]) -> dict[str, Any]:
    """Give every validated (then retrieved) source a stable number, 1…n."""
    refs: list[dict[str, Any]] = []
    n = 1
    seen_pmids = set()
    for row in ledger.get("records") or []:
        row["ref"] = n
        row["citation"] = vancouver(row)
        refs.append(_entry(n, row, "validated" if row.get("matchedFrom") != "pubmed" else "retrieved"))
        if row.get("pmid"):
            seen_pmids.add(str(row.get("pmid")))
        n += 1
    for hit in ledger.get("pubmed") or []:
        if str(hit.get("pmid") or "") in seen_pmids:
            continue
        hit["ref"] = n
        if not hit.get("citation"):
            hit["citation"] = vancouver(hit)
        refs.append({
            **_entry(n, hit, "retrieved"),
            "citation": f"{hit['citation']} [PubMed retrieval — confirm full text before it can lead.]",
            "id": hit.get("id") or f"pubmed-{hit.get('pmid') or n}",
            "short": (hit.get("title") or hit.get("short") or "PubMed hit")[:72],
        })
        n += 1
    ledger["references"] = refs
    by_id = {r.get("id"): r for r in ledger.get("records") or []}
    for cite in (ledger.get("lead") or {}).get("citations") or []:
        rec = by_id.get(cite.get("id"))
        if rec:
            cite["ref"] = rec["ref"]
            cite["citation"] = rec.get("citation")
    return ledger


def vancouver(row: dict[str, Any]) -> str:
    authors = row.get("authors") or "Anon"
    title = (row.get("title") or row.get("short") or "").rstrip(".")
    journal = row.get("journal") or ""
    year = row.get("year") or ""
    pages = row.get("pages") or ""
    doi = row.get("doi") or ""
    pmid = row.get("pmid") or ""
    loc = journal
    if year:
        loc = f"{loc}. {year}" if loc else str(year)
    if pages:
        loc = f"{loc};{pages}"
    parts = [f"{authors} {title}."]
    if loc:
        parts.append(f"{loc}.")
    if doi:
        parts.append(f"doi:{doi}.")
    if pmid:
        parts.append(f"PMID: {pmid}.")
    return " ".join(p for p in parts if p)


def mark(*items: Any) -> str:
    nums: list[int] = []
    for item in items:
        if item is None or item == "":
            continue
        if isinstance(item, dict) and item.get("ref") is not None:
            nums.append(int(item["ref"]))
        elif isinstance(item, (list, tuple)):
            for inner in item:
                tagged = mark(inner)
                if tagged:
                    nums.extend(_nums(tagged))
        else:
            try:
                nums.append(int(item))
            except (TypeError, ValueError):
                continue
    return format_marks(nums)


def format_marks(nums: list[int]) -> str:
    if not nums:
        return ""
    ordered = sorted(set(nums))
    parts: list[str] = []
    start = prev = ordered[0]
    for n in ordered[1:]:
        if n == prev + 1:
            prev = n
            continue
        parts.append(str(start) if start == prev else f"{start}–{prev}")
        start = prev = n
    parts.append(str(start) if start == prev else f"{start}–{prev}")
    return "[" + ",".join(parts) + "]"


def _nums(tag: str) -> list[int]:
    out = []
    for bit in tag.strip("[]").split(","):
        if "–" in bit:
            a, b = bit.split("–", 1)
            out.extend(range(int(a), int(b) + 1))
        elif bit.strip().isdigit():
            out.append(int(bit))
    return out


def _entry(n: int, row: dict[str, Any], status: str) -> dict[str, Any]:
    return {
        "n": n,
        "id": row.get("id") or "",
        "short": row.get("short") or row.get("trial") or row.get("title") or f"Ref {n}",
        "citation": vancouver(row),
        "pmid": str(row.get("pmid") or ""),
        "doi": str(row.get("doi") or ""),
        "url": row.get("url") or "",
        "status": status,
        "year": row.get("year"),
        "trial": row.get("trial") or "",
    }
