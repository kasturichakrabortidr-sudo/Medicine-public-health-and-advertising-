"""Renders real chart images from the structured chart specs the model emits.

Every phase in ``phases.py`` that presents comparative, hierarchical,
sequential, or quantitative data is instructed (via the system prompt's
"CHART SPEC FORMAT") to also emit a small, well-defined JSON chart spec
inside a fenced ```chart code block, placed next to the table/section it
visualises. This module finds those blocks in a phase's raw Markdown output,
renders each one to a real PNG chart with matplotlib (no browser, no
network, no Node.js dependency), and swaps the code block for a Markdown
image embed — so the shipped documents contain genuine graphical and
infographic representations of the underlying evidence and strategy data,
not only prose and tables.

Rendering is deliberately best-effort: a single malformed or unrenderable
chart spec is left in place as a code block (with a warning logged) rather
than breaking the whole phase, because a client-ready strategy document with
one ugly leftover code block is far better than one that fails to generate.
"""

from __future__ import annotations

import json
import re
import textwrap
from pathlib import Path
from typing import Callable

import matplotlib

matplotlib.use("Agg")  # headless: no display server required

import matplotlib.pyplot as plt  # noqa: E402 (must follow matplotlib.use)

CHART_BLOCK_RE = re.compile(r"```chart[^\n]*\n(.*?)```", re.DOTALL)

FIGSIZE = (8, 5)
DPI = 160
PALETTE = [
    "#1f6f8b", "#e0724a", "#6aa84f", "#8e44ad", "#c9a227",
    "#2c3e50", "#d1495b", "#3d5a80", "#59a14f", "#af7ac5",
]


class ChartError(ValueError):
    """Raised when a chart spec cannot be parsed or rendered."""


def render_charts_in_markdown(
    markdown: str,
    charts_dir: Path,
    phase_id: str,
    log: Callable[[str], None] = lambda _msg: None,
) -> str:
    """Replace every ```chart block in ``markdown`` with a rendered PNG embed.

    Chart PNGs (and a JSON sidecar of the spec, for auditability) are written
    under ``charts_dir``. Returns the updated markdown text. ``charts_dir``
    should be reachable via a relative ``charts/...`` path from wherever the
    resulting markdown file itself is written.
    """
    charts_dir.mkdir(parents=True, exist_ok=True)
    counter = 0

    def _replace(match: "re.Match[str]") -> str:
        nonlocal counter
        counter += 1
        raw = match.group(1)
        try:
            spec = json.loads(raw)
        except json.JSONDecodeError as exc:
            log(f"[chart] {phase_id}: could not parse chart #{counter} ({exc}); left as a code block.")
            return match.group(0)
        if not isinstance(spec, dict):
            log(f"[chart] {phase_id}: chart #{counter} is not a JSON object; left as a code block.")
            return match.group(0)

        slug = _slugify(str(spec.get("id") or spec.get("title") or f"chart-{counter}"))
        filename = f"{phase_id}-{counter:02d}-{slug}.png"
        out_path = charts_dir / filename
        try:
            render_chart(spec, out_path)
        except ChartError as exc:
            log(f"[chart] {phase_id}: could not render chart '{slug}' ({exc}); left as a code block.")
            return match.group(0)

        (charts_dir / f"{filename}.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")
        title = spec.get("title") or slug.replace("-", " ").title()
        log(f"[chart] {phase_id}: rendered '{title}' -> charts/{filename}")
        return f"![{title}](charts/{filename})\n\n*Figure: {title}*"

    return CHART_BLOCK_RE.sub(_replace, markdown)


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "chart"


# --------------------------------------------------------------- rendering

def render_chart(spec: dict, out_path: Path) -> None:
    """Render one chart spec to ``out_path`` as a PNG. Raises ChartError."""
    chart_type = spec.get("type")
    renderer = _RENDERERS.get(chart_type)
    if renderer is None:
        raise ChartError(f"unknown chart type {chart_type!r} (expected one of {sorted(_RENDERERS)})")

    figsize = _tree_figsize(spec) if chart_type == "tree" else FIGSIZE
    fig, ax = plt.subplots(figsize=figsize)
    try:
        renderer(spec, ax)
        title = spec.get("title")
        if title and chart_type != "tree":  # tree renders its own title so multi-line labels fit
            ax.set_title(str(title), fontsize=13, fontweight="bold", pad=14)
        fig.tight_layout()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path, dpi=DPI, facecolor="white")
    except ChartError:
        raise
    except Exception as exc:  # defensive: never let one bad spec crash the pipeline
        raise ChartError(str(exc)) from exc
    finally:
        plt.close(fig)


