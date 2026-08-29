import { useState } from "react";
import type { EvidenceRecord } from "../types";
import { Cite } from "./Cite";

export default function KeyEvidenceCarousel({ records }: { records: EvidenceRecord[] }) {
  const cards = records.slice(0, 12);
  const [i, setI] = useState(0);
  if (!cards.length) {
    return <p>No pivotal trial or guideline records survived validation in this run.</p>;
  }
  const rec = cards[i];
  const effect = rec.effects[0];
  return (
    <div className="paper-carousel">
      <div className="theme-card">
        <div className="eyebrow">
          Anchor evidence {i + 1}/{cards.length}
        </div>
        <h3>{rec.title}</h3>
        <p>
          {rec.issuing_body}
          {rec.year ? ` · ${rec.year}` : ""} · {rec.source_family.replaceAll("_", " ")}
          <Cite n={rec.citation_id} />
        </p>
        {effect ? (
          <p className="lede" style={{ color: "#e8d5a3" }}>
            {effect.metric} {effect.value} (95% CI {effect.ci_low}–{effect.ci_high}) · {effect.outcome}
          </p>
        ) : (
          <p>{(rec.snippets[0] || rec.abstract || "").slice(0, 280)}</p>
        )}
        <p className="muted-note">
          {rec.doi ? `https://doi.org/${rec.doi}` : rec.url}
        </p>
        <div className="dots">
          {cards.map((_, idx) => (
            <button
              key={idx}
              className={idx === i ? "on" : ""}
              onClick={() => setI(idx)}
              aria-label={`Show evidence card ${idx + 1}`}
            />
          ))}
        </div>
      </div>
      <div className="theme-card">
        <h3>Why this card is here</h3>
        <p>
          Every card is a registry-validated record (Crossref DOI, Europe PMC,
          ClinicalTrials.gov, or an official URL). Effect sizes appear only when
          a 95% CI was parsed from the abstract.
        </p>
        <ul>
          <li>{rec.is_guideline ? "Classified as a guideline / technical package." : "Primary or secondary research paper."}</li>
          <li>{rec.is_oa ? "Open access." : "Paywalled metadata + abstract only."}</li>
          <li>{rec.claims.length ? `Coded claims: ${rec.claims.length}.` : "No taxonomy claims fired on the abstract."}</li>
        </ul>
        <button className="btn ghost" onClick={() => setI((i + 1) % cards.length)}>
          Next paper →
        </button>
      </div>
    </div>
  );
}
