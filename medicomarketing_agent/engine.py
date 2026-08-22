"""Pipeline engine: runs the strategy phases against the Claude API.

The whole pipeline is one growing conversation. Each phase appends its
instruction as a user turn and the model's output as an assistant turn, so
later phases can reference everything before them. Prompt caching is applied
to the conversation prefix so each successive phase re-reads the earlier
phases from cache instead of re-billing them at full price.
"""

import sys
from pathlib import Path

import anthropic

from .config import render_brief
from .phases import EXPAND_PROMPT, PHASES, SYSTEM_PROMPT, Phase, build_phase_prompt
from .report import write_strategy_html

DEFAULT_MODEL = "claude-opus-5"
MAX_TOKENS = 64000
WEB_SEARCH_TOOL = {"type": "web_search_20260209", "name": "web_search", "max_uses": 8}


class StrategyEngine:
    def __init__(
        self,
        brief: dict,
        out_dir: str | Path = "output",
        model: str = DEFAULT_MODEL,
        web_search: bool = False,
        quiet: bool = False,
    ):
        self.client = anthropic.Anthropic()
        self.brief = brief
        self.out_dir = Path(out_dir)
        self.model = model
        self.web_search = web_search
        self.quiet = quiet
        self.messages: list[dict] = []
        self.results: dict[str, str] = {}

    # ------------------------------------------------------------------ run

    def run_pipeline(self, phases: list[Phase] | None = None) -> Path:
        """Run all phases in order and write one file per phase plus a
        combined strategy document. Returns the path of the combined doc."""
        self.out_dir.mkdir(parents=True, exist_ok=True)
        phases = phases or PHASES

        self._log(f"Running {len(phases)} phases with model {self.model}\n")
        first = True
        for phase in phases:
            self._log(f"\n{'=' * 72}\n{phase.id}  {phase.title}\n{'=' * 72}\n")
            content = build_phase_prompt(phase)
            if first:
                content = render_brief(self.brief) + "\n\n---\n\n" + content
                first = False
            text = self._turn(content)
            self.results[phase.id] = text
            phase_path = self.out_dir / f"{phase.id}.md"
            phase_path.write_text(f"# {phase.title}\n\n{text}\n", encoding="utf-8")
            self._log(f"\n[saved {phase_path}]")

        combined = self.out_dir / "medicomarketing-strategy.md"
        parts = [f"# Medicomarketing Strategy: {self.brief.get('brand', '')}", ""]
        for phase in phases:
            parts += [f"\n\n---\n\n## {phase.title}", "", self.results[phase.id]]
        combined.write_text("\n".join(parts), encoding="utf-8")
        self._log(f"\n\nCombined strategy written to {combined}")
        visual_report = self.out_dir / "medicomarketing-strategy.html"
        write_strategy_html(
            combined,
            visual_report,
            f"Medicomarketing Strategy: {self.brief.get('brand', '')}",
        )
        self._log(f"\nVisual strategy report written to {visual_report}")
        return combined

    def expand_outline(self, points: list[str]) -> Path:
        """Develop full detail for each user-supplied outline point."""
        self.out_dir.mkdir(parents=True, exist_ok=True)
        sections: list[str] = []
        for i, point in enumerate(points, 1):
            self._log(f"\n{'=' * 72}\nOutline point {i}/{len(points)}: {point[:80]}\n{'=' * 72}\n")
            content = EXPAND_PROMPT.format(point=point)
            if i == 1:
                content = render_brief(self.brief) + "\n\n---\n\n" + content
            text = self._turn(content)
            sections.append(f"## {i}. {point}\n\n{text}")

        out = self.out_dir / "outline-expansion.md"
        out.write_text(
            f"# Developed Outline: {self.brief.get('brand', '')}\n\n" + "\n\n---\n\n".join(sections) + "\n",
            encoding="utf-8",
        )
        self._log(f"\n\nExpanded outline written to {out}")
        visual_report = self.out_dir / "outline-expansion.html"
        write_strategy_html(
            out,
            visual_report,
            f"Developed Outline: {self.brief.get('brand', '')}",
        )
        self._log(f"\nVisual outline report written to {visual_report}")
        return out

    # ----------------------------------------------------------------- turns

    def _turn(self, user_content: str) -> str:
        """Send one user turn, stream the reply, handle pause_turn, append
        both turns to the conversation, and return the reply text."""
        self.messages.append({"role": "user", "content": user_content})

        while True:
            response = self._stream_once()

            if response.stop_reason == "refusal":
                detail = ""
                if response.stop_details:
                    detail = f" ({response.stop_details.category}: {response.stop_details.explanation})"
                raise RuntimeError(f"The model declined this request{detail}.")

            # Server-side tools (web search) can pause mid-turn; append the
            # partial assistant turn and re-send so the server resumes.
            self.messages.append({"role": "assistant", "content": response.content})
            if response.stop_reason == "pause_turn":
                continue
            break

        return "".join(b.text for b in response.content if b.type == "text")

    def _stream_once(self):
        kwargs: dict = {
            "model": self.model,
            "max_tokens": MAX_TOKENS,
            "system": [
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            "messages": self._messages_with_cache(),
        }
        if self.web_search:
            kwargs["tools"] = [WEB_SEARCH_TOOL]

        with self.client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                if not self.quiet:
                    sys.stdout.write(text)
                    sys.stdout.flush()
            return stream.get_final_message()

    def _messages_with_cache(self) -> list[dict]:
        """Mark the last message with cache_control so the whole conversation
        prefix is cached for the next phase."""
        msgs = [dict(m) for m in self.messages]
        last = msgs[-1]
        content = last["content"]
        if isinstance(content, str):
            last["content"] = [
                {"type": "text", "text": content, "cache_control": {"type": "ephemeral"}}
            ]
        return msgs

    def _log(self, text: str) -> None:
        if not self.quiet:
            print(text)
