from __future__ import annotations

import unittest
from unittest.mock import patch

try:
    import pandas as pd
except ImportError:  # pragma: no cover - optional dependency in bare environments
    pd = None

from app.charts.profiler import ResultProfiler
from app.charts.renderer import ChartRenderer
from app.charts.selector import ChartSelector
from app.intent.parser import QueryPlan
from app.orchestrator import Orchestrator


class StubParser:
    def __init__(self, plan: QueryPlan):
        self.plan = plan

    def parse(self, question: str):
        from app.intent.parser import ParseResult

        return ParseResult(plan=self.plan)


class StubPlanner:
    def __init__(self, plan: dict):
        self.plan = plan

    def build(self, query_plan: QueryPlan):
        from app.query.planner import PlannedQuery

        return PlannedQuery(plan=self.plan, notes=[])


class StubGenerator:
    def render(self, plan: dict):
        from app.query.generator import RenderedQuery

        return RenderedQuery(
            template_id=plan["template_id"],
            sql="SELECT 1",
            tables_used=["population_demographics"],
            fields_used={"population_demographics": {"geo_name", "metric_value"}},
            joins_used=[],
            geo_level=plan.get("geo_level"),
            metric_ids=[plan["metric_id"]],
            plan=plan,
        )


class StubValidation:
    is_valid = True
    errors: list[str] = []

    def raise_for_errors(self) -> None:
        return None


class StubValidator:
    def validate(self, rendered_query):
        return StubValidation()


class StubExecutor:
    def execute(self, rendered_query):
        return pd.DataFrame(
            {
                "geo_level": ["state", "state", "state"],
                "geo_id": ["06", "48", "12"],
                "geo_name": ["California", "Texas", "Florida"],
                "year": [2024, 2024, 2024],
                "metric_value": [39_400_000, 31_200_000, 23_400_000],
                "metric_id": ["pop_total", "pop_total", "pop_total"],
                "metric_label": ["Total Population", "Total Population", "Total Population"],
                "rank": [1, 2, 3],
            }
        )


class StubRenderer:
    def render(self, dataframe, *, selection, query_plan, profile, sql=None):
        from app.charts.renderer import RenderedChart

        return RenderedChart(
            chart_type=selection.chart_type,
            output_path="/tmp/chart.png",
            config_path="/tmp/config.json",
            data_path="/tmp/data.csv",
            command=["Rscript", "render_bar.R"],
        )


@unittest.skipIf(pd is None, "pandas is not installed in the active interpreter")
class ResultProfilerTests(unittest.TestCase):
    def test_profiles_ranking_result_shape(self) -> None:
        dataframe = pd.DataFrame(
            {
                "geo_name": ["California", "Texas"],
                "year": [2024, 2024],
                "metric_value": [1.0, 2.0],
                "rank": [1, 2],
            }
        )

        profile = ResultProfiler().profile(dataframe)

        self.assertEqual(profile.row_count, 2)
        self.assertTrue(profile.has_geo_column)
        self.assertEqual(profile.inferred_shape, "ranking")
        self.assertEqual(profile.measure_count, 1)

    def test_profiles_trend_result_shape(self) -> None:
        dataframe = pd.DataFrame(
            {
                "geo_name": ["California", "California", "California"],
                "period": [2022, 2023, 2024],
                "metric_value": [1.0, 2.0, 3.0],
            }
        )

        profile = ResultProfiler().profile(dataframe)

        self.assertTrue(profile.has_time_series)
        self.assertEqual(profile.time_point_count, 3)
        self.assertEqual(profile.inferred_shape, "trend")


@unittest.skipIf(pd is None, "pandas is not installed in the active interpreter")
class ChartSelectorTests(unittest.TestCase):
    def test_selects_line_for_trend(self) -> None:
        dataframe = pd.DataFrame(
            {
                "geo_name": ["California", "California"],
                "period": [2023, 2024],
                "metric_value": [1.0, 2.0],
            }
        )
        profile = ResultProfiler().profile(dataframe)

        selection = ChartSelector().select("trend", profile)

        self.assertEqual(selection.chart_type, "line")

    def test_selects_boxplot_for_distribution(self) -> None:
        dataframe = pd.DataFrame(
            {
                "geo_name": [f"Geo {i}" for i in range(10)],
                "geo_id": [str(i) for i in range(10)],
                "metric_value": list(range(10)),
                "highlight_flag": [False] * 10,
            }
        )
        profile = ResultProfiler().profile(dataframe)

        selection = ChartSelector().select("distribution", profile)

        self.assertEqual(selection.chart_type, "boxplot")


@unittest.skipIf(pd is None, "pandas is not installed in the active interpreter")
class ChartRendererTests(unittest.TestCase):
    @patch("app.charts.renderer.subprocess.run")
    def test_renderer_writes_temp_inputs_and_calls_rscript(self, mock_run) -> None:
        dataframe = pd.DataFrame(
            {
                "geo_level": ["state", "state"],
                "geo_id": ["06", "48"],
                "geo_name": ["California", "Texas"],
                "year": [2024, 2024],
                "metric_value": [39_400_000, 31_200_000],
                "metric_label": ["Total Population", "Total Population"],
                "rank": [1, 2],
            }
        )
        profile = ResultProfiler().profile(dataframe)
        selection = ChartSelector().select("ranking", profile)
        plan = QueryPlan(question_type="ranking", metric_id="pop_total", geo_level="state", year=2024)

        rendered = ChartRenderer().render(
            dataframe,
            selection=selection,
            query_plan=plan,
            profile=profile,
            sql="SELECT * FROM foo",
        )

        self.assertEqual(rendered.chart_type, "bar")
        self.assertTrue(rendered.output_path.endswith(".png"))
        self.assertIn("--config", rendered.command)
        self.assertTrue(mock_run.called)


@unittest.skipIf(pd is None, "pandas is not installed in the active interpreter")
class OrchestratorPhase4Tests(unittest.TestCase):
    def test_orchestrator_returns_chart_and_answer(self) -> None:
        plan = QueryPlan(question_type="ranking", metric_id="pop_total", geo_level="state", year=2024)
        orchestrator = Orchestrator(
            parser=StubParser(plan),
            planner=StubPlanner(
                {
                    "template_id": "ranking",
                    "metric_id": "pop_total",
                    "source_table": "population_demographics",
                    "geo_level": "state",
                    "year": 2024,
                    "sort_direction": "desc",
                    "limit": 10,
                }
            ),
            generator=StubGenerator(),
            validator=StubValidator(),
            executor=StubExecutor(),
            renderer=StubRenderer(),
        )

        result = orchestrator.run("Which states had the highest total population in 2024?")

        self.assertFalse(result.needs_clarification)
        self.assertEqual(result.chart_selection.chart_type, "bar")
        self.assertEqual(result.chart_path, "/tmp/chart.png")
        self.assertIsNotNone(result.answer_text)


if __name__ == "__main__":
    unittest.main()
