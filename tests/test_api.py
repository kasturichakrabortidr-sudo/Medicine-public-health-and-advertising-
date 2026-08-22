from fastapi.testclient import TestClient

from director_api.app import app

client = TestClient(app)


def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["ok"] is True
    assert "pdf" in res.json()["accept"]


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
