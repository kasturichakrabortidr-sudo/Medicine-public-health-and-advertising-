"""Launch the STRATA Strategy Director (API + web app) on one URL."""

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
APP_PORT = int(os.environ.get("STRATA_PORT", "8080"))


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


def ensure_web_build() -> None:
    ensure_node_deps()
    index = WEB / "dist" / "index.html"
    if index.exists():
        return
    print("Building the web app (one-time)...")
    subprocess.check_call(["npm", "run", "build"], cwd=str(WEB))


def main() -> None:
    ensure_python_deps()
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    dev = "--dev" in sys.argv

    if dev:
        ensure_node_deps()
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
        web = run(
            ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", str(WEB_PORT)],
            cwd=WEB,
            env=env,
        )
        url = f"http://127.0.0.1:{WEB_PORT}"
        procs = [api, web]
    else:
        ensure_web_build()
        api = run(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "director_api.app:app",
                "--host",
                "0.0.0.0",
                "--port",
                str(APP_PORT),
            ],
            env=env,
        )
        url = f"http://127.0.0.1:{APP_PORT}"
        procs = [api]
        web = None

    print(f"\nSTRATA is up.\n  Open this link:  {url}\n")
    time.sleep(1.5)
    if shutil.which("xdg-open") or sys.platform in {"darwin", "win32"}:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    try:
        while True:
            for proc in procs:
                if proc.poll() is not None:
                    print("A STRATA process stopped.")
                    for other in procs:
                        if other.poll() is None:
                            other.terminate()
                    sys.exit(proc.returncode or 1)
            time.sleep(0.4)
    except KeyboardInterrupt:
        for proc in procs:
            proc.terminate()


if __name__ == "__main__":
    main()
