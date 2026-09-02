"""Extract science-viz specs from strategy Markdown and render infographics.

The pipeline used to stop at tables. This module turns structured scientific
data into client-facing SVG infographics and a single-page visual brief, so
the numbers are shown as what they represent — and can be carried through
the science → solution → execution thread.
"""

from __future__ import annotations

import html
import json
import math
import re
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


VIZ_FENCE = "science-viz"
VIZ_BLOCK_RE = re.compile(
    rf"```{VIZ_FENCE}\s*\n(.*?)```",
    re.DOTALL,
)

# Clinical-comms palette: navy / teal / gold on warm paper.
PALETTE = {
    "navy": "#0B1F3A",
    "teal": "#1A7A7A",
    "gold": "#C4A35A",
    "slate": "#4A5568",
    "paper": "#F7F4EF",
    "card": "#FFFFFF",
    "line": "#D9D2C5",
    "positive": "#2F6F4E",
    "caution": "#9A5B13",
    "alert": "#B42318",
    "muted": "#8A8276",
    "soft_teal": "#D7EBEB",
    "soft_gold": "#F3E6C8",
    "soft_navy": "#D6DEE8",
}

TONES = {
    "positive": PALETTE["positive"],
    "caution": PALETTE["caution"],
    "alert": PALETTE["alert"],
    "neutral": PALETTE["navy"],
    "supportive": PALETTE["positive"],
    "unsupportive": PALETTE["alert"],
    "silent": PALETTE["muted"],
}

CHART_TYPES = (
    "patient_impact",
    "effect_size",
    "evidence_mix",
    "comparison_matrix",
    "cascade",
    "funnel",
    "driver_map",
    "callout_stat",
    "timeline",
)

VISUAL_GRAMMAR = """\
VISUAL GRAMMAR — required whenever you present scientific or behavioural data.

Do not leave numbers as table cells only. For every material finding, emit
one or more fenced `science-viz` JSON blocks. The engine renders each block
into a client-facing infographic. Rules:

- Never invent effect sizes, trial names, or guideline grades. If a number is
  not in the brief or a prior phase, use a labelled placeholder
  (e.g. "pending retrieval") and say so in `subtitle` and `source`.
- Every visual must answer: what the figure *represents* in plain clinical
  language (the "so what"), not only what was measured.
- Always include `source` and `mlr` (`required` | `not-promotional` | `cleared`).
- `id` must be unique kebab-case across the whole strategy.

Schema (all types share the header fields):

```science-viz
{
  "id": "unique-kebab-id",
  "type": "patient_impact|effect_size|evidence_mix|comparison_matrix|cascade|funnel|driver_map|callout_stat|timeline",
  "title": "What this picture shows",
  "subtitle": "What the data represents in clinical language",
  "source": "Named evidence, or 'illustrative — pending retrieval'",
  "mlr": "required",
  "...type-specific fields..."
}
```

Type-specific fields:

- patient_impact: {"of": 100, "horizon": "over the trial follow-up",
  "items": [{"label": "avoid a CV death or HF hospitalisation", "value": 5, "tone": "positive"}]}
- effect_size: {"unit": "hazard ratio", "comparator": "enalapril",
  "items": [{"label": "CV death or HF hospitalisation", "value": 0.80, "ci": "0.73–0.87", "direction": "favours brand", "note": ""}]}
- evidence_mix: {"items": [{"label": "Brand RCT", "value": 3, "grade": "A"},
  {"label": "Independent", "value": 4, "grade": "A/B"}]}
- comparison_matrix: {"columns": ["Brand", "Independent", "Evolving", "Guidelines"],
  "rows": [{"question": "Early initiation", "cells": ["supportive", "supportive", "supportive", "supportive"]}]}
  cells must be one of: supportive | neutral | unsupportive | silent
- cascade: {"steps": ["Science", "Implication", "Solution", "Execution", "Metric"],
  "rows": [{"id": "C1", "cells": ["finding", "what it means", "the solution", "the tactic", "the KPI"]}]}
- funnel: {"items": [{"label": "Aware", "value": 100}, {"label": "Advocating", "value": 8}]}
- driver_map: {"items": [{"driver": "...", "lever": "Motivation", "barrier": "..."}]}
- callout_stat: {"stat": "20%", "unit": "RRR", "meaning": "what this means at the bedside"}
- timeline: {"items": [{"stage": "Launch", "objective": "...", "cascade_ids": ["C1"]}]}
"""


