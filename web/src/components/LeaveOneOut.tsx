import {
  Bar,
  BarChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { PooledEffect } from "../types";
import { Cite } from "./Cite";

export default function LeaveOneOut({
  pooled,
}: {
  pooled?: PooledEffect | null;
}) {
  const rows = pooled?.leave_one_out || [];
  if (!rows.length) {
    return (
      <p>
        Leave-one-out needs at least two named-trial HR CIs. Missing numbers are
        never filled in.
      </p>
    );
  }
  const data = rows.map((row) => ({
    name: (row.omit || "trial").replace(/\s+\(\d{4}\)$/, ""),
    value: row.fixed_value,
  }));
  return (
    <div>
      <p style={{ color: "#e8d5a3" }}>
        Each bar is the fixed-effect pooled HR after dropping one trial. The
        gold line is the full-corpus fixed-effect HR ({pooled?.value ?? "—"}).
      </p>
      <div className="chart-panel" style={{ height: 360 }}>
        <ResponsiveContainer>
          <BarChart data={data} layout="vertical" margin={{ left: 8, right: 24 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
            <XAxis type="number" domain={["auto", "auto"]} stroke="#d7e4e1" />
            <YAxis type="category" dataKey="name" width={160} stroke="#d7e4e1" />
            <Tooltip />
            {pooled?.value != null ? (
              <ReferenceLine x={pooled.value} stroke="#c9a227" strokeDasharray="4 4" />
            ) : null}
            <Bar dataKey="value" fill="#7fb9b2" name="Pooled HR omitting this trial" />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <ul>
        {rows.slice(0, 8).map((row) => (
          <li key={`${row.citation_id}-${row.omit}`}>
            Omit {row.omit} <Cite n={row.citation_id || undefined} /> → HR{" "}
            {row.fixed_value} ({row.fixed_ci_low}–{row.fixed_ci_high})
          </li>
        ))}
      </ul>
    </div>
  );
}
