import json
import re

from director_api.app import _brief_from_mapping
from director_api.evidence import resolve_evidence
from director_api.extract import ExtractedBrief
from director_api.generate import generate_pack
from medicomarketing_agent.config import load_brief


def test_cardioshield_lead_is_cited_first_eligible_science():
    brief = _brief_from_mapping(load_brief("examples/brief.example.yaml"))
    ledger = resolve_evidence(brief, pubmed=False)
    pmids = {r["pmid"] for r in ledger["records"]}
    assert "25176015" in pmids  # PARADIGM-HF McMurray 2014 NEJM
    assert "30415601" in pmids  # PIONEER-HF
    assert "34447992" in pmids  # ESC 2021
    assert ledger["lead"]["directs"] == "first-eligible-start"
    assert "25176015" in " ".join(c["pmid"] or "" for c in ledger["lead"]["citations"]) or any(
        c["id"] == "paradigm-hf-2014" or c["id"] == "pioneer-hf-2019" for c in ledger["lead"]["citations"]
    )
    assert all(r.get("doi") and r.get("citation") for r in ledger["records"])
    assert "keynote-189-2018" not in {r["id"] for r in ledger["records"]}
    assert "keynote-024-2016" not in {r["id"] for r in ledger["records"]}
    assert any("local" in g["item"].lower() or "rwe" in g["item"].lower() or "indian" in g["item"].lower()
               for g in ledger["gaps"]) or ledger["gaps"]


def test_pack_exposes_science_slides_and_anchors():
    brief = _brief_from_mapping(load_brief("examples/brief.example.yaml"))
    pack = generate_pack(brief, mode="demo", pubmed=False)
    ids = [s["id"] for s in pack["slides"]]
    assert "literature-review" in ids
    assert "science-lead" in ids
    assert "citation-register" in ids
    assert "science-meaning" in ids
    assert "science-compare" in ids
    assert "science-execute" in ids
    assert "forest" in ids
    assert "house" in ids
    assert "journey" in ids
    assert "how-built" not in ids
    assert "questions" not in ids
    assert "references" in ids
    assert pack["workfile"]["phases"][0]["id"] == "01"
    assert len(pack["workfile"]["phases"]) == 11
    assert pack["references"][0]["n"] == 1
    assert pack["references"][0]["pmid"] == "25176015"
    assert "PMID: 25176015" in pack["references"][0]["citation"]
    meaning = next(s for s in pack["slides"] if s["id"] == "science-meaning")
    assert "[1]" in meaning["subtitle"] or "[1]" in meaning["narrative"]
    register = next(s for s in pack["slides"] if s["id"] == "citation-register")
    assert register["table"]["rows"][0][0] == "[1]"
    refs_slide = next(s for s in pack["slides"] if s["id"] == "references")
    assert refs_slide["layout"] == "references"
    assert "McMurray" in refs_slide["table"]["rows"][0][1]
    assert pack["doctrine"]["scienceAnchor"]
    assert "PMID" in pack["doctrine"]["scienceAnchor"]
    forefront = " ".join(str(c) for row in register["table"]["rows"] for c in row)
    assert "[1]" in forefront
    house = next(s for s in pack["slides"] if s["id"] == "house")
    house_text = " ".join(str(r) for r in (house.get("chart") or {}).get("data") or [])
    house_text += str(house.get("table") or "") + (house.get("narrative") or "")
    assert "[1]" in house_text or "[2]" in house_text or "PMID" in house_text
    forest = next(s for s in pack["slides"] if s["id"] == "forest")
    names = [row["name"] for row in forest["chart"]["data"]]
    assert any("PARADIGM-HF" in n for n in names)
    assert any("PIONEER-HF" in n for n in names)


def test_people_infographic_uses_published_paradigm_rates():
    brief = _brief_from_mapping(load_brief("examples/brief.example.yaml"))
    pack = generate_pack(brief, mode="demo", pubmed=False)
    meaning = next(s for s in pack["slides"] if s["id"] == "science-meaning")
    assert meaning["layout"] == "infographic"
    assert meaning["chart"]["kind"] == "people"
    row = meaning["chart"]["data"][0]
    assert row["pmid"] == "25176015"
    assert row["nnt"] == 21
    assert row["control"] == 26.5
    assert row["treat"] == 21.8
    assert pack["dashboard"]["meaning"][0]["nnt"] == 21


