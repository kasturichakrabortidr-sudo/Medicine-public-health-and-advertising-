"""FastAPI surface for STRATA — extract any brief format, generate a deck."""

from __future__ import annotations

import json
import os
import queue
import re
import threading
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response, StreamingResponse

from .agent import llm_model, llm_ready
from .extract import ExtractedBrief, extract_files, merge_into_brief, partition_uploads
from .generate import generate_pack
from .pptx_export import filename_for, pack_to_pptx
from .projects import delete_project, get_project, list_projects, save_project, upsert_ongoing
from .workfile_export import filename_for_workfile, workfile_to_markdown

app = FastAPI(title="STRATA Strategy Director", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ROOT = Path(__file__).resolve().parent.parent
_RESERVED_SPA = {"api", "docs", "redoc", "openapi.json"}

ACCEPT_HINT = (
    ".pdf .ppt .pptx .doc .docx .xls .xlsx .csv .tsv .txt .md .rtf .yaml .yml "
    ".json .html .htm .xml .odt .odp .ods .png .jpg .jpeg .webp .gif .log"
)


def web_dist() -> Path:
    override = os.environ.get("STRATA_WEB_DIST", "").strip()
    return Path(override) if override else ROOT / "web" / "dist"


@app.get("/api/health")
def health():
    dist = web_dist()
    ready = llm_ready()
    return {
        "ok": True,
        "service": "strata-director",
        "edition": "strategy-director",
        "accept": ACCEPT_HINT,
        "web": (dist / "index.html").is_file(),
        "agent": True,
        "llm": ready,
        "model": llm_model() if ready else "director-workflow",
    }


@app.post("/api/extract")
async def extract(
    files: list[UploadFile] | None = File(default=None),
    pasted: str = Form(default=""),
):
    uploads = []
    if files:
        for f in files:
            payload = await f.read()
            if len(payload) > 25 * 1024 * 1024:
                raise HTTPException(413, f"{f.filename} exceeds 25 MB")
            uploads.append((f.filename or "upload", payload, f.content_type or ""))
    if not uploads and not pasted.strip():
        raise HTTPException(400, "Upload at least one file or paste brief text.")

    templates, briefs = partition_uploads(uploads)
    extracted = extract_files(briefs)
    brief = merge_into_brief(extracted, pasted)
    if templates:
        names = ", ".join(name for name, _, _ in templates)
        brief.extraction_notes.append(
            f"Design template kept for the deck look, not read as a second brief: {names}"
        )
    file_rows = [
        {
            "filename": e.filename,
            "suffix": e.suffix,
            "bytes": e.bytes,
            "pages": e.pages,
            "notes": e.notes,
            "chars": len(e.text),
            "preview": e.text[:1200],
        }
        for e in extracted
    ]
    for name, payload, mime in templates:
        file_rows.append(
            {
                "filename": name,
                "suffix": Path(name).suffix.lower(),
                "bytes": len(payload),
                "pages": None,
                "notes": ["Design template — not merged into the brief."],
                "chars": 0,
                "preview": "",
            }
        )
    return {
        "files": file_rows,
        "brief": brief.to_dict(),
        "accept": ACCEPT_HINT,
    }


@app.post("/api/generate")
async def generate(
    files: list[UploadFile] | None = File(default=None),
    pasted: str = Form(default=""),
    brief_json: str = Form(default=""),
    mode: str = Form(default="director"),
    pubmed: str = Form(default="true"),
):
    brief, template_names = await _intake_brief(files, pasted, brief_json, mode)
    pack = generate_pack(brief, mode=mode, pubmed=_pubmed_flag(pubmed))
    return _stamp_and_save(pack, brief, template_names)


@app.post("/api/generate/stream")
async def generate_stream(
    files: list[UploadFile] | None = File(default=None),
    pasted: str = Form(default=""),
    brief_json: str = Form(default=""),
    mode: str = Form(default="director"),
    pubmed: str = Form(default="true"),
):
    brief, template_names = await _intake_brief(files, pasted, brief_json, mode)
    pubmed_on = _pubmed_flag(pubmed)

    def events():
        mailbox: queue.Queue = queue.Queue()

        def emit(event: dict) -> None:
            mailbox.put(("event", event))

        def run() -> None:
            try:
                pack = generate_pack(brief, mode=mode, pubmed=pubmed_on, emit=emit)
                _stamp_and_save(pack, brief, template_names)
                mailbox.put(("done", pack))
            except Exception as exc:
                mailbox.put(("error", str(exc) or exc.__class__.__name__))

        threading.Thread(target=run, daemon=True).start()
        while True:
            kind, payload = mailbox.get()
            if kind == "event":
                yield _sse(payload)
                yield ": \n\n"
            elif kind == "done":
                yield _sse({"type": "pack", "pack": payload})
                break
            else:
                yield _sse({"type": "error", "text": payload})
                break

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@app.get("/api/projects")
def projects_list():
    return {"projects": list_projects()}


@app.post("/api/projects")
async def projects_save(request: Request):
    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(400, f"Body must be JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise HTTPException(400, "Body must be an object.")
    pack = payload.get("pack")
    if not isinstance(pack, dict) or not pack.get("slides"):
        raise HTTPException(400, "A project must include a strategy pack with slides.")
    try:
        record = save_project(payload) if payload.get("id") or payload.get("status") == "saved" else upsert_ongoing(pack)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except OSError as exc:
        raise HTTPException(500, f"Could not save the project: {exc}") from exc
    return record


@app.get("/api/projects/{pid}")
def projects_get(pid: str):
    record = get_project(pid)
    if not record:
        raise HTTPException(404, "Project not found.")
    return record


@app.delete("/api/projects/{pid}")
def projects_delete(pid: str):
    if not delete_project(pid):
        raise HTTPException(404, "Project not found.")
    return {"ok": True, "id": pid}


@app.post("/api/export/pptx")
async def export_pptx(request: Request):
    try:
        pack = await request.json()
    except Exception as exc:
        raise HTTPException(400, f"Body must be a JSON strategy pack: {exc}") from exc
    if not isinstance(pack, dict) or not pack.get("slides"):
        raise HTTPException(400, "JSON must be a strategy pack with slides.")
    return _pptx_response(pack)


@app.post("/api/export/workfile")
async def export_workfile(request: Request):
    try:
        pack = await request.json()
    except Exception as exc:
        raise HTTPException(400, f"Body must be a JSON strategy pack: {exc}") from exc
    if not isinstance(pack, dict) or not pack.get("workfile"):
        raise HTTPException(400, "JSON must be a strategy pack with a working file.")
    return _workfile_response(pack)


def _pptx_response(pack: dict) -> Response:
    data = pack_to_pptx(pack)
    name = filename_for(pack)
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={
            "Content-Disposition": f'attachment; filename="{name}"',
            "Content-Length": str(len(data)),
        },
    )


def _workfile_response(pack: dict) -> Response:
    data = workfile_to_markdown(pack).encode("utf-8")
    name = filename_for_workfile(pack)
    return Response(
        content=data,
        media_type="text/markdown; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{name}"',
            "Content-Length": str(len(data)),
        },
    )


