"""Build an editable 16:9 PowerPoint from a STRATA strategy pack.

Shapes, text, tables, and native Office charts are written as real PPT
objects so a client can open the file in PowerPoint or Google Slides and
keep editing. Forest and box plots are drawn with shapes (still editable).
"""

from __future__ import annotations

import io
import re
from typing import Any

from pptx import Presentation
from pptx.chart.data import CategoryChartData, XyChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

INK = RGBColor(0x0B, 0x12, 0x20)
NAVY = RGBColor(0x13, 0x20, 0x37)
CREAM = RGBColor(0xFA, 0xF6, 0xEF)
PAPER = RGBColor(0xF4, 0xEF, 0xE6)
COPPER = RGBColor(0xC4, 0x84, 0x4A)
TEAL = RGBColor(0x2A, 0x6F, 0x6F)
CRIMSON = RGBColor(0x8B, 0x2E, 0x2E)
MUTED = RGBColor(0x5B, 0x62, 0x70)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)


def pack_to_pptx(pack: dict) -> bytes:
    """Return a .pptx byte string for the given strategy pack."""
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    blank = prs.slide_layouts[6]

    meta = pack.get("meta") or {}
    doctrine = pack.get("doctrine") or {}
    slides = pack.get("slides") or []

    for spec in slides:
        slide = prs.slides.add_slide(blank)
        dark = spec.get("layout") in {"title", "close"}
        _fill_slide(slide, INK if dark else CREAM)
        _render_slide(slide, spec, dark)
        _notes(slide, spec)

    _appendix_interventions(prs, blank, pack)
    _appendix_dashboard(prs, blank, pack)
    _appendix_edit_guide(prs, blank, meta, doctrine)

    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue()


def filename_for(pack: dict) -> str:
    brand = (pack.get("meta") or {}).get("brand") or "strategy"
    slug = re.sub(r"[^A-Za-z0-9]+", "-", brand).strip("-") or "strategy"
    return f"{slug}-strategy-deck.pptx"


def _fill_slide(slide, color: RGBColor) -> None:
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_W, SLIDE_H)
    shape.line.fill.background()
    fill = shape.fill
    fill.solid()
    fill.fore_color.rgb = color
    # Send the background behind other shapes.
    sp_tree = slide.shapes._spTree
    sp = shape._element
    sp_tree.remove(sp)
    sp_tree.insert(2, sp)


