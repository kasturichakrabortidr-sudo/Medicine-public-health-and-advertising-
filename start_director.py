"""Launch the STRATA Strategy Director (API + web app)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
API_PORT = 8787
WEB_PORT = 5173


def run(cmd: list[str], cwd: Path | None = None, env: dict | None = None) -> subprocess.Popen:
    return subprocess.Popen(cmd, cwd=str(cwd or ROOT), env=env)


def ensure_python_deps() -> None:
    try:
        import fastapi  # noqa: F401
        import uvicorn  # noqa: F401
        import yaml  # noqa: F401
    except ImportError:
        print("Installing Python dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(ROOT / "requirements.txt")])


def ensure_node_deps() -> None:
    if not (WEB / "node_modules").exists():
        print("Installing web dependencies...")
        subprocess.check_call(["npm", "install"], cwd=str(WEB))


def main() -> None:
    ensure_python_deps()
    ensure_node_deps()

    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")

    api = run(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "director_api.app:app",
            "--host",
            "0.0.0.0",
            "--port",
            str(API_PORT),
        ],
        env=env,
    )
    web_cmd = ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", str(WEB_PORT)]
    web = run(web_cmd, cwd=WEB, env=env)

    url = f"http://127.0.0.1:{WEB_PORT}"
    print(f"\nSTRATA is up.\n  App   {url}\n  API   http://127.0.0.1:{API_PORT}/api/health\n")
    time.sleep(1.5)
    if shutil.which("xdg-open") or sys.platform in {"darwin", "win32"}:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    try:
        while True:
            if api.poll() is not None:
                print("API stopped.")
                web.terminate()
                sys.exit(api.returncode or 1)
            if web.poll() is not None:
                print("Web stopped.")
                api.terminate()
                sys.exit(web.returncode or 1)
            time.sleep(0.4)
    except KeyboardInterrupt:
        api.terminate()
        web.terminate()


if __name__ == "__main__":
    main()
