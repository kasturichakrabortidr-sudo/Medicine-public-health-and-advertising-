"""Extract text and structured brief fields from any uploaded format."""

from __future__ import annotations

import csv
import io
import json
import re
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

KNOWN_FIELDS = (
    "brand",
    "product",
    "therapy_area",
    "indication",
    "market",
    "business_goal",
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
    "notes",
)

TEXT_SUFFIXES = {
    ".txt",
    ".md",
    ".markdown",
    ".rst",
    ".csv",
    ".tsv",
    ".json",
    ".yaml",
    ".yml",
    ".html",
    ".htm",
    ".xml",
    ".rtf",
    ".log",
    ".outline",
}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff"}
OFFICE_SUFFIXES = {".docx", ".pptx", ".xlsx", ".xls", ".odt", ".odp", ".ods", ".ppt", ".doc"}
PDF_SUFFIXES = {".pdf"}

SUPPORTED_SUFFIXES = TEXT_SUFFIXES | IMAGE_SUFFIXES | OFFICE_SUFFIXES | PDF_SUFFIXES | {".key"}


@dataclass
class ExtractedFile:
    filename: str
    mime: str
    suffix: str
    text: str
    notes: list[str] = field(default_factory=list)
    pages: int | None = None
    bytes: int = 0


@dataclass
class ExtractedBrief:
    brand: str = ""
    product: str = ""
    therapy_area: str = ""
    indication: str = ""
    market: str = ""
    business_goal: str = ""
    target_specialties: list[str] = field(default_factory=list)
    hcp_segments: list[str] = field(default_factory=list)
    brand_evidence: list[str] = field(default_factory=list)
    existing_evidence: list[str] = field(default_factory=list)
    evolving_evidence: list[str] = field(default_factory=list)
    guidelines: list[str] = field(default_factory=list)
    hcp_insights: list[str] = field(default_factory=list)
    competitors: list[str] = field(default_factory=list)
    access_and_cost: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    notes: str = ""
    source_files: list[str] = field(default_factory=list)
    raw_text: str = ""
    extraction_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def extract_files(uploads: list[tuple[str, bytes, str]]) -> list[ExtractedFile]:
    """Parse many uploads. Each tuple is (filename, payload, mime)."""
    return [extract_one(name, payload, mime) for name, payload, mime in uploads]


def extract_one(filename: str, payload: bytes, mime: str = "") -> ExtractedFile:
    suffix = Path(filename).suffix.lower()
    notes: list[str] = []
    text = ""
    pages = None
    route = _route_suffix(suffix, payload, mime)

    try:
        if route in {".yaml", ".yml"}:
            text = _from_yaml(payload)
        elif route == ".json":
            text = _from_json(payload)
        elif route in {".csv", ".tsv"}:
            text = _from_csv(payload, "\t" if route == ".tsv" else ",")
        elif route in {".html", ".htm", ".xml"}:
            text = _strip_markup(_decode(payload))
        elif route == ".rtf":
            text = _from_rtf(_decode(payload))
        elif route == ".pdf":
            text, pages = _from_pdf(payload)
        elif route == ".docx":
            text = _from_docx(payload)
        elif route == ".pptx":
            text = _from_pptx(payload)
        elif route in {".xlsx", ".xls"}:
            text = _from_xlsx(payload)
        elif route in {".odt", ".odp", ".ods"}:
            text = _from_opendocument(payload)
        elif route in {".ppt", ".doc"}:
            text = _from_ole_legacy(payload)
            if not text.strip():
                notes.append(
                    f"{route} is a legacy Office binary. Convert to .{route[1:]}x for richer extraction."
                )
        elif route in IMAGE_SUFFIXES:
            notes.append(
                "Image uploaded. Text was not OCR'd locally; attach a text/PDF brief for full extraction, "
                "or keep the image as a visual reference in the working file."
            )
            text = f"[Image attachment: {filename}]"
        elif route in TEXT_SUFFIXES or not route:
            text = _decode(payload)
        else:
            text = _decode(payload)
            if not text.strip():
                notes.append(f"No text extractor for {route or 'unknown type'}; stored as raw attachment.")
        if route in {".pdf", ".docx", ".pptx", ".xlsx"} and len(text.strip()) < 40:
            notes.append(
                "This file yielded very little text. If it is a scan or image-heavy deck, paste the brief."
            )
    except Exception as exc:  # keep the pipeline moving; record the failure
        notes.append(f"Partial extract for {filename}: {exc}")
        text = _decode(payload)

    return ExtractedFile(
        filename=filename,
        mime=mime or "application/octet-stream",
        suffix=suffix,
        text=text.strip(),
        notes=notes,
        pages=pages,
        bytes=len(payload),
    )


