import { PaperAnchor, paperHref, useRefLinks } from "../links";

export function Cited({ text }: { text: string }) {
  const refs = useRefLinks();
  const byN = new Map(refs.map((r) => [r.n, r]));
  const parts = String(text || "").split(/(\[\d+(?:[–,-]\d+)*\])/g);
  return (
    <>
      {parts.map((part, i) => {
        if (!/^\[\d/.test(part)) {
          return <span key={i}>{part}</span>;
        }
        const nums = Array.from(part.matchAll(/\d+/g), (m) => Number(m[0]));
        const href = paperHref(byN.get(nums[0]));
        return (
          <sup key={i} className="cite">
            <PaperAnchor href={href} className="cite-link">
              {part}
            </PaperAnchor>
          </sup>
        );
      })}
    </>
  );
}
