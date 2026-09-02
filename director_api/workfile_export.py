"""Working-file export — markdown the client can print, paste, or archive.

The deck is the argument. This file is the source of truth behind it.
"""

from __future__ import annotations

import re
from typing import Any


def filename_for_workfile(pack: dict) -> str:
    brand = (pack.get("meta") or {}).get("brand") or "strategy"
    slug = re.sub(r"[^A-Za-z0-9]+", "-", brand).strip("-") or "strategy"
    return f"{slug}-working-file.md"


def workfile_to_markdown(pack: dict) -> str:
    meta = pack.get("meta") or {}
    doctrine = pack.get("doctrine") or {}
    work = pack.get("workfile") or {}
    brand = meta.get("brand") or "Brand"
    lines = [
        f"# {brand} working file",
        "",
        f"*{meta.get('therapyArea') or ''} · {meta.get('market') or ''} · {doctrine.get('name') or ''}*".strip(" ·*"),
        "",
        work.get("howBuilt") or "",
        "",
    ]
    cannot = work.get("cannotClaim") or []
    if cannot:
        lines.append("## Do not claim")
        lines.extend(f"- {item}" for item in cannot)
        lines.append("")
    for phase in work.get("phases") or []:
        lines.append(f"## {phase.get('id')} · {phase.get('title')}")
        lines.append("")
        if phase.get("howBuilt"):
            lines.append(phase["howBuilt"])
            lines.append("")
        for key, value in phase.items():
            if key in {"id", "title", "howBuilt"}:
                continue
            lines.extend(_block(key, value))
        lines.append("")
    questions = work.get("openQuestions") or []
    if questions:
        lines.append("## Open questions")
        lines.extend(f"- {q}" for q in questions)
        lines.append("")
    refs = work.get("references") or pack.get("references") or []
    if refs:
        lines.append("## References")
        for ref in refs:
            n = ref.get("n") or ref.get("ref") or ""
            cite = ref.get("citation") or ref.get("short") or ""
            pmid = ref.get("pmid") or ""
            lines.append(f"{n}. {cite}" + (f" PMID {pmid}." if pmid else ""))
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def _label(key: str) -> str:
    spaced = re.sub(r"([A-Z])", r" \1", key).replace("_", " ").strip()
    return spaced[:1].upper() + spaced[1:]


def _block(key: str, value: Any) -> list[str]:
    if value in (None, "", [], {}):
        return []
    if isinstance(value, dict) and (value.get("headers") or value.get("rows") is not None):
        return _table(key, value)
    if isinstance(value, list):
        if value and isinstance(value[0], dict) and ("headers" in value[0] or "rows" in value[0]):
            out = []
            for i, item in enumerate(value, 1):
                out.extend(_table(f"{key} {i}", item))
            return out
        return [f"**{_label(key)}**", *[f"- {_as_text(v)}" for v in value], ""]
    return [f"**{_label(key)}.** {_as_text(value)}", ""]


def _table(key: str, block: dict) -> list[str]:
    headers = [str(h) for h in (block.get("headers") or [])]
    rows = block.get("rows") or []
    if not headers and rows:
        width = max(len(r) for r in rows)
        headers = [f"Col {i}" for i in range(1, width + 1)]
    if not headers:
        return []
    lines = [
        f"**{_label(key)}**",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        cells = [_as_text(row[i]) if i < len(row) else "" for i in range(len(headers))]
        lines.append("| " + " | ".join(c.replace("|", "/") for c in cells) + " |")
    lines.append("")
    return lines


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        return "; ".join(f"{k}: {v}" for k, v in value.items() if v not in (None, ""))
    if isinstance(value, list):
        return "; ".join(_as_text(v) for v in value)
    return str(value).replace("\n", " ").strip()