def merge_into_brief(files: list[ExtractedFile], pasted: str = "") -> ExtractedBrief:
    """Turn extracted file text + optional pasted copy into a structured brief."""
    chunks = [f.text for f in files if f.text]
    if pasted.strip():
        chunks.append(pasted.strip())
    raw = "\n\n---\n\n".join(chunks)
    brief = _parse_structured(raw)
    brief.raw_text = raw
    brief.source_files = [f.filename for f in files]
    brief.extraction_notes = [n for f in files for n in f.notes]
    _infer_missing(brief)
    from director_api.extract_infer import fill_from_prose

    fill_from_prose(brief)
    if raw.strip() and not brief.brand and not brief.therapy_area:
        brief.extraction_notes.append(
            "Could not find a brand or therapy area in this file. "
            "Paste the key lines, or type them into the working brief."
        )
    return brief


def _decode(payload: bytes) -> str:
    for enc in ("utf-8", "utf-16", "latin-1"):
        try:
            return payload.decode(enc)
        except UnicodeDecodeError:
            continue
    return payload.decode("utf-8", errors="replace")


def _from_yaml(payload: bytes) -> str:
    text = _decode(payload)
    if yaml is None:
        return text
    data = yaml.safe_load(text)
    if isinstance(data, dict):
        return _mapping_to_markdown(data)
    return text


def _from_json(payload: bytes) -> str:
    data = json.loads(_decode(payload))
    if isinstance(data, dict):
        return _mapping_to_markdown(data)
    return json.dumps(data, indent=2, ensure_ascii=False)


def _from_csv(payload: bytes, delimiter: str) -> str:
    buf = io.StringIO(_decode(payload))
    reader = csv.reader(buf, delimiter=delimiter)
    rows = list(reader)
    if not rows:
        return ""
    return "\n".join(" | ".join(cell.strip() for cell in row) for row in rows if any(row))


def _sniff_kind(payload: bytes) -> str | None:
    if payload[:4] == b"%PDF":
        return "pdf"
    if payload[:8] == b"\x89PNG\r\n\x1a\n" or payload[:3] == b"\xff\xd8\xff" or payload[:6] in {b"GIF87a", b"GIF89a"}:
        return "image"
    if payload[:2] == b"PK":
        try:
            with zipfile.ZipFile(io.BytesIO(payload)) as zf:
                names = set(zf.namelist())
        except zipfile.BadZipFile:
            return None
        if any(n.startswith("word/") for n in names):
            return "docx"
        if any(n.startswith("ppt/") for n in names):
            return "pptx"
        if any(n.startswith("xl/") for n in names):
            return "xlsx"
        if "content.xml" in names:
            return "odt"
    return None


def _route_suffix(suffix: str, payload: bytes, mime: str = "") -> str:
    sniffed = _sniff_kind(payload)
    mime_l = (mime or "").lower()
    if sniffed == "pdf" or "application/pdf" in mime_l:
        return ".pdf"
    if sniffed == "docx" or "wordprocessingml" in mime_l:
        return ".docx"
    if sniffed == "pptx" or "presentationml" in mime_l:
        return ".pptx"
    if sniffed == "xlsx" or "spreadsheetml" in mime_l:
        return ".xlsx"
    if sniffed == "image":
        return suffix if suffix in IMAGE_SUFFIXES else ".png"
    if sniffed == "odt":
        return suffix if suffix in {".odt", ".odp", ".ods"} else ".odt"
    return suffix


