from pathlib import Path

from fastapi.testclient import TestClient

from director_api.app import app

client = TestClient(app)


def test_health_reports_whether_the_website_is_built():
    res = client.get("/api/health")
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["service"] == "strata-director"
    assert "web" in body


def test_live_app_serves_built_website(tmp_path, monkeypatch):
    dist = tmp_path / "dist"
    assets = dist / "assets"
    assets.mkdir(parents=True)
    (dist / "index.html").write_text("<!doctype html><title>STRATA</title><div id='root'>live</div>", encoding="utf-8")
    (assets / "app.js").write_text("window.STRATA='ok'", encoding="utf-8")
    monkeypatch.setenv("STRATA_WEB_DIST", str(dist))

    home = client.get("/")
    assert home.status_code == 200
    assert "STRATA" in home.text

    js = client.get("/assets/app.js")
    assert js.status_code == 200
    assert "STRATA" in js.text

    missing_api = client.get("/api/does-not-exist")
    assert missing_api.status_code == 404
    assert "live" not in missing_api.text


def test_homepage_is_503_until_the_website_is_built(tmp_path, monkeypatch):
    monkeypatch.setenv("STRATA_WEB_DIST", str(tmp_path / "empty-dist"))
    res = client.get("/")
    assert res.status_code == 503
    assert "start_live.py" in res.json()["detail"]