def extract_viz_specs(markdown: str) -> list[dict[str, Any]]:
    """Return parsed science-viz objects, skipping invalid JSON."""
    specs: list[dict[str, Any]] = []
    for raw in VIZ_BLOCK_RE.findall(markdown or ""):
        spec = parse_viz_spec(raw)
        if spec:
            specs.append(spec)
    return specs


def parse_viz_spec(raw: str) -> dict[str, Any] | None:
    """Parse one science-viz payload. Returns None if it cannot be rendered."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    viz_type = str(data.get("type") or "").strip()
    viz_id = _safe_id(str(data.get("id") or ""))
    if viz_type not in CHART_TYPES or not viz_id:
        return None
    data = dict(data)
    data["id"] = viz_id
    data["type"] = viz_type
    data["title"] = str(data.get("title") or viz_id)
    data["subtitle"] = str(data.get("subtitle") or "")
    data["source"] = str(data.get("source") or "Source not stated")
    data["mlr"] = str(data.get("mlr") or "required")
    return data


def attach_visuals(markdown: str, visuals_dir: str | Path) -> tuple[str, list[Path]]:
    """Render every science-viz block and insert image embeds above them."""
    visuals_dir = Path(visuals_dir)
    visuals_dir.mkdir(parents=True, exist_ok=True)
    rendered: list[Path] = []

    def _replace(match: re.Match[str]) -> str:
        raw = match.group(1)
        spec = parse_viz_spec(raw)
        if not spec:
            return match.group(0)
        path = render_spec(spec, visuals_dir)
        rendered.append(path)
        rel = f"visuals/{path.name}"
        title = spec["title"]
        return (
            f"![{_md_alt(title)}]({rel})\n\n"
            f"*{_escape_md(spec['subtitle'])}*\n\n"
            f"Source: {_escape_md(spec['source'])} · MLR: {_escape_md(spec['mlr'])}\n\n"
            f"<details>\n<summary>Data behind this visual</summary>\n\n"
            f"```{VIZ_FENCE}\n{raw.strip()}\n```\n\n</details>"
        )

    rewritten = VIZ_BLOCK_RE.sub(_replace, markdown or "")
    return rewritten, rendered


def render_spec(spec: dict[str, Any], visuals_dir: str | Path) -> Path:
    """Render one spec to an SVG file. Raises ValueError on unknown type."""
    visuals_dir = Path(visuals_dir)
    visuals_dir.mkdir(parents=True, exist_ok=True)
    renderer = {
        "patient_impact": _render_patient_impact,
        "effect_size": _render_effect_size,
        "evidence_mix": _render_evidence_mix,
        "comparison_matrix": _render_comparison_matrix,
        "cascade": _render_cascade,
        "funnel": _render_funnel,
        "driver_map": _render_driver_map,
        "callout_stat": _render_callout_stat,
        "timeline": _render_timeline,
    }[spec["type"]]
    svg = renderer(spec)
    path = visuals_dir / f"{spec['id']}.svg"
    path.write_text(svg, encoding="utf-8")
    return path


def write_visual_brief(
    out_dir: str | Path,
    brief: dict[str, Any],
    phase_titles: list[tuple[str, str]],
    visual_paths: list[Path],
) -> Path:
    """Write a standalone HTML visual brief that inlines every infographic."""
    out_dir = Path(out_dir)
    brand = html.escape(str(brief.get("brand") or "Brand"))
    therapy = html.escape(str(brief.get("therapy_area") or ""))
    cards = []
    for path in visual_paths:
        if not path.exists():
            continue
        svg = path.read_text(encoding="utf-8")
        cards.append(
            f'<figure class="viz" id="{html.escape(path.stem)}">'
            f"{svg}"
            f"<figcaption>{html.escape(path.stem.replace('-', ' '))}</figcaption>"
            f"</figure>"
        )
    spine = "".join(
        f"<li><span class='pid'>{html.escape(pid)}</span>"
        f"{html.escape(title)}</li>"
        for pid, title in phase_titles
    )
    body_cards = "\n".join(cards) or "<p class='empty'>No visuals were produced in this run.</p>"
    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>{brand} — Science to solution visual brief</title>
<style>
  :root {{
    --navy: {PALETTE["navy"]};
    --teal: {PALETTE["teal"]};
    --gold: {PALETTE["gold"]};
    --paper: {PALETTE["paper"]};
    --slate: {PALETTE["slate"]};
  }}
  html, body {{ margin: 0; padding: 0; background: var(--paper); color: var(--navy);
    font-family: "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif; }}
  header.hero {{ background: var(--navy); color: #F7F4EF; padding: 56px 48px 40px; }}
  header.hero p.kicker {{ letter-spacing: 0.16em; text-transform: uppercase;
    color: var(--gold); font-size: 12px; margin: 0 0 12px;
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; }}
  header.hero h1 {{ font-weight: 500; font-size: 40px; margin: 0 0 8px; }}
  header.hero p.sub {{ margin: 0; opacity: 0.85; }}
  main {{ max-width: 1080px; margin: 0 auto; padding: 36px 28px 80px; }}
  section h2 {{ font-weight: 500; border-bottom: 1px solid {PALETTE["line"]};
    padding-bottom: 8px; }}
  ol.spine {{ columns: 2; padding-left: 20px; color: var(--slate); }}
  ol.spine .pid {{ display: inline-block; min-width: 3.2em;
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    color: var(--teal); font-size: 12px; }}
  figure.viz {{ background: #fff; border: 1px solid {PALETTE["line"]};
    border-radius: 8px; padding: 16px; margin: 24px 0;
    box-shadow: 0 1px 0 rgba(11,31,58,0.04); }}
  figure.viz svg {{ width: 100%; height: auto; display: block; }}
  figure.viz figcaption {{ font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    font-size: 12px; color: var(--slate); margin-top: 10px; }}
  .disclaimer {{ font-size: 13px; color: var(--slate); background: #fff;
    border-left: 4px solid var(--gold); padding: 12px 16px; }}
  .empty {{ color: var(--slate); font-style: italic; }}
</style>
</head>
<body>
<header class="hero">
  <p class="kicker">Science → solution → execution</p>
  <h1>{brand}</h1>
  <p class="sub">{therapy} · Visual strategy brief · not for promotional use until MLR clearance</p>
</header>
<main>
  <section>
    <h2>How to read this pack</h2>
    <p>Each infographic translates a scientific finding into what it
    <em>represents</em> clinically, then the cascade shows how that meaning
    becomes the solution and the execution move that delivers it.</p>
    <ol class="spine">{spine}</ol>
  </section>
  <section>
    <h2>The scientific story, drawn</h2>
    {body_cards}
  </section>
  <p class="disclaimer">Strategy draft only. Every number, claim, and graphic
  must pass medical-legal-regulatory review and local promotion codes before
  any use with healthcare professionals. Visuals marked
  “illustrative — pending retrieval” are scaffolds, not evidence.</p>
</main>
</body>
</html>
"""
    dest = out_dir / "visual-strategy-brief.html"
    dest.write_text(html_doc, encoding="utf-8")
    return dest


