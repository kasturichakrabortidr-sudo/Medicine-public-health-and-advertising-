import type { Slide } from "../types";
import { Cited } from "./Cited";
import { StrategyChart } from "./charts/StrategyChart";

export function SlideView({ slide }: { slide: Slide }) {
  const refs = (slide.refs || []).filter((n) => n !== "" && n != null);
  const layout = slide.layout;
  const source = slide.source || slide.footnote || "";
  return (
    <article className={`slide ${layout}`}>
      {slide.page ? <div className="slide-page">{slide.page}</div> : null}
      {layout === "title" ? (
        <TitleBody slide={slide} />
      ) : layout === "idea" || layout === "close" ? (
        <DarkBody slide={slide} />
      ) : layout === "insight" ? (
        <InsightBody slide={slide} />
      ) : (
        <>
          <header className="slide-head">
            <div className="slide-rules" aria-hidden="true" />
            <div className="kicker">{slide.kicker}</div>
            <h2>
              <Cited text={slide.title} />
            </h2>
            {slide.subtitle ? (
              <p className="sub">
                <Cited text={slide.subtitle} />
              </p>
            ) : null}
          </header>

          {layout === "split" ? (
            <SplitBody slide={slide} />
          ) : layout === "infographic" || layout === "chart" ? (
            <FigureBody slide={slide} />
          ) : layout === "table" || layout === "references" ? (
            <TableBody slide={slide} />
          ) : layout === "cards" ? (
            <CardsBody slide={slide} />
          ) : (
            <FigureBody slide={slide} />
          )}
        </>
      )}

      {source ? (
        <div className="slide-source">
          <Cited text={source} />
        </div>
      ) : refs.length ? (
        <div className="slide-refs">
          {refs.map((n) => `[${n}]`).join(" ")} · Vancouver list at the end
        </div>
      ) : null}
    </article>
  );
}

function Figure({ slide }: { slide: Slide }) {
  if (!slide.chart) return null;
  return (
    <div className="slide-visual">
      <StrategyChart spec={slide.chart} />
    </div>
  );
}

function TitleBody({ slide }: { slide: Slide }) {
  return (
    <div className="slide-title-body">
      <div className="kicker">{slide.kicker}</div>
      <h2>
        <Cited text={slide.title} />
      </h2>
      {slide.subtitle ? (
        <p className="sub">
          <Cited text={slide.subtitle} />
        </p>
      ) : null}
      {slide.narrative ? (
        <p className="lede">
          <Cited text={slide.narrative} />
        </p>
      ) : null}
      {slide.cards?.length ? (
        <div className="title-chips">
          {slide.cards.map((card) => (
            <div className={`title-chip accent-${card.accent || "blue"}`} key={card.title}>
              <div className="chip-meta">{card.meta}</div>
              <h3>{card.title}</h3>
              <p>
                <Cited text={card.body} />
              </p>
            </div>
          ))}
        </div>
      ) : (
        <Figure slide={slide} />
      )}
    </div>
  );
}

function DarkBody({ slide }: { slide: Slide }) {
  return (
    <div className="slide-dark-body">
      <div className="kicker">{slide.kicker}</div>
      <h2>
        <Cited text={slide.title} />
      </h2>
      {slide.subtitle ? (
        <p className="sub">
          <Cited text={slide.subtitle} />
        </p>
      ) : null}
      {slide.narrative ? (
        <p className="lede">
          <Cited text={slide.narrative} />
        </p>
      ) : null}
      {slide.cards?.length ? (
        <div className={`idea-grid n-${slide.cards.length}`}>
          {slide.cards.map((card, i) => (
            <div className={`idea-card accent-${card.accent || (i % 2 === 0 ? "blue" : "orange")}`} key={card.title}>
              <h3>{card.title}</h3>
              <p>
                <Cited text={card.body} />
              </p>
            </div>
          ))}
        </div>
      ) : (
        <Figure slide={slide} />
      )}
      {slide.callout ? (
        <p className="next-line">
          <Cited text={slide.callout.text} />
        </p>
      ) : null}
    </div>
  );
}

