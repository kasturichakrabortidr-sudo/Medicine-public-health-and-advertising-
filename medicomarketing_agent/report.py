"""HTML report writer.

The pipeline's Markdown output embeds its visuals as Mermaid code blocks,
which render on GitHub and in Markdown editors but appear as raw code in
Word or a plain-text viewer. This module writes a single .html file next to
the Markdown that any web browser opens as a fully rendered client report —
charts, quadrants, flowcharts, and timelines drawn as real graphics.

The file carries the Markdown inside it and renders in the browser using
pinned CDN builds of marked (Markdown) and Mermaid (diagrams), so the report
needs an internet connection the first time it is opened; if offline, it
degrades to showing the plain text instead of losing the content.
"""

import html
from pathlib import Path

_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
  :root {
    --ink: #1c2230;
    --muted: #5a6472;
    --line: #d9dee6;
    --accent: #0f6b5c;
    --panel: #fbfcfe;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    background: #fff;
    color: var(--ink);
    font-family: -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    line-height: 1.55;
  }
  main { max-width: 940px; margin: 0 auto; padding: 0 28px 90px; }
  header.report {
    border-bottom: 3px solid var(--accent);
    padding: 34px 0 16px;
    margin-bottom: 24px;
  }
  header.report .kicker {
    color: var(--accent);
    font-size: 0.8em;
    font-weight: 700;
    letter-spacing: 0.09em;
    text-transform: uppercase;
  }
  header.report h1 { margin: 6px 0 4px; font-size: 1.9em; }
  header.report .sub { color: var(--muted); font-size: 0.95em; }
  h1, h2, h3, h4 { line-height: 1.25; }
  #content h1 { font-size: 1.55em; margin-top: 1.8em; }
  #content h2 {
    font-size: 1.3em;
    margin-top: 2.1em;
    padding-bottom: 6px;
    border-bottom: 2px solid var(--line);
  }
  #content h3 { font-size: 1.1em; margin-top: 1.6em; }
  hr { border: none; border-top: 1px solid var(--line); margin: 2.2em 0; }
  table { border-collapse: collapse; width: 100%; font-size: 0.92em; margin: 14px 0; }
  th, td { border: 1px solid var(--line); padding: 6px 10px; text-align: left; vertical-align: top; }
  th { background: #f2f5f8; }
  tr:nth-child(even) td { background: #fafbfd; }
  code {
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    font-size: 0.9em;
    background: #f1f3f6;
    padding: 1px 5px;
    border-radius: 4px;
  }
  pre { background: #f6f8fa; border: 1px solid var(--line); border-radius: 8px; padding: 14px; overflow-x: auto; }
  pre code { background: none; padding: 0; }
  pre.mermaid {
    display: flex;
    justify-content: center;
    background: var(--panel);
    padding: 20px;
    margin: 22px 0;
  }
  pre.mermaid svg { max-width: 100%; height: auto; }
  blockquote { border-left: 4px solid var(--accent); margin: 14px 0; padding: 2px 16px; color: var(--muted); }
  .notice {
    background: #fff7e6;
    border: 1px solid #e8cf90;
    border-radius: 8px;
    padding: 10px 14px;
  }
  @media print {
    main { max-width: none; padding: 0 6mm; }
    pre.mermaid { break-inside: avoid; border: none; }
    header.report { padding-top: 8px; }
  }
</style>
</head>
<body>
<main>
  <header class="report">
    <div class="kicker">Medicomarketing Strategy Agent</div>
    <h1>__TITLE__</h1>
    <div class="sub">Evidence-led strategy report &mdash; diagrams and charts render below. For HCP-directed use only after MLR review.</div>
  </header>
  <div id="content"><p class="notice">Rendering the report&hellip; If this message does not go away,
  check your internet connection and reload (the chart renderer is fetched once from the web).</p></div>
</main>
<script type="text/plain" id="source">__MARKDOWN__</script>
<script type="module">
  const content = document.getElementById("content");
  const source = document.getElementById("source").textContent;
  try {
    const [{ marked }, { default: mermaid }] = await Promise.all([
      import("https://cdn.jsdelivr.net/npm/marked@12.0.2/lib/marked.esm.js"),
      import("https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs"),
    ]);
    marked.use({
      renderer: {
        code(code, infostring) {
          const lang = (infostring || "").trim().split(/\\s+/)[0];
          if (lang === "mermaid") {
            const esc = code.replace(/&/g, "&amp;").replace(/</g, "&lt;");
            return '<pre class="mermaid">' + esc + "</pre>";
          }
          return false;
        },
      },
    });
    content.innerHTML = marked.parse(source);
    mermaid.initialize({ startOnLoad: false, theme: "neutral" });
    await mermaid.run({ querySelector: ".mermaid", suppressErrors: true });
  } catch (err) {
    content.innerHTML =
      '<p class="notice">This report needs an internet connection the first time it is opened, ' +
      "to fetch the chart renderer. Showing the plain-text version below.</p>";
    const pre = document.createElement("pre");
    pre.textContent = source;
    content.appendChild(pre);
  }
</script>
</body>
</html>
"""


def write_html_report(markdown_text: str, title: str, path: str | Path) -> Path:
    """Write `markdown_text` as a browser-openable HTML report at `path`."""
    path = Path(path)
    # A literal "</script" inside the embedded Markdown would end the carrier
    # tag early; break it up (harmless inside a text/plain script).
    safe_md = markdown_text.replace("</script", "<\\/script")
    page = _TEMPLATE.replace("__TITLE__", html.escape(title)).replace("__MARKDOWN__", safe_md)
    path.write_text(page, encoding="utf-8")
    return path
