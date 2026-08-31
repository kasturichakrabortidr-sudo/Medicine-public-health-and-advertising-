"""Client strategy deck is a 12-slide argument, not a literature dump."""

from pathlib import Path

from director_api.extract import merge_into_brief
from director_api.generate import generate_pack
from director_api.app import _brief_from_mapping
from medicomarketing_agent.config import load_brief

DUMP_IDS = {
    "landscape",
    "barriers",
    "literature-review",
    "citation-register",
    "science-compare",
    "matrix",
    "who",
    "opportunity",
    "segments",
    "forest",
}


def test_example_deck_is_twelve_slides_not_a_dump():
    pack = generate_pack(_brief_from_mapping(load_brief("examples/brief.example.yaml")), pubmed=False)
    slides = pack["slides"]
    ids = [s["id"] for s in slides]
    assert 10 <= len(slides) <= 12, ids
    assert ids[0] == "title"
    assert "problem" in ids
    assert "science-lead" in ids
    assert ids[-1] == "references" or ids[-1].startswith("references")
    assert DUMP_IDS.isdisjoint(ids), ids
    for slide in slides:
        if slide["id"] in {"title", "references"} or str(slide["id"]).startswith("references-"):
            continue
        assert len(slide["title"]) <= 90, (slide["id"], slide["title"])
        assert not slide["title"].lower().endswith(" is.")
        blob = " ".join(
            [
                slide["title"],
                slide.get("narrative") or "",
                " ".join(st.get("caption") or "" for st in slide.get("stats") or []),
            ]
        ).lower()
        assert "numbered papers on the working-file" not in blob
        assert "brief lines still lack" not in blob


def test_trivora_deck_is_a_strategy_argument_not_an_abstract_dump():
    raw = (Path(__file__).resolve().parent / "fixtures" / "trivora_client_brief.txt").read_text(
        encoding="utf-8"
    )
    pack = generate_pack(merge_into_brief([], pasted=raw), pubmed=False)
    slides = pack["slides"]
    ids = [s["id"] for s in slides]
    assert 10 <= len(slides) <= 12, ids
    assert DUMP_IDS.isdisjoint(ids), ids
    titles = [s["title"] for s in slides]
    assert all(len(t) <= 90 for t in titles)
    dump = " ".join(titles).lower()
    assert "budesonide/glycopyrrolate/formoterol triple therapy versus dual therapies" not in dump
    problem = next(s for s in slides if s["id"] == "problem")
    assert "stable in clinic" not in problem["title"].lower()
    assert "rescue" in problem["title"].lower() or "free-mix" in problem["title"].lower()
    assert len(problem["title"]) <= 56
    stats = " ".join(st["value"] for st in problem["stats"])
    assert "20%" in stats
    lead = next(s for s in slides if s["id"] == "science-lead")
    assert not lead["title"].lower().endswith("health-related.")
    assert "progressive illness" not in lead["title"].lower()
    house = next(s for s in slides if s["id"] == "house")
    assert "pillar" in house["title"].lower()
    close = next(s for s in slides if s["id"] == "close")
    assert close["title"].startswith("Sign")
    assert "do not lock a scientific lead" not in (close.get("callout") or {}).get("text", "").lower()
    moves = next(s for s in slides if s["id"] == "interventions")
    assert "first-line" in moves["title"].lower()
    assert "retire the wait" not in moves["title"].lower()
    names = [c["title"] for c in moves["cards"]]
    assert "First-line maintenance protocol" in names
    assert "Free-mix cost script" in names
    blob = " ".join(s["title"] for s in slides).lower()
    assert "first-line" in blob or "maintenance" in blob
