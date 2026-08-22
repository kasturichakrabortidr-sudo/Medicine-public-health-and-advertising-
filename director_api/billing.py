"""Credit wallets and paid plans.

Free, Practice, and Agency are monthly allowances. Stripe Checkout buys a
plan or a one-time credit pack. The wallet is the source of truth for spend.
"""

from __future__ import annotations

import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

COOKIE = "strata_wallet"

ACTIONS = {
    "write_file": {"credits": 8, "label": "Write a working file"},
    "export_pptx": {"credits": 3, "label": "Download PPTX"},
}

PLANS = {
    "free": {
        "id": "free",
        "name": "Free",
        "price": 0,
        "priceLabel": "$0",
        "interval": "month",
        "credits": 20,
        "kind": "allowance",
        "blurb": "Read a brief and write one working file.",
        "includes": [
            "20 credits each month",
            "Write a working file (8 credits)",
            "CardioShield demo is free",
            "PPTX export (3 credits)",
        ],
    },
    "practice": {
        "id": "practice",
        "name": "Practice",
        "price": 4900,
        "priceLabel": "$49",
        "interval": "month",
        "credits": 200,
        "kind": "subscription",
        "blurb": "For one brand team shipping a launch deck.",
        "includes": [
            "200 credits each month",
            "About 25 working files",
            "PPTX for every pack",
            "Keep leftover credits until you spend them",
        ],
    },
    "agency": {
        "id": "agency",
        "name": "Agency",
        "price": 19900,
        "priceLabel": "$199",
        "interval": "month",
        "credits": 1000,
        "kind": "subscription",
        "blurb": "For several brands in the same month.",
        "includes": [
            "1,000 credits each month",
            "About 125 working files",
            "Priority for multi-brand work",
            "Customer portal to change or cancel",
        ],
    },
}

PACKS = {
    "credits_50": {
        "id": "credits_50",
        "name": "50 credits",
        "price": 1900,
        "priceLabel": "$19",
        "credits": 50,
        "kind": "pack",
        "blurb": "A one-time top-up. It does not renew.",
        "includes": ["50 credits added now", "Use them on any paid action"],
    },
}


class BillingError(Exception):
    def __init__(self, message: str, *, status: int = 402, payload: dict | None = None):
        super().__init__(message)
        self.status = status
        self.payload = payload or {"message": message}


def _root() -> Path:
    env = os.environ.get("STRATA_WALLETS_DIR")
    path = Path(env) if env else Path(__file__).resolve().parent.parent / "data" / "wallets"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _path(wid: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9._-]", "", wid)[:80]
    if not safe:
        raise ValueError("Invalid wallet id")
    return _root() / f"{safe}.json"


def free_credits() -> int:
    try:
        return max(0, int(os.environ.get("STRATA_FREE_CREDITS") or PLANS["free"]["credits"]))
    except ValueError:
        return int(PLANS["free"]["credits"])


def catalog() -> dict:
    return {
        "plans": list(PLANS.values()),
        "packs": list(PACKS.values()),
        "actions": ACTIONS,
        "stripe": bool((os.environ.get("STRIPE_SECRET_KEY") or "").strip()),
        "sandbox": not bool((os.environ.get("STRIPE_SECRET_KEY") or "").strip()),
    }


def _blank(wid: str) -> dict:
    return {
        "id": wid,
        "email": "",
        "plan": "free",
        "credits": free_credits(),
        "granted": free_credits(),
        "stripeCustomerId": "",
        "stripeSubscriptionId": "",
        "periodEnd": "",
        "createdAt": _now(),
        "updatedAt": _now(),
        "ledger": [
            {
                "at": _now(),
                "action": "grant",
                "credits": free_credits(),
                "note": "Free monthly allowance",
            }
        ],
    }


def load_wallet(wid: str | None) -> dict:
    if not wid:
        return _blank(str(uuid.uuid4()))
    path = _path(wid)
    if not path.is_file():
        wallet = _blank(wid)
        save_wallet(wallet)
        return wallet
    try:
        wallet = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        wallet = _blank(wid)
        save_wallet(wallet)
        return wallet
    if not isinstance(wallet, dict) or not wallet.get("id"):
        wallet = _blank(wid)
        save_wallet(wallet)
    return wallet


