from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from frontend.qa_utils import build_summary_frame, load_run_bundle, load_run_collections


class QaUtilsTests(unittest.TestCase):
    def test_load_run_bundle_reads_saved_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            run_dir = Path(tempdir) / "sample_run"
            run_dir.mkdir()
            (run_dir / "query_plan.json").write_text(
                '{"question_type":"ranking","metric_id":"pop_total","geo_level":"state","template_id":"ranking"}',
                encoding="utf-8",
            )
            (run_dir / "result.sql").write_text("SELECT 1", encoding="utf-8")
            (run_dir / "answer.txt").write_text("California ranks highest.", encoding="utf-8")
            (run_dir / "result.csv").write_text("geo_name,metric_value\nCalifornia,1\n", encoding="utf-8")
            (run_dir / "chart.png").write_bytes(b"png")

            bundle = load_run_bundle(run_dir, collection="provider_qa")

            self.assertIsNotNone(bundle)
            assert bundle is not None
            self.assertEqual(bundle.collection, "provider_qa")
            self.assertEqual(bundle.question_type, "ranking")
            self.assertEqual(bundle.metric_id, "pop_total")
            self.assertEqual(bundle.row_count, 1)
            self.assertTrue(bundle.has_chart)

    def test_load_run_collections_and_summary_frame(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir) / "provider_qa"
            run_dir = root / "groq_case"
            run_dir.mkdir(parents=True)
            (run_dir / "query_plan.json").write_text(
                '{"question_type":"trend","metric_id":"pop_total","geo_level":"cbsa","template_id":"trend"}',
                encoding="utf-8",
            )
            (run_dir / "result.csv").write_text("period,metric_value\n2024,1\n", encoding="utf-8")

            bundles = load_run_collections([root])
            summary = build_summary_frame(bundles)

            self.assertEqual(len(bundles), 1)
            self.assertEqual(summary.iloc[0]["collection"], "provider_qa")
            self.assertEqual(summary.iloc[0]["question_type"], "trend")

    def test_load_run_bundle_reads_clarification_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            run_dir = Path(tempdir) / "clarification_case"
            run_dir.mkdir()
            (run_dir / "clarification.json").write_text(
                '{"clarification":{"message":"Need benchmark details.","missing_fields":["benchmark_type"],"partial_plan":{"question_type":"benchmark","target_geo_level":"state"}}}',
                encoding="utf-8",
            )

            bundle = load_run_bundle(run_dir, collection="provider_qa")

            self.assertIsNotNone(bundle)
            assert bundle is not None
            self.assertTrue(bundle.needs_clarification)
            self.assertEqual(bundle.question_type, "benchmark")
            self.assertEqual(bundle.missing_fields, ["benchmark_type"])


if __name__ == "__main__":
    unittest.main()
