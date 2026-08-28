"""Polite HTTP helper for public scholarly APIs."""

from __future__ import annotations

import json
import ssl
import time
import urllib.error
import urllib.request
from typing import Any

USER_AGENT = (
    "EvidenceWorkflow/1.4 (academic literature automation; "
    "https://github.com/kasturichakrabortidr-sudo/medicine-public-health-and-advertising-)"
)
_CTX = ssl.create_default_context()


def get_json(url: str, timeout: int = 40, retries: int = 3) -> Any:
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=timeout, context=_CTX) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                return json.loads(raw)
        except urllib.error.HTTPError as exc:
            last_err = exc
            if exc.code in {429, 500, 502, 503, 504} and attempt < retries - 1:
                time.sleep(1.5 * (attempt + 1))
                continue
            raise
        except Exception as exc:  # noqa: BLE001 - network noise is retried
            last_err = exc
            if attempt < retries - 1:
                time.sleep(1.2 * (attempt + 1))
                continue
            raise
    raise last_err or RuntimeError(f"GET failed: {url}")


def head_ok(url: str, timeout: int = 20) -> bool:
    try:
        req = urllib.request.Request(
            url, method="HEAD", headers={"User-Agent": USER_AGENT}
        )
        with urllib.request.urlopen(req, timeout=timeout, context=_CTX) as resp:
            return 200 <= resp.status < 400
    except urllib.error.HTTPError as exc:
        if exc.code in {403, 405}:
            return _get_ok(url, timeout)
        return False
    except Exception:
        return _get_ok(url, timeout)


def _get_ok(url: str, timeout: int) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout, context=_CTX) as resp:
            return 200 <= resp.status < 400
    except Exception:
        return False
