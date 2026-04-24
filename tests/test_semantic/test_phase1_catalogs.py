from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
SEMANTIC_DIR = REPO_ROOT / "semantic_layer"


def _read_catalog(name: str) -> str:
    return (SEMANTIC_DIR / name).read_text(encoding="utf-8")


class Phase1CatalogTests(unittest.TestCase):
    def test_phase1_catalogs_are_not_placeholders(self) -> None:
        for filename in [
            "table_catalog.yml",
            "metric_catalog.yml",
            "geography_catalog.yml",
            "join_catalog.yml",
            "chart_rules.yml",
            "query_templates.yml",
        ]:
            content = _read_catalog(filename)
            self.assertNotIn("Phase 0 placeholder", content)
            self.assertIn("catalog_name:", content)
            self.assertIn("version:", content)

    def test_table_catalog_has_expected_active_and_deferred_tables(self) -> None:
        content = _read_catalog("table_catalog.yml")
        for required in [
            "table_id: population_demographics",
            "table_id: housing_core_wide",
            "table_id: economics_income_wide",
        ]:
            self.assertIn(required, content)

        self.assertGreaterEqual(content.count("status: deferred"), 6)

    def test_metric_catalog_covers_three_active_subject_areas(self) -> None:
        content = _read_catalog("metric_catalog.yml")
        self.assertGreaterEqual(content.count("source_table: population_demographics"), 8)
        self.assertGreaterEqual(content.count("source_table: housing_core_wide"), 8)
        self.assertGreaterEqual(content.count("source_table: economics_income_wide"), 8)

    def test_query_templates_cover_phase1_patterns(self) -> None:
        content = _read_catalog("query_templates.yml")
        for template_id in [
            "template_id: ranking",
            "template_id: trend",
            "template_id: compare_selected",
            "template_id: distribution",
            "template_id: benchmark",
            "template_id: growth",
        ]:
            self.assertIn(template_id, content)


if __name__ == "__main__":
    unittest.main()
