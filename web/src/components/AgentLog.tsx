import { useEffect, useRef } from "react";
import type { AgentEvent } from "../types";

export function AgentLog({ events }: { events: AgentEvent[] }) {
  const root = useRef<HTMLOListElement>(null);
  useEffect(() => {
    const el = root.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
    el.scrollIntoView({ block: "nearest" });
  }, [events.length]);
  if (!events.length) return null;
  return (
    <ol className="agent-log" ref={root} aria-live="polite">
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
