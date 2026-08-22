import { useState } from "react";
import { sandboxGrant, startCheckout, startPortal } from "../api";
import type { BillingCatalog, BillingPlan, Wallet } from "../types";

export function PlansTab({
  billing,
  onWallet,
  onError,
}: {
  billing: BillingCatalog | null;
  onWallet: (wallet: Wallet) => void;
  onError: (msg: string) => void;
}) {
  const [busy, setBusy] = useState("");
  const catalog = billing?.catalog;
  const wallet = billing?.wallet;

  const buy = async (item: BillingPlan) => {
    setBusy(item.id);
    onError("");
    try {
      if (catalog?.stripe) {
        const session = await startCheckout(item.id);
        if (session.url) {
          window.location.href = session.url;
          return;
        }
        throw new Error("Stripe did not return a checkout URL.");
      }
      const res = await sandboxGrant(item.id);
      onWallet(res.wallet);
    } catch (err) {
      onError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy("");
    }
  };

  const portal = async () => {
    setBusy("portal");
    onError("");
    try {
      const session = await startPortal();
      if (session.url) window.location.href = session.url;
    } catch (err) {
      onError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy("");
    }
  };

  if (!catalog || !wallet) {
    return <p className="muted">Loading plans…</p>;
  }

  return (
    <div>
      <div className="topbar">
        <div>
          <h1>Plans and credits</h1>
          <p>
            {wallet.planName} · {wallet.credits} credits left. Write a working file for{" "}
            {catalog.actions.write_file.credits}. Download PPTX for {catalog.actions.export_pptx.credits}.
          </p>
        </div>
        {wallet.hasCustomer && catalog.stripe ? (
          <div className="actions">
            <button className="btn" type="button" disabled={Boolean(busy)} onClick={() => void portal()}>
              Manage billing
            </button>
          </div>
        ) : null}
      </div>
      {catalog.sandbox ? (
        <div className="demo-banner">
          Stripe is not connected on this machine. Starting a plan adds credits here so you can
          try the meter. Add STRIPE_SECRET_KEY to take real cards.
        </div>
      ) : null}
      <div className="plan-grid">
        {catalog.plans.map((plan) => (
          <article className={`plan-card${wallet.plan === plan.id ? " current" : ""}`} key={plan.id}>
            <p className="plan-kicker">{wallet.plan === plan.id ? "Your plan" : plan.kind}</p>
            <h2>{plan.name}</h2>
            <p className="plan-price">
              {plan.priceLabel}
              {plan.interval ? <span> / {plan.interval}</span> : null}
            </p>
            <p className="plan-credits">{plan.credits} credits</p>
            <p>{plan.blurb}</p>
            <ul>
              {plan.includes.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
            {plan.id === "free" ? (
              <button className="btn" type="button" disabled>
                Included
              </button>
            ) : (
              <button
                className="btn copper"
                type="button"
                disabled={Boolean(busy) || wallet.plan === plan.id}
                onClick={() => void buy(plan)}
              >
                {wallet.plan === plan.id ? "Current" : busy === plan.id ? "Working…" : catalog.stripe ? `Pay ${plan.priceLabel}` : `Start ${plan.name} here`}
              </button>
            )}
          </article>
        ))}
      </div>
      <h2 className="plan-pack-head">Need more credits this month</h2>
      <div className="plan-grid packs">
        {catalog.packs.map((pack) => (
          <article className="plan-card" key={pack.id}>
            <p className="plan-kicker">Top-up</p>
            <h2>{pack.name}</h2>
            <p className="plan-price">{pack.priceLabel}</p>
            <p>{pack.blurb}</p>
            <button className="btn" type="button" disabled={Boolean(busy)} onClick={() => void buy(pack)}>
              {busy === pack.id ? "Working…" : catalog.stripe ? `Buy ${pack.priceLabel}` : "Add 50 credits here"}
            </button>
          </article>
        ))}
      </div>
      {wallet.ledger.length ? (
        <ol className="credit-ledger">
          {wallet.ledger
            .slice()
            .reverse()
            .map((row, i) => (
              <li key={`${row.at}-${i}`}>
                <strong>{row.credits > 0 ? `+${row.credits}` : row.credits}</strong>
                <span>{row.note}</span>
              </li>
            ))}
        </ol>
      ) : null}
    </div>
  );
}
