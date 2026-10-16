"""Integration tests for the file-backed, subprocess-based Ralph controller."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from src.ralph_loop import Config, demo, read_items, run_loop


class RalphLoopTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.workspace = self.base / "workspace"
        self.workspace.mkdir()
        (self.workspace / "tasks").mkdir()
        self.state = self.workspace / "tasks/state.json"
        self.state.write_text(json.dumps({"schema_version": 1, "items": [
            {"id": "a", "status": "pending"}, {"id": "b", "status": "pending"},
        ]}), encoding="utf-8")
        self.prompt = self.base / "prompt.md"
        self.prompt.write_text("One item only\n", encoding="utf-8")
        self.scope = self.base / "scope.sh"
        self.scope.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        self.final = self.base / "final.sh"
        self.final.write_text("#!/bin/sh\ntest -f result.txt && test \"$(cat result.txt)\" = a,b\n", encoding="utf-8")
        self.scope.chmod(0o700)
        self.final.chmod(0o700)
        self.worker = self.base / "worker.py"
        self.worker.write_text("""import json, pathlib, sys
mode = sys.argv[1]
prompt = sys.stdin.read()
assert prompt == 'One item only\\n'
p = pathlib.Path('tasks/state.json')
d = json.loads(p.read_text())
if mode == 'claim':
    d['status'] = 'complete'
    print('<promise>COMPLETE</promise>')
elif mode == 'two':
    for item in d['items']: item['status'] = 'done'
elif mode == 'mutate':
    pathlib.Path(sys.argv[2]).write_text('#!/bin/sh\\nexit 0\\n')
elif mode == 'one':
    for item in d['items']:
        if item['status'] == 'pending':
            item['status'] = 'done'
            out = pathlib.Path('result.txt')
            out.write_text((out.read_text() + ',' if out.exists() else '') + item['id'])
            break
p.write_text(json.dumps(d))
if mode == 'fail_after_one':
    d['items'][0]['status'] = 'done'
    p.write_text(json.dumps(d))
    sys.exit(1)
""", encoding="utf-8")

    def config(self, mode: str, *extra: str, iterations: int = 3) -> Config:
        return Config(self.workspace, self.prompt, self.state,
                      (sys.executable, str(self.worker), mode, *extra),
                      self.scope, self.final, iterations, 3)

    def test_demo_uses_two_fresh_workers(self) -> None:
        self.assertEqual(demo(), 0)

    def test_real_subprocess_completes_one_item_each_iteration(self) -> None:
        self.assertEqual(run_loop(self.config("one")), 0)
        self.assertEqual(read_items(self.state), (("a", "done"), ("b", "done")))
        self.assertEqual((self.workspace / "result.txt").read_text(), "a,b")

    def test_cli_accepts_external_worker_and_verifiers(self) -> None:
        script = Path(__file__).resolve().parents[1] / "src/ralph_loop.py"
        result = subprocess.run([
            sys.executable, str(script), "--workspace", str(self.workspace),
            "--prompt", str(self.prompt), "--state", str(self.state),
            "--worker", sys.executable, "--worker-arg", str(self.worker),
            "--worker-arg", "one", "--scope-verifier", str(self.scope),
            "--final-verifier", str(self.final), "--max-iterations", "3",
            "--timeout", "3",
        ], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("COMPLETE", result.stdout)

    def test_prose_claim_does_not_count_as_completion(self) -> None:
        self.assertEqual(run_loop(self.config("claim", iterations=2)), 1)
        self.assertEqual(read_items(self.state)[0][1], "pending")

    def test_two_items_in_one_iteration_rejected(self) -> None:
        self.assertEqual(run_loop(self.config("two")), 3)

    def test_failed_worker_cannot_claim_item(self) -> None:
        self.assertEqual(run_loop(self.config("fail_after_one")), 3)

    def test_protected_verifier_change_rejected(self) -> None:
        self.assertEqual(run_loop(self.config("mutate", str(self.final))), 3)

    def test_false_final_evidence_not_accepted(self) -> None:
        self.final.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        self.assertEqual(run_loop(self.config("one", iterations=2)), 1)

    def test_invalid_state_rejected(self) -> None:
        self.state.write_text('{"schema_version": 1, "items": []}', encoding="utf-8")
        self.assertEqual(run_loop(self.config("one")), 2)

    def test_verifier_inside_worker_workspace_rejected(self) -> None:
        unsafe_verifier = self.workspace / "scope.sh"
        unsafe_verifier.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        unsafe_verifier.chmod(0o700)
        config = self.config("one")
        self.assertEqual(run_loop(Config(config.workspace, config.prompt, config.state,
                                         config.worker, unsafe_verifier, config.final_verifier)), 2)


if __name__ == "__main__":
    unittest.main()
