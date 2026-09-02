import { useEffect, useMemo, useRef, useState } from "react";
import { SlideCanvas } from "../components/SlideCanvas";
import type { StrategyPack } from "../types";

export function DeckScreen({
  pack,
  busy,
  onExport,
}: {
  pack: StrategyPack;
  busy: boolean;
  onExport: () => void;
}) {
  const [i, setI] = useState(0);
  const [fit, setFit] = useState({ w: 0, h: 0 });
  const stageRef = useRef<HTMLDivElement>(null);
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

  const go = (next: number) => setI(Math.max(0, Math.min(slides.length - 1, next)));

  useEffect(() => {
    const el = stageRef.current;
    if (!el) return;
    const apply = () => {
      const w = el.clientWidth;
      const h = el.clientHeight;
      if (w < 8 || h < 8) return;
      const width = Math.min(w, (h * 16) / 9);
      setFit({ w: Math.floor(width), h: Math.floor((width * 9) / 16) });
    };
    apply();
    const ro = new ResizeObserver(apply);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight" || e.key === " ") {
        e.preventDefault();
        go(i + 1);
      } else if (e.key === "ArrowLeft") {
        e.preventDefault();
        go(i - 1);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [i, slides.length]);

  if (!slide) return null;

  return (
    <div className="deck">
      <header className="deck-bar">
        <div>
          <h1>{pack.meta.brand}</h1>
          <p>
            {pack.meta.therapyArea} · {slides.length} slides
          </p>
        </div>
        <button className="primary" type="button" disabled={busy} onClick={onExport}>
          {busy ? "Building PPTX…" : "Download PPTX"}
        </button>
      </header>
      <div className="presenter">
        <nav className="sections">
          {sections.map((s) => (
            <button key={`${s.section}-${s.index}`} type="button" className={slide.section === s.section ? "on" : ""} onClick={() => go(s.index)}>
              {s.section}
            </button>
          ))}
        </nav>
        <div className="stage-wrap" ref={stageRef}>
          <div className="slide-fit" style={fit.w ? { width: fit.w, height: fit.h } : undefined}>
            <SlideCanvas slide={slide} />
          </div>
          <div className="deck-nav">
            <button type="button" onClick={() => go(i - 1)} disabled={i === 0}>
              Previous
            </button>
            <span>
              {i + 1} / {slides.length} {slide.kicker}
            </span>
            <button type="button" onClick={() => go(i + 1)} disabled={i === slides.length - 1}>
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
