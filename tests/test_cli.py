"""Canonical entry points and protected-source regressions."""
from importlib import import_module
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from loopeng.__main__ import COMMANDS, main
from loopeng.runtime import live

ROOT = Path(__file__).resolve().parents[1]


class CommandTests(unittest.TestCase):
    def run_cli(self, args, cwd=ROOT):
        return subprocess.run([sys.executable, "-B", *args], cwd=cwd,
                              text=True, capture_output=True, timeout=20)

    def test_dispatch_forwards_arguments_and_exit_status(self):
        for command, module in COMMANDS.items():
            with self.subTest(command=command), patch.object(import_module(module), "main", return_value=7) as entry:
                self.assertEqual(main([command, "--example", "value with spaces"]), 7)
                entry.assert_called_once_with(["--example", "value with spaces"])

    def test_top_level_help_and_unknown_command(self):
        help_result = self.run_cli(["-m", "loopeng", "--help"])
        self.assertEqual(help_result.returncode, 0, help_result.stderr)
        for command in COMMANDS:
            self.assertIn(command, help_result.stdout)
        unknown = self.run_cli(["-m", "loopeng", "unknown"])
        self.assertEqual(unknown.returncode, 2)

    def test_all_commands_offer_help_from_external_directory(self):
        with tempfile.TemporaryDirectory() as outside:
            for command in COMMANDS:
                with self.subTest(command=command):
                    canonical = self.run_cli(["-m", "loopeng", command, "--help"])
                    old = self.run_cli([str(ROOT / "loopeng/__main__.py"), command, "--help"], outside)
                    self.assertEqual(canonical.returncode, 0, canonical.stderr)
                    self.assertEqual(old.returncode, 0, old.stderr)
                    self.assertIn("usage:", canonical.stdout)
                    self.assertIn("usage:", old.stdout)

    def test_offline_ralph_launchers_work_from_other_directory(self):
        with tempfile.TemporaryDirectory() as outside:
            for launcher in ("scripts/ralph",):
                with self.subTest(launcher=launcher):
                    result = subprocess.run(["bash", str(ROOT / launcher), "--demo"], cwd=outside,
                                            env={**os.environ, "PYTHON_BIN": sys.executable},
                                            capture_output=True, text=True, timeout=20)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn("COMPLETE", result.stdout)

    def test_live_controller_hashes_relocated_code_and_entry_points(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp).resolve() / "run"
            with patch.object(live, "local_image", return_value="sha256:" + "a" * 64), \
                 patch.object(live, "controls"), patch.object(live, "run_loop", return_value=0) as run:
                self.assertEqual(live.demo(output, "endpoint", "model", ["docker"], "image", True), 0)
            config = json.loads((output / "controller/config.json").read_text())
            protected = config["protected"]
            for path in (ROOT / "loopeng").rglob("*.py"):
                self.assertEqual(protected[str(path)], live.sha256(path))
            worker = run.call_args.args[0].worker
            self.assertTrue(Path(worker[2]).is_file())
            wrapper = (output / "controller/verify_scope.sh").read_text()
            self.assertIn(str(ROOT / "loopeng/__main__.py"), wrapper)
            scope = subprocess.run([str(output / "controller/verify_scope.sh")],
                                   cwd=output / "workspace", capture_output=True, text=True, timeout=20)
            self.assertEqual(scope.returncode, 0, scope.stderr)


if __name__ == "__main__":
    unittest.main()
