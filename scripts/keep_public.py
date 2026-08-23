#!/usr/bin/env python3
"""Keep a public URL in front of the local STRATA app while this machine is up.

Cloudflare quick tunnels (*.trycloudflare.com) have no uptime guarantee. The
hostname also changes if cloudflared restarts. That is why a shared workbench
link goes dead.

A named Cloudflare tunnel token (CLOUDFLARE_TUNNEL_TOKEN) keeps one hostname
across restarts. For a link people can use at all times, run Docker on a host
you control and set PUBLIC_BASE_URL to that domain — this script is not a
substitute for that.
"""

from __future__ import annotations

import os
import re
import shutil
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
URL_FILE = ROOT / ".strata-public-url"
PID_FILE = Path("/tmp/strata-tunnel.pid")
LOG_FILE = Path("/tmp/strata-public.log")
APP = os.environ.get("STRATA_APP_URL", "http://127.0.0.1:8080").rstrip("/")
URL_RE = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com", re.I)
BIN_CANDIDATES = [
    Path.home() / ".local/bin/cloudflared",
    Path("/usr/local/bin/cloudflared"),
    Path("/tmp/cloudflared"),
]


def log(msg: str) -> None:
    line = time.strftime("%Y-%m-%dT%H:%M:%SZ ", time.gmtime()) + msg
    print(line, flush=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def http_ok(url: str, timeout: float = 12) -> bool:
    req = urllib.request.Request(url, headers={"User-Agent": "STRATA-public-keeper/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return 200 <= resp.status < 400
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def tunnel_connected(text: str) -> bool:
    """True when cloudflared last registered a connector, not when it last failed."""
    registered = text.rfind("Registered tunnel connection")
    if registered < 0:
        return False
    failed = max(text.rfind("Serve tunnel error"), text.rfind("failed to serve tunnel connection"))
    return registered > failed


def read_url() -> str:
    if URL_FILE.is_file():
        text = URL_FILE.read_text(encoding="utf-8").strip().split()
        if text and text[0].startswith("http"):
            return text[0]
    return ""


def write_url(url: str) -> None:
    URL_FILE.write_text(url.rstrip("/") + "\n", encoding="utf-8")
    Path("/tmp/strata-public-url.txt").write_text(url.rstrip("/") + "\n", encoding="utf-8")
    artifacts = Path("/opt/cursor/artifacts")
    if artifacts.is_dir():
        (artifacts / "public_share_url.txt").write_text(url.rstrip("/") + "\n", encoding="utf-8")


def find_cloudflared() -> str:
    token = os.environ.get("CLOUDFLARE_TUNNEL_TOKEN", "").strip()
    for path in BIN_CANDIDATES:
        if path.is_file() and os.access(path, os.X_OK):
            stable = Path.home() / ".local/bin/cloudflared"
            if path != stable:
                stable.parent.mkdir(parents=True, exist_ok=True)
                if not stable.is_file():
                    shutil.copy2(path, stable)
                    stable.chmod(0o755)
                    return str(stable)
            return str(path)
    which = shutil.which("cloudflared")
    if which:
        return which
    raise SystemExit(
        "cloudflared is not installed. Download it from "
        "https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/"
        + (" A named-tunnel token is set; install the binary and rerun." if token else "")
    )


def tunnel_pid() -> int | None:
    if not PID_FILE.is_file():
        return None
    try:
        pid = int(PID_FILE.read_text(encoding="utf-8").strip())
    except ValueError:
        return None
    try:
        os.kill(pid, 0)
    except OSError:
        return None
    return pid


def stop_tunnel() -> None:
    pid = tunnel_pid()
    if not pid:
        return
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        pass
    for _ in range(20):
        try:
            os.kill(pid, 0)
        except OSError:
            break
        time.sleep(0.15)
    else:
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass
    PID_FILE.unlink(missing_ok=True)


def start_tunnel() -> str:
    binary = find_cloudflared()
    token = os.environ.get("CLOUDFLARE_TUNNEL_TOKEN", "").strip()
    named_host = (os.environ.get("CLOUDFLARE_TUNNEL_HOST") or "").rstrip("/")
    stop_tunnel()
    if token:
        cmd = [binary, "tunnel", "--no-autoupdate", "run", "--token", token]
    else:
        cmd = [
            binary,
            "tunnel",
            "--url",
            APP,
            "--no-autoupdate",
            "--protocol",
            "http2",
            "--ha-connections",
            "4",
        ]
    log_path = Path("/tmp/cloudflared-public.log")
    log_path.write_text("", encoding="utf-8")
    fh = log_path.open("w", encoding="utf-8")
    proc = subprocess.Popen(cmd, stdout=fh, stderr=subprocess.STDOUT, start_new_session=True)
    PID_FILE.write_text(str(proc.pid), encoding="utf-8")
    log(f"started cloudflared pid={proc.pid} named={bool(token)}")
    if token and named_host:
        write_url(named_host if named_host.startswith("http") else f"https://{named_host}")
        return read_url()
    deadline = time.time() + 40
    while time.time() < deadline:
        text = log_path.read_text(encoding="utf-8", errors="replace")
        match = URL_RE.search(text)
        if match:
            url = match.group(0).rstrip("/")
            write_url(url)
            log(f"public url {url}")
            return url
        if proc.poll() is not None:
            log(f"cloudflared exited early: {text[-400:]}")
            break
        time.sleep(0.4)
    raise RuntimeError("cloudflared started but no public hostname appeared")


def connector_ok() -> bool:
    if not tunnel_pid():
        return False
    log_path = Path("/tmp/cloudflared-public.log")
    if not log_path.is_file():
        return False
    return tunnel_connected(log_path.read_text(encoding="utf-8", errors="replace"))


def main() -> int:
    os.chdir(ROOT)
    while not http_ok(f"{APP}/api/health"):
        log(f"waiting for local app at {APP}/api/health")
        time.sleep(2)
    misses = 0
    while True:
        url = read_url()
        if connector_ok() and url:
            misses = 0
            time.sleep(20)
            continue
        misses += 1
        log(f"connector check failed url={url or '-'} pid={tunnel_pid() or '-'} misses={misses}")
        if misses < 2 and tunnel_pid():
            time.sleep(8)
            continue
        try:
            url = start_tunnel()
        except Exception as exc:
            log(f"tunnel restart failed: {exc}")
            time.sleep(12)
            continue
        if connector_ok():
            misses = 0
            log(f"share is live {url}")
        else:
            time.sleep(8)
    return 0


if __name__ == "__main__":
    sys.exit(main())
