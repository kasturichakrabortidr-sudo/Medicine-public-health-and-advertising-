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
  if (spec.kind === "scatter") {
    return (
      <div className="chart">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="feasibility" type="number" name="Feasibility" />
            <YAxis dataKey="impact" type="number" name="Impact" />
            <Tooltip cursor={{ strokeDasharray: "3 3" }} />
            <Scatter data={spec.data} fill="#4e7df2" />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    );
  }
  if (spec.kind === "bar" || spec.kind === "house" || spec.kind === "compare") {
    const key = spec.series?.[0] || Object.keys(spec.data[0] || {}).find((k) => k !== "name") || "value";
    return (
      <div className="chart">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={spec.data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey={key} fill="#ff6433" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  }
  if (spec.kind === "people") {
    return (
      <div className="people">
        {spec.data.map((row) => (
          <div key={String(row.pmid || row.name)}>
            <strong>
              {row.control} vs {row.treat}
            </strong>
            <span>NNT {row.nnt}</span>
          </div>
        ))}
      </div>
    );
  }
  if (spec.kind === "spine" || spec.kind === "flow") {
    return (
      <ol className="spine">
        {spec.data.map((row) => (
          <li key={String(row.name)}>
            <strong>{row.name}</strong>
            <span>{row.detail || row.execute || row.means || ""}</span>
          </li>
        ))}
      </ol>
    );
  }
  if (spec.kind === "forest") {
    return (
      <ul className="forest">
        {spec.data.map((row) => (
          <li key={String(row.name)}>
            {row.name} · HR {row.hr} ({row.low}–{row.high})
          </li>
        ))}
      </ul>
    );
  }
  return spec.title ? <p className="chart-title">{spec.title}</p> : null;
}
