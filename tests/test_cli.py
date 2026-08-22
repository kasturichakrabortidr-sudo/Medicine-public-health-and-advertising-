"""Tests that the CLI's phase selection and outline parsing still work with
the 12-phase pipeline (after inserting the science-to-execution bridge)."""

import unittest
from pathlib import Path

from medicomarketing_agent.cli import parse_outline, select_phases
from medicomarketing_agent.phases import PHASES

REPO_ROOT = Path(__file__).resolve().parent.parent


class SelectPhasesTests(unittest.TestCase):
    def test_none_spec_returns_none_meaning_run_everything(self):
        self.assertIsNone(select_phases(None))

    def test_selecting_the_bridge_phase_by_prefix(self):
        selected = select_phases("11")
        self.assertEqual([p.id for p in selected], ["11-science-to-execution-bridge"])

    def test_selecting_the_executive_summary_by_prefix(self):
        selected = select_phases("12")
        self.assertEqual([p.id for p in selected], ["12-executive-summary"])

    def test_selecting_a_range_of_phases(self):
        selected = select_phases("03,11,12")
        self.assertEqual(
            [p.id for p in selected],
            ["03-evidence-forefront", "11-science-to-execution-bridge", "12-executive-summary"],
        )

    def test_unknown_prefix_raises(self):
        with self.assertRaises(ValueError):
            select_phases("99")

    def test_all_twelve_phases_present_exactly_once(self):
        self.assertEqual(len(PHASES), 12)
        self.assertEqual(len({p.id for p in PHASES}), 12)


class ParseOutlineTests(unittest.TestCase):
    def test_parses_the_bundled_example_outline(self):
        points = parse_outline(str(REPO_ROOT / "examples" / "outline.example.md"))
        self.assertGreaterEqual(len(points), 5)
        self.assertTrue(all(isinstance(p, str) and p for p in points))


if __name__ == "__main__":
    unittest.main()