def _web_file(relative: str) -> FileResponse:
    dist = web_dist().resolve()
    index = dist / "index.html"
    if not index.is_file():
        raise HTTPException(
            503,
            "Web build missing. From the repo root run: python start_live.py",
        )
    if not relative or relative == "index.html":
        return FileResponse(index)
    candidate = (dist / relative).resolve()
    try:
        candidate.relative_to(dist)
    except ValueError as exc:
        raise HTTPException(404, "Not found") from exc
    if candidate.is_file():
        return FileResponse(candidate)
    return FileResponse(index)


@app.get("/")
def spa_index():
    return _web_file("index.html")


@app.get("/{full_path:path}")
def spa_or_asset(full_path: str):
    first = full_path.split("/", 1)[0]
    if first in _RESERVED_SPA:
        raise HTTPException(404, "Not found")
    return _web_file(full_path)


def _pubmed_flag(value: str) -> bool:
    return (value or "true").strip().lower() not in {"0", "false", "no", "off"}


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


async def _intake_brief(
    files: list[UploadFile] | None,
    pasted: str,
    brief_json: str,
    mode: str,
) -> tuple[ExtractedBrief, list[str]]:
    uploads = []
    template_names: list[str] = []
    if files:
        for f in files:
            payload = await f.read()
            if len(payload) > 25 * 1024 * 1024:
                raise HTTPException(413, f"{f.filename} exceeds 25 MB")
            uploads.append((f.filename or "upload", payload, f.content_type or ""))
        templates, briefs = partition_uploads(uploads)
        template_names = [name for name, _, _ in templates]
        uploads = briefs

    form = None
    if brief_json.strip():
        try:
            mapping = json.loads(brief_json)
        except json.JSONDecodeError as exc:
            raise HTTPException(400, f"brief_json is not valid JSON: {exc}") from exc
        form = _brief_from_mapping(mapping)

    extracted = None
    if uploads or pasted.strip():
        extracted = merge_into_brief(extract_files(uploads), pasted)

    brief = _compose_brief(extracted, form)
    if not brief:
        raise HTTPException(400, "Provide files, pasted text, or brief_json.")
    if template_names:
        note = (
            "Design template kept for the deck look, not read as a second brief: "
            + ", ".join(template_names)
        )
        if note not in brief.extraction_notes:
            brief.extraction_notes.append(note)

    if not brief.brand and not brief.therapy_area and not brief.raw_text:
        raise HTTPException(422, "Could not read a usable brief from the upload.")

    if mode == "demo":
        raise HTTPException(400, "Demo mode is not available. Upload your own brief.")
    return brief, template_names


def _stamp_and_save(pack: dict, brief: ExtractedBrief, template_names: list[str]) -> dict:
    pack.setdefault("meta", {})
    pack["meta"]["source"] = (
        ", ".join(brief.source_files)
        or pack["meta"].get("source")
        or "uploaded brief"
    )
    if template_names:
        pack["meta"]["templateFiles"] = template_names
    try:
        upsert_ongoing(pack)
    except OSError:
        pass
    return pack


def _norm_brand(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def _compose_brief(extracted: ExtractedBrief | None, form: ExtractedBrief | None) -> ExtractedBrief | None:
    """One brief only. A new upload/paste wins over a leftover working-brief form."""
    if extracted is None and form is None:
        return None
    if extracted is None:
        return form
    if form is None:
        return extracted
    extracted_brand = _norm_brand(extracted.brand)
    form_brand = _norm_brand(form.brand)
    if extracted_brand and form_brand and extracted_brand != form_brand:
        return extracted
    same_sources = set(extracted.source_files or []) == set(form.source_files or [])
    if not same_sources and (extracted.brand or extracted.therapy_area or extracted.raw_text):
        return extracted
    data = extracted.to_dict()
    for key, value in form.to_dict().items():
        if value not in (None, "", []):
            data[key] = value
    return _brief_from_mapping(data)


def _brief_from_mapping(data: dict) -> ExtractedBrief:
    brief = ExtractedBrief()
    for key in brief.to_dict():
        if key in data and data[key] not in (None, ""):
            setattr(brief, key, data[key])
    if not brief.raw_text:
        brief.raw_text = json.dumps(data, ensure_ascii=False)
    return brief
