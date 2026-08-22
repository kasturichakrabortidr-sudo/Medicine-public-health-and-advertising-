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
    assert "science-lead" in ids
    assert "citation-register" in ids
    assert "science-meaning" in ids
    assert "science-compare" in ids
    assert "science-execute" in ids
    assert "how-built" in ids
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
    forest = next(s for s in pack["slides"] if s["id"] == "forest")
    names = [row["name"] for row in forest["chart"]["data"]]
    assert any("PARADIGM-HF" in n for n in names)
    assert any("PIONEER-HF" in n for n in names)
    assert pack["doctrine"]["scienceAnchor"]
    assert "PMID" in pack["doctrine"]["scienceAnchor"]
    house = next(s for s in pack["slides"] if s["id"] == "house")
    house_text = " ".join(house.get("bullets") or []) + str(house.get("table") or "")
    assert "[1]" in house_text or "[2]" in house_text or "PMID" in house_text
    assert pack["interventions"][0]["evidenceAnchor"]


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


def test_oncology_brief_matches_keynote_not_hf():
    brief = ExtractedBrief(
        brand="HelixOne",
        therapy_area="Oncology - NSCLC",
        indication="first-line NSCLC",
        business_goal="Grow first-line share. Cost of IO combo is the main barrier.",
    )
    ledger = resolve_evidence(brief, pubmed=False)
    ids = {r["id"] for r in ledger["records"]}
    assert "keynote-189-2018" in ids
    assert "paradigm-hf-2014" not in ids
    assert ledger["lead"]["citations"][0]["pmid"] == "29658856"
    pack = generate_pack(brief, pubmed=False)
    meaning = next(s for s in pack["slides"] if s["id"] == "science-meaning")
    assert meaning["chart"]["data"][0]["pmid"] == "29658856"
    assert meaning["chart"]["data"][0]["nnt"] == 5


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
    assert pack["meta"]["brand"] == "Aero"
    assert pack["meta"]["demo"] is False
    assert "CardioShield" not in pack["slides"][0]["title"]
    assert pack["interventions"][0]["id"] == "afford-kit"


def test_unrelated_india_brief_does_not_get_cardioshield_science():
    brief = ExtractedBrief(
        brand="LumenDerm",
        therapy_area="Dermatology - psoriasis",
        market="India",
        business_goal="Grow related clinic starts among related specialists.",
        hcp_insights=["Doctors want a template they can use in clinic."],
    )
    pack = generate_pack(brief, pubmed=False)
    ids = {r["id"] for r in pack["evidence"]["records"]}
    assert "paradigm-hf-2014" not in ids
    assert "pioneer-hf-2019" not in ids
    assert "trivandrum-hf-2015" not in ids
    assert pack["meta"]["brand"] == "LumenDerm"
    assert pack["doctrine"]["id"] != "first-touch"
    assert "CardioShield" not in str(pack["doctrine"])
    assert pack["interventions"][0]["name"] != "First-Touch Protocol"


def test_hf_sglt2_brief_does_not_attach_arni_trials():
    brief = ExtractedBrief(
        brand="GlucoHeart",
        product="dapagliflozin",
        therapy_area="Cardiology - chronic heart failure",
        indication="HFrEF",
        market="India",
        business_goal="Grow SGLT2 foundational use.",
    )
    ledger = resolve_evidence(brief, pubmed=False)
    ids = {r["id"] for r in ledger["records"]}
    assert "paradigm-hf-2014" not in ids
    assert "pioneer-hf-2019" not in ids
    assert "keynote-189-2018" not in ids


def test_product_without_trial_names_still_gets_catalog():
    brief = ExtractedBrief(
        brand="HelixOne",
        product="sacubitril",
        therapy_area="Cardiology — HFrEF",
        market="India",
        business_goal="Grow ARNI initiation in metro clinics",
        hcp_insights=["Cost is the veto at the desk"],
    )
    ledger = resolve_evidence(brief, pubmed=False)
    ids = {r["id"] for r in ledger["records"]}
    assert "paradigm-hf-2014" in ids
    assert ledger["lead"]["citations"][0]["pmid"]


def test_brief_without_paper_links_gets_pubmed_records(monkeypatch):
    def fake_search(term, retmax=8):
        assert "lumetinib" in term.lower() or "psoriasis" in term.lower() or "dermatology" in term.lower()
        return ["39001111"]

    def fake_summary(pmids):
        return {
            "39001111": {
                "title": "Lumetinib in moderate-to-severe plaque psoriasis: a randomized trial",
                "fulljournalname": "N Engl J Med",
                "pubdate": "2024 Jan",
                "authors": [{"name": "Chen L"}, {"name": "Rao P"}, {"name": "Singh A"}, {"name": "Other"}],
                "articleids": [{"idtype": "doi", "value": "10.1056/NEJMoa9999999"}],
                "pubtype": ["Randomized Controlled Trial"],
            }
        }

    monkeypatch.setattr("director_api.evidence._esearch", fake_search)
    monkeypatch.setattr("director_api.evidence._esummary", fake_summary)
    brief = ExtractedBrief(
        brand="LumenDerm",
        product="lumetinib",
        therapy_area="Dermatology",
        indication="plaque psoriasis",
        market="India",
        business_goal="Grow first-line share among metro dermatologists",
    )
    ledger = resolve_evidence(brief, pubmed=True)
    pmids = {r["pmid"] for r in ledger["records"]}
    assert "39001111" in pmids
    assert "paradigm-hf-2014" not in {r["id"] for r in ledger["records"]}
    assert ledger["lead"]["citations"]
    assert ledger["lead"]["citations"][0]["pmid"] == "39001111"
    assert "paper links" in ledger["lead"]["statement"].lower()
    pack = generate_pack(brief, pubmed=True)
    assert pack["references"][0]["pmid"] == "39001111"
    assert pack["references"][0]["url"].endswith("39001111/")
    assert pack["evidence"]["records"][0]["hr"] is None
    assert "CardioShield" not in pack["slides"][0]["title"]


def test_sglt2_pubmed_does_not_steal_arni_catalog(monkeypatch):
    def fake_search(term, retmax=8):
        return ["31535829"]

    def fake_summary(pmids):
        return {
            "31535829": {
                "title": "Dapagliflozin in patients with heart failure and reduced ejection fraction",
                "fulljournalname": "N Engl J Med",
                "pubdate": "2019",
                "authors": [{"name": "McMurray JJV"}],
                "articleids": [{"idtype": "doi", "value": "10.1056/NEJMoa1911303"}],
                "pubtype": ["Randomized Controlled Trial"],
            }
        }

    monkeypatch.setattr("director_api.evidence._esearch", fake_search)
    monkeypatch.setattr("director_api.evidence._esummary", fake_summary)
    brief = ExtractedBrief(
        brand="GlucoHeart",
        product="dapagliflozin",
        therapy_area="Cardiology - chronic heart failure",
        indication="HFrEF",
        market="India",
    )
    ledger = resolve_evidence(brief, pubmed=True)
    ids = {r["id"] for r in ledger["records"]}
    pmids = {r["pmid"] for r in ledger["records"]}
    assert "paradigm-hf-2014" not in ids
    assert "31535829" in pmids
