import { useState } from "react";
import { downloadPptx } from "../api";
import type { StrategyPack } from "../types";
import { SlideView } from "./SlideView";

export function DeckTab({ pack }: { pack: StrategyPack }) {
  const [i, setI] = useState(0);
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState("");
  const slide = pack.slides[i];
  const present = () => {
    const el = document.querySelector(".slide-stage");
    if (el && el.requestFullscreen) el.requestFullscreen();
  };
  const exportDeck = async () => {
    setExportError("");
    setExporting(true);
    try {
      await downloadPptx(pack);
    } catch (err) {
      setExportError(err instanceof Error ? err.message : String(err));
    } finally {
      setExporting(false);
    }
  };

  return (
    <div>
      <div className="topbar">
        <div>
          <h1>{pack.meta.doctrine}</h1>
          <p>
            {pack.meta.brand} · {pack.meta.therapyArea} · {pack.meta.market} ·{" "}
            {pack.slides.length} slides
          </p>
        </div>
        <div className="actions">
          <button className="btn" type="button" onClick={() => window.print()}>
            Print / PDF
          </button>
          <button className="btn copper" type="button" disabled={exporting} onClick={exportDeck}>
            {exporting ? "Building PPTX…" : "Download PPTX"}
          </button>
          <button className="btn" type="button" onClick={present}>
            Present
          </button>
        </div>
      </div>
      {exportError ? <p className="error">{exportError}</p> : null}
      <p className="small muted" style={{ marginTop: -12, marginBottom: 12 }}>
        The PPTX is a real PowerPoint file — native text, tables, and Office charts you can edit
        in PowerPoint or Google Slides. Forest and box plots are shapes, not pictures.
      </p>
      <div className="slide-stage">
        <SlideView slide={slide} />
        <div className="deck-nav">
          <button
            className="btn"
            type="button"
            onClick={() => setI((n) => Math.max(0, n - 1))}
            disabled={i === 0}
          >
            Prev
          </button>
          <div className="thumbs">
            {pack.slides.map((s, idx) => (
              <button
                key={s.id}
                type="button"
                className={idx === i ? "on" : ""}
                onClick={() => setI(idx)}
                title={s.title}
              >
                {idx + 1}
              </button>
            ))}
          </div>
          <button
            className="btn"
            type="button"
            onClick={() => setI((n) => Math.min(pack.slides.length - 1, n + 1))}
            disabled={i === pack.slides.length - 1}
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
