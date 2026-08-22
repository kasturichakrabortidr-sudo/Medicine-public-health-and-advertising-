from fastapi.testclient import TestClient

from director_api.app import app
from director_api.billing import apply_subscription, load_wallet, spend, BillingError
from director_api.stripe_billing import apply_checkout_session, claim_session, handle_event


client = TestClient(app)


def test_new_wallet_starts_on_free_plan():
    res = client.get("/api/billing/me")
    assert res.status_code == 200
    body = res.json()
    assert body["plan"] == "free"
    assert body["credits"] == 1000
    assert client.cookies.get("strata_wallet")


def test_catalog_lists_credit_costs():
    res = client.get("/api/billing")
    assert res.status_code == 200
    catalog = res.json()["catalog"]
    assert catalog["actions"]["write_file"]["credits"] == 8
    assert catalog["actions"]["export_pptx"]["credits"] == 3
    names = {p["id"] for p in catalog["plans"]}
    assert names == {"free", "practice", "agency"}


def test_generate_spends_write_credits():
    before = client.get("/api/billing/me").json()["credits"]
    generated = client.post(
        "/api/generate",
        files=[("files", ("brief.yaml", b"brand: Helix\ntherapy_area: Oncology\n", "text/yaml"))],
    )
    assert generated.status_code == 200
    after = generated.json()["meta"]["credits"]["credits"]
    assert after == before - 8


def test_export_demo_pptx_is_free():
    before = client.get("/api/billing/me").json()["credits"]
    pack = client.get("/api/demo").json()
    res = client.post("/api/export/pptx", json=pack)
    assert res.status_code == 200
    after = client.get("/api/billing/me").json()["credits"]
    assert after == before


def test_export_user_pptx_spends_credits():
    pack = client.post(
        "/api/generate",
        files=[("files", ("brief.yaml", b"brand: Helix\ntherapy_area: Oncology\n", "text/yaml"))],
    ).json()
    before = client.get("/api/billing/me").json()["credits"]
    res = client.post("/api/export/pptx", json=pack)
    assert res.status_code == 200
    after = client.get("/api/billing/me").json()["credits"]
    assert after == before - 3


def test_empty_wallet_blocks_generate(tmp_path, monkeypatch):
    monkeypatch.setenv("STRATA_WALLETS_DIR", str(tmp_path / "empty"))
    monkeypatch.setenv("STRATA_FREE_CREDITS", "2")
    local = TestClient(app)
    res = local.post(
        "/api/generate",
        files=[("files", ("brief.yaml", b"brand: Helix\ntherapy_area: Oncology\n", "text/yaml"))],
    )
    assert res.status_code == 402
    assert res.json()["detail"]["needed"] == 8
    assert res.json()["detail"]["remaining"] == 2


def test_sandbox_starts_practice():
    res = client.post("/api/billing/sandbox", json={"item": "practice"})
    assert res.status_code == 200
    wallet = res.json()["wallet"]
    assert wallet["plan"] == "practice"
    assert wallet["credits"] >= 200


def test_checkout_without_stripe_is_explicit():
    res = client.post("/api/billing/checkout", json={"item": "practice"})
    assert res.status_code == 503
    assert res.json()["detail"]["error"] == "stripe_missing"


def test_webhook_checkout_grants_plan(tmp_path, monkeypatch):
    monkeypatch.setenv("STRATA_WALLETS_DIR", str(tmp_path / "wh"))
    wallet = load_wallet("wal_test")
    assert wallet["plan"] == "free"
    apply_checkout_session(
        {
            "metadata": {"wallet": "wal_test", "item": "agency"},
            "customer": "cus_1",
            "subscription": "sub_1",
            "customer_details": {"email": "buyer@example.com"},
        }
    )
    again = load_wallet("wal_test")
    assert again["plan"] == "agency"
    assert again["credits"] >= 1000
    assert again["email"] == "buyer@example.com"


def test_invoice_paid_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setenv("STRATA_WALLETS_DIR", str(tmp_path / "inv"))
    wallet = load_wallet("wal_inv")
    apply_subscription(wallet, "practice", invoice="in_1")
    mid = load_wallet("wal_inv")
    credits = mid["credits"]
    handle_event(
        {
            "type": "invoice.paid",
            "data": {
                "object": {
                    "id": "in_1",
                    "billing_reason": "subscription_cycle",
                    "customer": "",
                    "subscription": "",
                }
            },
        }
    )
    # invoice.paid without a matching customer is ignored; replay of apply_subscription is the lock
    apply_subscription(load_wallet("wal_inv"), "practice", invoice="in_1")
    assert load_wallet("wal_inv")["credits"] == credits


def test_claim_rejects_bad_session_id():
    try:
        claim_session("not-a-session")
        assert False, "should have rejected"
    except ValueError:
        pass


def test_invoice_payment_failed_notes_wallet(tmp_path, monkeypatch):
    monkeypatch.setenv("STRATA_WALLETS_DIR", str(tmp_path / "fail"))
    wallet = load_wallet("wal_fail")
    wallet["stripeCustomerId"] = "cus_fail"
    from director_api.billing import save_wallet
    save_wallet(wallet)
    handle_event(
        {
            "type": "invoice.payment_failed",
            "data": {"object": {"customer": "cus_fail", "subscription": ""}},
        }
    )
    again = load_wallet("wal_fail")
    assert any("failed" in (row.get("note") or "").lower() for row in again["ledger"])


def test_spend_raises_when_short(tmp_path, monkeypatch):
    monkeypatch.setenv("STRATA_WALLETS_DIR", str(tmp_path / "short"))
    monkeypatch.setenv("STRATA_FREE_CREDITS", "1")
    wallet = load_wallet("wal_short")
    try:
        spend(wallet, "write_file")
        assert False, "should have blocked"
    except BillingError as exc:
        assert exc.status == 402
        assert exc.payload["needed"] == 8
