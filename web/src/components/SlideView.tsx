import type { Slide } from "../types";
import { Cited } from "./Cited";
import { PaperAnchor, paperHref, useRefLinks } from "../links";
import { StrategyChart } from "./charts/StrategyChart";

export function SlideView({ slide }: { slide: Slide }) {
  const refs = (slide.refs || []).filter((n) => n !== "" && n != null);
  const catalog = useRefLinks();
  const byN = new Map(catalog.map((r) => [r.n, r]));
  return (
    <article className={`slide ${slide.layout}`}>
      <div className="kicker">{slide.kicker}</div>
      <h2>
        <Cited text={slide.title} />
      </h2>
      {slide.subtitle ? (
        <p className="sub">
          <Cited text={slide.subtitle} />
        </p>
      ) : null}

      {slide.layout === "infographic" ? (
        <>
          <p className="narrative">
            <Cited text={slide.narrative} />
          </p>
          {slide.chart ? <StrategyChart spec={slide.chart} height={280} /> : null}
          {slide.bullets ? <Bullets items={slide.bullets} /> : null}
          <Callout callout={slide.callout} />
        </>
      ) : slide.layout === "references" ? (
        <>
          <p className="narrative">
            <Cited text={slide.narrative} />
          </p>
          {slide.table ? <Table table={slide.table} /> : null}
        </>
      ) : slide.layout === "title" || slide.layout === "close" || slide.layout === "insight" ? (
        <>
          <p className="narrative">
            <Cited text={slide.narrative} />
          </p>
          {slide.bullets ? <Bullets items={slide.bullets} /> : null}
          <Callout callout={slide.callout} />
        </>
      ) : (
        <div className="slide-body">
          <div>
            <p className="narrative">
              <Cited text={slide.narrative} />
            </p>
            {slide.bullets ? <Bullets items={slide.bullets} /> : null}
            <Callout callout={slide.callout} />
            {slide.table && !slide.chart ? <Table table={slide.table} /> : null}
          </div>
          <div>
            {slide.chart ? <StrategyChart spec={slide.chart} height={220} /> : null}
            {slide.table && slide.chart ? <Table table={slide.table} /> : null}
          </div>
        </div>
      )}
      {refs.length ? (
        <div className="slide-refs">
          Refs{" "}
          {refs.map((n, i) => (
            <span key={`${n}-${i}`}>
              {i ? " " : null}
              <PaperAnchor href={paperHref(byN.get(Number(n)))} className="cite-link">
                [{n}]
              </PaperAnchor>
            </span>
          ))}{" "}
          · full list at the end
        </div>
      ) : null}
    </article>
  );
}

function Bullets({ items }: { items: string[] }) {
  return (
    <ul className="bullets">
      {items.map((b) => (
        <li key={b}>
          <Cited text={b} />
        </li>
      ))}
    </ul>
  );
}

function Callout({ callout }: { callout?: { label: string; text: string } }) {
  if (!callout) return null;
  return (
    <div className="callout">
      <strong>{callout.label}. </strong>
      <Cited text={callout.text} />
    </div>
  );
}

function Table({ table }: { table: { headers: string[]; rows: string[][] } }) {
  return (
    <table className="table">
      <thead>
        <tr>
          {table.headers.map((h) => (
            <th key={h}>{h}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {table.rows.map((row, i) => (
          <tr key={i}>
            {row.map((c, j) => (
              <td key={j}>
                <Cited text={c} />
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
