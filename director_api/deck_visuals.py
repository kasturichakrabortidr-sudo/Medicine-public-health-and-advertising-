"""Row builders and copy helpers. Numbers come from numbered papers only.

Copy rule: complete sentences. Never an ellipsis. Never a cut clause.
"""

from __future__ import annotations

import re

from .cite import mark

HANGING = re.compile(
    r"\b(the|a|an|at|in|if|to|for|of|and|or|with|on|by|from|as|than|that|this|is|are)\s*$",
    re.I,
)
STOP = re.compile(r"[^.!?]*[.!?]")


def sentence(text, n: int = 1) -> str:
    """First n complete sentences. Never adds an ellipsis."""
    text = " ".join(str(text or "").split())
    if not text:
        return ""
    found = [m.group(0).strip() for m in STOP.finditer(text)]
    if found:
        return " ".join(found[: max(1, n)])
    cleaned = text.rstrip(" .…,;:—-")
    if not cleaned:
        return ""
    if HANGING.search(cleaned):
        cleaned = HANGING.sub("", cleaned).rstrip(" ,;:—-")
    if not cleaned:
        return ""
    if cleaned[-1] not in ".!?":
        cleaned += "."
    return cleaned


def line(text) -> str:
    """A complete noun phrase or sentence for a card title. No ellipsis."""
    text = " ".join(str(text or "").split())
    text = text.replace("…", "").rstrip(" .")
    if not text:
        return ""
    if HANGING.search(text):
        text = HANGING.sub("", text).rstrip(" ,;:—-")
    return text


def phase(work: dict, pid: str) -> dict:
    for item in work.get("phases") or []:
        if item.get("id") == pid:
            return item
    return {}


def rows_of(block) -> list[list]:
    if not isinstance(block, dict):
        return []
    out = []
    for row in block.get("rows") or []:
        if isinstance(row, (list, tuple)) and row:
            out.append(list(row))
    return out


def finding(row: dict) -> str:
    if row.get("nnt"):
        return f"{row.get('control_event')} vs {row.get('treat_event')} per 100; NNT {row['nnt']}"
    if row.get("hr") is not None:
        return f"{row.get('effect_metric') or 'HR'} {row['hr']} ({row.get('low')}–{row.get('high')})"
    return sentence(row.get("claim_permitted") or row.get("endpoint") or "")


def people_rows(records: list[dict]) -> list[dict]:
    rows = []
    for r in records:
        if r.get("control_event") is None or r.get("treat_event") is None:
            continue
        if r.get("nnt") is None:
            continue
        control = r["control_event"]
        treat = r["treat_event"]
        arr = r.get("arr")
        if arr is None:
            arr = round(float(control) - float(treat), 1)
        rows.append({
            "name": f"{mark(r)} {r.get('short') or r.get('trial')}",
            "control": control,
            "treat": treat,
            "arr": arr,
            "nnt": r["nnt"],
            "horizon": r.get("horizon") or "",
            "unit": r.get("visual_unit") or "events per 100",
            "pmid": r.get("pmid") or "",
            "ref": r.get("ref") or "",
            "control_label": "Comparator",
            "treat_label": r.get("trial") or "Intervention",
            "claim": sentence(r.get("claim_permitted") or ""),
        })
    return rows


def compare_rows(records: list[dict]) -> list[dict]:
    rows = []
    for r in records:
        if r.get("control_event") is None or r.get("treat_event") is None:
            continue
        if r.get("nnt") is not None:
            continue
        rows.append({
            "name": f"{mark(r)} {r.get('short') or r.get('trial')}",
            "left": r["control_event"],
            "right": r["treat_event"],
            "left_label": "Comparator",
            "right_label": r.get("trial") or "Intervention",
            "delta": r.get("arr") if r.get("arr") is not None else "",
            "unit": r.get("visual_unit") or "",
            "pmid": r.get("pmid") or "",
            "ref": r.get("ref") or "",
            "claim": sentence(r.get("claim_permitted") or ""),
            "horizon": r.get("horizon") or "",
        })
    return rows


def spine_rows(records: list[dict], interventions: list[dict]) -> list[dict]:
    mapping = {
        "first-eligible-start": "first-touch",
        "outcome-permission": "habit-lock",
        "guideline-cover": "peer-cascade",
        "segment-confidence": "myth-reset",
        "local-context": "afford-kit",
    }
    rows = []
    for r in records:
        means = r.get("spine_means")
        if not means:
            continue
        short = r.get("short") or ""
        execute = r.get("spine_execute") or ""
        iv = next((i for i in interventions if i["name"] and i["name"] in execute), None)
        if iv is None:
            iv = next((i for i in interventions if short and short in (i.get("evidenceAnchor") or "")), None)
        if iv is None:
            want = mapping.get(r.get("directs") or "")
            iv = next((i for i in interventions if i["id"] == want), None) if want else None
        rows.append({
            "name": f"{mark(r)} {r.get('short') or r.get('trial') or ''}",
            "science": sentence(r.get("claim_permitted") or ""),
            "means": sentence(means),
            "barrier": sentence(r.get("spine_barrier") or ""),
            "execute": sentence(r.get("spine_execute") or (iv["name"] if iv else "")),
            "measure": sentence(r.get("spine_measure") or (iv["kill"] if iv else "")),
            "pmid": r.get("pmid") or "",
            "ref": r.get("ref") or "",
            "move": iv["name"] if iv else (r.get("spine_execute") or ""),
        })
    return rows[:2]


def forest_rows(records: list[dict]) -> list[dict]:
    rows = []
    for r in records:
        if r.get("hr") is None:
            continue
        rows.append({
            "name": f"{mark(r)} {r.get('short') or r.get('trial')}",
            "stream": r.get("stream"),
            "hr": r["hr"],
            "low": r.get("low") if r.get("low") is not None else r["hr"],
            "high": r.get("high") if r.get("high") is not None else r["hr"],
            "grade": r.get("grade"),
            "note": f"{mark(r)} PMID {r.get('pmid') or '—'} · doi:{r.get('doi') or '—'}",
        })
    return rows[:5]


def reference_slides(references: list[dict]) -> list[dict]:
    if not references:
        return [{
            "id": "references",
            "section": "References",
            "kicker": "Numbered sources",
            "title": "The pack, when we have it",
            "narrative": "No PMID is on the register yet. Do not invent a reference list.",
            "layout": "insight",
            "phase": "03",
            "question": "Where are the PMIDs?",
            "skill": "visuals",
            "bullets": ["Retrieve primary papers before anyone writes a claim."],
        }]
    slides = []
    chunk = 7
    for i in range(0, len(references), chunk):
        part = references[i: i + chunk]
        slides.append({
            "id": "references" if i == 0 else f"references-{i // chunk + 1}",
            "section": "References",
            "kicker": "Numbered sources",
            "title": "Every superscript points here",
            "narrative": "These are the numbered papers. Nothing else is a source.",
            "layout": "references",
            "phase": "03",
            "question": "Where are the PMIDs?",
            "skill": "visuals",
            "table": {
                "headers": ["No.", "Citation"],
                "rows": [[str(r.get("n") or ""), r.get("citation") or r.get("short") or ""] for r in part],
            },
        })
    return slides
