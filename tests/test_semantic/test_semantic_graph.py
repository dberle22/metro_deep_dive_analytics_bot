import json
import tempfile
import unittest
from importlib.util import find_spec
from pathlib import Path


HAS_GRAPH_DEPS = find_spec("yaml") is not None and find_spec("networkx") is not None


@unittest.skipUnless(HAS_GRAPH_DEPS, "semantic graph dependencies are not installed")
class SemanticGraphTests(unittest.TestCase):
    def setUp(self) -> None:
        from semantic_layer.graph_builder import build_semantic_graph, load_catalogs

        self.build_semantic_graph = build_semantic_graph
        self.catalogs = load_catalogs()
        self.graph = build_semantic_graph(self.catalogs)

    def test_graph_contains_expected_node_kinds(self) -> None:
        kinds = {attrs["kind"] for _, attrs in self.graph.nodes(data=True)}
        for expected in {"table", "metric", "geo_level", "template", "question_type", "chart_type"}:
            self.assertIn(expected, kinds)

    def test_graph_contains_core_relationships(self) -> None:
        relations = {attrs["relation"] for _, _, attrs in self.graph.edges(data=True)}
        for expected in {
            "from_table",
            "supports_geo_level",
            "valid_for_geo_level",
            "rolls_up_to",
            "joins_to",
            "uses_template",
            "approved_chart",
        }:
            self.assertIn(expected, relations)

    def test_mermaid_output_mentions_key_entities(self) -> None:
        from semantic_layer.graph_builder import mermaid_from_graph

        mermaid = mermaid_from_graph(self.graph)
        self.assertIn("flowchart LR", mermaid)
        self.assertIn('table_population_demographics["population_demographics"]', mermaid)
        self.assertIn("|joins to|", mermaid)

    def test_default_artifacts_are_written(self) -> None:
        from semantic_layer.graph_builder import write_default_artifacts

        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir) / "semantic_layer"
            root.mkdir(parents=True, exist_ok=True)

            repo_semantic_dir = Path(__file__).resolve().parents[2] / "semantic_layer"
            for filename in [
                "table_catalog.yml",
                "metric_catalog.yml",
                "geography_catalog.yml",
                "join_catalog.yml",
                "chart_rules.yml",
                "query_templates.yml",
            ]:
                (root / filename).write_text((repo_semantic_dir / filename).read_text(encoding="utf-8"), encoding="utf-8")

            artifacts = write_default_artifacts(root)
            for path in artifacts.values():
                self.assertTrue(path.exists())

            summary = json.loads(artifacts["summary"].read_text(encoding="utf-8"))
            self.assertGreater(summary["node_count"], 0)


if __name__ == "__main__":
    unittest.main()
