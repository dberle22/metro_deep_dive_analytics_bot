from __future__ import annotations

import unittest

from app.intent.parser import IntentParser


class GrowthParserDefaultsTests(unittest.TestCase):
    def test_growth_question_uses_fast_heuristic_defaults(self) -> None:
        parser = IntentParser()

        result = parser.parse("Which states had the highest population growth over 5 years?")

        self.assertFalse(result.needs_clarification)
        self.assertIsNotNone(result.plan)
        assert result.plan is not None
        self.assertEqual(result.plan.template_id, "growth")
        self.assertEqual(result.plan.question_type, "ranking")
        self.assertEqual(result.plan.base_metric_id, "pop_total")
        self.assertEqual(result.plan.source_table, "population_demographics")
        self.assertEqual(result.plan.geo_level, "state")
        self.assertEqual(result.plan.end_year, 2024)
        self.assertEqual(result.plan.window_years, 5)


if __name__ == "__main__":
    unittest.main()
