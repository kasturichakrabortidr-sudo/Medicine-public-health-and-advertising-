import type { StrategyPack } from "../types";
import { StrategyChart } from "./charts/StrategyChart";

export function DashboardTab({ pack }: { pack: StrategyPack }) {
  const d = pack.dashboard;
  return (
    <div>
      <div className="topbar">
        <div>
          <h1>Measurement room</h1>
          <p>
            Leading indicators must move before revenue. Kill-criteria live on every
            intervention.
          </p>
        </div>
      </div>

      {pack.doctrine.scienceLead && (
        <div className="alert info">{pack.doctrine.scienceLead}</div>
      )}
      {d.alerts.map((a) => (
        <div className={`alert ${a.level}`} key={a.text}>
          {a.text}
        </div>
      ))}

      <div className="kpi-row" style={{ margin: "16px 0" }}>
        {d.kpis.map((k) => (
          <div className="kpi" key={k.id}>
            <div className="label">{k.tone} · {k.label}</div>
            <div className="value">
              {k.value}
              <span style={{ fontSize: 16 }}> {k.unit}</span>
            </div>
            <div className="meta">Target {k.target}</div>
          </div>
        ))}
      </div>

      {d.meaning?.length ? (
        <section className="card" style={{ marginBottom: 16 }}>
          <h3>Scientific prize — what we are trying to capture</h3>
          <StrategyChart
            spec={{
              kind: "people",
              title: "Published event rates per 100 patients",
              data: d.meaning,
            }}
          />
        </section>
      ) : null}

      {d.spine?.length ? (
        <section className="card" style={{ marginBottom: 16 }}>
          <h3>Science to solution through execution</h3>
          <StrategyChart
            spec={{
              kind: "spine",
              title: "Cited finding → campaign move → KPI",
              data: d.spine,
            }}
          />
        </section>
      ) : null}

      <div className="grid-2">
        <section className="card">
          <h3>Revenue parent metric</h3>
          <StrategyChart
            spec={{
              kind: "line",
              title: "Index, Q0 = 100 (planning path)",
              data: d.revenue,
              series: ["revenue", "initiation", "conviction"],
            }}
          />
        </section>
        <section className="card">
          <h3>Adoption funnel</h3>
          <StrategyChart
            spec={{ kind: "funnel", title: "HCP funnel snapshot", data: d.funnel }}
          />
        </section>
        <section className="card">
          <h3>Evidence mix in the working file</h3>
          <StrategyChart spec={{ kind: "pie", title: "Stream weight", data: d.evidenceMix }} />
        </section>
        <section className="card">
          <h3>Segment heat</h3>
          <StrategyChart
            spec={{
              kind: "bar",
              title: "Commercial impact by segment",
              data: d.segments.map((s) => ({ name: s.name, value: s.impact })),
            }}
          />
        </section>
      </div>

      <section className="card" style={{ marginTop: 18 }}>
        <h3>Intervention board</h3>
        <table className="table">
          <thead>
            <tr>
              <th>Move</th>
              <th>COM-B lever</th>
              <th>Segment</th>
              <th>Impact</th>
              <th>Feasibility</th>
              <th>Science anchor</th>
              <th>Kill-criterion</th>
            </tr>
          </thead>
          <tbody>
            {pack.interventions.map((iv) => (
              <tr key={iv.id}>
                <td>
                  <strong>{iv.name}</strong>
                  <div className="small muted">{iv.promise}</div>
                </td>
                <td>{iv.lever}</td>
                <td>{iv.segment}</td>
                <td>{iv.impact}</td>
                <td>{iv.feasibility}</td>
                <td className="small">{iv.evidenceAnchor || "—"}</td>
                <td>{iv.kill}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="card" style={{ marginTop: 18 }}>
        <h3>Governance</h3>
        <table className="table">
          <thead>
            <tr>
              <th>Cadence</th>
              <th>Forum</th>
              <th>Looks at</th>
            </tr>
          </thead>
          <tbody>
            {d.governance.map((g) => (
              <tr key={g.cadence}>
                <td>{g.cadence}</td>
                <td>{g.forum}</td>
                <td>{g.looksAt}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