def test_spine_connects_pioneer_to_first_touch():
    brief = _brief_from_mapping(load_brief("examples/brief.example.yaml"))
    pack = generate_pack(brief, mode="demo", pubmed=False)
    execute = next(s for s in pack["slides"] if s["id"] == "science-execute")
    assert execute["chart"]["kind"] == "spine"
    names = " ".join(str(r.get("name")) for r in execute["chart"]["data"])
    moves = " ".join(f"{r.get('move')} {r.get('execute')}" for r in execute["chart"]["data"])
    assert "PIONEER-HF" in names
    assert "First-Touch" in moves
    paradigm = next(r for r in execute["chart"]["data"] if "PARADIGM" in str(r.get("name")))
    pioneer = next(r for r in execute["chart"]["data"] if "PIONEER" in str(r.get("name")))
    assert "First-Touch" in str(paradigm.get("move"))
    assert "First-Touch" in str(pioneer.get("move"))
    assert any("30415601" in str(r.get("pmid")) for r in execute["chart"]["data"])
    compare = next(s for s in pack["slides"] if s["id"] == "science-compare")
    assert compare["chart"]["kind"] == "compare"
    assert compare["chart"]["data"][0]["pmid"] == "30415601"
    iv = next(s for s in pack["slides"] if s["id"] == "interventions")
    assert any("[" in b and "PMID" in b for b in iv["bullets"])


def test_oncology_brief_without_named_molecule_does_not_borrow_keynote():
    brief = ExtractedBrief(
        brand="HelixOne",
        therapy_area="Oncology - NSCLC",
        indication="first-line NSCLC",
        business_goal="Grow first-line share. Cost of IO combo is the main barrier.",
    )
    ledger = resolve_evidence(brief, pubmed=False)
    assert ledger["records"] == []
    assert ledger["lead"]["citations"] == []
    pack = generate_pack(brief, pubmed=False)
    blob = json.dumps(pack).lower()
    assert "keynote" not in blob
    assert "pembrolizumab" not in blob
    assert "keytruda" not in blob
    assert "paradigm-hf" not in blob
    assert "sacubitril" not in blob
    assert "29658856" not in blob
    ids = [s["id"] for s in pack["slides"]]
    assert "science-meaning" not in ids
    assert "forest" not in ids


def test_named_keynote_attaches_only_that_oncology_row():
    brief = ExtractedBrief(
        brand="HelixOne",
        product="pembrolizumab",
        therapy_area="Oncology - NSCLC",
        indication="first-line NSCLC",
        existing_evidence=["KEYNOTE-189 pembrolizumab plus chemotherapy"],
        business_goal="Grow first-line share. Cost of IO combo is the main barrier.",
    )
    ledger = resolve_evidence(brief, pubmed=False)
    ids = {r["id"] for r in ledger["records"]}
    assert "keynote-189-2018" in ids
    assert "paradigm-hf-2014" not in ids
    assert "pioneer-hf-2019" not in ids
    pack = generate_pack(brief, pubmed=False)
    meaning = next(s for s in pack["slides"] if s["id"] == "science-meaning")
    assert meaning["chart"]["data"][0]["pmid"] == "29658856"
    blob = json.dumps(pack).lower()
    assert "paradigm-hf" not in blob
    assert "sacubitril" not in blob


def test_unrelated_hf_molecule_does_not_borrow_paradigm():
    brief = ExtractedBrief(
        brand="Lumenol",
        product="lumenolol",
        therapy_area="Cardiology - HFrEF",
        indication="HFrEF, NYHA II–IV",
        market="India",
        business_goal="Grow early initiation in HFrEF",
        hcp_insights=["Most agree in principle but start late"],
        access_and_cost=["Out-of-pocket cost is high"],
    )
    ledger = resolve_evidence(brief, pubmed=False)
    ids = {r["id"] for r in ledger["records"]}
    assert ids == set()
    pack = generate_pack(brief, pubmed=False)
    blob = json.dumps(pack).lower()
    assert "paradigm-hf" not in blob
    assert "pioneer-hf" not in blob
    assert "sacubitril" not in blob
    assert "pembrolizumab" not in blob
    assert "keynote" not in blob
    assert "25176015" not in blob
    assert pack["evidence"]["records"] == []


