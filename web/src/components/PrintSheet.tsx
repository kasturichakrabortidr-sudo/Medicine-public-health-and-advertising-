import type { StrategyPack } from "../types";
import { SlideCanvas } from "./SlideCanvas";

export function PrintSheet({ pack }: { pack: StrategyPack }) {
  return (
    <div className="print-deck" aria-hidden="true">
      {pack.slides.map((s) => (
        <div className="print-page" key={s.id}>
          <SlideCanvas slide={s} />
        </div>
      ))}
    </div>
  );
}
