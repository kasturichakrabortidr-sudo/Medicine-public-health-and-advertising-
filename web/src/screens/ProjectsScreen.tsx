import { useEffect } from "react";
import { listProjects } from "../api";
import type { ProjectSummary } from "../types";

export function ProjectsScreen({
  rows,
  setRows,
  busy,
  onOpen,
  onDelete,
}: {
  rows: ProjectSummary[] | null;
  setRows: (rows: ProjectSummary[]) => void;
  busy: boolean;
  onOpen: (id: string) => void;
  onDelete: (id: string) => void;
}) {
  useEffect(() => {
    if (rows) return;
    void listProjects().then(setRows);
  }, [rows, setRows]);

  return (
    <section className="panel projects">
      <p className="eyebrow">Saved packs</p>
      <h1>Projects</h1>
      <p className="lede">Each pack keeps all five levels. Nothing opens until you click it.</p>
      {!rows ? <p className="muted">Loading…</p> : null}
      {rows && rows.length === 0 ? <p className="muted">No packs yet. Build a strategy from 01 Brief.</p> : null}
      <ul className="project-list">
        {(rows || []).map((row) => (
          <li key={row.id}>
            <div>
              <p className="kicker">{row.status}</p>
              <strong>{row.title}</strong>
              <span>
                {row.therapyArea} · {row.slides} slides · {row.papers} papers
              </span>
            </div>
            <div className="row-actions">
              <button type="button" disabled={busy} onClick={() => onOpen(row.id)}>
                Open all levels
              </button>
              <button type="button" className="ghost" disabled={busy} onClick={() => onDelete(row.id)}>
                Delete
              </button>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