def _from_pdf(payload: bytes) -> tuple[str, int | None]:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(payload))
    pages = []
    for i, page in enumerate(reader.pages, 1):
        content = page.extract_text() or ""
        if content.strip():
            pages.append(f"Page {i}\n{content.strip()}")
    text = "\n\n".join(pages)
    page_count = len(reader.pages)
    if len(text.strip()) < 120:
        richer = _from_pdf_pdfminer(payload)
        if len(richer.strip()) > len(text.strip()):
            text = richer
    return text, page_count


def _from_pdf_pdfminer(payload: bytes) -> str:
    try:
        from pdfminer.high_level import extract_text as pdfminer_extract
    except ImportError:
        return ""
    try:
        return (pdfminer_extract(io.BytesIO(payload)) or "").strip()
    except Exception:
        return ""


def _from_docx(payload: bytes) -> str:
    from docx import Document

    doc = Document(io.BytesIO(payload))
    parts = [p.text.strip() for p in doc.paragraphs if p.text and p.text.strip()]
    for section in doc.sections:
        for hf in (section.header, section.footer):
            if hf is None:
                continue
            for p in hf.paragraphs:
                if p.text and p.text.strip():
                    parts.append(p.text.strip())
    for table in doc.tables:
        for row in table.rows:
            cells = [c.text.strip().replace("\n", " ") for c in row.cells if c.text.strip()]
            if cells:
                parts.append(" | ".join(cells))
    xml_bits = _docx_all_text_nodes(payload)
    joined = "\n".join(parts)
    if len(xml_bits) > len(joined) + 40:
        joined = f"{joined}\n\n{xml_bits}".strip() if joined else xml_bits
    return joined


def _docx_all_text_nodes(payload: bytes) -> str:
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as zf:
            xml = zf.read("word/document.xml").decode("utf-8", errors="replace")
    except Exception:
        return ""
    parts = re.findall(r"<w:t[^>]*>([^<]*)</w:t>", xml)
    return "\n".join(p.strip() for p in parts if p.strip())


def _from_pptx(payload: bytes) -> str:
    from pptx import Presentation

    prs = Presentation(io.BytesIO(payload))
    slides = []
    for i, slide in enumerate(prs.slides, 1):
        bits = _pptx_shape_text(slide.shapes)
        try:
            notes_slide = slide.notes_slide
            if notes_slide and notes_slide.notes_text_frame:
                nt = notes_slide.notes_text_frame.text.strip()
                if nt:
                    bits.append("Notes: " + nt)
        except Exception:
            pass
        if bits:
            slides.append(f"Slide {i}\n" + "\n".join(bits))
    return "\n\n".join(slides)


def _pptx_shape_text(shapes) -> list[str]:
    bits: list[str] = []
    for shape in shapes:
        if getattr(shape, "has_text_frame", False):
            t = shape.text_frame.text.strip()
            if t:
                bits.append(t)
        if getattr(shape, "has_table", False):
            for row in shape.table.rows:
                cells = [c.text.strip().replace("\n", " ") for c in row.cells if c.text.strip()]
                if cells:
                    bits.append(" | ".join(cells))
        nested = getattr(shape, "shapes", None)
        if nested is not None:
            try:
                bits.extend(_pptx_shape_text(nested))
            except Exception:
                pass
    return bits


