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
  try {
    const data = await res.json();
    return data.detail || data.error || res.statusText;
  } catch {
    return res.statusText;
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
  const res = await fetch("/api/extract", { method: "POST", body });
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
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
  const res = await fetch("/api/generate", { method: "POST", body });
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}
