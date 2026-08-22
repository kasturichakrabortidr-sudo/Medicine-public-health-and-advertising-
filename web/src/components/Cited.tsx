export function Cited({ text }: { text: string }) {
  const parts = String(text || "").split(/(\[\d+(?:[–,-]\d+)*\])/g);
  return (
    <>
      {parts.map((part, i) =>
        /^\[\d/.test(part) ? (
          <sup key={i} className="cite">
            {part}
          </sup>
        ) : (
          <span key={i}>{part}</span>
        ),
      )}
    </>
  );
}
