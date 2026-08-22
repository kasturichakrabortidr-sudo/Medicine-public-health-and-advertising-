from director_api.evidence import _pubmed_queries, resolve_evidence
from director_api.extract import ExtractedBrief
from director_api.generate import generate_pack
from director_api.molecule import inn_from_text, science_name
from director_api.paper_read import extract_finding, search_product_name


def test_inn_from_brand_and_dressed_product():
    assert inn_from_text("Entresto 97/103 mg") == "sacubitril/valsartan"
    assert inn_from_text("Jardiance") == "empagliflozin"
    assert inn_from_text("Farxiga") == "dapagliflozin"
    assert inn_from_text("Keytruda") == "pembrolizumab"
    assert inn_from_text(
        "sacubitril/valsartan fixed-dose combination (illustrative example)"
    ) == "sacubitril/valsartan"
    assert inn_from_text("lumetinib") == "lumetinib"
    assert inn_from_text("Finerenone") == "finerenone"
    assert inn_from_text("Kerendia") == "finerenone"
    assert inn_from_text("Velmecor 10 mg / 20 mg (fictional once-daily oral therapy)") == ""
    assert inn_from_text("Cardiava™ (fictional brand)") == ""
    assert inn_from_text("CardioShield") == ""


def test_pubmed_queries_use_inn_never_brand():
    brief = ExtractedBrief(
        brand="HelixOne",
        product="Entresto",
        therapy_area="Cardiology — HFrEF",
        indication="HFrEF",
    )
    assert science_name(brief) == "sacubitril/valsartan"
    blob = " ".join(_pubmed_queries(brief)).lower()
    assert "sacubitril" in blob
    assert "entresto" not in blob
    assert "helixone" not in blob


def test_jardiance_hfpef_searches_empagliflozin():
    brief = ExtractedBrief(
        brand="Cardiava",
        product="Jardiance",
        therapy_area="Heart Failure with Preserved Ejection Fraction (HFpEF",
    )
    assert science_name(brief) == "empagliflozin"
    blob = " ".join(_pubmed_queries(brief)).lower()
    assert "empagliflozin" in blob
    assert "jardiance" not in blob
    assert "cardiava" not in blob


def test_finerenone_brief_uses_inn_not_campaign_brand():
    brief = ExtractedBrief(
        brand="FINERVA (finerenone 10/20 mg film-coated tablets)",
        product="Finerenone",
        therapy_area="diabetes (CKD-T2D)",
        indication="Cardiorenal protection",
    )
    assert science_name(brief) == "finerenone"
    blob = " ".join(_pubmed_queries(brief)).lower()
    assert "finerenone" in blob
    assert "finerva" not in blob
    kerendia = ExtractedBrief(
        brand="Metro launch",
        product="Kerendia 10 mg / 20 mg",
        therapy_area="CKD with type 2 diabetes",
    )
    assert science_name(kerendia) == "finerenone"


def test_claim_sentence_uses_inn_not_trade_name():
    parsed = extract_finding(
        "Empagliflozin in heart failure with a preserved ejection fraction",
        "RESULTS: The primary composite occurred in 13.8% with empagliflozin and in 17.1% with placebo "
        "(hazard ratio 0.79; 95% CI 0.69 to 0.90). "
        "CONCLUSIONS: Empagliflozin reduced cardiovascular death or hospitalisation.",
        product="Jardiance",
    )
    assert "empagliflozin" in parsed["claim"].lower()
    assert "jardiance" not in parsed["claim"].lower()


def test_cardioshield_science_names_the_molecule():
    brief = ExtractedBrief(
        brand="CardioShield",
        product="sacubitril/valsartan fixed-dose combination (illustrative example)",
        therapy_area="Cardiology - chronic heart failure",
        indication="HFrEF",
    )
    assert search_product_name(brief.product) == "sacubitril/valsartan"
    pack = generate_pack(brief, pubmed=False)
    assert pack["meta"]["molecule"] == "sacubitril/valsartan"
    p02 = next(p for p in pack["workfile"]["phases"] if p["id"] == "02")
    intervention = " ".join(str(c) for c in p02["pico"]["rows"][1]).lower()
    assert "sacubitril" in intervention
    assert "cardioshield" not in intervention
    how = (pack["workfile"].get("howBuilt") or "").lower()
    assert "sacubitril" in how
    papers = " ".join(r.get("claim_permitted") or "" for r in pack["evidence"]["records"]).lower()
    assert "entresto" not in papers
    ledger = resolve_evidence(brief, pubmed=False)
    assert "paradigm-hf-2014" in {r["id"] for r in ledger["records"]}
