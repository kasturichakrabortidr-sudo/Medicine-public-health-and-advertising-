import { useState } from "react";
import { ACCEPT } from "../api";
import { AgentLog } from "../components/AgentLog";
import { LEVELS } from "../levels";
import type { AgentEvent } from "../types";

export function HomeScreen({
  busy,
  log,
  llm,
  model,
  onBuild,
}: {
  busy: boolean;
  log: AgentEvent[];
  llm: boolean | null;
  model: string;
  onBuild: (files: File[], pasted: string) => Promise<void>;
}) {
  const [pasted, setPasted] = useState("");
  const [files, setFiles] = useState<File[]>([]);

  const add = (list: FileList | File[]) => {
    const next = [...files];
    for (const f of Array.from(list)) {
      if (!next.some((x) => x.name === f.name && x.size === f.size)) next.push(f);
    }
    setFiles(next);
  };

  const latest = log[log.length - 1];

  return (
    <section className="home">
      <p className="eyebrow">Five levels. One argument.</p>
      <h1>Paste the brief. Get every level of the strategy, not a literature dump.</h1>
      <p className="lede">
        A director agent thinks before each step, then executes the workflow: working file, numbered
        papers, 12-slide deck, takeaway. Claims stay inside the papers.
      </p>
      <p className="agent-status">
        Director connected
        {llm === true ? ` · model pass on ${model}` : " · workflow agent (model pass off until an API key is set)"}
      </p>

      <ol className="home-levels">
        {LEVELS.map((level) => (
          <li key={level.id}>
            <span>{level.n}</span>
            <strong>{level.label}</strong>
          </li>
        ))}
      </ol>

      <label className="paste-label" htmlFor="paste">
        Brief
      </label>
      <textarea
        id="paste"
        value={pasted}
        onChange={(e) => setPasted(e.target.value)}
        placeholder="Brand, molecule, indication, the HCP habit, the business number, MLR lines. YAML, JSON, or prose."
      />

      <div className="drop">
        <input type="file" multiple accept={ACCEPT} onChange={(e) => e.target.files && add(e.target.files)} />
        <span>Or drop PDF, PPTX, DOCX, YAML.</span>
      </div>
      {files.length ? (
        <ul className="files">
          {files.map((f) => (
            <li key={f.name + f.size}>
              {f.name}
              <button type="button" onClick={() => setFiles(files.filter((x) => x !== f))}>
                Remove
              </button>
            </li>
          ))}
        </ul>
      ) : null}

      <button
        className="primary"
        type="button"
        disabled={busy || (!pasted.trim() && files.length === 0)}
        onClick={() => onBuild(files, pasted)}
      >
        {busy ? (latest ? `${latest.type === "think" ? "Thinking" : "Executing"} · ${latest.title}` : "Director running") : "Build the strategy"}
      </button>

      {log.length ? <AgentLog events={log} /> : null}
    </section>
  );
}
