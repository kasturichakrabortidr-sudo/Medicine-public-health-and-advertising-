import type { StrategyPack } from "../types";

export function PapersScreen({ pack }: { pack: StrategyPack }) {
  const records = pack.evidence?.records || [];
  const gaps = pack.evidence?.gaps || [];
  return (
    <section className="panel">
      <h1>Papers</h1>
      <p className="lede">
        Numbered register for this brief. Independent class papers are labelled as such — not trials of{" "}
        {pack.meta.brand}.
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
