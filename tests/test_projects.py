from fastapi.testclient import TestClient

from director_api.app import app

client = TestClient(app)


def test_projects_roundtrip_and_pin():
    generated = client.post(
        "/api/generate",
        files=[("files", ("brief.yaml", b"brand: LumenDerm\ntherapy_area: Dermatology\n", "text/yaml"))],
    )
    assert generated.status_code == 200
    pack = generated.json()
    assert pack["meta"]["brand"] == "LumenDerm"
    listed = client.get("/api/projects").json()["projects"]
    ongoing = [p for p in listed if p["status"] == "ongoing" and p["brand"] == "LumenDerm"]
    assert len(ongoing) == 1
    pid = ongoing[0]["id"]

    loaded = client.get(f"/api/projects/{pid}")
    assert loaded.status_code == 200
    assert loaded.json()["pack"]["meta"]["brand"] == "LumenDerm"

    pinned = client.post("/api/projects", json={"id": pid, "status": "saved", "pack": pack})
    assert pinned.status_code == 200
    assert pinned.json()["status"] == "saved"

    again = client.post(
        "/api/generate",
        files=[("files", ("brief.yaml", b"brand: LumenDerm\ntherapy_area: Dermatology\n", "text/yaml"))],
    )
    assert again.status_code == 200
    rows = client.get("/api/projects").json()["projects"]
    assert any(p["id"] == pid and p["status"] == "saved" for p in rows)
    assert any(p["status"] == "ongoing" and p["brand"] == "LumenDerm" and p["id"] != pid for p in rows)

    gone = client.delete(f"/api/projects/{pid}")
    assert gone.status_code == 200
    assert client.get(f"/api/projects/{pid}").status_code == 404


def test_projects_reject_empty_pack():
    res = client.post("/api/projects", json={"status": "saved", "pack": {"meta": {}}})
    assert res.status_code == 400