def save_wallet(wallet: dict) -> dict:
    wallet["updatedAt"] = _now()
    path = _path(str(wallet["id"]))
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(wallet, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)
    return wallet


def public_wallet(wallet: dict) -> dict:
    plan = PLANS.get(wallet.get("plan") or "free") or PLANS["free"]
    return {
        "id": wallet["id"],
        "email": wallet.get("email") or "",
        "plan": plan["id"],
        "planName": plan["name"],
        "credits": int(wallet.get("credits") or 0),
        "granted": int(wallet.get("granted") or 0),
        "periodEnd": wallet.get("periodEnd") or "",
        "hasCustomer": bool(wallet.get("stripeCustomerId")),
        "stripe": bool((os.environ.get("STRIPE_SECRET_KEY") or "").strip()),
        "sandbox": not bool((os.environ.get("STRIPE_SECRET_KEY") or "").strip()),
        "actions": ACTIONS,
        "ledger": list(wallet.get("ledger") or [])[-8:],
    }


def _append(wallet: dict, action: str, credits: int, note: str, extra: dict | None = None) -> None:
    row = {"at": _now(), "action": action, "credits": credits, "note": note}
    if extra:
        row.update(extra)
    ledger = list(wallet.get("ledger") or [])
    ledger.append(row)
    wallet["ledger"] = ledger[-40:]


def grant(wallet: dict, credits: int, note: str, *, plan: str | None = None, extra: dict | None = None) -> dict:
    wallet["credits"] = int(wallet.get("credits") or 0) + max(0, int(credits))
    if plan and plan in PLANS:
        wallet["plan"] = plan
        wallet["granted"] = int(PLANS[plan]["credits"])
    _append(wallet, "grant", int(credits), note, extra)
    return save_wallet(wallet)


def spend(wallet: dict, action: str) -> dict:
    spec = ACTIONS.get(action)
    if not spec:
        raise BillingError(f"Unknown paid action: {action}", status=400)
    cost = int(spec["credits"])
    remaining = int(wallet.get("credits") or 0)
    if remaining < cost:
        raise BillingError(
            f"{spec['label']} costs {cost} credits. You have {remaining} left.",
            status=402,
            payload={
                "error": "not_enough_credits",
                "message": f"{spec['label']} costs {cost} credits. You have {remaining} left.",
                "action": action,
                "needed": cost,
                "remaining": remaining,
                "plan": wallet.get("plan") or "free",
            },
        )
    wallet["credits"] = remaining - cost
    _append(wallet, action, -cost, spec["label"])
    return save_wallet(wallet)


def apply_subscription(wallet: dict, plan_id: str, *, email: str = "", customer: str = "", subscription: str = "", invoice: str = "") -> dict:
    plan = PLANS.get(plan_id)
    if not plan or plan["kind"] != "subscription":
        raise BillingError("Unknown paid plan.", status=400)
    if invoice and any(row.get("invoice") == invoice for row in (wallet.get("ledger") or [])):
        return wallet
    if email:
        wallet["email"] = email
    if customer:
        wallet["stripeCustomerId"] = customer
    if subscription:
        wallet["stripeSubscriptionId"] = subscription
    return grant(
        wallet,
        int(plan["credits"]),
        f"{plan['name']} monthly credits",
        plan=plan_id,
        extra={"invoice": invoice} if invoice else None,
    )


def apply_pack(wallet: dict, pack_id: str, *, email: str = "", customer: str = "", payment: str = "") -> dict:
    pack = PACKS.get(pack_id)
    if not pack:
        raise BillingError("Unknown credit pack.", status=400)
    if payment and any(row.get("payment") == payment for row in (wallet.get("ledger") or [])):
        return wallet
    if email:
        wallet["email"] = email
    if customer:
        wallet["stripeCustomerId"] = customer
    return grant(
        wallet,
        int(pack["credits"]),
        f"{pack['name']} top-up",
        extra={"payment": payment} if payment else None,
    )


def cancel_subscription(wallet: dict) -> dict:
    wallet["plan"] = "free"
    wallet["stripeSubscriptionId"] = ""
    _append(wallet, "cancel", 0, "Subscription ended. Leftover credits stay.")
    return save_wallet(wallet)
