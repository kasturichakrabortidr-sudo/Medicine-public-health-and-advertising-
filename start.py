"""Friendly launcher for the medicomarketing strategy agent.

Run with:  python start.py   (or double-click Start-Windows.bat / Start-Mac.command)

It installs its own dependencies, asks for your API key once (saved locally),
interviews you in plain English to build the client brief, and runs the agent.
No command-line knowledge needed.
"""

import os
import subprocess
import sys
import webbrowser
from pathlib import Path

HERE = Path(__file__).resolve().parent
KEY_FILE = HERE / "api_key.txt"
BRIEF_FILE = HERE / "my-brief.yaml"
OUT_DIR = HERE / "output"


def say(text=""):
    print(text)


def ask(question, required=False):
    while True:
        answer = input(f"{question}\n> ").strip()
        if answer or not required:
            return answer
        say("  (this one is required — please type an answer)")


def ask_lines(question):
    """Collect multiple lines; empty line finishes."""
    say(f"{question}")
    say("  (type one item per line; press Enter on an empty line when done, or just Enter to skip)")
    lines = []
    while True:
        line = input("> ").strip()
        if not line:
            return lines
        lines.append(line)


# ------------------------------------------------------------ dependencies

def ensure_dependencies():
    try:
        import anthropic  # noqa: F401
        import mistune  # noqa: F401
        import yaml  # noqa: F401
        return
    except ImportError:
        pass
    say("First-time setup: installing the two required packages (takes a minute)...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(HERE / "requirements.txt")],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        say("\nAutomatic install failed. Please run this once, then start again:")
        say(f"  {sys.executable} -m pip install -r requirements.txt")
        say("\nError details:\n" + result.stderr[-2000:])
        sys.exit(1)
    say("Done.\n")


# ------------------------------------------------------------------ API key

def ensure_api_key():
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not key and KEY_FILE.exists():
        key = KEY_FILE.read_text(encoding="utf-8").strip()
    while not key.startswith("sk-ant-"):
        say("─" * 60)
        say("You need an Anthropic API key (a password that lets this tool")
        say("use the Claude AI — it's pay-as-you-go, like a prepaid SIM).")
        say("")
        say("How to get one (about 3 minutes):")
        say("  1. Sign in at  https://platform.claude.com")
        say("  2. Add a payment method under Billing")
        say("  3. Go to 'API Keys' -> 'Create Key' -> copy it")
        say("─" * 60)
        if ask("Open that website in your browser now? (y/n)").lower().startswith("y"):
            webbrowser.open("https://platform.claude.com")
        key = ask("Paste your API key here (it starts with sk-ant-)", required=True)
        if not key.startswith("sk-ant-"):
            say("  Hmm, that doesn't look like an API key. It should start with sk-ant-")
    KEY_FILE.write_text(key + "\n", encoding="utf-8")
    os.environ["ANTHROPIC_API_KEY"] = key
    say("API key saved (in api_key.txt, on this computer only). You won't be asked again.\n")


# -------------------------------------------------------------------- brief

def build_brief():
    import yaml

    if BRIEF_FILE.exists():
        say(f"Found your saved answers from last time ({BRIEF_FILE.name}).")
        if ask("Use them again? (y = reuse, n = start fresh)").lower().startswith("y"):
            return yaml.safe_load(BRIEF_FILE.read_text(encoding="utf-8"))

    say("─" * 60)
    say("I'll ask a few questions about your brand. Only the first two are")
    say("required — press Enter to skip any other question. Whatever you skip,")
    say("the agent will mark as a research task instead of making things up.")
    say("─" * 60 + "\n")

    brief = {}
    brief["brand"] = ask("1/9  Brand name?", required=True)
    brief["therapy_area"] = ask("2/9  Therapy area? (e.g. 'Cardiology - heart failure')", required=True)
    brief["product"] = ask("3/9  Product / molecule / service? (Enter to skip)")
    brief["indication"] = ask("4/9  Indication / patient group? (Enter to skip)")
    brief["market"] = ask("5/9  Market / country / cities? (Enter to skip)")
    brief["business_goal"] = ask("6/9  Business goal? (e.g. 'grow prescriptions 15% per quarter')")
    brief["target_specialties"] = ask_lines("7/9  Which doctor specialties are you targeting?")
    brief["brand_evidence"] = ask_lines("8/9  Key evidence you have (trials, real-world data, guidelines)?")
    brief["hcp_insights"] = ask_lines("9/9  What have your in-house doctors/advisors told you?")

    brief = {k: v for k, v in brief.items() if v}
    BRIEF_FILE.write_text(yaml.safe_dump(brief, sort_keys=False, allow_unicode=True), encoding="utf-8")
    say(f"\nSaved your answers to {BRIEF_FILE.name} — next time you can reuse them.\n")
    return brief


# --------------------------------------------------------------------- menu

def choose_mode():
    say("What would you like to do?")
    say("  1. Quick test        (runs just the first step - fast and cheap, good first try)")
    say("  2. Full strategy     (all 11 steps - the complete strategy document)")
    say("  3. Expand my outline (develops each point of an outline file you wrote)")
    while True:
        choice = ask("Type 1, 2 or 3")
        if choice in ("1", "2", "3"):
            return choice


def open_folder(path: Path):
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", str(path)], check=False)
        else:
            subprocess.run(["xdg-open", str(path)], check=False)
    except Exception:
        pass


def main():
    say("")
    say("=" * 60)
    say("   MEDICOMARKETING STRATEGY AGENT")
    say("=" * 60)
    say("")

    ensure_dependencies()
    ensure_api_key()

    from medicomarketing_agent.engine import StrategyEngine
    from medicomarketing_agent.phases import PHASES

    mode = choose_mode()
    say("")
    brief = build_brief()
    engine = StrategyEngine(brief, out_dir=OUT_DIR)

    if mode == "1":
        say("Running the quick test (Phase 1 only). Watch it think...\n")
        engine.run_pipeline(PHASES[:1])
    elif mode == "2":
        say("Running the full 11-phase strategy. This takes a while — each phase")
        say("streams to this window and is saved as a document.\n")
        engine.run_pipeline()
    else:
        outline_path = HERE / "my-outline.txt"
        if not outline_path.exists():
            say(f"I'll create a file called {outline_path.name} for you.")
            points = ask_lines("Type your outline points now (one per line):")
            if not points:
                say("No points given — nothing to do. Bye!")
                return
            outline_path.write_text("\n".join(f"- {p}" for p in points), encoding="utf-8")
        from medicomarketing_agent.cli import parse_outline
        engine.expand_outline(parse_outline(str(outline_path)))

    say("")
    say("=" * 60)
    say(f"ALL DONE. Your documents are in the '{OUT_DIR.name}' folder:")
    for f in sorted(
        path for path in OUT_DIR.iterdir() if path.suffix.lower() in {".md", ".html"}
    ):
        say(f"  - {f.name}")
    say("The .html report is the visual version; open it in a web browser.")
    say("The .md files preserve the editable source and Mermaid diagrams.")
    say("=" * 60)
    visual_report = OUT_DIR / "medicomarketing-strategy.html"
    if not visual_report.exists():
        visual_report = OUT_DIR / "outline-expansion.html"
    if visual_report.exists():
        webbrowser.open(visual_report.as_uri())
    else:
        open_folder(OUT_DIR)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        say("\n\nStopped. Run me again any time — your answers and key are saved.")
    except Exception as e:  # show a human-readable error instead of a traceback wall
        say("\n" + "!" * 60)
        say(f"Something went wrong: {e}")
        if "authentication" in str(e).lower() or "api_key" in str(e).lower() or "401" in str(e):
            say("Your API key seems invalid. Delete the file 'api_key.txt' and run me again.")
        elif "credit" in str(e).lower() or "billing" in str(e).lower():
            say("It looks like billing isn't set up at platform.claude.com yet.")
        say("!" * 60)
        try:
            input("\nPress Enter to close.")
        except EOFError:
            pass
