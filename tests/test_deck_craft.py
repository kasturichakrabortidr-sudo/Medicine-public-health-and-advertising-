import re

from director_api.extract import ExtractedBrief
from director_api.generate import generate_pack
from medicomarketing_agent.config import load_brief
from director_api.app import _brief_from_mapping
from director_api.deck_visuals import cue, line, sentence


BANNED_IDS = {"how-built", "questions", "boxplot", "citation-register", "science-lead"}
VISUAL_KEYS = ("chart", "board", "flow", "stat")
REQUIRED_PHASES = {f"{i:02d}" for i in range(1, 12)}
REQUIRED_SLIDES = {
    "title", "need", "tension", "belief", "pico", "pack", "stand",
    "house", "objections", "sequence", "who", "interventions", "measure", "close",
}
HANGING = re.compile(
    r"\b(the|a|an|at|in|if|to|for|of|and|or|with|on|by|from|as|than)\s*$",
    re.I,
)


def _demo_pack(**kwargs):
    brief = _brief_from_mapping(load_brief("examples/brief.example.yaml"))
    return generate_pack(brief, mode="demo", pubmed=False, **kwargs)


def _copy_blobs(slide: dict) -> list[str]:
    blobs = [
        slide.get("title") or "",
        slide.get("subtitle") or "",
        slide.get("narrative") or "",
    ]
    for card in (slide.get("board") or {}).get("cards") or []:
        blobs.extend([card.get("title") or "", card.get("body") or ""])
    for step in (slide.get("flow") or {}).get("steps") or []:
        blobs.extend([step.get("title") or "", step.get("body") or ""])
    for item in (slide.get("stat") or {}).get("items") or []:
        blobs.extend([item.get("value") or "", item.get("label") or ""])
    return blobs


def test_sentence_never_uses_ellipsis():
    assert "…" not in sentence("Start CardioShield at the first eligible encounter — in hospital if that is when they are eligible.")
    assert sentence("The doctors wait. Cost does the rest.") == "The doctors wait."
    assert sentence("No stop here") == "No stop here."
    assert sentence("The patient cannot afford this") == "The patient cannot afford this."
    assert line("The patient cannot afford this") == "The patient cannot afford this"
    assert cue('Advisory board (n=12 cardiologists) - most agree with early initiation in principle but start on ACEi/ARB "to stabilise first"') == "They wait to stabilise first"
    assert cue("The patient cannot afford this") == "The patient cannot afford this"
    assert cue("to stabilise first") == "They wait to stabilise first"
    assert "…" not in cue("x" * 200)


def test_deck_interprets_plan_not_the_file():
    pack = _demo_pack()
    ids = [s["id"] for s in pack["slides"]]
    assert pack["meta"]["deckSkill"] == "strata-deck"
    assert pack["meta"]["deckSkills"] == ["story", "visuals", "copy", "layout"]
    assert not (set(ids) & BANNED_IDS)
    assert ids[0] == "title"
    missing = REQUIRED_SLIDES - set(ids)
    assert not missing, missing
    assert pack["workfile"]["phases"][0]["id"] == "01"
    phases = {row["phase"] for row in pack["meta"]["storyMap"]}
    assert REQUIRED_PHASES <= phases
    assert all(row.get("slide") and row.get("question") for row in pack["meta"]["storyMap"])
    assert pack["meta"]["deckSkillCards"][0]["id"] == "story"


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


def test_copy_is_complete_never_clipped():
    pack = _demo_pack()
    for slide in pack["slides"]:
        for blob in _copy_blobs(slide):
            assert "…" not in blob, (slide["id"], blob)
            assert "..." not in blob, (slide["id"], blob)
            words = blob.strip()
            if len(words.split()) >= 4:
                assert not HANGING.search(words.rstrip(".!?")), (slide["id"], blob)


def test_visuals_interpret_the_working_file():
    pack = _demo_pack()
    need = next(s for s in pack["slides"] if s["id"] == "need")
    assert "doctors already told us" not in (need.get("narrative") or "").lower()
    assert "advisory board" not in (need.get("narrative") or "").lower()
    assert need["stat"]["items"][0]["value"] == "15%"
    assert need["stat"]["items"][1]["value"] == "Delay"
    belief = next(s for s in pack["slides"] if s["id"] == "belief")
    titles = " ".join(c["title"] for c in belief["board"]["cards"])
    assert "advisory board" not in titles.lower()
    assert "stabilis" in titles.lower()
    pico = next(s for s in pack["slides"] if s["id"] == "pico")
    cards = pico["board"]["cards"]
    assert len(cards) == 5
    assert cards[0]["kicker"].lower().startswith("population")
    assert cards[0]["title"].lower() != cards[0]["kicker"].lower()
    for slide in pack["slides"]:
        for card in (slide.get("board") or {}).get("cards") or []:
            words = (card.get("title") or "").replace("—", " ").split()
            assert len(words) <= 12, (slide["id"], card.get("title"))


def test_objections_keep_full_clause():
    pack = _demo_pack()
    obj = next(s for s in pack["slides"] if s["id"] == "objections")
    titles = " ".join(c["title"] for c in obj["board"]["cards"])
    assert "cannot afford this" in titles.lower()
    for card in obj["board"]["cards"]:
        ref = (card.get("ref") or "").strip()
        if ref:
            assert "[" in ref and "]" in ref, (card["title"], ref)


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

    story = {"headline": "Start at the first eligible visit", "need": "They still wait."}
    assert polish_story(dict(story), None, {"name": "Start"}) == story


def test_titles_stay_short_and_complete():
    pack = _demo_pack()
    for slide in pack["slides"]:
        if slide["layout"] == "references":
            continue
        title = slide.get("title") or ""
        words = [w for w in title.replace("—", " ").split() if w]
        assert 1 <= len(words) <= 14, (slide["id"], title)
        assert "…" not in title
        assert not HANGING.search(title.rstrip(".!?")), title


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
    assert "need" in ids
    assert "pico" in ids
    assert "pack" in ids
    assert "measure" in ids
    assert pack["meta"]["brand"] == "HelixOne"
    meaning = next(s for s in pack["slides"] if s["id"] == "science-meaning")
    assert meaning["chart"]["data"][0]["pmid"] == "29658856"
    for slide in pack["slides"]:
        for blob in _copy_blobs(slide):
            assert "…" not in blob, (slide["id"], blob)
