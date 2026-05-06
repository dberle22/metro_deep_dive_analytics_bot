from __future__ import annotations

import unittest

try:
    import pandas as pd
except ImportError:  # pragma: no cover - optional dependency in bare environments
    pd = None

from app.charts.renderer import ChartRenderer
from app.intent.parser import IntentParser, QueryPlan
from app.query.generator import QueryGenerator
from app.response.assembler import ResponseAssembler


class Loop4ParserFixTests(unittest.TestCase):
    def test_benchmark_questions_default_to_latest_year(self) -> None:
        parser = IntentParser()

        result = parser.parse("How does Texas household income stack up against the national average?")

        self.assertFalse(result.needs_clarification)
        assert result.plan is not None
        self.assertEqual(result.plan.template_id, "benchmark")
        self.assertEqual(result.plan.year, 2024)

    def test_benchmark_question_keeps_named_state_as_target_level(self) -> None:
        parser = IntentParser()

        result = parser.parse("Compare Florida's population to the US in 2024.")

        self.assertFalse(result.needs_clarification)
        assert result.plan is not None
        self.assertEqual(result.plan.target_geo_level, "state")
        self.assertEqual(result.plan.target_geo_id, "12")
        self.assertEqual(result.plan.benchmark_geo_level, "us")

    def test_relative_growth_phrase_defaults_end_year(self) -> None:
        parser = IntentParser()

        result = parser.parse("What are the fastest-growing states by population over the last five years?")

        self.assertFalse(result.needs_clarification)
        assert result.plan is not None
        self.assertEqual(result.plan.template_id, "growth")
        self.assertEqual(result.plan.end_year, 2024)
        self.assertEqual(result.plan.window_years, 5)

    def test_since_year_growth_question_infers_window(self) -> None:
        parser = IntentParser()

        result = parser.parse("Rank states by housing unit growth since 2019.")

        self.assertFalse(result.needs_clarification)
        assert result.plan is not None
        self.assertEqual(result.plan.template_id, "growth")
        self.assertEqual(result.plan.end_year, 2024)
        self.assertEqual(result.plan.window_years, 5)


class Loop4GeneratorFixTests(unittest.TestCase):
    def test_benchmark_sql_uses_reference_then_inline_fallback(self) -> None:
        generator = QueryGenerator()

        rendered = generator.render(
            {
                "template_id": "benchmark",
                "question_type": "benchmark",
                "metric_id": "pop_total",
                "source_table": "population_demographics",
                "target_geo_level": "state",
                "target_geo_id": "12",
                "benchmark_type": "us",
                "benchmark_geo_level": "us",
                "comparison_label": "United States",
                "year": 2024,
            }
        )

        self.assertIn("reference_benchmark AS", rendered.sql)
        self.assertIn("benchmark_inline AS", rendered.sql)
        self.assertIn("WHERE NOT EXISTS (SELECT 1 FROM reference_benchmark)", rendered.sql)


@unittest.skipIf(pd is None, "pandas is not installed in the active interpreter")
class Loop4ResponseAndChartFixTests(unittest.TestCase):
    def test_growth_label_style_uses_percent(self) -> None:
        renderer = ChartRenderer()
        plan = QueryPlan(
            question_type="ranking",
            base_metric_id="pop_total",
            geo_level="state",
            end_year=2024,
            window_years=5,
            template_id="growth",
        )

        self.assertEqual(renderer._label_style(plan), "percent")

    def test_comparison_answer_names_leader_and_gaps(self) -> None:
        assembler = ResponseAssembler()
        dataframe = pd.DataFrame(
            {
                "geo_name": ["Texas", "California", "Florida"],
                "metric_value": [73035, 65149, 61777],
                "metric_label": ["Median Household Income"] * 3,
            }
        )
        plan = QueryPlan(
            question_type="comparison",
            metric_id="median_hh_income",
            geo_level="state",
            geo_ids=["48", "06", "12"],
            year=2024,
        )

        response = assembler.assemble(
            question="Compare California, Texas, and Florida on median household income in 2024.",
            query_plan=plan,
            dataframe=dataframe,
            profile=None,
            selection=None,
        )

        self.assertIn("Texas leads", response.answer_text)
        self.assertIn("California", response.answer_text)
        self.assertIn("Florida", response.answer_text)

    def test_benchmark_answer_states_above_or_below(self) -> None:
        assembler = ResponseAssembler()
        dataframe = pd.DataFrame(
            {
                "geo_name": ["Florida", "United States"],
                "metric_value": [23400000, 336000000],
                "comparison_group": ["target", "benchmark"],
                "metric_label": ["Total Population", "Total Population"],
            }
        )
        plan = QueryPlan(
            question_type="benchmark",
            metric_id="pop_total",
            target_geo_level="state",
            target_geo_id="12",
            benchmark_type="us",
            year=2024,
        )

        response = assembler.assemble(
            question="Compare Florida's population to the US in 2024.",
            query_plan=plan,
            dataframe=dataframe,
            profile=None,
            selection=None,
        )

        self.assertIn("Florida is below United States", response.answer_text)


if __name__ == "__main__":
    unittest.main()
