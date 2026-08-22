"""Tests for the chart rendering module.

These tests exercise every chart type the model is instructed to emit (bar,
pie, quadrant, funnel, tree) and the Markdown post-processing step that turns
```chart code blocks into rendered PNG images, including the graceful
fallback for malformed chart specs.
"""

import json
import tempfile
import unittest
from pathlib import Path

from medicomarketing_agent.visuals import (
    ChartError,
    render_chart,
    render_charts_in_markdown,
)


VALID_SPECS = {
    "bar": {
        "type": "bar", "id": "evidence-volume", "title": "Evidence volume by stream",
        "x_label": "Stream", "y_label": "Items",
        "categories": ["Brand", "Independent", "Evolving", "Guidelines", "Health-economic"],
        "series": [{"name": "Items collated", "values": [3, 2, 2, 3, 1]}],
    },
    "pie": {
        "type": "pie", "id": "evidence-grade", "title": "Evidence grade distribution",
        "labels": ["High", "Moderate", "Low"],
        "values": [5, 3, 2],
    },
    "quadrant": {
        "type": "quadrant", "id": "concordance-map", "title": "Concordance vs discordance",
        "x_label": "Evidence strength", "y_label": "HCP signal strength",
        "x_range": [0, 10], "y_range": [0, 10],
        "quadrant_labels": {
            "top_left": "Perception gap", "top_right": "Amplify",
            "bottom_left": "Low priority", "bottom_right": "Silent zone",
        },
        "points": [
            {"label": "Early initiation safety", "x": 8, "y": 3},
            {"label": "Cost concern", "x": 4, "y": 9},
        ],
    },
    "funnel": {
        "type": "funnel", "id": "adoption-funnel", "title": "HCP adoption funnel",
        "stages": [
            {"label": "Aware", "value": 1000},
            {"label": "Engaged", "value": 600},
            {"label": "Trialling", "value": 250},
            {"label": "Repeating", "value": 120},
            {"label": "Advocating", "value": 40},
        ],
    },
    "tree": {
        "type": "tree", "id": "kpi-tree", "title": "KPI tree", "orientation": "horizontal",
        "nodes": [
            {"id": "rev", "label": "Quarterly revenue growth", "level": 0},
            {"id": "vol", "label": "Rx volume & share", "level": 1},
            {"id": "aware", "label": "Aware", "level": 2},
            {"id": "engaged", "label": "Engaged", "level": 2},
        ],
        "edges": [
            {"from": "rev", "to": "vol"},
            {"from": "vol", "to": "aware"},
            {"from": "vol", "to": "engaged"},
        ],
    },
}


class RenderChartTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp_path = Path(self._tmp.name)

    def test_all_five_chart_types_render_a_nonempty_png(self):
        for chart_type, spec in VALID_SPECS.items():
            with self.subTest(chart_type=chart_type):
                out_path = self.tmp_path / f"{chart_type}.png"
                render_chart(spec, out_path)
                self.assertTrue(out_path.exists())
                self.assertGreater(out_path.stat().st_size, 1000)

    def test_tree_chart_without_explicit_edges_auto_meshes_levels(self):
        spec = {
            "type": "tree", "id": "auto-mesh", "title": "Auto mesh",
            "nodes": [
                {"id": "a", "label": "Root", "level": 0},
                {"id": "b", "label": "Child 1", "level": 1},
                {"id": "c", "label": "Child 2", "level": 1},
            ],
        }
        out_path = self.tmp_path / "auto-mesh.png"
        render_chart(spec, out_path)
        self.assertTrue(out_path.exists())

    def test_unknown_chart_type_raises_chart_error(self):
        spec = {"type": "scatter3d", "id": "x", "title": "x"}
        with self.assertRaises(ChartError):
            render_chart(spec, self.tmp_path / "bad.png")

    def test_bar_chart_missing_categories_raises_chart_error(self):
        spec = {"type": "bar", "id": "x", "title": "x", "series": [{"values": [1, 2]}]}
        with self.assertRaises(ChartError):
            render_chart(spec, self.tmp_path / "bad.png")

    def test_bar_chart_series_length_mismatch_raises_chart_error(self):
        spec = {
            "type": "bar", "id": "x", "title": "x",
            "categories": ["A", "B", "C"],
            "series": [{"name": "s", "values": [1, 2]}],
        }
        with self.assertRaises(ChartError):
            render_chart(spec, self.tmp_path / "bad.png")

    def test_pie_chart_mismatched_lengths_raises_chart_error(self):
        spec = {"type": "pie", "id": "x", "title": "x", "labels": ["A", "B"], "values": [1]}
        with self.assertRaises(ChartError):
            render_chart(spec, self.tmp_path / "bad.png")

    def test_quadrant_chart_point_missing_coordinates_raises_chart_error(self):
        spec = {
            "type": "quadrant", "id": "x", "title": "x",
            "points": [{"label": "missing xy"}],
        }
        with self.assertRaises(ChartError):
            render_chart(spec, self.tmp_path / "bad.png")

    def test_funnel_chart_non_numeric_value_raises_chart_error(self):
        spec = {
            "type": "funnel", "id": "x", "title": "x",
            "stages": [{"label": "Aware", "value": "lots"}],
        }
        with self.assertRaises(ChartError):
            render_chart(spec, self.tmp_path / "bad.png")

    def test_tree_chart_node_missing_label_raises_chart_error(self):
        spec = {"type": "tree", "id": "x", "title": "x", "nodes": [{"id": "a"}]}
        with self.assertRaises(ChartError):
            render_chart(spec, self.tmp_path / "bad.png")


class RenderChartsInMarkdownTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp_path = Path(self._tmp.name)
        self.charts_dir = self.tmp_path / "charts"
        self.log_messages: list[str] = []

    def _log(self, msg: str) -> None:
        self.log_messages.append(msg)

    def test_valid_chart_block_is_replaced_with_image_embed(self):
        spec = VALID_SPECS["pie"]
        markdown = (
            "# Phase 3\n\nSome table.\n\n"
            f"```chart\n{json.dumps(spec)}\n```\n\nMore text."
        )
        result = render_charts_in_markdown(markdown, self.charts_dir, "03-evidence-forefront", log=self._log)

        self.assertNotIn("```chart", result)
        self.assertIn("![Evidence grade distribution](charts/", result)
        self.assertIn("More text.", result)
        pngs = list(self.charts_dir.glob("*.png"))
        self.assertEqual(len(pngs), 1)
        self.assertTrue((self.charts_dir / f"{pngs[0].name}.json").exists())

    def test_multiple_chart_blocks_each_get_a_unique_file(self):
        markdown = "\n\n".join(
            f"```chart\n{json.dumps(spec)}\n```" for spec in VALID_SPECS.values()
        )
        result = render_charts_in_markdown(markdown, self.charts_dir, "10-measurement", log=self._log)
        self.assertNotIn("```chart", result)
        pngs = list(self.charts_dir.glob("*.png"))
        self.assertEqual(len(pngs), len(VALID_SPECS))

    def test_malformed_json_is_left_as_a_code_block_and_logged(self):
        markdown = "```chart\n{not valid json\n```"
        result = render_charts_in_markdown(markdown, self.charts_dir, "05-behavioural-drivers", log=self._log)
        self.assertIn("```chart", result)
        self.assertTrue(any("could not parse chart" in m for m in self.log_messages))
        self.assertEqual(list(self.charts_dir.glob("*.png")), [])

    def test_unrenderable_spec_is_left_as_a_code_block_and_logged(self):
        spec = {"type": "pie", "id": "bad", "title": "Bad", "labels": ["A"], "values": [1, 2]}
        markdown = f"```chart\n{json.dumps(spec)}\n```"
        result = render_charts_in_markdown(markdown, self.charts_dir, "06-evidence-position", log=self._log)
        self.assertIn("```chart", result)
        self.assertTrue(any("could not render chart" in m for m in self.log_messages))

    def test_non_chart_code_blocks_are_left_untouched(self):
        markdown = "```python\nprint('hello')\n```"
        result = render_charts_in_markdown(markdown, self.charts_dir, "01-critical-thinking", log=self._log)
        self.assertEqual(result, markdown)

    def test_text_without_any_chart_blocks_is_unchanged(self):
        markdown = "# Just prose\n\nNo charts here at all."
        result = render_charts_in_markdown(markdown, self.charts_dir, "02-scientific-criteria", log=self._log)
        self.assertEqual(result, markdown)


if __name__ == "__main__":
    unittest.main()