def _textbox(slide, l, t, w, h, text, *, size=16, bold=False, color=INK, font="Calibri", align=PP_ALIGN.LEFT):
    box = slide.shapes.add_textbox(l, t, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    tf.auto_size = None
    p = tf.paragraphs[0]
    p.text = text or ""
    p.font.size = Pt(size)
    p.font.bold = bold
    p.font.color.rgb = color
    p.font.name = font
    p.alignment = align
    return box


def _as_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        return "; ".join(f"{k}: {v}" for k, v in value.items())
    if isinstance(value, list):
        return "; ".join(_as_text(v) for v in value)
    return str(value)


def _bullets(slide, l, t, w, h, items: list, *, color=INK, size=15):
    box = slide.shapes.add_textbox(l, t, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items or []):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = _as_text(item)
        p.level = 0
        p.font.size = Pt(size)
        p.font.color.rgb = color
        p.font.name = "Calibri"
        p.space_after = Pt(8)
    return box


def _table(slide, l, t, w, h, headers: list[str], rows: list[list[str]]):
    cols = max(len(headers), 1)
    n_rows = 1 + len(rows)
    table_shape = slide.shapes.add_table(n_rows, cols, l, t, w, h)
    table = table_shape.table
    for j, header in enumerate(headers):
        cell = table.cell(0, j)
        cell.text = header
        _style_cell(cell, NAVY, WHITE, bold=True, size=11)
    for i, row in enumerate(rows, 1):
        for j in range(cols):
            cell = table.cell(i, j)
            cell.text = _as_text(row[j] if j < len(row) else "")
            bg = PAPER if i % 2 else CREAM
            _style_cell(cell, bg, INK, size=11)
    return table_shape


def _style_cell(cell, bg: RGBColor, fg: RGBColor, *, bold=False, size=12):
    cell.fill.solid()
    cell.fill.fore_color.rgb = bg
    for p in cell.text_frame.paragraphs:
        p.font.size = Pt(size)
        p.font.bold = bold
        p.font.color.rgb = fg
        p.font.name = "Calibri"
        p.alignment = PP_ALIGN.LEFT
    cell.vertical_anchor = MSO_ANCHOR.MIDDLE


def _notes(slide, spec: dict) -> None:
    bits = [spec.get("narrative") or ""]
    if spec.get("callout"):
        bits.append(f"{spec['callout'].get('label')}: {spec['callout'].get('text')}")
    chart = spec.get("chart") or {}
    if chart.get("note"):
        bits.append(chart["note"])
    notes = slide.notes_slide.notes_text_frame
    notes.text = "\n\n".join(b for b in bits if b)


def _render_slide(slide, spec: dict, dark: bool) -> None:
    ink = CREAM if dark else INK
    muted = RGBColor(0xF0, 0xC4, 0x8A) if dark else COPPER
    body = RGBColor(0xE8, 0xE2, 0xD6) if dark else MUTED

    _textbox(slide, Inches(0.55), Inches(0.28), Inches(12.2), Inches(0.32),
             (spec.get("kicker") or "").upper(), size=11, color=muted, font="Calibri")
    _textbox(slide, Inches(0.55), Inches(0.58), Inches(12.2), Inches(1.15),
             spec.get("title") or "", size=28 if dark else 24, bold=True, color=ink, font="Calibri")

    if spec.get("subtitle"):
        _textbox(slide, Inches(0.55), Inches(1.7), Inches(12.2), Inches(0.4),
                 spec["subtitle"], size=16, color=body)

    layout = spec.get("layout")
    if layout in {"title", "close", "insight"}:
        top = Inches(2.25) if spec.get("subtitle") else Inches(1.9)
        _textbox(slide, Inches(0.55), top, Inches(12.1), Inches(1.6),
                 spec.get("narrative") or "", size=16, color=body)
        if spec.get("bullets"):
            _bullets(slide, Inches(0.7), Inches(4.0), Inches(11.8), Inches(2.4),
                     spec["bullets"], color=ink if not dark else CREAM, size=16)
        if spec.get("callout"):
            _callout(slide, Inches(0.55), Inches(6.55), Inches(12.2), Inches(0.7), spec["callout"], dark)
        return

    # Two-column body slides
    _textbox(slide, Inches(0.55), Inches(1.85), Inches(5.6), Inches(1.5),
             spec.get("narrative") or "", size=14, color=body)
    if spec.get("bullets"):
        _bullets(slide, Inches(0.55), Inches(3.4), Inches(5.6), Inches(2.4),
                 spec["bullets"], color=INK, size=14)
    if spec.get("callout"):
        _callout(slide, Inches(0.55), Inches(6.55), Inches(5.6), Inches(0.7), spec["callout"], False)

    right_l, right_t, right_w, right_h = Inches(6.4), Inches(1.85), Inches(6.4), Inches(4.9)
    if spec.get("chart"):
        _add_chart(slide, spec["chart"], right_l, right_t, right_w, right_h)
    elif spec.get("table"):
        table = spec["table"]
        _table(slide, right_l, right_t, right_w, right_h, table.get("headers") or [], table.get("rows") or [])

    if spec.get("table") and spec.get("chart"):
        table = spec["table"]
        _table(slide, Inches(0.55), Inches(5.6), Inches(5.6), Inches(1.5),
               table.get("headers") or [], table.get("rows") or [])


def _callout(slide, l, t, w, h, callout: dict, dark: bool) -> None:
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, l, t, w, h)
    shape.adjustments[0] = 0.08
    shape.line.fill.background()
    fill = shape.fill
    fill.solid()
    fill.fore_color.rgb = NAVY if dark else RGBColor(0xF3, 0xE3, 0xC8)
    label = callout.get("label") or ""
    text = callout.get("text") or ""
    _textbox(slide, l + Inches(0.15), t + Inches(0.08), w - Inches(0.3), h - Inches(0.1),
             f"{label}. {text}".strip(), size=12, color=CREAM if dark else INK)


