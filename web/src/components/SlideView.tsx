import type { Slide } from "../types";
import { Cited } from "./Cited";
import { StrategyChart } from "./charts/StrategyChart";

export function SlideView({ slide }: { slide: Slide }) {
  const refs = (slide.refs || []).filter((n) => n !== "" && n != null);
  const layout = slide.layout;
  return (
    <article className={`slide ${layout}`}>
      <header className="slide-head">
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

      {layout === "title" ? (
        <TitleBody slide={slide} />
      ) : layout === "close" ? (
        <CloseBody slide={slide} />
      ) : layout === "statement" ? (
        <StatementBody slide={slide} />
      ) : layout === "infographic" ? (
        <div className="slide-visual">
          {slide.chart ? <StrategyChart spec={slide.chart} height={420} /> : null}
        </div>
      ) : layout === "table" || layout === "references" ? (
        <TableBody slide={slide} />
      ) : layout === "cards" ? (
        <CardsBody slide={slide} />
      ) : (
        <StatementBody slide={slide} />
      )}

      {refs.length ? (
        <div className="slide-refs">
          {refs.map((n) => `[${n}]`).join(" ")} · Vancouver list at the end
        </div>
      ) : null}
    </article>
  );
}

function TitleBody({ slide }: { slide: Slide }) {
  return (
    <div className="slide-title-body">
      {slide.narrative ? (
        <p className="narrative">
          <Cited text={slide.narrative} />
        </p>
      ) : null}
    </div>
  );
}

function CloseBody({ slide }: { slide: Slide }) {
  return (
    <div className="slide-close-body">
      {slide.narrative ? (
        <p className="narrative">
          <Cited text={slide.narrative} />
        </p>
      ) : null}
      {slide.bullets ? <Bullets items={slide.bullets} /> : null}
    </div>
  );
}

function StatementBody({ slide }: { slide: Slide }) {
  return (
    <div className="slide-statement-body">
      {slide.narrative ? (
        <p className="narrative">
          <Cited text={slide.narrative} />
        </p>
      ) : null}
      {slide.bullets ? <Bullets items={slide.bullets} /> : null}
      <Callout callout={slide.callout} />
    </div>
  );
}

function TableBody({ slide }: { slide: Slide }) {
  return (
    <div className="slide-table-body">
      {slide.narrative ? (
        <p className="narrative">
          <Cited text={slide.narrative} />
        </p>
      ) : null}
      {slide.table ? <Table table={slide.table} /> : null}
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
        {cards.map((card) => (
          <div className="deck-card" key={card.title}>
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
      <strong>{callout.label}</strong>
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
