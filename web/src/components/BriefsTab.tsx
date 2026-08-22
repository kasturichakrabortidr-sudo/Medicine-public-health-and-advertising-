import { useMemo, useState } from "react";
import { ACCEPT, ACCEPT_LABELS, extractBriefs, generatePack } from "../api";
import type { ExtractedBrief, FilePreview, StrategyPack } from "../types";

const emptyBrief = (): ExtractedBrief => ({
  brand: "",
  product: "",
  therapy_area: "",
  indication: "",
  market: "",
  business_goal: "",
  target_specialties: [],
  hcp_segments: [],
  brand_evidence: [],
  existing_evidence: [],
  evolving_evidence: [],
  guidelines: [],
  hcp_insights: [],
  competitors: [],
  access_and_cost: [],
  constraints: [],
  notes: "",
  source_files: [],
  raw_text: "",
  extraction_notes: [],
});

export function BriefsTab({
  onPack,
  busy,
  setBusy,
}: {
  onPack: (pack: StrategyPack) => void;
  busy: boolean;
  setBusy: (v: boolean) => void;
}) {
  const [files, setFiles] = useState<File[]>([]);
  const [pasted, setPasted] = useState("");
  const [previews, setPreviews] = useState<FilePreview[]>([]);
  const [brief, setBrief] = useState<ExtractedBrief>(emptyBrief);
  const [error, setError] = useState("");
  const [over, setOver] = useState(false);

  const addFiles = (list: FileList | File[]) => {
    const next = [...files];
    for (const f of Array.from(list)) {
      if (!next.some((x) => x.name === f.name && x.size === f.size)) next.push(f);
    }
    setFiles(next);
  };

  const field = (key: keyof ExtractedBrief, label: string, list = false) => (
    <div className="field" key={key}>
      <label htmlFor={key}>{label}</label>
      {list ? (
        <textarea
          id={key}
          className="small"
          rows={3}
          value={(brief[key] as string[]).join("\n")}
          onChange={(e) =>
            setBrief({
              ...brief,
              [key]: e.target.value
                .split("\n")
                .map((s) => s.trim())
                .filter(Boolean),
            })
          }
        />
      ) : (
        <input
          id={key}
          value={String(brief[key] || "")}
          onChange={(e) => setBrief({ ...brief, [key]: e.target.value })}
        />
      )}
    </div>
  );

  const extract = async () => {
    setError("");
    setBusy(true);
    try {
      const res = await extractBriefs(files, pasted);
      setPreviews(res.files);
      setBrief({ ...emptyBrief(), ...res.brief });
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  const generate = async () => {
    setError("");
    setBusy(true);
    try {
      const pack = await generatePack({
        files,
        pasted,
        brief: brief.brand || brief.therapy_area ? brief : undefined,
      });
      onPack(pack);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  const bytes = useMemo(() => files.reduce((n, f) => n + f.size, 0), [files]);

  return (
    <div className="grid-2">
      <section className="card">
        <h2>Upload a brief — any format</h2>
        <p className="muted small">
          Drop the client files, the advisory notes, a messy paste. We will pull the fields,
          then write the eleven-step working file. We will not jump to a deck from a slogan.
        </p>
        <div
          className={`drop ${over ? "over" : ""}`}
          onDragOver={(e) => {
            e.preventDefault();
            setOver(true);
          }}
          onDragLeave={() => setOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setOver(false);
            addFiles(e.dataTransfer.files);
          }}
        >
          <p>
            <strong>Drag files here</strong> or choose from disk
          </p>
          <p className="small muted">Up to 25 MB each. Mix formats in one drop.</p>
          <input
            type="file"
            multiple
            accept={ACCEPT}
            onChange={(e) => e.target.files && addFiles(e.target.files)}
          />
          <div className="formats">
            {ACCEPT_LABELS.map((l) => (
              <code key={l}>{l}</code>
            ))}
          </div>
        </div>

        {files.length > 0 && (
          <div>
            {files.map((f) => (
              <div className="file-row" key={f.name + f.size}>
                <span>
                  {f.name} <span className="muted">· {(f.size / 1024).toFixed(1)} KB</span>
                </span>
                <button
                  className="btn"
                  type="button"
                  onClick={() => setFiles(files.filter((x) => x !== f))}
                >
                  Remove
                </button>
              </div>
            ))}
            <p className="small muted">{files.length} files · {(bytes / 1024).toFixed(1)} KB</p>
          </div>
        )}

        <label className="field" htmlFor="paste">
          <span>Or paste the brief</span>
        </label>
        <textarea
          id="paste"
          value={pasted}
          placeholder="YAML, JSON, or prose. Brand and therapy area are enough to start."
          onChange={(e) => setPasted(e.target.value)}
        />

        <div className="actions" style={{ marginTop: 12 }}>
          <button className="btn" type="button" disabled={busy} onClick={extract}>
            Extract fields
          </button>
          <button className="btn copper" type="button" disabled={busy} onClick={generate}>
            {busy ? "Reading the brief…" : "Write the working file"}
          </button>
        </div>
        {error ? <p className="error">{error}</p> : null}

        {previews.map((p) => (
          <div key={p.filename} className="file-row">
            <div>
              <strong>{p.filename}</strong>
              <div className="small muted">
                {p.chars} chars {p.pages ? `· ${p.pages} pages` : ""}
              </div>
              {p.notes.map((n) => (
                <div className="note" key={n}>
                  {n}
                </div>
              ))}
            </div>
          </div>
        ))}
      </section>

      <section className="card">
        <h2>Working brief</h2>
        <p className="muted small">
          Edit after extraction. Only brand and therapy area are required; gaps become
          research tasks, not invented facts.
        </p>
        <div className="field-grid">
          {field("brand", "Brand")}
          {field("product", "Product / molecule")}
          {field("therapy_area", "Therapy area")}
          {field("indication", "Indication")}
          {field("market", "Market")}
          {field("business_goal", "Business goal")}
        </div>
        {field("target_specialties", "Target specialties (one per line)", true)}
        {field("hcp_insights", "HCP insights", true)}
        {field("brand_evidence", "Brand evidence", true)}
        {field("guidelines", "Guidelines", true)}
        {field("competitors", "Competitors", true)}
        {field("access_and_cost", "Access & cost", true)}
        {field("constraints", "Constraints / MLR", true)}
        {brief.extraction_notes.length > 0 && (
          <div className="alert watch">
            {brief.extraction_notes.map((n) => (
              <div key={n}>{n}</div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
