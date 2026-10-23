#!/usr/bin/env python3
"""Chapter 6 casebook: offline fixtures, real checks, no external side effects.

All actions are reports or in-memory simulations. No network, generated Python,
Git operations, refunds, merges, issue edits, deletions, or publication are exposed.
Run from the repository root: python3 -m loopeng cases --case all
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import csv
from datetime import datetime
import io
import json
from pathlib import Path
import sqlite3

from loopeng import engineering as le

FIXTURES = Path(__file__).resolve().parents[2] / "examples" / "chapter6"


def fixtures() -> dict:
    return json.loads((FIXTURES / "fixtures.json").read_text(encoding="utf-8"))


def verify_sql(query: str, spec: dict) -> tuple[bool, dict]:
    """Execute read-only SQL against a fresh fixture; compare ordered rows.

    The oracle is a separate Python aggregation, not another copy of the SQL.
    SQLite authorizer forbids writes, functions, PRAGMA, ATTACH, and other tables.
    The instruction and row caps also bound malformed or recursive candidates.
    """
    totals: dict[str, list[int]] = {}
    for _, customer, status, cents in spec["rows"]:
        if status == "paid":
            totals.setdefault(customer, []).append(cents)
    expected = [(name, sum(values)) for name, values in sorted(totals.items())
                if len(values) >= 2]
    with sqlite3.connect(":memory:") as database:
        database.execute(spec["schema"])
        database.executemany("INSERT INTO orders VALUES (?, ?, ?, ?)", spec["rows"])
        database.commit()

        def authorize(action, name, column, _db, _trigger):
            allowed = action == sqlite3.SQLITE_SELECT
            allowed |= action == sqlite3.SQLITE_READ and name == "orders"
            allowed |= action == sqlite3.SQLITE_FUNCTION and column in {"sum", "count"}
            return sqlite3.SQLITE_OK if allowed else sqlite3.SQLITE_DENY

        database.set_authorizer(authorize)
        database.set_progress_handler(lambda: 1, 10000)
        try:
            rows = database.execute(query).fetchmany(101)
        except sqlite3.Error as error:
            return False, {"gate": "sql_execution", "error": str(error)}
    passed = len(rows) <= 100 and rows == expected
    return passed, {"gate": "row_equivalence", "actual": rows, "expected": expected}


def sql_example() -> dict:
    spec = fixtures()["sql"]
    prompt = le.build_context_prompt(spec["question"], spec["schema"])
    seen = []

    def make(_task, feedback):
        seen.append(feedback)
        return spec["baseline"] if feedback is None else spec["candidate"]

    result = le.run_until_done(prompt, make, lambda _, sql: verify_sql(sql, spec), 2)
    return {"state": "verified" if result["solved"] else "escalated",
            "prompt": prompt, "result": result, "feedback_received": seen,
            "authority": "read_only_in_memory_database"}


def checker_example() -> dict:
    """Check SQL against two independent data slices, including a held-out change."""
    visible = fixtures()["sql"]
    held_out = deepcopy(visible)
    held_out["rows"].append([7, "Ben", "paid", 100])
    candidates = {
        "known_good": visible["candidate"],
        "hardcoded_visible_answer": "SELECT 'Ada', 2000 UNION ALL SELECT 'Cy', 600",
        "known_bad": "SELECT customer, SUM(cents) FROM orders GROUP BY customer",
    }
    results = {name: le.maker_checker(
        visible["question"], lambda _, query=query: query,
        lambda _: [visible, held_out], lambda query, spec: verify_sql(query, spec)[0])
        for name, query in candidates.items()}
    results["missing_checks"] = le.maker_checker(
        visible["question"], lambda _: visible["candidate"], lambda _: [], lambda *_: True)
    return {"state": "report_only", "results": results,
            "scope_limit": "Fixed independent checks; no claim of model-generated test quality"}


def retrieve_policy(query: str, records: list[dict], *, max_age_days: int = 90,
                    min_similarity: float = 0.2, access: str = "support") -> list[dict]:
    # Filter access BEFORE indexing: restricted text never enters the context.
    eligible = [record for record in records
                if record.get("access") == access and record.get("source")
                and 0 <= record.get("age_days", max_age_days + 1) <= max_age_days]
    memory = le.EmbeddingMemory()
    memory.add([record["text"] for record in eligible], eligible)
    return [hit for hit in memory.retrieve(query, top_k=len(eligible))
            if hit["score"] >= min_similarity]


def memory_example() -> dict:
    records = fixtures()["memory"]
    hits = retrieve_policy("Payments incident retry policy", records)
    missing = retrieve_policy("unrelated gardening harvest", records)
    return {"state": "report_only", "hits": hits, "unknown_query":
            {"state": "abstained" if not missing else "retrieved", "hits": missing},
            "scorer": "lexical cosine, not learned semantic embeddings"}


def reconcile_payments(csv_text: str) -> dict:
    """Typed read tool: reject duplicate IDs and malformed money; no eval/exec."""
    records = list(csv.DictReader(io.StringIO(csv_text)))
    if not records:
        raise ValueError("payment export is empty")
    seen: set[str] = set()
    totals: Counter[str] = Counter()
    included = []
    for row in records:
        if set(row) != {"payment_id", "status", "currency", "cents"}:
            raise ValueError("unexpected payment schema")
        if not row["payment_id"] or row["payment_id"] in seen:
            raise ValueError("duplicate or missing payment ID")
        seen.add(row["payment_id"])
        if row["status"] not in {"settled", "pending", "refunded"}:
            raise ValueError("unknown payment status")
        if row["currency"] not in {"EUR", "USD"} or not row["cents"].isdigit():
            raise ValueError("invalid currency or cents")
        if row["status"] == "settled":
            totals[row["currency"]] += int(row["cents"])
            included.append(row["payment_id"])
    return {"settled_cents": dict(sorted(totals.items())), "payment_ids": included,
            "records_read": len(records)}


def data_example() -> dict:
    data = (FIXTURES / "payments.csv").read_text(encoding="utf-8")
    observation = reconcile_payments(data)
    # A plausible answer is checked against a constrained executor's observation.
    baseline = {"EUR": 2900, "USD": 500}  # incorrectly includes pending p3
    return {"state": "verified", "baseline_accepted": baseline == observation["settled_cents"],
            "tool": "reconcile_settled_payments", "observation": observation,
            "answer": observation["settled_cents"], "authority": "read_fixture_only"}


def verify_pr(pr: dict) -> tuple[bool, dict]:
    head, checks = pr.get("head"), pr.get("checks", {})
    required = pr.get("required", [])
    failures = [name for name in required
                if checks.get(name) != {"head": head, "state": "passed"}]
    if not head or not required:
        failures.append("missing_required_evidence")
    if pr.get("review") != {"head": head, "state": "approved"}:
        failures.append("current_head_review")
    return not failures, {"head": head, "failed_gates": failures}


def dependency_decision(update: dict) -> dict:
    route = le.route_dependency_update(update)
    missing = [field for field in ("provenance_verified", "license_approved",
                                   "reversible", "authorized") if update.get(field) is not True]
    # Even a low-risk policy proposal does not perform an installation or merge.
    return {"name": update["name"], "state": "eligible_proposal" if
            route == "auto_apply" and not missing else "human_review",
            "risk_route": route, "missing_gates": missing, "action_executed": False}


def ci_case(kind: str) -> dict:
    """Execute deterministic test probes; persistent failure alone is not diagnosis."""
    if kind not in {"regression", "flake", "environment", "dependency", "policy", "unknown"}:
        raise ValueError("unknown CI case")
    observations = []
    repair_calls = []

    def probe():
        if kind in {"environment", "dependency", "policy", "unknown"}:
            observations.append({"passed": False, "class": kind})
            return False
        # A fixture of intermittent service availability, not randomness/sleep.
        available = len(observations) % 2 == 1 if kind == "flake" else True
        actual = "/health/".rstrip("/") if kind == "flake" else "/health/"
        passed = available and actual == "/health"
        observations.append({"passed": passed, "actual": actual, "available": available})
        return passed

    def repair():
        repair_calls.append("normalize_trailing_slash")
        cases = {"/health/": "/health", "/health": "/health", "/": "/"}
        results = {path: (path.rstrip("/") or "/") == expected
                   for path, expected in cases.items()}
        return {"candidate": "path.rstrip('/') or '/'", "checks": results,
                "verified": all(results.values())}

    if kind in {"environment", "dependency", "policy", "unknown"}:
        diagnosis = le.classify_ci_failure(probe)
        result = {"state": "human_review", "diagnosis": kind,
                  "repeat_observation": diagnosis, "owner": "ci-maintainer"}
    else:
        result = le.ci_sweeper(probe, repair)
    return {**result, "observations": observations, "repair_calls": repair_calls,
            "action_executed": False}


def maintenance_example() -> dict:
    data = fixtures()
    triage = le.semantic_triage(data["issues"], ["production outage payment writes lost"],
                               review_limit=2)
    by_id = {issue["id"]: issue for issue in data["issues"]}
    for entry in triage:
        entry.update({key: by_id[entry["id"]][key] for key in ("owner", "impact")})
    vectors = [le.lexical_vector(issue["text"]) for issue in data["issues"]]
    duplicates = [{"id": data["issues"][index]["id"], "score": score,
                   "decision": "human_confirm_equivalence"}
                  for index, score in le.duplicate_candidates(0, vectors, top_k=1)]
    prs = []
    for pr in data["prs"]:
        passed, evidence = verify_pr(pr)
        result = le.pr_babysitter(pr, lambda item: item["id"], lambda *_: passed)
        prs.append({**result, "evidence": evidence})
    eligible_debt = [item for item in data["debt"] if item["age_days"] >= 90
                     and item["owner"] and item["obsolete_verified"] is True]
    debt = le.semantic_debt_queue([item["text"] for item in eligible_debt],
                                 ["temporary workaround remove after migration"], top_k=2)
    merged = [commit for commit in data["commits"] if commit["merged"] is True]
    def classify(message):
        return {"fix": "Fixes", "feat": "Features"}.get(message.split(":")[0], "Review")
    changelog = le.draft_changelog(merged, classify,
                                  lambda commit: f"{commit['message']} ({commit['id']})")
    return {"state": "report_only", "triage": triage, "duplicates": duplicates,
            "ci": {kind: ci_case(kind) for kind in
                   ("regression", "flake", "environment", "dependency", "policy", "unknown")},
            "dependencies": [dependency_decision(update) for update in data["updates"]],
            "prs": prs, "cleanup": {"queue": debt, "decision": "human_approves_removal"},
            "changelog": {"draft": changelog, "decision": "human_publishes"},
            "external_actions": []}


def orchestration_example(*, all_wrong: bool = False, budget: int = 4) -> dict:
    """A schema-grounded SQL cascade with a real final gate and pre-call cap.

    Budget units are candidate generations, NOT fabricated token measurements.
    Highest-ranked fallback is deliberately wrong to test independent acceptance.
    """
    spec = fixtures()["sql"]
    wrong = "SELECT customer, SUM(cents) FROM orders GROUP BY customer ORDER BY customer"
    history, calls = [], []
    fallback = iter([wrong, wrong if all_wrong else spec["candidate"]])

    def spend(stage):
        if len(calls) >= budget:
            raise RuntimeError("candidate_budget_exhausted")
        calls.append(stage)

    def implement(_task, _plan, feedback):
        spend("refinement")
        return spec["baseline"] if feedback is None else wrong

    def sample(*_):
        spend("fallback")
        return next(fallback)

    def check(_task, candidate):
        passed, evidence = verify_sql(candidate, spec)
        history.append({"candidate": candidate, "passed": passed, "evidence": evidence})
        return passed, evidence

    try:
        candidate = le.capstone_orchestra(spec["question"], lambda _: spec["schema"],
                                         implement, check, sample,
                                         lambda _, query: 10 if query == wrong else 1,
                                         retries=2, fallback_samples=2)
        result = {"state": "verified", "candidate": candidate}
    except RuntimeError as error:
        result = {"state": "escalated", "reason": str(error), "owner": "data-engineer"}
    return {**result, "history": history, "calls": calls, "budget_units": "candidate_generations"}


def coordination_example() -> dict:
    result = le.run_coordinated([
        {"name": "pr", "priority": 1, "queue": ["PR-42"]},
        {"name": "ci", "priority": 2, "queue": ["PR-42", "BUILD-9"]},
        {"name": "dependencies", "priority": 3, "queue": ["PR-42"]}])
    return {"state": "report_only", **result,
            "scope_limit": "One scheduling round; no Git writes, leases, or concurrent workers"}


def verify_refund_receipt(recommendation: dict, approval: dict, receipt: dict) -> bool:
    """A human approval is not evidence that billing completed the right action."""
    return (approval.get("approved") is True
            and approval.get("source") == "fixture/specialist-approval"
            and receipt.get("source") == "fixture/billing-receipt"
            and receipt.get("confirmed") is True
            and receipt.get("charge") == recommendation.get("charge")
            and type(receipt.get("cents")) is int
            and receipt["cents"] > 0
            and receipt["cents"] == recommendation.get("cents"))


SUPPORT_SCENARIOS = ("refund", "approved", "unconfirmed", "human", "identity", "fraud",
                     "policy", "repeat_failure", "tool_timeout", "tool_exhausted")


def support_example(scenario: str = "refund", *, ticket: dict | None = None,
                    queue_accepts: bool = True) -> dict:
    """Replay the manuscript's 08:15/08:42 billing case with serialized state.

    Human approval and billing confirmation are fixture receipts only. Financial
    authority is always zero. No callback here can contact an external system.
    """
    if scenario not in SUPPORT_SCENARIOS:
        raise ValueError("unknown support scenario")
    record = deepcopy(fixtures()["support"] if ticket is None else ticket)
    state = {"ticket_id": record["id"], "state": "collecting", "evidence": {},
             "attempts": [], "reasoning_retries": 0, "tool_resumptions": 0,
             "clarifications": 0, "financial_authority_cents": 0, "external_actions": []}

    def handoff(reason):
        # The acceptance receipt is simulated; an unaccepted queue is not terminal.
        state.update(state="escalated" if queue_accepts else "handoff_pending",
                     handoff={"owner": "billing-specialist", "reason": reason,
                              "accepted": queue_accepts,
                              "receipt": "fixture-handoff/T-42" if queue_accepts else None})
        state["response"] = "A billing specialist will review your refund request."
        return deepcopy(state)

    if scenario == "identity":
        record["authenticated"] = False
    if scenario == "human":
        record["human_requested"] = True
    if scenario == "fraud":
        record["risk"] = "suspected_fraud"
    if scenario == "policy":
        record["policy"]["current"] = False
    # Identity and explicit escalation precede retrieval/disclosure of account data.
    if record.get("authenticated") is not True:
        return handoff("identity_unresolved")
    if record.get("human_requested") or record.get("risk"):
        return handoff("human_requested" if record.get("human_requested") else record["risk"])
    if record.get("request") != "refund":
        return handoff("request_outside_refund_contract")
    state["evidence"]["account"] = record["account"]
    interruptions = 1 if scenario == "tool_timeout" else 4 if scenario == "tool_exhausted" else 0
    for _ in range(interruptions):
        if state["tool_resumptions"] >= 3:
            return handoff("tool_resumption_budget_exhausted")
        state["tool_resumptions"] += 1
        # A real serialization boundary proves evidence survives a new invocation.
        state = json.loads(json.dumps(state))
    state["evidence"] = {key: record[key] for key in
                         ("account", "charge", "renewal", "cancellation", "charge_cents",
                          "payment_status", "policy", "sources")}
    policy = record["policy"]
    if policy.get("approved") is not True or policy.get("current") is not True:
        return handoff("policy_not_current_and_approved")
    if record["payment_status"] != "settled":
        return handoff("payment_not_settled")
    renewal = datetime.fromisoformat(record["renewal"])
    cancellation = datetime.fromisoformat(record["cancellation"])
    gap_hours = (cancellation - renewal).total_seconds() / 3600
    if not 0 <= gap_hours <= policy["grace_hours"]:
        return handoff("refund_requires_policy_exception")
    previous_failure = None
    for attempt in range(3):
        # The corrective draft consumes the preceding gate's authoritative timestamps.
        if previous_failure is None or scenario == "repeat_failure":
            claim = "before"
        else:
            observed_cancel = datetime.fromisoformat(previous_failure["cancellation"])
            observed_renewal = datetime.fromisoformat(previous_failure["renewal"])
            claim = "after" if observed_cancel > observed_renewal else "same_time"
        passed = claim == ("after" if cancellation > renewal else "same_time")
        evidence = {"gate": "timeline", "renewal": record["renewal"],
                    "cancellation": record["cancellation"], "passed": passed}
        state["attempts"].append({"claim": claim, "verification": evidence})
        if passed:
            break
        if previous_failure == evidence:
            return handoff("repeated_failure_without_new_evidence")
        previous_failure = evidence
        state["reasoning_retries"] += 1
    else:
        return handoff("reasoning_budget_exhausted")
    state["recommendation"] = {"action": "refund", "cents": record["charge_cents"],
                               "charge": record["charge"], "policy_source": policy["source"]}
    state = handoff("financial_authority_zero")
    if scenario not in {"approved", "unconfirmed"} or not queue_accepts:
        return state
    # Resume after a *simulated* human action. Approval alone cannot close a ticket.
    state["human_approval"] = {"source": "fixture/specialist-approval", "approved": True}
    confirmation = {"source": "fixture/billing-receipt", "confirmed": scenario == "approved",
                    "charge": record["charge"], "cents": record["charge_cents"]}
    state["confirmation"] = confirmation
    if not verify_refund_receipt(state["recommendation"], state["human_approval"], confirmation):
        state["state"] = "awaiting_confirmation"
        state["response"] = "Your refund is approved; billing confirmation is pending."
        return state
    state["state"] = "resolved"
    state["response"] = "The simulated billing receipt confirms your refund."
    return state


CASES = {"sql": sql_example, "checker": checker_example,
         "memory": memory_example, "data": data_example,
         "maintenance": maintenance_example, "orchestra": orchestration_example,
         "coordination": coordination_example, "support": support_example}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=[*CASES, "all"], default="all")
    parser.add_argument("--support-scenario", choices=SUPPORT_SCENARIOS, default="refund")
    args = parser.parse_args(argv)
    selected = CASES if args.case == "all" else {args.case: CASES[args.case]}
    report = {name: support_example(args.support_scenario) if name == "support" else run()
              for name, run in selected.items()}
    print(json.dumps({"mode": "offline_fixture", "real_external_side_effects": False,
                      "cases": report}, indent=2, sort_keys=True))
    # Expected rejection and handoff are successful demonstrations, not CLI errors.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
