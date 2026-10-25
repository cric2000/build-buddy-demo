import json
from pathlib import Path
import tempfile
import unittest
from scripts.demo import TestRun, result_status


class DemoTests(unittest.TestCase):
    def test_missing_report_is_unknown(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(result_status(Path(directory) / "missing.json", 0), ("unknown", None))

    def test_untrusted_or_inconsistent_reports_are_unknown(self):
        invalid = ["invalid json", "[]", "{}", json.dumps({"tests_run": 0, "failed_tests": 0, "exit_code": 0}),
                   json.dumps({"tests_run": 12, "failed_tests": 2, "exit_code": 0}),
                   json.dumps({"tests_run": 12, "failed_tests": 0, "exit_code": 1}),
                   json.dumps({"tests_run": True, "failed_tests": 0, "exit_code": 0}),
                   json.dumps({"tests_run": 12, "failed_tests": 13, "exit_code": 1})]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            for content in invalid:
                with self.subTest(content=content):
                    path.write_text(content)
                    self.assertEqual(result_status(path, 0), ("unknown", None))

    def test_process_exit_and_report_must_agree(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            path.write_text(json.dumps({"tests_run": 12, "failed_tests": 0, "exit_code": 0}))
            self.assertEqual(result_status(path, 1), ("unknown", None))

    def test_real_worker_moves_from_queued_to_running_to_passing(self):
        with tempfile.TemporaryDirectory() as directory:
            run = TestRun(directory)
            try:
                self.assertEqual(run.status(), ("queued", None))
                run.start()
                self.assertEqual(run.status(), ("running", None))
                self.assertEqual(run.finish(), 0)
                state, report = run.status()
                self.assertEqual(state, "passing")
                self.assertEqual(report["tests_run"], 12)
                self.assertEqual(report["failed_tests"], 0)
            finally:
                run.close()

    def test_real_regression_produces_failing_tests(self):
        with tempfile.TemporaryDirectory() as directory:
            run = TestRun(directory, broken=True)
            try:
                run.start()
                self.assertEqual(run.finish(), 1)
                state, report = run.status()
                self.assertEqual(state, "failing")
                self.assertEqual(report["tests_run"], 12)
                self.assertEqual(report["failed_tests"], 2)
            finally:
                run.close()
