"""No network or Docker daemon needed: restricted response and acceptance tests."""
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from loopeng.runtime import live as demo
from loopeng.ralph import model_worker as worker


class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.workspace = self.root / "workspace"
        (self.workspace / "tasks").mkdir(parents=True)
        self.receipts = self.root / "receipts"
        self.receipts.mkdir()
        for name in ("add.py", "multiply.py"):
            (self.workspace / name).write_bytes((demo.FIXTURE / name).read_bytes())
        (self.workspace / "tasks/state.json").write_bytes((demo.FIXTURE / "state.json").read_bytes())

    def test_plain_and_fenced_same_code(self):
        code = "def add(a, b):\n    return a + b\n"
        self.assertEqual(worker.normalize_code(code, "add"), code)
        self.assertEqual(worker.normalize_code("```python\n" + code + "```", "add"), code)

    def test_reject_host_execution_and_signature_variants(self):
        for code in ("import os\ndef add(a,b): return a+b", "def add(a,b): return eval(a)",
                     "def add(a,b=1): return a+b", "def add(a,b,*args): return a+b",
                     "def add(a,b,/,): return a+b", "def multiply(a,b): return a*b",
                     "@evil\ndef add(a,b): return a+b", "def add(a,b): return 'bad'",
                     "Here you go:\n```python\ndef add(a,b): return a+b\n```",
                     "def add(a,b): return unknown", "def add(a: x,b): return a+b"):
            with self.subTest(code=code), self.assertRaises((ValueError, SyntaxError)):
                worker.normalize_code(code, "add")

    def test_one_item_per_request(self):
        response = {"choices": [{"message": {"content": "def add(a,b): return a+b"}}]}
        with patch.object(worker, "chat", return_value=response) as chat:
            self.assertEqual(worker.work(self.workspace, self.receipts, "endpoint", "model", "prompt"), 0)
        chat.assert_called_once()
        state = json.loads((self.workspace / "tasks/state.json").read_text())
        self.assertEqual([i["status"] for i in state["items"]], ["done", "pending"])
        self.assertEqual((self.workspace / "multiply.py").read_bytes(), (demo.FIXTURE / "multiply.py").read_bytes())
        self.assertEqual(len(list(self.receipts.glob("worker-*/response.json"))), 1)

    def test_rejected_response_preserves_state_and_code(self):
        before = (self.workspace / "tasks/state.json").read_bytes()
        code = (self.workspace / "add.py").read_bytes()
        with patch.object(worker, "chat", return_value={"choices": [{"message": {"content": "import os"}}]}):
            with self.assertRaises(ValueError):
                worker.work(self.workspace, self.receipts, "endpoint", "model", "prompt")
        self.assertEqual(before, (self.workspace / "tasks/state.json").read_bytes())
        self.assertEqual(code, (self.workspace / "add.py").read_bytes())
        self.assertEqual(len(list(self.receipts.glob("worker-*/failure.json"))), 1)

    def test_scope_rejects_symlink_and_extra_file(self):
        extra = self.workspace / "extra"
        extra.write_text("extra")
        with self.assertRaises(ValueError):
            worker.check_workspace(self.workspace)
        extra.unlink()
        (self.workspace / "add.py").unlink()
        (self.workspace / "add.py").symlink_to(demo.FIXTURE / "add.py")
        with self.assertRaises(ValueError):
            worker.check_workspace(self.workspace)

    def test_no_remote_endpoint_or_redirect(self):
        for endpoint in ("https://example.com/v1/chat/completions", "http://localhost/v1/chat/completions",
                         "http://127.0.0.1/v1/chat/completions?token=secret"):
            with self.assertRaises(ValueError):
                worker.chat(endpoint, {})
        with self.assertRaises(ValueError):
            worker.NoRedirect().redirect_request(None, None, 302, "", {}, "https://example.com")

    def test_no_execution_without_opt_in(self):
        with patch.object(demo.subprocess, "run") as run:
            with self.assertRaises(ValueError):
                demo.demo(self.root / "out", "endpoint", "model", ["docker"], "image", False)
        run.assert_not_called()

    def test_docker_restrictions_and_exact_cleanup_on_timeout(self):
        with patch.object(demo.subprocess, "run", side_effect=[subprocess.TimeoutExpired("docker", 10),
                          subprocess.CompletedProcess([], 0, "", "")]) as run:
            self.assertEqual(demo.docker_check("candidate", ["docker"], "image", self.receipts)["status"], "timeout")
        command = run.call_args_list[0].args[0]
        for flag in ("--network=none", "--read-only", "--pull=never", "--cap-drop=ALL", "--user=65534:65534"):
            self.assertIn(flag, command)
        self.assertFalse(any(arg in command for arg in ("-v", "--mount", "--volume")))
        name = command[command.index("--name") + 1]
        self.assertEqual(run.call_args_list[1].args[0], ["docker", "rm", "-f", name])
        self.assertEqual(json.loads(next(self.receipts.glob("*.json")).read_text())["error_type"], "TimeoutExpired")

    def test_original_eight_assertions_unchanged(self):
        lines = (demo.FIXTURE / "assertions.py").read_text().splitlines()
        self.assertEqual([line for line in lines if line.startswith("assert ")], [
            "assert add(2, 3) == 5", "assert add(-1, 1) == 0", "assert add(0, 0) == 0",
            "assert add(10**30, 7) == 10**30 + 7", "assert multiply(2, 3) == 6",
            "assert multiply(-4, 5) == -20", "assert multiply(0, 99) == 0", "assert multiply(-7, -8) == 56"])

    def test_controls_reject_infrastructure_failures_and_require_positive_first(self):
        for status in ("backend_error", "timeout", "execution_error", "passed"):
            with self.subTest(status=status), patch.object(demo, "docker_check", side_effect=[
                    {"status": "passed"}, {"status": status}]) as check:
                with self.assertRaisesRegex(ValueError, "AssertionError"):
                    demo.controls("assert add(2,3)==5", "bad fixture", ["docker"], "image", self.receipts)
                self.assertIn("return a + b", check.call_args_list[0].args[0])
                self.assertIn("bad fixture", check.call_args_list[1].args[0])
        with patch.object(demo, "docker_check", return_value={"status": "backend_error"}) as check:
            with self.assertRaisesRegex(ValueError, "Positive"):
                demo.controls("assertions", "bad fixture", ["docker"], "image", self.receipts)
            self.assertEqual(check.call_count, 1)

    def test_actual_assertion_classification(self):
        stderr = 'Traceback (most recent call last):\n  File "<stdin>", line 4, in <module>\nAssertionError\n'
        with patch.object(demo.subprocess, "run", side_effect=[subprocess.CompletedProcess([], 1, "", stderr),
                          subprocess.CompletedProcess([], 0, "", "")]):
            self.assertEqual(demo.docker_check("candidate", ["docker"], "image", self.receipts)["status"], "assertion_failed")

    def test_chapter6_controls_block_network(self):
        with patch.object(demo, "local_image", return_value="sha256:" + "a" * 64), \
             patch.object(demo, "docker_check", return_value={"status": "backend_error"}), \
             patch.object(demo, "chat") as chat:
            with self.assertRaisesRegex(ValueError, "Positive"):
                demo.chapter6(self.root / "ch6", "endpoint", "model", ["docker"], "image", True)
        chat.assert_not_called()

    def test_chapter6_retries_with_original_checks_and_docker_only(self):
        responses = [{"choices": [{"message": {"content": content}}],
                      "usage": {"prompt_tokens": 10, "completion_tokens": 10}}
                     for content in ("def add(a,b): return a-b", "def add(a,b): return a+b")]
        checks = [{"status": "passed"}, {"status": "assertion_failed"},
                  {"status": "assertion_failed", "stderr": "AssertionError"}, {"status": "passed"}]
        with patch.object(demo, "local_image", return_value="sha256:" + "a" * 64), \
             patch.object(demo, "docker_check", side_effect=checks) as docker, \
             patch.object(demo, "chat", side_effect=responses) as chat:
            self.assertEqual(demo.chapter6(self.root / "ch6", "endpoint", "model", ["docker"], "image", True), 0)
        self.assertEqual(chat.call_count, 2)
        for call in docker.call_args_list:
            self.assertTrue(call.args[0].endswith("assert add(2, 3) == 5\nassert add(-1, 1) == 0\n"))
        self.assertIn("AssertionError", chat.call_args_list[1].args[1]["messages"][1]["content"])
        result = json.loads((self.root / "ch6/result.json").read_text())
        self.assertEqual((result["attempts"], result["tokens"]), (2, 40))


if __name__ == "__main__":
    unittest.main()
