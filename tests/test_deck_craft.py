from director_api.extract import ExtractedBrief
from director_api.generate import generate_pack
from medicomarketing_agent.config import load_brief
from director_api.app import _brief_from_mapping


BANNED_IDS = {"how-built", "questions", "boxplot", "citation-register", "science-lead"}
VISUAL_KEYS = ("chart", "board", "flow", "stat")


def _demo_pack(**kwargs):
    brief = _brief_from_mapping(load_brief("examples/brief.example.yaml"))
    return generate_pack(brief, mode="demo", pubmed=False, **kwargs)


def test_deck_interprets_plan_not_the_file():
    pack = _demo_pack()
    ids = [s["id"] for s in pack["slides"]]
    assert pack["meta"]["deckSkill"] == "strata-deck"
    assert not (set(ids) & BANNED_IDS)
    assert ids[0] == "title"
    assert "tension" in ids
    assert "science-meaning" in ids
    assert "forest" in ids
    assert "pack" in ids
    assert "house" in ids
    assert "science-execute" in ids
    assert "interventions" in ids
    assert "close" in ids
    assert "references" in ids
    assert pack["workfile"]["phases"][0]["id"] == "01"


def test_one_visual_owns_each_content_slide():
    pack = _demo_pack()
    for slide in pack["slides"]:
        assert not (slide.get("chart") and slide.get("table")), slide["id"]
        layout = slide.get("layout")
        if layout in {"title", "close", "references", "insight"}:
            continue
        assert any(slide.get(k) for k in VISUAL_KEYS), slide["id"]
        if slide.get("layout") in {"visual", "board", "flow", "stat"}:
            assert not slide.get("bullets")


def test_people_grid_is_one_paper():
    pack = _demo_pack()
    meaning = next(s for s in pack["slides"] if s["id"] == "science-meaning")
    assert meaning["layout"] == "visual"
    assert meaning["chart"]["kind"] == "people"
    assert len(meaning["chart"]["data"]) == 1
    row = meaning["chart"]["data"][0]
    assert row["pmid"] == "25176015"
    assert row["nnt"] == 21


def test_spine_is_at_most_two_rows():
    pack = _demo_pack()
    execute = next(s for s in pack["slides"] if s["id"] == "science-execute")
    assert execute["chart"]["kind"] == "spine"
    assert len(execute["chart"]["data"]) <= 2
    names = " ".join(str(r.get("name")) for r in execute["chart"]["data"])
    assert "PIONEER-HF" in names
    assert "PARADIGM" in names


def test_polish_is_off_without_flag(monkeypatch):
    monkeypatch.delenv("STRATA_DECK_AI", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    from director_api.deck_ai import polish_story

    story = {"headline": "Start at the first eligible visit", "tension": "They still wait."}
    assert polish_story(dict(story), None, {"name": "Start"}) == story


def test_titles_stay_short():
    pack = _demo_pack()
    for slide in pack["slides"]:
        if slide["layout"] == "references":
            continue
        words = [w for w in (slide.get("title") or "").replace("—", " ").split() if w]
        assert len(words) <= 12, slide["id"]


def test_helix_cost_brief_still_gets_a_visual_deck():
    brief = ExtractedBrief(
        brand="HelixOne",
        therapy_area="Oncology - NSCLC",
        indication="first-line NSCLC",
        business_goal="Grow first-line share. Cost of IO combo is the main barrier.",
    )
    pack = generate_pack(brief, pubmed=False)
    ids = {s["id"] for s in pack["slides"]}
    assert "title" in ids
    assert "tension" in ids
    assert "science-meaning" in ids
    assert pack["meta"]["brand"] == "HelixOne"
    meaning = next(s for s in pack["slides"] if s["id"] == "science-meaning")
    assert meaning["chart"]["data"][0]["pmid"] == "29658856"