def _add_chart(slide, spec: dict, l, t, w, h) -> None:
    kind = spec.get("kind")
    data = spec.get("data") or []
    title = spec.get("title") or ""
    _textbox(slide, l, t - Inches(0.28), w, Inches(0.28), title, size=11, color=MUTED)

    if kind == "forest":
        _forest(slide, data, l, t, w, h)
        return
    if kind == "box":
        _box(slide, data, l, t, w, h)
        return
    if not data:
        return

    if kind == "pie":
        cd = CategoryChartData()
        cd.categories = [str(r.get("name", "")) for r in data]
        cd.add_series("Share", [_num(r.get("value")) for r in data])
        chart = slide.shapes.add_chart(XL_CHART_TYPE.PIE, l, t, w, h, cd).chart
        chart.has_legend = True
        chart.legend.position = XL_LEGEND_POSITION.BOTTOM
        return

    if kind == "line":
        series = spec.get("series") or ["value"]
        cd = CategoryChartData()
        cd.categories = [str(r.get("name", "")) for r in data]
        for s in series:
            cd.add_series(s, [_num(r.get(s)) for r in data])
        chart = slide.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, l, t, w, h, cd).chart
        chart.has_legend = True
        return

    if kind == "scatter":
        cd = XyChartData()
        series = cd.add_series("Moves")
        for r in data:
            series.add_data_point(_num(r.get("x")), _num(r.get("y")))
        slide.shapes.add_chart(XL_CHART_TYPE.XY_SCATTER, l, t, w, h, cd)
        return

    if kind == "diverging":
        cd = CategoryChartData()
        cd.categories = [str(r.get("name", "")) for r in data]
        cd.add_series("Matches evidence", [max(_num(r.get("value")), 0) for r in data])
        cd.add_series("Perception gap", [min(_num(r.get("value")), 0) for r in data])
        chart = slide.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, l, t, w, h, cd).chart
        chart.has_legend = True
        return

    # bar / funnel default
    cd = CategoryChartData()
    cd.categories = [str(r.get("name", "")) for r in data]
    cd.add_series(spec.get("unit") or "Value", [_num(r.get("value")) for r in data])
    slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, l, t, w, h, cd)


def _num(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _forest(slide, rows: list[dict], l, t, w, h) -> None:
    """Editable forest plot: lines + diamonds, not a flattened image."""
    if not rows:
        return
    nums = []
    for r in rows:
        nums.extend([_num(r.get("low")), _num(r.get("high")), _num(r.get("hr"))])
    lo, hi = min(0.55, min(nums) - 0.04), max(1.15, max(nums) + 0.04)
    plot_l = l + Inches(2.3)
    plot_w = w - Inches(2.5)
    row_h = int(h / max(len(rows), 1))

    def x_at(v: float) -> int:
        return int(plot_l + ((v - lo) / (hi - lo)) * plot_w)

    # Null line at 1.0
    null_x = x_at(1.0)
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, null_x, t, Emu(12700), h - Inches(0.2))
    line.fill.solid()
    line.fill.fore_color.rgb = COPPER
    line.line.fill.background()
    _textbox(slide, null_x - Inches(0.4), t - Inches(0.22), Inches(0.9), Inches(0.22),
             "null 1.0", size=9, color=COPPER, align=PP_ALIGN.CENTER)

    for i, r in enumerate(rows):
        y = t + row_h * i + int(row_h * 0.35)
        _textbox(slide, l, y - Inches(0.12), Inches(2.2), Inches(0.45),
                 f"{r.get('name', '')}\n{r.get('stream', '')} · {r.get('grade', '')}",
                 size=10, color=INK)
        x1, x2, xm = x_at(_num(r.get("low"))), x_at(_num(r.get("high"))), x_at(_num(r.get("hr")))
        bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, min(x1, x2), y, max(abs(x2 - x1), Emu(12700)), Emu(19050))
        bar.fill.solid()
        bar.fill.fore_color.rgb = NAVY
        bar.line.fill.background()
        diamond = slide.shapes.add_shape(MSO_SHAPE.DIAMOND, xm - Emu(69850), y - Emu(50800), Emu(139700), Emu(139700))
        diamond.fill.solid()
        diamond.fill.fore_color.rgb = COPPER
        diamond.line.fill.background()


def _box(slide, rows: list[dict], l, t, w, h) -> None:
    if not rows:
        return
    col_w = int(w / len(rows))
    axis_top, axis_bot = t + Inches(0.15), t + h - Inches(0.45)

    def y_at(v: float) -> int:
        return int(axis_bot - (v / 10.0) * (axis_bot - axis_top))

    for i, r in enumerate(rows):
        cx = l + col_w * i + col_w // 2
        y_min, y_q1 = y_at(_num(r.get("min"))), y_at(_num(r.get("q1")))
        y_med, y_q3 = y_at(_num(r.get("median"))), y_at(_num(r.get("q3")))
        y_max = y_at(_num(r.get("max")))
        whisker = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, cx, min(y_max, y_min), Emu(12700), abs(y_min - y_max))
        whisker.fill.solid()
        whisker.fill.fore_color.rgb = NAVY
        whisker.line.fill.background()
        box_top, box_bot = min(y_q3, y_q1), max(y_q3, y_q1)
        box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, cx - Inches(0.22), box_top, Inches(0.44), max(box_bot - box_top, Emu(25400)))
        box.fill.solid()
        box.fill.fore_color.rgb = TEAL
        box.line.color.rgb = NAVY
        med = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, cx - Inches(0.22), y_med, Inches(0.44), Emu(19050))
        med.fill.solid()
        med.fill.fore_color.rgb = CREAM
        med.line.fill.background()
        _textbox(slide, l + col_w * i, t + h - Inches(0.4), col_w, Inches(0.4),
                 str(r.get("name", "")), size=10, color=INK, align=PP_ALIGN.CENTER)