# ------------------------------------------------------------------ renderers


def _frame(spec: dict[str, Any], width: int, height: int, body: str) -> str:
    title = _esc(spec["title"])
    subtitle = _esc(spec.get("subtitle") or "")
    source = _esc(spec.get("source") or "")
    mlr = _esc(spec.get("mlr") or "required")
    vid = _esc(spec["id"])
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="{vid}-title {vid}-desc"
     viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <title id="{vid}-title">{title}</title>
  <desc id="{vid}-desc">{subtitle}. Source: {source}. MLR: {mlr}.</desc>
  <rect width="{width}" height="{height}" fill="{PALETTE["paper"]}"/>
  <rect x="0" y="0" width="8" height="{height}" fill="{PALETTE["teal"]}"/>
  <text x="32" y="36" fill="{PALETTE["gold"]}" font-size="11"
        font-family="Helvetica, Arial, sans-serif" letter-spacing="1.6">
    WHAT THE SCIENCE REPRESENTS</text>
  <text x="32" y="64" fill="{PALETTE["navy"]}" font-size="22"
        font-family="Georgia, 'Times New Roman', serif">{title}</text>
  <text x="32" y="88" fill="{PALETTE["slate"]}" font-size="13"
        font-family="Helvetica, Arial, sans-serif">{subtitle}</text>
  {body}
  <text x="32" y="{height - 18}" fill="{PALETTE["muted"]}" font-size="11"
        font-family="Helvetica, Arial, sans-serif">Source: {source}  ·  MLR: {mlr}</text>
