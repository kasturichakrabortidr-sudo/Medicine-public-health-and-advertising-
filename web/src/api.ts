import type { AgentEvent, ExtractedBrief, FilePreview, ProjectRecord, ProjectStatus, ProjectSummary, StrategyPack } from "./types";

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

function directorForm(files: File[], pasted: string): FormData {
  const body = new FormData();
  files.forEach((f) => body.append("files", f));
  body.append("pasted", pasted);
  body.append("mode", "director");
  return body;
}

export async function fetchHealth(): Promise<{ ok: boolean; agent?: boolean; llm?: boolean; model?: string }> {
  const res = await fetch("/api/health");
  if (!res.ok) throw new Error(await fail(res));
  return res.json();
}

export async function extractBriefs(files: File[], pasted: string): Promise<{ files: FilePreview[]; brief: ExtractedBrief }> {
  const body = new FormData();
  files.forEach((f) => body.append("files", f));
  body.append("pasted", pasted);
  const res = await fetch("/api/extract", { method: "POST", body });
  if (!res.ok) throw new Error(await fail(res));
  return res.json();
}

export async function generatePack(
  files: File[],
  pasted: string,
  onEvent?: (event: AgentEvent) => void,
): Promise<StrategyPack> {
  const streamed = await fetch("/api/generate/stream", {
    method: "POST",
    body: directorForm(files, pasted),
    headers: { Accept: "text/event-stream" },
  });
  if (streamed.ok && streamed.body) {
    return readDirectorStream(streamed, onEvent);
  }
  if (streamed.status !== 404 && streamed.status !== 405) {
    throw new Error(await fail(streamed));
  }
  const res = await fetch("/api/generate", { method: "POST", body: directorForm(files, pasted) });
  if (!res.ok) throw new Error(await fail(res));
  const pack: StrategyPack = await res.json();
  for (const event of pack.agent?.log || []) onEvent?.(event);
  return pack;
}

async function readDirectorStream(
  res: Response,
  onEvent?: (event: AgentEvent) => void,
): Promise<StrategyPack> {
  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let pack: StrategyPack | null = null;
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split("\n\n");
    buffer = chunks.pop() || "";
    for (const chunk of chunks) {
      const line = chunk
        .split("\n")
        .map((row) => row.trimEnd())
        .find((row) => row.startsWith("data:"));
      if (!line) continue;
      const event = JSON.parse(line.slice(5).trim());
      if (event.type === "pack") pack = event.pack;
      else if (event.type === "error") throw new Error(event.text || "Director failed.");
      else onEvent?.(event);
    }
  }
  if (buffer.trim()) {
    const line = buffer
      .split("\n")
      .map((row) => row.trimEnd())
      .find((row) => row.startsWith("data:"));
    if (line) {
      const event = JSON.parse(line.slice(5).trim());
      if (event.type === "pack") pack = event.pack;
      else if (event.type === "error") throw new Error(event.text || "Director failed.");
      else onEvent?.(event);
    }
  }
  if (!pack) throw new Error("Director finished without a pack.");
  return pack;
}

async function downloadBlob(res: Response, fallback: string): Promise<void> {
  const blob = await res.blob();
  const match = /filename="?([^"]+)"?/i.exec(res.headers.get("content-disposition") || "");
  const name = match?.[1] || fallback;
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export async function downloadPptx(pack: StrategyPack): Promise<void> {
  const res = await fetch("/api/export/pptx", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(pack),
  });
  if (!res.ok) throw new Error(await fail(res));
  await downloadBlob(res, `${pack.meta.brand || "strategy"}-strategy-deck.pptx`);
}

export async function downloadWorkfile(pack: StrategyPack): Promise<void> {
  const res = await fetch("/api/export/workfile", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(pack),
  });
  if (!res.ok) throw new Error(await fail(res));
  await downloadBlob(res, `${pack.meta.brand || "strategy"}-working-file.md`);
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