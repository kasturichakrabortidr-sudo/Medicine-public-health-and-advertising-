import type { ChartSpec } from "../../types";

const W = 720;
const ROW_H = 48;
const LEFT = 210;
const RIGHT = 88;
const AXIS_Y_PAD = 28;

export function ForestPlot({ spec }: { spec: ChartSpec }) {
  const rows = spec.data;
  const nums = rows.flatMap((r) => [Number(r.low), Number(r.high), Number(r.hr)]);
  const min = Math.min(0.55, ...nums) - 0.04;
  const max = Math.max(1.15, ...nums) + 0.04;
  const inner = W - LEFT - RIGHT;
  const h = AXIS_Y_PAD + rows.length * ROW_H + 42;
  const x = (v: number) => LEFT + ((v - min) / (max - min)) * inner;
  const ticks = [0.6, 0.7, 0.8, 0.9, 1.0, 1.1];

  return (
    <div className="forest-wrap">
      <div className="small muted">{spec.title}</div>
      <svg viewBox={`0 0 ${W} ${h}`} role="img" aria-label={spec.title} width="100%" height="100%">
        <line
          x1={x(1)}
          y1={12}
          x2={x(1)}
          y2={h - 16}
          stroke="#FF6433"
          strokeDasharray="3 3"
        />
        {ticks.map((t) => (
          <g key={t}>
            <line x1={x(t)} y1={h - 32} x2={x(t)} y2={h - 28} stroke="#132037" />
            <text x={x(t)} y={h - 16} fontSize="11" textAnchor="middle" fill="#5b6270">
              {t.toFixed(1)}
            </text>
          </g>
        ))}
        <text x={LEFT} y={h - 2} fontSize="11" fill="#4E7DF2">
          Favours intervention
        </text>
        <text x={W - 8} y={h - 2} fontSize="11" textAnchor="end" fill="#FF6433">
          Favours comparator
        </text>
        {rows.map((r, i) => {
          const y = AXIS_Y_PAD + i * ROW_H;
          const low = Number(r.low);
          const high = Number(r.high);
          const hr = Number(r.hr);
          return (
            <g key={String(r.name)}>
              <text x={8} y={y + 4} fontSize="12" fill="#111111">
                {String(r.name)}
              </text>
              <text x={8} y={y + 18} fontSize="9" fill="#777777">
                {String(r.stream || "")} · {String(r.grade || "")}
              </text>
              <line x1={x(low)} y1={y} x2={x(high)} y2={y} stroke="#111111" strokeWidth="2" />
              <rect x={x(hr) - 5} y={y - 5} width="10" height="10" fill="#4E7DF2" />
              <text x={W - 8} y={y + 4} fontSize="10" textAnchor="end" fill="#777777">
                {hr.toFixed(2)} ({low.toFixed(2)}–{high.toFixed(2)})
              </text>
            </g>
          );
        })}
        <text x={x(1)} y={10} fontSize="9" textAnchor="middle" fill="#FF6433">
          null (1.0)
        </text>
      </svg>
      {spec.note ? <div className="small muted">{spec.note}</div> : null}
    </div>
  );
}
