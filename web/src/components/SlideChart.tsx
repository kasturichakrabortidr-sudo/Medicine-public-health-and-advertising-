import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ChartSpec } from "../types";

export function SlideChart({ spec }: { spec: ChartSpec }) {
  if (spec.kind === "people") return <PeopleChart spec={spec} />;
  if (spec.kind === "forest") return <ForestChart spec={spec} />;
  if (spec.kind === "spine") return <SpineChart spec={spec} />;
  if (spec.kind === "house") return <HouseChart spec={spec} />;
  if (spec.kind === "compare") return <CompareChart spec={spec} />;
  if (spec.kind === "flow") return <FlowChart spec={spec} />;
  if (spec.kind === "scatter") {
    return (
      <div className="chart">
        {spec.title ? <p className="chart-title">{spec.title}</p> : null}
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart>
            <CartesianGrid strokeDasharray="3 3" stroke="#e8e4dc" />
            <XAxis dataKey="feasibility" type="number" name="Feasibility" />
            <YAxis dataKey="impact" type="number" name="Impact" />
            <Tooltip cursor={{ strokeDasharray: "3 3" }} />
            <Scatter data={spec.data} fill="#4e7df2" />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    );
  }
  if (spec.kind === "bar" || spec.kind === "line") {
    const key = spec.series?.[0] || Object.keys(spec.data[0] || {}).find((k) => k !== "name") || "value";
    return (
      <div className="chart">
        {spec.title ? <p className="chart-title">{spec.title}</p> : null}
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={spec.data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e8e4dc" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey={key} fill="#ff6433" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  }
  return spec.title ? <p className="chart-title">{spec.title}</p> : null;
}

function n(value: unknown): number {
  const x = Number(value);
  return Number.isFinite(x) ? x : 0;
}

function PeopleChart({ spec }: { spec: ChartSpec }) {
  const row = spec.data[0] || {};
  const control = Math.max(0, Math.min(100, Math.round(n(row.control))));
  const treat = Math.max(0, Math.min(100, Math.round(n(row.treat))));
  const saved = Math.max(0, Math.min(100, Math.round(n(row.arr) || Math.max(0, control - treat))));
  return (
    <div className="people-chart">
      <PeopleGrid label={String(row.control_label || "Comparator")} events={control} saved={0} tone="event" />
      <PeopleGrid label={String(row.treat_label || "Intervention")} events={treat} saved={saved} tone="saved" />
      <div className="nnt-card">
        <span>NNT</span>
        <strong>{String(row.nnt || "—")}</strong>
        <p>
          Treat {String(row.nnt || "—")} to prevent 1 event
          {row.horizon ? ` over ${row.horizon}` : ""}. PMID {String(row.pmid || "—")}.
        </p>
      </div>
    </div>
  );
}

function PeopleGrid({
  label,
  events,
  saved,
  tone,
}: {
  label: string;
  events: number;
  saved: number;
  tone: "event" | "saved";
}) {
  return (
    <div className="people-grid">
      <span className="muted">{label}</span>
      <strong>
        {events} / 100
      </strong>
      <div className="dots">
        {Array.from({ length: 100 }, (_, i) => {
          const cls = i < events ? "dot event" : i < events + saved ? "dot saved" : "dot";
          return <i className={cls} key={i} />;
        })}
      </div>
      <span className="muted">{tone === "event" ? "event" : "event + avoided"}</span>
    </div>
  );
}

function ForestChart({ spec }: { spec: ChartSpec }) {
  const nums = spec.data.flatMap((r) => [n(r.low), n(r.high), n(r.hr)]);
  const lo = Math.min(0.55, Math.min(...nums, 1) - 0.04);
  const hi = Math.max(1.15, Math.max(...nums, 1) + 0.04);
  const pct = (v: number) => `${((v - lo) / (hi - lo)) * 100}%`;
  return (
    <div className="forest-chart">
      {spec.title ? <p className="chart-title">{spec.title}</p> : null}
      <div className="forest-axis">
        <span>Favours intervention</span>
        <span>null 1.0</span>
        <span>Favours comparator</span>
      </div>
      <ul>
        {spec.data.map((row) => {
          const low = n(row.low);
          const high = n(row.high);
          const hr = n(row.hr);
          const left = Math.min(low, high);
          const width = Math.max(Math.abs(high - low), 0.01);
          return (
            <li key={String(row.name)}>
              <div className="forest-label">
                <strong>{row.name}</strong>
                <span>
                  {row.stream} · {row.grade}
                </span>
              </div>
              <div className="forest-track">
                <i className="null" style={{ left: pct(1) }} />
                <i
                  className="ci"
                  style={{ left: pct(left), width: `${(width / (hi - lo)) * 100}%` }}
                />
                <i className="hr" style={{ left: pct(hr) }} />
              </div>
              <span className="forest-num">
                {hr.toFixed(2)} ({low.toFixed(2)}–{high.toFixed(2)})
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

function SpineChart({ spec }: { spec: ChartSpec }) {
  const cols = [
    ["science", "1. Science"],
    ["means", "2. Means"],
    ["barrier", "3. Barrier"],
    ["execute", "4. Execution"],
    ["measure", "5. We measure"],
  ] as const;
  return (
    <div className="spine-chart">
      <p className="chart-title">{spec.title || "Science → means → barrier → execution → we measure"}</p>
      {spec.data.slice(0, 3).map((row) => (
        <div className="spine-row" key={String(row.name)}>
          {cols.map(([key, label]) => (
            <div className={`spine-cell ${key}`} key={key}>
              <span>{key === "science" ? `${label} · ${row.name}` : label}</span>
              <p>
                {String(row[key] || "—")}
                {key === "science" && row.pmid ? ` PMID ${row.pmid}.` : ""}
              </p>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

function HouseChart({ spec }: { spec: ChartSpec }) {
  return (
    <div className="house-chart">
      <p className="chart-title">THEME</p>
      <h3>{spec.title}</h3>
      <div className={`cards ${spec.data.length > 3 ? "five" : ""}`}>
        {spec.data.map((row) => (
          <div className="card" key={String(row.name)}>
            <span>{row.ref || "Pillar"}</span>
            <strong>{row.name}</strong>
            <p>{row.line}</p>
            {row.proof ? <em>{String(row.proof)}</em> : null}
          </div>
        ))}
      </div>
    </div>
  );
}

function CompareChart({ spec }: { spec: ChartSpec }) {
  const row = spec.data[0] || {};
  const left = n(row.left);
  const right = n(row.right);
  const mx = Math.max(left, right, 1);
  return (
    <div className="compare-chart">
      <CompareCol label={String(row.left_label || "Comparator")} value={left} max={mx} tone="event" />
      <div className="compare-mid">
        <span>Difference</span>
        <strong>{String(row.delta ?? Math.abs(left - right))}</strong>
        <p>
          {row.claim} PMID {String(row.pmid || "—")}.
        </p>
      </div>
      <CompareCol label={String(row.right_label || "Intervention")} value={right} max={mx} tone="saved" />
    </div>
  );
}

function CompareCol({
  label,
  value,
  max,
  tone,
}: {
  label: string;
  value: number;
  max: number;
  tone: string;
}) {
  return (
    <div className="compare-col">
      <span className="muted">{label}</span>
      <strong>{value}</strong>
      <div className="compare-bar">
        <i className={tone} style={{ height: `${Math.max(8, (value / max) * 100)}%` }} />
      </div>
    </div>
  );
}

function FlowChart({ spec }: { spec: ChartSpec }) {
  return (
    <ol className="flow-chart">
      {spec.data.map((row, i) => (
        <li key={String(row.name)}>
          <span>{i + 1}</span>
          <strong>{row.name}</strong>
          <p>{row.detail || row.claim || ""}</p>
        </li>
      ))}
    </ol>
  );
}
