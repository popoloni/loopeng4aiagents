"""Chapter 5 control-policy examples; report-only, no Git or shell actions.

This is a teaching model of Kowalski's documented decisions, not that external
framework. Callers supply actual gate implementations; booleans in the JSON
demo are explicitly synthetic observations, not proof that software was tested.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
from typing import Callable


GATE_ORDER = (
    "shell", "feature_markers", "change", "wiring", "behavior",
    "task_plugins", "independent_checker", "authorization", "plan",
)


def _nonnegative_int(value: int, name: str) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")


def choose_executor(task: dict, current_size: int = 0,
                    size_threshold: int = 10000) -> str:
    """Mirror chapter 5 precedence, using supplied byte sizes, not host reads."""
    if not isinstance(task, dict):
        raise ValueError("task must be an object")
    _nonnegative_int(current_size, "current_size")
    _nonnegative_int(size_threshold, "size_threshold")
    if task.get("mode") not in (None, "agent", "direct"):
        raise ValueError("unknown executor mode")
    if task.get("strategy") not in (None, "edit", "rewrite"):
        raise ValueError("unknown execution strategy")
    target = task.get("file")
    context = task.get("context", [])
    if not isinstance(target, str) or not target:
        raise ValueError("task needs a nonempty file name")
    if not isinstance(context, list) or not all(isinstance(p, str) for p in context):
        raise ValueError("context must be a list of file names")
    if task.get("mode") != "direct" or task.get("strategy") == "edit":
        return "agent"
    if task.get("strategy") == "rewrite":
        return "direct"
    if target in context and current_size > size_threshold:
        return "agent"
    return "direct"


def run_gates(gates: list[tuple[str, Callable[[], bool]]]) -> dict:
    """Fail closed and stop immediately; missing gates never imply acceptance."""
    names = [name for name, _ in gates]
    if names != list(GATE_ORDER):
        raise ValueError("supply each required gate exactly once in declared order")
    observations = []
    for name, check in gates:
        try:
            result = check()
            if type(result) is not bool:
                raise TypeError("gate must return a boolean, not a completion claim")
            record = {"gate": name, "passed": result}
        except Exception as exc:
            record = {"gate": name, "passed": False, "error": type(exc).__name__,
                      "detail": str(exc)}
        observations.append(record)
        if not record["passed"]:
            return {"verified": False, "failed_gate": name,
                    "observations": observations}
    return {"verified": True, "failed_gate": None, "observations": observations}


@dataclass(frozen=True)
class Budget:
    max_attempts: int = 3
    max_retries: int = 2
    max_resumes: int = 1
    max_seconds: float = 90
    attempts_used: int = 0
    retries_used: int = 0
    resumes_used: int = 0
    elapsed_seconds: float = 0

    def __post_init__(self):
        for name in ("max_attempts", "max_retries", "max_resumes",
                     "attempts_used", "retries_used", "resumes_used"):
            _nonnegative_int(getattr(self, name), name)
        for name in ("max_seconds", "elapsed_seconds"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError(f"{name} must be finite and nonnegative")
        if self.max_attempts == 0 or self.max_seconds == 0:
            raise ValueError("attempt/time limits must be positive")


def next_transition(outcome: str, budget: Budget, *,
                    authorized: bool = True, usable_progress: bool = False) -> dict:
    """Decide after an attempt; used counters include the completed attempt.

Retry/resume counters count continuations already granted. The returned counts
reserve the next continuation. Repository actions are recommendations only.
"""
    if outcome not in {"OK", "VERIFY_FAILED", "TIMEOUT", "AGENT_ERROR"}:
        raise ValueError("unknown attempt outcome")
    if type(authorized) is not bool or type(usable_progress) is not bool:
        raise ValueError("authorization and progress must be booleans")
    counts = asdict(budget)
    def decision(action, repository_action, reason):
        return {"action": action, "repository_action": repository_action,
                "reason": reason, "budget": counts, "executed": False}
    if not authorized:
        return decision("halt_for_human", "restore_accepted_checkpoint",
                        "authorization_violation")
    # A result at/after the deadline cannot retrospectively become accepted.
    if budget.elapsed_seconds >= budget.max_seconds or budget.attempts_used > budget.max_attempts:
        return decision("escalate", "preserve_diagnostics_and_safe_baseline",
                        "attempt_or_time_budget_exhausted")
    if outcome == "OK":
        return decision("advance", "propose_verified_commit", "verified_and_authorized")
    if budget.attempts_used >= budget.max_attempts:
        return decision("escalate", "preserve_diagnostics_and_safe_baseline",
                        "attempt_budget_exhausted")
    if outcome in {"TIMEOUT", "AGENT_ERROR"} and usable_progress:
        if budget.resumes_used >= budget.max_resumes:
            return decision("escalate", "preserve_valid_wip", "resume_budget_exhausted")
        counts["resumes_used"] += 1
        return decision("resume", "preserve_valid_wip", "usable_partial_progress")
    if budget.retries_used >= budget.max_retries:
        return decision("escalate", "restore_accepted_checkpoint", "retry_budget_exhausted")
    counts["retries_used"] += 1
    return decision("retry_with_evidence", "restore_accepted_checkpoint", outcome.lower())


def evaluate_scenario(data: dict) -> dict:
    if not isinstance(data, dict) or not isinstance(data.get("name"), str) or not data["name"]:
        raise ValueError("scenario must be an object with a nonempty name")
    if not isinstance(data.get("budget"), dict):
        raise ValueError("budget must be an object")
    checks = data["gate_results"]
    if not isinstance(checks, dict) or set(checks) != set(GATE_ORDER):
        raise ValueError("gate_results must name exactly the declared gates")
    if not all(type(value) is bool for value in checks.values()):
        raise ValueError("synthetic gate results must be booleans")
    gate_result = run_gates([(name, lambda name=name: checks[name]) for name in GATE_ORDER])
    transition = next_transition(
        data["outcome"], Budget(**data["budget"]),
        authorized=data["authorized"], usable_progress=data.get("usable_progress", False))
    if data["outcome"] == "OK" and not gate_result["verified"]:
        raise ValueError("OK cannot be asserted when gates fail")
    if data["authorized"] != checks["authorization"]:
        raise ValueError("authorization decision contradicts its gate")
    return {"name": data["name"], "executor": choose_executor(
                data["task"], data.get("current_size", 0), data.get("size_threshold", 10000)),
            "gates": gate_result, "transition": transition,
            "evidence_kind": "SYNTHETIC_POLICY_EXAMPLE"}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--demo", action="store_true")
    group.add_argument("--scenarios", type=Path)
    args = parser.parse_args(argv)
    path = args.scenarios or Path(__file__).resolve().parents[2] / "examples/local_policy/scenarios.json"
    try:
        data = json.loads(path.read_text())
        if not isinstance(data, list) or not data:
            raise ValueError("nonempty scenario list required")
        print(json.dumps([evaluate_scenario(item) for item in data], indent=2))
    except (ValueError, TypeError, KeyError, OSError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
