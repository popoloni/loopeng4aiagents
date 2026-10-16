#!/usr/bin/env python3
"""Runnable, standard-library companion to chapter 6's loop mechanisms.

The CLI runs a deterministic code-repair example or a JSON task containing candidate
programs and assertions. Callback-based functions also accept real model/tool adapters.
Candidate Python is executed in a subprocess, NOT a security sandbox: use trusted
candidate code and tests only. No network calls, merges, or external actions occur
in the default demo.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
from typing import Any, Callable, Iterable
from urllib.request import Request, urlopen


def run_until_done(task, make, check, max_attempts=3):
    """Listing 042: bounded candidate/check/feedback loop."""
    if max_attempts < 1:
        raise ValueError("max_attempts must be positive")
    feedback = None
    history = []
    candidate = None
    for attempt in range(1, max_attempts + 1):
        candidate = make(task, feedback)
        passed, evidence = check(task, candidate)
        history.append({"attempt": attempt, "passed": bool(passed), "evidence": evidence})
        if passed:
            return {"solved": True, "candidate": candidate, "attempts": attempt, "history": history}
        feedback = evidence
    return {"solved": False, "candidate": candidate, "attempts": max_attempts, "history": history}


def maker_checker(task, make, write_checks, run_check):
    """Listing 043: reject unless at least one independent check passes."""
    candidate = make(task)
    checks = list(write_checks(task))
    if not checks:
        return {"accepted": False, "candidate": candidate, "reason": "no executable checks",
                "checks_passed": 0, "checks_total": 0}
    results = [bool(run_check(candidate, check)) for check in checks]
    return {"accepted": all(results), "candidate": candidate,
            "checks_passed": sum(results), "checks_total": len(results)}


def build_context_prompt(question, schema, examples=()):
    """Listing 044: make stable schema and examples explicit in the prompt."""
    parts = []
    if examples:
        rendered = "\n\n".join(
            f"Schema: {ex['schema']}\nQuestion: {ex['question']}\nAnswer: {ex['answer']}"
            for ex in examples
        )
        parts.append(f"Examples:\n{rendered}")
    parts.append(f"Use only fields present in this schema:\n{schema}\n\nQuestion: {question}")
    return "\n\n".join(parts)


def lexical_vector(text: str) -> Counter[str]:
    """Deterministic offline substitute for the course's learned embeddings."""
    return Counter(re.findall(r"[a-z0-9]+", text.lower()))


def cosine(left: Counter[str], right: Counter[str]) -> float:
    numerator = sum(value * right.get(key, 0) for key, value in left.items())
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    return numerator / (left_norm * right_norm) if left_norm and right_norm else 0.0


class EmbeddingMemory:
    """Listing 045: in-memory retrieval with an injectable vector scorer.

    The default lexical scorer is deliberately not a semantic embedding model.
    Supply an encode/scorer pair to use an external embedding backend.
    """

    def __init__(self, encode=lexical_vector, score=cosine):
        self.encode = encode
        self.score = score
        self.documents: list[str] = []
        self.metadata: list[Any] = []
        self.vectors: list[Any] = []

    def add(self, documents, metadata=None):
        documents = list(documents)
        metadata = [None] * len(documents) if metadata is None else list(metadata)
        if len(documents) != len(metadata):
            raise ValueError("documents and metadata must have equal length")
        self.documents.extend(documents)
        self.metadata.extend(metadata)
        self.vectors.extend(self.encode(doc) for doc in documents)

    def retrieve(self, query, top_k=3):
        if top_k < 0:
            raise ValueError("top_k must be nonnegative")
        query_vector = self.encode(query)
        ranked = sorted(range(len(self.documents)),
                        key=lambda index: (-self.score(self.vectors[index], query_vector), index))
        return [{"document": self.documents[i], "metadata": self.metadata[i],
                 "score": float(self.score(self.vectors[i], query_vector))}
                for i in ranked[:top_k]]


def _code_block(text):
    blocks = re.findall(r"```(?:python)?\s*\n(.*?)```", text, re.DOTALL | re.IGNORECASE)
    return blocks[-1].strip() if blocks else ""


