import json

from director_api.extract import ExtractedBrief
from director_api.generate import generate_pack
from medicomarketing_agent.config import load_brief
from director_api.app import _brief_from_mapping


def test_first_touch_doctrine_from_stabilize_insight():
    brief = ExtractedBrief(
        brand="CardioShield",
        therapy_area="Cardiology - HFrEF",
        market="India",
        business_goal="Move from late/second-line use to early initiation",
        hcp_insights=["Most agree in principle but start on ACEi to stabilise first"],
        access_and_cost=["Out-of-pocket, 8-10x generic ARB"],
    )
    pack = generate_pack(brief, pubmed=False)
    assert pack["doctrine"]["id"] == "first-touch"
    assert pack["meta"]["brand"] == "CardioShield"
    ids = [s["id"] for s in pack["slides"]]
    assert 10 <= len(pack["slides"]) <= 13
    assert "how-built" not in ids
    assert "boxplot" not in ids
    # This brief never named PARADIGM-HF or sacubitril — do not invent those charts.
    assert "forest" not in ids
    assert "science-meaning" not in ids
    blob = json.dumps(pack).lower()
    assert "paradigm-hf" not in blob
    assert "sacubitril" not in blob
    assert "pembrolizumab" not in blob
    assert "keynote" not in blob
    kinds = {s.get("chart", {}).get("kind") for s in pack["slides"] if s.get("chart")}
    assert "flow" in kinds
    assert pack["dashboard"]["kpis"]
    assert len(pack["interventions"]) == 5


def test_affordability_doctrine_when_cost_dominates():
    brief = ExtractedBrief(
        brand="Aero",
        therapy_area="Respiratory",
        access_and_cost=["High out-of-pocket cost is the only stated barrier"],
        business_goal="Grow reimbursed volume",
    )
    pack = generate_pack(brief, pubmed=False)
    assert pack["doctrine"]["id"] == "affordability-confidence"


def test_example_brief_is_presentation_ready():
    brief = _brief_from_mapping(load_brief("examples/brief.example.yaml"))
    pack = generate_pack(brief, mode="demo", pubmed=False)
    title = pack["slides"][0]
    assert title["layout"] == "title"
    assert "CardioShield" in title["title"]
    assert title.get("bullets") in (None, [])
    ids = [s["id"] for s in pack["slides"]]
    assert "science-meaning" in ids
    assert "references" in ids
    assert pack["dashboard"]["alerts"]
    kinds = {s.get("chart", {}).get("kind") for s in pack["slides"] if s.get("chart")}
    assert {"people", "spine", "flow", "house", "scatter", "line"} <= kinds
    assert "forest" in kinds
    for slide in pack["slides"]:
        assert slide.get("chart") or slide.get("table") or slide.get("cards")
        headline = slide["title"]
        assert "…" not in headline
        if slide["id"] not in {"title", "references"} and not str(slide["id"]).startswith("references-"):
            assert headline[-1] in ".?!"
        for text in [slide.get("narrative"), slide.get("subtitle"), *(slide.get("bullets") or [])]:
            if not text:
                continue
            assert "…" not in text
        for card in slide.get("cards") or []:
            body = card.get("body") or ""
            if body:
                assert "…" not in body
                assert body.rstrip()[-1] in ".?!"
        chart = slide.get("chart") or {}
        for row in chart.get("data") or []:
            for key in ("detail", "line", "science", "means", "barrier", "execute", "measure", "claim"):
                value = row.get(key) if isinstance(row, dict) else None
                if value and str(value).strip() not in {"—", "-"}:
                    assert "…" not in str(value)


def test_trivora_step_up_brief_is_first_line_not_hospital_wait():
    from pathlib import Path

    from director_api.extract import merge_into_brief

    raw = (Path(__file__).resolve().parent / "fixtures" / "trivora_client_brief.txt").read_text(
        encoding="utf-8"
    )
    brief = merge_into_brief([], pasted=raw)
    pack = generate_pack(brief, pubmed=False)
    assert pack["meta"]["brand"] == "Trivora-NB Smartules"
    assert pack["doctrine"]["id"] == "first-line-not-rescue"
    assert "step-up" in pack["doctrine"]["name"].lower() or "first-line" in pack["doctrine"]["name"].lower()
    enemy = (pack["doctrine"].get("enemy") or "").lower()
    assert "stable" not in enemy
    assert "rescue" in enemy or "free-mix" in enemy or "step-up" in enemy
    assert pack["interventions"][0]["name"] == "First-line maintenance protocol"
    work = json.dumps(pack["workfile"]).lower()
    assert "first-line maintenance" in work
    p05 = next(p for p in pack["workfile"]["phases"] if p["id"] == "05")
    assert "first eligible encounter" not in json.dumps(p05).lower()
    assert "first-line" in json.dumps(p05).lower()
    slides = pack["slides"]
    assert 10 <= len(slides) <= 13
    titles = [s["title"] for s in slides]
    assert all(len(t) <= 90 for t in titles)
    dump = json.dumps(slides).lower()
    assert "kronos" not in dump or "literature review retrieved" not in dump
    assert "do not lock a scientific lead" not in dump
    blob = json.dumps(pack).lower()
    assert "paradigm-hf" not in blob
    assert "sacubitril" not in blob
    assert "keynote" not in blob
    assert "do not lock a scientific lead" in pack["evidence"]["lead"]["statement"].lower()