function InsightBody({ slide }: { slide: Slide }) {
  const stats = slide.stats?.length ? slide.stats : (slide.cards || []).slice(0, 2).map((c) => ({
    value: c.title,
    caption: c.body,
    accent: c.accent,
  }));
  return (
    <div className="slide-insight">
      <div className="slide-insight-copy">
        <div className="slide-rules" aria-hidden="true" />
        <div className="kicker">{slide.kicker}</div>
        <h2>
          <Cited text={slide.title} />
        </h2>
        {slide.narrative ? (
          <p className="lede">
            <Cited text={slide.narrative} />
          </p>
        ) : null}
      </div>
      <div className="slide-insight-main">
        {stats.length ? (
          <div className={`stat-cards n-${stats.length}`}>
            {stats.map((stat, i) => (
              <div className={`stat-card accent-${stat.accent || (i % 2 === 0 ? "blue" : "orange")}`} key={`${stat.value}-${i}`}>
                <div className="stat-value">{stat.value}</div>
                <p>
                  <Cited text={stat.caption} />
                </p>
              </div>
            ))}
          </div>
        ) : null}
        {slide.soWhat ? (
          <p className="so-what">
            <Cited text={slide.soWhat} />
          </p>
        ) : null}
        {slide.chart ? <Figure slide={slide} /> : null}
        {!stats.length && slide.cards ? <MiniCards cards={slide.cards} /> : null}
        {!stats.length && slide.table ? <Table table={slide.table} /> : null}
        <Callout callout={slide.callout} />
      </div>
    </div>
  );
}

function FigureBody({ slide }: { slide: Slide }) {
  return (
    <div className="slide-figure-body">
      {slide.narrative ? (
        <p className="narrative figure-note">
          <Cited text={slide.narrative} />
        </p>
      ) : null}
      {slide.stats?.length ? (
        <div className={`stat-cards n-${slide.stats.length} compact`}>
          {slide.stats.map((stat, i) => (
            <div className={`stat-card accent-${stat.accent || (i % 2 === 0 ? "blue" : "orange")}`} key={`${stat.value}-${i}`}>
              <div className="stat-value">{stat.value}</div>
              <p>
                <Cited text={stat.caption} />
              </p>
            </div>
          ))}
        </div>
      ) : null}
      <Figure slide={slide} />
      {slide.soWhat ? (
        <p className="so-what">
          <Cited text={slide.soWhat} />
        </p>
      ) : null}
    </div>
  );
}

function SplitBody({ slide }: { slide: Slide }) {
  return (
    <div className="slide-split">
      <div className="slide-split-copy">
        {slide.narrative ? (
          <p className="narrative">
            <Cited text={slide.narrative} />
          </p>
        ) : null}
        {slide.bullets ? <Bullets items={slide.bullets} /> : null}
        {slide.table ? <Table table={slide.table} /> : null}
        <Callout callout={slide.callout} />
      </div>
      <div className="slide-split-visual">
        {slide.chart ? (
          <div className="slide-visual">
            <StrategyChart spec={slide.chart} />
          </div>
        ) : null}
        {slide.cards ? <MiniCards cards={slide.cards} /> : null}
      </div>
    </div>
  );
}

function TableBody({ slide }: { slide: Slide }) {
  return (
    <div className={`slide-table-body ${slide.chart ? "with-chart" : ""}`}>
      {slide.narrative ? (
        <p className="narrative">
          <Cited text={slide.narrative} />
        </p>
      ) : null}
      <div className="table-wrap">
        {slide.table ? <Table table={slide.table} /> : null}
        {slide.chart ? (
          <div className="slide-visual">
            <StrategyChart spec={slide.chart} />
          </div>
        ) : null}
      </div>
    </div>
  );
}

function CardsBody({ slide }: { slide: Slide }) {
  const cards = slide.cards || [];
  const n = cards.length;
  return (
    <div className="slide-cards-body">
      {slide.narrative ? (
        <p className="narrative">
          <Cited text={slide.narrative} />
        </p>
      ) : null}
      <div className={`card-grid n-${n}`}>
        {cards.map((card, i) => (
          <div className={`deck-card accent-${card.accent || (i % 2 === 0 ? "blue" : "orange")}`} key={card.title}>
            <h3>{card.title}</h3>
            <p>
              <Cited text={card.body} />
            </p>
            {card.meta ? (
              <div className="deck-card-meta">
                <Cited text={card.meta} />
              </div>
            ) : null}
          </div>
        ))}
      </div>
      <Figure slide={slide} />
    </div>
  );
}

function MiniCards({ cards }: { cards: { title: string; body: string; meta?: string; accent?: "blue" | "orange" }[] }) {
  return (
    <div className="mini-cards">
      {cards.map((card, i) => (
        <div className={`deck-card accent-${card.accent || (i % 2 === 0 ? "blue" : "orange")}`} key={card.title}>
          <h3>{card.title}</h3>
          <p>
            <Cited text={card.body} />
          </p>
          {card.meta ? (
            <div className="deck-card-meta">
              <Cited text={card.meta} />
            </div>
          ) : null}
        </div>
      ))}
    </div>
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
              <td key={j} className={j === 0 ? "ref-col" : ""}>
                <Cited text={c} />
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
