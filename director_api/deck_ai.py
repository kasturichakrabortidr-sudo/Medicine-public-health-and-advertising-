"""Optional LLM polish for deck headlines.

Only complete sentences. Never ellipses. Never invented numbers.
Off unless STRATA_DECK_AI is on and a key is present.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from .deck_visuals import sentence


def polish_story(story: dict[str, Any], brief: Any, doctrine: dict) -> dict[str, Any]:
    key = os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    if not key or os.environ.get("STRATA_DECK_AI", "").lower() not in {"1", "on", "true"}:
        return story
    try:
        return _openai_polish(story, doctrine, key) if os.environ.get("OPENAI_API_KEY") else story
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, ValueError):
        return story


def _openai_polish(story: dict, doctrine: dict, key: str) -> dict:
    base = os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1"
    model = os.environ.get("STRATA_DECK_MODEL") or "gpt-4o-mini"
    prompt = {
        "model": model,
        "temperature": 0.2,
        "max_tokens": 280,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You write slide headlines for a medical-affairs strategy deck. "
                    "Return JSON with keys headline, need. Each must be a complete sentence. "
                    "Never use ellipses. Never cut a clause. Do not add numbers, trial names, "
                    "or claims that are not in the input."
                ),
            },
            {
                "role": "user",
                "content": json.dumps({
                    "headline": story.get("headline"),
                    "need": story.get("need"),
                    "enemy": story.get("enemy"),
                    "doctrine": doctrine.get("name"),
                }),
            },
        ],
    }
    req = urllib.request.Request(
        f"{base.rstrip('/')}/chat/completions",
        data=json.dumps(prompt).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=8) as resp:
        data = json.loads(resp.read().decode())
    text = data["choices"][0]["message"]["content"]
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < 0:
        return story
    parsed = json.loads(text[start: end + 1])
    if parsed.get("headline"):
        story["headline"] = sentence(parsed["headline"])
    if parsed.get("need"):
        story["need"] = sentence(parsed["need"])
    return story
