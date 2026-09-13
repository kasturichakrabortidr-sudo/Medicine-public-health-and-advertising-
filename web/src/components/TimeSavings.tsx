import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export default function TimeSavings({
  manualHours,
  automatedHours,
  reduction,
  wallClockSeconds,
}: {
  manualHours: number;
  automatedHours: number;
  reduction: number;
  wallClockSeconds?: number;
}) {
  const data = [
    { name: "Hand search + slides", hours: manualHours },
    { name: "This workflow (oversight)", hours: automatedHours },
  ];
  const minutes =
    wallClockSeconds != null ? Math.max(1, Math.round(wallClockSeconds / 60)) : null;
  return (
    <>
      <div className="kpi-row">
        <div className="kpi">
          <strong>{reduction}%</strong>modelled calendar cut
        </div>
        <div className="kpi">
          <strong>{manualHours}h → {automatedHours}h</strong>analyst time
        </div>
        {minutes != null ? (
          <div className="kpi">
            <strong>{minutes} min</strong>machine wall-clock this run
          </div>
        ) : null}
      </div>
      <div className="chart-panel" style={{ height: 240, marginTop: "1rem" }}>
        <ResponsiveContainer>
          <BarChart data={data} layout="vertical" margin={{ left: 16, right: 16 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
            <XAxis type="number" stroke="#d7e4e1" />
            <YAxis type="category" dataKey="name" width={190} stroke="#d7e4e1" />
            <Tooltip />
            <Bar dataKey="hours" fill="#e8d5a3" name="Hours" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </>
  );
}
