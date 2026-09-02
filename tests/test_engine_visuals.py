"""Engine + CLI integration around visuals, with the model stubbed out."""

from __future__ import annotations

from pathlib import Path

from medicomarketing_agent.cli import main
from medicomarketing_agent.engine import StrategyEngine
from medicomarketing_agent.phases import PHASES


VIZ_REPLY = """How this section was built: stubbed for tests.

```science-viz
{"id": "test-callout", "type": "callout_stat", "title": "Lead figure",
 "subtitle": "what the number represents", "source": "stub", "mlr": "required",
 "stat": "15%", "unit": "QoQ volume", "meaning": "the commercial target the science must serve"}
```
"""


def test_run_pipeline_renders_visuals_and_html_brief(tmp_path: Path, monkeypatch):
    engine = StrategyEngine(
        {"brand": "CardioShield", "therapy_area": "HFrEF"},
        out_dir=tmp_path,
        quiet=True,
    )
    monkeypatch.setattr(engine, "_turn", lambda _content: VIZ_REPLY)
    phase = next(p for p in PHASES if p.id == "04-science-infographics")
    combined = engine.run_pipeline([phase])
    assert combined.exists()
    phase_md = (tmp_path / "04-science-infographics.md").read_text(encoding="utf-8")
    assert "![Lead figure](visuals/test-callout.svg)" in phase_md
    assert (tmp_path / "visuals" / "test-callout.svg").exists()
    html = (tmp_path / "visual-strategy-brief.html").read_text(encoding="utf-8")
    assert "CardioShield" in html
    assert "test-callout" in html


def test_cli_phases_lists_new_spine(capsys):
    assert main(["phases"]) == 0
    out = capsys.readouterr().out
    assert "04-science-infographics" in out
    assert "08-science-to-solution" in out
    assert "13-executive-summary" in out
    assert out.count("\n") >= 13


def test_cli_render_visuals(tmp_path: Path, capsys):
    src = Path(__file__).resolve().parents[1] / "examples" / "science-viz.example.md"
    assert main(["render-visuals", "--input", str(src), "--out", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "Rendered 9 infographic(s)" in out
    assert (tmp_path / "visuals" / "science-to-solution-cascade.svg").exists()
    rewritten = (tmp_path / src.name).read_text(encoding="utf-8")
    assert "![Science to solution through strategy execution]" in rewritten
