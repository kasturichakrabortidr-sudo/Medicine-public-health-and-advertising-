"""Ongoing and saved STRATA projects.

Generate upserts an ongoing record. Pinning it (status=saved) keeps it after
the next brief. Records live as JSON under data/projects — never as a demo pack.
"""

from __future__ import annotations

import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path


def _root() -> Path:
    env = os.environ.get("STRATA_PROJECTS_DIR")
    path = Path(env) if env else Path(__file__).resolve().parent.parent / "data" / "projects"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _summary(record: dict) -> dict:
    pack = record.get("pack") or {}
    meta = pack.get("meta") or {}
    evidence = pack.get("evidence") or {}
    return {
        "id": record.get("id"),
        "status": record.get("status") or "ongoing",
        "title": record.get("title") or meta.get("brand") or "Untitled",
        "brand": meta.get("brand") or "",
        "molecule": meta.get("molecule") or meta.get("product") or "",
        "therapyArea": meta.get("therapyArea") or "",
        "market": meta.get("market") or "",
        "doctrine": meta.get("doctrine") or "",
        "source": meta.get("source") or "",
        "papers": len(evidence.get("records") or []),
        "slides": len(pack.get("slides") or []),
        "createdAt": record.get("createdAt"),
        "updatedAt": record.get("updatedAt"),
    }


def _path(pid: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9._-]", "", pid)[:80]
    if not safe:
        raise ValueError("Invalid project id")
    return _root() / f"{safe}.json"


def list_projects() -> list[dict]:
    rows = []
    for path in sorted(_root().glob("*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(record, dict) or not record.get("id"):
            continue
        rows.append(_summary(record))
    rows.sort(key=lambda r: r.get("updatedAt") or "", reverse=True)
    return rows


def get_project(pid: str) -> dict | None:
    path = _path(pid)
    if not path.is_file():
        return None
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(record, dict):
        return None
    return record


def delete_project(pid: str) -> bool:
    path = _path(pid)
    if not path.is_file():
        return False
    path.unlink()
    return True


def save_project(payload: dict) -> dict:
    pack = payload.get("pack")
    if not isinstance(pack, dict) or not pack.get("slides"):
        raise ValueError("A project must include a strategy pack with slides.")
    status = payload.get("status") if payload.get("status") in {"ongoing", "saved"} else "ongoing"
    meta = pack.get("meta") or {}
    brand = meta.get("brand") or "Untitled"
    pid = str(payload.get("id") or "").strip() or str(uuid.uuid4())
    existing = get_project(pid) if payload.get("id") else None
    created = (existing or {}).get("createdAt") or _now()
    record = {
        "id": pid,
        "status": status,
        "title": payload.get("title") or f"{brand} · {meta.get('therapyArea') or 'strategy'}",
        "createdAt": created,
        "updatedAt": _now(),
        "pack": pack,
    }
    _path(pid).write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
    return record


def upsert_ongoing(pack: dict) -> dict:
    """Keep one live working file per brand + source. Generate calls this."""
    meta = pack.get("meta") or {}
    brand = meta.get("brand") or ""
    source = meta.get("source") or ""
    for row in list_projects():
        if row.get("status") != "ongoing":
            continue
        if row.get("brand") == brand and (row.get("source") or "") == source:
            existing = get_project(row["id"]) or {}
            return save_project(
                {"id": row["id"], "status": "ongoing", "pack": pack, "title": existing.get("title")}
            )
    return save_project({"status": "ongoing", "pack": pack, "id": str(uuid.uuid4())})
