import type { PooledEffect } from "../types";
import { Cite } from "./Cite";

export default function FunnelPlot({ pooled }: { pooled?: PooledEffect | null }) {
  const points = pooled?.funnel || [];
  if (!points.length) {
    return (
      <p>
        No funnel points: the inverse-variance summary needs at least one named
        trial with a parsed 95% CI.
      </p>
    );
  }
  const xs = points.map((p) => p.log_effect);
  const ys = points.map((p) => p.precision);
  const minX = Math.min(-0.6, ...xs) - 0.05;
  const maxX = Math.max(0.2, ...xs) + 0.05;
  const maxY = Math.max(8, ...ys) * 1.15;
  const w = 640;
  const h = 320;
  const padL = 48;
  const padR = 16;
  const padT = 16;
  const padB = 36;
  const xOf = (v: number) => padL + ((v - minX) / (maxX - minX)) * (w - padL - padR);
  const yOf = (v: number) => padT + (1 - v / maxY) * (h - padT - padB);
  const nullX = xOf(0);

  return (
    <div>
      <p style={{ color: "#e8d5a3" }}>
        Contour of precision (1/SE of ln HR) vs ln(effect). Points are named
        trials whose 95% CIs were parsed from abstracts — not modelled. The
        vertical line is HR = 1.
      </p>
      <svg viewBox={`0 0 ${w} ${h}`} className="funnel-svg" role="img" aria-label="Funnel plot of parsed hazard ratios">
        <line x1={nullX} y1={padT} x2={nullX} y2={h - padB} stroke="rgba(255,255,255,0.45)" />
        <line x1={padL} y1={h - padB} x2={w - padR} y2={h - padB} stroke="rgba(255,255,255,0.25)" />
        <text x={nullX} y={h - 8} fill="#e8d5a3" fontSize="12" textAnchor="middle">
          ln HR = 0
        </text>
        <text x={12} y={h / 2} fill="#e8d5a3" fontSize="11" transform={`rotate(-90 12 ${h / 2})`}>
          Precision (1/SE)
        </text>
        {points.map((p, i) => (
          <circle
            key={`${p.citation_id}-${i}`}
            cx={xOf(p.log_effect)}
            cy={yOf(p.precision)}
            r={6}
            fill="#c9a227"
          />
        ))}
      </svg>
      <ul className="funnel-legend">
        {points.map((p, i) => (
          <li key={`${p.citation_id}-${i}`}>
            {p.label} <Cite n={p.citation_id || undefined} /> · HR {p.value.toFixed(2)} · SE(ln) {p.se.toFixed(3)}
          </li>
        ))}
      </ul>
    </div>
  );
}
