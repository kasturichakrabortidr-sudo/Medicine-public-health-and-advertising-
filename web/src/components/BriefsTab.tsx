import { useMemo, useRef, useState } from "react";
import { ACCEPT_LABELS, extractBriefs, generatePack } from "../api";
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
  const extractGen = useRef(0);

  const runExtract = async (nextFiles: File[], nextPasted: string) => {
    if (!nextFiles.length && !nextPasted.trim()) {
      setPreviews([]);
      return;
    }
    const gen = ++extractGen.current;
    setError("");
    setBusy(true);
    try {
      const res = await extractBriefs(nextFiles, nextPasted);
      if (gen !== extractGen.current) return;
      setPreviews(res.files);
      setBrief({ ...emptyBrief(), ...res.brief });
    } catch (err) {
      if (gen !== extractGen.current) return;
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      if (gen === extractGen.current) setBusy(false);
    }
  };

  const addFiles = (list: FileList | File[]) => {
    const next = [...files];
    for (const f of Array.from(list)) {
      if (!next.some((x) => x.name === f.name && x.size === f.size)) next.push(f);
    }
    setFiles(next);
    void runExtract(next, pasted);
  };

  const removeFile = (file: File) => {
    const next = files.filter((x) => x !== file);
    setFiles(next);
    void runExtract(next, pasted);
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
    if (!files.length && !pasted.trim()) {
      setError("Upload a file or paste the brief first.");
      return;
    }
    await runExtract(files, pasted);
  };

  const generate = async () => {
    setError("");
    const hasBrief = Boolean(brief.brand || brief.therapy_area || brief.raw_text);
    if (!files.length && !pasted.trim() && !hasBrief) {
      setError("Upload or paste a brief before writing the working file. The CardioShield demo will not be used.");
      return;
    }
    setBusy(true);
    try {
      const pack = await generatePack({
        files,
        pasted,
        brief: hasBrief ? brief : undefined,
      });
      if (pack.meta.mode === "demo" || pack.meta.demo) {
        throw new Error("The engine returned the demo pack. Your brief was not used.");
      }
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
          Drop the client PDF, Word file, or deck. Fields are pulled automatically from titles,
          tables, and labelled lines — then the eleven-step working file is written for{" "}
          <em>this</em> brief, not the CardioShield demo.
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
          <input type="file" multiple onChange={(e) => e.target.files && addFiles(e.target.files)} />
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
                <button className="btn" type="button" onClick={() => removeFile(f)}>
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
          placeholder="Brand name, product, therapy area, market, insights — or paste the whole brief."
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
                {p.chars} chars extracted {p.pages ? `· ${p.pages} pages` : ""}
                {p.chars < 40 ? " · little text found" : ""}
              </div>
              {p.notes.map((n) => (
                <div className="note" key={n}>
                  {n}
                </div>
              ))}
              {p.preview ? <pre className="extract-preview">{p.preview}</pre> : null}
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
        {(previews.length > 0 || Boolean(brief.raw_text)) && (!brief.brand || !brief.therapy_area) ? (
          <div className="alert watch">
            {!brief.brand && !brief.therapy_area
              ? "Brand and therapy area are still empty. If the upload was a scanned PDF, paste the key lines from the brief."
              : `Still empty: ${[!brief.brand ? "brand" : "", !brief.therapy_area ? "therapy area" : ""]
                  .filter(Boolean)
                  .join(" and ")}. Fill ${!brief.brand ? "brand" : "therapy area"} before writing the working file, or paste more of the brief.`}
          </div>
        ) : null}
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
        {brief.raw_text ? (
          <div className="field">
            <label htmlFor="raw_text">Text pulled from the files</label>
            <textarea id="raw_text" className="small" rows={8} readOnly value={brief.raw_text} />
          </div>
        ) : null}
      </section>
    </div>
  );
}
