"""Render the generated Markdown strategy as a client-friendly visual report."""

from __future__ import annotations

from html import escape
from pathlib import Path

import mistune


MERMAID_MODULE_URL = (
    "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs"
)


class _StrategyRenderer(mistune.HTMLRenderer):
    """Escape model-authored HTML and expose Mermaid fences to the renderer."""

    def __init__(self) -> None:
        super().__init__(escape=True)

    def block_code(self, code: str, info: str | None = None) -> str:
        language = (info or "").strip().split(maxsplit=1)[0].lower()
        if language == "mermaid":
            return f'<pre class="mermaid">{escape(code)}</pre>\n'
        return super().block_code(code, info)


def render_strategy_html(markdown_text: str, title: str) -> str:
    """Convert strategy Markdown into a standalone visual HTML document.

    Scientific diagrams remain text until Mermaid loads in the browser. This
    preserves the underlying evidence map even when the report is opened
    offline, while avoiding execution of HTML authored by the model.
    """

    renderer = _StrategyRenderer()
    markdown = mistune.create_markdown(
        renderer=renderer,
        plugins=["table", "strikethrough", "task_lists"],
    )
    body = markdown(markdown_text)
    safe_title = escape(title)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe_title}</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #183044;
      --muted: #5f7281;
      --paper: #ffffff;
      --wash: #eef6f7;
      --line: #cbdadd;
      --accent: #007f83;
      --accent-dark: #005d61;
      --caution: #a05a00;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      background: var(--wash);
      font: 16px/1.6 Inter, ui-sans-serif, system-ui, -apple-system,
        BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    main {{
      width: min(1180px, calc(100% - 32px));
      margin: 32px auto;
      padding: clamp(24px, 5vw, 64px);
      background: var(--paper);
      border-top: 8px solid var(--accent);
      border-radius: 8px;
      box-shadow: 0 16px 44px rgb(24 48 68 / 12%);
    }}
    h1, h2, h3 {{ line-height: 1.2; color: var(--accent-dark); }}
    h1 {{ font-size: clamp(2rem, 5vw, 3.5rem); }}
    h2 {{
      margin-top: 2.5em;
      padding-bottom: .35em;
      border-bottom: 2px solid var(--line);
    }}
    a {{ color: var(--accent-dark); }}
    table {{
      display: block;
      width: 100%;
      overflow-x: auto;
      border-collapse: collapse;
      margin: 1.25rem 0 2rem;
      font-size: .92rem;
    }}
    th, td {{
      min-width: 120px;
      padding: .7rem .8rem;
      border: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
    }}
    th {{ background: var(--wash); }}
    blockquote {{
      margin: 1.5rem 0;
      padding: .25rem 1.25rem;
      color: var(--muted);
      border-left: 5px solid var(--accent);
      background: #f8fbfb;
    }}
    code {{
      padding: .12rem .3rem;
      border-radius: 3px;
      background: #edf2f3;
    }}
    pre {{
      overflow-x: auto;
      padding: 1rem;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #f8fbfb;
    }}
    .mermaid {{
      margin: 1.75rem 0 .75rem;
      padding: 1.25rem;
      text-align: center;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fbfefe;
    }}
    hr {{ margin: 3rem 0; border: 0; border-top: 1px solid var(--line); }}
    @media print {{
      body {{ background: #fff; }}
      main {{ width: 100%; margin: 0; padding: 18mm; box-shadow: none; }}
      h2, h3, table, blockquote, .mermaid {{ break-inside: avoid; }}
    }}
  </style>
</head>
<body>
  <main>{body}</main>
  <script type="module">
    import mermaid from "{MERMAID_MODULE_URL}";
    mermaid.initialize({{
      startOnLoad: true,
      securityLevel: "strict",
      theme: "base",
      themeVariables: {{
        primaryColor: "#dff1f1",
        primaryTextColor: "#183044",
        primaryBorderColor: "#007f83",
        lineColor: "#476b73",
        secondaryColor: "#eef6f7",
        tertiaryColor: "#fff4dc",
        fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
      }}
    }});
  </script>
</body>
</html>
"""


def write_strategy_html(markdown_path: Path, html_path: Path, title: str) -> Path:
    """Render a Markdown strategy file and return the written HTML path."""

    markdown_text = markdown_path.read_text(encoding="utf-8")
    html_path.write_text(render_strategy_html(markdown_text, title), encoding="utf-8")
    return html_path
