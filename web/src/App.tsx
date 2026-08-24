import { useEffect, useState } from "react";
import { fetchDemo } from "./api";
import { BriefsTab } from "./components/BriefsTab";
import { DashboardTab } from "./components/DashboardTab";
import { DeckTab } from "./components/DeckTab";
import { EvidenceTab } from "./components/EvidenceTab";
import { WorkingFileTab } from "./components/WorkingFileTab";
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
      setTab("work");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    loadDemo().catch(() => undefined);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className={tab === "deck" ? "app deck-mode" : "app"}>
      <aside className="rail">
        <div className="mark">
          <strong>STRATA</strong>
          <span>Working file for HCP campaigns</span>
        </div>
        <nav className="nav">
          <button type="button" className={tab === "briefs" ? "active" : ""} onClick={() => setTab("briefs")}>
            Brief
          </button>
          <button
            type="button"
            className={tab === "work" ? "active" : ""}
            onClick={() => setTab("work")}
            disabled={!pack}
          >
            Working file
          </button>
          <button
            type="button"
            className={tab === "evidence" ? "active" : ""}
            onClick={() => setTab("evidence")}
            disabled={!pack}
          >
            Papers
          </button>
          <button
            type="button"
            className={tab === "deck" ? "active" : ""}
            onClick={() => setTab("deck")}
            disabled={!pack}
          >
            Deck
          </button>
          <button
            type="button"
            className={tab === "dashboard" ? "active" : ""}
            onClick={() => setTab("dashboard")}
            disabled={!pack}
          >
            Measurement
          </button>
        </nav>
        <button className="btn" type="button" onClick={loadDemo} disabled={busy}>
          Open the CardioShield working file
        </button>
        <div className="doctrine-chip">
          <em>{pack ? pack.doctrine.name : "Nothing read yet"}</em>
          {pack ? pack.doctrine.bet : "Drop a brief. We will write the working file before anyone sees a slide."}
        </div>
      </aside>
      <main className="main">
        {error ? <p className="error">{error}</p> : null}
        {tab === "briefs" && (
          <>
            <div className="topbar">
              <div>
                <h1>The brief</h1>
                <p>We read this first. The working file comes next. The deck is last.</p>
              </div>
            </div>
            <BriefsTab
              busy={busy}
              setBusy={setBusy}
              onPack={(next) => {
                setPack(next);
                setTab("work");
              }}
            />
          </>
        )}
        {tab === "work" && pack && <WorkingFileTab pack={pack} />}
        {tab === "evidence" && pack && <EvidenceTab pack={pack} />}
        {tab === "deck" && pack && <DeckTab pack={pack} />}
        {tab === "dashboard" && pack && <DashboardTab pack={pack} />}
      </main>
    </div>
  );
}