def react_solve(question, complete, run_tool, max_steps=4):
    """Listing 046: a tool callback receives proposed code; never implicit eval."""
    if max_steps < 1:
        raise ValueError("max_steps must be positive")
    transcript = f"Question: {question}\n"
    for _ in range(max_steps):
        reply = complete(transcript)
        if "FINAL:" in reply:
            answer = reply.split("FINAL:", 1)[1].strip().splitlines()
            return answer[0] if answer else ""
        code = _code_block(reply)
        observation = run_tool(code) if code else "no runnable action"
        transcript += f"{reply}\nTOOL OUTPUT:\n{observation}\n"
    raise RuntimeError("tool loop ended without a FINAL answer")


def _git(repository, *arguments):
    return subprocess.run(["git", "-C", str(repository), *arguments],
                          check=True, text=True, capture_output=True)


def run_in_worktree(repository, task_id, edit):
    """Listing 047: isolate edits; leave a failed worktree available for inspection."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", task_id):
        raise ValueError("task_id must be a simple branch-safe name")
    repository = Path(repository).resolve()
    branch = f"loop/{task_id}"
    path = Path(tempfile.mkdtemp(prefix=f"loop-{task_id}-"))
    try:
        _git(repository, "worktree", "add", "-b", branch, str(path))
        edit(path)
        _git(path, "add", "-A")
        if _git(path, "status", "--porcelain").stdout.strip():
            _git(path, "commit", "-m", f"complete {task_id}")
        _git(repository, "worktree", "remove", str(path))
    except Exception as error:
        raise RuntimeError(f"worktree retained for inspection at {path}: {error}") from error
    return branch


def integrate_branch(repository, branch):
    """Explicit, conflict-surfacing integration; not called by the CLI."""
    return _git(repository, "merge", "--no-edit", branch).stdout


def run_coordinated(loops):
    """Listing 048: assign one owner per target by priority."""
    owned_by, actions, yielded = {}, [], []
    for loop in sorted(loops, key=lambda item: item["priority"]):
        for target in loop["queue"]:
            if target in owned_by:
                yielded.append({"loop": loop["name"], "target": target, "owner": owned_by[target]})
            else:
                owned_by[target] = loop["name"]
                actions.append((loop["name"], target))
    return {"actions": actions, "yielded": yielded, "collisions": 0, "owned_by": owned_by}


def projected_daily_tokens(cadence_minutes, outcome_mix, token_cost):
    """Listing 049: estimate token budget from a normalized outcome mix."""
    if cadence_minutes <= 0:
        raise ValueError("cadence_minutes must be positive")
    if any(outcome_mix[name] < 0 for name in ("noop", "report", "action")):
        raise ValueError("outcome weights cannot be negative")
    if not math.isclose(sum(outcome_mix[name] for name in ("noop", "report", "action")), 1.0):
        raise ValueError("outcome weights must sum to one")
    runs = 1440 // cadence_minutes
    per_run = sum(outcome_mix[name] * token_cost[name] for name in ("noop", "report", "action"))
    return {"runs_per_day": runs, "tokens_per_run": per_run, "tokens_per_day": runs * per_run}


def pareto_frontier(strategies):
    """Keep nondominated cost/quality strategies, including equivalent ties."""
    return [candidate for candidate in strategies if not any(
        other["tokens"] <= candidate["tokens"] and other["quality"] >= candidate["quality"]
        and (other["tokens"] < candidate["tokens"] or other["quality"] > candidate["quality"])
        for other in strategies)]


def guardrail_autoact(change, denylisted_paths, max_files=10, min_confidence=0.8):
    """Listing 050: fail closed on unknown scope, risk, or missing verification."""
    paths = change.get("paths", [])
    if not paths or change.get("n_files") != len(paths):
        return False
    if any(Path(path).is_absolute() or ".." in Path(path).parts for path in paths):
        return False
    normalized = [Path(path).as_posix().removeprefix("./") for path in paths]
    denied = [Path(path).as_posix().rstrip("/") for path in denylisted_paths]
    touches_denylist = any(path == prefix or path.startswith(prefix + "/")
                           for path in normalized for prefix in denied)
    return bool(not touches_denylist and len(paths) <= max_files
                and change.get("confidence", 0) >= min_confidence
                and change.get("verified") is True
                and change.get("reversible") is True
                and change.get("approved_scope") is True)


def tree_digest(paths):
    """Listing 051: content digest of protected verifier files."""
    digest = sha256()
    for path in sorted(map(Path, paths), key=str):
        digest.update(str(path).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def run_protected_verifier(candidate, protected_paths, verifier):
    before = tree_digest(protected_paths)
    try:
        result = verifier(candidate)
    finally:
        if tree_digest(protected_paths) != before:
            raise PermissionError("protected verifier assets were modified")
    return result


def _rank_by_examples(texts, examples, encode=lexical_vector, score=cosine):
    if not examples:
        raise ValueError("at least one reference example is required")
    reference = [encode(example) for example in examples]
    return [sum(score(text_vector, vector) for vector in reference) / len(reference)
            for text_vector in (encode(text) for text in texts)]


def semantic_triage(items, urgent_examples, embed=lexical_vector, review_limit=20):
    """Listing 052: report-only ranking; default is lexical, not semantic."""
    scores = _rank_by_examples([item["text"] for item in items], urgent_examples, embed)
    order = sorted(range(len(items)), key=lambda i: (-scores[i], i))[:review_limit]
    return [{"id": items[i]["id"], "score": scores[i], "decision": "human_review"}
            for i in order]


def classify_ci_failure(run_test, runs=5):
    """Listing 053: repeated observations separate persistent failure and flake."""
    if runs < 1:
        raise ValueError("runs must be positive")
    outcomes = [bool(run_test()) for _ in range(runs)]
    return "real_failure" if not any(outcomes) else "passing" if all(outcomes) else "flake"


def ci_sweeper(run_test, repair):
    diagnosis = classify_ci_failure(run_test)
    if diagnosis != "real_failure":
        return {"state": "report_only", "diagnosis": diagnosis}
    return {"state": "candidate_patch", "diagnosis": diagnosis, "patch": repair()}


def route_dependency_update(update):
    """Listing 054: route changes; returned auto_apply is a policy decision, not an action."""
    safe = (update.get("tier") == "patch" and update.get("severity") in (None, "none", "low")
            and not update.get("denylisted", False) and update.get("green") is True)
    return "auto_apply" if safe else "human_review"


def duplicate_candidates(query_index, vectors, top_k=10):
    """Listing 055: rank other items by cosine similarity."""
    if not 0 <= query_index < len(vectors):
        raise IndexError("invalid query_index")
    scores = [(i, cosine(vectors[query_index], vector)) for i, vector in enumerate(vectors)
              if i != query_index]
    return sorted(scores, key=lambda pair: (-pair[1], pair[0]))[:top_k]


def pr_babysitter(problem, refine, executable_verify):
    candidate = refine(problem)
    ready = bool(executable_verify(problem, candidate))
    return {"proposal": "ready_to_merge" if ready else "needs_work",
            "human_still_merges": True, "candidate": candidate}


def semantic_debt_queue(comments, debt_examples, embed=lexical_vector, top_k=20):
    scores = _rank_by_examples(comments, debt_examples, embed)
    order = sorted(range(len(comments)), key=lambda i: (-scores[i], i))[:top_k]
    return [comments[i] for i in order]


def draft_changelog(commits, classify, summarize):
    sections = {}
    for commit in commits:
        kind = classify(commit["message"])
        sections.setdefault(kind, []).append(summarize(commit))
    return "\n".join(f"## {kind}\n" + "\n".join(f"- {item}" for item in items)
                     for kind, items in sorted(sections.items()))


def capstone_orchestra(task, plan, implement, check, sample, checker_score,
                       retries=3, fallback_samples=4):
    """Listing 056: only a real check can approve the fallback winner."""
    plan_text = plan(task)
    feedback = None
    for _ in range(retries):
        candidate = implement(task, plan_text, feedback)
        passed, feedback = check(task, candidate)
        if passed:
            return candidate
    candidates = [sample(task, plan_text) for _ in range(fallback_samples)]
    for candidate in sorted(candidates, key=lambda item: checker_score(task, item), reverse=True):
        passed, _ = check(task, candidate)
        if passed:
            return candidate
    raise RuntimeError("all verified orchestration stages failed")


@dataclass(frozen=True)
class LoopContract:
    """Listing 057: explicit execution limits and action authority."""
    objective: str
    verify: Callable[[object], tuple[bool, dict]]
    max_attempts: int
    max_seconds: float
    allowed_actions: frozenset[str]
    escalation_owner: str

    def permits(self, action: str) -> bool:
        return action in self.allowed_actions


def validate_task_contract(data):
    """Listing 058: validate the technology-neutral JSON task contract."""
    required = ("id", "trigger", "scope", "verification", "budget", "risk", "on_failure")
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError(f"task contract missing: {', '.join(missing)}")
    if data["verification"].get("default") != "reject":
        raise ValueError("verification must default to reject")
    if data["budget"].get("max_attempts", 0) < 1:
        raise ValueError("budget must set a positive max_attempts")
    if not isinstance(data["scope"].get("paths"), list):
        raise ValueError("scope.paths must be a list")
    return data


def choose_controls(problem):
    """Listing 059: choose only controls justified by observed deficiencies."""
    controls = ["budget", "observability"]
    if not problem["independently_verifiable"]:
        return ["refine_specification_or_human_review"]
    for condition, control in (("missing_stable_context", "skill"),
                               ("missing_historical_fact", "retrieval"),
                               ("needs_exact_operation", "tool")):
        if problem.get(condition):
            controls.append(control)
    if problem.get("false_acceptance_cost", 0) > 0.5:
        controls.append("maker_checker")
    if problem.get("concurrent_writers", 1) > 1:
        controls.extend(["worktree", "ownership_registry"])
    if problem.get("material_side_effect"):
        controls.append("authorization_guardrail")
    return list(dict.fromkeys(controls))


def resolve_ticket(ticket, retrieve, draft, verify, authorize,
                   execute_action, handoff, max_retries=2):
    """Listing 060: bounded support loop; action requires separate authorization."""
    evidence = retrieve(ticket)
    feedback = None
    for _ in range(max_retries + 1):
        response, action = draft(ticket, evidence, feedback)
        passed, feedback = verify(ticket, response, action, evidence)
        if not passed:
            continue
        if action is None:
            return {"state": "resolved", "response": response}
        if not authorize(ticket, action):
            return handoff(ticket, evidence, response, action)
        confirmation = execute_action(action)
        if confirmation.get("confirmed"):
            return {"state": "resolved", "response": response,
                    "confirmation": confirmation}
    return handoff(ticket, evidence, None, None)


def execute_python(candidate: str, assertions: Iterable[str], timeout=3.0):
    """Run trusted candidate plus assertions with a timeout; NOT a security sandbox."""
    assertions = list(assertions)
    if not assertions:
        raise ValueError("at least one assertion is required")
    with tempfile.TemporaryDirectory(prefix="loop-check-") as temp:
        script = Path(temp) / "candidate.py"
        script.write_text(candidate + "\n\n" + "\n".join(assertions) + "\n", encoding="utf-8")
        try:
            result = subprocess.run([sys.executable, "-I", str(script)], cwd=temp,
                                    text=True, capture_output=True, timeout=timeout, check=False)
        except subprocess.TimeoutExpired:
            return False, {"status": "timeout", "stderr": "candidate timed out"}
    return result.returncode == 0, {"status": "passed" if result.returncode == 0 else "failed",
                                    "stderr": result.stderr[-1200:]}


class VLLMGenerator:
    """Minimal HTTP adapter for the course's local vLLM chat-completions server.

    Uses the standard library only. The endpoint must be supplied explicitly by the CLI.
    This is for a trusted local environment, not a remote multi-user service.
    """

    def __init__(self, endpoint: str, model: str, max_output_tokens: int = 1024,
                 token_budget: int = 5000, timeout: float = 30.0):
        self.endpoint = endpoint
        self.model = model
        self.max_output_tokens = max_output_tokens
        self.token_budget = token_budget
        self.timeout = timeout
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.previous_code: str | None = None

    @property
    def total_tokens(self):
        return self.prompt_tokens + self.completion_tokens

    def __call__(self, objective: str, feedback: Any) -> str:
        if self.total_tokens >= self.token_budget:
            raise RuntimeError("model token budget exhausted")
        prompt = f"Implement this Python task. Return one complete fenced Python code block.\n\n{objective}"
        if self.previous_code is not None:
            prompt += f"\n\nPrevious attempt:\n```python\n{self.previous_code}\n```"
        if feedback is not None:
            prompt += f"\n\nExecution feedback:\n{json.dumps(feedback)}\nRepair the failure."
        payload = {"model": self.model, "messages": [
            {"role": "system", "content": "Write correct, self-contained Python code. Return only a fenced code block."},
            {"role": "user", "content": prompt}],
            "temperature": 0, "max_tokens": self.max_output_tokens}
        request = Request(self.endpoint, data=json.dumps(payload).encode("utf-8"),
                          headers={"Content-Type": "application/json",
                                   "Authorization": f"Bearer {os.environ.get('VLLM_API_KEY', 'EMPTY')}"})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = json.load(response)
            text = body["choices"][0]["message"]["content"]
        except (OSError, ValueError, KeyError, IndexError, TypeError) as error:
            raise RuntimeError(f"model request or response failed: {error}") from error
        usage = body.get("usage") or {}
        self.prompt_tokens += int(usage.get("prompt_tokens", 0))
        self.completion_tokens += int(usage.get("completion_tokens", 0))
        if self.total_tokens > self.token_budget:
            raise RuntimeError("model token budget exhausted")
        candidate = _code_block(text)
        if not candidate:
            raise RuntimeError("model did not return a fenced Python code block")
        self.previous_code = candidate
        return candidate


def run_code_task(task, generator=None):
    """Run one code-repair loop with replay candidates or a supplied generator."""
    objective = task["objective"]
    assertions = task["assertions"]
    candidates = task.get("candidates", [])
    max_attempts = task.get("max_attempts", len(candidates))
    if max_attempts < 1 or (generator is None and not candidates):
        raise ValueError("task needs positive max_attempts and candidates or a generator")
    contract = LoopContract(objective, lambda code: execute_python(code, assertions),
                            max_attempts, float(task.get("max_seconds", 15)),
                            frozenset({"report"}), task.get("escalation_owner", "human"))
    start = time.monotonic()
    attempts = iter(candidates)

    def make(_task, _feedback):
        if time.monotonic() - start > contract.max_seconds:
            raise TimeoutError("loop time budget exhausted")
        return generator(objective, _feedback) if generator is not None else next(attempts)

    def check(_task, candidate):
        passed, evidence = contract.verify(candidate)
        if time.monotonic() - start > contract.max_seconds:
            return False, {"status": "time_budget_exhausted"}
        return passed, evidence

    try:
        result = run_until_done(objective, make, check,
                                max_attempts=max_attempts if generator is not None
                                else min(max_attempts, len(candidates)))
    except TimeoutError:
        return {"state": "escalated", "reason": "time_budget_exhausted",
                "owner": contract.escalation_owner}
    except (RuntimeError, StopIteration) as error:
        return {"state": "escalated", "reason": "generation_failed",
                "detail": str(error), "owner": contract.escalation_owner}
    if result["solved"]:
        return {"state": "verified", "attempts": result["attempts"],
                "candidate": result["candidate"], "history": result["history"],
                "action": "report_only"}
    return {"state": "escalated", "reason": "verification_failed",
            "owner": contract.escalation_owner, "history": result["history"]}


DEMO_TASK = {
    "objective": "Implement add(a, b) correctly",
    "assertions": ["assert add(2, 3) == 5", "assert add(-1, 1) == 0"],
    "candidates": ["def add(a, b):\n    return a - b",
                   "def add(a, b):\n    return a + b"],
    "max_attempts": 2,
}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--demo", action="store_true", help="run the built-in offline repair loop")
    group.add_argument("--task", type=Path, help="JSON file with objective, assertions, candidates")
    parser.add_argument("--vllm-model", help="generate candidates with a local vLLM model")
    parser.add_argument("--vllm-endpoint", default="http://127.0.0.1:8000/v1/chat/completions",
                        help="full vLLM chat-completions endpoint URL")
    parser.add_argument("--allow-model-code", action="store_true",
                        help="explicitly allow executing generated code (subprocess is not a sandbox)")
    args = parser.parse_args(argv)
    task = DEMO_TASK if args.demo else json.loads(args.task.read_text(encoding="utf-8"))
    if args.demo and args.vllm_model:
        parser.error("--demo uses deterministic candidates; use --task for a model run")
    if not args.demo and not task.get("trusted_code", False):
        parser.error("task must set trusted_code=true: subprocess execution is not a sandbox")
    if args.vllm_model and not args.allow_model_code:
        parser.error("--vllm-model requires --allow-model-code")
    generator = VLLMGenerator(args.vllm_endpoint, args.vllm_model,
                              token_budget=int(task.get("max_tokens", 5000)),
                              timeout=min(30, float(task.get("max_seconds", 15)))) if args.vllm_model else None
    result = run_code_task(task, generator=generator)
    if generator is not None:
        result["model_usage"] = {"prompt_tokens": generator.prompt_tokens,
                                 "completion_tokens": generator.completion_tokens}
    print(json.dumps(result, indent=2))
    return 0 if result["state"] == "verified" else 1


if __name__ == "__main__":
    raise SystemExit(main())
