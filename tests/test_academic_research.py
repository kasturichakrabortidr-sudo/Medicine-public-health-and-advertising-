"""Unit tests for extraction, screening, frequency, and IPA coding.

These tests use fixture abstracts from real, well-known publications. They do
not hit the network. Live API behaviour is exercised by the demo pipeline run.
"""

from __future__ import annotations

import unittest

from academic_research.analyze import forest_rows, qualitative, quantitative
from academic_research.extract import (
    classify_study_design,
    code_claims,
    ipa_hits,
    is_qualitative,
    on_topic,
    parse_effects,
    pick_primary_effect,
    short_study_label,
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

    def test_forest_labels_use_trial_acronyms_not_full_titles(self):
        self.assertEqual(
            short_study_label(
                "Angiotensin-Neprilysin Inhibition versus Enalapril in Heart Failure",
                "10.1056/NEJMoa1409077",
                2014,
            ),
            "PARADIGM-HF (2014)",
        )
        self.assertEqual(
            short_study_label(
                "Dapagliflozin in Patients with Heart Failure and Reduced Ejection Fraction",
                "10.1056/NEJMoa1911303",
                2019,
            ),
            "DAPA-HF (2019)",
        )
        self.assertEqual(
            short_study_label(
                "Dapagliflozin in Heart Failure with Mildly Reduced or Preserved Ejection Fraction",
                "10.1056/NEJMoa2206286",
                2022,
            ),
            "DELIVER (2022)",
        )
        self.assertEqual(
            short_study_label(
                "Ivabradine and outcomes in chronic heart failure (SHIFT)",
                "10.1016/S0140-6736(10)61198-1",
                2010,
            ),
            "SHIFT (2010)",
        )
        self.assertEqual(
            short_study_label(
                "Sotagliflozin in Patients with Diabetes and Recent Worsening Heart Failure",
                "10.1056/NEJMoa2030183",
                2021,
            ),
            "SOLOIST-WHF (2021)",
        )
        self.assertEqual(
            short_study_label(
                "The SGLT2 inhibitor empagliflozin in patients hospitalized for acute heart failure",
                "10.1038/s41591-021-01659-1",
                2022,
            ),
            "EMPULSE (2022)",
        )
        self.assertEqual(
            short_study_label(
                "The Effect of Spironolactone on Morbidity and Mortality in Patients with Severe Heart Failure",
                "10.1056/NEJM199909023411001",
                1999,
            ),
            "RALES (1999)",
        )
        self.assertEqual(
            short_study_label(
                "Spironolactone for Heart Failure with Preserved Ejection Fraction",
                "10.1056/NEJMoa1313731",
                2014,
            ),
            "TOPCAT (2014)",
        )
        self.assertEqual(
            short_study_label(
                "Transcatheter Mitral-Valve Repair in Patients with Heart Failure",
                "10.1056/NEJMoa1806640",
                2018,
            ),
            "COAPT (2018)",
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

    def test_rct_design_and_grade_band(self):
        trial = rec(title="PARADIGM-HF randomised trial", abstract=PARADIGM_ABSTRACT, citation_id=1)
        trial.study_design = classify_study_design(trial)
        self.assertEqual(trial.study_design, "rct")
        quant = quantitative([trial])
        bands = {row["id"]: row for row in quant["grade_profile"]}
        self.assertEqual(bands["rct"]["band"], "High")
        self.assertTrue(quant["by_study_design"])
        self.assertIn("agency_coverage", quant)
        self.assertTrue(quant.get("geography") is not None)

    def test_geography_tags_india_and_un(self):
        india = rec(
            title="Five-year mortality of heart failure in the Trivandrum Heart Failure Registry",
            issuing_body="Indian Heart Journal",
            venue="Indian Heart Journal",
            citation_id=1,
        )
        who = rec(
            title="HEARTS technical package",
            issuing_body="World Health Organization",
            venue="WHO",
            citation_id=2,
        )
        wpro = rec(
            title="Cardiovascular diseases — WHO Western Pacific",
            issuing_body="WHO Western Pacific",
            venue="WHO WPRO",
            citation_id=3,
        )
        geo = {row["id"]: row["count"] for row in quantitative([india, who, wpro])["geography"]}
        self.assertEqual(geo.get("India"), 1)
        self.assertEqual(geo.get("Global / UN system"), 1)
        self.assertEqual(geo.get("Western Pacific"), 1)

    def test_connector_yield_parses_harvest_log(self):
        from academic_research.analyze import connector_yield

        rows = connector_yield(
            [
                {"step": "harvest", "detail": "12 raw records from live APIs"},
                {"step": "europe_pmc", "detail": "primary_evidence: 8 hits"},
                {"step": "semantic_scholar", "detail": "primary_evidence: FAILED HTTPError"},
            ]
        )
        by = {r["connector"]: r for r in rows}
        self.assertEqual(by["europe_pmc"]["hits"], 8)
        self.assertTrue(by["europe_pmc"]["ok"])
        self.assertFalse(by["semantic_scholar"]["ok"])
        self.assertNotIn("harvest", by)

    def test_forest_skips_unnamed_systematic_reviews(self):
        review = rec(
            title="Association between adiposity and cardiovascular outcomes: an umbrella review",
            abstract="The relative risk was 1.49 (95% CI, 1.40 to 1.60).",
            citation_id=9,
            doi="10.1093/eurheartj/ehab1234",
        )
        review.study_design = "systematic_review"
        review.effects = parse_effects(review.abstract, review.title)
        trial = rec(
            title="Angiotensin-Neprilysin Inhibition versus Enalapril in Heart Failure",
            abstract=PARADIGM_ABSTRACT,
            citation_id=1,
            doi="10.1056/nejmoa1409077",
            year=2014,
        )
        trial.study_design = "rct"
        trial.effects = parse_effects(PARADIGM_ABSTRACT, trial.title)
        rows = forest_rows([review, trial])
        self.assertEqual(len(rows), 1)
        self.assertIn("PARADIGM", rows[0]["label"])

    def test_forest_dedupes_same_trial_acronym(self):
        a = rec(
            title="Angiotensin-Neprilysin Inhibition versus Enalapril in Heart Failure",
            abstract=PARADIGM_ABSTRACT,
            citation_id=1,
            doi="10.1056/nejmoa1409077",
            year=2014,
        )
        a.effects = parse_effects(PARADIGM_ABSTRACT, a.title)
        b = rec(
            title="Angiotensin-Neprilysin Inhibition versus Enalapril in Heart Failure — secondary report",
            abstract=PARADIGM_ABSTRACT,
            citation_id=2,
            doi="10.1056/nejmoa1409077",
            year=2014,
        )
        b.effects = parse_effects(PARADIGM_ABSTRACT, b.title)
        rows = forest_rows([a, b])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["value"], 0.80)
        self.assertIn("PARADIGM", rows[0]["label"])
        a = rec(
            title="Angiotensin-Neprilysin Inhibition versus Enalapril in Heart Failure",
            abstract=PARADIGM_ABSTRACT,
            citation_id=1,
            doi="10.1056/nejmoa1409077",
            year=2014,
        )
        a.effects = parse_effects(PARADIGM_ABSTRACT, a.title)
        b = rec(
            title="Angiotensin-Neprilysin Inhibition versus Enalapril in Heart Failure — secondary report",
            abstract=PARADIGM_ABSTRACT,
            citation_id=2,
            doi="10.1056/nejmoa1409077",
            year=2014,
        )
        b.effects = parse_effects(PARADIGM_ABSTRACT, b.title)
        rows = forest_rows([a, b])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["value"], 0.80)
        self.assertIn("PARADIGM", rows[0]["label"])

    def test_pick_primary_prefers_composite(self):
        effects = parse_effects(
            "The primary outcome was a composite of death from cardiovascular "
            "causes or hospitalization for heart failure. The hazard ratio was "
            "0.80 (95% CI, 0.73 to 0.87). Died from cardiovascular causes "
            "(hazard ratio, 0.80; 95% CI, 0.71 to 0.89)."
        )
        primary = pick_primary_effect(effects)
        self.assertIsNotNone(primary)
        self.assertEqual(primary.value, 0.80)
        self.assertEqual(primary.ci_low, 0.73)

    def test_un_ngo_filter_does_not_match_who_in_patient_title(self):
        pipe = ResearchPipeline(
            {
                "brand": "CardioShield",
                "therapy_area": "Cardiology - chronic heart failure",
                "indication": "HFrEF",
            }
        )
        paper = rec(
            title="Who is on your health-care team? Asking individuals with heart failure",
            issuing_body="Health Expectations",
            venue="Health Expectations",
            source_family="open_access",
        )
        who = rec(
            title="HEARTS technical package for cardiovascular disease management in primary health care",
            issuing_body="World Health Organization",
            venue="WHO",
            source_family="international_guideline",
        )
        self.assertFalse(pipe._is_un_or_ngo(paper))
        self.assertTrue(pipe._is_un_or_ngo(who))


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
        self.assertIn("systematic_reviews", ids)
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
        self.assertIn("10.1056/NEJMoa1915928", hf_seeds)
        self.assertIn("10.1056/NEJMoa2025797", hf_seeds)
        self.assertIn("10.1056/NEJMoa2206286", hf_seeds)
        self.assertIn("10.1056/NEJMoa1908655", hf_seeds)
        self.assertIn("10.1002/ejhf.283", hf_seeds)
        self.assertIn("10.1111/jocn.13615", hf_seeds)
        self.assertIn("10.1016/j.ihj.2017.11.015", hf_seeds)
        self.assertIn("10.1016/S0140-6736(10)61198-1", hf_seeds)
        self.assertIn("10.1056/NEJMoa1009492", hf_seeds)
        self.assertIn("10.1056/NEJMoa2407107", hf_seeds)
        self.assertIn("10.1016/S0140-6736(20)32339-4", hf_seeds)
        self.assertIn("10.1056/NEJMoa2030183", hf_seeds)
        self.assertIn("10.1056/NEJMoa2306963", hf_seeds)
        self.assertIn("10.1038/s41591-021-01659-1", hf_seeds)
        self.assertIn("10.1016/S0140-6736(22)02083-9", hf_seeds)
        self.assertIn("10.1056/NEJMoa2304968", hf_seeds)
        self.assertIn("10.1056/NEJMoa2410027", hf_seeds)
        self.assertIn("10.1056/NEJM199909023411001", hf_seeds)
        self.assertIn("10.1016/S0140-6736(03)14282-1", hf_seeds)
        self.assertIn("10.1016/S0140-6736(03)14283-3", hf_seeds)
        self.assertIn("10.1056/NEJMoa1313731", hf_seeds)
        self.assertIn("10.1056/NEJMoa2104508", hf_seeds)
        self.assertIn("10.1056/NEJMoa1806640", hf_seeds)
        self.assertIn("10.1056/NEJMoa2203094", hf_seeds)
        self.assertIn("10.1016/S0140-6736(11)60101-3", hf_seeds)
        self.assertIn("10.1177/1474515117707666", hf_seeds)

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
        self.assertTrue(_allowlisted("https://www.paho.org/en/hearts-americas"))
        self.assertTrue(
            _allowlisted("https://world-heart-federation.org/what-we-do/heart-failure/")
        )
        self.assertTrue(
            _allowlisted(
                "https://www.who.int/news-room/fact-sheets/detail/noncommunicable-diseases"
            )
        )
        self.assertTrue(
            _allowlisted(
                "https://www.worldbank.org/en/topic/health/brief/noncommunicable-diseases"
            )
        )
        self.assertTrue(_allowlisted("https://iris.who.int/handle/10665/333221"))
        self.assertTrue(
            _allowlisted(
                "https://www.who.int/southeastasia/health-topics/cardiovascular-diseases"
            )
        )
        self.assertTrue(
            _allowlisted("https://www.afro.who.int/health-topics/cardiovascular-diseases")
        )
        self.assertTrue(_allowlisted("https://sdgs.un.org/goals/goal3"))
        self.assertTrue(_allowlisted("https://nhm.gov.in/"))
        self.assertTrue(_allowlisted("https://www.mohfw.gov.in/"))
        self.assertTrue(_allowlisted("https://www.icmr.gov.in/"))
        self.assertTrue(_allowlisted("https://www.unaids.org/en"))
        self.assertTrue(_allowlisted("https://www.fao.org/nutrition/en"))
        self.assertTrue(_allowlisted("https://unhabitat.org/"))
        self.assertTrue(_allowlisted("https://www.un.org/sustainabledevelopment/health/"))
        self.assertTrue(_allowlisted("https://www.emro.who.int/noncommunicable-diseases/index.html"))
        self.assertTrue(_allowlisted("https://kdigo.org/guidelines/"))
        self.assertTrue(_allowlisted("https://www.unfpa.org/"))
        self.assertTrue(_allowlisted("https://www.unwomen.org/en"))
        from academic_research.connectors import official_seeds_for_brief

        seeds = official_seeds_for_brief(
            {
                "therapy_area": "Cardiology - chronic heart failure",
                "indication": "HFrEF",
                "market": "India",
            }
        )
        urls = {s.url for s in seeds}
        self.assertIn("https://sdgs.un.org/goals/goal3", urls)
        self.assertIn(
            "https://www.who.int/southeastasia/health-topics/cardiovascular-diseases",
            urls,
        )
        self.assertIn("https://nhm.gov.in/", urls)
        self.assertIn("https://www.icmr.gov.in/", urls)
        self.assertIn("https://www.unaids.org/en", urls)
        self.assertIn("https://www.un.org/sustainabledevelopment/health/", urls)
        self.assertIn("https://www.unfpa.org/", urls)
        self.assertIn("https://www.unwomen.org/en", urls)
        self.assertIn("https://www.emro.who.int/noncommunicable-diseases/index.html", urls)
        self.assertIn(
            "https://www.who.int/westernpacific/health-topics/cardiovascular-diseases",
            urls,
        )
        self.assertIn("https://kdigo.org/guidelines/", urls)
        self.assertIn("https://www.acc.org/Guidelines", urls)
        self.assertGreaterEqual(len(seeds), 36)
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