def _require(spec: dict, *keys: str) -> None:
    missing = [k for k in keys if k not in spec]
    if missing:
        raise ChartError(f"missing required field(s): {', '.join(missing)}")


def _tree_figsize(spec: dict) -> tuple[float, float]:
    """Size the figure to the tree's actual shape instead of a fixed box, so
    wide/shallow bridge diagrams and tall/narrow hierarchies both use the
    canvas efficiently rather than floating in whitespace."""
    nodes = spec.get("nodes", []) or []
    per_level: dict[int, int] = {}
    for node in nodes:
        lvl = int(node.get("level", 0))
        per_level[lvl] = per_level.get(lvl, 0) + 1
    n_levels = max(len(per_level), 1)
    max_per_level = max(per_level.values()) if per_level else 1
    if spec.get("orientation") == "horizontal":
        width = max(8.0, min(16.0, 1.9 * n_levels + 2.0))
        height = max(3.5, min(10.0, 1.3 * max_per_level + 1.2))
    else:
        width = max(8.0, min(16.0, 1.7 * max_per_level + 2.0))
        height = max(4.0, min(10.0, 1.5 * n_levels + 1.2))
    return width, height


def _strip_top_right_spines(ax) -> None:
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


def _render_bar(spec: dict, ax) -> None:
    _require(spec, "categories", "series")
    categories = spec["categories"]
    series = spec["series"]
    if not categories or not series:
        raise ChartError("bar chart needs at least one category and one series")
    n_series = len(series)
    n_cats = len(categories)
    width = 0.8 / max(n_series, 1)
    x = list(range(n_cats))
    for i, s in enumerate(series):
        values = s.get("values", [])
        if len(values) != n_cats:
            raise ChartError(f"series {s.get('name', i)!r} values must align with categories")
        offsets = [xi + (i - (n_series - 1) / 2) * width for xi in x]
        ax.bar(offsets, values, width=width, label=s.get("name", f"Series {i + 1}"),
               color=PALETTE[i % len(PALETTE)])
    ax.set_xticks(x)
    ax.set_xticklabels([textwrap.fill(str(c), 16) for c in categories], rotation=15, ha="right")
    if spec.get("x_label"):
        ax.set_xlabel(spec["x_label"])
    if spec.get("y_label"):
        ax.set_ylabel(spec["y_label"])
    if n_series > 1:
        ax.legend(fontsize=8)
    _strip_top_right_spines(ax)
    ax.grid(axis="y", alpha=0.25)


def _render_pie(spec: dict, ax) -> None:
    _require(spec, "labels", "values")
    labels, values = spec["labels"], spec["values"]
    if not labels or not values or len(labels) != len(values):
        raise ChartError("pie chart needs equal-length, non-empty labels and values")
    colors = [PALETTE[i % len(PALETTE)] for i in range(len(labels))]
    ax.pie(
        values, labels=labels, autopct="%1.0f%%", colors=colors, startangle=90,
        wedgeprops={"edgecolor": "white", "linewidth": 1},
        textprops={"fontsize": 9},
    )
    ax.set_aspect("equal")


def _render_quadrant(spec: dict, ax) -> None:
    _require(spec, "points")
    points = spec["points"]
    if not points:
        raise ChartError("quadrant chart needs at least one point")
    for p in points:
        _require(p, "x", "y")
    x_range = spec.get("x_range", [0, 10])
    y_range = spec.get("y_range", [0, 10])

    xs = [p["x"] for p in points]
    ys = [p["y"] for p in points]
    ax.scatter(xs, ys, s=150, color=PALETTE[0], zorder=3, edgecolor="white", linewidth=1)
    for p in points:
        ax.annotate(str(p.get("label", "")), (p["x"], p["y"]), textcoords="offset points",
                    xytext=(6, 6), fontsize=8)

    mid_x = sum(x_range) / 2
    mid_y = sum(y_range) / 2
    ax.axvline(mid_x, color="#999999", linestyle="--", linewidth=1)
    ax.axhline(mid_y, color="#999999", linestyle="--", linewidth=1)
    ax.set_xlim(*x_range)
    ax.set_ylim(*y_range)
    ax.set_xlabel(spec.get("x_label", ""))
    ax.set_ylabel(spec.get("y_label", ""))

    q = spec.get("quadrant_labels", {}) or {}
    corners = {
        "top_left": (x_range[0], y_range[1], "left", "top"),
        "top_right": (x_range[1], y_range[1], "right", "top"),
        "bottom_left": (x_range[0], y_range[0], "left", "bottom"),
        "bottom_right": (x_range[1], y_range[0], "right", "bottom"),
    }
    for key, (cx, cy, ha, va) in corners.items():
        label = q.get(key)
        if label:
            ax.text(cx, cy, textwrap.fill(str(label), 18), ha=ha, va=va, fontsize=7.5,
                     style="italic", color="#555555",
                     bbox={"boxstyle": "round", "fc": "white", "ec": "none", "alpha": 0.75})
    _strip_top_right_spines(ax)


