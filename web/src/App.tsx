import { useEffect, useState } from "react";
import { fetchDemo } from "./api";
import { BriefsTab } from "./components/BriefsTab";
import { DashboardTab } from "./components/DashboardTab";
import { DeckTab } from "./components/DeckTab";
import { EvidenceTab } from "./components/EvidenceTab";
import type { StrategyPack, TabId } from "./types";

export default function App() {
  const [tab, setTab] = useState<TabId>("briefs");
  const [pack, setPack] = useState<StrategyPack | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const loadDemo = async () => {
    setBusy(true);
    setError("");
    try {
      const demo = await fetchDemo();
      setPack(demo);
      setTab("deck");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    loadDemo().catch(() => undefined);
    // Show the demo doctrine on first paint so the room is never empty.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="app">
      <aside className="rail">
        <div className="mark">
          <strong>STRATA</strong>
          <span>AI Strategy Director</span>
        </div>
        <nav className="nav">
          <button type="button" className={tab === "briefs" ? "active" : ""} onClick={() => setTab("briefs")}>
            Briefs
          </button>
          <button
            type="button"
            className={tab === "evidence" ? "active" : ""}
            onClick={() => setTab("evidence")}
            disabled={!pack}
          >
            Evidence
          </button>
          <button
            type="button"
            className={tab === "deck" ? "active" : ""}
            onClick={() => setTab("deck")}
            disabled={!pack}
          >
            Strat deck
          </button>
          <button
            type="button"
            className={tab === "dashboard" ? "active" : ""}
            onClick={() => setTab("dashboard")}
            disabled={!pack}
          >
            Dashboard
          </button>
        </nav>
        <button className="btn" type="button" onClick={loadDemo} disabled={busy}>
          Load CardioShield demo
        </button>
        <div className="doctrine-chip">
          <em>{pack ? pack.doctrine.name : "No doctrine yet"}</em>
          {pack ? pack.doctrine.bet : "Upload a brief in any format to open a working file."}
        </div>
      </aside>
      <main className="main">
        {error ? <p className="error">{error}</p> : null}
        {tab === "briefs" && (
          <>
            <div className="topbar">
              <div>
                <h1>Intake</h1>
                <p>The director reads the brief before anyone writes a slide.</p>
              </div>
            </div>
            <BriefsTab
              busy={busy}
              setBusy={setBusy}
              onPack={(next) => {
                setPack(next);
                setTab("deck");
              }}
            />
          </>
        )}
        {tab === "evidence" && pack && <EvidenceTab pack={pack} />}
        {tab === "deck" && pack && <DeckTab pack={pack} />}
        {tab === "dashboard" && pack && <DashboardTab pack={pack} />}
      </main>
    </div>
  );
}
