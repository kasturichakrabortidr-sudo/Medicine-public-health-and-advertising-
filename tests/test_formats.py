from pathlib import Path

from fastapi.testclient import TestClient

from director_api.app import _brief_from_mapping, app
from director_api.generate import generate_pack
from director_api.workfile_export import filename_for_workfile, workfile_to_markdown
from medicomarketing_agent.config import load_brief

ROOT = Path(__file__).resolve().parents[1]
client = TestClient(app)


def _sample_pack():
    return generate_pack(_brief_from_mapping(load_brief("examples/brief.example.yaml")), mode="demo", pubmed=False)


def test_workfile_markdown_export():
    pack = _sample_pack()
    text = workfile_to_markdown(pack)
    assert "CardioShield" in text
    assert "## 01" in text
    assert filename_for_workfile(pack) == "CardioShield-working-file.md"
    posted = client.post("/api/export/workfile", json=pack)
    assert posted.status_code == 200
    assert "markdown" in posted.headers["content-type"]
    assert b"CardioShield" in posted.content
    assert b"## 01" in posted.content


def test_workfile_export_rejects_empty_pack():
    res = client.post("/api/export/workfile", json={"meta": {}})
    assert res.status_code == 400


def test_print_and_visual_surfaces_exist():
    css = (ROOT / "web" / "src" / "styles.css").read_text(encoding="utf-8")
    assert "@media print" in css
    assert "print-deck" in css
    deck = (ROOT / "web" / "src" / "screens" / "DeckScreen.tsx").read_text(encoding="utf-8")
    assert "Print PDF" in deck
    assert "print-deck" in deck
    work = (ROOT / "web" / "src" / "screens" / "WorkfileScreen.tsx").read_text(encoding="utf-8")
    assert "Download markdown" in work
    assert "Print PDF" in work
    charts = (ROOT / "web" / "src" / "components" / "SlideChart.tsx").read_text(encoding="utf-8")
    assert "PeopleChart" in charts
    assert "ForestChart" in charts
    assert "HouseChart" in charts
    assert "SpineChart" in charts
