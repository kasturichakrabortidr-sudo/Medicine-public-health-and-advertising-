from fastapi.testclient import TestClient

from director_api.app import app

client = TestClient(app)


def test_spa_and_demo_json():
    res = client.get("/")
    if res.status_code != 503:
        assert res.status_code == 200
        assert "STRATA" in res.text
    demo = client.get("/demo.json")
    assert demo.status_code == 200
    assert demo.json()["meta"]["brand"] == "CardioShield"


def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["ok"] is True
    assert "pdf" in res.json()["accept"]
    skills = client.get("/api/deck-skills")
    assert skills.status_code == 200
    names = {s["id"] for s in skills.json()["skills"]}
    assert names == {"story", "visuals", "copy", "critic"}
    assert {e["id"] for e in skills.json()["engines"]} == names
    assert len(skills.json()["beats"]) >= 11


def test_demo_pack():
    res = client.get("/api/demo")
    assert res.status_code == 200
    pack = res.json()
    assert pack["meta"]["brand"] == "CardioShield"
    assert pack["slides"]
    assert pack["dashboard"]["kpis"]


def test_extract_and_generate_upload():
    files = [("files", ("brief.yaml", b"brand: Helix\ntherapy_area: Oncology\n", "text/yaml"))]
    extracted = client.post("/api/extract", files=files)
    assert extracted.status_code == 200
    assert extracted.json()["brief"]["brand"] == "Helix"

    generated = client.post("/api/generate", files=files)
    assert generated.status_code == 200
    assert generated.json()["meta"]["brand"] == "Helix"


def test_generate_rejects_empty():
    res = client.post("/api/generate", data={"pasted": ""})
    assert res.status_code == 400


def test_generate_uploaded_brief_is_not_cardioshield_demo():
    files = [(
        "files",
        (
            "acme.yaml",
            b"brand: AcmeDerm\ntherapy_area: Dermatology\nmarket: India\n"
            b"business_goal: Grow related clinic share.\n",
            "text/yaml",
        ),
    )]
    generated = client.post("/api/generate", files=files)
    assert generated.status_code == 200
    pack = generated.json()
    assert pack["meta"]["brand"] == "AcmeDerm"
    assert pack["meta"]["demo"] is False
    assert pack["meta"]["mode"] != "demo"
    assert "CardioShield" not in pack["slides"][0]["title"]
    ids = {r["id"] for r in pack["evidence"]["records"]}
    assert "paradigm-hf-2014" not in ids
    assert "pioneer-hf-2019" not in ids


def test_generate_prefers_uploaded_file_over_empty_form_brand():
    files = [("files", ("brief.yaml", b"brand: Helix\ntherapy_area: Oncology - NSCLC\n", "text/yaml"))]
    generated = client.post(
        "/api/generate",
        files=files,
        data={"brief_json": '{"brand":"","therapy_area":"Oncology - NSCLC"}'},
    )
    assert generated.status_code == 200
    pack = generated.json()
    assert pack["meta"]["brand"] == "Helix"
    assert pack["meta"]["demo"] is False


def test_extract_labelled_client_prose():
    pasted = (
        "Brand name: LumenDerm\nProduct: lumetinib\nTherapy area: Dermatology\n"
        "Market: India\nInsights:\n- Cost is the veto at the desk\n"
    )
    res = client.post("/api/extract", data={"pasted": pasted})
    assert res.status_code == 200
    brief = res.json()["brief"]
    assert brief["brand"] == "LumenDerm"
    assert brief["product"] == "lumetinib"
    assert "Dermatology" in brief["therapy_area"]
    assert brief["market"] == "India"
    assert any("veto" in s.lower() for s in brief["hcp_insights"])

    pack = client.post("/api/generate", data={"pasted": pasted}).json()
    assert pack["meta"]["brand"] == "LumenDerm"
    assert pack["meta"]["demo"] is False
    assert "CardioShield" not in pack["slides"][0]["title"]

