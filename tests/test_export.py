"""Export-format tests — no network."""

from __future__ import annotations

import unittest

from academic_research.export import to_bibtex, to_claim_csv, to_forest_csv, to_reference_csv, to_ris, write_pptx


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.payload = {
            "meta": {
                "pipeline_version": "1.9.0",
                "time_savings": {"reduction_percent": 75},
            },
            "brief": {"brand": "CardioShield", "indication": "HFrEF"},
            "pico": {
                "question": "In HFrEF, what validated evidence describes ARNI?",
                "population": "HFrEF",
                "intervention": "sacubitril/valsartan",
                "comparator": "enalapril",
                "outcomes": "CV death or HF hospitalisation",
                "setting": "India",
            },
            "prisma": {
                "identified": 10,
                "duplicates_removed": 2,
                "screened": 8,
                "excluded_off_topic": 1,
                "excluded_unvalidated": 1,
                "included": 1,
            },
            "quantitative": {
                "n_included": 1,
                "claim_frequency": [
                    {
                        "id": "mortality_or_hospitalisation_benefit",
                        "label": "Mortality or HF hospitalisation benefit",
                        "percent": 100,
                        "count": 1,
                        "citation_ids": [1],
                    }
                ],
                "grade_profile": [],
                "pooled_effect": {
                    "n_trials": 1,
                    "metric": "HR",
                    "value": 0.80,
                    "ci_low": 0.73,
                    "ci_high": 0.87,
                    "i_squared": 0.0,
                    "funnel": [
                        {
                            "citation_id": 1,
                            "label": "PARADIGM-HF (2014)",
                            "se": 0.045,
                            "weight": 493.8,
                        }
                    ],
                },
            },
            "qualitative": {"ipa": {"superordinate_themes": []}},
            "insights": {
                "cohort": "HFrEF",
                "prevalent_benefits": [],
                "prevalent_barriers": [],
                "gaps": [],
            },
            "forest": [
                {
                    "citation_id": 1,
                    "label": "PARADIGM-HF (2014)",
                    "value": 0.80,
                    "ci_low": 0.73,
                    "ci_high": 0.87,
                }
            ],
            "guidelines": [],
            "un_and_ngo": [],
            "references": [
                {
                    "n": 1,
                    "title": "Angiotensin-Neprilysin Inhibition versus Enalapril in Heart Failure",
                    "citation": "McMurray JJV et al. (2014). Angiotensin-Neprilysin Inhibition versus Enalapril in Heart Failure. NEJM.",
                    "doi": "10.1056/nejmoa1409077",
                    "url": "https://doi.org/10.1056/NEJMoa1409077",
                    "pmid": "25176015",
                    "validated_via": "crossref",
                }
            ],
        }

    def test_bibtex_contains_doi_and_validation_note(self):
        bib = to_bibtex(self.payload)
        self.assertIn("@article{", bib)
        self.assertIn("10.1056/nejmoa1409077", bib)
        self.assertIn("validated via crossref", bib.lower())

    def test_ris_contains_doi(self):
        ris = to_ris(self.payload)
        self.assertIn("TY  - JOUR", ris)
        self.assertIn("DO  - 10.1056/nejmoa1409077", ris)
        self.assertIn("ER  -", ris)

    def test_csv_tables_carry_citation_ids(self):
        claims = to_claim_csv(self.payload)
        self.assertIn("mortality_or_hospitalisation_benefit", claims)
        self.assertIn("100", claims)
        refs = to_reference_csv(self.payload)
        self.assertIn("10.1056/nejmoa1409077", refs)
        self.assertIn("crossref", refs)

    def test_forest_csv_includes_parsed_ci_and_pooled_row(self):
        csv_text = to_forest_csv(self.payload)
        self.assertIn("PARADIGM-HF (2014)", csv_text)
        self.assertIn("0.8", csv_text)
        self.assertIn("pooled", csv_text)
        self.assertIn("I2=0.0", csv_text)

    def test_pptx_writes_when_library_present(self):
        import tempfile
        from pathlib import Path

        try:
            import pptx  # noqa: F401
        except ImportError:
            self.skipTest("python-pptx not installed")
        with tempfile.TemporaryDirectory() as tmp:
            path = write_pptx(self.payload, Path(tmp) / "deck.pptx")
            self.assertIsNotNone(path)
            self.assertTrue(path.exists())
            self.assertGreater(path.stat().st_size, 2000)


if __name__ == "__main__":
    unittest.main()
