import type { AgentEvent } from "../types";

export function AgentLog({ events }: { events: AgentEvent[] }) {
  if (!events.length) return null;
  return (
    <ol className="agent-log" aria-live="polite">
      {events.map((event, index) => (
        <li key={`${event.step || "x"}-${event.type}-${index}`} className={event.type}>
          <span className="tag">{event.type === "think" ? "THINK" : "EXECUTE"}</span>
          <strong>{event.title}</strong>
          <p>{event.text}</p>
        </li>
      ))}
    </ol>
  );
}