def test_respiratory_without_catalog_does_not_invent_trials():
    brief = ExtractedBrief(
        brand="Aero",
        therapy_area="Respiratory",
        access_and_cost=["High out-of-pocket cost is the only stated barrier"],
        business_goal="Grow reimbursed volume",
    )
    pack = generate_pack(brief, pubmed=False)
    assert pack["doctrine"]["id"] == "affordability-confidence"
    assert pack["evidence"]["records"] == []
    assert "do not lock" in pack["evidence"]["lead"]["statement"].lower()


def test_pubmed_does_not_search_another_molecule_from_therapy_area():
    from director_api.evidence import _pubmed_hit_belongs, _pubmed_term, _pubmed_terms

    nsclc = ExtractedBrief(
        brand="HelixOne",
        therapy_area="Oncology - NSCLC",
        indication="first-line NSCLC",
    )
    terms = " ".join(_pubmed_terms(nsclc)).lower()
    assert terms
    core = re.sub(r"not\s+[a-z0-9\-]+(?:\[ti\])?", " ", terms)
    # Query the indication, not a substitute catalog drug.
    assert "pembrolizumab" not in core
    assert "keynote" not in core
    assert "sacubitril" not in core
    assert "nsclc" in terms or "lung" in terms
    assert "randomized" in terms or "guideline" in terms
    # Brand-only: same-family landmarks belong as independent landscape.
    assert "not pembrolizumab" not in terms
    assert "not sacubitril" in terms
    assert _pubmed_hit_belongs(nsclc, "Pembrolizumab plus chemotherapy in metastatic NSCLC") is True
    assert _pubmed_hit_belongs(nsclc, "NCCN guidelines for non-small cell lung cancer") is True
    assert _pubmed_hit_belongs(nsclc, "Sacubitril/valsartan in heart failure") is False

    named = ExtractedBrief(
        brand="HelixOne",
        product="pembrolizumab",
        therapy_area="Oncology - NSCLC",
        indication="first-line NSCLC",
    )
    named_term = _pubmed_term(named).lower()
    assert "pembrolizumab" in named_term
    assert "sacubitril" not in named_term
    assert _pubmed_hit_belongs(named, "Pembrolizumab plus chemotherapy in metastatic NSCLC") is True
    assert _pubmed_hit_belongs(named, "Sacubitril/valsartan in heart failure") is False

    hf = ExtractedBrief(
        brand="Lumenol",
        product="lumenolol",
        therapy_area="Cardiology - HFrEF",
        indication="HFrEF",
    )
    hf_terms = " ".join(_pubmed_terms(hf)).lower()
    hf_core = re.sub(r"not\s+[a-z0-9\-]+(?:\[ti\])?", " ", hf_terms)
    assert "sacubitril" not in hf_core
    assert "pembrolizumab" not in hf_core
    assert _pubmed_hit_belongs(hf, "Angiotensin–neprilysin inhibition versus enalapril in heart failure") is False
    assert _pubmed_hit_belongs(hf, "Hospital admissions among patients with reduced ejection fraction") is True
    assert _pubmed_hit_belongs(
        hf,
        "2021 ESC Guidelines for the diagnosis and treatment of acute and chronic heart failure",
        "Sacubitril/valsartan is Class I in HFrEF",
    ) is True


