"""Bounded, file-backed Ralph controller for the book's chapter 4.

The worker is a fresh process on every iteration. Only controller-owned checks
can accept completion. This is orchestration, not a sandbox for untrusted code.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    workspace: Path
    prompt: Path
    state: Path
    worker: tuple[str, ...]
    scope_verifier: Path
    final_verifier: Path
    max_iterations: int = 10
    timeout: int = 300


def read_items(path: Path) -> tuple[tuple[str, str], ...]:
    """Validate persistent state; a worker's top-level status is not trusted."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError("state requires schema_version=1")
    items = data.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("state requires a nonempty items list")
    result: list[tuple[str, str]] = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("each item must be an object")
        identifier, status = item.get("id"), item.get("status")
        if not isinstance(identifier, str) or not identifier or status not in ("pending", "done"):
            raise ValueError("each item needs a nonempty id and pending/done status")
        result.append((identifier, status))
    if len({identifier for identifier, _ in result}) != len(result):
        raise ValueError("item ids must be unique")
    return tuple(result)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(path: Path, workspace: Path, timeout: int) -> bool:
    try:
        result = subprocess.run(
            [str(path)], cwd=workspace, capture_output=True, text=True,
            timeout=timeout, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"Verifier {path.name} failed: {exc}", file=sys.stderr)
        return False
    if result.returncode != 0:
        print(f"Verifier {path.name} failed: {result.stderr or result.stdout}", file=sys.stderr)
        return False
    return True


def run_loop(config: Config) -> int:
    """Return 0 only after all items and both independent gates pass.

    Exit 1: budget or verifier failure; 2: setup/state error; 3: scope or
    one-item protocol violation. No commit, push, merge, or approval occurs here.
    """
    if config.max_iterations < 1 or config.timeout < 1 or not config.worker:
        print("Positive budgets and a worker command are required.", file=sys.stderr)
        return 2
    workspace = config.workspace.resolve()
    if not workspace.is_dir():
        print("Workspace does not exist.", file=sys.stderr)
        return 2
    try:
        prompt = config.prompt.resolve(strict=True)
        state = config.state.resolve(strict=True)
        scope = config.scope_verifier.resolve(strict=True)
        final = config.final_verifier.resolve(strict=True)
        if not state.is_relative_to(workspace):
            raise ValueError("state must be inside the worker workspace")
        if any(path.is_relative_to(workspace) for path in (prompt, scope, final)):
            raise ValueError("prompt and verifiers must be outside the worker workspace")
        if not all(path.is_file() for path in (prompt, state, scope, final)):
            raise ValueError("prompt, state, and verifiers must be files")
        if not all(os.access(path, os.X_OK) for path in (scope, final)):
            raise ValueError("verifiers must be executable")
        expected = read_items(state)
        protected = {path: digest(path) for path in (prompt, scope, final)}
        prompt_text = prompt.read_text(encoding="utf-8")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Invalid Ralph setup: {exc}", file=sys.stderr)
        return 2

    def protected_unchanged() -> bool:
        try:
            return all(path.is_file() and digest(path) == value for path, value in protected.items())
        except OSError:
            return False

    if all(status == "done" for _, status in expected):
        if not protected_unchanged() or not verify(scope, workspace, config.timeout):
            return 3
        return 0 if verify(final, workspace, config.timeout) else 1

    for iteration in range(1, config.max_iterations + 1):
        print(f"Ralph iteration {iteration}/{config.max_iterations}", flush=True)
        try:
            result = subprocess.run(
                list(config.worker), cwd=workspace, input=prompt_text,
                capture_output=True, text=True, timeout=config.timeout,
                check=False,
            )
            if result.stdout:
                print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
            if result.stderr:
                print(result.stderr, file=sys.stderr, end="" if result.stderr.endswith("\n") else "\n")
            worker_ok = result.returncode == 0
            if not worker_ok:
                print(f"Worker exited with status {result.returncode}; state preserved.", file=sys.stderr)
        except subprocess.TimeoutExpired:
            print("Worker timed out; state preserved.", file=sys.stderr)
            worker_ok = False
        except OSError as exc:
            print(f"Worker could not start: {exc}", file=sys.stderr)
            return 2

        if not protected_unchanged():
            print("Controller-owned prompt or verifier changed; refusing acceptance.", file=sys.stderr)
            return 3
        try:
            current = read_items(state)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"Invalid state after worker: {exc}", file=sys.stderr)
            return 2
        before = dict(expected)
        after = dict(current)
        if [key for key, _ in current] != [key for key, _ in expected]:
            print("Worker changed the item inventory or order.", file=sys.stderr)
            return 3
        changed = [key for key in before if before[key] != after[key]]
        if len(changed) > 1 or any(before[key] != "pending" or after[key] != "done" for key in changed):
            print("Worker violated the one-item-per-iteration rule.", file=sys.stderr)
            return 3
        if changed and not worker_ok:
            print("Worker changed state but failed; human review required.", file=sys.stderr)
            return 3
        if not verify(scope, workspace, config.timeout):
            print("Scope check failed; human review required.", file=sys.stderr)
            return 3
        if not protected_unchanged():
            print("Controller-owned files changed during scope verification.", file=sys.stderr)
            return 3
        expected = current
        if worker_ok and all(status == "done" for _, status in current):
            if verify(final, workspace, config.timeout):
                print("COMPLETE: all items and controller checks passed.")
                return 0
            print("Final evidence failed; completion not accepted.", file=sys.stderr)
    print("BUDGET_EXHAUSTED: inspect preserved state and escalate.", file=sys.stderr)
    return 1


