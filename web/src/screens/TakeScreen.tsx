import { AgentLog } from "../components/AgentLog";
import { printAs } from "../print";
import type { StrategyPack } from "../types";

export function TakeScreen({
  pack,
  busy,
  onPptx,
  onWorkfile,
  onPrintWork,
}: {
  pack: StrategyPack;
  busy: boolean;
  onPptx: () => void;
  onWorkfile: () => void;
  onPrintWork: () => void;
}) {
  const close = pack.slides.find((s) => s.id === "close");
  const levels = pack.levels;
  return (
    <section className="take">
      <header className="doc-bar no-print">
        <div>
          <p className="eyebrow">05 · Take</p>
          <h1>{pack.meta.brand}</h1>
          <p className="muted">The page you take into the room. Draft for MLR.</p>
        </div>
      </header>

      <article className="work-cover">
        <p className="kicker">Sign-off</p>
        <h2>{pack.doctrine.name}</h2>
        <p className="lede">{pack.doctrine.bet}</p>
        <p>
          <strong>The enemy.</strong> {pack.doctrine.enemy}
        </p>
        {close?.callout?.text ? (
          <p className="callout-line">{close.callout.text}</p>
        ) : null}
      </article>

      <div className="level-grid">
        <button type="button" className="level-card" disabled={busy} onClick={onPptx}>
          <span>04 → PPTX</span>
          <strong>{busy ? "Building PPTX…" : "Download PowerPoint"}</strong>
          <p>Native Office charts, same orange / blue / cream as the website.</p>
        </button>
        <button type="button" className="level-card" onClick={() => printAs("deck")}>
          <span>04 → PDF</span>
          <strong>Print the deck</strong>
          <p>Full 16:9 sheet. Use the browser print dialog to save PDF.</p>
        </button>
        <button type="button" className="level-card" disabled={busy} onClick={onWorkfile}>
          <span>02 → Markdown</span>
          <strong>{busy ? "Building markdown…" : "Download working file"}</strong>
          <p>Eleven phases, do-not-claim lines, and the numbered register.</p>
        </button>
        <button type="button" className="level-card" onClick={onPrintWork}>
          <span>02 → PDF</span>
          <strong>Print the working file</strong>
          <p>Opens level 02, then the A4 print sheet.</p>
        </button>
      </div>

      {levels ? (
        <ol className="level-strip">
          <li>
            <span>01</span> Brief · {levels.brief.title}
          </li>
          <li>
            <span>02</span> Working file · {levels.workfile.phases} phases
          </li>
          <li>
            <span>03</span> Papers · {levels.papers.count} numbered
          </li>
          <li>
            <span>04</span> Deck · {levels.deck.slides} slides
          </li>
          <li>
            <span>05</span> Take · PPTX, print, markdown
          </li>
        </ol>
      ) : null}

      {pack.agent?.log?.length ? (
        <div className="director-trace">
          <p className="eyebrow">Director log</p>
          <p className="muted">
            {pack.agent.llm ? `Model pass on ${pack.agent.model}` : "Workflow agent — think, then execute, at every level."}
          </p>
          <AgentLog events={pack.agent.log} />
        </div>
      ) : null}

      {pack.workfile?.cannotClaim?.length ? (
        <div className="warn">
          <strong>Do not claim</strong>
          <ul>
            {pack.workfile.cannotClaim.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}