def _from_xlsx(payload: bytes) -> str:
    from openpyxl import load_workbook

    wb = load_workbook(io.BytesIO(payload), data_only=True, read_only=True)
    sheets = []
    for name in wb.sheetnames:
        ws = wb[name]
        rows = []
        for row in ws.iter_rows(values_only=True):
            cells = [str(c).strip() for c in row if c not in (None, "")]
            if cells:
                rows.append(" | ".join(cells))
        if rows:
            sheets.append(f"## Sheet {name}\n" + "\n".join(rows[:400]))
    return "\n\n".join(sheets)


def _from_opendocument(payload: bytes) -> str:
    """Read text from ODF packages (content.xml)."""
    with zipfile.ZipFile(io.BytesIO(payload)) as zf:
        xml = zf.read("content.xml").decode("utf-8", errors="replace")
    return _strip_markup(xml)


def _from_ole_legacy(payload: bytes) -> str:
    """Best-effort string harvest from old .doc / .ppt binaries."""
    strings = re.findall(rb"[\x20-\x7e]{6,}", payload)
    text = "\n".join(s.decode("ascii", errors="ignore") for s in strings)
    return "\n".join(line for line in text.splitlines() if not _noise_line(line))


def _from_rtf(text: str) -> str:
    text = re.sub(r"\\'[0-9a-fA-F]{2}", " ", text)
    text = re.sub(r"\\[a-zA-Z]+-?\d* ?", " ", text)
    text = text.replace("{", " ").replace("}", " ")
    return re.sub(r"\s+", " ", text).strip()


def _strip_markup(text: str) -> str:
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _noise_line(line: str) -> bool:
    s = line.strip()
    if len(s) < 4:
        return True
    return bool(re.fullmatch(r"[A-Z0-9_\-.]{4,}", s)) and " " not in s


def _mapping_to_markdown(data: dict) -> str:
    lines = ["# CLIENT BRIEF", ""]
    for key, value in data.items():
        lines.append(f"## {str(key).replace('_', ' ').title()}")
        if isinstance(value, list):
            lines.extend(f"- {item}" for item in value)
        elif isinstance(value, dict):
            for k, v in value.items():
                lines.append(f"- **{k}**: {v}")
        else:
            lines.append(str(value))
        lines.append("")
    return "\n".join(lines)


def _parse_structured(raw: str) -> ExtractedBrief:
    """Accept YAML/JSON-shaped text or headed Markdown and fill known fields."""
    brief = ExtractedBrief()
    parsed = _try_load_mapping(raw)
    if parsed:
        _apply_mapping(brief, parsed)
        return brief

    current = None
    bucket: list[str] = []

    def flush():
        nonlocal current, bucket
        if current:
            _assign(brief, current, bucket)
        current = None
        bucket = []

    for line in raw.splitlines():
        stripped = line.strip()
        if re.match(r"^#{0,3}\s*(page|slide|sheet)\s+\S+", stripped, re.I):
            continue
        heading = re.match(r"^#{1,3}\s+(.+)$", stripped)
        label = re.match(r"^([A-Za-z][A-Za-z0-9 /_-]{1,40}):\s*(.*)$", stripped)
        key = None
        rest = ""
        if heading:
            key = _normalize_key(heading.group(1))
        elif label and _normalize_key(label.group(1)) in KNOWN_FIELDS:
            key = _normalize_key(label.group(1))
            rest = label.group(2).strip()
        if key and key in KNOWN_FIELDS:
            flush()
            current = key
            if rest:
                bucket.append(rest)
            continue
        if current:
            cleaned = stripped.lstrip("-*•").strip()
            if cleaned:
                bucket.append(cleaned)
    flush()
    return brief


def _looks_like_json_document(text: str) -> bool:
    stripped = text.lstrip()
    return stripped.startswith("{") and stripped.rstrip().endswith("}")


def _looks_like_yaml_document(text: str) -> bool:
    """True only for compact key: value YAML — not a 20-page Word brief."""
    if _looks_like_json_document(text):
        return False
    if "\x00" in text[:200]:
        return False
    lines = [ln.rstrip() for ln in text.splitlines() if ln.strip()]
    if not lines or len(lines) > 80:
        return False
    mappingish = 0
    for ln in lines[:40]:
        if re.match(r"^[\w.-]+\s*:", ln) and not ln.lstrip().startswith("#"):
            mappingish += 1
    return mappingish >= 2 and mappingish / max(len(lines[:40]), 1) >= 0.35


