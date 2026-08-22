import type { Slide } from "../types";
import { Cited } from "./Cited";
import { PaperAnchor, paperHref, useRefLinks } from "../links";
import { StrategyChart } from "./charts/StrategyChart";

export function SlideView({ slide }: { slide: Slide }) {
  const refs = (slide.refs || []).filter((n) => n !== "" && n != null);
  const catalog = useRefLinks();
  const byN = new Map(catalog.map((r) => [r.n, r]));
  const bullets = (slide.bullets || []).filter(Boolean);
  const chart = slide.chart;
  const table = slide.layout === "references" ? slide.table : chart ? undefined : slide.table;
  const board = slide.board;
  const flow = slide.flow;
  const stat = slide.stat;
  const visual = chart || board || flow || stat || table;

  return (
    <article className={`slide ${slide.layout}`}>
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
        {slide.narrative ? (
          <p className="narrative">
            <Cited text={slide.narrative} />
          </p>
        ) : null}
      </header>

      <div className="slide-visual">
        {chart ? <StrategyChart spec={chart} height={slide.layout === "visual" ? 340 : 260} /> : null}
        {board?.cards?.length ? <Board cards={board.cards} /> : null}
        {flow?.steps?.length ? <Flow steps={flow.steps} /> : null}
        {stat?.items?.length ? <Stat items={stat.items} /> : null}
        {table ? <Table table={table} /> : null}
        {!visual && bullets.length ? <Bullets items={bullets} /> : null}
        <Callout callout={slide.callout} />
      </div>

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

function Board({ cards }: { cards: NonNullable<Slide["board"]>["cards"] }) {
  return (
    <div className={`slide-board n${Math.min(cards.length, 5)}`}>
      {cards.map((card, i) => (
        <div className="slide-card" key={`${card.title}-${i}`}>
          {card.kicker ? <div className="kicker">{card.kicker}</div> : null}
          <h3>
            <Cited text={card.title} />
          </h3>
          {card.body ? (
            <p>
              <Cited text={card.body} />
            </p>
          ) : null}
          {card.ref ? <div className="small muted">{card.ref}</div> : null}
        </div>
      ))}
    </div>
  );
}

function Flow({ steps }: { steps: NonNullable<Slide["flow"]>["steps"] }) {
  return (
    <ol className={`slide-flow n${Math.min(steps.length, 4)}`}>
      {steps.map((step) => (
        <li className="flow-step" key={`${step.n}-${step.title}`}>
          <div className="flow-n">{step.n}</div>
          <h3>
            <Cited text={step.title} />
          </h3>
          <p>
            <Cited text={step.body} />
          </p>
        </li>
      ))}
    </ol>
  );
}

function Stat({ items }: { items: NonNullable<Slide["stat"]>["items"] }) {
  return (
    <div className={`slide-stat n${Math.min(items.length, 3)}`}>
      {items.map((item, i) => (
        <div className="stat-item" key={`${item.value}-${i}`}>
          {item.kicker ? <div className="kicker">{item.kicker}</div> : null}
          <div className="stat-value">
            <Cited text={item.value} />
          </div>
          <p>
            <Cited text={item.label} />
          </p>
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
