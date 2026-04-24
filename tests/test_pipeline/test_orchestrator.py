from __future__ import annotations

import os
import unittest

from app.intent.parser import IntentParser
from app.llm.provider import LLMProvider
from app.orchestrator import Orchestrator
from app.query.executor import QueryExecutor


class StubProvider(LLMProvider):
    def __init__(self, payload: dict):
        self.payload = payload

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict:
        assert "Approved tables" in system_prompt
        assert "Few-shot examples" in system_prompt
        assert "Question:" in user_prompt
        return self.payload


class IntentParserTests(unittest.TestCase):
    def test_parser_exact_match_recovers_example_plan(self) -> None:
        parser = IntentParser()
        result = parser.parse("Which states had the highest total population in 2024?")

        self.assertFalse(result.needs_clarification)
        self.assertEqual(result.matched_example_id, "q01_ranking_pop_states")
        self.assertIsNotNone(result.plan)
        assert result.plan is not None
        self.assertEqual(result.plan.template_id, "ranking")
        self.assertEqual(result.plan.metric_id, "pop_total")
        self.assertEqual(result.plan.geo_level, "state")

    def test_parser_returns_targeted_clarification_when_required_slots_are_missing(self) -> None:
        parser = IntentParser()
        result = parser.parse("Which places are growing fastest?")

        self.assertTrue(result.needs_clarification)
        self.assertIsNotNone(result.clarification)
        assert result.clarification is not None
        self.assertIn("base_metric_id", result.clarification.missing_fields)
        self.assertIn("end_year", result.clarification.missing_fields)
        self.assertIn("window_years", result.clarification.missing_fields)

    def test_parser_can_use_provider_payload(self) -> None:
        parser = IntentParser(
            provider=StubProvider(
                {
                    "clarification_needed": False,
                    "query_plan": {
                        "question_type": "ranking",
                        "metric_id": "median_hh_income",
                        "source_table": "economics_income_wide",
                        "geo_level": "state",
                        "year": 2023,
                        "sort_direction": "desc",
                        "limit": 5,
                    },
                }
            )
        )

        result = parser.parse("Rank states by median household income.")

        self.assertFalse(result.needs_clarification)
        self.assertEqual(result.provider_used, "StubProvider")
        self.assertIsNotNone(result.plan)
        assert result.plan is not None
        self.assertEqual(result.plan.metric_id, "median_hh_income")

    def test_parser_matches_question_library_examples_at_target_rate(self) -> None:
        parser = IntentParser()
        matched = 0

        for example in parser.examples:
            result = parser.parse(example["natural_language_question"])
            if result.plan is None:
                continue
            actual = result.plan.model_dump(exclude_none=True)
            if actual == example["structured_query_plan"]:
                matched += 1

        accuracy = matched / len(parser.examples)
        self.assertGreaterEqual(accuracy, 0.8)


class OrchestratorTests(unittest.TestCase):
    @unittest.skipUnless(os.getenv("DB_CONNECTION"), "DB_CONNECTION is not configured")
    def test_orchestrator_runs_end_to_end_with_duckdb(self) -> None:
        orchestrator = Orchestrator(executor=QueryExecutor())
        result = orchestrator.run(
            "Which states had the highest total population in 2024?"
        )

        self.assertFalse(result.needs_clarification)
        self.assertIsNotNone(result.query_plan)
        self.assertIsNotNone(result.validation)
        assert result.validation is not None
        self.assertTrue(result.validation.is_valid)
        self.assertIsNotNone(result.sql)
        assert result.sql is not None
        self.assertIn("gold.population_demographics", result.sql)
        self.assertIsNotNone(result.dataframe)
        assert result.dataframe is not None
        self.assertFalse(result.dataframe.empty)


if __name__ == "__main__":
    unittest.main()
