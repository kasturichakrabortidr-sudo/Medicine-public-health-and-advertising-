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
