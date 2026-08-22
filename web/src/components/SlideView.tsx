import type { Slide } from "../types";
import { StrategyChart } from "./charts/StrategyChart";

export function SlideView({ slide }: { slide: Slide }) {
  return (
    <article className={`slide ${slide.layout}`}>
      <div className="kicker">{slide.kicker}</div>
      <h2>{slide.title}</h2>
      {slide.subtitle ? <p className="sub">{slide.subtitle}</p> : null}

      {slide.layout === "infographic" ? (
        <>
          <p className="narrative">{slide.narrative}</p>
          {slide.chart ? <StrategyChart spec={slide.chart} height={280} /> : null}
          {slide.bullets ? (
            <ul className="bullets">
              {slide.bullets.map((b) => (
                <li key={b}>{b}</li>
              ))}
            </ul>
          ) : null}
          {slide.callout ? (
            <div className="callout">
              <strong>{slide.callout.label}. </strong>
              {slide.callout.text}
            </div>
          ) : null}
        </>
      ) : slide.layout === "title" || slide.layout === "close" || slide.layout === "insight" ? (
        <>
          <p className="narrative">{slide.narrative}</p>
          {slide.bullets ? (
            <ul className="bullets">
              {slide.bullets.map((b) => (
                <li key={b}>{b}</li>
              ))}
            </ul>
          ) : null}
          {slide.callout ? (
            <div className="callout">
              <strong>{slide.callout.label}. </strong>
              {slide.callout.text}
            </div>
          ) : null}
        </>
      ) : (
        <div className="slide-body">
          <div>
            <p className="narrative">{slide.narrative}</p>
            {slide.bullets ? (
              <ul className="bullets">
                {slide.bullets.map((b) => (
                  <li key={b}>{b}</li>
                ))}
              </ul>
            ) : null}
            {slide.callout ? (
              <div className="callout">
                <strong>{slide.callout.label}. </strong>
                {slide.callout.text}
              </div>
            ) : null}
            {slide.table && !slide.chart ? <Table table={slide.table} /> : null}
          </div>
          <div>
            {slide.chart ? <StrategyChart spec={slide.chart} height={220} /> : null}
            {slide.table && slide.chart ? <Table table={slide.table} /> : null}
          </div>
        </div>
      )}
    </article>
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
              <td key={j}>{c}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
