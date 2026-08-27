"""Unit tests for extraction, screening, frequency, and IPA coding.

These tests use fixture abstracts from real, well-known publications. They do
not hit the network. Live API behaviour is exercised by the demo pipeline run.
"""

from __future__ import annotations

import unittest

from academic_research.analyze import qualitative, quantitative
from academic_research.extract import (
    code_claims,
    ipa_hits,
    is_qualitative,
    on_topic,
    parse_effects,
)
from academic_research.models import EvidenceRecord, Validation
from academic_research.pipeline import ResearchPipeline
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

    def test_parses_confidence_interval_bracket_form(self):
        text = (
            "the primary outcome had occurred in the LCZ696 group "
            "(hazard ratio in the LCZ696 group, 0.80; 95% confidence interval [CI], "
            "0.73 to 0.87; P<0.001)."
        )
        effects = parse_effects(text)
        self.assertTrue(effects)
        self.assertEqual(effects[0].value, 0.80)
        self.assertEqual(effects[0].ci_low, 0.73)
        self.assertEqual(effects[0].ci_high, 0.87)
        text = (
            "died from cardiovascular causes (hazard ratio, 0.80; 95% CI, 0.71 to 0.89; "
            "P<0.001)."
        )
        effects = parse_effects(text)
        self.assertTrue(effects)
        self.assertEqual(effects[0].value, 0.80)
        self.assertEqual(effects[0].ci_low, 0.71)
        self.assertEqual(effects[0].ci_high, 0.89)

    def test_alzheimer_not_on_topic_for_hf_brief(self):
        r = rec(
            title="NIA-AA Research Framework: Toward a biological definition of Alzheimer's disease",
            abstract="Alzheimer's disease diagnostic recommendations and dementia stages.",
        )
        self.assertFalse(on_topic(r, ["heart failure", "hfref", "sacubitril"], min_hits=1))

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
    def test_ipa_does_not_mine_trial_abstracts(self):
        trial = rec(title="PARADIGM-HF", abstract=PARADIGM_ABSTRACT, citation_id=1)
        trial.is_qualitative = is_qualitative(trial)
        self.assertFalse(trial.is_qualitative)
        q = qualitative([trial], "HFrEF")
        self.assertEqual(q["n_qualitative_papers"], 0)
        self.assertEqual(q["ipa"]["superordinate_themes"], [])

    def test_ipa_uses_qualitative_papers(self):
        paper = rec(title="Lived experience of chronic heart failure", abstract=QUAL_ABSTRACT, citation_id=3)
        paper.is_qualitative = is_qualitative(paper)
        self.assertTrue(paper.is_qualitative)
        q = qualitative([paper], "HFrEF")
        ids = {t["id"] for t in q["ipa"]["superordinate_themes"]}
        self.assertGreaterEqual(len(ids), 4)
        self.assertIn("corporeal_disruption", ids)
        self.assertIn("constrained_agency", ids)

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
        self.assertIn('TITLE:"heart failure"', qual["europe_pmc"])
        self.assertNotIn("NYHA", qual["europe_pmc"])


class ScreeningTests(unittest.TestCase):
    def test_who_keep_uses_brief_terms_not_hardcoded_hf(self):
        pipe = ResearchPipeline(
            {
                "brand": "X",
                "therapy_area": "Diabetes",
                "indication": "type 2 diabetes",
                "product": "SGLT2",
            }
        )
        keep = rec(
            title="WHO package of essential noncommunicable disease interventions for diabetes care",
            source_connector="who_iris",
            source_family="un_agency",
        )
        drop = rec(
            title="Abstracts",
            source_connector="who_iris",
            source_family="un_agency",
        )
        self.assertTrue(pipe._keep_record(keep))
        self.assertFalse(pipe._keep_record(drop))

    def test_doi_seeds_skip_placeholder_topic_filter(self):
        pipe = ResearchPipeline(
            {
                "brand": "CardioShield",
                "therapy_area": "Cardiology - chronic heart failure",
                "indication": "HFrEF",
            }
        )
        seed = rec(
            title="DOI seed 10.1056/nejmoa1409077",
            abstract="",
            source_connector="doi_seed",
            doi="10.1056/nejmoa1409077",
        )
        self.assertFalse(on_topic(seed, pipe.terms, min_hits=1))
        self.assertEqual(seed.source_connector, "doi_seed")
        from academic_research.connectors import records_from_dois

        rows = records_from_dois(["https://doi.org/10.1056/NEJMoa1409077"])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].doi, "10.1056/nejmoa1409077")
        self.assertTrue(rows[0].title.startswith("DOI seed"))
        from academic_research.connectors import ANCHOR_DOI_SEEDS

        hf_seeds = ANCHOR_DOI_SEEDS["heart failure"]
        self.assertIn("10.1056/NEJMoa1911303", hf_seeds)
        self.assertIn("10.1056/NEJMoa2022190", hf_seeds)
        self.assertIn("10.1002/ejhf.283", hf_seeds)

    def test_official_url_seeds_are_allowlisted_and_skip_screen(self):
        from academic_research.validate import _allowlisted

        self.assertTrue(
            _allowlisted("https://www.who.int/publications/i/item/hearts-technical-package")
        )
        self.assertTrue(
            _allowlisted(
                "https://www.escardio.org/Guidelines/Clinical-Practice-Guidelines/Acute-and-Chronic-Heart-Failure"
            )
        )
        self.assertTrue(_allowlisted("https://www.nice.org.uk/guidance/ng106"))
        seed = rec(
            title="DOI seed placeholder until Crossref runs",
            source_connector="official_url_seed",
            source_family="un_agency",
        )
        self.assertFalse(
            on_topic(seed, ["heart failure", "hfref", "sacubitril"], min_hits=1)
        )


if __name__ == "__main__":
    unittest.main()
