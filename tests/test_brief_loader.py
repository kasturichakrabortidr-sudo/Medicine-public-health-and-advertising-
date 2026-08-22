from pathlib import Path

import pytest

from medicomarketing_agent.cli import parse_outline
from medicomarketing_agent.config import load_brief, render_brief


def test_example_brief_loads():
    brief = load_brief("examples/brief.example.yaml")
    assert brief["brand"] == "CardioShield"
    assert "Cardiology" in brief["therapy_area"]
    md = render_brief(brief)
    assert "CLIENT BRIEF" in md
    assert "PARADIGM-HF" in md


def test_missing_required_fields(tmp_path: Path):
    p = tmp_path / "bad.yaml"
    p.write_text("product: only\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing required"):
        load_brief(p)


def test_parse_outline(tmp_path: Path):
    p = tmp_path / "outline.md"
    p.write_text("- First point\n- Second point\n\n# ignore\n", encoding="utf-8")
    assert parse_outline(str(p)) == ["First point", "Second point"]
