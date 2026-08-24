import pytest

from director_api.app import app
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _isolate_projects(tmp_path, monkeypatch):
    monkeypatch.setenv("STRATA_PROJECTS_DIR", str(tmp_path / "projects"))
