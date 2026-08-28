import type { ClaimFreq, EvidenceRecord } from "../types";
import { familyLabel } from "./Cite";

export default function ClaimMatrix({
  claims,
  records,
}: {
  claims: ClaimFreq[];
  records: EvidenceRecord[];
}) {
  const families = [...new Set(records.map((r) => r.source_family))];
  const top = claims.slice(0, 6);
  return (
    <table className="table heatmap">
      <thead>
        <tr>
          <th>Claim × source</th>
          {families.map((f) => (
            <th key={f}>{familyLabel(f)}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {top.map((c) => {
          const ids = new Set(c.citation_ids);
          return (
            <tr key={c.id}>
              <td>{c.label}</td>
              {families.map((f) => {
                const n = records.filter((r) => ids.has(r.citation_id) && r.source_family === f).length;
                const intensity = Math.min(1, n / 6);
                return (
                  <td
                    key={f}
                    style={{
                      background: `rgba(201, 162, 39, ${0.12 + intensity * 0.7})`,
                      color: "#f4efe4",
                      textAlign: "center",
                      fontWeight: 700,
                    }}
                  >
                    {n || "·"}
                  </td>
                );
              })}
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
