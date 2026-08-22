"""Stripe Checkout and Customer Portal for STRATA plans.

One Product per plan. Credits are an application allowance, not a Stripe meter.
Do not enable automatic_tax until a registration exists.
"""

from __future__ import annotations

import json
import os
import secrets
from pathlib import Path

import stripe

from .billing import PACKS, PLANS, apply_pack, apply_subscription, cancel_subscription, load_wallet

API_VERSION = "2026-07-29.dahlia"


def configured() -> bool:
    return bool((os.environ.get("STRIPE_SECRET_KEY") or "").strip())


def _client() -> stripe.StripeClient:
    key = (os.environ.get("STRIPE_SECRET_KEY") or "").strip()
    if not key:
        raise RuntimeError("STRIPE_SECRET_KEY is not set")
    return stripe.StripeClient(key, stripe_version=API_VERSION)


def _catalog_path() -> Path:
    env = os.environ.get("STRATA_STRIPE_CATALOG")
    return Path(env) if env else Path(__file__).resolve().parent.parent / "data" / "stripe_catalog.json"


def _load_catalog() -> dict:
    path = _catalog_path()
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _save_catalog(data: dict) -> None:
    path = _catalog_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)


def _price_env(item_id: str) -> str:
    return (os.environ.get(f"STRIPE_PRICE_{item_id.upper()}") or "").strip()


def ensure_price(item_id: str) -> str:
    env_id = _price_env(item_id)
    if env_id:
        return env_id
    catalog = _load_catalog()
    if catalog.get(item_id):
        return str(catalog[item_id])
    spec = PLANS.get(item_id) or PACKS.get(item_id)
    if not spec:
        raise ValueError(f"Unknown catalog item {item_id}")
    client = _client()
    product = client.v1.products.create(
        params={
            "name": f"STRATA {spec['name']}",
            "description": spec["blurb"],
            "tax_code": "txcd_10103001",
            "metadata": {"plan": item_id, "credits": str(spec["credits"])},
        }
    )
    price_params = {
        "product": product.id,
        "unit_amount": int(spec["price"]),
        "currency": "usd",
        "metadata": {"plan": item_id, "credits": str(spec["credits"])},
    }
    if spec.get("kind") == "subscription":
        price_params["recurring"] = {"interval": "month"}
    price = client.v1.prices.create(params=price_params)
    catalog[item_id] = price.id
    _save_catalog(catalog)
    return price.id


def _base_url(request_base: str) -> str:
    return (os.environ.get("PUBLIC_BASE_URL") or request_base or "http://127.0.0.1:8080").rstrip("/")


def start_checkout(wallet: dict, item_id: str, request_base: str) -> dict:
    spec = PLANS.get(item_id) or PACKS.get(item_id)
    if not spec or spec.get("kind") == "allowance":
        raise ValueError("Pick Practice, Agency, or a credit pack.")
    if not configured():
        raise RuntimeError("Stripe is not configured")
    price_id = ensure_price(item_id)
    client = _client()
    mode = "subscription" if spec.get("kind") == "subscription" else "payment"
    params = {
        "mode": mode,
        "line_items": [{"price": price_id, "quantity": 1}],
        "success_url": f"{_base_url(request_base)}/?billing=success&session_id={{CHECKOUT_SESSION_ID}}",
        "cancel_url": f"{_base_url(request_base)}/?billing=cancel",
        "client_reference_id": wallet["id"],
        "metadata": {"wallet": wallet["id"], "item": item_id},
        "allow_promotion_codes": True,
        "billing_address_collection": "auto",
    }
    if wallet.get("email"):
        params["customer_email"] = wallet["email"]
    if wallet.get("stripeCustomerId"):
        params["customer"] = wallet["stripeCustomerId"]
        params.pop("customer_email", None)
        params["customer_update"] = {"address": "auto", "name": "auto"}
    if mode == "subscription":
        params["subscription_data"] = {"metadata": {"wallet": wallet["id"], "item": item_id}}
    else:
        if not wallet.get("stripeCustomerId"):
            params["customer_creation"] = "always"
        params["invoice_creation"] = {
            "enabled": True,
            "invoice_data": {
                "description": f"STRATA {spec['name']}",
                "metadata": {"wallet": wallet["id"], "item": item_id},
                "footer": "Credits for HCP medicomarketing strategy work. Demo packs stay free.",
            },
        }
        params["payment_intent_data"] = {"metadata": {"wallet": wallet["id"], "item": item_id}}
    try:
        params["integration_identifier"] = f"strata-credits-{secrets.token_hex(4)}"
        session = client.v1.checkout.sessions.create(params=params)
    except stripe.InvalidRequestError:
        params.pop("integration_identifier", None)
        session = client.v1.checkout.sessions.create(params=params)
    return {"url": session.url, "id": session.id}


def start_portal(wallet: dict, request_base: str) -> dict:
    if not wallet.get("stripeCustomerId"):
        raise RuntimeError("No Stripe customer on this wallet yet.")
    client = _client()
    session = client.v1.billing_portal.sessions.create(
        params={
            "customer": wallet["stripeCustomerId"],
            "return_url": f"{_base_url(request_base)}/?billing=portal",
        }
    )
    return {"url": session.url}


