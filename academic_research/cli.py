"""CLI for the academic research automation.

Usage:
    python -m academic_research run --brief examples/brief.example.yaml --out output/research
    python -m academic_research demo --out web/public/demo
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from medicomarketing_agent.config import load_brief

from .pipeline import ResearchPipeline, write_deck


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="academic_research",
        description=(
            "Multi-source literature search with registry validation, "
            "frequency analysis, IPA/narrative synthesis, and a visual deck."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="Run the pipeline from a YAML/JSON brief.")
    run.add_argument("--brief", required=True, help="Path to client brief.")
    run.add_argument("--out", default="output/research", help="Output directory.")
    run.add_argument(
        "--max-per-query",
        type=int,
        default=8,
        help="Max hits per connector/query (default 8).",
    )
    demo = sub.add_parser("demo", help="Run the example CardioShield brief into the web demo folder.")
    demo.add_argument("--out", default="web/public/demo", help="Demo JSON directory.")
    demo.add_argument("--brief", default="examples/brief.example.yaml")
    demo.add_argument("--max-per-query", type=int, default=8)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    brief = load_brief(args.brief)
    pipe = ResearchPipeline(brief, max_per_query=args.max_per_query)
    payload = pipe.run()
    path = write_deck(payload, args.out, git_safe=args.command == "demo")
    print(f"Included {payload['prisma']['included']} validated records")
    print(f"Wrote {path}")
    if args.command == "demo":
        dest_dir = Path("web/public/demo")
        dest_dir.mkdir(parents=True, exist_ok=True)
        src_dir = Path(args.out)
        for name in (
            "literature-deck.json",
            "references.md",
            "references.bib",
            "references.ris",
            "references.csv",
            "claim-frequency.csv",
            "evidence-campaign-deck.pptx",
        ):
            src = src_dir / name
            dest = dest_dir / name
            if src.exists() and src.resolve() != dest.resolve():
                shutil.copyfile(src, dest)
                print(f"Copied {name} to {dest}")
    summary = {
        "prisma": payload["prisma"],
        "top_claims": payload["quantitative"]["claim_frequency"][:6],
        "n_references": len(payload["references"]),
        "n_forest": len(payload["forest"]),
        "n_ipa_themes": len(
            payload["qualitative"]["ipa"]["superordinate_themes"]
        ),
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
