#!/usr/bin/env python3
"""Create or update the always-on Fly.io host for STRATA.

Needs FLY_API_TOKEN. Copies Stripe keys already in this environment onto the
Fly app, deploys the Docker image, and points Checkout + the webhook at
https://<app>.fly.dev.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_APP = "strata-director"
REGION = os.environ.get("FLY_REGION", "iad").strip() or "iad"


def run(cmd: list[str], *, secret: bool = False, check: bool = True) -> subprocess.CompletedProcess:
    print("+ " + (cmd[0] if secret else " ".join(cmd)), flush=True)
    return subprocess.run(cmd, cwd=str(ROOT), check=check, text=True)


def capture(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(ROOT), text=True, capture_output=True)


def flyctl() -> str:
    for name in ("fly", "flyctl"):
        path = shutil.which(name)
        if path:
            return path
    home = Path.home() / ".fly" / "bin" / "flyctl"
    if home.is_file():
        return str(home)
    print("Installing flyctl…", flush=True)
    subprocess.check_call("curl -fsSL https://fly.io/install.sh | sh", shell=True)
    home = Path.home() / ".fly" / "bin" / "flyctl"
    if not home.is_file():
        raise SystemExit("flyctl install failed")
    os.environ["PATH"] = str(home.parent) + os.pathsep + os.environ.get("PATH", "")
    return str(home)


def http_ok(url: str) -> bool:
    req = urllib.request.Request(url, headers={"User-Agent": "STRATA-fly-deploy/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return 200 <= resp.status < 400
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def ensure_app(fly: str, wanted: str) -> str:
    listed = capture([fly, "apps", "list"])
    blob = (listed.stdout or "") + (listed.stderr or "")
    if wanted in blob:
        return wanted
    created = capture([fly, "apps", "create", wanted])
    out = (created.stdout or "") + (created.stderr or "")
    if created.returncode == 0 or "already" in out.lower():
        return wanted
    alt = f"{wanted}-{os.getpid() % 10000}"
    print(f"name {wanted} unavailable, using {alt}", flush=True)
    run([fly, "apps", "create", alt])
    return alt


def ensure_volume(fly: str, app: str) -> None:
    listed = capture([fly, "volumes", "list", "-a", app])
    blob = (listed.stdout or "") + (listed.stderr or "")
    if listed.returncode == 0 and "strata_data" in blob:
        return
    run(
        [fly, "volumes", "create", "strata_data", "-a", app, "--region", REGION, "--size", "1", "--yes"],
        check=False,
    )


def main() -> int:
    token = (os.environ.get("FLY_API_TOKEN") or "").strip()
    if not token:
        print(
            "FLY_API_TOKEN is not set. Create a free Fly account, then a token at "
            "https://fly.io/dashboard/personal/tokens and add FLY_API_TOKEN as an "
            "environment secret. I will deploy as soon as it is present.",
            file=sys.stderr,
        )
        return 2
    os.environ["FLY_API_TOKEN"] = token
    os.chdir(ROOT)
    fly = flyctl()
    wanted = (os.environ.get("FLY_APP") or DEFAULT_APP).strip() or DEFAULT_APP
    app = ensure_app(fly, wanted)
    public = f"https://{app}.fly.dev"
    ensure_volume(fly, app)

    secret_pairs = []
    for key in (
        "STRIPE_SECRET_KEY",
        "STRIPE_PUBLISHABLE_KEY",
        "STRIPE_WEBHOOK_SECRET",
        "STRIPE_PRICE_PRACTICE",
        "STRIPE_PRICE_AGENCY",
        "STRIPE_PRICE_CREDITS_50",
    ):
        val = (os.environ.get(key) or "").strip()
        if val:
            secret_pairs.append(f"{key}={val}")
    secret_pairs.append(f"PUBLIC_BASE_URL={public}")
    run([fly, "secrets", "set", "-a", app, *secret_pairs], secret=True)
    run([fly, "deploy", "-a", app, "--ha=false", "--config", str(ROOT / "fly.toml")])

    deadline = time.time() + 180
    while time.time() < deadline:
        if http_ok(f"{public}/api/health"):
            print(f"live {public}", flush=True)
            break
        time.sleep(5)
    else:
        print(f"deployed but health not yet reachable at {public}", file=sys.stderr)
        return 1

    os.environ["PUBLIC_BASE_URL"] = public
    subprocess.check_call([sys.executable, str(ROOT / "scripts" / "bootstrap_stripe.py")], cwd=str(ROOT))
    print(f"share {public}", flush=True)
    (ROOT / ".strata-public-url").write_text(public + "\n", encoding="utf-8")
    artifacts = Path("/opt/cursor/artifacts")
    if artifacts.is_dir():
        (artifacts / "public_share_url.txt").write_text(public + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
