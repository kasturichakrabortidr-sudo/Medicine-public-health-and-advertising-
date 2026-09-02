import type { ChartSpec, Slide } from "../types";
import { SlideChart } from "./SlideChart";

export function SlideCanvas({ slide }: { slide: Slide }) {
  const layout = slide.layout;
  const source = slide.source || "";
  return (
    <article className={`slide ${layout}`}>
      {slide.page ? <div className="page">{slide.page}</div> : null}
      {layout === "title" ? (
        <Title slide={slide} />
      ) : layout === "idea" || layout === "close" ? (
        <Dark slide={slide} />
      ) : layout === "insight" ? (
        <Insight slide={slide} />
      ) : layout === "references" || layout === "table" ? (
        <TableSlide slide={slide} />
      ) : (
        <DefaultSlide slide={slide} />
      )}
      {source ? <div className="source">{source}</div> : null}
    </article>
  );
}

function Title({ slide }: { slide: Slide }) {
  return (
    <div className="title-body">
      <div className="kicker">{slide.kicker}</div>
      <h2>{slide.title}</h2>
      {slide.subtitle ? <p className="sub">{slide.subtitle}</p> : null}
      <div className="cards three">
        {(slide.cards || []).map((c) => (
          <div className="card" key={c.meta || c.title}>
            <span>{c.meta}</span>
            <strong>{c.title}</strong>
            <p>{c.body}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function Dark({ slide }: { slide: Slide }) {
  return (
    <div className="dark-body">
      <div className="kicker">{slide.kicker}</div>
      <h2>{slide.title}</h2>
      {slide.subtitle || slide.narrative ? <p className="sub">{slide.subtitle || slide.narrative}</p> : null}
      <div className="cards">
        {(slide.cards || []).map((c) => (
          <div className="card" key={c.title}>
            <strong>{c.title}</strong>
            <p>{c.body}</p>
          </div>
        ))}
      </div>
      {slide.callout ? <p className="callout">{slide.callout.text}</p> : null}
    </div>
  );
}

function Insight({ slide }: { slide: Slide }) {
  return (
    <div className="insight-body">
      <div className="copy">
        <div className="kicker">{slide.kicker}</div>
        <h2>{slide.title}</h2>
        {slide.subtitle ? <p className="sub">{slide.subtitle}</p> : null}
        {slide.narrative ? <p className="narrative">{slide.narrative}</p> : null}
      </div>
      <div className="main">
        {(slide.stats || []).length ? (
          <div className="stats">
            {slide.stats!.map((s) => (
              <div className={`stat ${s.accent || "blue"}`} key={s.value + s.caption}>
                <strong>{s.value}</strong>
                <p>{s.caption}</p>
              </div>
            ))}
          </div>
        ) : null}
        {slide.soWhat ? <p className="so-what">{slide.soWhat}</p> : null}
        {slide.chart ? <SlideChart spec={slide.chart} /> : null}
      </div>
    </div>
  );
}

function DefaultSlide({ slide }: { slide: Slide }) {
  return (
    <>
      <header>
        <div className="kicker">{slide.kicker}</div>
        <h2>{slide.title}</h2>
        {slide.subtitle ? <p className="sub">{slide.subtitle}</p> : null}
      </header>
      {(slide.cards || []).length ? (
        <div className={`cards ${slide.cards!.length > 3 ? "five" : ""}`}>
          {slide.cards!.map((c) => (
            <div className={`card ${c.accent || ""}`} key={c.title}>
              <strong>{c.title}</strong>
              <p>{c.body}</p>
              {c.meta ? <span>{c.meta}</span> : null}
            </div>
          ))}
        </div>
      ) : null}
      {slide.chart ? <SlideChart spec={slide.chart} /> : null}
      {slide.narrative ? <p className="narrative">{slide.narrative}</p> : null}
    </>
  );
}

function TableSlide({ slide }: { slide: Slide }) {
  const table = slide.table;
  return (
    <>
      <header>
        <div className="kicker">{slide.kicker}</div>
        <h2>{slide.title}</h2>
      </header>
      {table ? (
        <table>
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
                {row.map((cell, j) => (
                  <td key={j}>{cell}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
    </>
  );
}

export type { ChartSpec };
