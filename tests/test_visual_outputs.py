import tempfile
import unittest
from pathlib import Path

from medicomarketing_agent.engine import StrategyEngine
from medicomarketing_agent.phases import (
    EXPAND_PROMPT,
    PHASES,
    PHASE_VISUAL_BRIEFS,
    SYSTEM_PROMPT,
    build_phase_prompt,
)
from medicomarketing_agent.report import MERMAID_MODULE_URL, render_strategy_html


SAMPLE_VISUAL = """\
## Visual synthesis

```mermaid
flowchart LR
    EV["EV-001: trial"] --> CM["CM-001: clinical meaning"]
    CM --> SOL["SOL-001: solution"]
```

**What it shows**: A traceable scientific path.
**So what**: The solution is not an orphan tactic.
**Evidence anchors**: EV-001 and CM-001.
**Decision enabled**: Advance SOL-001 to MLR review.
"""


class VisualContractTests(unittest.TestCase):
    def test_every_phase_has_a_visual_brief_and_contract(self):
        self.assertEqual({phase.id for phase in PHASES}, set(PHASE_VISUAL_BRIEFS))

        for phase in PHASES:
            rendered = build_phase_prompt(phase)
            with self.subTest(phase=phase.id):
                self.assertIn("## Required visual synthesis", rendered)
                self.assertIn(PHASE_VISUAL_BRIEFS[phase.id], rendered)
                self.assertIn("**Evidence anchors**", rendered)
                self.assertIn("valid Mermaid fenced block", rendered)

    def test_system_contract_connects_science_to_execution(self):
        expected_chain = (
            "EV-### evidence -> CM-### clinical meaning -> HI-### HCP insight or\n"
            "   BD-### behavioural driver -> SC-### strategic choice -> SOL-### solution or\n"
            "   message -> EX-### execution -> KPI-### measure"
        )
        self.assertIn(expected_chain, SYSTEM_PROMPT)
        self.assertIn("HYPOTHESIS — REQUIRES VALIDATION", SYSTEM_PROMPT)

    def test_outline_expansion_requires_visual_traceability(self):
        self.assertIn("valid Mermaid flowchart", EXPAND_PROMPT)
        self.assertIn("EV-### | CM-###", EXPAND_PROMPT)
        self.assertIn("Never invent numeric chart", EXPAND_PROMPT)


class VisualReportTests(unittest.TestCase):
    def test_report_renders_mermaid_tables_and_escapes_model_html(self):
        markdown = (
            "# Strategy\n\n"
            + SAMPLE_VISUAL
            + "\n| ID | Meaning |\n|---|---|\n| EV-001 | Benefit |\n\n"
            + '<script data-model-authored="true">alert("unsafe")</script>'
        )

        report = render_strategy_html(markdown, 'Strategy <script>alert("title")</script>')

        self.assertIn('<pre class="mermaid">flowchart LR', report)
        self.assertIn("<table>", report)
        self.assertIn(MERMAID_MODULE_URL, report)
        self.assertIn("&lt;script", report)
        self.assertNotIn('<script data-model-authored="true">', report)
        self.assertIn("&lt;script&gt;alert", report)

    def test_pipeline_writes_markdown_and_visual_html(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = StrategyEngine.__new__(StrategyEngine)
            engine.brief = {"brand": "TestBrand", "therapy_area": "Test area"}
            engine.out_dir = Path(temp_dir)
            engine.model = "test-model"
            engine.quiet = True
            engine.messages = []
            engine.results = {}
            engine._turn = lambda _content: SAMPLE_VISUAL

            combined = engine.run_pipeline([PHASES[0]])
            visual_report = Path(temp_dir) / "medicomarketing-strategy.html"

            self.assertTrue(combined.exists())
            self.assertTrue(visual_report.exists())
            self.assertIn(
                '<pre class="mermaid">flowchart LR',
                visual_report.read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
