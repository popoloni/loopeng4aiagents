"""Executable fixture contracts, negative controls, and authority boundaries."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from loopeng.cases import chapter6 as ex


class SQLTests(unittest.TestCase):
    def test_independent_checker_rejects_overfit_and_missing_checks(self):
        results = ex.checker_example()["results"]
        self.assertTrue(results["known_good"]["accepted"])
        self.assertEqual(results["hardcoded_visible_answer"]["checks_passed"], 1)
        for name in ("hardcoded_visible_answer", "known_bad", "missing_checks"):
            self.assertFalse(results[name]["accepted"])

    def test_schema_failure_drives_repair(self):
        result = ex.sql_example()
        self.assertEqual(result["state"], "verified")
        history = result["result"]["history"]
        self.assertEqual([entry["passed"] for entry in history], [False, True])
        self.assertEqual(result["feedback_received"][1], history[0]["evidence"])
        self.assertEqual(history[1]["evidence"]["actual"], [("Ada", 2000), ("Cy", 600)])

    def test_verifier_rejects_wrong_results_and_side_effects(self):
        spec = ex.fixtures()["sql"]
        for query in (
            "SELECT customer, SUM(cents) FROM orders GROUP BY customer",
            "SELECT 'Ada', 2000",  # plausible partial answer
            "SELECT 'Ada', 2000 UNION ALL SELECT 'Ada', 2000 UNION ALL SELECT 'Cy', 600",
            "DELETE FROM orders", "DROP TABLE orders", "PRAGMA table_info(orders)",
            "ATTACH DATABASE '/tmp/forbidden.db' AS other", "SELECT load_extension('x')",
            "nonsense", "SELECT 1; SELECT 2",
        ):
            with self.subTest(query=query):
                self.assertFalse(ex.verify_sql(query, spec)[0])
        self.assertTrue(ex.verify_sql(spec["candidate"], spec)[0])

    def test_oracle_changes_with_data_not_candidate(self):
        spec = ex.fixtures()["sql"]
        spec["rows"].append([7, "Ben", "paid", 100])
        passed, evidence = ex.verify_sql(spec["candidate"], spec)
        self.assertTrue(passed)
        self.assertIn(("Ben", 600), evidence["actual"])
        self.assertFalse(ex.verify_sql("SELECT 'Ada', 2000 UNION ALL SELECT 'Cy', 600", spec)[0])

    def test_sql_execution_budget_rejects_cross_product(self):
        query = "SELECT count(*) FROM orders a, orders b, orders c, orders d, orders e, orders f, orders g"
        passed, evidence = ex.verify_sql(query, ex.fixtures()["sql"])
        self.assertFalse(passed)
        self.assertEqual(evidence["gate"], "sql_execution")

    def test_orchestra_rechecks_highest_ranked_wrong_candidate(self):
        result = ex.orchestration_example()
        self.assertEqual(result["state"], "verified")
        self.assertEqual(result["calls"], ["refinement", "refinement", "fallback", "fallback"])
        self.assertEqual([entry["passed"] for entry in result["history"]], [False, False, False, True])
        self.assertEqual(ex.orchestration_example(all_wrong=True)["state"], "escalated")
        limited = ex.orchestration_example(budget=2)
        self.assertEqual(limited["reason"], "candidate_budget_exhausted")
        self.assertEqual(limited["calls"], ["refinement", "refinement"])


class GroundingTests(unittest.TestCase):
    def test_memory_filters_before_ranking_and_abstains(self):
        records = ex.fixtures()["memory"]
        hits = ex.retrieve_policy("Payments incident retry policy", records)
        self.assertEqual([hit["metadata"]["source"] for hit in hits], ["incident/42"])
        self.assertEqual(ex.retrieve_policy("gardening harvest", records), [])
        self.assertEqual(ex.retrieve_policy("Payments", records, max_age_days=0), [])
        self.assertEqual(ex.retrieve_policy("Payments", records, min_similarity=1), [])
        records[0]["age_days"] = -1
        self.assertEqual(ex.retrieve_policy("Payments", records), [])

    def test_exact_tool_reconciles_records(self):
        result = ex.data_example()
        self.assertFalse(result["baseline_accepted"])
        self.assertEqual(result["answer"], {"EUR": 2000, "USD": 500})
        self.assertEqual(result["observation"]["payment_ids"], ["p1", "p2", "p4"])
        csv_text = "payment_id,status,currency,cents\nx,settled,EUR,17\ny,pending,EUR,8\n"
        self.assertEqual(ex.reconcile_payments(csv_text)["settled_cents"], {"EUR": 17})

    def test_tool_fails_closed_on_duplicate_or_malformed_exports(self):
        header = "payment_id,status,currency,cents\n"
        for body in ("", "x,settled,EUR,1\nx,settled,EUR,1\n", "x,settled,EUR,1.5\n",
                     "x,settled,EUR,-1\n", "x,unknown,EUR,1\n", "x,settled,XYZ,1\n"):
            with self.subTest(body=body), self.assertRaises(ValueError):
                ex.reconcile_payments(header + body)


class MaintenanceTests(unittest.TestCase):
    def test_queues_remain_proposals(self):
        report = ex.maintenance_example()
        self.assertEqual({item["id"] for item in report["triage"]}, {"BUG-1", "BUG-2"})
        self.assertTrue(all(item["decision"] == "human_review" for item in report["triage"]))
        self.assertEqual(report["duplicates"][0]["id"], "BUG-2")
        self.assertEqual(len(report["cleanup"]["queue"]), 1)
        self.assertIn("c1", report["changelog"]["draft"])
        self.assertIn("c2", report["changelog"]["draft"])
        self.assertNotIn("c3", report["changelog"]["draft"])
        self.assertEqual(report["external_actions"], [])

    def test_ci_repairs_only_verified_product_regression(self):
        result = ex.ci_case("regression")
        self.assertEqual(result["repair_calls"], ["normalize_trailing_slash"])
        self.assertTrue(result["patch"]["verified"])
        self.assertEqual(len(result["patch"]["checks"]), 3)
        for kind in ("flake", "environment", "dependency", "policy", "unknown"):
            with self.subTest(kind=kind):
                result = ex.ci_case(kind)
                self.assertEqual(result["repair_calls"], [])
                self.assertEqual(len(result["observations"]), 5)
        self.assertEqual(ex.ci_case("flake")["diagnosis"], "flake")

    def test_green_dependencies_still_need_risk_and_permission(self):
        updates = ex.fixtures()["updates"]
        self.assertEqual(ex.dependency_decision(updates[0])["state"], "eligible_proposal")
        self.assertEqual(ex.dependency_decision(updates[1])["state"], "human_review")
        self.assertEqual(ex.dependency_decision(updates[2])["state"], "human_review")
        for field in ("green", "authorized", "reversible", "provenance_verified", "license_approved"):
            update = {**updates[0], field: False}
            self.assertEqual(ex.dependency_decision(update)["state"], "human_review")

    def test_pr_rejects_stale_missing_and_red_evidence(self):
        good, bad = ex.fixtures()["prs"]
        self.assertTrue(ex.verify_pr(good)[0])
        self.assertFalse(ex.verify_pr(bad)[0])
        for field in ("head", "required", "review", "checks"):
            candidate = deepcopy(good)
            del candidate[field]
            self.assertFalse(ex.verify_pr(candidate)[0])
        stale = deepcopy(good)
        stale["review"]["head"] = "old"
        self.assertFalse(ex.verify_pr(stale)[0])

    def test_coordination_owns_logical_target_once(self):
        result = ex.coordination_example()
        self.assertEqual(result["owned_by"]["PR-42"], "pr")
        self.assertEqual(len(result["yielded"]), 2)
        self.assertEqual(len({target for _, target in result["actions"]}), len(result["actions"]))


class SupportTests(unittest.TestCase):
    def test_manuscript_timeline_repair_then_zero_authority_handoff(self):
        state = ex.support_example()
        self.assertEqual(state["state"], "escalated")
        self.assertEqual(state["handoff"]["reason"], "financial_authority_zero")
        self.assertTrue(state["handoff"]["accepted"])
        self.assertEqual([step["verification"]["passed"] for step in state["attempts"]], [False, True])
        self.assertEqual(state["recommendation"]["cents"], 2900)
        self.assertEqual(state["recommendation"]["policy_source"], "refund-policy/v3")
        self.assertEqual(state["external_actions"], [])
        self.assertNotIn("confirms", state["response"])

    def test_handoff_requires_acceptance(self):
        state = ex.support_example(queue_accepts=False)
        self.assertEqual(state["state"], "handoff_pending")
        self.assertIsNone(state["handoff"]["receipt"])

    def test_mandatory_escalation_and_no_identity_disclosure(self):
        for scenario, reason in (("identity", "identity_unresolved"), ("human", "human_requested"),
                                 ("fraud", "suspected_fraud"), ("policy", "policy_not_current_and_approved")):
            with self.subTest(scenario=scenario):
                state = ex.support_example(scenario)
                self.assertEqual(state["handoff"]["reason"], reason)
                self.assertEqual(state["attempts"], [])
        self.assertEqual(ex.support_example("identity")["evidence"], {})

    def test_policy_eligibility_is_computed_from_timestamps(self):
        record = ex.fixtures()["support"]
        record["cancellation"] = "2026-10-03T08:42:00+00:00"
        state = ex.support_example(ticket=record)
        self.assertEqual(state["handoff"]["reason"], "refund_requires_policy_exception")
        self.assertNotIn("recommendation", state)

    def test_support_fails_closed_outside_contract_and_parses_timezones(self):
        record = ex.fixtures()["support"]
        record["request"] = "delete_account"
        self.assertEqual(ex.support_example(ticket=record)["handoff"]["reason"],
                         "request_outside_refund_contract")
        record = ex.fixtures()["support"]
        record["policy"]["approved"] = "yes"
        self.assertEqual(ex.support_example(ticket=record)["attempts"], [])
        record = ex.fixtures()["support"]
        record["renewal"] = "2026-10-01T10:15:00+02:00"
        state = ex.support_example(ticket=record)
        self.assertEqual(state["attempts"][-1]["claim"], "after")
        self.assertEqual(state["handoff"]["reason"], "financial_authority_zero")
        record["cancellation"] = record["renewal"]
        self.assertEqual(ex.support_example(ticket=record)["attempts"][-1]["claim"], "same_time")

    def test_repeated_failure_stops_and_tool_budget_is_separate(self):
        repeated = ex.support_example("repeat_failure")
        self.assertEqual(repeated["handoff"]["reason"], "repeated_failure_without_new_evidence")
        self.assertEqual(len(repeated["attempts"]), 2)
        resumed = ex.support_example("tool_timeout")
        self.assertEqual(resumed["tool_resumptions"], 1)
        self.assertEqual(resumed["reasoning_retries"], 1)
        self.assertEqual(resumed["evidence"]["account"], "acct-42")
        exhausted = ex.support_example("tool_exhausted")
        self.assertEqual(exhausted["tool_resumptions"], 3)
        self.assertEqual(exhausted["reasoning_retries"], 0)
        self.assertEqual(exhausted["handoff"]["reason"], "tool_resumption_budget_exhausted")

    def test_approval_is_not_confirmation_and_receipt_must_match(self):
        self.assertEqual(ex.support_example("unconfirmed")["state"], "awaiting_confirmation")
        state = ex.support_example("approved")
        self.assertEqual(state["state"], "resolved")
        self.assertEqual(state["external_actions"], [])
        for field, value in (("confirmed", False), ("charge", "another-charge"),
                             ("cents", 1), ("source", "maker-claim")):
            receipt = {**state["confirmation"], field: value}
            self.assertFalse(ex.verify_refund_receipt(state["recommendation"], state["human_approval"], receipt))
        self.assertFalse(ex.verify_refund_receipt(state["recommendation"], {}, state["confirmation"]))


class EntryPointTests(unittest.TestCase):
    def test_default_cases_are_deterministic_and_never_call_external_adapters(self):
        with patch("socket.socket", side_effect=AssertionError("network forbidden")), \
             patch("subprocess.run", side_effect=AssertionError("subprocess forbidden")):
            for name, run in ex.CASES.items():
                with self.subTest(case=name):
                    self.assertEqual(run(), run())

    def test_module_and_script_entrypoints(self):
        root = Path(__file__).resolve().parents[1]
        for entry in (["-m", "loopeng", "cases"], [str(root / "loopeng/__main__.py"), "cases"]):
            result = subprocess.run([sys.executable, *entry, "--case", "all"], cwd=root,
                                    text=True, capture_output=True, check=True, timeout=10)
            report = json.loads(result.stdout)
            self.assertFalse(report["real_external_side_effects"])
            self.assertEqual(set(report["cases"]), set(ex.CASES))


if __name__ == "__main__":
    unittest.main()
