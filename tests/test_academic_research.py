"""Unit tests for extraction, screening, frequency, and IPA coding.

These tests use fixture abstracts from real, well-known publications. They do
not hit the network. Live API behaviour is exercised by the demo pipeline run.
"""

from __future__ import annotations

import unittest

from academic_research.analyze import quantitative
from academic_research.extract import (
    code_claims,
    ipa_hits,
    is_qualitative,
    on_topic,
    parse_effects,
)
from academic_research.models import EvidenceRecord, Validation
from academic_research.queries import build_queries, pico
from academic_research.validate import normalize_doi


PARADIGM_ABSTRACT = (
    "We compared the angiotensin receptor-neprilysin inhibitor LCZ696 with "
    "enalapril in patients who had heart failure with reduced ejection fraction. "
    "In this double-blind trial, the primary outcome was a composite of death "
    "from cardiovascular causes or hospitalization for heart failure. LCZ696 "
    "was superior to enalapril in reducing the risks of death and of "
    "hospitalization for heart failure. The hazard ratio was 0.80 (95% CI, "
    "0.73 to 0.87; P<0.001)."
)

QUAL_ABSTRACT = (
    "This qualitative study explored the lived experience of people with "
    "chronic heart failure using semi-structured interviews. Participants "
    "described overwhelming fatigue, fear about the future, loss of identity, "
    "and reliance on family caregivers. Cost of medicines constrained "
    "self-management and left people uncertain about what they could afford."
)


def rec(**kwargs) -> EvidenceRecord:
    base = dict(
        key="x",
        title="Heart failure lived experience",
        url="https://doi.org/10.example/x",
        source_connector="test",
        source_family="open_access",
        issuing_body="Test",
        abstract="",
        validation=Validation(
            status="verified",
            via="crossref",
            identifier="10.example/x",
            retrieved_at="2026-08-24T00:00:00Z",
            canonical_url="https://doi.org/10.example/x",
        ),
    )
    base.update(kwargs)
    return EvidenceRecord(**base)


class ExtractTests(unittest.TestCase):
    def test_parses_hazard_ratio_with_ci(self):
        effects = parse_effects(PARADIGM_ABSTRACT, "PARADIGM-HF")
        self.assertTrue(effects)
        hr = effects[0]
        self.assertEqual(hr.metric, "HR")
        self.assertEqual(hr.value, 0.80)
        self.assertEqual(hr.ci_low, 0.73)
        self.assertEqual(hr.ci_high, 0.87)
        self.assertIn("0.80", hr.excerpt)

    def test_rejects_implausible_effect_sizes(self):
        text = "The hazard ratio was 42.0 (95% CI, 30 to 50)"
        self.assertEqual(parse_effects(text), [])

    def test_claim_coding_requires_benefit_cooccurrence(self):
        r = rec(title="ARNI in HFrEF", abstract=PARADIGM_ABSTRACT)
        claims = code_claims(r)
        self.assertIn("mortality_or_hospitalisation_benefit", claims)

    def test_off_topic_covid_paper_is_excluded(self):
        covid = rec(
            title="Clinical course of COVID-19 in Wuhan",
            abstract="Adult inpatients with COVID-19 and risk factors for mortality.",
        )
        self.assertFalse(
            on_topic(covid, ["hfref", "sacubitril", "heart failure"], min_hits=1)
        )

    def test_on_topic_hf_paper(self):
        r = rec(title="Sacubitril/valsartan in HFrEF", abstract=PARADIGM_ABSTRACT)
        self.assertTrue(on_topic(r, ["hfref", "heart failure", "sacubitril"], min_hits=1))

    def test_qualitative_detection(self):
        r = rec(abstract=QUAL_ABSTRACT)
        self.assertTrue(is_qualitative(r))
        themes = ipa_hits(QUAL_ABSTRACT)
        self.assertIn("corporeal_disruption", themes)
        self.assertIn("existential_uncertainty", themes)
        self.assertIn("constrained_agency", themes)
        self.assertIn("biographical_disruption", themes)
        self.assertIn("relational_care", themes)

    def test_doi_normalize(self):
        self.assertEqual(
            normalize_doi("https://doi.org/10.1056/NEJMoa1409077"),
            "10.1056/nejmoa1409077",
        )


class AnalyzeTests(unittest.TestCase):
    def test_frequency_uses_unique_citation_ids(self):
        a = rec(title="A", abstract=PARADIGM_ABSTRACT, citation_id=1)
        a.claims = ["mortality_or_hospitalisation_benefit", "cost_or_access_barrier"]
        b = rec(title="B", abstract=PARADIGM_ABSTRACT, citation_id=2)
        b.claims = ["mortality_or_hospitalisation_benefit"]
        quant = quantitative([a, b])
        freq = {c["id"]: c for c in quant["claim_frequency"]}
        self.assertEqual(freq["mortality_or_hospitalisation_benefit"]["count"], 2)
        self.assertEqual(freq["mortality_or_hospitalisation_benefit"]["percent"], 100.0)
        self.assertEqual(freq["cost_or_access_barrier"]["count"], 1)
        self.assertEqual(freq["cost_or_access_barrier"]["percent"], 50.0)


class QueryTests(unittest.TestCase):
    def test_pico_and_queries_from_brief(self):
        brief = {
            "brand": "CardioShield",
            "therapy_area": "Cardiology - chronic heart failure",
            "indication": "HFrEF",
            "product": "sacubitril/valsartan",
            "market": "India",
        }
        p = pico(brief)
        self.assertIn("HFrEF", p["population"])
        self.assertIn("sacubitril", p["intervention"])
        qs = build_queries(brief)
        ids = {q["id"] for q in qs}
        self.assertIn("primary_evidence", ids)
        self.assertIn("qualitative", ids)
        self.assertIn("national", ids)
        qual = next(q for q in qs if q["id"] == "qualitative")
        self.assertIn("lived experience", qual["europe_pmc"])


if __name__ == "__main__":
    unittest.main()