def _appendix_interventions(prs, blank, pack: dict) -> None:
    items = pack.get("interventions") or []
    if not items:
        return
    slide = prs.slides.add_slide(blank)
    _fill_slide(slide, CREAM)
    _textbox(slide, Inches(0.55), Inches(0.28), Inches(12.2), Inches(0.32),
             "APPENDIX  ·  INTERVENTION BOARD", size=11, color=COPPER)
    _textbox(slide, Inches(0.55), Inches(0.55), Inches(12.2), Inches(0.5),
             "Five moves — owners can edit effort, copy, and kill-criteria", size=22, bold=True, color=INK)
    headers = ["Move", "Promise", "COM-B lever", "Segment", "Impact", "Feasibility", "Kill-criterion"]
    rows = [
        [i.get("name", ""), i.get("promise", ""), i.get("lever", ""), i.get("segment", ""),
         str(i.get("impact", "")), str(i.get("feasibility", "")), i.get("kill", "")]
        for i in items
    ]
    _table(slide, Inches(0.4), Inches(1.3), Inches(12.5), Inches(5.7), headers, rows)


def _appendix_dashboard(prs, blank, pack: dict) -> None:
    dash = pack.get("dashboard") or {}
    kpis = dash.get("kpis") or []
    if not kpis:
        return
    slide = prs.slides.add_slide(blank)
    _fill_slide(slide, CREAM)
    _textbox(slide, Inches(0.55), Inches(0.28), Inches(12.2), Inches(0.32),
             "APPENDIX  ·  MEASUREMENT ROOM", size=11, color=COPPER)
    _textbox(slide, Inches(0.55), Inches(0.55), Inches(12.2), Inches(0.5),
             "Starting KPIs — replace illustrative numbers before client lock", size=22, bold=True, color=INK)
    headers = ["KPI", "Now", "Target", "Unit", "Type"]
    rows = [[k.get("label", ""), str(k.get("value", "")), str(k.get("target", "")),
             k.get("unit", ""), k.get("tone", "")] for k in kpis]
    _table(slide, Inches(0.55), Inches(1.25), Inches(6.2), Inches(3.2), headers, rows)

    revenue = dash.get("revenue") or []
    if revenue:
        cd = CategoryChartData()
        cd.categories = [str(r.get("name", "")) for r in revenue]
        for s in ("revenue", "initiation", "conviction"):
            if s in revenue[0]:
                cd.add_series(s, [_num(r.get(s)) for r in revenue])
        slide.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, Inches(7.0), Inches(1.25), Inches(5.7), Inches(3.4), cd)

    gov = dash.get("governance") or []
    if gov:
        _table(slide, Inches(0.55), Inches(4.7), Inches(12.2), Inches(2.3),
               ["Cadence", "Forum", "Looks at"],
               [[g.get("cadence", ""), g.get("forum", ""), g.get("looksAt", "")] for g in gov])


def _appendix_edit_guide(prs, blank, meta: dict, doctrine: dict) -> None:
    slide = prs.slides.add_slide(blank)
    _fill_slide(slide, INK)
    _textbox(slide, Inches(0.55), Inches(0.4), Inches(12.2), Inches(0.32),
             "HOW TO EDIT THIS DECK", size=11, color=COPPER)
    _textbox(slide, Inches(0.55), Inches(0.8), Inches(12.2), Inches(0.7),
             "Every object is a native PowerPoint shape, chart, or table.", size=26, bold=True, color=CREAM)
    _bullets(slide, Inches(0.7), Inches(1.8), Inches(12.0), Inches(4.8), [
        "Click any title, bullet, or table cell and type. Fonts are Calibri so they travel.",
        "Bar, line, pie, and scatter charts are Office charts — right-click → Edit Data to change numbers.",
        "Forest and box plots are grouped shapes. Drag a diamond or box to restyle; replace values in the labels.",
        "Speaker notes under each slide carry the narrative and any evidence caveats.",
        "MLR: no promotional use until medical-legal-regulatory clears claims and field scripts.",
        f"Brand: {meta.get('brand', '—')}  ·  Doctrine: {doctrine.get('name', meta.get('doctrine', '—'))}  ·  Generated: {meta.get('generatedAt', '—')}",
    ], color=CREAM, size=16)


