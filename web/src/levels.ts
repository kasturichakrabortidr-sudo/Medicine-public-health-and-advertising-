import type { TabId } from "./types";

export const LEVELS: { id: TabId; n: string; label: string; needsPack: boolean }[] = [
  { id: "briefs", n: "01", label: "Brief", needsPack: false },
  { id: "work", n: "02", label: "Working file", needsPack: true },
  { id: "evidence", n: "03", label: "Papers", needsPack: true },
  { id: "deck", n: "04", label: "Deck", needsPack: true },
  { id: "take", n: "05", label: "Take", needsPack: true },
];
