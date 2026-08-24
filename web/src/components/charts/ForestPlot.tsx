import { useEffect, useRef, useState } from "react";
import type { ChartSpec } from "../../types";

export function ForestPlot({ spec }: { spec: ChartSpec }) {
  const host = useRef<HTMLDivElement>(null);
  const [box, setBox] = useState({ w: 880, h: 420 });

  useEffect(() => {
    const el = host.current;
    if (!el) return;
    const apply = () => {
      const w = Math.floor(el.clientWidth);
      const h = Math.floor(el.clientHeight);
      if (w > 40 && h > 40) setBox({ w, h });
    };
    apply();
    const ro = new ResizeObserver(apply);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const rows = spec.data;
  const nums = rows.flatMap((r) => [Number(r.low), Number(r.high), Number(r.hr)]);
  const min = Math.min(0.55, ...nums) - 0.04;
  const max = Math.max(1.15, ...nums) + 0.04;
  const W = box.w;
  const H = box.h;
  const LEFT = Math.max(168, Math.round(W * 0.26));
  const RIGHT = 108;
  const TOP = 22;
  const BOTTOM = 36;
  const inner = W - LEFT - RIGHT;
  const rowH = (H - TOP - BOTTOM) / Math.max(rows.length, 1);
  const x = (v: number) => LEFT + ((v - min) / (max - min)) * inner;
  const ticks = [0.6, 0.7, 0.8, 0.9, 1.0, 1.1];

  return (
    <div className="forest-wrap">
      {spec.title ? <div className="small muted">{spec.title}</div> : null}
      <div className="forest-plot" ref={host}>
        <svg
          className="forest-svg"
          viewBox={`0 0 ${W} ${H}`}
          preserveAspectRatio="none"
          role="img"
          aria-label={spec.title}
          width="100%"
          height="100%"
        >
          <line x1={x(1)} y1={8} x2={x(1)} y2={H - 28} stroke="#c4844a" strokeDasharray="3 3" />
          {ticks.map((t) => (
            <g key={t}>
              <line x1={x(t)} y1={H - 30} x2={x(t)} y2={H - 26} stroke="#132037" />
              <text x={x(t)} y={H - 14} fontSize="12" textAnchor="middle" fill="#5b6270">
                {t.toFixed(1)}
              </text>
            </g>
          ))}
          <text x={LEFT} y={H - 2} fontSize="12" fill="#2a6f6f">
            Favours intervention
          </text>
          <text x={W - 8} y={H - 2} fontSize="12" textAnchor="end" fill="#8b2e2e">
            Favours comparator
          </text>
          {rows.map((r, i) => {
            const y = TOP + i * rowH + rowH * 0.45;
            const low = Number(r.low);
            const high = Number(r.high);
            const hr = Number(r.hr);
            return (
              <g key={String(r.name)}>
                <text x={8} y={y - 6} fontSize="13" fill="#0b1220">
                  {String(r.name)}
                </text>
                <text x={8} y={y + 10} fontSize="10" fill="#2a6f6f">
                  {String(r.stream || "")} · {String(r.grade || "")}
                </text>
                <line x1={x(low)} y1={y} x2={x(high)} y2={y} stroke="#132037" strokeWidth="3" />
                <rect x={x(hr) - 6} y={y - 6} width="12" height="12" fill="#c4844a" />
                <text x={W - 8} y={y + 4} fontSize="11" textAnchor="end" fill="#5b6270">
                  {hr.toFixed(2)} ({low.toFixed(2)}–{high.toFixed(2)})
                </text>
              </g>
            );
          })}
          <text x={x(1)} y={14} fontSize="10" textAnchor="middle" fill="#c4844a">
            null (1.0)
          </text>
        </svg>
      </div>
      {spec.note ? <div className="small muted">{spec.note}</div> : null}
    </div>
  );
}
