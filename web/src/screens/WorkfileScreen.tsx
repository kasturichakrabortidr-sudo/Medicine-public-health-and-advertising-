import { printAs } from "../print";
import type { StrategyPack, WorkBlock, WorkPhase } from "../types";

const TEXT_KEYS: (keyof WorkPhase)[] = [
  "restatedAsk",
  "restatedNeed",
  "current",
  "required",
  "enemy",
  "theme",
  "scienceLead",
  "leadStatement",
  "lead",
  "bet",
  "warn",
  "rule",
  "who",
  "note",
  "parent",
  "caveat",
  "include",
  "exclude",
  "position",
];

const LIST_KEYS: (keyof WorkPhase)[] = [
  "questions",
  "hypotheses",
  "known",
  "unknown",
  "inventory",
  "ask",
  "hierarchy",
  "assets",
  "roadmap",
  "competitors",
];

const TABLE_KEYS: (keyof WorkPhase)[] = [
  "pico",
  "assumptions",
  "forefront",
  "gaps",
  "concord",
  "discord",
  "silent",
  "concerns",
  "drivers",
  "fourway",
  "house",
  "objections",
  "stages",
  "grid",
  "kpis",
];

export function WorkfileScreen({
  pack,
  busy,
  onExport,
}: {
  pack: StrategyPack;
  busy: boolean;
  onExport: () => void;
}) {
  const work = pack.workfile;
  if (!work) return <p className="muted">No working file on this pack.</p>;
  return (
    <section className="workfile">
      <header className="doc-bar no-print">
        <div>
          <p className="eyebrow">Working file</p>
          <h1>{pack.meta.brand}</h1>
          <p className="muted">
            {pack.meta.therapyArea} · {work.refCount} references · {work.validatedCount} numbered papers
          </p>
        </div>
        <div className="actions">
          <button type="button" onClick={() => printAs("work")}>
            Print PDF
          </button>
          <button className="primary" type="button" disabled={busy} onClick={onExport}>
            {busy ? "Building markdown…" : "Download markdown"}
          </button>
        </div>
      </header>

      <article className="work-cover">
        <p className="kicker">Source of truth</p>
        <h2>{pack.doctrine.name}</h2>
        <p className="lede">{work.howBuilt}</p>
        <p>
          <strong>The bet.</strong> {pack.doctrine.bet}
        </p>
        <p>
          <strong>The enemy.</strong> {pack.doctrine.enemy}
        </p>
      </article>

      {work.cannotClaim?.length ? (
        <div className="warn">
          <strong>Do not claim</strong>
          <ul>
            {work.cannotClaim.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {work.phases.map((phase) => (
        <PhaseCard key={phase.id} phase={phase} />
      ))}

      {work.openQuestions?.length ? (
        <article className="phase">
          <p className="kicker">Open</p>
          <h2>Questions that still block a claim</h2>
          <ul>
            {work.openQuestions.map((q) => (
              <li key={q}>{q}</li>
            ))}
          </ul>
        </article>
      ) : null}
    </section>
  );
}

function PhaseCard({ phase }: { phase: WorkPhase }) {
  return (
    <article className="phase">
      <p className="kicker">
        {phase.id} · Working file
      </p>
      <h2>{phase.title}</h2>
      <p className="muted">{phase.howBuilt}</p>
      {TEXT_KEYS.map((key) =>
        phase[key] ? (
          <p key={key}>
            <strong>{label(key)}.</strong> {String(phase[key])}
          </p>
        ) : null,
      )}
      {LIST_KEYS.map((key) => {
        const items = phase[key] as string[] | undefined;
        if (!items?.length) return null;
        return (
          <div key={key}>
            <h3>{label(key)}</h3>
            <ul>
              {items.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        );
      })}
      {TABLE_KEYS.map((key) => {
        const block = phase[key] as WorkBlock | undefined;
        if (!block?.rows?.length) return null;
        return <BlockTable key={key} title={label(key)} block={block} />;
      })}
    </article>
  );
}

function BlockTable({ title, block }: { title: string; block: WorkBlock }) {
  const headers = block.headers || [];
  return (
    <div className="work-table">
      <h3>{title}</h3>
      <table>
        {headers.length ? (
          <thead>
            <tr>
              {headers.map((h) => (
                <th key={h}>{h}</th>
              ))}
            </tr>
          </thead>
        ) : null}
        <tbody>
          {block.rows!.map((row, i) => (
            <tr key={i}>
              {row.map((cell, j) => (
                <td key={j}>{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function label(key: string): string {
  return key
    .replace(/([A-Z])/g, " $1")
    .replace(/_/g, " ")
    .replace(/^./, (c) => c.toUpperCase());
}
