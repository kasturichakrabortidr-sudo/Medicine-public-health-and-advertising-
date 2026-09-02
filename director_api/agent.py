"""Director agent — think, then execute, for every workflow step.

The website used to jump straight to a template pack. This agent walks the
same workflow the working file uses: brief → papers → bet → working file →
deck → take. Each step emits a THINK trace from the actual brief and papers,
then EXECUTE runs the tools (PubMed, workfile, deck). If an Anthropic key is
present, a second pass thinks with the model and patches prose only — never
invented HRs, NNTs, or PMIDs.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Callable

from .extract import ExtractedBrief
from .evidence import (
    _campaign_lead,
    _finding_from_abstract,
    _has_published_finding,
    _lead_priority,
    resolve_evidence,
)

Emit = Callable[[dict[str, Any]], None]


def llm_ready() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"))


def llm_model() -> str:
    return os.environ.get("STRATA_MODEL") or "claude-sonnet-4-5"


def run_director(
    brief: ExtractedBrief,
    *,
    mode: str = "director",
    pubmed: bool = True,
    emit: Emit | None = None,
    llm: Any | None = None,
) -> dict[str, Any]:
    """Think, then execute, through the strategy workflow. Returns a pack."""
    from .cite import attach_references
    from .deck import build_client_deck
    from .generate import _bind_science, _dashboard, _doctrine_for, _interventions
    from .workfile import build_workfile

    log: list[dict[str, Any]] = []
    client = llm if llm is not None else (_anthropic_client() if llm_ready() else None)

    def say(kind: str, step: str, title: str, text: str) -> None:
        event = {"type": kind, "step": step, "title": title, "text": text}
        log.append(event)
        if emit:
            emit(event)

    def think(step: str, title: str, heuristic: str) -> None:
        text = heuristic
        if client:
            try:
                richer = _llm_think(client, step, heuristic, brief)
                if richer:
                    text = richer
            except Exception:
                text = heuristic
        say("think", step, title, text)

    think("brief", "01 Brief", _think_brief(brief))
    say(
        "execute",
        "brief",
        "01 Brief",
        f"Locked {brief.brand or 'unnamed brand'} · {brief.therapy_area or 'therapy area'} · "
        f"{(brief.indication or '')[:80] or 'no indication line'}.",
    )

    think("evidence", "03 Papers", _think_evidence_plan(brief, pubmed))
    ledger = resolve_evidence(brief, pubmed=pubmed)
    attach_references(ledger)
    records = list(ledger.get("records") or [])
    catalog = [r for r in records if r.get("matchedFrom") != "pubmed"]
    retrieved = [r for r in records if r.get("matchedFrom") == "pubmed"]
    if retrieved:
        retrieved.sort(key=_lead_priority)
        ledger["records"] = catalog + retrieved
        ledger["lead"] = _campaign_lead(brief, ledger["records"], ledger.get("review"))
        attach_references(ledger)
    lead = ledger.get("lead") or {}
    primary = (lead.get("citations") or [{}])[0]
    say(
        "execute",
        "evidence",
        "03 Papers",
        _execute_evidence_note(ledger, primary),
    )

    think("doctrine", "The bet", _think_doctrine(brief, ledger))
    doctrine = _doctrine_for(brief, ledger)
    _bind_science(doctrine, ledger)
    say(
        "execute",
        "doctrine",
        "The bet",
        f"{doctrine.get('name')}. Enemy: {doctrine.get('enemy')}. Bet: {doctrine.get('bet')}",
    )

    think(
        "workfile",
        "02 Working file",
        "Write eleven phases from the papers versus the habit in the brief. "
        "Uncited brief lines stay Unknown. Do not invent a trial or an effect size.",
    )
    work = build_workfile(brief, doctrine, ledger)
    moves = _interventions(brief, doctrine, ledger)
    say(
        "execute",
        "workfile",
        "02 Working file",
        f"{len(work.get('phases') or [])} phases. {work.get('validatedCount') or 0} numbered papers. "
        f"{work.get('gapCount') or 0} gaps. Cannot-claim: {len(work.get('cannotClaim') or [])}.",
    )

    think(
        "deck",
        "04 Deck",
        "Twelve-slide argument from the working file: problem, bet, science-lead finding, house, "
        "execute, moves, journey, measure, close. Science-lead must be a published finding, not a methods opener.",
    )
    slides = build_client_deck(brief, doctrine, ledger, work, moves)
    say(
        "execute",
        "deck",
        "04 Deck",
        f"{len(slides)} slides. Open: {slides[0].get('title') if slides else '—'}. "
        f"Science-lead: {next((s.get('title') for s in slides if s.get('id') == 'science-lead'), '—')}",
    )

    think(
        "take",
        "05 Take",
        "Assemble the pack the room can take: PPTX, print, working-file markdown. "
        "MLR: no superiority claim the papers did not state.",
    )
    pack = _assemble(brief, doctrine, ledger, work, moves, slides, mode)
    if client:
        think("model", "Director model", f"Thinking with {llm_model()} before patching prose. No new HR, NNT, or PMID.")
        pack = _model_pass(client, brief, pack)
        say("execute", "model", "Director model", "Prose patched. Numbers still only from numbered papers.")
    pack["agent"] = {
        "model": llm_model() if client else "director-workflow",
        "llm": bool(client),
        "log": log,
    }
    say(
        "execute",
        "take",
        "05 Take",
        f"Pack ready for {pack['meta']['brand']}: working file, papers, deck, takeaway.",
    )
    pack["agent"]["log"] = log
    return pack


def _assemble(brief, doctrine, ledger, work, moves, slides, mode) -> dict[str, Any]:
    from datetime import date

    from .generate import _dashboard

    brand = brief.brand or "Unnamed brand"
    return {
        "meta": {
            "brand": brand,
            "product": brief.product or brand,
            "therapyArea": brief.therapy_area or "Specialty care",
            "market": brief.market or "Priority markets",
            "generatedAt": date.today().isoformat(),
            "mode": mode,
            "doctrine": doctrine["name"],
            "angleId": doctrine["id"],
            "campaignLead": (ledger.get("lead") or {}).get("directs"),
        },
        "brief": brief.to_dict(),
        "doctrine": doctrine,
        "evidence": ledger,
        "workfile": work,
        "references": ledger.get("references") or [],
        "slides": slides,
        "interventions": moves,
        "dashboard": _dashboard(brief, doctrine, ledger, work, moves),
        "levels": {
            "brief": {"n": "01", "label": "Brief", "title": brand, "note": brief.business_goal or ""},
            "workfile": {
                "n": "02",
                "label": "Working file",
                "phases": len(work.get("phases") or []),
                "gaps": work.get("gapCount") or 0,
            },
            "papers": {
                "n": "03",
                "label": "Papers",
                "count": len(ledger.get("records") or []),
                "gaps": len(ledger.get("gaps") or []),
            },
            "deck": {"n": "04", "label": "Deck", "slides": len(slides)},
            "take": {"n": "05", "label": "Take", "pptx": True, "markdown": True, "print": True},
        },
    }


def _think_brief(brief: ExtractedBrief) -> str:
    habit = (brief.hcp_insights or ["The brief did not name the HCP habit."])[0]
    goal = brief.business_goal or "No business number in the brief."
    mlr = (brief.constraints or ["No MLR line supplied."])[0]
    return (
        f"Brand is {brief.brand or 'missing'}. Habit: {habit[:160]} "
        f"Goal: {goal[:160]} MLR: {mlr[:120]} "
        "Do not treat the upload as the strategy. The habit and the papers set the bet."
    )


def _think_evidence_plan(brief: ExtractedBrief, pubmed: bool) -> str:
    if not pubmed:
        return "PubMed is off for this run. Use only papers this brief already numbered. Do not invent a trial."
    product = brief.product or brief.brand or "this product"
    return (
        f"Search PubMed for {product} in {brief.indication or brief.therapy_area or 'the indication'}. "
        "A guideline-recommend sentence is not a campaign finding. "
        "Prefer a result clause (reduced / versus / exacerbations) from KRONOS, ETHOS, or class RCTs. "
        "Independent papers stay labelled as class evidence, not as this brand's trial."
    )


def _execute_evidence_note(ledger: dict, primary: dict) -> str:
    n = len(ledger.get("records") or [])
    finding = _finding_from_abstract(primary.get("claim") or "", primary.get("short") or "") or primary.get("claim") or ""
    return (
        f"{n} numbered paper{'s' if n != 1 else ''}. "
        f"Lead {primary.get('short') or 'none'} · PMID {primary.get('pmid') or '—'}. "
        f"{(finding or 'No finding clause on the lead.')[:180]}"
    )


def _think_doctrine(brief: ExtractedBrief, ledger: dict) -> str:
    insights = " ".join(brief.hcp_insights or []).lower()
    if "step-up" in insights or "when dual" in insights or "rescue" in insights:
        return "The brief already named triple-as-rescue. The bet is first-line maintenance, not a late step-up."
    if any(w in insights for w in ("stabilis", "stabiliz", "wait")):
        return "The brief named a wait. The bet is first-eligible start, not another clinic visit."
    if ledger.get("records"):
        return "Papers are on the register. Pick the doctrine from those findings versus the habit, not from a slogan."
    return "No numbered paper yet. Doctrine stays behavioural. Do not lock a scientific lead."


def _anthropic_client():
    try:
        import anthropic

        return anthropic.Anthropic()
    except Exception:
        return None


def _llm_think(client, step: str, heuristic: str, brief: ExtractedBrief) -> str:
    """Short reasoning turn. Returns empty if the model emitted JSON or unsafe prose."""
    prompt = (
        f"THINK about the {step} step of a medicomarketing strategy. Do not execute. "
        "Do not invent a trial, HR, NNT, or PMID. Independent class papers are not this brand's trials.\n"
        f"Brand: {brief.brand or 'missing'}. Indication: {brief.indication or brief.therapy_area or 'missing'}.\n"
        f"Working notes: {heuristic}\n"
        "Reply with 2-4 sentences of reasoning only."
    )
    raw = (_complete(client, prompt, think=False, max_tokens=400) or "").strip()
    if not raw or raw.startswith("{") or raw.startswith("["):
        return ""
    if not _safe_prose(raw, set(), set()):
        return ""
    return raw[:700]


def _model_pass(client, brief: ExtractedBrief, pack: dict[str, Any]) -> dict[str, Any]:
    """Think, then patch headlines/soWhat/bet. Refuse new numbers."""
    allowed_pmids = {str(r.get("pmid")) for r in (pack.get("evidence") or {}).get("records") or [] if r.get("pmid")}
    allowed_nums = _numbers_in(json.dumps(pack.get("evidence") or {}))
    slides = pack.get("slides") or []
    payload = {
        "brand": brief.brand,
        "habit": (brief.hcp_insights or [""])[0],
        "goal": brief.business_goal,
        "doctrine": pack.get("doctrine"),
        "lead": (pack.get("evidence") or {}).get("lead"),
        "slides": [
            {"id": s.get("id"), "title": s.get("title"), "soWhat": s.get("soWhat"), "kicker": s.get("kicker")}
            for s in slides
        ],
    }
    prompt = (
        "You are the STRATA strategy director. THINK about the brief and the numbered papers, "
        "then EXECUTE by returning JSON only.\n"
        "Rules: do not invent HR, NNT, PMID, or trial names. Independent class papers are not "
        "this brand's trials. No superiority vs free-mix. Headlines must fit a slide (max 72 chars) "
        "and end with . ! or ? except title and references.\n"
        "Return JSON: {\"doctrine\": {\"enemy\": \"\", \"bet\": \"\"}, \"slides\": "
        "[{\"id\": \"problem\", \"title\": \"\", \"soWhat\": \"\"}]}\n"
        "Only include slides you are changing. Only use ids from the input.\n\n"
        + json.dumps(payload, ensure_ascii=False)[:12000]
    )
    raw = _complete(client, prompt)
    patch = _extract_json(raw)
    if not isinstance(patch, dict):
        return pack
    doctrine = pack.get("doctrine") or {}
    dpatch = patch.get("doctrine") or {}
    for key in ("enemy", "bet", "name"):
        val = dpatch.get(key)
        if isinstance(val, str) and val.strip() and _safe_prose(val, allowed_pmids, allowed_nums):
            doctrine[key] = val.strip()
    by_id = {s.get("id"): s for s in slides}
    for row in patch.get("slides") or []:
        if not isinstance(row, dict):
            continue
        slide = by_id.get(row.get("id"))
        if not slide:
            continue
        for key in ("title", "soWhat", "narrative", "subtitle"):
            val = row.get(key)
            if isinstance(val, str) and val.strip() and _safe_prose(val, allowed_pmids, allowed_nums):
                if key == "title" and len(val) > 90:
                    continue
                slide[key] = val.strip()
    return pack


def _complete(client, prompt: str, *, think: bool = True, max_tokens: int = 4000) -> str:
    model = llm_model()
    kwargs: dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens,
        "system": (
            "Think before you write. You are a medicomarketing strategy director. "
            "Never invent evidence. JSON only on the execute turn."
        ),
        "messages": [{"role": "user", "content": prompt}],
    }
    try:
        if think:
            kwargs["thinking"] = {"type": "enabled", "budget_tokens": min(2000, max(1024, max_tokens // 2))}
        msg = client.messages.create(**kwargs)
    except Exception:
        kwargs.pop("thinking", None)
        msg = client.messages.create(**kwargs)
    parts = []
    for block in getattr(msg, "content", []) or []:
        if getattr(block, "type", None) == "text":
            parts.append(block.text)
    return "\n".join(parts)


def _extract_json(text: str) -> dict:
    blob = (text or "").strip()
    if "```" in blob:
        blob = re.sub(r"^.*?```(?:json)?\s*", "", blob, flags=re.S)
        blob = re.sub(r"```.*$", "", blob, flags=re.S)
    start, end = blob.find("{"), blob.rfind("}")
    if start < 0 or end <= start:
        return {}
    try:
        data = json.loads(blob[start : end + 1])
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _numbers_in(text: str) -> set[str]:
    return set(re.findall(r"\d+(?:\.\d+)?", text or ""))


def _safe_prose(text: str, pmids: set[str], nums: set[str]) -> bool:
    for pmid in re.findall(r"\b\d{7,8}\b", text):
        if pmid not in pmids:
            return False
    for num in re.findall(r"\b\d+\.\d+\b", text):
        if num not in nums and not re.search(r"\b" + re.escape(num) + r"x\b", text):
            return False
    return "…" not in text
