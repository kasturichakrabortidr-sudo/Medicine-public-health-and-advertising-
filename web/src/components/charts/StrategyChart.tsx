import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
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

const PALETTE = ["#4E7DF2", "#FF6433", "#000000", "#4E7DF2", "#FF6433", "#111111"];

function ChartFrame({ title, note, children }: { title?: string; note?: string; children: React.ReactNode }) {
  return (
    <div className="chart-fill">
      {title ? <div className="small muted">{title}</div> : null}
      <div className="chart-fill-plot">{children}</div>
      {note ? <div className="small muted">{note}</div> : null}
    </div>
  );
}

export function StrategyChart({ spec }: { spec: ChartSpec; height?: number }) {
  if (spec.kind === "forest") return <ForestPlot spec={spec} />;
  if (spec.kind === "box") return <BoxPlot spec={spec} />;
  if (spec.kind === "people" || spec.kind === "compare" || spec.kind === "spine" || spec.kind === "flow" || spec.kind === "house") {
    return <Infographic spec={spec} />;
  }

  if (spec.kind === "pie") {
    return (
      <ChartFrame title={spec.title}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={spec.data} dataKey="value" nameKey="name" outerRadius="70%">
              {spec.data.map((_, i) => (
                <Cell key={i} fill={PALETTE[i % PALETTE.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </ChartFrame>
    );
  }

  if (spec.kind === "line") {
    const series = spec.series || ["value"];
    return (
      <ChartFrame title={spec.title} note={spec.note}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={spec.data} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(11, 18, 32, 0.08)" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Legend />
            {series.map((s, i) => (
              <Line key={s} type="monotone" dataKey={s} stroke={PALETTE[i % PALETTE.length]} strokeWidth={2} dot />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </ChartFrame>
    );
  }

  if (spec.kind === "scatter") {
    const points = spec.data.map((d) => ({
      name: String(d.name ?? ""),
      x: Number(d.x),
      y: Number(d.y),
    }));
    return (
      <ChartFrame title={spec.title} note={spec.note}>
        <div className="scatter-layout">
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 12, right: 12, left: 8, bottom: 28 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(11,18,32,0.08)" />
              <XAxis type="number" dataKey="x" name={spec.xLabel || "x"} domain={[0, 100]} label={{ value: spec.xLabel || "Feasibility", position: "insideBottom", offset: -12, fontSize: 11 }} />
              <YAxis type="number" dataKey="y" name={spec.yLabel || "y"} domain={[0, 100]} label={{ value: spec.yLabel || "Impact", angle: -90, position: "insideLeft", fontSize: 11 }} />
              <Tooltip cursor={{ strokeDasharray: "3 3" }} />
              <Scatter data={points} fill="#4E7DF2" />
            </ScatterChart>
          </ResponsiveContainer>
          <ul className="scatter-legend">
            {points.map((d) => (
              <li key={String(d.name)}>
                <strong>{d.name}</strong>
                <span>
                  {spec.xLabel || "Feasibility"} {d.x} · {spec.yLabel || "Impact"} {d.y}
                </span>
              </li>
            ))}
          </ul>
        </div>
      </ChartFrame>
    );
  }

  if (spec.kind === "diverging") {
    const data = spec.data.map((d) => ({
      ...d,
      pos: Number(d.value) > 0 ? Number(d.value) : 0,
      neg: Number(d.value) < 0 ? Number(d.value) : 0,
    }));
    return (
      <ChartFrame title={spec.title} note={spec.note}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(11,18,32,0.08)" />
            <XAxis type="number" domain={[-80, 80]} />
            <YAxis type="category" dataKey="name" width={120} />
            <Tooltip />
            <Bar dataKey="neg" fill="#8b2e2e" />
            <Bar dataKey="pos" fill="#2a6f6f" />
          </BarChart>
        </ResponsiveContainer>
      </ChartFrame>
    );
  }

  if (spec.kind === "funnel") {
    return (
      <ChartFrame title={spec.title} note={spec.note}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={spec.data} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(11,18,32,0.08)" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="value" fill="#132037" />
          </BarChart>
        </ResponsiveContainer>
      </ChartFrame>
    );
  }

  return (
    <ChartFrame title={spec.title} note={spec.note || spec.unit}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={spec.data} margin={{ top: 8, right: 12, left: 0, bottom: 28 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(11,18,32,0.08)" />
          <XAxis dataKey="name" interval={0} />
          <YAxis />
          <Tooltip />
            <Bar dataKey="value" fill="#4E7DF2">
            <LabelList dataKey="value" position="top" fontSize={11} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}
