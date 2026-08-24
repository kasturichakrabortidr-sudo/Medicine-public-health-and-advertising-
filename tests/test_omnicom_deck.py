import io
import zipfile

from director_api.app import _brief_from_mapping
from director_api.extract import ExtractedBrief
from director_api.generate import generate_pack
from director_api.pptx_export import pack_to_pptx
from medicomarketing_agent.config import load_brief


def test_deck_follows_omnicom_medical_strategy_template():
    brief = _brief_from_mapping(load_brief("examples/brief.example.yaml"))
    pack = generate_pack(brief, mode="demo", pubmed=False)
    slides = pack["slides"]
    title = slides[0]
    assert title["layout"] == "title"
    assert title["kicker"].upper().startswith("MEDICAL STRATEGY DECK")
    assert "CardioShield" in title["title"]
    assert title.get("cards")

    kickers = [s["kicker"].lower() for s in slides]
    assert any("market context" in k for k in kickers)
    assert any("messaging architecture" in k for k in kickers)
    assert any("strategic" in k for k in kickers)

    sourced = [s for s in slides if s.get("source")]
    assert len(sourced) >= 10
    assert all(s.get("page") for s in slides)

    problem = next(s for s in slides if s["id"] == "problem")
    assert problem["layout"] == "insight"
    assert problem.get("stats")
    assert "15%" in " ".join(st["value"] for st in problem["stats"]) or "8-10x" in " ".join(
        st["value"].lower() for st in problem["stats"]
    )
    assert "working file 01" in (problem.get("source") or "").lower()

    idea = next(s for s in slides if s["id"] == "the-bet")
    assert idea["layout"] == "idea"
    assert len(idea.get("cards") or []) >= 3

    house = next(s for s in slides if s["id"] == "house")
    assert house["kicker"].lower().startswith("messaging")
    assert house["chart"]["kind"] == "house"


def test_helix_deck_is_not_a_cardioshield_copy():
    brief = ExtractedBrief(
        brand="HelixOne",
        therapy_area="Oncology - NSCLC",
        indication="first-line NSCLC",
        business_goal="Grow first-line share. Cost of IO combo is the main barrier.",
    )
    pack = generate_pack(brief, pubmed=False)
    title = pack["slides"][0]
    blob = " ".join(
        [
            title["title"],
            title.get("subtitle") or "",
            title.get("narrative") or "",
            *(c.get("title") or "" for c in title.get("cards") or []),
        ]
    )
    assert "HelixOne" in blob
    assert "CardioShield" not in blob
    problem = next(s for s in pack["slides"] if s["id"] == "problem")
    assert "CardioShield" not in (problem["title"] + (problem.get("narrative") or ""))


def test_pptx_uses_omnicom_palette():
    brief = _brief_from_mapping(load_brief("examples/brief.example.yaml"))
    pack = generate_pack(brief, mode="demo", pubmed=False)
    data = pack_to_pptx(pack)
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        xml = b"".join(zf.read(name) for name in zf.namelist() if name.endswith(".xml"))
    assert b"4E7DF2" in xml
    assert b"FF6433" in xml
    assert b"F7F7F4" in xml
