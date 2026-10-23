"""The repository gate must expose broken navigation and failed executions."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from scripts import check


class RepositoryCheckTests(unittest.TestCase):
    def test_duplicate_content_is_detected_without_empty_package_markers(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "a.md").write_text("same", encoding="utf-8")
            (root / "b.md").write_text("same", encoding="utf-8")
            (root / "empty.md").write_text("", encoding="utf-8")
            self.assertEqual(check.check_duplicates(root), [["a.md", "b.md"]])

    def test_links_find_missing_but_ignore_urls_anchors_and_fences(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docs").mkdir()
            (root / "docs/a file.md").write_text("# Target", encoding="utf-8")
            (root / "README.md").write_text(
                '[ok](docs/a%20file.md#target) [also](<docs/a file.md>) '
                '[web](https://example.invalid/no.md) [anchor](#a) '
                '[bad](docs/missing.md)\n```md\n[example](missing-example.md)\n```', encoding="utf-8")
            self.assertEqual(check.check_links(root), ["README.md: missing docs/missing.md"])

    def test_html_image_target_checked(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text('<img src="missing.png">', encoding="utf-8")
            self.assertEqual(check.check_links(root), ["README.md: missing missing.png"])

    def test_command_nonzero_and_timeout_fail(self):
        for outcome in (subprocess.CompletedProcess([], 2, "", "failure"),
                        subprocess.TimeoutExpired("example", 120), OSError("missing")):
            with self.subTest(outcome=outcome):
                kw = {"side_effect": outcome} if isinstance(outcome, Exception) else {"return_value": outcome}
                with patch.object(check.subprocess, "run", **kw), patch("builtins.print"):
                    self.assertFalse(check.run_command(["example"]))

    def test_main_propagates_failure_and_runs_remaining_checks(self):
        with patch.object(check, "run_command", side_effect=[False, True]) as run, patch("builtins.print"):
            self.assertEqual(check.main(["--checks", "tests", "assets"]), 1)
            self.assertEqual(run.call_count, 2)


if __name__ == "__main__":
    unittest.main()
