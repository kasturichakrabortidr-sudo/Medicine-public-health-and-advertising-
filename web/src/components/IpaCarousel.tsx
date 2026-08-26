import { useState } from "react";
import type { IpaTheme } from "../types";
import { Cite } from "./Cite";

export default function IpaCarousel({ themes }: { themes: IpaTheme[] }) {
  const [i, setI] = useState(0);
  if (!themes.length) {
    return <p>No IPA-eligible qualitative extracts survived screening.</p>;
  }
  const theme = themes[i];
  return (
    <div className="carousel">
      <div className="theme-card">
        <div className="eyebrow">IPA superordinate theme {i + 1}/{themes.length}</div>
        <h2>{theme.title}</h2>
        <p>{theme.description}</p>
        <p>
          Grounded in {theme.n_papers} paper{theme.n_papers === 1 ? "" : "s"}
          <Cite n={theme.citation_ids} />
        </p>
        <blockquote style={{ borderLeft: "3px solid var(--gold)", paddingLeft: "1rem" }}>
          {(theme.evidence_extracts[0]?.text) || theme.analytic_memo}
          {theme.evidence_extracts[0] ? <Cite n={theme.evidence_extracts[0].citation_id} /> : null}
        </blockquote>
        <div className="dots">
          {themes.map((_, idx) => (
            <button key={idx} className={idx === i ? "on" : ""} onClick={() => setI(idx)} />
          ))}
        </div>
      </div>
      <div className="theme-card">
        <h3>First-order extracts</h3>
        <p>Verbatim abstract clauses — not generated quotations.</p>
        <ol>
          {theme.evidence_extracts.map((ex, idx) => (
            <li key={idx}>
              {ex.text} <Cite n={ex.citation_id} />
            </li>
          ))}
        </ol>
        <button className="btn ghost" onClick={() => setI((i + 1) % themes.length)}>
          Next theme →
        </button>
      </div>
    </div>
  );
}