def _try_load_mapping(raw: str) -> dict | None:
    text = raw.strip()
    data = None
    if _looks_like_json_document(text):
        try:
            loaded = json.loads(text)
            data = loaded if isinstance(loaded, dict) else None
        except json.JSONDecodeError:
            data = None
    elif yaml is not None and _looks_like_yaml_document(text):
        try:
            loaded = yaml.safe_load(text)
            data = loaded if isinstance(loaded, dict) else None
        except Exception:
            data = None
    if not data:
        return None
    keys = {_normalize_key(str(k)) for k in data}
    if "brand" not in keys and "therapy_area" not in keys:
        return None
    return data


def _apply_mapping(brief: ExtractedBrief, data: dict) -> None:
    for key, value in data.items():
        norm = _normalize_key(str(key))
        if norm in KNOWN_FIELDS:
            _assign(brief, norm, value)


def _assign(brief: ExtractedBrief, key: str, value) -> None:
    list_fields = {
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
    }
    if key in list_fields:
        items = _as_list(value)
        setattr(brief, key, items)
    elif key == "notes":
        brief.notes = _as_text(value)
    else:
        items = _as_list(value)
        first = items[0] if items else ""
        setattr(brief, key, first if len(first) <= 400 else first[:397].rstrip() + "…")


def _as_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        out = []
        for item in value:
            if isinstance(item, (dict, list)):
                out.append(json.dumps(item, ensure_ascii=False))
            else:
                text = str(item).strip()
                if text:
                    out.append(text)
        return out
    text = str(value).strip()
    if not text:
        return []
    if "\n" in text:
        return [ln.lstrip("-*• ").strip() for ln in text.splitlines() if ln.strip()]
    return [text]


def _as_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "; ".join(str(v) for v in value if v)
    return str(value).strip()


def _normalize_key(label: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
    aliases = {
        "therapy": "therapy_area",
        "ta": "therapy_area",
        "therapy_area": "therapy_area",
        "disease_area": "therapy_area",
        "brand_name": "brand",
        "campaign": "brand",
        "campaign_name": "brand",
        "product_name": "product",
        "molecule": "product",
        "inn": "product",
        "goal": "business_goal",
        "objective": "business_goal",
        "objectives": "business_goal",
        "specialties": "target_specialties",
        "specialty": "target_specialties",
        "targets": "target_specialties",
        "segments": "hcp_segments",
        "evidence": "brand_evidence",
        "insights": "hcp_insights",
        "hcp_insight": "hcp_insights",
        "competitor": "competitors",
        "competition": "competitors",
        "access": "access_and_cost",
        "cost": "access_and_cost",
        "constraint": "constraints",
        "country": "market",
        "geography": "market",
        "region": "market",
    }
    return aliases.get(s, s)


def _infer_missing(brief: ExtractedBrief) -> None:
    """Fill obvious gaps from free text when structured fields are empty."""
    blob = brief.raw_text
    if not brief.brand:
        m = re.search(r"\bbrand\s*[:\-]\s*([A-Z][\w\- ]{1,40})", blob, re.I)
        if m:
            brief.brand = m.group(1).strip()
    if not brief.therapy_area:
        m = re.search(r"(cardiology|oncology|diabetes|neurology|respiratory|immunology|dermatology|infectious|heart failure|HFrEF|HFpEF)[^\n]{0,40}", blob, re.I)
        if m:
            brief.therapy_area = m.group(0).strip()
    if not brief.market:
        m = re.search(r"\b(India|United States|USA|UK|EU|China|Brazil|Japan|Germany|France)\b", blob)
        if m:
            brief.market = m.group(1)
