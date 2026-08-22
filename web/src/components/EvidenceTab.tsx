import type { StrategyPack } from "../types";

export function EvidenceTab({ pack }: { pack: StrategyPack }) {
  const ev = pack.evidence;
  const lead = ev?.lead || pack.dashboard.campaignLead;
  const records = ev?.records || pack.dashboard.citations || [];
  const gaps = ev?.gaps || pack.dashboard.evidenceGaps || [];
  const pubmed = ev?.pubmed || pack.dashboard.pubmed || [];

  return (
    <div>
      <div className="topbar">
        <div>
          <h1>Sourced science</h1>
          <p>
            The campaign lead is the highest-leverage validated citation — not a slogan.
            Uncited brief items stay gaps.
          </p>
        </div>
      </div>

      {lead && (
        <section className="card" style={{ marginBottom: 16 }}>
          <h3>Campaign lead</h3>
          <p>{lead.statement}</p>
          <p className="small muted">{lead.why}</p>
          <ul className="bullets">
            {(lead.citations || []).map((c) => (
              <li key={c.id}>
                <strong>{c.short}</strong> — {c.claim}
                <div className="small muted">
                  PMID {c.pmid || "—"} · doi:{c.doi || "—"}
                </div>
              </li>
            ))}
          </ul>
          {lead.doNotClaim?.filter(Boolean).length ? (
            <div className="alert mlr">
              Do not claim: {lead.doNotClaim.filter(Boolean).join(" · ")}
            </div>
          ) : null}
        </section>
      )}

      <section className="card">
        <h3>Validated register</h3>
        <table className="table">
          <thead>
            <tr>
              <th>Source</th>
              <th>Citation</th>
              <th>Design / N</th>
              <th>Grade</th>
              <th>What we may say</th>
            </tr>
          </thead>
          <tbody>
            {records.map((r) => (
              <tr key={r.id}>
                <td>
                  <strong>{r.short}</strong>
                  <div className="small muted">{r.stream}</div>
                </td>
                <td>
                  {r.url ? (
                    <a href={r.url} target="_blank" rel="noreferrer">
                      {r.citation}
                    </a>
                  ) : (
                    r.citation
                  )}
                </td>
                <td>
                  {r.design} · n={r.n ?? "—"}
                </td>
                <td>{r.grade}</td>
                <td>{r.claim_permitted}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {records.length === 0 && (
          <p className="muted">No catalog match. Do not invent a trial name or effect size.</p>
        )}
      </section>

      <section className="card" style={{ marginTop: 18 }}>
        <h3>Unvalidated brief items</h3>
        {gaps.length === 0 ? (
          <p className="muted">Every brief evidence line resolved to a citation.</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Stream</th>
                <th>Item from the brief</th>
                <th>Needed</th>
              </tr>
            </thead>
            <tbody>
              {gaps.map((g) => (
                <tr key={g.item}>
                  <td>{g.stream}</td>
                  <td>{g.item}</td>
                  <td>{g.needed}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {pubmed.length > 0 && (
        <section className="card" style={{ marginTop: 18 }}>
          <h3>PubMed — retrieved, not yet lead</h3>
          <p className="small muted">
            Live NCBI hits for the product/indication. Confirm full text before promoting any of these
            to the campaign lead.
          </p>
          <ul className="bullets">
            {pubmed.map((p) => (
              <li key={p.pmid}>
                <a href={p.url} target="_blank" rel="noreferrer">
                  {p.citation}
                </a>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
