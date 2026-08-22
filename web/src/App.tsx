import { useEffect, useState } from "react";
import { fetchDemo, saveProject } from "./api";
import { BriefsTab } from "./components/BriefsTab";
import { DashboardTab } from "./components/DashboardTab";
import { DeckTab } from "./components/DeckTab";
import { EvidenceTab } from "./components/EvidenceTab";
import { ProjectsTab } from "./components/ProjectsTab";
import { WorkingFileTab } from "./components/WorkingFileTab";
import { RefLinksProvider } from "./links";
import type { StrategyPack, TabId } from "./types";

const USER_PACK_KEY = "strata.userPack.v4";

function isDemoPack(pack: StrategyPack | null): boolean {
  if (!pack) return false;
  return pack.meta.mode === "demo" || pack.meta.demo === true;
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

  const startOver = () => {
    setPack(null);
    setTab("briefs");
    setError("");
    try {
      sessionStorage.removeItem(USER_PACK_KEY);
    } catch {
      /* ignore */
    }
  };

  useEffect(() => {
    // Fresh load always starts on Brief. A previous pack on this origin
    // is the usual reason the old one-paper campaign reappears.
    try {
      sessionStorage.removeItem(USER_PACK_KEY);
    } catch {
      /* ignore */
    }
  }, []);

  const demo = isDemoPack(pack);
  const refs = pack?.references || pack?.evidence?.references || [];

  return (
    <RefLinksProvider refs={refs}>
    <div className="app">
      <aside className="rail">
        <div className="mark">
          <strong>STRATA</strong>
          <span>Working file for HCP campaigns</span>
          <span className="build-stamp">22 Aug · visuals tell the working file</span>
        </div>
        <nav className="nav">
          <button type="button" className={tab === "briefs" ? "active" : ""} onClick={() => setTab("briefs")}>
            Brief
          </button>
          <button type="button" className={tab === "projects" ? "active" : ""} onClick={() => setTab("projects")}>
            Projects
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
        <button className="btn ghost" type="button" onClick={startOver} disabled={busy}>
          Start over
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
                if (!isDemoPack(next)) {
                  void saveProject(next, "ongoing").catch((err) => {
                    setError(err instanceof Error ? err.message : String(err));
                  });
                }
              }}
            />
          </>
        )}
        {tab === "projects" && (
          <ProjectsTab
            pack={pack}
            onOpen={(next) => {
              setError("");
              applyPack(next, "work");
            }}
            onError={setError}
          />
        )}
        {tab === "work" && pack && <WorkingFileTab pack={pack} />}
        {tab === "evidence" && pack && <EvidenceTab pack={pack} />}
        {tab === "deck" && pack && <DeckTab pack={pack} />}
        {tab === "dashboard" && pack && <DashboardTab pack={pack} />}
      </main>
    </div>
    </RefLinksProvider>
  );
}
