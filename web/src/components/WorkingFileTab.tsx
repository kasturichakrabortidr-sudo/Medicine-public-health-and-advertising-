import type { StrategyPack, WorkPhase } from "../types";
import { Cited } from "./Cited";
import { PaperAnchor, paperHref } from "../links";

export function WorkingFileTab({ pack }: { pack: StrategyPack }) {
  const work = pack.workfile;
  const refs = pack.references || pack.evidence?.references || [];
  if (!work) {
    return (
      <div className="card">
        <h2>No working file yet</h2>
        <p>Read a brief first. We will not invent a strategy from an empty page.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="topbar">
        <div>
          <h1>Working file</h1>
          <p>
            Eleven steps, in order. The deck is this file presented — not a separate idea.
          </p>
        </div>
      </div>
      <section className="card" style={{ marginBottom: 16 }}>
        <h3>How this was built</h3>
        <p>
          <Cited text={work.howBuilt} />
        </p>
        <p className="small muted">
          {work.validatedCount} numbered papers · {work.gapCount} uncited brief lines · {work.refCount}{" "}
          references
        </p>
        {work.openQuestions.length > 0 && (
          <>
            <h3 style={{ marginTop: 18 }}>Still open</h3>
            <ul className="bullets">
              {work.openQuestions.map((q) => (
                <li key={q}>
                  <Cited text={q} />
                </li>
              ))}
            </ul>
          </>
        )}
      </section>
      {work.phases.map((phase) => (
        <PhaseCard key={phase.id} phase={phase} />
      ))}
      <section className="card" style={{ marginTop: 16 }}>
        <h3>References</h3>
        <p className="small muted">Vancouver. Numbers in the file and on the slides are these papers.</p>
        <ol className="ref-list">
          {refs.map((r) => (
            <li key={r.n} id={`ref-${r.n}`} value={r.n}>
              {paperHref(r) ? (
                <PaperAnchor href={paperHref(r)}>{r.citation}</PaperAnchor>
              ) : (
                r.citation
              )}
              {r.status === "retrieved" ? <span className="small muted"> — retrieved, not lead</span> : null}
            </li>
          ))}
        </ol>
        {refs.length === 0 && <p className="muted">No numbered paper matched this brief.</p>}
      </section>
    </div>
  );
}

function PhaseCard({ phase }: { phase: WorkPhase }) {
  const tables = [
    phase.assumptions,
    phase.pico,
    phase.forefront,
    phase.gaps,
    phase.concord,
    phase.discord,
    phase.silent,
    phase.concerns,
    phase.drivers,
    phase.fourway,
    phase.house,
    phase.objections,
    phase.stages,
    phase.grid,
    phase.kpis,
  ].filter((t) => t && t.headers && t.rows && t.rows.length);

  const lists = [
    phase.questions,
    phase.hypotheses,
    phase.known,
    phase.unknown,
    phase.inventory,
    phase.hierarchy,
    phase.assets,
    phase.roadmap,
    phase.ask,
  ].filter((x): x is string[] => Array.isArray(x) && x.length > 0);

  return (
    <section className="card work-phase" style={{ marginBottom: 14 }}>
      <div className="kicker">
        Phase {phase.id}
      </div>
      <h3>{phase.title}</h3>
      <p className="small muted">
        <Cited text={phase.howBuilt} />
      </p>
      {phase.restatedAsk ? (
        <p>
          <strong>Asked. </strong>
          <Cited text={phase.restatedAsk} />
        </p>
      ) : null}
      {phase.restatedNeed ? (
        <p>
          <strong>Needs. </strong>
          <Cited text={phase.restatedNeed} />
        </p>
      ) : null}
      {phase.current ? (
        <p>
          <strong>Today. </strong>
          <Cited text={phase.current} />
        </p>
      ) : null}
      {phase.required ? (
        <p>
          <strong>Change. </strong>
          <Cited text={phase.required} />
        </p>
      ) : null}
      {phase.theme ? (
        <p>
          <strong>Theme. </strong>
          <Cited text={phase.theme} />
        </p>
      ) : null}
      {phase.scienceLead ? (
        <p>
          <Cited text={phase.scienceLead} />
        </p>
      ) : null}
      {phase.leadStatement ? (
        <p>
          <Cited text={phase.leadStatement} />
        </p>
      ) : null}
      {phase.position ? (
        <p>
          <Cited text={phase.position} />
        </p>
      ) : null}
      {phase.lead ? (
        <p>
          <Cited text={phase.lead} />
        </p>
      ) : null}
      {phase.bet ? (
        <p>
          <strong>Bet. </strong>
          <Cited text={phase.bet} />
        </p>
      ) : null}
      {lists.map((items, i) => (
        <ul className="bullets" key={i}>
          {items.map((item) => (
            <li key={item}>
              <Cited text={item} />
            </li>
          ))}
        </ul>
      ))}
      {tables.map((table, i) => (
        <table className="table" key={i} style={{ marginTop: 12 }}>
          <thead>
            <tr>
              {table!.headers!.map((h) => (
                <th key={h}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {table!.rows!.map((row, ri) => (
              <tr key={ri}>
                {row.map((c, ci) => (
                  <td key={ci}>
                    <Cited text={c} />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      ))}
      {phase.warn ? <div className="alert mlr">{phase.warn}</div> : null}
      {phase.caveat ? <p className="small muted">{phase.caveat}</p> : null}
    </section>
  );
}
