"""Optional multi-provider ensemble for slide titles.

Story, Visuals, Copy, and Critic already directed the pack. This module
only seasons headlines when STRATA_DECK_AI is on and at least one provider
key is present. It never invents numbers, trials, HRs, or PMIDs.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from .deck_visuals import line, sentence


def polish_story(story: dict[str, Any], brief: Any, doctrine: dict) -> dict[str, Any]:
    """Kept for interpret_plan. Title seasoning happens in ensemble_titles."""
    return story


def ensemble_titles(slides: list[dict], story: dict) -> list[dict]:
    if os.environ.get("STRATA_DECK_AI", "").lower() not in {"1", "on", "true"}:
        return slides
    providers = _providers()
    if not providers:
        return slides
    payload = {
        "headline": story.get("headline"),
        "need": story.get("need"),
        "enemy": story.get("enemy"),
        "titles": {s.get("id"): s.get("title") for s in slides if s.get("id") != "references"},
    }
    votes: list[dict] = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futs = [pool.submit(_call, spec, payload) for spec in providers]
        for fut in as_completed(futs):
            try:
                parsed = fut.result()
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, ValueError, OSError):
                parsed = None
            if parsed:
                votes.append(parsed)
    if not votes:
        return slides
    merged = votes[0]
    for extra in votes[1:]:
        for key, value in extra.items():
            if key not in merged and value:
                merged[key] = value
    by_id = {s.get("id"): s for s in slides}
    for sid, title in (merged.get("titles") or merged).items():
        if sid in by_id and isinstance(title, str) and title.strip():
            cleaned = line(title.replace("…", "").replace("...", ""))
            if cleaned and "[" not in cleaned:
                by_id[sid]["title"] = cleaned if not _looks_sentence(cleaned) else sentence(cleaned).rstrip(".") + ("" if cleaned.endswith((".", "!", "?")) else ".")
    return slides


def _looks_sentence(text: str) -> bool:
    words = text.split()
    return bool(words) and words[0][:1].isupper() and " " in text


def _providers() -> list[dict]:
    out = []
    if os.environ.get("OPENAI_API_KEY"):
        out.append({
            "name": "openai",
            "url": (os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/") + "/chat/completions",
            "key": os.environ["OPENAI_API_KEY"],
            "model": os.environ.get("STRATA_DECK_MODEL") or "gpt-4o-mini",
            "kind": "openai",
        })
    if os.environ.get("ANTHROPIC_API_KEY"):
        out.append({
            "name": "anthropic",
            "url": (os.environ.get("ANTHROPIC_BASE_URL") or "https://api.anthropic.com").rstrip("/") + "/v1/messages",
            "key": os.environ["ANTHROPIC_API_KEY"],
            "model": os.environ.get("STRATA_ANTHROPIC_MODEL") or "claude-sonnet-4-5-20250929",
            "kind": "anthropic",
        })
    if os.environ.get("GEMINI_API_KEY"):
        model = os.environ.get("STRATA_GEMINI_MODEL") or "gemini-2.5-flash"
        out.append({
            "name": "gemini",
            "url": f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={os.environ['GEMINI_API_KEY']}",
            "key": os.environ["GEMINI_API_KEY"],
            "model": model,
            "kind": "gemini",
        })
    return out[:3]


SYSTEM = (
    "You direct a medical-affairs strategy deck. Return JSON {\"titles\": {slideId: title}}. "
    "Each title is a complete conclusion, at most 12 words. Never use ellipses. "
    "Do not add numbers, trial names, HRs, NNTs, or PMIDs that are not already in the input."
)


def _call(spec: dict, payload: dict) -> dict | None:
    if spec["kind"] == "openai":
        body = {
            "model": spec["model"],
            "temperature": 0.2,
            "max_tokens": 500,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": json.dumps(payload)},
            ],
        }
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {spec['key']}"}
    elif spec["kind"] == "anthropic":
        body = {
            "model": spec["model"],
            "max_tokens": 500,
            "temperature": 0.2,
            "system": SYSTEM,
            "messages": [{"role": "user", "content": json.dumps(payload)}],
        }
        headers = {
            "Content-Type": "application/json",
            "x-api-key": spec["key"],
            "anthropic-version": "2023-06-01",
        }
    else:
        body = {
            "contents": [{"parts": [{"text": SYSTEM + "\n" + json.dumps(payload)}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 500},
        }
        headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(
        spec["url"],
        data=json.dumps(body).encode(),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=8) as resp:
        data = json.loads(resp.read().decode())
    text = _extract_text(spec["kind"], data)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < 0:
        return None
    return json.loads(text[start: end + 1])


def _extract_text(kind: str, data: dict) -> str:
    if kind == "openai":
        return data["choices"][0]["message"]["content"]
    if kind == "anthropic":
        return "".join(part.get("text") or "" for part in data.get("content") or [])
    cands = data.get("candidates") or []
    parts = (((cands[0] or {}).get("content") or {}).get("parts") or []) if cands else []
    return "".join(p.get("text") or "" for p in parts)
