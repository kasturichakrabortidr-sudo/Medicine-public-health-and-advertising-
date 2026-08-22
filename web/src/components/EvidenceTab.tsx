import type { StrategyPack } from "../types";
import { StrategyChart } from "./charts/StrategyChart";

export function EvidenceTab({ pack }: { pack: StrategyPack }) {
  const ev = pack.evidence;
  const lead = ev?.lead || pack.dashboard.campaignLead;
  const records = ev?.records || pack.dashboard.citations || [];
  const gaps = ev?.gaps || pack.dashboard.evidenceGaps || [];
  const pubmed = ev?.pubmed || pack.dashboard.pubmed || [];
  const refs = pack.references || ev?.references || pack.dashboard.references || [];

  return (
    <div>
      <div className="topbar">
        <div>
          <h1>Numbered papers</h1>
          <p>
            Every claim we are willing to lead with has a number. Uncited brief items stay
            gaps. The full Vancouver list is at the bottom.
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

      {(pack.dashboard.meaning?.length || pack.dashboard.compare?.length) ? (
        <section className="card" style={{ marginBottom: 16 }}>
          <h3>What the published rates mean</h3>
          {pack.dashboard.meaning?.length ? (
            <StrategyChart
              spec={{
                kind: "people",
                title: "Events in a clinic of 100 — published rates, not a model",
                data: pack.dashboard.meaning,
              }}
            />
          ) : null}
          {pack.dashboard.compare?.length ? (
            <StrategyChart
              spec={{
                kind: "compare",
                title: "Comparator vs intervention on the published scale",
                data: pack.dashboard.compare,
              }}
            />
          ) : null}
        </section>
      ) : null}

      {pack.dashboard.spine?.length ? (
        <section className="card" style={{ marginBottom: 16 }}>
          <h3>Science to execution</h3>
          <p className="small muted">
            Each cited finding names a prize, a barrier, a campaign move, and a measure.
          </p>
          <StrategyChart
            spec={{
              kind: "spine",
              title: "Science → means → barrier → execution → we measure",
              data: pack.dashboard.spine,
            }}
          />
        </section>
      ) : null}

      <section className="card">
        <h3>Validated register</h3>
        <table className="table">
          <thead>
            <tr>
              <th>No.</th>
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
                <td>[{r.ref || "—"}]</td>
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

      <section className="card" style={{ marginTop: 18 }}>
        <h3>Reference list</h3>
        <p className="small muted">Vancouver. Same numbers as the superscripts in the working file and the deck.</p>
        <ol className="ref-list">
          {refs.map((r) => (
            <li key={r.n} value={r.n}>
              {r.url ? (
                <a href={r.url} target="_blank" rel="noreferrer">
                  {r.citation}
                </a>
              ) : (
                r.citation
              )}
            </li>
          ))}
        </ol>
        {refs.length === 0 && <p className="muted">No numbered paper matched this brief.</p>}
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
