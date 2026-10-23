"""Focused tests for every chapter-6 mechanism and the standalone CLI."""

from collections import Counter
from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from loopeng import engineering as le


ROOT = Path(__file__).resolve().parents[1]


class LoopMechanismTests(unittest.TestCase):
    def test_042_retry_uses_real_feedback_and_stops(self):
        seen = []

        def make(_task, feedback):
            seen.append(feedback)
            return len(seen)

        result = le.run_until_done("goal", make, lambda _t, c: (c == 2, f"got {c}"), 3)
        self.assertTrue(result["solved"])
        self.assertEqual(result["attempts"], 2)
        self.assertEqual(seen, [None, "got 1"])
        self.assertFalse(le.run_until_done("goal", lambda *_: 0, lambda *_: (False, "bad"), 2)["solved"])

    def test_043_checker_fails_closed(self):
        self.assertFalse(le.maker_checker(None, lambda _: 3, lambda _: [], lambda *_: True)["accepted"])
        result = le.maker_checker(None, lambda _: 3, lambda _: ["positive", "even"],
                                  lambda value, check: value > 0 if check == "positive" else value % 2 == 0)
        self.assertEqual((result["accepted"], result["checks_passed"]), (False, 1))

    def test_044_context_contains_schema_and_examples(self):
        prompt = le.build_context_prompt("total?", "sales(amount)",
                                         [{"schema": "sales(amount)", "question": "count?", "answer": "COUNT(*)"}])
        self.assertIn("Use only fields", prompt)
        self.assertIn("COUNT(*)", prompt)

    def test_045_memory_indexes_new_documents_and_metadata(self):
        memory = le.EmbeddingMemory()
        memory.add(["red apple"], [{"source": "a"}])
        memory.add(["blue berry"])
        self.assertEqual(memory.retrieve("apple", 1)[0]["metadata"], {"source": "a"})
        with self.assertRaises(ValueError):
            memory.add(["x"], [1, 2])

    def test_046_react_uses_tool_output(self):
        def complete(transcript):
            return "```python\nprint(2 + 3)\n```" if "TOOL OUTPUT" not in transcript else "FINAL: 5"

        self.assertEqual(le.react_solve("2+3?", complete, lambda code: "5" if "2 + 3" in code else "bad"), "5")
        with self.assertRaises(RuntimeError):
            le.react_solve("?", lambda _: "no action", lambda _: "", max_steps=1)

    def test_047_worktree_preserves_parent_until_explicit_integration(self):
        with tempfile.TemporaryDirectory() as folder:
            repo = Path(folder)

            def git(*args):
                return subprocess.run(["git", "-C", str(repo), *args], check=True,
                                      text=True, capture_output=True)

            git("init")
            git("config", "user.name", "Loop Test")
            git("config", "user.email", "loop@example.invalid")
            (repo / "base.txt").write_text("base", encoding="utf-8")
            git("add", "base.txt")
            git("commit", "-m", "base")
            branch = le.run_in_worktree(repo, "example", lambda worktree:
                                        (worktree / "new.txt").write_text("new", encoding="utf-8"))
            self.assertFalse((repo / "new.txt").exists())
            le.integrate_branch(repo, branch)
            self.assertEqual((repo / "new.txt").read_text(encoding="utf-8"), "new")
            with self.assertRaises(ValueError):
                le.run_in_worktree(repo, "../bad", lambda _: None)

    def test_048_coordination_yields_overlaps(self):
        result = le.run_coordinated([
            {"name": "low", "priority": 2, "queue": ["a", "b"]},
            {"name": "high", "priority": 1, "queue": ["a"]}])
        self.assertEqual(result["owned_by"]["a"], "high")
        self.assertEqual(len(result["yielded"]), 1)

    def test_049_budget_and_pareto(self):
        projection = le.projected_daily_tokens(60, {"noop": 0.5, "report": 0.5, "action": 0},
                                               {"noop": 10, "report": 20, "action": 100})
        self.assertEqual(projection["tokens_per_day"], 360)
        with self.assertRaises(ValueError):
            le.projected_daily_tokens(0, {"noop": 1, "report": 0, "action": 0},
                                      {"noop": 1, "report": 1, "action": 1})
        strategies = [{"tokens": 10, "quality": 0.9}, {"tokens": 20, "quality": 0.8},
                      {"tokens": 30, "quality": 1.0}]
        self.assertEqual(le.pareto_frontier(strategies), [strategies[0], strategies[2]])

    def test_050_autoact_requires_all_gates(self):
        change = {"paths": ["src/a.py"], "n_files": 1, "confidence": 0.9,
                  "verified": True, "reversible": True, "approved_scope": True}
        self.assertTrue(le.guardrail_autoact(change, ["secrets/"]))
        self.assertFalse(le.guardrail_autoact({**change, "verified": False}, []))
        self.assertFalse(le.guardrail_autoact({**change, "paths": ["secrets/key"]}, ["secrets/"]))
        self.assertFalse(le.guardrail_autoact({**change, "paths": ["../secrets/key"]}, ["secrets/"]))

    def test_051_protected_verifier_detects_mutation(self):
        with tempfile.TemporaryDirectory() as folder:
            protected = Path(folder) / "tests.txt"
            protected.write_text("fixed", encoding="utf-8")
            self.assertTrue(le.run_protected_verifier("ok", [protected], lambda _: True))

            def corrupt(_):
                protected.write_text("changed", encoding="utf-8")
                return True

            with self.assertRaises(PermissionError):
                le.run_protected_verifier("ok", [protected], corrupt)

    def test_052_triage_is_ranked_report_only(self):
        ranked = le.semantic_triage([{"id": 1, "text": "urgent outage"},
                                     {"id": 2, "text": "routine update"}], ["urgent outage"], review_limit=1)
        self.assertEqual(ranked[0]["id"], 1)
        self.assertEqual(ranked[0]["decision"], "human_review")

    def test_053_ci_sweeper_classifies_before_repair(self):
        values = iter([False, True, False, True, False])
        self.assertEqual(le.classify_ci_failure(lambda: next(values)), "flake")
        called = []
        self.assertEqual(le.ci_sweeper(lambda: True, lambda: called.append(1))["state"], "report_only")
        self.assertFalse(called)
        self.assertEqual(le.ci_sweeper(lambda: False, lambda: "patch")["patch"], "patch")

    def test_054_dependency_routing(self):
        safe = {"tier": "patch", "green": True, "severity": "low"}
        self.assertEqual(le.route_dependency_update(safe), "auto_apply")
        self.assertEqual(le.route_dependency_update({**safe, "severity": "high"}), "human_review")

    def test_055_production_patterns(self):
        vectors = [Counter({"bug": 1}), Counter({"bug": 1}), Counter({"docs": 1})]
        self.assertEqual(le.duplicate_candidates(0, vectors, 1)[0][0], 1)
        proposal = le.pr_babysitter("issue", lambda _: "fix", lambda _p, _c: False)
        self.assertEqual(proposal["proposal"], "needs_work")
        self.assertEqual(le.semantic_debt_queue(["remove old code", "new feature"],
                                                 ["old code"], top_k=1), ["remove old code"])
        notes = le.draft_changelog([{"message": "fix crash"}],
                                    lambda _: "fix", lambda commit: commit["message"])
        self.assertIn("## fix\n- fix crash", notes)

    def test_056_orchestra_fallback_still_verifies(self):
        samples = iter(["bad", "good"])
        candidate = le.capstone_orchestra("task", lambda _: "plan", lambda *_: "bad",
                                           lambda _t, c: (c == "good", "failed"),
                                           lambda *_: next(samples),
                                           lambda _t, c: 1 if c == "bad" else 0,
                                           retries=1, fallback_samples=2)
        self.assertEqual(candidate, "good")

    def test_057_contract_permissions(self):
        contract = le.LoopContract("goal", lambda _: (True, {}), 2, 10,
                                   frozenset({"report"}), "human")
        self.assertTrue(contract.permits("report"))
        self.assertFalse(contract.permits("merge"))

    def test_058_task_contract_rejects_bad_verification_default(self):
        data = {"id": "t", "trigger": "failure", "scope": {"paths": []},
                "verification": {"default": "reject"}, "budget": {"max_attempts": 1},
                "risk": {}, "on_failure": "escalate"}
        self.assertIs(le.validate_task_contract(data), data)
        with self.assertRaises(ValueError):
            le.validate_task_contract({**data, "verification": {"default": "accept"}})

    def test_059_select_controls(self):
        problem = {"independently_verifiable": True, "needs_exact_operation": True,
                   "concurrent_writers": 2, "material_side_effect": True}
        self.assertIn("tool", le.choose_controls(problem))
        self.assertIn("authorization_guardrail", le.choose_controls(problem))
        self.assertEqual(le.choose_controls({"independently_verifiable": False}),
                         ["refine_specification_or_human_review"])

    def test_060_ticket_resolves_or_hands_off(self):
        callbacks = dict(retrieve=lambda _: "evidence", draft=lambda *_: ("answer", "refund"),
                         verify=lambda *_: (True, {}), execute_action=lambda _: {"confirmed": True},
                         handoff=lambda *_: {"state": "handoff"})
        self.assertEqual(le.resolve_ticket("t", authorize=lambda *_: False, **callbacks)["state"], "handoff")
        self.assertEqual(le.resolve_ticket("t", authorize=lambda *_: True, **callbacks)["state"], "resolved")

    def test_integrated_loop_and_cli(self):
        result = le.run_code_task(le.DEMO_TASK)
        self.assertEqual((result["state"], result["attempts"], result["action"]),
                         ("verified", 2, "report_only"))
        failed = le.run_code_task({**le.DEMO_TASK, "candidates": le.DEMO_TASK["candidates"][:1]})
        self.assertEqual(failed["state"], "escalated")
        proc = subprocess.run([sys.executable, str(ROOT / "loopeng/__main__.py"), "engineering", "--demo"],
                              capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["state"], "verified")

    def test_local_model_adapter_uses_feedback_and_accounts_tokens(self):
        requests = []
        replies = ["```python\ndef add(a, b):\n    return a - b\n```",
                   "```python\ndef add(a, b):\n    return a + b\n```"]

        def fake_urlopen(request, timeout):
            requests.append(json.loads(request.data))
            body = {"choices": [{"message": {"content": replies.pop(0)}}],
                    "usage": {"prompt_tokens": 10, "completion_tokens": 5}}
            return BytesIO(json.dumps(body).encode("utf-8"))

        generator = le.VLLMGenerator("http://127.0.0.1:8000/v1/chat/completions",
                                    "local-test-model", token_budget=50)
        with patch("loopeng.engineering.urlopen", side_effect=fake_urlopen):
            result = le.run_code_task({key: value for key, value in le.DEMO_TASK.items()
                                       if key != "candidates"}, generator=generator)
        self.assertEqual(result["state"], "verified")
        self.assertEqual(generator.total_tokens, 30)
        self.assertIn("Execution feedback", requests[1]["messages"][1]["content"])

    def test_local_model_failure_escalates_without_executing_code(self):
        generator = le.VLLMGenerator("http://127.0.0.1:8000/v1/chat/completions", "local-test-model")
        with patch("loopeng.engineering.urlopen", side_effect=OSError("server unavailable")):
            result = le.run_code_task({key: value for key, value in le.DEMO_TASK.items()
                                       if key != "candidates"}, generator=generator)
        self.assertEqual(result["state"], "escalated")
        self.assertEqual(result["reason"], "generation_failed")


if __name__ == "__main__":
    unittest.main()
