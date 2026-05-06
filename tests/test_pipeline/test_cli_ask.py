from __future__ import annotations

import io
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from app.intent.parser import ClarificationRequest, ParseResult, QueryPlan
from app.orchestrator import OrchestrationResult
from app.scripts.ask import (
    TimedOrchestrationResult,
    TimedParseResult,
    append_model_test_log,
    main,
    resolve_output_dir,
    save_run_artifacts,
)


class AskCliTests(unittest.TestCase):
    def test_resolve_output_dir_rejects_paths_outside_repo(self) -> None:
        with self.assertRaises(ValueError):
            resolve_output_dir("../outside")

    @patch("app.scripts.ask.parse_only")
    def test_parser_only_json_output(self, mock_parse_only) -> None:
        mock_parse_only.return_value = TimedParseResult(
            result=ParseResult(
                plan=QueryPlan(
                    question_type="ranking",
                    metric_id="pop_total",
                    geo_level="state",
                    year=2024,
                ),
                provider_used="StubProvider",
            ),
            timings_ms={"parse": 123.4},
        )

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = main(
                [
                    "Which states had the highest total population in 2024?",
                    "--parser-only",
                    "--json",
                ]
            )

        self.assertEqual(exit_code, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["plan"]["metric_id"], "pop_total")
        self.assertEqual(payload["provider_used"], "StubProvider")
        self.assertEqual(payload["timings_ms"]["parse"], 123.4)

    @patch("app.scripts.ask.run_question")
    def test_full_run_summary_output(self, mock_run_question) -> None:
        plan = QueryPlan(
            question_type="ranking",
            metric_id="pop_total",
            geo_level="state",
            year=2024,
        )
        result = OrchestrationResult(
            question="Which states had the highest total population in 2024?",
            parse_result=ParseResult(plan=plan),
            query_plan=plan,
        )
        result.chart_selection = type(
            "ChartSelectionStub",
            (),
            {"chart_type": "bar"},
        )()
        result.response = type(
            "ResponseStub",
            (),
            {"answer_text": "California ranks highest."},
        )()
        result.rendered_query = type(
            "RenderedQueryStub",
            (),
            {"sql": "SELECT * FROM foo"},
        )()
        result.dataframe = [1, 2, 3]
        mock_run_question.return_value = TimedOrchestrationResult(
            result=result,
            timings_ms={"parse": 100.0, "total": 250.0},
        )

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = main(
                [
                    "Which states had the highest total population in 2024?",
                ]
            )

        self.assertEqual(exit_code, 0)
        output = buffer.getvalue()
        self.assertIn("Answer", output)
        self.assertIn("California ranks highest.", output)
        self.assertIn("Chart type: bar", output)
        self.assertIn("SELECT * FROM foo", output)

    @patch("app.scripts.ask.parse_only")
    def test_force_provider_flag_is_forwarded(self, mock_parse_only) -> None:
        mock_parse_only.return_value = TimedParseResult(
            result=ParseResult(
                plan=QueryPlan(
                    question_type="ranking",
                    metric_id="pop_total",
                    geo_level="state",
                    year=2024,
                )
            ),
            timings_ms={"parse": 1.0},
        )

        with redirect_stdout(io.StringIO()):
            exit_code = main(
                [
                    "Rank states by population in 2024.",
                    "--parser-only",
                    "--force-provider",
                ]
            )

        self.assertEqual(exit_code, 0)
        self.assertTrue(mock_parse_only.called)
        self.assertTrue(mock_parse_only.call_args.kwargs["force_provider"])

    def test_append_model_test_log_writes_parser_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "model_test.md"
            path.write_text("# Test Log\n", encoding="utf-8")
            timed_result = TimedParseResult(
                result=ParseResult(
                    plan=QueryPlan(
                        question_type="ranking",
                        metric_id="pop_total",
                        geo_level="state",
                        year=2024,
                    ),
                    provider_used="OllamaProvider",
                ),
                timings_ms={"parse": 12.5},
            )

            append_model_test_log(
                question="Rank states by population in 2024.",
                command="python -m app.scripts.ask ...",
                parser_only=True,
                timed_parse_result=timed_result,
                path=path,
            )

            content = path.read_text(encoding="utf-8")
            self.assertIn("### Run", content)
            self.assertIn("provider_used: OllamaProvider", content)
            self.assertIn("Result: parsed", content)

    @patch("app.scripts.ask.run_question")
    def test_log_model_test_flag_appends_entry(self, mock_run_question) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "model_test.md"
            path.write_text("# Test Log\n", encoding="utf-8")
            plan = QueryPlan(
                question_type="ranking",
                metric_id="pop_total",
                geo_level="state",
                year=2024,
            )
            result = OrchestrationResult(
                question="Which states had the highest total population in 2024?",
                parse_result=ParseResult(plan=plan),
                query_plan=plan,
            )
            result.chart_selection = type("ChartSelectionStub", (), {"chart_type": "bar"})()
            result.response = type("ResponseStub", (), {"answer_text": "California ranks highest."})()
            result.rendered_query = type("RenderedQueryStub", (), {"sql": "SELECT * FROM foo"})()
            result.dataframe = [1, 2, 3]
            mock_run_question.return_value = TimedOrchestrationResult(
                result=result,
                timings_ms={"parse": 10.0, "total": 20.0},
            )

            with patch("app.scripts.ask.MODEL_TEST_LOG_PATH", path):
                with redirect_stdout(io.StringIO()):
                    exit_code = main(
                        [
                            "Which states had the highest total population in 2024?",
                            "--log-model-test",
                        ]
                    )

            self.assertEqual(exit_code, 0)
            content = path.read_text(encoding="utf-8")
            self.assertIn("Question: Which states had the highest total population in 2024?", content)
            self.assertIn("chart_type: bar", content)

    def test_save_run_artifacts_writes_expected_files(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            plan = QueryPlan(
                question_type="ranking",
                metric_id="pop_total",
                geo_level="state",
                year=2024,
            )
            chart_source = Path(tempdir) / "source_chart.png"
            chart_source.write_bytes(b"png")

            result = OrchestrationResult(
                question="Which states had the highest total population in 2024?",
                parse_result=ParseResult(plan=plan),
                query_plan=plan,
            )
            result.rendered_chart = type(
                "RenderedChartStub",
                (),
                {"output_path": str(chart_source)},
            )()
            result.rendered_query = type(
                "RenderedQueryStub",
                (),
                {"sql": "SELECT * FROM foo"},
            )()
            result.response = type(
                "ResponseStub",
                (),
                {"answer_text": "California ranks highest."},
            )()

            try:
                import pandas as pd
            except ImportError:  # pragma: no cover
                self.skipTest("pandas is not installed")
            result.dataframe = pd.DataFrame(
                [{"geo_name": "California", "metric_value": 1, "metric_label": "Population"}]
            )

            output_dir = Path(tempdir) / "saved_run"
            artifact_paths = save_run_artifacts(result, output_dir)

            self.assertTrue((output_dir / "chart.png").exists())
            self.assertTrue((output_dir / "query_plan.json").exists())
            self.assertTrue((output_dir / "result.sql").exists())
            self.assertTrue((output_dir / "result.csv").exists())
            self.assertTrue((output_dir / "answer.txt").exists())
            self.assertEqual(artifact_paths["chart_path"], str(output_dir / "chart.png"))

    def test_save_run_artifacts_writes_clarification_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            result = OrchestrationResult(
                question="Benchmark Florida population against the United States in 2024.",
                parse_result=ParseResult(
                    clarification=ClarificationRequest(
                        message="Need benchmark details.",
                        missing_fields=["benchmark_type"],
                        partial_plan={"question_type": "benchmark"},
                    ),
                    provider_used="GroqProvider",
                ),
            )

            output_dir = Path(tempdir) / "clarification_run"
            artifact_paths = save_run_artifacts(result, output_dir)

            self.assertTrue((output_dir / "clarification.json").exists())
            self.assertEqual(
                artifact_paths["clarification_path"],
                str(output_dir / "clarification.json"),
            )

    @patch("app.scripts.ask.run_question")
    def test_output_dir_flag_saves_artifacts(self, mock_run_question) -> None:
        with tempfile.TemporaryDirectory(dir=".") as tempdir:
            plan = QueryPlan(
                question_type="ranking",
                metric_id="pop_total",
                geo_level="state",
                year=2024,
            )
            chart_source = Path(tempdir) / "source_chart.png"
            chart_source.write_bytes(b"png")

            result = OrchestrationResult(
                question="Which states had the highest total population in 2024?",
                parse_result=ParseResult(plan=plan),
                query_plan=plan,
            )
            result.rendered_chart = type(
                "RenderedChartStub",
                (),
                {"output_path": str(chart_source)},
            )()
            result.rendered_query = type(
                "RenderedQueryStub",
                (),
                {"sql": "SELECT * FROM foo"},
            )()
            result.response = type(
                "ResponseStub",
                (),
                {"answer_text": "California ranks highest."},
            )()

            try:
                import pandas as pd
            except ImportError:  # pragma: no cover
                self.skipTest("pandas is not installed")
            result.dataframe = pd.DataFrame(
                [{"geo_name": "California", "metric_value": 1, "metric_label": "Population"}]
            )

            mock_run_question.return_value = TimedOrchestrationResult(
                result=result,
                timings_ms={"parse": 10.0, "total": 20.0},
            )

            output_dir = Path("tmp_cli_artifacts")
            try:
                with redirect_stdout(io.StringIO()):
                    exit_code = main(
                        [
                            "Which states had the highest total population in 2024?",
                            "--output-dir",
                            str(output_dir),
                        ]
                    )

                self.assertEqual(exit_code, 0)
                self.assertTrue((output_dir / "query_plan.json").exists())
                self.assertTrue((output_dir / "result.sql").exists())
                self.assertTrue((output_dir / "result.csv").exists())
                self.assertTrue((output_dir / "answer.txt").exists())
                self.assertTrue((output_dir / "chart.png").exists())
            finally:
                if output_dir.exists():
                    for child in output_dir.iterdir():
                        child.unlink()
                    output_dir.rmdir()


if __name__ == "__main__":
    unittest.main()
