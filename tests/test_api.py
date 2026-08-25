from fastapi.testclient import TestClient

from director_api.app import app

client = TestClient(app)


def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["ok"] is True
    assert "pdf" in res.json()["accept"]


def test_cardioshield_demo_is_not_in_the_app():
    assert client.get("/api/demo").status_code == 404
    demo_json = client.get("/demo.json")
    if demo_json.status_code == 200:
        assert "json" not in (demo_json.headers.get("content-type") or "")
        assert "slides" not in demo_json.text.lower()[:200]
    else:
        assert demo_json.status_code in {404, 405, 503}
    export = client.get("/api/export/pptx")
    assert export.status_code in {404, 405}


def test_extract_and_generate_upload_is_the_uploaded_brand():
    files = [("files", ("brief.yaml", b"brand: Helix\ntherapy_area: Oncology\n", "text/yaml"))]
    extracted = client.post("/api/extract", files=files)
    assert extracted.status_code == 200
    assert extracted.json()["brief"]["brand"] == "Helix"

    generated = client.post("/api/generate", files=files)
    assert generated.status_code == 200
    pack = generated.json()
    assert pack["meta"]["brand"] == "Helix"
    assert pack["meta"]["brand"] != "CardioShield"

    listed = client.get("/api/projects").json()["projects"]
    assert any(p["brand"] == "Helix" and p["status"] == "ongoing" for p in listed)


def test_generate_rejects_empty():
    res = client.post("/api/generate", data={"pasted": ""})
    assert res.status_code == 400


def test_generate_rejects_demo_mode():
    res = client.post(
        "/api/generate",
        data={"pasted": "brand: Helix\ntherapy_area: Oncology\n", "mode": "demo"},
    )
    assert res.status_code == 400