def _render_funnel(spec: dict, ax) -> None:
    _require(spec, "stages")
    stages = spec["stages"]
    if not stages:
        raise ChartError("funnel chart needs at least one stage")
    n = len(stages)
    values = []
    for s in stages:
        v = s.get("value", 0)
        if not isinstance(v, (int, float)):
            raise ChartError(f"stage {s.get('label', '?')!r} value must be numeric")
        values.append(v)
    max_v = max(values) or 1

    ax.set_xlim(-1.15, 1.15)
    ax.set_ylim(0, n)
    ax.axis("off")
    for i, (s, v) in enumerate(zip(stages, values)):
        y = n - i - 1
        half_w = 0.15 + 0.85 * (v / max_v)
        ax.add_patch(plt.Polygon(
            [(-half_w, y + 0.08), (half_w, y + 0.08), (half_w, y + 0.92), (-half_w, y + 0.92)],
            closed=True, color=PALETTE[i % len(PALETTE)], alpha=0.9,
        ))
        value_text = f"{v:,.0f}" if float(v).is_integer() else f"{v:,.1f}"
        ax.text(0, y + 0.5, f"{s.get('label', '')}  —  {value_text}", ha="center", va="center",
                 color="white", fontsize=9, fontweight="bold")


def _render_tree(spec: dict, ax) -> None:
    _require(spec, "nodes")
    nodes = spec["nodes"]
    if not nodes:
        raise ChartError("tree chart needs at least one node")
    for n in nodes:
        _require(n, "id", "label")

    orientation = spec.get("orientation", "vertical")
    levels: dict[int, list[dict]] = {}
    for node in nodes:
        levels.setdefault(int(node.get("level", 0)), []).append(node)

    edges = spec.get("edges")
    if edges is None:
        edges = []
        sorted_levels = sorted(levels)
        for lvl, nxt in zip(sorted_levels, sorted_levels[1:]):
            for a in levels[lvl]:
                for b in levels[nxt]:
                    edges.append({"from": a["id"], "to": b["id"]})

    positions: dict[str, tuple[float, float]] = {}
    for lvl, ns in levels.items():
        for i, node in enumerate(ns):
            offset = i - (len(ns) - 1) / 2
            positions[node["id"]] = (lvl, offset) if orientation == "horizontal" else (offset, -lvl)

    ax.axis("off")
    if spec.get("title"):
        ax.set_title(str(spec["title"]), fontsize=13, fontweight="bold", pad=14)

    for edge in edges:
        src, dst = edge.get("from"), edge.get("to")
        if src not in positions or dst not in positions:
            continue
        x1, y1 = positions[src]
        x2, y2 = positions[dst]
        ax.annotate(
            "", xy=(x2, y2), xytext=(x1, y1),
            arrowprops={"arrowstyle": "-|>", "color": "#999999", "lw": 1.2,
                        "shrinkA": 20, "shrinkB": 20},
        )

    for node in nodes:
        x, y = positions[node["id"]]
        label = textwrap.fill(str(node["label"]), 22)
        level = int(node.get("level", 0))
        color = PALETTE[level % len(PALETTE)]
        ax.text(x, y, label, ha="center", va="center", fontsize=8.5, color="white",
                 fontweight="bold", bbox={"boxstyle": "round,pad=0.5", "fc": color, "ec": "none"})

    xs = [p[0] for p in positions.values()]
    ys = [p[1] for p in positions.values()]
    pad = 1.0
    ax.set_xlim(min(xs) - pad, max(xs) + pad)
    ax.set_ylim(min(ys) - pad, max(ys) + pad)


_RENDERERS: dict[str, Callable[[dict, object], None]] = {
    "bar": _render_bar,
    "pie": _render_pie,
    "quadrant": _render_quadrant,
    "funnel": _render_funnel,
    "tree": _render_tree,
}
