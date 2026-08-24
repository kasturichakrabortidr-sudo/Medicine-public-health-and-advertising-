import type { ChartSpec } from "../../types";

function num(value: string | number | undefined, fallback = 0): number {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function dots(rate: number): number {
  return Math.max(0, Math.min(100, Math.round(rate)));
}

function PeoplePanel({
  label,
  rate,
  saved,
  unit,
}: {
  label: string;
  rate: number;
  saved?: number;
  unit: string;
}) {
  const events = dots(rate);
  const rescued = saved ? dots(saved) : 0;
  return (
    <div className="people-panel">
      <div className="people-label">{label}</div>
      <div className="people-rate">
        {rate}
        <span> / 100</span>
      </div>
      <div className="people-grid" aria-hidden="true">
        {Array.from({ length: 100 }, (_, i) => {
          const kind = i < events ? "event" : i < events + rescued ? "saved" : "ok";
          return <span key={i} className={`dot ${kind}`} />;
        })}
      </div>
      <div className="small muted">{unit}</div>
    </div>
  );
}

function PeopleVisual({ spec }: { spec: ChartSpec }) {
  const row = spec.data[0];
  if (!row) return null;
  const control = num(row.control);
  const treat = num(row.treat);
  const arr = num(row.arr, Math.max(0, control - treat));
  return (
    <div className="infographic people">
      <div className="people-pair">
        <PeoplePanel label={String(row.control_label || "Comparator")} rate={control} unit={String(row.unit || spec.unit || "")} />
        <PeoplePanel
          label={String(row.treat_label || "Intervention")}
          rate={treat}
          saved={arr}
          unit="crimson = events · teal = events avoided"
        />
        <div className="nnt-card">
          <div className="kicker">NNT</div>
          <div className="nnt-value">{row.nnt || "—"}</div>
          <p>
            Treat {row.nnt || "—"} to prevent 1 event
            {row.horizon ? ` over ${row.horizon}` : ""}.
          </p>
          <p className="small muted">PMID {row.pmid || "—"}</p>
        </div>
      </div>
    </div>
  );
}

function CompareVisual({ spec }: { spec: ChartSpec }) {
  const row = spec.data[0];
  if (!row) return null;
  const left = num(row.left);
  const right = num(row.right);
  const max = Math.max(left, right, 1);
  return (
    <div className="infographic compare">
      <div className="compare-row">
        <div className="compare-col">
          <div className="people-label">{row.left_label || "Comparator"}</div>
          <div className="compare-num">{left}</div>
          <div className="compare-bar">
            <span style={{ height: `${(left / max) * 100}%` }} />
          </div>
        </div>
        <div className="compare-delta">
          <div className="kicker">Difference</div>
          <strong>{row.delta !== "" && row.delta != null ? row.delta : Math.abs(left - right)}</strong>
          <p>{row.claim}</p>
          <p className="small muted">
            PMID {row.pmid || "—"} · {row.horizon || ""}
          </p>
        </div>
        <div className="compare-col treat">
          <div className="people-label">{row.right_label || "Intervention"}</div>
          <div className="compare-num">{right}</div>
          <div className="compare-bar">
            <span style={{ height: `${(right / max) * 100}%` }} />
          </div>
        </div>
      </div>
    </div>
  );
}

const SPINE_STEPS = [
  ["science", "Science"],
  ["means", "Means"],
  ["barrier", "Barrier"],
  ["execute", "Execution"],
  ["measure", "We measure"],
] as const;

function SpineVisual({ spec }: { spec: ChartSpec }) {
  const rows = spec.data.slice(0, 3);
  return (
    <div className="infographic spine">
      <div className="spine-head">
        {SPINE_STEPS.map(([_, label], i) => (
          <div key={label} className="spine-step-label">
            {i + 1}. {label}
          </div>
        ))}
      </div>
      {rows.map((row) => (
        <div key={String(row.name)} className="spine-row">
          {SPINE_STEPS.map(([key, label]) => (
            <div key={key} className={`spine-cell ${key}`}>
              <div className="spine-cell-kicker">
                {label}
                {key === "science" ? ` · ${row.name}` : ""}
                {key === "execute" && row.move ? ` · ${row.move}` : ""}
              </div>
              <p>{row[key] || "—"}</p>
              {key === "science" ? <div className="small muted">PMID {row.pmid || "—"}</div> : null}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

export function Infographic({ spec }: { spec: ChartSpec }) {
  if (spec.kind === "people") return <PeopleVisual spec={spec} />;
  if (spec.kind === "compare") return <CompareVisual spec={spec} />;
  return <SpineVisual spec={spec} />;
}