def test_pubmed_review_builds_strategy_without_brief_bibliography(monkeypatch):
    from director_api import evidence as ev

    def fake_esearch(term, retmax=4):
        return ["11111111", "22222222", "33333333"]

    def fake_esummary(pmids):
        return {
            "11111111": {
                "title": "Early initiation of systemic therapy in advanced non-small cell lung cancer",
                "fulljournalname": "J Clin Oncol",
                "pubdate": "2023",
                "authors": [{"name": "Smith A"}],
                "articleids": [{"idtype": "doi", "value": "10.1000/fake.nsclc"}],
                "pubtype": ["Journal Article"],
            },
            "22222222": {
                "title": "NCCN guidelines for non-small cell lung cancer",
                "fulljournalname": "J Natl Compr Canc Netw",
                "pubdate": "2024",
                "authors": [{"name": "Ettinger DS"}],
                "articleids": [],
                "pubtype": ["Practice Guideline"],
            },
            "33333333": {
                "title": "Pembrolizumab plus chemotherapy in metastatic non-small cell lung cancer",
                "fulljournalname": "N Engl J Med",
                "pubdate": "2018",
                "authors": [{"name": "Gandhi L"}],
                "articleids": [{"idtype": "doi", "value": "10.1000/fake.keynote"}],
                "pubtype": ["Randomized Controlled Trial"],
            },
        }

    def fake_abstracts(pmids):
        return {
            "11111111": (
                "Delayed first-line therapy is associated with worse survival. "
                "Immediate initiation after diagnosis improved outcomes versus a clinic wait."
            ),
            "22222222": (
                "Guidelines recommend first-line systemic therapy for eligible patients "
                "with metastatic NSCLC rather than delayed start."
            ),
            "33333333": (
                "Pembrolizumab plus chemotherapy improved overall survival versus chemotherapy "
                "alone in metastatic nonsquamous NSCLC. HR 0.49 (95% CI 0.38-0.64)."
            ),
        }

    monkeypatch.setattr(ev, "_esearch", fake_esearch)
    monkeypatch.setattr(ev, "_esummary", fake_esummary)
    monkeypatch.setattr(ev, "_efetch_abstracts", fake_abstracts)

    brief = ExtractedBrief(
        brand="HelixOne",
        therapy_area="Oncology - NSCLC",
        indication="first-line NSCLC",
        business_goal="Grow first-line share. Cost of IO combo is the main barrier.",
        hcp_insights=["Oncologists wait for molecular results then delay start"],
        access_and_cost=["Out-of-pocket cost of IO combo is high"],
    )
    pack = generate_pack(brief, pubmed=True)
    records = pack["evidence"]["records"]
    assert records
    pmids = {r["pmid"] for r in records}
    assert {"11111111", "22222222", "33333333"} <= pmids
    lead = pack["evidence"]["lead"]["statement"].lower()
    assert "do not lock" not in lead
    assert "literature review" in lead
    assert "11111111" in lead or "early initiation" in lead
    blob = json.dumps(pack)
    ids = {r["id"] for r in records}
    assert "pubmed-11111111" in ids
    assert "pubmed-33333333" in ids
    assert "keynote-189-2018" not in ids
    assert "paradigm-hf-2014" not in ids
    assert "29658856" not in blob
    assert "25176015" not in blob
    landscape = next(r for r in records if r["pmid"] == "33333333")
    assert landscape["independence"] == "indication-landscape"
    assert "not a trial of helixone" in (landscape.get("claim_permitted") or "").lower()
    assert pack["doctrine"]["id"] == "first-touch"
    problem = next(s for s in pack["slides"] if s["id"] == "problem")
    assert "grow first-line share" not in (problem.get("narrative") or "").lower()
    assert any(s["id"] == "literature-review" for s in pack["slides"])
    built = pack["workfile"]["howBuilt"].lower()
    assert "literature review" in built
    assert pack["evidence"]["review"]["paperCount"] == 3
    assert "nccn" in json.dumps(pack["evidence"]["review"]["findings"]).lower()


def test_trivora_pubmed_queries_are_short_copd_not_the_whole_brief():
    from pathlib import Path

    from director_api.evidence import _pubmed_hit_belongs, _pubmed_terms
    from director_api.extract import merge_into_brief

    raw = (Path(__file__).resolve().parent / "fixtures" / "trivora_client_brief.txt").read_text(
        encoding="utf-8"
    )
    brief = merge_into_brief([], pasted=raw)
    terms = _pubmed_terms(brief)
    joined = " ".join(terms).lower()
    assert terms
    assert all(len(t) < 180 for t in terms)
    assert "cardiovascular risk" not in joined
    assert "stated population" not in joined
    assert "breath 6-month" not in joined
    assert "glycopyrronium" in joined
    assert "copd" in joined
    assert "gold" in joined
    assert "triple" in joined
    assert _pubmed_hit_belongs(
        brief,
        "Budesonide/glycopyrronium/formoterol for COPD vs dual therapy",
    )
    assert _pubmed_hit_belongs(
        brief,
        "Global strategy for the diagnosis, management and prevention of COPD GOLD",
    )
    assert not _pubmed_hit_belongs(
        brief,
        "Tongxinluo capsule in patients with ST-segment elevation myocardial infarction",
    )
    assert not _pubmed_hit_belongs(brief, "Sacubitril/valsartan in heart failure")
