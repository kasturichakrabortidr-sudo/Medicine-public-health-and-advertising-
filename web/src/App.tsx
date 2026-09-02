import { useEffect, useState } from "react";
import { deleteProject, downloadPptx, downloadWorkfile, fetchHealth, generatePack, listProjects, loadProject, saveProject } from "./api";
import { LEVELS } from "./levels";
import { printAs } from "./print";
import { PrintSheet } from "./components/PrintSheet";
import { DeckScreen } from "./screens/DeckScreen";
import { HomeScreen } from "./screens/HomeScreen";
import { PapersScreen } from "./screens/PapersScreen";
import { ProjectsScreen } from "./screens/ProjectsScreen";
import { TakeScreen } from "./screens/TakeScreen";
import { WorkfileScreen } from "./screens/WorkfileScreen";
import type { AgentEvent, ProjectSummary, StrategyPack, TabId } from "./types";

export default function App() {
  const [tab, setTab] = useState<TabId>("briefs");
  const [pack, setPack] = useState<StrategyPack | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [projects, setProjects] = useState<ProjectSummary[] | null>(null);
  const [log, setLog] = useState<AgentEvent[]>([]);
  const [llm, setLlm] = useState<boolean | null>(null);
  const [model, setModel] = useState("director-workflow");

  useEffect(() => {
    fetchHealth()
      .then((health) => {
        setLlm(Boolean(health.llm));
        setModel(health.model || "director-workflow");
      })
      .catch(() => {
        setLlm(false);
      });
  }, []);

  const openPack = (next: StrategyPack, go: TabId = "deck") => {
    setPack(next);
    setTab(go);
    setError("");
  };

  const build = async (files: File[], pasted: string) => {
    setBusy(true);
    setError("");
    setLog([]);
    try {
      const next = await generatePack(files, pasted, (event) => {
        setLog((prev) => [...prev, event]);
      });
      if (next.agent?.log?.length) setLog(next.agent.log);
      setPack(next);
      setError("");
      await new Promise((resolve) => window.setTimeout(resolve, 1200));
      setTab("deck");
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
        <nav className="levels-nav">
          {LEVELS.map((level) => (
            <button
              key={level.id}
              type="button"
              className={tab === level.id ? "on" : ""}
              disabled={level.needsPack && !pack}
              onClick={() => setTab(level.id)}
            >
              <em>{level.n}</em>
              {level.label}
            </button>
          ))}
        </nav>
        <button type="button" className={tab === "projects" ? "on archive" : "archive"} onClick={() => setTab("projects")}>
          Projects
        </button>
        <div className="rail-foot">
          <button type="button" className="ghost" disabled={!pack || busy} onClick={pin}>
            Save this pack
          </button>
          {pack ? (
            <p className="doctrine">
              {pack.doctrine.name}. {pack.doctrine.bet}
            </p>
          ) : (
            <p className="doctrine">Five levels from one brief: working file, papers, deck, then the takeaway.</p>
          )}
        </div>
      </aside>

      <main className="stage">
        {error ? <p className="banner">{error}</p> : null}
        {tab === "briefs" ? <HomeScreen busy={busy} log={log} llm={llm} model={model} onBuild={build} /> : null}
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
        {tab === "take" && pack ? (
          <TakeScreen
            pack={pack}
            busy={busy}
            onPptx={exportDeck}
            onWorkfile={exportWork}
            onPrintWork={() => {
              setTab("work");
              window.setTimeout(() => printAs("work"), 120);
            }}
          />
        ) : null}
        {pack ? <PrintSheet pack={pack} /> : null}
      </main>
    </div>
  );
}
