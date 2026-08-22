"""Renderer, extraction, and visual-brief tests — no API required."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from medicomarketing_agent.visuals import (
    CHART_TYPES,
    attach_visuals,
    extract_viz_specs,
    parse_viz_spec,
    render_spec,
    svg_is_well_formed,
    write_visual_brief,
)

EXAMPLES = Path(__file__).resolve().parents[1] / "examples" / "science-viz.example.md"


def _minimal(viz_type: str, **extra) -> dict:
    spec = {
        "id": f"demo-{viz_type.replace('_', '-')}",
        "type": viz_type,
        "title": f"Demo {viz_type}",
        "subtitle": "What this figure represents",
        "source": "unit test",
        "mlr": "not-promotional",
    }
    spec.update(extra)
    return spec


def test_example_markdown_contains_every_chart_type():
    specs = extract_viz_specs(EXAMPLES.read_text(encoding="utf-8"))
    found = {s["type"] for s in specs}
    assert found == set(CHART_TYPES)


def test_each_chart_type_renders_well_formed_svg(tmp_path: Path):
    payloads = {
        "patient_impact": {"of": 20, "items": [{"label": "avoid an event", "value": 3, "tone": "positive"}]},
        "effect_size": {
            "unit": "HR",
            "comparator": "ACEI",
            "items": [{"label": "composite", "value": 0.8, "ci": "0.7–0.9", "direction": "favours brand"}],
        },
        "evidence_mix": {"items": [{"label": "Brand RCT", "value": 2, "grade": "A"}]},
        "comparison_matrix": {
            "columns": ["Brand", "Guidelines"],
            "rows": [{"question": "Early start", "cells": ["supportive", "supportive"]}],
        },
        "cascade": {
            "steps": ["Science", "Implication", "Solution", "Execution", "Metric"],
            "rows": [{"id": "C1", "cells": ["finding", "means", "solution", "tactic", "KPI"]}],
        },
        "funnel": {"items": [{"label": "Aware", "value": 10}, {"label": "Advocating", "value": 1}]},
        "driver_map": {"items": [{"driver": "Confidence", "lever": "Motivation", "barrier": "Habit"}]},
        "callout_stat": {"stat": "20%", "unit": "RRR", "meaning": "fewer composite events"},
        "timeline": {"items": [{"stage": "Launch", "objective": "Show the visual", "cascade_ids": ["C1"]}]},
    }
    for viz_type, extra in payloads.items():
        path = render_spec(_minimal(viz_type, **extra), tmp_path)
        svg = path.read_text(encoding="utf-8")
        assert path.name == f"demo-{viz_type.replace('_', '-')}.svg"
        assert svg_is_well_formed(svg)
        assert "WHAT THE SCIENCE REPRESENTS" in svg
        assert "Source: unit test" in svg


def test_parse_viz_spec_rejects_unknown_type_and_bad_json():
    assert parse_viz_spec("{") is None
    assert parse_viz_spec(json.dumps({"id": "x", "type": "pie"})) is None
    assert parse_viz_spec(json.dumps({"id": "", "type": "funnel"})) is None


def test_attach_visuals_embeds_image_and_keeps_data(tmp_path: Path):
    md = """
## Finding

```science-viz
{"id": "lead-callout-rrr", "type": "callout_stat", "title": "20% RRR",
 "subtitle": "population-level composite", "source": "example", "mlr": "required",
 "stat": "20%", "unit": "RRR", "meaning": "not a promise to one patient"}
```
"""
    rewritten, paths = attach_visuals(md, tmp_path / "visuals")
    assert len(paths) == 1
    assert paths[0].exists()
    assert "![20% RRR](visuals/lead-callout-rrr.svg)" in rewritten
    assert "Data behind this visual" in rewritten
    assert '"type": "callout_stat"' in rewritten


def test_invalid_block_is_left_untouched(tmp_path: Path):
    md = "```science-viz\nnot-json\n```"
    rewritten, paths = attach_visuals(md, tmp_path)
    assert rewritten == md
    assert paths == []


def test_write_visual_brief_inlines_svg(tmp_path: Path):
    spec = _minimal(
        "callout_stat",
        stat="20%",
        unit="RRR",
        meaning="bedside so-what",
    )
    path = render_spec(spec, tmp_path / "visuals")
    dest = write_visual_brief(
        tmp_path,
        {"brand": "CardioShield", "therapy_area": "HFrEF"},
        [("04-science-infographics", "Scientific Data Visualization")],
        [path],
    )
    html = dest.read_text(encoding="utf-8")
    assert dest.name == "visual-strategy-brief.html"
    assert "CardioShield" in html
    assert "Science → solution → execution" in html
    assert "WHAT THE SCIENCE REPRESENTS" in html
    assert "04-science-infographics" in html


def test_example_file_renders_end_to_end(tmp_path: Path):
    rewritten, paths = attach_visuals(EXAMPLES.read_text(encoding="utf-8"), tmp_path / "visuals")
    assert len(paths) == 9
    assert all(p.suffix == ".svg" and p.exists() for p in paths)
    assert "science-to-solution-cascade" in rewritten
    cascade = next(s for s in extract_viz_specs(EXAMPLES.read_text(encoding="utf-8")) if s["id"] == "science-to-solution-cascade")
    assert cascade["rows"][0]["id"] == "C1"
    assert len(cascade["rows"][0]["cells"]) == 5
