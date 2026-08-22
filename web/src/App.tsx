import { useEffect, useState } from "react";
import { fetchDemo } from "./api";
import { BriefsTab } from "./components/BriefsTab";
import { DashboardTab } from "./components/DashboardTab";
import { DeckTab } from "./components/DeckTab";
import { EvidenceTab } from "./components/EvidenceTab";
import { WorkingFileTab } from "./components/WorkingFileTab";
import type { StrategyPack, TabId } from "./types";

const USER_PACK_KEY = "strata.userPack";

function isDemoPack(pack: StrategyPack | null): boolean {
  if (!pack) return false;
  return pack.meta.mode === "demo" || pack.meta.demo === true;
}

function readSavedPack(): StrategyPack | null {
  try {
    const raw = sessionStorage.getItem(USER_PACK_KEY);
    if (!raw) return null;
    const pack = JSON.parse(raw) as StrategyPack;
    if (!pack?.meta?.brand || isDemoPack(pack)) return null;
    return pack;
  } catch {
    return null;
  }
}

export default function App() {
  const [tab, setTab] = useState<TabId>("briefs");
  const [pack, setPack] = useState<StrategyPack | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const applyPack = (next: StrategyPack, go: TabId = "work") => {
    setPack(next);
    setTab(go);
    if (!isDemoPack(next)) {
      try {
        sessionStorage.setItem(USER_PACK_KEY, JSON.stringify(next));
      } catch {
        /* ignore quota */
      }
    }
  };

  const loadDemo = async () => {
    if (pack && !isDemoPack(pack)) {
      const ok = window.confirm(
        `Replace the working file for ${pack.meta.brand} with the CardioShield demo?`,
      );
      if (!ok) return;
    }
    setBusy(true);
    setError("");
    try {
      const demo = await fetchDemo();
      demo.meta.demo = true;
      demo.meta.mode = "demo";
      setPack(demo);
      setTab("work");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    const saved = readSavedPack();
    if (saved) {
      setPack(saved);
      setTab("work");
    }
  }, []);

  const demo = isDemoPack(pack);

  return (
    <div className="app">
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
          Open the CardioShield demo
        </button>
        <div className="doctrine-chip">
          <em>{pack ? pack.meta.brand : "Nothing read yet"}</em>
          {pack
            ? demo
              ? "This is the example working file. Upload your brief on the Brief tab to replace it."
              : pack.doctrine.bet
            : "Drop a brief. We will write the working file before anyone sees a slide."}
        </div>
      </aside>
      <main className="main">
        {error ? <p className="error">{error}</p> : null}
        {demo && pack ? (
          <div className="demo-banner">
            Demo strategy for CardioShield — not from your upload. Go to Brief, drop your
            files, then click Write the working file.
          </div>
        ) : null}
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
                setError("");
                applyPack(next, "work");
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
