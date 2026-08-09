"""Command-line interface for the medicomarketing strategy agent.

Usage:
    python -m medicomarketing_agent run --brief examples/brief.example.yaml
    python -m medicomarketing_agent run --brief brief.yaml --phases 01,03,07
    python -m medicomarketing_agent expand --brief brief.yaml --outline outline.md
    python -m medicomarketing_agent phases        # list all pipeline phases
"""

import argparse
import os
import sys
from pathlib import Path

from .config import load_brief
from .engine import DEFAULT_MODEL, StrategyEngine
from .phases import PHASES


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="medicomarketing_agent",
        description="AI agent that builds evidence-led medicomarketing strategies for HCP audiences.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Run the full strategy pipeline from a client brief.")
    _common_args(run)
    run.add_argument(
        "--phases",
        help="Comma-separated phase id prefixes to run (e.g. '01,02,03'). Default: all.",
    )

    expand = sub.add_parser("expand", help="Develop full detail for each point of your outline.")
    _common_args(expand)
    expand.add_argument(
        "--outline",
        required=True,
        help="Markdown/text file with one outline point per line or bullet.",
    )

    sub.add_parser("phases", help="List the pipeline phases and exit.")
    return parser


def _common_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--brief", required=True, help="Path to the client brief (YAML or JSON).")
    p.add_argument("--out", default="output", help="Output directory (default: output/).")
    p.add_argument("--model", default=DEFAULT_MODEL, help=f"Model ID (default: {DEFAULT_MODEL}).")
    p.add_argument(
        "--web-search",
        action="store_true",
        help="Let the model search the web for current evidence and guidelines.",
    )
    p.add_argument("--quiet", action="store_true", help="Suppress streaming output.")


def parse_outline(path: str) -> list[str]:
    """Extract outline points from a Markdown/text file.

    If the file contains bulleted or numbered lines, those are the points
    (headings and prose are ignored). Otherwise every non-empty, non-heading
    line is treated as a point."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()

    def strip_marker(line: str) -> str | None:
        s = line.strip()
        if s.startswith(("-", "*", "+")):
            return s.lstrip("-*+").strip()
        head = s.split(".", 1)[0].split(")", 1)[0]
        if head.isdigit() and len(head) < len(s):
            return s[len(head) + 1 :].strip()
        return None

    points = [p for p in (strip_marker(l) for l in lines) if p]
    if not points:
        points = [l.strip() for l in lines if l.strip() and not l.strip().startswith("#")]
    if not points:
        raise ValueError(f"No outline points found in {path}")
    return points


def select_phases(spec: str | None):
    if not spec:
        return None
    prefixes = [s.strip() for s in spec.split(",") if s.strip()]
    selected = [p for p in PHASES if any(p.id.startswith(pre) for pre in prefixes)]
    if not selected:
        raise ValueError(f"No phases match: {spec}")
    return selected


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "phases":
        for p in PHASES:
            print(f"{p.id}  {p.title}")
        return 0

    if not os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get("ANTHROPIC_AUTH_TOKEN"):
        print(
            "Note: ANTHROPIC_API_KEY is not set. The SDK will fall back to an "
            "`ant auth login` profile if one exists.",
            file=sys.stderr,
        )

    brief = load_brief(args.brief)
    engine = StrategyEngine(
        brief,
        out_dir=args.out,
        model=args.model,
        web_search=args.web_search,
        quiet=args.quiet,
    )

    if args.command == "run":
        engine.run_pipeline(select_phases(args.phases))
    elif args.command == "expand":
        engine.expand_outline(parse_outline(args.outline))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
