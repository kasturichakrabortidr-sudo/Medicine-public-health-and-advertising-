from pathlib import Path

from director_api.extract import extract_one, merge_into_brief


def test_yaml_brief_fields():
    payload = b"""
brand: CardioShield
therapy_area: Cardiology - chronic heart failure
hcp_insights:
  - Field notes - cost is the veto
"""
    extracted = extract_one("brief.yaml", payload, "text/yaml")
    brief = merge_into_brief([extracted])
    assert brief.brand == "CardioShield"
    assert "Cardiology" in brief.therapy_area
    assert brief.hcp_insights[0].startswith("Field notes")


def test_json_brief():
    extracted = extract_one(
        "brief.json",
        b'{"brand":"Lumen","therapy_area":"Oncology"}',
        "application/json",
    )
    brief = merge_into_brief([extracted])
    assert brief.brand == "Lumen"
    assert brief.therapy_area == "Oncology"


def test_csv_and_markdown_heading():
    csv_file = extract_one("notes.csv", b"theme,detail\ncost,OOP burden\n", "text/csv")
    md = extract_one(
        "notes.md",
        b"# Brand\nHelix\n## Therapy Area\nNeurology\n",
        "text/markdown",
    )
    brief = merge_into_brief([csv_file, md])
    assert "Helix" in brief.brand
    assert "Neurology" in brief.therapy_area
    assert "cost" in brief.raw_text


def test_html_and_rtf_strip_markup():
    html = extract_one("a.html", b"<html><body><p>Brand: Nimbus</p></body></html>", "text/html")
    rtf = extract_one("a.rtf", b"{\\rtf1 Therapy area: Dermatology}", "application/rtf")
    assert "Nimbus" in html.text
    assert "<p>" not in html.text
    assert "Dermatology" in rtf.text


def test_image_is_noted_not_ocrd():
    extracted = extract_one("scan.png", b"\x89PNG\r\n", "image/png")
    assert extracted.notes
    assert "scan.png" in extracted.text


def test_docx_and_pptx_extract_text():
    from docx import Document
    from pptx import Presentation
    from pptx.util import Inches
    import io

    doc = Document()
    doc.add_heading("Brand", level=1)
    doc.add_paragraph("Nimbus")
    buf = io.BytesIO()
    doc.save(buf)
    brief = merge_into_brief([extract_one("b.docx", buf.getvalue())])
    assert "Nimbus" in brief.raw_text

    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    box = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(6), Inches(1))
    box.text_frame.text = "Therapy area: Immunology"
    pbuf = io.BytesIO()
    prs.save(pbuf)
    ppt = extract_one("deck.pptx", pbuf.getvalue())
    assert "Immunology" in ppt.text


def test_pasted_prose_infers_market():
    brief = merge_into_brief([], pasted="A cardiology brand launch in India for HFrEF.")
    assert brief.market == "India"
    assert "cardiology" in brief.therapy_area.lower()


TRIVORA = (Path(__file__).resolve().parent / "fixtures" / "trivora_client_brief.txt").read_text(
    encoding="utf-8"
)


def test_trivora_client_brief_is_not_swallowed_into_brand():
    brief = merge_into_brief([], pasted=TRIVORA)
    assert brief.brand == "Trivora-NB Smartules"
    assert "Formoterol" in brief.product or "formoterol" in brief.product
    assert "Glycopyrronium" in brief.product
    assert "COPD" in brief.therapy_area
    assert "first-line" in (brief.business_goal or "").lower()
    assert "20%" in (brief.business_goal or "")
    assert any("free-mix" in c.lower() for c in brief.competitors)
    assert any("GOLD" in g for g in brief.guidelines)
    assert len(brief.hcp_insights) >= 5
    blob = " ".join(brief.hcp_insights).lower()
    assert "rescue or step-up" in blob or "when dual" in blob
    assert "mix it myself" in blob
    assert "consultant physicians, metro and tier-1)" not in blob
    assert "Molecule" not in brief.brand
    assert len(brief.brand) < 60
    assert "GOLD 2026" not in (brief.indication or "")
    assert "STATED POPULATION" not in (brief.indication or "")
