import type { StrategyPack } from "../types";

export function WorkfileScreen({ pack }: { pack: StrategyPack }) {
  const work = pack.workfile;
  if (!work) return <p className="muted">No working file on this pack.</p>;
  return (
    <section className="panel workfile">
      <h1>Working file</h1>
      <p className="lede">{work.howBuilt}</p>
      {work.cannotClaim?.length ? (
        <div className="warn">
          <strong>Do not claim</strong>
          <ul>
            {work.cannotClaim.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        </div>
      ) : null}
      {work.phases.map((phase) => (
        <article key={phase.id} className="phase">
          <h2>
            {phase.id} · {phase.title}
          </h2>
          <p className="muted">{phase.howBuilt}</p>
          {phase.restatedNeed ? <p>{phase.restatedNeed}</p> : null}
          {phase.bet ? <p>{phase.bet}</p> : null}
          {phase.enemy ? <p>{phase.enemy}</p> : null}
          {phase.theme ? <p>{phase.theme}</p> : null}
          {phase.leadStatement ? <p>{phase.leadStatement}</p> : null}
          {(phase.known || []).length ? (
            <ul>
              {phase.known!.map((k) => (
                <li key={k}>{k}</li>
              ))}
            </ul>
          ) : null}
        </article>
      ))}
    </section>
  );
}