def demo() -> int:
    """Exercise two real, fresh worker processes without a model or credentials."""
    with tempfile.TemporaryDirectory(prefix="ralph-demo-") as temp:
        base = Path(temp)
        workspace = base / "workspace"
        workspace.mkdir()
        tasks = workspace / "tasks"
        tasks.mkdir()
        state = tasks / "state.json"
        state.write_text(json.dumps({"schema_version": 1, "items": [
            {"id": "first", "status": "pending"},
            {"id": "second", "status": "pending"},
        ]}), encoding="utf-8")
        prompt = base / "prompt.md"
        prompt.write_text("Complete exactly one pending item and stop.\n", encoding="utf-8")
        scope = base / "verify_scope.sh"
        scope.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        final = base / "verify_final.sh"
        final.write_text("#!/bin/sh\ntest -f result.txt && test \"$(cat result.txt)\" = first,second\n", encoding="utf-8")
        scope.chmod(0o700)
        final.chmod(0o700)
        worker = Path(__file__).with_name("ralph_demo_worker.py")
        return run_loop(Config(workspace, prompt, state, (sys.executable, str(worker)), scope, final, 3, 10))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", help="run the offline two-item example")
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--prompt", type=Path)
    parser.add_argument("--state", type=Path)
    parser.add_argument("--worker", help="worker executable, e.g. claude")
    parser.add_argument("--worker-arg", action="append", default=[], help="repeat for worker arguments; use --worker-arg=--print")
    parser.add_argument("--scope-verifier", type=Path)
    parser.add_argument("--final-verifier", type=Path)
    parser.add_argument("--max-iterations", type=int, default=10)
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args(argv)
    if args.demo:
        return demo()
    required = (args.workspace, args.prompt, args.state, args.worker, args.scope_verifier, args.final_verifier)
    if not all(required):
        parser.error("without --demo, workspace, prompt, state, worker, and both verifiers are required")
    return run_loop(Config(args.workspace, args.prompt, args.state, (args.worker, *args.worker_arg),
                           args.scope_verifier, args.final_verifier, args.max_iterations, args.timeout))


if __name__ == "__main__":
    raise SystemExit(main())
