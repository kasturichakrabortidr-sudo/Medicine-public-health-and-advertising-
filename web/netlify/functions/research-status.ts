import type { Config, Context } from "@netlify/functions";
import { getStore } from "@netlify/blobs";

export default async (req: Request, context: Context) => {
  const fromParams = context.params?.id;
  const fromPath = new URL(req.url).pathname.split("/").filter(Boolean).pop();
  const id = fromParams || (fromPath && fromPath !== "research-status" ? fromPath : "");
  if (!id) return Response.json({ status: "error", detail: "missing id" }, { status: 400 });
  try {
    const store = getStore({ name: "research-decks", consistency: "strong" });
    const data = await store.get(id, { type: "json" });
    if (!data) return Response.json({ status: "running" });
    return Response.json(data);
  } catch (err) {
    return Response.json({ status: "error", detail: (err as Error).message }, { status: 500 });
  }
};

export const config: Config = {
  path: "/api/research/:id",
  method: "GET",
};
