"""FastAPI surface for STRATA — extract any brief format, generate a deck."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from medicomarketing_agent.config import load_brief

from .billing import (
    COOKIE,
    BillingError,
    apply_pack,
    apply_subscription,
    catalog as billing_catalog,
    load_wallet,
    public_wallet,
    spend,
)
from .deck_skills import catalog
from .extract import ExtractedBrief, extract_files, merge_into_brief
from .generate import generate_pack
from .pptx_export import filename_for, pack_to_pptx
from .projects import delete_project, get_project, list_projects, save_project, upsert_ongoing
from . import stripe_billing

app = FastAPI(title="STRATA Strategy Director", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_BRIEF = ROOT / "examples" / "brief.example.yaml"
DIST = ROOT / "web" / "dist"

ACCEPT_HINT = (
    ".pdf .ppt .pptx .doc .docx .xls .xlsx .csv .tsv .txt .md .rtf .yaml .yml "
    ".json .html .htm .xml .odt .odp .ods .png .jpg .jpeg .webp .gif .log"
)


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "service": "strata-director",
        "accept": ACCEPT_HINT,
        "build": "2026-08-22-credits",
        "deckSkills": catalog()["skills"],
        "billing": {"stripe": billing_catalog()["stripe"], "actions": billing_catalog()["actions"]},
    }


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
    request: Request,
    files: list[UploadFile] | None = File(default=None),
    pasted: str = Form(default=""),
    brief_json: str = Form(default=""),
    mode: str = Form(default="director"),
):
    uploads = []
    if files:
        for f in files:
            payload = await f.read()
            if len(payload) > 25 * 1024 * 1024:
                raise HTTPException(413, f"{f.filename} exceeds 25 MB")
            uploads.append((f.filename or "upload", payload, f.content_type or ""))

    file_brief = None
    if uploads or pasted.strip():
        file_brief = merge_into_brief(extract_files(uploads), pasted)

    json_brief = None
    if brief_json.strip():
        try:
            mapping = json.loads(brief_json)
        except json.JSONDecodeError as exc:
            raise HTTPException(400, f"brief_json is not valid JSON: {exc}") from exc
        if not isinstance(mapping, dict):
            raise HTTPException(400, "brief_json must be an object.")
        json_brief = _brief_from_mapping(mapping)

    if json_brief and file_brief:
        brief = _fill_empty(json_brief, file_brief)
    else:
        brief = json_brief or file_brief

    if brief is None:
        raise HTTPException(400, "Provide files, pasted text, or brief_json.")

    if not brief.brand and not brief.therapy_area and not brief.raw_text:
        raise HTTPException(422, "Could not read a usable brief from the upload.")

    if mode == "demo":
        raise HTTPException(400, "Demo mode is only available from GET /api/demo.")

    wallet = _wallet(request)
    try:
        spend(wallet, "write_file")
    except BillingError as exc:
        raise HTTPException(exc.status, exc.payload) from exc

    pack = generate_pack(brief, mode=mode)
    pack["meta"]["demo"] = False
    pack["meta"]["source"] = (
        ", ".join(brief.source_files)
        or pack["meta"].get("source")
        or "uploaded brief"
    )
    try:
        recs = (pack.get("evidence") or {}).get("records") or []
        Path("/tmp/strata-last-generate.json").write_text(
            json.dumps(
                {
                    "brand": brief.brand,
                    "product": brief.product,
                    "molecule": (pack.get("meta") or {}).get("molecule"),
                    "therapy_area": brief.therapy_area,
                    "indication": brief.indication,
                    "insights": brief.hcp_insights,
                    "doctrine": (pack.get("doctrine") or {}).get("id"),
                    "n_records": len(recs),
                    "papers": [
                        {
                            "ref": r.get("ref"),
                            "role": r.get("roleLabel") or r.get("role"),
                            "pmid": r.get("pmid"),
                            "short": r.get("short"),
                        }
                        for r in recs
                    ],
                    "lead": ((pack.get("evidence") or {}).get("lead") or {}).get("statement"),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    except OSError:
        pass
    try:
        upsert_ongoing(pack)
    except (OSError, ValueError, TypeError):
        pass
    pack["meta"]["credits"] = public_wallet(wallet)
    return _with_wallet(pack, request, wallet)


@app.get("/api/deck-skills")
def deck_skills():
    return catalog()


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
        if payload.get("id"):
            record = save_project(payload)
        elif payload.get("status") == "saved":
            record = save_project(payload)
        else:
            record = upsert_ongoing(pack)
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


@app.get("/api/billing")
def billing_catalog_get(request: Request):
    wallet = _wallet(request)
    return _with_wallet({"catalog": billing_catalog(), "wallet": public_wallet(wallet)}, request, wallet)


@app.get("/api/billing/me")
def billing_me(request: Request):
    wallet = _wallet(request)
    return _with_wallet(public_wallet(wallet), request, wallet)


@app.post("/api/billing/checkout")
async def billing_checkout(request: Request):
    wallet = _wallet(request)
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    item = str((payload or {}).get("item") or "")
    base = str(request.base_url).rstrip("/")
    if not stripe_billing.configured():
        raise HTTPException(
            503,
            {
                "error": "stripe_missing",
                "message": "Add STRIPE_SECRET_KEY to take real payments. Until then you can start a plan on this machine.",
                "sandbox": True,
            },
        )
    try:
        session = stripe_billing.start_checkout(wallet, item, base)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, f"Stripe checkout failed: {exc}") from exc
    return _with_wallet(session, request, wallet)


@app.post("/api/billing/portal")
async def billing_portal(request: Request):
    wallet = _wallet(request)
    if not stripe_billing.configured():
        raise HTTPException(503, "Stripe is not configured.")
    try:
        session = stripe_billing.start_portal(wallet, str(request.base_url).rstrip("/"))
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc
    return _with_wallet(session, request, wallet)


@app.post("/api/billing/sandbox")
async def billing_sandbox(request: Request):
    if stripe_billing.configured():
        raise HTTPException(400, "Stripe is configured. Use Checkout, not the local grant.")
    wallet = _wallet(request)
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    item = str((payload or {}).get("item") or "")
    try:
        if item in ("practice", "agency"):
            wallet = apply_subscription(wallet, item)
        elif item:
            wallet = apply_pack(wallet, item)
        else:
            raise HTTPException(400, "Pick a plan or credit pack.")
    except BillingError as exc:
        raise HTTPException(exc.status, exc.payload) from exc
    return _with_wallet({"ok": True, "wallet": public_wallet(wallet)}, request, wallet)


@app.post("/api/billing/claim")
async def billing_claim(request: Request):
    if not stripe_billing.configured():
        raise HTTPException(503, "Stripe is not configured.")
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    session_id = str((payload or {}).get("session_id") or "")
    try:
        wallet = stripe_billing.claim_session(session_id)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, f"Could not claim checkout: {exc}") from exc
    if not wallet:
        raise HTTPException(404, "Checkout did not match a wallet.")
    return _with_wallet({"ok": True, "wallet": public_wallet(wallet)}, request, wallet)


@app.post("/api/billing/webhook")
async def billing_webhook(request: Request):
    payload = await request.body()
    signature = request.headers.get("stripe-signature") or ""
    try:
        event = stripe_billing.parse_webhook(payload, signature)
    except Exception as exc:
        raise HTTPException(400, f"Webhook rejected: {exc}") from exc
    return stripe_billing.handle_event(event)


@app.get("/api/export/pptx")
def export_demo_pptx():
    return _pptx_response(demo())


@app.post("/api/export/pptx")
async def export_pptx(request: Request):
    try:
        pack = await request.json()
    except Exception as exc:
        raise HTTPException(400, f"Body must be a JSON strategy pack: {exc}") from exc
    if not isinstance(pack, dict) or not pack.get("slides"):
        raise HTTPException(400, "JSON must be a strategy pack with slides.")
    meta = pack.get("meta") or {}
    demo = bool(meta.get("demo")) or meta.get("mode") == "demo"
    wallet = _wallet(request)
    if not demo:
        try:
            spend(wallet, "export_pptx")
        except BillingError as exc:
            raise HTTPException(exc.status, exc.payload) from exc
    response = _pptx_response(pack)
    _set_cookie(response, request, wallet)
    return response


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


@app.get("/demo.json")
def demo_file():
    path = DIST / "demo.json"
    if not path.exists():
        path = ROOT / "web" / "public" / "demo.json"
    if not path.exists():
        raise HTTPException(404, "demo.json missing")
    return FileResponse(path, media_type="application/json")


@app.get("/")
def spa_index():
    return _web_file("")


@app.get("/{full_path:path}")
def spa(full_path: str):
    """Serve the built web app so a single URL opens on phones and laptops."""
    if full_path == "api" or full_path.startswith("api/"):
        raise HTTPException(404, "Not found")
    return _web_file(full_path)


def _web_file(path: str):
    if path:
        for root in (DIST, ROOT / "web" / "public"):
            candidate = (root / path).resolve()
            try:
                candidate.relative_to(root.resolve())
            except ValueError:
                continue
            if candidate.is_file():
                headers = {}
                if candidate.name in {"index.html", "index.htm"}:
                    headers = {
                        "Cache-Control": "no-store, no-cache, must-revalidate",
                        "Pragma": "no-cache",
                    }
                return FileResponse(candidate, headers=headers)
    index = DIST / "index.html"
    if index.exists():
        return FileResponse(
            index,
            headers={
                "Cache-Control": "no-store, no-cache, must-revalidate",
                "Pragma": "no-cache",
            },
        )
    raise HTTPException(
        503,
        "Web build missing. From the repo root run: python start_director.py",
    )


def _wallet(request: Request) -> dict:
    return load_wallet(request.cookies.get(COOKIE))


def _set_cookie(response: Response, request: Request, wallet: dict) -> None:
    response.set_cookie(
        COOKIE,
        wallet["id"],
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 365,
        path="/",
        secure=request.url.scheme == "https",
    )


def _with_wallet(payload, request: Request, wallet: dict) -> JSONResponse:
    response = JSONResponse(payload)
    _set_cookie(response, request, wallet)
    return response


def _brief_from_mapping(data: dict) -> ExtractedBrief:
    brief = ExtractedBrief()
    for key in brief.to_dict():
        if key in data and data[key] not in (None, ""):
            setattr(brief, key, data[key])
    if not brief.raw_text:
        brief.raw_text = json.dumps(data, ensure_ascii=False)
    return brief


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
    "source_files",
    "extraction_notes",
}


def _fill_empty(primary: ExtractedBrief, fallback: ExtractedBrief) -> ExtractedBrief:
    """Keep edited form fields; fill blanks from the uploaded files."""
    out = ExtractedBrief()
    for key in out.to_dict():
        pv = getattr(primary, key)
        fv = getattr(fallback, key)
        if key == "raw_text":
            parts = [p for p in (pv, fv) if p]
            setattr(out, key, "\n\n---\n\n".join(dict.fromkeys(parts)))
        elif key in LIST_FIELDS:
            setattr(out, key, list(pv or fv or []))
        else:
            setattr(out, key, pv or fv)
    return out
