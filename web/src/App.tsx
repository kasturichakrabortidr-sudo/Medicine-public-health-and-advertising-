import { useState } from "react";
import { deleteProject, downloadPptx, downloadWorkfile, generatePack, listProjects, loadProject, saveProject } from "./api";
import { DeckScreen } from "./screens/DeckScreen";
import { HomeScreen } from "./screens/HomeScreen";
import { PapersScreen } from "./screens/PapersScreen";
import { ProjectsScreen } from "./screens/ProjectsScreen";
import { WorkfileScreen } from "./screens/WorkfileScreen";
import type { ProjectSummary, StrategyPack, TabId } from "./types";

export default function App() {
  const [tab, setTab] = useState<TabId>("briefs");
  const [pack, setPack] = useState<StrategyPack | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [projects, setProjects] = useState<ProjectSummary[] | null>(null);

  const openPack = (next: StrategyPack, go: TabId = "deck") => {
    setPack(next);
    setTab(go);
    setError("");
  };

  const build = async (files: File[], pasted: string) => {
    setBusy(true);
    setError("");
    try {
      const next = await generatePack(files, pasted);
      openPack(next, "deck");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  const pin = async () => {
    if (!pack) return;
    setBusy(true);
    setError("");
    try {
      await saveProject(pack, "saved");
      setProjects(await listProjects());
      setTab("projects");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  const openSaved = async (id: string) => {
    setBusy(true);
    setError("");
    try {
      const record = await loadProject(id);
      openPack(record.pack, "deck");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  const remove = async (id: string) => {
    setBusy(true);
    setError("");
    try {
      await deleteProject(id);
      setProjects(await listProjects());
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  const exportDeck = async () => {
    if (!pack) return;
    setBusy(true);
    setError("");
    try {
      await downloadPptx(pack);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  const exportWork = async () => {
    if (!pack) return;
    setBusy(true);
    setError("");
    try {
      await downloadWorkfile(pack);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className={tab === "deck" && pack ? "shell decking" : "shell"}>
      <aside className="rail">
        <div className="brand">
          <strong>STRATA</strong>
          <span>HCP strategy director</span>
        </div>
        <nav>
          <button type="button" className={tab === "briefs" ? "on" : ""} onClick={() => setTab("briefs")}>
            Brief
          </button>
          <button type="button" className={tab === "projects" ? "on" : ""} onClick={() => setTab("projects")}>
            Projects
          </button>
          <button type="button" className={tab === "work" ? "on" : ""} disabled={!pack} onClick={() => setTab("work")}>
            Working file
          </button>
          <button
            type="button"
            className={tab === "evidence" ? "on" : ""}
            disabled={!pack}
            onClick={() => setTab("evidence")}
          >
            Papers
          </button>
          <button type="button" className={tab === "deck" ? "on" : ""} disabled={!pack} onClick={() => setTab("deck")}>
            Deck
          </button>
        </nav>
        <div className="rail-foot">
          <button type="button" className="ghost" disabled={!pack || busy} onClick={pin}>
            Save this pack
          </button>
          {pack ? (
            <p className="doctrine">
              {pack.doctrine.name}. {pack.doctrine.bet}
            </p>
          ) : (
            <p className="doctrine">Paste a brief. STRATA writes the working file and a 12-slide strategy deck.</p>
          )}
        </div>
      </aside>

      <main className="stage">
        {error ? <p className="banner">{error}</p> : null}
        {tab === "briefs" ? <HomeScreen busy={busy} onBuild={build} /> : null}
        {tab === "projects" ? (
          <ProjectsScreen
            rows={projects}
            setRows={setProjects}
            busy={busy}
            onOpen={openSaved}
            onDelete={remove}
          />
        ) : null}
        {tab === "work" && pack ? <WorkfileScreen pack={pack} busy={busy} onExport={exportWork} /> : null}
        {tab === "evidence" && pack ? <PapersScreen pack={pack} /> : null}
        {tab === "deck" && pack ? <DeckScreen pack={pack} busy={busy} onExport={exportDeck} /> : null}
      </main>
    </div>
  );
}
