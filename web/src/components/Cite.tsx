import type { DeckPayload } from "../types";

export function Cite({ n }: { n?: number | number[] | null }) {
  if (n == null) return null;
  const ids = Array.isArray(n) ? n : [n];
  return (
    <>
      {ids.slice(0, 6).map((id) => (
        <a key={id} className="cite" href={`#ref-${id}`} title={`Reference ${id}`}>
          {id}
        </a>
      ))}
    </>
  );
}

export function familyLabel(id: string) {
  return id.replaceAll("_", " ");
}

export function briefBits(deck: DeckPayload) {
  const b = deck.brief;
  return {
    brand: String(b.brand || "Brand"),
    therapy: String(b.therapy_area || ""),
    indication: String(b.indication || ""),
    product: String(b.product || ""),
    market: String(b.market || ""),
  };
}
