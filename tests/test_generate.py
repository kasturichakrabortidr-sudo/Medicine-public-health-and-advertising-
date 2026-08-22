from director_api.extract import ExtractedBrief
from director_api.generate import generate_pack
from medicomarketing_agent.config import load_brief
from director_api.app import _brief_from_mapping


def test_first_touch_doctrine_from_stabilize_insight():
    brief = ExtractedBrief(
        brand="CardioShield",
        product="sacubitril/valsartan",
        therapy_area="Cardiology - HFrEF",
        market="India",
        business_goal="Move from late/second-line use to early initiation",
        brand_evidence=["PARADIGM-HF style pivotal RCT vs enalapril"],
        evolving_evidence=["Emerging data on early in-hospital initiation"],
        guidelines=["ESC heart failure guidelines Class I for ARNI"],
        hcp_insights=["Most agree in principle but start on ACEi to stabilise first"],
        access_and_cost=["Out-of-pocket, 8-10x generic ARB"],
    )
    pack = generate_pack(brief)
    assert pack["doctrine"]["id"] == "first-touch"
    assert pack["meta"]["brand"] == "CardioShield"
    assert len(pack["slides"]) >= 12
    kinds = {s.get("chart", {}).get("kind") for s in pack["slides"] if s.get("chart")}
    assert {"bar", "forest", "pie", "line", "scatter", "diverging", "people", "compare", "spine"} <= kinds
    assert pack["dashboard"]["kpis"]
    assert len(pack["interventions"]) == 5


def test_affordability_doctrine_when_cost_dominates():
    brief = ExtractedBrief(
        brand="Aero",
        therapy_area="Respiratory",
        access_and_cost=["High out-of-pocket cost is the only stated barrier"],
        business_goal="Grow reimbursed volume",
    )
    pack = generate_pack(brief)
    assert pack["doctrine"]["id"] == "affordability-confidence"


def test_example_brief_is_presentation_ready():
    brief = _brief_from_mapping(load_brief("examples/brief.example.yaml"))
    pack = generate_pack(brief, mode="demo")
    title = pack["slides"][0]
    assert title["layout"] == "title"
    assert "CardioShield" in title["title"]
    assert any(s["id"] == "forest" for s in pack["slides"])
    assert any(s["id"] == "boxplot" for s in pack["slides"])
    assert pack["dashboard"]["alerts"]
    assert pack["meta"]["demo"] is True


def test_related_word_does_not_trigger_first_touch_demo():
    brief = ExtractedBrief(
        brand="Nimbus",
        therapy_area="Immunology",
        business_goal="Grow related specialist advocacy.",
        hcp_insights=["They want a template, not a lecture."],
    )
    pack = generate_pack(brief, pubmed=False)
    assert pack["doctrine"]["id"] != "first-touch"
    assert pack["meta"]["brand"] == "Nimbus"
    assert pack["interventions"][0]["name"] != "First-Touch Protocol"
