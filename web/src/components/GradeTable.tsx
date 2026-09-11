import { Cite } from "./Cite";

export interface GradeRow {
  id: string;
  label: string;
  band: string;
  note: string;
  count: number;
  citation_ids: number[];
}

export default function GradeTable({ rows }: { rows: GradeRow[] }) {
  if (!rows.length) {
    return <p>No design markers were coded in this corpus.</p>;
  }
  return (
    <table className="table">
      <thead>
        <tr>
          <th>Design</th>
          <th>Certainty band</th>
          <th>n</th>
          <th>Citations</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row.id}>
            <td>
              <strong>{row.label}</strong>
              <div className="muted-note">{row.note}</div>
            </td>
            <td>{row.band}</td>
            <td>{row.count}</td>
            <td>
              <Cite n={row.citation_ids} />
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
