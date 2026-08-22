import type { ChartSpec } from "../../types";

export function BoxPlot({ spec }: { spec: ChartSpec }) {
  const rows = spec.data;
  const W = 560;
  const H = 220;
  const padL = 36;
  const padB = 36;
  const padT = 16;
  const innerW = W - padL - 16;
  const innerH = H - padT - padB;
  const col = innerW / Math.max(rows.length, 1);
  const y = (v: number) => padT + innerH - (v / 10) * innerH;

  return (
    <div>
      <div className="small muted">{spec.title}</div>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label={spec.title}>
        {[0, 2, 4, 6, 8, 10].map((t) => (
          <g key={t}>
            <line x1={padL} x2={W - 8} y1={y(t)} y2={y(t)} stroke="rgba(11,18,32,0.08)" />
            <text x={4} y={y(t) + 3} fontSize="9" fill="#5b6270">
              {t}
            </text>
          </g>
        ))}
        {rows.map((r, i) => {
          const cx = padL + col * i + col / 2;
          const min = Number(r.min);
          const q1 = Number(r.q1);
          const median = Number(r.median);
          const q3 = Number(r.q3);
          const max = Number(r.max);
          const boxW = Math.min(46, col * 0.45);
          return (
            <g key={String(r.name)}>
              <line x1={cx} x2={cx} y1={y(min)} y2={y(max)} stroke="#132037" />
              <line x1={cx - 8} x2={cx + 8} y1={y(min)} y2={y(min)} stroke="#132037" />
              <line x1={cx - 8} x2={cx + 8} y1={y(max)} y2={y(max)} stroke="#132037" />
              <rect
                x={cx - boxW / 2}
                y={y(q3)}
                width={boxW}
                height={Math.max(2, y(q1) - y(q3))}
                fill="#2a6f6f"
                opacity="0.85"
              />
              <line
                x1={cx - boxW / 2}
                x2={cx + boxW / 2}
                y1={y(median)}
                y2={y(median)}
                stroke="#f4efe6"
                strokeWidth="2"
              />
              <text
                x={cx}
                y={H - 8}
                fontSize="10"
                textAnchor="middle"
                fill="#0b1220"
              >
                {String(r.name).replace(" ", "\n")}
              </text>
            </g>
          );
        })}
      </svg>
      {spec.unit ? <div className="small muted">{spec.unit}</div> : null}
    </div>
  );
}
