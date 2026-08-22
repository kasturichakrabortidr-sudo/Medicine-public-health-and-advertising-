import type { ExtractedBrief, FilePreview, StrategyPack } from "./types";

const ACCEPT =
  ".pdf,.ppt,.pptx,.doc,.docx,.xls,.xlsx,.csv,.tsv,.txt,.md,.rtf,.yaml,.yml,.json,.html,.htm,.xml,.odt,.odp,.ods,.png,.jpg,.jpeg,.webp,.gif,.log,.outline";

export const ACCEPT_LABELS = [
  "PDF",
  "PPT/PPTX",
  "DOC/DOCX",
  "XLS/XLSX",
  "CSV",
  "TXT/MD",
  "YAML/JSON",
  "RTF",
  "HTML",
  "ODT/ODP/ODS",
  "Images",
];

export { ACCEPT };

async function readError(res: Response): Promise<string> {
  const fallback =
    res.status === 404
      ? "The strategy engine is not running, so uploaded briefs cannot replace the demo. Start it with python start_director.py."
      : res.statusText;
  try {
    const data = await res.json();
    return data.detail || data.error || fallback;
  } catch {
    return fallback;
  }
}

export async function fetchDemo(): Promise<StrategyPack> {
  try {
    const res = await fetch("/api/demo");
    if (res.ok) return res.json();
  } catch {
    /* fall through to the static pack */
  }
  const fallback = await fetch("/demo.json");
  if (!fallback.ok) throw new Error("Could not load the demo strategy pack.");
  return fallback.json();
}

export async function extractBriefs(
  files: File[],
  pasted: string,
): Promise<{ files: FilePreview[]; brief: ExtractedBrief }> {
  const body = new FormData();
  files.forEach((f) => body.append("files", f));
  body.append("pasted", pasted);
  let res: Response;
  try {
    res = await fetch("/api/extract", { method: "POST", body });
  } catch {
    throw new Error(
      "Could not reach the strategy engine. Start it with python start_director.py so uploaded briefs can be read.",
    );
  }
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}

export async function downloadPptx(pack: StrategyPack): Promise<void> {
  const res = await fetch("/api/export/pptx", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(pack),
  });
  if (!res.ok) throw new Error(await readError(res));
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

export async function generatePack(args: {
  files?: File[];
  pasted?: string;
  brief?: ExtractedBrief;
}): Promise<StrategyPack> {
  const body = new FormData();
  (args.files || []).forEach((f) => body.append("files", f));
  body.append("pasted", args.pasted || "");
  if (args.brief) body.append("brief_json", JSON.stringify(args.brief));
  let res: Response;
  try {
    res = await fetch("/api/generate", { method: "POST", body });
  } catch {
    throw new Error(
      "Could not reach the strategy engine. Uploaded briefs cannot be turned into a strategy until python start_director.py is running.",
    );
  }
  if (!res.ok) throw new Error(await readError(res));
  const pack = (await res.json()) as StrategyPack;
  if (pack?.meta?.brand === "CardioShield" && args.brief?.brand && args.brief.brand !== "CardioShield") {
    throw new Error("The engine returned the CardioShield demo instead of your brief. Try Write the working file again.");
  }
  return pack;
}
