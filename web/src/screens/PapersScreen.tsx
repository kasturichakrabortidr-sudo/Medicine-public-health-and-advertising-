import { printAs } from "../print";
import type { StrategyPack } from "../types";

export function PapersScreen({ pack }: { pack: StrategyPack }) {
  const records = pack.evidence?.records || [];
  const gaps = pack.evidence?.gaps || [];
  return (
    <section className="panel papers-page">
      <header className="doc-bar no-print">
        <div>
          <p className="eyebrow">03 · Papers</p>
          <h1>Numbered register</h1>
        </div>
        <button type="button" onClick={() => printAs("work")}>
          Print PDF
        </button>
      </header>
      <p className="lede">
        Independent class papers are labelled as such — not trials of {pack.meta.brand}.
      </p>
      <ol className="papers">
        {records.map((row) => (
          <li key={row.id}>
            <strong>
              [{row.ref}] {row.short}
            </strong>
            <p>{row.claim_permitted}</p>
            <p className="muted">
              PMID {row.pmid || "—"} · {row.journal} {row.year} · {row.stream}
            </p>
          </li>
        ))}
      </ol>
      {gaps.length ? (
        <>
          <h2>Gaps</h2>
          <ul className="gaps">
            {gaps.map((g) => (
              <li key={g.item}>
                {g.item} — {g.needed}
              </li>
            ))}
          </ul>
        </>
      ) : null}
    </section>
  );
}
