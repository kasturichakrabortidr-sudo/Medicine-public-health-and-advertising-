"""FastAPI surface for STRATA — extract any brief format, generate a deck."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from medicomarketing_agent.config import load_brief

from .extract import ExtractedBrief, extract_files, merge_into_brief
from .generate import generate_pack

app = FastAPI(title="STRATA Strategy Director", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_BRIEF = ROOT / "examples" / "brief.example.yaml"

ACCEPT_HINT = (
    ".pdf .ppt .pptx .doc .docx .xls .xlsx .csv .tsv .txt .md .rtf .yaml .yml "
    ".json .html .htm .xml .odt .odp .ods .png .jpg .jpeg .webp .gif .log"
)


@app.get("/api/health")
def health():
    return {"ok": True, "service": "strata-director", "accept": ACCEPT_HINT}


@app.get("/api/demo")
def demo():
    brief = _brief_from_mapping(load_brief(EXAMPLE_BRIEF))
    pack = generate_pack(brief, mode="demo")
    pack["meta"]["source"] = "examples/brief.example.yaml"
    return pack


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

    extracted = extract_files(uploads)
    brief = merge_into_brief(extracted, pasted)
    return {
        "files": [
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
        ],
        "brief": brief.to_dict(),
        "accept": ACCEPT_HINT,
    }


@app.post("/api/generate")
async def generate(
    files: list[UploadFile] | None = File(default=None),
    pasted: str = Form(default=""),
    brief_json: str = Form(default=""),
    mode: str = Form(default="director"),
):
    if brief_json.strip():
        try:
            mapping = json.loads(brief_json)
        except json.JSONDecodeError as exc:
            raise HTTPException(400, f"brief_json is not valid JSON: {exc}") from exc
        brief = _brief_from_mapping(mapping)
    else:
        uploads = []
        if files:
            for f in files:
                payload = await f.read()
                if len(payload) > 25 * 1024 * 1024:
                    raise HTTPException(413, f"{f.filename} exceeds 25 MB")
                uploads.append((f.filename or "upload", payload, f.content_type or ""))
        if not uploads and not pasted.strip():
            raise HTTPException(400, "Provide files, pasted text, or brief_json.")
        brief = merge_into_brief(extract_files(uploads), pasted)

    if not brief.brand and not brief.therapy_area and not brief.raw_text:
        raise HTTPException(422, "Could not read a usable brief from the upload.")

    return generate_pack(brief, mode=mode)


def _brief_from_mapping(data: dict) -> ExtractedBrief:
    brief = ExtractedBrief()
    for key in brief.to_dict():
        if key in data and data[key] not in (None, ""):
            setattr(brief, key, data[key])
    if not brief.raw_text:
        brief.raw_text = json.dumps(data, ensure_ascii=False)
    return brief
