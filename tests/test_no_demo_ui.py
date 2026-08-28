from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "web" / "src" / "App.tsx"
API = Path(__file__).resolve().parents[1] / "web" / "src" / "api.ts"


def test_app_does_not_autoload_cardioshield():
    app = APP.read_text(encoding="utf-8")
    api = API.read_text(encoding="utf-8")
    assert "CardioShield" not in app
    assert "fetchDemo" not in app
    assert "fetchDemo" not in api
    assert 'useState<TabId>("briefs")' in app
    assert "ProjectsTab" in app
    assert "/api/demo" not in api
    assert "/demo.json" not in api
