import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ChartSpec } from "../../types";
import { BoxPlot } from "./BoxPlot";
import { ForestPlot } from "./ForestPlot";
import { Infographic } from "./Infographic";

const PALETTE = ["#132037", "#c4844a", "#2a6f6f", "#8b2e2e", "#5c7a5c", "#1b2c49"];

export function StrategyChart({ spec, height = 260 }: { spec: ChartSpec; height?: number }) {
  if (spec.kind === "forest") return <ForestPlot spec={spec} />;
  if (spec.kind === "box") return <BoxPlot spec={spec} />;
  if (spec.kind === "people" || spec.kind === "compare" || spec.kind === "spine") {
    return <Infographic spec={spec} />;
  }

  if (spec.kind === "pie") {
    return (
      <div>
        <div className="small muted">{spec.title}</div>
        <ResponsiveContainer width="100%" height={height}>
          <PieChart>
            <Pie data={spec.data} dataKey="value" nameKey="name" outerRadius={90} label>
              {spec.data.map((_, i) => (
                <Cell key={i} fill={PALETTE[i % PALETTE.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (spec.kind === "line") {
    const series = spec.series || ["value"];
    return (
      <div>
        <div className="small muted">{spec.title}</div>
        <ResponsiveContainer width="100%" height={height}>
          <LineChart data={spec.data}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(11,18,32,0.08)" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Legend />
            {series.map((s, i) => (
              <Line key={s} type="monotone" dataKey={s} stroke={PALETTE[i % PALETTE.length]} strokeWidth={2} dot />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (spec.kind === "scatter") {
    return (
      <div>
        <div className="small muted">{spec.title}</div>
        <ResponsiveContainer width="100%" height={height}>
          <ScatterChart>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(11,18,32,0.08)" />
            <XAxis type="number" dataKey="x" name={spec.xLabel || "x"} domain={[0, 100]} />
            <YAxis type="number" dataKey="y" name={spec.yLabel || "y"} domain={[0, 100]} />
            <Tooltip cursor={{ strokeDasharray: "3 3" }} />
            <Scatter data={spec.data} fill="#c4844a" />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (spec.kind === "diverging") {
    const data = spec.data.map((d) => ({
      ...d,
      pos: Number(d.value) > 0 ? Number(d.value) : 0,
      neg: Number(d.value) < 0 ? Number(d.value) : 0,
    }));
    return (
      <div>
        <div className="small muted">{spec.title}</div>
        <ResponsiveContainer width="100%" height={height}>
          <BarChart data={data} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(11,18,32,0.08)" />
            <XAxis type="number" domain={[-80, 80]} />
            <YAxis type="category" dataKey="name" width={120} />
            <Tooltip />
            <Bar dataKey="neg" fill="#8b2e2e" />
            <Bar dataKey="pos" fill="#2a6f6f" />
          </BarChart>
        </ResponsiveContainer>
        {spec.note ? <div className="small muted">{spec.note}</div> : null}
      </div>
    );
  }

  if (spec.kind === "funnel") {
    return (
      <div>
        <div className="small muted">{spec.title}</div>
        <ResponsiveContainer width="100%" height={height}>
          <BarChart data={spec.data}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(11,18,32,0.08)" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="value" fill="#132037" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  }

  const names = spec.data.map((d) => String(d.name ?? ""));
  const wide = names.some((n) => n.length > 12);
  const tipLabel = (_: string, rows: { payload?: Record<string, string | number> }[]) =>
    String(rows?.[0]?.payload?.full || rows?.[0]?.payload?.name || "");
  if (wide) {
    const labelW = Math.min(220, Math.max(140, ...names.map((n) => Math.round(n.length * 7.2))));
    return (
      <div>
        <div className="small muted">{spec.title}</div>
        <ResponsiveContainer width="100%" height={Math.max(height, 72 * spec.data.length)}>
          <BarChart data={spec.data} layout="vertical" margin={{ left: 4, right: 16, top: 8, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(11,18,32,0.08)" />
            <XAxis type="number" allowDecimals={false} />
            <YAxis type="category" dataKey="name" width={labelW} interval={0} tick={{ fontSize: 13 }} />
            <Tooltip labelFormatter={tipLabel} />
            <Bar dataKey="value" fill="#c4844a" />
          </BarChart>
        </ResponsiveContainer>
        {spec.note ? <div className="small muted">{spec.note}</div> : spec.unit ? <div className="small muted">{spec.unit}</div> : null}
      </div>
    );
  }

  return (
    <div>
      <div className="small muted">{spec.title}</div>
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={spec.data}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(11,18,32,0.08)" />
          <XAxis dataKey="name" interval={0} />
          <YAxis />
          <Tooltip labelFormatter={tipLabel} />
          <Bar dataKey="value" fill="#c4844a" />
        </BarChart>
      </ResponsiveContainer>
      {spec.note ? <div className="small muted">{spec.note}</div> : spec.unit ? <div className="small muted">{spec.unit}</div> : null}
    </div>
  );
}
