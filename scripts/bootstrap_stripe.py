"""Create STRATA Billing products and a webhook on the connected Stripe account.

Reads keys from the environment. Prints price ids only — never keys.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from director_api.stripe_billing import PACKS, PLANS, _catalog_path, _client, _load_catalog, _save_catalog, ensure_price


def main() -> None:
    if not (os.environ.get("STRIPE_SECRET_KEY") or "").strip():
        raise SystemExit("STRIPE_SECRET_KEY is not set")
    ids = {}
    for item in ("practice", "agency", "credits_50"):
        ids[item] = ensure_price(item)
        print(f"{item} {ids[item]}")
    catalog = _load_catalog()
    catalog.update(ids)
    _save_catalog(catalog)
    print(f"catalog {_catalog_path()}")

    url = (os.environ.get("PUBLIC_BASE_URL") or "").rstrip("/")
    if url:
        client = _client()
        hook_url = f"{url}/api/billing/webhook"
        existing = client.v1.webhook_endpoints.list(params={"limit": 20})
        data = existing.data if hasattr(existing, "data") else []
        found = next((h for h in data if getattr(h, "url", "") == hook_url), None)
        if found:
            print(f"webhook exists {found.id}")
        else:
            hook = client.v1.webhook_endpoints.create(
                params={
                    "url": hook_url,
                    "enabled_events": [
                        "checkout.session.completed",
                        "invoice.paid",
                        "invoice.payment_failed",
                        "customer.subscription.deleted",
                    ],
                    "description": "STRATA credits",
                }
            )
            secret = getattr(hook, "secret", None)
            print(f"webhook {hook.id}")
            if secret:
                env_path = ROOT / ".env"
                text = env_path.read_text(encoding="utf-8") if env_path.is_file() else ""
                if "STRIPE_WEBHOOK_SECRET=" in text:
                    lines = []
                    for line in text.splitlines():
                        if line.startswith("STRIPE_WEBHOOK_SECRET="):
                            lines.append(f"STRIPE_WEBHOOK_SECRET={secret}")
                        else:
                            lines.append(line)
                    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
                else:
                    with env_path.open("a", encoding="utf-8") as fh:
                        fh.write(f"STRIPE_WEBHOOK_SECRET={secret}\n")
                print("webhook secret written to .env")


if __name__ == "__main__":
    # Local import after path setup; silence unused-plan warning
    _ = (PLANS, PACKS)
    main()
