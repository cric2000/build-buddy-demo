from pathlib import Path
import unittest
from scripts.update_readme import update_readme


class ReadmePublicationTests(unittest.TestCase):
    def test_failure_then_pass_changes_image_url_and_visible_test_count(self):
        template = Path(__file__).resolve().parents[1].joinpath("README.md").read_text()
        failure = {"selected_status": "failing", "snapshots": {"failing": {"test_report": {"tests_run": 12, "failed_tests": 2}}}}
        passing = {"selected_status": "passing", "snapshots": {"passing": {"test_report": {"tests_run": 12, "failed_tests": 0}}}}
        old = update_readme(template, "a" * 40, "owner/demo", 123, "c" * 40, failure)
        new = update_readme(old, "b" * 40, "owner/demo", 124, "c" * 40, passing)
        self.assertIn("**Passing · 12 tests · 0 failures**", new)
        self.assertNotIn("**Failing · 12 tests · 2 failures**", new)
        self.assertNotIn("/" + "a" * 40 + "/", new)
        self.assertEqual(new.count("https://raw.githubusercontent.com/owner/demo/" + "b" * 40), 6)
        self.assertIn("/actions/runs/124", new)
        self.assertEqual(new.split("<!-- buildbuddy:latest:start -->")[0], template.split("<!-- buildbuddy:latest:start -->")[0])

    def test_unavailable_state_does_not_invent_test_counts(self):
        template = "<!-- buildbuddy:latest:start --><!-- buildbuddy:latest:end -->\n<!-- buildbuddy:gallery:start --><!-- buildbuddy:gallery:end -->"
        summary = {"selected_status": "unknown", "snapshots": {"unknown": {"test_report": None}}}
        text = update_readme(template, "a" * 40, "owner/demo", 123, "b" * 40, summary)
        self.assertIn("**Unknown**", text)
        self.assertNotIn("0 failures", text)

    def test_missing_markers_fail_without_replacing_unrelated_readme_text(self):
        with self.assertRaises(ValueError):
            update_readme("Handwritten README", "a" * 40, "owner/demo", 123, "b" * 40,
                          {"selected_status": "unknown", "snapshots": {"unknown": {"test_report": None}}})
