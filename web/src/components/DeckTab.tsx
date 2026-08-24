import { useEffect, useMemo, useState } from "react";
import { downloadPptx } from "../api";
import type { StrategyPack } from "../types";
import { SlideView } from "./SlideView";

export function DeckTab({ pack }: { pack: StrategyPack }) {
  const [i, setI] = useState(0);
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState("");
  const slides = pack.slides;
  const slide = slides[i];
  const sections = useMemo(() => {
    const seen: { section: string; index: number }[] = [];
    slides.forEach((s, idx) => {
      if (!seen.length || seen[seen.length - 1].section !== s.section) {
        seen.push({ section: s.section, index: idx });
      }
    });
    return seen;
  }, [slides]);

  const go = (next: number) => {
    setI(Math.max(0, Math.min(slides.length - 1, next)));
  };

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const t = e.target as HTMLElement | null;
      if (t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.isContentEditable)) return;
      if (e.key === "ArrowRight" || e.key === "PageDown" || e.key === " ") {
        e.preventDefault();
        go(i + 1);
      } else if (e.key === "ArrowLeft" || e.key === "PageUp") {
        e.preventDefault();
        go(i - 1);
      } else if (e.key === "Home") {
        e.preventDefault();
        go(0);
      } else if (e.key === "End") {
        e.preventDefault();
        go(slides.length - 1);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [i, slides.length]);

  const present = () => {
    const el = document.querySelector(".presenter");
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

  if (!slide) return null;

  return (
    <div className="deck-shell">
      <div className="deck-chrome">
        <div>
          <h1>{pack.meta.brand}</h1>
          <p>
            {pack.meta.therapyArea} · {pack.meta.market} · {slides.length} slides
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

      <div className="presenter">
        <nav className="section-rail" aria-label="Deck sections">
          {sections.map((s) => (
            <button
              key={`${s.section}-${s.index}`}
              type="button"
              className={slide.section === s.section ? "on" : ""}
              onClick={() => go(s.index)}
            >
              {s.section}
            </button>
          ))}
        </nav>

        <div className="stage-wrap">
          <div className="slide-stage">
            <SlideView slide={slide} />
          </div>
          <div className="deck-nav">
            <button className="btn" type="button" onClick={() => go(i - 1)} disabled={i === 0}>
              Previous
            </button>
            <div className="slide-pos">
              {i + 1} / {slides.length}
              <span>{slide.kicker}</span>
            </div>
            <button
              className="btn"
              type="button"
              onClick={() => go(i + 1)}
              disabled={i === slides.length - 1}
            >
              Next
            </button>
          </div>
        </div>
      </div>

      <div className="print-deck" aria-hidden="true">
        {slides.map((s) => (
          <SlideView key={s.id} slide={s} />
        ))}
      </div>
    </div>
  );
}
