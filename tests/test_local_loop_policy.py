import json
from pathlib import Path
import subprocess
import sys
import unittest

from loopeng.policies.local import Budget, GATE_ORDER, choose_executor, evaluate_scenario, next_transition, run_gates


class LocalPolicyTests(unittest.TestCase):
    def test_executor_precedence(self):
        task = {"file": "tokenizer.py", "context": ["tokenizer.py"]}
        self.assertEqual(choose_executor(task), "agent")
        self.assertEqual(choose_executor({**task, "mode": "direct"}, 10001), "agent")
        self.assertEqual(choose_executor({**task, "mode": "direct"}, 10000), "direct")
        self.assertEqual(choose_executor({**task, "mode": "direct", "strategy": "rewrite"}, 20000), "direct")
        self.assertEqual(choose_executor({**task, "mode": "direct", "strategy": "edit"}), "agent")
        self.assertEqual(choose_executor({**task, "strategy": "rewrite"}), "agent")

    def test_bad_inputs(self):
        for kwargs in ({"max_seconds": float("nan")}, {"max_seconds": float("inf")},
                       {"max_attempts": True}, {"max_attempts": 0}, {"retries_used": -1}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                Budget(**kwargs)
        with self.assertRaises(ValueError):
            choose_executor({"file": "x", "mode": "guess"})
        with self.assertRaises(ValueError):
            choose_executor([])
        with self.assertRaises(ValueError):
            evaluate_scenario([])

    def test_gates_fail_fast(self):
        visited = []
        def gate(name):
            visited.append(name)
            return name != "change"
        result = run_gates([(name, lambda name=name: gate(name)) for name in GATE_ORDER])
        self.assertFalse(result["verified"])
        self.assertEqual(visited, ["shell", "feature_markers", "change"])

    def test_gates_refuse_missing_or_truthy_results(self):
        with self.assertRaises(ValueError):
            run_gates([])
        checks = [(name, lambda: True) for name in GATE_ORDER]
        self.assertTrue(run_gates(checks)["verified"])
        checks[0] = ("shell", lambda: "I am done")
        self.assertFalse(run_gates(checks)["verified"])

    def test_authorization_always_halts(self):
        result = next_transition("OK", Budget(), authorized=False)
        self.assertEqual(result["action"], "halt_for_human")
        self.assertFalse(result["executed"])

    def test_retry_and_resume_are_separate(self):
        budget = Budget(attempts_used=1)
        retry = next_transition("VERIFY_FAILED", budget, usable_progress=True)
        resume = next_transition("TIMEOUT", budget, usable_progress=True)
        self.assertEqual(retry["budget"]["retries_used"], 1)
        self.assertEqual(retry["budget"]["resumes_used"], 0)
        self.assertEqual(resume["budget"]["retries_used"], 0)
        self.assertEqual(resume["budget"]["resumes_used"], 1)
        self.assertEqual(next_transition("AGENT_ERROR", budget)["action"], "retry_with_evidence")

    def test_boundary_budget_decisions(self):
        self.assertEqual(next_transition("OK", Budget(attempts_used=3))["action"], "advance")
        self.assertEqual(next_transition("VERIFY_FAILED", Budget(attempts_used=3))["action"], "escalate")
        self.assertEqual(next_transition("OK", Budget(elapsed_seconds=90))["action"], "escalate")
        self.assertEqual(next_transition("VERIFY_FAILED", Budget(retries_used=2))["action"], "escalate")
        self.assertEqual(next_transition("TIMEOUT", Budget(resumes_used=1), usable_progress=True)["action"], "escalate")

    def test_demo(self):
        root = Path(__file__).resolve().parents[1]
        proc = subprocess.run([sys.executable, "-B", str(root / "loopeng/__main__.py"), "policies", "--demo"],
                              text=True, capture_output=True, timeout=10)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        rows = json.loads(proc.stdout)
        self.assertEqual([r["transition"]["action"] for r in rows],
                         ["advance", "retry_with_evidence", "resume", "halt_for_human", "escalate"])
        self.assertTrue(all(not row["transition"]["executed"] for row in rows))


if __name__ == "__main__":
    unittest.main()
