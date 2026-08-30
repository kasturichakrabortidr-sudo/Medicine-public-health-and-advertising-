const STEPS = [
  ["01", "Search", "Journals, guidelines, UN, NGO, trials"],
  ["02", "Screen", "On-topic for the brief (PRISMA counts)"],
  ["03", "Validate", "DOI / PMID / NCT / official URL must resolve"],
  ["04", "Collate", "PICO-tied claim coding from abstracts"],
  ["05", "Quant", "Frequency of facts + forest of parsed CIs"],
  ["06", "Qual", "Narrative review + IPA themes"],
  ["07", "Deck", "Numbered visual slides, ready to drop in"],
];

export default function WorkflowInfographic() {
  return (
    <div className="infographic" aria-label="Seven-step evidence workflow">
      {STEPS.map(([n, title, detail], i) => (
        <div className="infographic-step" key={n}>
          <span className="infographic-n">{n}</span>
          <strong>{title}</strong>
          <p>{detail}</p>
          {i < STEPS.length - 1 ? <span className="infographic-arrow" aria-hidden>→</span> : null}
        </div>
      ))}
    </div>
  );
}
