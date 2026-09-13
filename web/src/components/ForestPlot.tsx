import type { ForestRow, PooledEffect } from "../types";
import { Cite } from "./Cite";

function clamp(n: number, lo: number, hi: number) {
  return Math.max(lo, Math.min(hi, n));
}

export default function ForestPlot({
  rows,
  pooled,
}: {
  rows: ForestRow[];
  pooled?: PooledEffect | null;
}) {
  if (!rows.length) {
    return (
      <p>
        No hazard/odds/risk ratios with 95% CIs could be parsed from validated
        abstracts. The pipeline never fills missing effect sizes.
      </p>
    );
  }
  const extras = pooled?.value != null ? [pooled.ci_low, pooled.value, pooled.ci_high] : [];
  const values = rows.flatMap((r) => [r.ci_low, r.value, r.ci_high]).concat(extras);
  const min = Math.min(0.4, ...values) * 0.85;
  const max = Math.max(1.6, ...values) * 1.1;
  const pct = (v: number) => ((clamp(v, min, max) - min) / (max - min)) * 100;
  const nullX = pct(1);

  return (
    <div className="forest">
      <p style={{ color: "#e8d5a3" }}>
        Values &lt; 1 favour the intervention. Whiskers are 95% CIs copied from
        the source abstract — not modelled.
        {pooled?.value != null
          ? ` Diamond: fixed-effect inverse-variance of these parsed CIs (I² ${pooled.i_squared}%).`
          : ""}
      </p>
      {rows.map((row, i) => {
        const left = pct(row.ci_low);
        const right = pct(row.ci_high);
        return (
          <div className="forest-row" key={`${row.citation_id}-${i}`}>
            <div>
              <div>
                {row.label}
                <Cite n={row.citation_id} />
              </div>
              <small>
                {row.year} · {row.metric} {row.value} ({row.ci_low}–{row.ci_high}) · {row.outcome}
              </small>
            </div>
            <div className="forest-axis">
              <div className="forest-null" style={{ left: `${nullX}%` }} />
              <div
                className="forest-line"
                style={{ left: `${left}%`, width: `${Math.max(right - left, 1)}%` }}
              />
              <div className="forest-dot" style={{ left: `${pct(row.value)}%` }} />
            </div>
            <div>
              {row.metric} {row.value.toFixed(2)}
            </div>
          </div>
        );
      })}
      {pooled?.value != null ? (
        <div className="forest-row forest-pooled">
          <div>
            <div>Pooled IV (fixed effect)</div>
            <small>
              n={pooled.n_trials} · I² {pooled.i_squared}% · {pooled.metric} {pooled.value} (
              {pooled.ci_low}–{pooled.ci_high})
            </small>
          </div>
          <div className="forest-axis">
            <div className="forest-null" style={{ left: `${nullX}%` }} />
            <div
              className="forest-line"
              style={{
                left: `${pct(pooled.ci_low)}%`,
                width: `${Math.max(pct(pooled.ci_high) - pct(pooled.ci_low), 1)}%`,
              }}
            />
            <div className="forest-diamond" style={{ left: `${pct(pooled.value)}%` }} />
          </div>
          <div>
            {pooled.metric} {pooled.value.toFixed(2)}
          </div>
        </div>
      ) : null}
    </div>
  );
}
