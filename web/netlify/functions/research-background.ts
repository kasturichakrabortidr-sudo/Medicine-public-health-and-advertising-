import type { Config } from "@netlify/functions";
import { getStore } from "@netlify/blobs";
import { runResearch } from "./_shared/pipeline";

export default async (req: Request) => {
  const body = await req.json().catch(() => ({}));
  const runId = String(body.runId || crypto.randomUUID());
  const brief = body.brief || {};
  const store = getStore({ name: "research-decks", consistency: "strong" });
  await store.setJSON(runId, { status: "running", started_at: new Date().toISOString() });
  try {
    const deck = await runResearch(brief);
    await store.setJSON(runId, { status: "ready", deck });
  } catch (err) {
    await store.setJSON(runId, {
      status: "error",
      detail: (err as Error).message,
    });
  }
};

export const config: Config = {
  path: "/api/research",
  method: "POST",
};