def _session_payload(session) -> dict:
    details = getattr(session, "customer_details", None)
    email = ""
    if details is not None:
        email = getattr(details, "email", None) or ""
    meta = session.metadata if getattr(session, "metadata", None) is not None else {}
    if hasattr(meta, "to_dict"):
        meta = meta.to_dict()
    return {
        "id": getattr(session, "id", None),
        "status": getattr(session, "status", None),
        "payment_status": getattr(session, "payment_status", None),
        "metadata": dict(meta or {}),
        "client_reference_id": getattr(session, "client_reference_id", None),
        "customer": getattr(session, "customer", None),
        "customer_email": getattr(session, "customer_email", None) or email,
        "customer_details": {"email": email},
        "subscription": getattr(session, "subscription", None),
        "invoice": getattr(session, "invoice", None),
        "payment_intent": getattr(session, "payment_intent", None),
    }


def claim_session(session_id: str) -> dict | None:
    if not session_id or not session_id.startswith("cs_"):
        raise ValueError("A Checkout session id is required.")
    client = _client()
    session = client.v1.checkout.sessions.retrieve(session_id)
    payload = _session_payload(session)
    if payload.get("status") != "complete" and payload.get("payment_status") not in {
        "paid",
        "no_payment_required",
    }:
        raise RuntimeError("Checkout is not complete yet.")
    return apply_checkout_session(payload)


def apply_checkout_session(session: dict) -> dict | None:
    meta = session.get("metadata") or {}
    wallet_id = meta.get("wallet") or session.get("client_reference_id")
    item = meta.get("item") or ""
    if not wallet_id:
        return None
    wallet = load_wallet(str(wallet_id))
    email = (session.get("customer_details") or {}).get("email") or session.get("customer_email") or ""
    customer = session.get("customer") or ""
    if item in PLANS:
        return apply_subscription(
            wallet,
            item,
            email=email,
            customer=str(customer or ""),
            subscription=str(session.get("subscription") or ""),
            invoice=str(session.get("invoice") or ""),
        )
    if item in PACKS:
        return apply_pack(
            wallet,
            item,
            email=email,
            customer=str(customer or ""),
            payment=str(session.get("payment_intent") or session.get("id") or ""),
        )
    return wallet


def apply_invoice(invoice: dict) -> dict | None:
    billing_reason = invoice.get("billing_reason") or ""
    if billing_reason == "subscription_create":
        return None
    sub = invoice.get("subscription") or ""
    customer = invoice.get("customer") or ""
    wallet = _wallet_by_customer(str(customer), str(sub))
    if not wallet:
        return None
    plan_id = wallet.get("plan") if wallet.get("plan") in ("practice", "agency") else "practice"
    parent = invoice.get("parent") or {}
    sub_details = (parent.get("subscription_details") or {}) if isinstance(parent, dict) else {}
    meta = sub_details.get("metadata") or invoice.get("subscription_details") or {}
    if isinstance(meta, dict) and meta.get("item") in PLANS:
        plan_id = meta["item"]
    return apply_subscription(
        wallet,
        plan_id,
        customer=str(customer or ""),
        subscription=str(sub or wallet.get("stripeSubscriptionId") or ""),
        invoice=str(invoice.get("id") or ""),
    )


def _wallet_by_customer(customer: str, subscription: str) -> dict | None:
    if not customer and not subscription:
        return None
    root = Path(os.environ.get("STRATA_WALLETS_DIR") or Path(__file__).resolve().parent.parent / "data" / "wallets")
    if not root.is_dir():
        return None
    for path in root.glob("*.json"):
        try:
            wallet = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if customer and wallet.get("stripeCustomerId") == customer:
            return wallet
        if subscription and wallet.get("stripeSubscriptionId") == subscription:
            return wallet
    return None


def handle_event(event: dict) -> dict:
    kind = event.get("type") or ""
    obj = (event.get("data") or {}).get("object") or {}
    if kind == "checkout.session.completed":
        wallet = apply_checkout_session(obj)
        return {"ok": True, "handled": kind, "wallet": wallet.get("id") if wallet else None}
    if kind == "invoice.paid":
        wallet = apply_invoice(obj)
        return {"ok": True, "handled": kind, "wallet": wallet.get("id") if wallet else None}
    if kind == "invoice.payment_failed":
        wallet = _wallet_by_customer(str(obj.get("customer") or ""), str(obj.get("subscription") or ""))
        if wallet:
            from .billing import note as wallet_note
            wallet_note(wallet, "A Stripe invoice failed. Update the card in Manage billing.")
            return {"ok": True, "handled": kind, "wallet": wallet["id"]}
    if kind in {"customer.subscription.deleted", "customer.subscription.canceled"}:
        wallet = _wallet_by_customer(str(obj.get("customer") or ""), str(obj.get("id") or ""))
        if wallet:
            cancel_subscription(wallet)
            return {"ok": True, "handled": kind, "wallet": wallet["id"]}
    return {"ok": True, "handled": kind or "ignored"}


def parse_webhook(payload: bytes, signature: str) -> dict:
    secret = (os.environ.get("STRIPE_WEBHOOK_SECRET") or "").strip()
    if not secret:
        raise RuntimeError("STRIPE_WEBHOOK_SECRET is not set")
    client = _client()
    event = client.construct_event(payload, signature, secret)
    if hasattr(event, "to_dict"):
        return event.to_dict()
    return dict(event)
