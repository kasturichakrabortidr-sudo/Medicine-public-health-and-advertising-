from pathlib import Path

from scripts.deploy_fly import main as deploy_main


def test_fly_toml_stays_always_on():
    text = Path("fly.toml").read_text(encoding="utf-8")
    assert 'app = "strata-director"' in text
    assert 'auto_stop_machines = "off"' in text
    assert "min_machines_running = 1" in text
    assert 'destination = "/data"' in text


def test_deploy_fly_exits_without_token(monkeypatch):
    monkeypatch.delenv("FLY_API_TOKEN", raising=False)
    assert deploy_main() == 2
