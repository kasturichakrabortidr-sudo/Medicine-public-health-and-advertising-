import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import SlideDeck from "../components/SlideDeck";
import type { DeckPayload } from "../types";

export default function DeckPage() {
  const { runId } = useParams();
  const [deck, setDeck] = useState<DeckPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const url = runId ? `/api/research/${runId}` : "/demo/literature-deck.json";
    fetch(url)
      .then(async (res) => {
        if (!res.ok) throw new Error(`Could not load deck (${res.status})`);
        return res.json();
      })
      .then((data) => {
        if (data.status && data.status !== "ready") {
          throw new Error(data.detail || data.status);
        }
        setDeck(data.deck ?? data);
      })
      .catch((err: Error) => setError(err.message));
  }, [runId]);

  if (error) {
    return (
      <div className="methods">
        <h1>Deck unavailable</h1>
        <p>{error}</p>
        <p>
          If you are looking at the demo, generate it with{" "}
          <code>python -m academic_research demo</code>.
        </p>
      </div>
    );
  }
  if (!deck) {
    return (
      <div className="methods">
        <h1>Loading validated corpus…</h1>
      </div>
    );
  }
  return <SlideDeck deck={deck} />;
}