</svg>
"""


def _render_patient_impact(spec: dict[str, Any]) -> str:
    total = int(spec.get("of") or 100)
    total = max(1, min(total, 200))
    items = list(spec.get("items") or [])
    horizon = _esc(str(spec.get("horizon") or ""))
    cols = 10 if total <= 100 else 20
    rows = math.ceil(total / cols)
    cell = 18
    block_h = 110 + rows * cell
    height = 130 + len(items) * block_h + 36
    width = 920
    blocks = []
    y = 110
    if horizon:
        blocks.append(
            f'<text x="32" y="108" fill="{PALETTE["slate"]}" font-size="12" '
            f'font-family="Helvetica, Arial, sans-serif">{horizon}</text>'
        )
        y = 124
    for item in items:
        value = max(0, min(int(item.get("value") or 0), total))
        tone = TONES.get(str(item.get("tone") or "positive"), PALETTE["positive"])
        label = _esc(str(item.get("label") or ""))
        dots = []
        for i in range(total):
            r, c = divmod(i, cols)
            cx = 40 + c * cell
            cy = y + 48 + r * cell
            fill = tone if i < value else PALETTE["soft_navy"]
            dots.append(f'<circle cx="{cx}" cy="{cy}" r="6" fill="{fill}"/>')
        blocks.append(
            f'<text x="32" y="{y + 8}" fill="{PALETTE["navy"]}" font-size="36" '
            f'font-family="Georgia, serif">{value}</text>'
            f'<text x="88" y="{y + 2}" fill="{PALETTE["slate"]}" font-size="13" '
            f'font-family="Helvetica, Arial, sans-serif">of {total} patients</text>'
            f'<text x="88" y="{y + 20}" fill="{PALETTE["navy"]}" font-size="14" '
            f'font-family="Helvetica, Arial, sans-serif">{label}</text>'
            f"{''.join(dots)}"
        )
        y += block_h
    if not items:
        blocks.append(
            f'<text x="32" y="140" fill="{PALETTE["muted"]}" font-size="14" '
            f'font-family="Helvetica, Arial, sans-serif">No patient-impact items supplied.</text>'
        )
    return _frame(spec, width, max(height, y + 28), "".join(blocks))


def _render_effect_size(spec: dict[str, Any]) -> str:
    items = list(spec.get("items") or [])
    unit = _esc(str(spec.get("unit") or "effect"))
    comparator = _esc(str(spec.get("comparator") or "comparator"))
    width = 920
    row_h = 64
    height = 150 + max(1, len(items)) * row_h
    # Values may be HRs (~1) or percentages. Scale by max absolute value.
    values = []
    for item in items:
        try:
            values.append(float(item.get("value")))
        except (TypeError, ValueError):
            values.append(0.0)
    max_abs = max([abs(v) for v in values] + [1.0])
    axis_x0, axis_x1 = 300, 860
    axis_w = axis_x1 - axis_x0
    # If all values are below 2, treat as ratio around 1; else as magnitude bars.
    ratio_mode = max_abs <= 2.5 and any(v > 0 for v in values)
    body = [
        f'<text x="32" y="116" fill="{PALETTE["slate"]}" font-size="12" '
        f'font-family="Helvetica, Arial, sans-serif">Unit: {unit}  ·  vs {comparator}</text>'
    ]
    if ratio_mode:
        scale_max = max(2.0, max_abs * 1.15)
        mid = axis_x0 + axis_w * (1.0 / scale_max)
        body.append(
            f'<line x1="{mid}" y1="128" x2="{mid}" y2="{height - 40}" '
            f'stroke="{PALETTE["gold"]}" stroke-dasharray="3 3"/>'
            f'<text x="{mid + 6}" y="126" fill="{PALETTE["gold"]}" font-size="11" '
            f'font-family="Helvetica, Arial, sans-serif">1.0 (no difference)</text>'
        )
    else:
        mid = axis_x0
        scale_max = max_abs * 1.15 or 1
    for idx, item in enumerate(items):
        y = 148 + idx * row_h
        val = values[idx] if idx < len(values) else 0.0
        label = _esc(str(item.get("label") or f"Endpoint {idx + 1}"))
        ci = _esc(str(item.get("ci") or ""))
        direction = _esc(str(item.get("direction") or ""))
        if ratio_mode:
            x = axis_x0 + axis_w * (val / scale_max)
            x = min(max(x, axis_x0), axis_x1)
            bar_x, bar_w = (mid, x - mid) if x >= mid else (x, mid - x)
        else:
            bar_w = axis_w * (abs(val) / scale_max)
            bar_x = axis_x0
            x = axis_x0 + bar_w
        fill = PALETTE["teal"] if val <= 1 or not ratio_mode else PALETTE["alert"]
        if str(item.get("direction") or "").lower().startswith("favour"):
            fill = PALETTE["teal"]
        body.append(
            f'<text x="32" y="{y}" fill="{PALETTE["navy"]}" font-size="13" '
            f'font-family="Helvetica, Arial, sans-serif">{_truncate(label, 42)}</text>'
            f'<text x="32" y="{y + 16}" fill="{PALETTE["muted"]}" font-size="11" '
            f'font-family="Helvetica, Arial, sans-serif">{direction}  {ci}</text>'
            f'<rect x="{axis_x0}" y="{y - 10}" width="{axis_w}" height="16" '
            f'fill="{PALETTE["soft_navy"]}" rx="8"/>'
            f'<rect x="{bar_x}" y="{y - 10}" width="{max(bar_w, 0)}" height="16" '
            f'fill="{fill}" rx="8"/>'
            f'<text x="{min(x + 8, axis_x1 - 4)}" y="{y + 4}" fill="{PALETTE["navy"]}" '
            f'font-size="12" font-family="Helvetica, Arial, sans-serif">{_fmt_num(val)}</text>'
        )
    if not items:
        body.append(
            f'<text x="32" y="150" fill="{PALETTE["muted"]}" font-size="14" '
            f'font-family="Helvetica, Arial, sans-serif">No effect-size items supplied.</text>'
        )
    return _frame(spec, width, height, "".join(body))


def _render_evidence_mix(spec: dict[str, Any]) -> str:
    items = list(spec.get("items") or [])
    width, height = 920, 420
    total = sum(_num(i.get("value")) for i in items) or 1
    cx, cy, r, stroke = 210, 250, 92, 34
    circ = 2 * math.pi * r
    offset = 0.0
    colors = [PALETTE["teal"], PALETTE["navy"], PALETTE["gold"], PALETTE["positive"], PALETTE["caution"]]
    slices = []
    legend = []
    for idx, item in enumerate(items):
        value = _num(item.get("value"))
        length = circ * (value / total)
        color = colors[idx % len(colors)]
        # SVG circles start at 3 o'clock; rotate to 12 o'clock via dashoffset.
        slices.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" '
            f'stroke-width="{stroke}" stroke-dasharray="{length:.2f} {circ - length:.2f}" '
            f'stroke-dashoffset="{circ * 0.25 - offset:.2f}"/>'
        )
        offset += length
        label = _esc(str(item.get("label") or f"Stream {idx + 1}"))
        grade = _esc(str(item.get("grade") or ""))
        ly = 160 + idx * 36
        legend.append(
            f'<rect x="380" y="{ly - 14}" width="16" height="16" fill="{color}" rx="3"/>'
            f'<text x="406" y="{ly}" fill="{PALETTE["navy"]}" font-size="14" '
            f'font-family="Helvetica, Arial, sans-serif">{label}</text>'
            f'<text x="700" y="{ly}" fill="{PALETTE["slate"]}" font-size="13" '
            f'font-family="Helvetica, Arial, sans-serif">{_fmt_num(value)}  ·  grade {grade}</text>'
        )
    centre = (
        f'<text x="{cx}" y="{cy - 4}" text-anchor="middle" fill="{PALETTE["navy"]}" '
        f'font-size="28" font-family="Georgia, serif">{int(total)}</text>'
        f'<text x="{cx}" y="{cy + 18}" text-anchor="middle" fill="{PALETTE["slate"]}" '
        f'font-size="12" font-family="Helvetica, Arial, sans-serif">evidence items</text>'
    )
    body = "".join(slices) + centre + "".join(legend)
    if not items:
        body = (
            f'<text x="32" y="160" fill="{PALETTE["muted"]}" font-size="14" '
            f'font-family="Helvetica, Arial, sans-serif">No evidence-mix items supplied.</text>'
        )
    return _frame(spec, width, height, body)


def _render_comparison_matrix(spec: dict[str, Any]) -> str:
    columns = [str(c) for c in (spec.get("columns") or ["Brand", "Independent", "Evolving", "Guidelines"])]
    rows = list(spec.get("rows") or [])
    width = 920
    col_w = 140
    x0 = 280
    row_h = 48
    height = 150 + max(1, len(rows)) * row_h + 50
    fills = {
        "supportive": PALETTE["positive"],
        "neutral": PALETTE["gold"],
        "unsupportive": PALETTE["alert"],
        "silent": PALETTE["muted"],
    }
    body = []
    for i, col in enumerate(columns):
        body.append(
            f'<text x="{x0 + i * col_w + col_w / 2}" y="124" text-anchor="middle" '
            f'fill="{PALETTE["navy"]}" font-size="12" '
            f'font-family="Helvetica, Arial, sans-serif">{_esc(_truncate(col, 16))}</text>'
        )
    for r_idx, row in enumerate(rows):
        y = 148 + r_idx * row_h
        q = _esc(_truncate(str(row.get("question") or f"Q{r_idx + 1}"), 36))
        body.append(
            f'<text x="32" y="{y + 18}" fill="{PALETTE["navy"]}" font-size="13" '
            f'font-family="Helvetica, Arial, sans-serif">{q}</text>'
        )
        cells = list(row.get("cells") or [])
        for c_idx, col in enumerate(columns):
            status = str(cells[c_idx] if c_idx < len(cells) else "silent").lower()
            fill = fills.get(status, PALETTE["muted"])
            body.append(
                f'<rect x="{x0 + c_idx * col_w + 10}" y="{y}" width="{col_w - 20}" '
                f'height="32" rx="6" fill="{fill}"/>'
                f'<text x="{x0 + c_idx * col_w + col_w / 2}" y="{y + 21}" text-anchor="middle" '
                f'fill="#fff" font-size="11" font-family="Helvetica, Arial, sans-serif">'
                f"{_esc(status)}</text>"
            )
    legend_y = height - 40
    for i, (name, color) in enumerate(fills.items()):
        body.append(
            f'<rect x="{32 + i * 160}" y="{legend_y}" width="12" height="12" fill="{color}" rx="2"/>'
            f'<text x="{48 + i * 160}" y="{legend_y + 11}" fill="{PALETTE["slate"]}" font-size="11" '
            f'font-family="Helvetica, Arial, sans-serif">{name}</text>'
        )
    return _frame(spec, width, height, "".join(body))


def _render_cascade(spec: dict[str, Any]) -> str:
    steps = [str(s) for s in (spec.get("steps") or ["Science", "Implication", "Solution", "Execution", "Metric"])]
    rows = list(spec.get("rows") or [])
    width = 1100
    col_w = 196
    x0 = 32
    row_h = 92
    header_h = 130
    height = header_h + 28 + max(1, len(rows)) * row_h + 36
    body = []
    colors = [PALETTE["navy"], PALETTE["teal"], PALETTE["gold"], PALETTE["positive"], PALETTE["slate"]]
    for i, step in enumerate(steps):
        x = x0 + i * col_w
        body.append(
            f'<rect x="{x}" y="108" width="{col_w - 12}" height="28" rx="4" fill="{colors[i % len(colors)]}"/>'
            f'<text x="{x + (col_w - 12) / 2}" y="127" text-anchor="middle" fill="#fff" font-size="12" '
            f'font-family="Helvetica, Arial, sans-serif">{_esc(step.upper())}</text>'
        )
        if i < len(steps) - 1:
            body.append(
                f'<polygon points="{x + col_w - 14},122 {x + col_w - 2},122 {x + col_w - 8},128" '
                f'fill="{PALETTE["gold"]}"/>'
            )
    for r_idx, row in enumerate(rows):
        y = header_h + 20 + r_idx * row_h
        rid = _esc(str(row.get("id") or f"C{r_idx + 1}"))
        cells = list(row.get("cells") or [])
        body.append(
            f'<text x="32" y="{y - 4}" fill="{PALETTE["gold"]}" font-size="11" '
            f'font-family="Helvetica, Arial, sans-serif">{rid}</text>'
        )
        for c_idx, step in enumerate(steps):
            x = x0 + c_idx * col_w
            text = _esc(_truncate(str(cells[c_idx] if c_idx < len(cells) else ""), 90))
            wrapped = _svg_wrapped_text(
                text, x + 8, y + 16, width=col_w - 28, font_size=12, fill=PALETTE["navy"]
            )
            body.append(
                f'<rect x="{x}" y="{y}" width="{col_w - 12}" height="{row_h - 12}" '
                f'rx="6" fill="{PALETTE["card"]}" stroke="{PALETTE["line"]}"/>'
                f"{wrapped}"
            )
    if not rows:
        body.append(
            f'<text x="32" y="200" fill="{PALETTE["muted"]}" font-size="14" '
            f'font-family="Helvetica, Arial, sans-serif">No cascade rows supplied.</text>'
        )
    return _frame(spec, width, height, "".join(body))


def _render_funnel(spec: dict[str, Any]) -> str:
    items = list(spec.get("items") or [])
    width, height = 920, 160 + max(1, len(items)) * 52
    max_val = max([_num(i.get("value")) for i in items] + [1])
    body = []
    for idx, item in enumerate(items):
        y = 120 + idx * 52
        val = _num(item.get("value"))
        bar_w = 200 + 520 * (val / max_val)
        x = (width - bar_w) / 2
        label = _esc(str(item.get("label") or f"Stage {idx + 1}"))
        body.append(
            f'<rect x="{x}" y="{y}" width="{bar_w}" height="36" rx="4" fill="{PALETTE["teal"]}" '
            f'opacity="{max(0.35, 1 - idx * 0.12)}"/>'
            f'<text x="{width / 2}" y="{y + 24}" text-anchor="middle" fill="#fff" font-size="14" '
            f'font-family="Helvetica, Arial, sans-serif">{label}  ·  {_fmt_num(val)}</text>'
        )
    if not items:
        body.append(
            f'<text x="32" y="150" fill="{PALETTE["muted"]}" font-size="14" '
            f'font-family="Helvetica, Arial, sans-serif">No funnel items supplied.</text>'
        )
    return _frame(spec, width, height, "".join(body))


def _render_driver_map(spec: dict[str, Any]) -> str:
    items = list(spec.get("items") or [])
    width = 920
    height = 140 + max(1, len(items)) * 70
    body = []
    for idx, item in enumerate(items):
        y = 120 + idx * 70
        driver = _esc(str(item.get("driver") or f"Driver {idx + 1}"))
        lever = _esc(str(item.get("lever") or ""))
        barrier = _esc(str(item.get("barrier") or ""))
        body.append(
            f'<rect x="32" y="{y}" width="856" height="58" rx="8" fill="{PALETTE["card"]}" '
            f'stroke="{PALETTE["line"]}"/>'
            f'<rect x="32" y="{y}" width="8" height="58" fill="{PALETTE["teal"]}"/>'
            f'<text x="56" y="{y + 24}" fill="{PALETTE["navy"]}" font-size="15" '
            f'font-family="Georgia, serif">{driver}</text>'
            f'<text x="56" y="{y + 44}" fill="{PALETTE["slate"]}" font-size="12" '
            f'font-family="Helvetica, Arial, sans-serif">COM-B lever: {lever}  ·  Barrier: {barrier}</text>'
        )
    if not items:
        body.append(
            f'<text x="32" y="150" fill="{PALETTE["muted"]}" font-size="14" '
            f'font-family="Helvetica, Arial, sans-serif">No drivers supplied.</text>'
        )
    return _frame(spec, width, height, "".join(body))


def _render_callout_stat(spec: dict[str, Any]) -> str:
    stat = _esc(str(spec.get("stat") or "—"))
    unit = _esc(str(spec.get("unit") or ""))
    meaning = _esc(str(spec.get("meaning") or spec.get("subtitle") or ""))
    width, height = 920, 300
    body = (
        f'<rect x="32" y="120" width="856" height="140" rx="10" fill="{PALETTE["navy"]}"/>'
        f'<text x="64" y="188" fill="{PALETTE["gold"]}" font-size="56" '
        f'font-family="Georgia, serif">{stat}</text>'
        f'<text x="64" y="216" fill="{PALETTE["soft_gold"]}" font-size="14" '
        f'font-family="Helvetica, Arial, sans-serif">{unit}</text>'
        f'<text x="360" y="188" fill="#F7F4EF" font-size="16" '
        f'font-family="Helvetica, Arial, sans-serif">{_truncate(meaning, 70)}</text>'
    )
    return _frame(spec, width, height, body)


def _render_timeline(spec: dict[str, Any]) -> str:
    items = list(spec.get("items") or [])
    width = 920
    n = max(1, len(items))
    slot = 840 / n
    height = 280
    body = [
        f'<line x1="60" y1="180" x2="860" y2="180" stroke="{PALETTE["gold"]}" stroke-width="3"/>'
    ]
    for idx, item in enumerate(items):
        x = 60 + slot * idx + slot / 2
        stage = _esc(str(item.get("stage") or f"Stage {idx + 1}"))
        objective = _esc(_truncate(str(item.get("objective") or ""), 42))
        cids = item.get("cascade_ids") or []
        cid_text = _esc(", ".join(str(c) for c in cids))
        body.append(
            f'<circle cx="{x}" cy="180" r="10" fill="{PALETTE["teal"]}"/>'
            f'<text x="{x}" y="150" text-anchor="middle" fill="{PALETTE["navy"]}" font-size="13" '
            f'font-family="Helvetica, Arial, sans-serif">{stage}</text>'
            f'<text x="{x}" y="214" text-anchor="middle" fill="{PALETTE["slate"]}" font-size="11" '
            f'font-family="Helvetica, Arial, sans-serif">{objective}</text>'
            f'<text x="{x}" y="232" text-anchor="middle" fill="{PALETTE["gold"]}" font-size="11" '
            f'font-family="Helvetica, Arial, sans-serif">{cid_text}</text>'
        )
    if not items:
        body.append(
            f'<text x="32" y="150" fill="{PALETTE["muted"]}" font-size="14" '
            f'font-family="Helvetica, Arial, sans-serif">No timeline items supplied.</text>'
        )
    return _frame(spec, width, height, "".join(body))


# ----------------------------------------------------------------- helpers


def _safe_id(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9-]+", "-", value.strip().lower()).strip("-")
    return cleaned[:80]


def _esc(value: str) -> str:
    return html.escape(value or "", quote=True)


def _escape_md(value: str) -> str:
    return (value or "").replace("\n", " ").strip()


def _md_alt(value: str) -> str:
    return _escape_md(value).replace("]", "")


def _truncate(value: str, n: int) -> str:
    value = " ".join((value or "").split())
    return value if len(value) <= n else value[: n - 1] + "…"


def _num(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _fmt_num(value: float) -> str:
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _svg_wrapped_text(text: str, x: float, y: float, width: int, font_size: int, fill: str) -> str:
    """Naive word-wrap for SVG (approx 0.6em per character)."""
    chars = max(8, int(width / (font_size * 0.55)))
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if len(trial) <= chars:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    lines = lines[:4]
    parts = []
    for i, line in enumerate(lines):
        parts.append(
            f'<text x="{x}" y="{y + i * (font_size + 4)}" fill="{fill}" '
            f'font-size="{font_size}" font-family="Helvetica, Arial, sans-serif">{line}</text>'
        )
    return "".join(parts)


def svg_is_well_formed(svg: str) -> bool:
    """True when the SVG parses as XML — used by tests."""
    try:
        ET.fromstring(svg)
    except ET.ParseError:
        return False
    return True
