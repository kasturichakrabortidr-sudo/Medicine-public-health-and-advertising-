import { useState } from "react";
import { saveProject } from "./api";
import { BriefsTab } from "./components/BriefsTab";
import { DashboardTab } from "./components/DashboardTab";
import { DeckTab } from "./components/DeckTab";
import { EvidenceTab } from "./components/EvidenceTab";
import { ProjectsTab } from "./components/ProjectsTab";
import { WorkingFileTab } from "./components/WorkingFileTab";
import type { StrategyPack, TabId } from "./types";

export default function App() {
  const [tab, setTab] = useState<TabId>("projects");
  const [pack, setPack] = useState<StrategyPack | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const applyPack = (next: StrategyPack, go: TabId = "work") => {
    setPack(next);
    setTab(go);
  };

  const pinPack = async () => {
    if (!pack) return;
    setBusy(true);
    setError("");
    try {
      await saveProject(pack, "saved");
      setTab("projects");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

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
            className={tab === "projects" ? "active" : ""}
            onClick={() => setTab("projects")}
          >
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
        {pack ? (
          <button className="btn" type="button" onClick={() => void pinPack()} disabled={busy}>
            Save this pack
          </button>
        ) : null}
        <div className="doctrine-chip">
          <em>{pack ? pack.doctrine.name : "No working file yet"}</em>
          {pack
            ? pack.doctrine.bet
            : "Upload a brief, or open a saved project. Nothing is preloaded."}
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
                applyPack(next, "work");
              }}
            />
          </>
        )}
        {tab === "projects" && (
          <ProjectsTab
            pack={pack}
            onOpen={(next) => applyPack(next, "work")}
            onError={setError}
          />
        )}
        {tab === "work" && pack && <WorkingFileTab pack={pack} />}
        {tab === "evidence" && pack && <EvidenceTab pack={pack} />}
        {tab === "deck" && pack && <DeckTab pack={pack} />}
        {tab === "dashboard" && pack && <DashboardTab pack={pack} />}
      </main>
    </div>
  );
}
