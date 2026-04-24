from __future__ import annotations

import os
from pathlib import Path
import unittest

import duckdb
import importlib.util
import yaml

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency in bare environments
    def load_dotenv() -> bool:
        return False

from app.query.generator import QueryGenerator
from app.query.validator import QueryValidator


REPO_ROOT = Path(__file__).resolve().parents[2]
QUESTION_LIBRARY_PATH = REPO_ROOT / "examples" / "question_library.yml"


def _load_examples() -> list[dict]:
    payload = yaml.safe_load(QUESTION_LIBRARY_PATH.read_text(encoding="utf-8"))
    return payload["examples"]


class QueryPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        load_dotenv()
        cls.examples = _load_examples()
        cls.generator = QueryGenerator()
        cls.validator = QueryValidator()
        cls.db_connection = os.getenv("DB_CONNECTION")

    def test_question_library_is_not_placeholder(self) -> None:
        content = QUESTION_LIBRARY_PATH.read_text(encoding="utf-8")
        self.assertNotIn("Phase 0 placeholder", content)
        self.assertGreaterEqual(len(self.examples), 20)

    def test_examples_render_and_validate(self) -> None:
        for example in self.examples:
            with self.subTest(example_id=example["example_id"]):
                rendered = self.generator.render(example["structured_query_plan"])
                result = self.validator.validate(rendered)

                self.assertTrue(result.is_valid, msg=result.errors)
                self.assertEqual(rendered.template_id, example["expected_template_type"])

                sql_lower = rendered.sql.lower()
                for fragment in example["expected_sql_pattern"]:
                    self.assertIn(fragment.lower(), sql_lower)

    def test_examples_execute_against_duckdb_when_configured(self) -> None:
        if not self.db_connection:
            self.skipTest("DB_CONNECTION is not configured")
        if importlib.util.find_spec("duckdb") is None:
            self.skipTest("duckdb is not installed in the active interpreter")

        connection = duckdb.connect(self.db_connection, read_only=True)

        try:
            for example in self.examples:
                with self.subTest(example_id=example["example_id"]):
                    rendered = self.generator.render(example["structured_query_plan"])
                    result = self.validator.validate(rendered)
                    result.raise_for_errors()

                    row_count = connection.execute(
                        f"SELECT COUNT(*) FROM ({rendered.sql}) AS generated_query"
                    ).fetchone()[0]
                    self.assertGreater(row_count, 0)
        finally:
            connection.close()


if __name__ == "__main__":
    unittest.main()
