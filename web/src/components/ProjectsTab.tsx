import { useEffect, useState } from "react";
import { deleteProject, listProjects, loadProject, saveProject } from "../api";
import type { ProjectStatus, ProjectSummary, StrategyPack } from "../types";

export function ProjectsTab({
  pack,
  onOpen,
  onError,
}: {
  pack: StrategyPack | null;
  onOpen: (next: StrategyPack) => void;
  onError: (message: string) => void;
}) {
  const [rows, setRows] = useState<ProjectSummary[]>([]);
  const [busy, setBusy] = useState(false);

  const refresh = async () => {
    try {
      setRows(await listProjects());
    } catch (err) {
      onError(err instanceof Error ? err.message : String(err));
    }
  };

  useEffect(() => {
    void refresh();
  }, []);

  const run = async (fn: () => Promise<void>) => {
    setBusy(true);
    onError("");
    try {
      await fn();
      await refresh();
    } catch (err) {
      onError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  const ongoing = rows.filter((r) => r.status === "ongoing");
  const saved = rows.filter((r) => r.status === "saved");

  return (
    <div>
      <div className="topbar">
        <div>
          <h1>Projects</h1>
          <p>Ongoing working files stay here. Save one to pin it past the next brief.</p>
        </div>
        {pack ? (
          <div className="actions">
            <button
              className="btn copper"
              type="button"
              disabled={busy}
              onClick={() =>
                run(async () => {
                  await saveProject(pack, "saved");
                })
              }
            >
              Save this pack
            </button>
          </div>
        ) : null}
      </div>
      <Section
        title="Ongoing"
        empty="Nothing in flight. Write a working file from Brief and it will land here."
        rows={ongoing}
        busy={busy}
        onOpen={(id) =>
          run(async () => {
            const record = await loadProject(id);
            onOpen(record.pack);
          })
        }
        onSave={(id) =>
          run(async () => {
            const record = await loadProject(id);
            await saveProject(record.pack, "saved", id);
          })
        }
        onDelete={(id) =>
          run(async () => {
            await deleteProject(id);
          })
        }
      />
      <Section
        title="Saved"
        empty="Pin a pack with Save this pack. Saved projects survive the next brief."
        rows={saved}
        busy={busy}
        onOpen={(id) =>
          run(async () => {
            const record = await loadProject(id);
            onOpen(record.pack);
          })
        }
        onDelete={(id) =>
          run(async () => {
            await deleteProject(id);
          })
        }
      />
    </div>
  );
}

function Section({
  title,
  empty,
  rows,
  busy,
  onOpen,
  onSave,
  onDelete,
}: {
  title: string;
  empty: string;
  rows: ProjectSummary[];
  busy: boolean;
  onOpen: (id: string) => void;
  onSave?: (id: string) => void;
  onDelete: (id: string) => void;
}) {
  return (
    <section className="card" style={{ marginBottom: 16 }}>
      <h3>{title}</h3>
      {rows.length === 0 ? <p className="muted">{empty}</p> : null}
      <div className="project-list">
        {rows.map((row) => (
          <article className="project-card" key={row.id}>
            <div>
              <div className="kicker">{statusLabel(row.status)}</div>
              <h3>{row.title}</h3>
              <p>
                {row.molecule ? `${row.molecule} · ` : ""}
                {row.therapyArea || "Therapy area pending"} · {row.market || "Market pending"}
              </p>
              <p className="small muted">
                {row.doctrine || "No doctrine yet"} · {row.papers} papers · {row.slides} slides
                {row.source ? ` · ${row.source}` : ""}
              </p>
              <p className="small muted">Updated {row.updatedAt?.replace("T", " ").replace("Z", " UTC")}</p>
            </div>
            <div className="actions">
              <button className="btn copper" type="button" disabled={busy} onClick={() => onOpen(row.id)}>
                Open
              </button>
              {onSave ? (
                <button className="btn" type="button" disabled={busy} onClick={() => onSave(row.id)}>
                  Save
                </button>
              ) : null}
              <button className="btn ghost" type="button" disabled={busy} onClick={() => onDelete(row.id)}>
                Delete
              </button>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function statusLabel(status: ProjectStatus): string {
  return status === "saved" ? "Saved" : "Ongoing";
}
