"""Tests that the pipeline's phase content actually asks for and can produce
the visual chart specs, and that the new science-to-execution bridge phase
is wired into the pipeline in the right place."""

import unittest

from medicomarketing_agent.phases import EXPAND_PROMPT, PHASES, SYSTEM_PROMPT

EXPECTED_ORDER = [
    "01-critical-thinking",
    "02-scientific-criteria",
    "03-evidence-forefront",
    "04-hcp-insights",
    "05-behavioural-drivers",
    "06-evidence-position",
    "07-core-messaging",
    "08-hcp-engagement",
    "09-activation-ideas",
    "10-measurement",
    "11-science-to-execution-bridge",
    "12-executive-summary",
]

# Phases that must instruct the model to emit at least one ```chart block —
# i.e. every phase that presents comparative/hierarchical/sequential/
# quantitative scientific or strategic data.
PHASES_REQUIRING_CHARTS = set(EXPECTED_ORDER)


class PhaseOrderingTests(unittest.TestCase):
    def test_phase_ids_are_in_the_expected_order(self):
        self.assertEqual([p.id for p in PHASES], EXPECTED_ORDER)

    def test_bridge_phase_sits_between_measurement_and_executive_summary(self):
        ids = [p.id for p in PHASES]
        bridge_idx = ids.index("11-science-to-execution-bridge")
        measurement_idx = ids.index("10-measurement")
        summary_idx = ids.index("12-executive-summary")
        self.assertEqual(bridge_idx, measurement_idx + 1)
        self.assertEqual(summary_idx, bridge_idx + 1)

    def test_bridge_phase_title_reflects_science_to_execution_connection(self):
        bridge = next(p for p in PHASES if p.id == "11-science-to-execution-bridge")
        self.assertIn("Science-to-Solution Bridge", bridge.title)
        self.assertIn("Traceability", bridge.title)


class ChartInstructionCoverageTests(unittest.TestCase):
    def test_system_prompt_documents_the_chart_spec_format(self):
        self.assertIn("CHART SPEC FORMAT", SYSTEM_PROMPT)
        for chart_type in ("bar", "pie", "quadrant", "funnel", "tree"):
            self.assertIn(f'"type":"{chart_type}"', SYSTEM_PROMPT)

    def test_every_phase_instructs_at_least_one_chart(self):
        for phase in PHASES:
            if phase.id in PHASES_REQUIRING_CHARTS:
                with self.subTest(phase=phase.id):
                    self.assertIn("`", phase.prompt)
                    self.assertIn("chart", phase.prompt.lower())
                    self.assertRegex(phase.prompt, r"`(bar|pie|quadrant|funnel|tree)` chart")

    def test_bridge_phase_asks_for_a_tree_diagram_connecting_evidence_to_kpi(self):
        bridge = next(p for p in PHASES if p.id == "11-science-to-execution-bridge")
        self.assertIn("`tree` chart", bridge.prompt)
        self.assertIn("Traceability matrix", bridge.prompt)
        self.assertIn("evidence", bridge.prompt.lower())
        self.assertIn("KPI", bridge.prompt)

    def test_expand_prompt_also_requires_charts_and_science_to_execution_links(self):
        self.assertIn("CHART SPEC FORMAT", EXPAND_PROMPT)
        self.assertIn("science and execution", EXPAND_PROMPT.lower())


if __name__ == "__main__":
    unittest.main()
