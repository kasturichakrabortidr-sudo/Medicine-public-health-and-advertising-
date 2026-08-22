import pytest

from director_api.app import app
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _isolate_projects(tmp_path, monkeypatch):
    monkeypatch.setenv("STRATA_PROJECTS_DIR", str(tmp_path / "projects"))
    monkeypatch.setenv("STRATA_WALLETS_DIR", str(tmp_path / "wallets"))
    monkeypatch.setenv("STRATA_STRIPE_CATALOG", str(tmp_path / "stripe_catalog.json"))
    monkeypatch.setenv("STRATA_FREE_CREDITS", "1000")
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    monkeypatch.delenv("STRIPE_WEBHOOK_SECRET", raising=False)
