import type { ExtractedBrief, FilePreview, ProjectRecord, ProjectStatus, ProjectSummary, StrategyPack } from "./types";

export const ACCEPT =
  ".pdf,.ppt,.pptx,.doc,.docx,.xls,.xlsx,.csv,.tsv,.txt,.md,.rtf,.yaml,.yml,.json,.html,.htm,.xml,.odt,.odp,.ods,.png,.jpg,.jpeg,.webp,.gif,.log,.outline";

async function fail(res: Response): Promise<string> {
  try {
    const data = await res.json();
    return data.detail || data.error || res.statusText;
  } catch {
    return res.statusText;
  }
}

export async function extractBriefs(files: File[], pasted: string): Promise<{ files: FilePreview[]; brief: ExtractedBrief }> {
  const body = new FormData();
  files.forEach((f) => body.append("files", f));
  body.append("pasted", pasted);
  const res = await fetch("/api/extract", { method: "POST", body });
  if (!res.ok) throw new Error(await fail(res));
  return res.json();
}

export async function generatePack(files: File[], pasted: string): Promise<StrategyPack> {
  const body = new FormData();
  files.forEach((f) => body.append("files", f));
  body.append("pasted", pasted);
  body.append("mode", "director");
  const res = await fetch("/api/generate", { method: "POST", body });
  if (!res.ok) throw new Error(await fail(res));
  return res.json();
}

export async function downloadPptx(pack: StrategyPack): Promise<void> {
  const res = await fetch("/api/export/pptx", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(pack),
  });
  if (!res.ok) throw new Error(await fail(res));
  const blob = await res.blob();
  const match = /filename="?([^"]+)"?/i.exec(res.headers.get("content-disposition") || "");
  const name = match?.[1] || `${pack.meta.brand || "strategy"}-strategy-deck.pptx`;
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export async function listProjects(): Promise<ProjectSummary[]> {
  const res = await fetch("/api/projects");
  if (!res.ok) throw new Error(await fail(res));
  const data = await res.json();
  return data.projects || [];
}

export async function loadProject(id: string): Promise<ProjectRecord> {
  const res = await fetch(`/api/projects/${encodeURIComponent(id)}`);
  if (!res.ok) throw new Error(await fail(res));
  return res.json();
}

export async function saveProject(pack: StrategyPack, status: ProjectStatus, id?: string): Promise<ProjectRecord> {
  const res = await fetch("/api/projects", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pack, status, id }),
  });
  if (!res.ok) throw new Error(await fail(res));
  return res.json();
}

export async function deleteProject(id: string): Promise<void> {
  const res = await fetch(`/api/projects/${encodeURIComponent(id)}`, { method: "DELETE" });
  if (!res.ok) throw new Error(await fail(res));
}
