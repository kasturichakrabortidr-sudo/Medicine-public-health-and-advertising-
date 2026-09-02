import { useState } from "react";
import { ACCEPT } from "../api";

export function HomeScreen({
  busy,
  onBuild,
}: {
  busy: boolean;
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

  return (
    <section className="home">
      <p className="eyebrow">Client brief in. Strategy deck out.</p>
      <h1>Paste the brief. Get a 12-slide argument, not a literature dump.</h1>
      <p className="lede">
        STRATA reads the habit in the brief, searches PubMed for this product and indication, and writes a
        working file plus a client deck. Nothing is preloaded. Claims stay inside the papers.
      </p>

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
        {busy ? "Searching PubMed…" : "Build the strategy"}
      </button>
    </section>
  );
}
