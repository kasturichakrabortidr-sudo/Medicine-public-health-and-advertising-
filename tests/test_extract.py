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


def test_yaml_without_brand_does_not_swallow_prose():
    pasted = (
        "date: 12 May\nfrom: medical affairs\n\n"
        "# Brand\nLumenDerm\n## Therapy Area\nDermatology\n"
    )
    brief = merge_into_brief([], pasted=pasted)
    assert brief.brand == "LumenDerm"
    assert "Dermatology" in brief.therapy_area


def test_labelled_prose_fills_working_brief():
    pasted = """
Confidential campaign brief
Brand name: LumenDerm
Product: lumetinib
Therapy area: Dermatology
Indication: moderate-to-severe plaque psoriasis
Market: India
Objective: Grow first-line share among metro dermatologists
Target HCPs:
- Dermatologists
- Immunologists
Insights:
- Cost is the veto at the desk
- They wait for phototherapy to fail
Evidence:
- BEACON-PSO week-16 PASI 90
Guidelines:
- IADVL psoriasis 2023
Competitors:
- adalimumab biosimilars
Access:
- High OOP in private clinics
"""
    brief = merge_into_brief([], pasted=pasted)
    assert brief.brand == "LumenDerm"
    assert brief.product.lower() == "lumetinib"
    assert "Dermatology" in brief.therapy_area
    assert "psoriasis" in brief.indication.lower()
    assert brief.market == "India"
    assert "share" in brief.business_goal.lower()
    assert any("Dermatolog" in s for s in brief.target_specialties)
    assert any("veto" in s.lower() for s in brief.hcp_insights)
    assert any("BEACON" in s for s in brief.brand_evidence)
    assert any("IADVL" in s for s in brief.guidelines)
    assert any("adalimumab" in s.lower() for s in brief.competitors)
    assert any("OOP" in s for s in brief.access_and_cost)


def test_guidelines_do_not_swallow_following_table_rows():
    pasted = """
Brand name: HelixOne
Product: sacubitril
Guidelines:
- ESC HF 2021
Therapy area | Cardiology — HFrEF
Market | India
Insights | Cost is the veto at the desk
"""
    brief = merge_into_brief([], pasted=pasted)
    assert brief.brand == "HelixOne"
    assert "Cardiology" in brief.therapy_area
    assert brief.market == "India"
    assert brief.guidelines == ["ESC HF 2021"]
    assert any("veto" in s.lower() for s in brief.hcp_insights)


def test_title_only_and_table_rows():
    pasted = """
HELIXONE

A launch plan for sacubitril in chronic heart failure, India.

Brand | HelixOne
Product | sacubitril
Therapy area | Cardiology
"""
    brief = merge_into_brief([], pasted=pasted)
    assert "Helix" in brief.brand or brief.brand == "HELIXONE"
    assert "sacubitril" in brief.product.lower()
    assert "cardio" in brief.therapy_area.lower() or "heart failure" in brief.therapy_area.lower()
    assert brief.market == "India"


def test_long_doc_with_brand_colon_keeps_insights():
    body = "\n".join(f"Background paragraph {i} about clinic workflow and follow-up." for i in range(40))
    pasted = f"""Brand: NimbusTide
Therapy area: Endocrinology
Market: Brazil

{body}

Insights:
- Endocrinologists titrate slowly because of GI events
- Nurses own the initiation conversation

Competitors:
- semaglutide
"""
    brief = merge_into_brief([], pasted=pasted)
    assert brief.brand == "NimbusTide"
    assert "Endocrinology" in brief.therapy_area
    assert any("titrate" in s.lower() for s in brief.hcp_insights)
    assert any("semaglutide" in s.lower() for s in brief.competitors)
    assert "Background paragraph 12" in brief.raw_text


def test_docx_table_and_brand_name_label():
    from docx import Document
    import io

    doc = Document()
    doc.add_paragraph("CAMPAIGN BRIEF")
    doc.add_paragraph("Brand name: LumenDerm")
    doc.add_paragraph("Product: lumetinib")
    table = doc.add_table(rows=3, cols=2)
    table.cell(0, 0).text = "Therapy area"
    table.cell(0, 1).text = "Dermatology"
    table.cell(1, 0).text = "Market"
    table.cell(1, 1).text = "India"
    table.cell(2, 0).text = "Insights"
    table.cell(2, 1).text = "Cost is the veto at the desk"
    buf = io.BytesIO()
    doc.save(buf)
    payload = buf.getvalue()
    extracted = extract_one("client-brief.docx", payload)
    brief = merge_into_brief([extracted])
    assert brief.brand == "LumenDerm"
    assert "lumetinib" in brief.product.lower()
    assert "Dermatology" in brief.therapy_area
    assert brief.market == "India"
    assert any("veto" in s.lower() for s in brief.hcp_insights)

    sniffed = extract_one("upload", payload)
    assert "LumenDerm" in sniffed.text
    sniffed_brief = merge_into_brief([sniffed])
    assert sniffed_brief.brand == "LumenDerm"


def test_pptx_title_and_table():
    from pptx import Presentation
    from pptx.util import Inches
    import io

    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    title = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(8), Inches(0.8))
    title.text_frame.text = "HELIXONE"
    body = slide.shapes.add_textbox(Inches(0.5), Inches(1.1), Inches(8), Inches(0.6))
    body.text_frame.text = "sacubitril/valsartan  launch  —  heart failure  —  India"
    table = slide.shapes.add_table(2, 2, Inches(0.5), Inches(2), Inches(8), Inches(1.2)).table
    table.cell(0, 0).text = "Brand"
    table.cell(0, 1).text = "HelixOne"
    table.cell(1, 0).text = "Therapy area"
    table.cell(1, 1).text = "Cardiology"
    pbuf = io.BytesIO()
    prs.save(pbuf)
    extracted = extract_one("helix.pptx", pbuf.getvalue())
    brief = merge_into_brief([extracted])
    assert "Helix" in brief.brand
    assert "cardio" in brief.therapy_area.lower() or "heart failure" in brief.therapy_area.lower()
    assert "sacubitril" in (brief.product or extracted.text).lower()
    assert brief.market == "India"


def test_references_heading_fills_existing_evidence():
    pasted = """
Brand name: FINERVA
Product: Finerenone
Therapy area: CKD-T2D
References:
- FIDELIO-DKD Bakris 2020 PMID 33264825
- FIGARO-DKD Pitt 2021
- FIDELITY pooled analysis
"""
    brief = merge_into_brief([], pasted=pasted)
    assert any("FIDELIO" in s for s in brief.existing_evidence)
    assert any("FIGARO" in s for s in brief.existing_evidence)
    assert any("FIDELITY" in s for s in brief.existing_evidence)


def test_yaml_files_still_win_on_explicit_keys():
    payload = b"brand: CardioShield\ntherapy_area: Cardiology - chronic heart failure\n"
    brief = merge_into_brief([extract_one("brief.yaml", payload, "text/yaml")])
    assert brief.brand == "CardioShield"
    assert "Cardiology" in brief.therapy_area

