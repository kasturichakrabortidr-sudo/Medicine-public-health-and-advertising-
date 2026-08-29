"""Guardrail: the committed demo deck must only contain validated references."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

DEMO = Path("web/public/demo/literature-deck.json")


class DemoDeckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DEMO.exists():
            raise unittest.SkipTest("demo deck not generated")
        cls.deck = json.loads(DEMO.read_text(encoding="utf-8"))

    def test_prisma_matches_records(self):
        self.assertEqual(self.deck["prisma"]["included"], len(self.deck["records"]))
        self.assertEqual(len(self.deck["records"]), len(self.deck["references"]))

    def test_every_reference_is_registry_validated(self):
        for ref in self.deck["references"]:
            self.assertTrue(ref.get("validated_via"), ref)
            self.assertTrue(ref.get("url"), ref)
            self.assertTrue(ref.get("citation"), ref)

    def test_no_covid_false_positives(self):
        for rec in self.deck["records"]:
            self.assertNotIn("covid-19", rec["title"].lower())

    def test_has_quant_qual_and_visuals(self):
        self.assertGreaterEqual(len(self.deck["quantitative"]["claim_frequency"]), 3)
        if self.deck["qualitative"]["n_qualitative_papers"]:
            self.assertGreaterEqual(len(self.deck["qualitative"]["ipa"]["superordinate_themes"]), 1)
        self.assertGreaterEqual(len(self.deck["forest"]), 1)
        self.assertTrue(str(self.deck["meta"]["pipeline_version"]).startswith("1.5"))
        self.assertTrue(any("NG106" in r["title"] for r in self.deck["records"]))
        self.assertTrue(any("HEARTS" in r["title"] for r in self.deck["records"]))
        self.assertTrue(self.deck["quantitative"].get("grade_profile"))
        self.assertIn("wall_clock_seconds", self.deck["meta"]["time_savings"])
        paradigm = [r for r in self.deck["forest"] if abs(r["value"] - 0.80) < 0.001 and abs(r["ci_low"] - 0.73) < 0.001]
        self.assertTrue(paradigm, "PARADIGM-HF HR 0.80 (0.73-0.87) must appear on the forest plot")
        self.assertTrue(any("PARADIGM" in (r.get("label") or "") for r in paradigm))
        dois = " ".join((r.get("doi") or "") for r in self.deck["records"]).lower()
        self.assertIn("nejmoa1409077", dois)
        self.assertTrue(
            self.deck["qualitative"]["n_qualitative_papers"] >= 1
            or "jocn.13615" in dois
            or "1472-6963-10-77" in dois,
            "at least one qualitative HF paper must remain in the demo corpus",
        )
