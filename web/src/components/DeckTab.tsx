import { useState } from "react";
import { downloadPptx } from "../api";
import type { StrategyPack } from "../types";
import { SlideView } from "./SlideView";

const FALLBACK_SKILLS = [
  { id: "story", name: "Story", rule: "Every working-file phase has a beat. The deck is the argument, in order." },
  { id: "visuals", name: "Visuals", rule: "The picture carries the room. A slide without a visual is a failed beat." },
  { id: "copy", name: "Copy", rule: "Complete sentences only. Never an ellipsis. Never a cut clause." },
  { id: "layout", name: "Layout", rule: "One visual owns the 16:9. Refs sit in the flow. Nothing overlaps." },
];

export function DeckTab({ pack }: { pack: StrategyPack }) {
  const [i, setI] = useState(0);
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState("");
  const slide = pack.slides[i];
  const skills = pack.meta.deckSkillCards?.length ? pack.meta.deckSkillCards : FALLBACK_SKILLS;
  const map = pack.meta.storyMap || [];
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
  const goTo = (id: string) => {
    const idx = pack.slides.findIndex((s) => s.id === id);
    if (idx >= 0) setI(idx);
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
      <p className="small muted craft-line">
        Visual aids drive the working file. They do not paste it. Four skills run on
        every generate.
      </p>
      <div className="skill-strip">
        {skills.map((skill) => (
          <div className="skill-chip" key={skill.id}>
            <strong>{skill.name}</strong>
            <span>{skill.rule}</span>
          </div>
        ))}
      </div>
      {map.length ? (
        <ol className="story-rail">
          {map.map((beat) => (
            <li key={`${beat.slide}-${beat.phase}`}>
              <button
                type="button"
                className={beat.slide === slide.id ? "on" : ""}
                title={beat.question}
                onClick={() => goTo(beat.slide)}
              >
                {beat.phase} · {beat.question}
              </button>
            </li>
          ))}
        </ol>
      ) : null}
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
