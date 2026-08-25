"""Serve the live STRATA app: one process, website + API.

Use this on a VPS or to preview production locally. Hosted deploys use the
same uvicorn command after Docker builds the website into web/dist.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
DIST = WEB / "dist"
PORT = os.environ.get("PORT", "8080")


def ensure_python_deps() -> None:
    try:
        import fastapi  # noqa: F401
        import uvicorn  # noqa: F401
        import yaml  # noqa: F401
    except ImportError:
        print("Installing Python dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(ROOT / "requirements.txt")])


def ensure_web_build() -> None:
    if (DIST / "index.html").is_file() and (DIST / "assets").is_dir():
        return
    print("Building the website...")
    if not (WEB / "node_modules").exists():
        subprocess.check_call(["npm", "ci" if (WEB / "package-lock.json").exists() else "install"], cwd=str(WEB))
    subprocess.check_call(["npm", "run", "build"], cwd=str(WEB))
    if not (DIST / "index.html").is_file():
        raise SystemExit("Website build failed: web/dist/index.html is missing.")


def main() -> None:
    ensure_python_deps()
    ensure_web_build()
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    print(f"\nSTRATA live server\n  App  http://127.0.0.1:{PORT}\n  API  http://127.0.0.1:{PORT}/api/health\n")
    os.execvpe(
        sys.executable,
        [
            sys.executable,
            "-m",
            "uvicorn",
            "director_api.app:app",
            "--host",
            "0.0.0.0",
            "--port",
            str(PORT),
        ],
        env,
    )


if __name__ == "__main__":
    main()
