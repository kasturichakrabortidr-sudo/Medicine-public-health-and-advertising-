import type { DeckPayload } from "../types";

export default function PrismaFlow({ prisma }: { prisma: DeckPayload["prisma"] }) {
  const rows = [
    ["Identified from live APIs", prisma.identified],
    [`Duplicates removed (${prisma.duplicates_removed})`, prisma.screened],
    [`Off-topic excluded (${prisma.excluded_off_topic})`, prisma.screened - prisma.excluded_off_topic],
    [`Unresolved identifiers excluded (${prisma.excluded_unvalidated})`, prisma.included],
    ["Included, registry-validated corpus", prisma.included],
  ];
  return (
    <div className="prisma">
      {rows.map(([label, n], i) => (
        <div key={i}>
          {i > 0 ? <div className="arrow">↓</div> : null}
          <div className="box">
            <strong>{n}</strong>
            <div>{label}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
