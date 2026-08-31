import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

export default function RunBrief() {
  const navigate = useNavigate();
  const [status, setStatus] = useState<string | null>(null);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const brief = {
      brand: String(form.get("brand") || ""),
      therapy_area: String(form.get("therapy_area") || ""),
      indication: String(form.get("indication") || ""),
      product: String(form.get("product") || ""),
      market: String(form.get("market") || ""),
      business_goal: String(form.get("business_goal") || ""),
    };
    setStatus("Queuing multi-source search…");
    const runId = crypto.randomUUID();
    const res = await fetch("/api/research", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ runId, brief }),
    });
    if (!res.ok && res.status !== 202) {
      setStatus(`Start failed (${res.status}). You can still open the demo deck.`);
      return;
    }
    setStatus("Running. Polling for a validated deck…");
    for (let i = 0; i < 40; i += 1) {
      await new Promise((r) => setTimeout(r, 4000));
      const st = await fetch(`/api/research/${runId}`);
      if (!st.ok) continue;
      const data = await st.json();
      if (data.status === "ready") {
        navigate(`/deck/${runId}`);
        return;
      }
      if (data.status === "error") {
        setStatus(data.detail || "Pipeline error");
        return;
      }
      setStatus(`Still running (${data.status || "working"})…`);
    }
    setStatus("Timed out waiting for the background job. Try the demo deck.");
  }

  return (
    <>
      <header className="hero">
        <div className="eyebrow">New brief</div>
        <h1>Point the workflow at another cohort.</h1>
        <p className="lede">
          Same connectors, same validation rules. The live run uses a Netlify
          background function (up to 15 minutes) and stores the deck JSON as a
          file in Blobs.
        </p>
      </header>
      <form className="form" onSubmit={onSubmit}>
        <label>
          Brand *
          <input name="brand" required defaultValue="CardioShield" />
        </label>
        <label>
          Therapy area *
          <input name="therapy_area" required defaultValue="Cardiology - chronic heart failure" />
        </label>
        <label>
          Indication
          <input name="indication" defaultValue="HFrEF" />
        </label>
        <label>
          Product / molecule
          <input name="product" defaultValue="sacubitril/valsartan" />
        </label>
        <label>
          Market
          <input name="market" defaultValue="India" />
        </label>
        <label>
          Goal / brief need
          <textarea name="business_goal" rows={3} defaultValue="Guideline-consistent early initiation; understand benefit frequency and lived experience." />
        </label>
        <button className="btn" type="submit">
          Run validated literature workflow
        </button>
      </form>
      {status ? <p className="status">{status}</p> : null}
    </>
  );
}
