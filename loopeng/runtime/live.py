"""Reproducible live Ralph arithmetic driver; generated code executes only in Docker."""
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
import time
import uuid
from pathlib import Path

from loopeng.runtime.local_model import REPO, fresh_directory, sha256, write_json
from loopeng.ralph.controller import Config, run_loop
from loopeng.ralph.model_worker import chat, check_workspace, normalize_code
from loopeng.engineering import run_until_done

FIXTURE = REPO / "examples/local_model"


def docker_check(code: str, docker: list[str], image: str, receipts: Path, timeout: int = 10) -> dict:
    """No host mounts or network. Finally removes only this call's unique container."""
    name = "loopeng-check-" + uuid.uuid4().hex
    command = [*docker, "run", "--rm", "--pull=never", "--name", name,
               "--network=none", "--read-only", "--cap-drop=ALL", "--security-opt=no-new-privileges",
               "--pids-limit=32", "--memory=128m", "--memory-swap=128m", "--cpus=1",
               "--user=65534:65534", "-i", image, "python", "-I", "-B", "-"]
    receipt = {"command": command, "code": code, "receipt": str(receipts / (name + ".json"))}
    try:
        result = subprocess.run(command, input=code, text=True, capture_output=True, timeout=timeout, check=False)
        receipt.update(exit_code=result.returncode, stdout=result.stdout, stderr=result.stderr)
        status = "passed" if result.returncode == 0 else "execution_error"
        if result.returncode in (125, 126, 127):
            status = "backend_error"
        elif (result.returncode == 1 and 'File "<stdin>"' in result.stderr
              and result.stderr.rstrip().splitlines()[-1] == "AssertionError"):
            status = "assertion_failed"
        receipt["status"] = status
    except (OSError, subprocess.TimeoutExpired) as exc:
        receipt.update(exit_code=1, error_type=type(exc).__name__,
                       status="timeout" if isinstance(exc, subprocess.TimeoutExpired) else "backend_error")
    finally:
        try:
            cleanup = subprocess.run([*docker, "rm", "-f", name], capture_output=True, text=True, timeout=5, check=False)
            receipt["cleanup_exit_code"] = cleanup.returncode
        except (OSError, subprocess.TimeoutExpired) as exc:
            receipt["cleanup_error"] = type(exc).__name__
        write_json(receipts / (name + ".json"), receipt)
    return receipt


def controls(assertions: str, negative: str, docker: list[str], image: str, receipts: Path) -> None:
    """Known controls are never candidates or repairs; both use the real verifier."""
    positive = "def add(a, b):\n    return a + b\ndef multiply(a, b):\n    return a * b\n"
    good = docker_check(positive + "\n" + assertions, docker, image, receipts)
    write_json(receipts / "positive-control.json", good)
    if good["status"] != "passed":
        raise ValueError("Positive arithmetic control failed; no model call allowed")
    bad = docker_check(negative + "\n" + assertions, docker, image, receipts)
    write_json(receipts / "negative-control.json", bad)
    if bad["status"] != "assertion_failed":
        raise ValueError("Negative fixture did not produce an actual AssertionError; no model call allowed")


def local_image(docker: list[str], image: str) -> str:
    if not docker or not image or image.startswith("-"):
        raise ValueError("Valid Docker command and local image required")
    result = subprocess.run([*docker, "image", "inspect", "--format", "{{.Id}}", image],
                            text=True, capture_output=True, timeout=10, check=True)
    image_id = result.stdout.strip()
    if not image_id.startswith("sha256:") or len(image_id) != 71:
        raise ValueError("Docker did not return an immutable image ID")
    return image_id


def verify(kind: str, config_path: Path) -> int:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    workspace = Path.cwd()
    check_workspace(workspace)
    for path, digest in config["protected"].items():
        if sha256(Path(path)) != digest:
            raise ValueError("Protected fixture/implementation changed")
    if kind == "scope":
        return 0
    if not config["allow_model_code"]:
        raise ValueError("Candidate execution requires explicit opt-in")
    code = "\n".join(normalize_code((workspace / f"{name}.py").read_text(encoding="utf-8"), name) for name in ("add", "multiply"))
    code += "\n" + Path(config["assertions"]).read_text(encoding="utf-8")
    return docker_check(code, config["docker"], config["image"], Path(config["receipts"]))["exit_code"]


def demo(output: Path, endpoint: str, model: str, docker: list[str], image: str, allow_model_code: bool) -> int:
    if not allow_model_code:
        raise ValueError("Pass --allow-model-code to execute candidates in Docker")
    # Resolve an already installed image to its immutable local identity; never pull.
    image_id = local_image(docker, image)
    output = fresh_directory(output)
    workspace = output / "workspace"
    (workspace / "tasks").mkdir(parents=True)
    controller = output / "controller"
    controller.mkdir()
    receipts = output / "receipts"
    receipts.mkdir()
    for name in ("add.py", "multiply.py"):
        (workspace / name).write_bytes((FIXTURE / name).read_bytes())
    (workspace / "tasks/state.json").write_bytes((FIXTURE / "state.json").read_bytes())
    prompt = controller / "prompt.md"
    prompt.write_bytes((FIXTURE / "prompt.md").read_bytes())
    assertions = controller / "assertions.py"
    assertions.write_bytes((FIXTURE / "assertions.py").read_bytes())
    script = REPO / "loopeng/__main__.py"
    # Protect actual implementations and the subprocess entry points.
    sources = [*sorted((REPO / "loopeng").rglob("*.py")), assertions, prompt]
    config_path = controller / "config.json"
    config = {"protected": {str(path): sha256(path) for path in sources}, "assertions": str(assertions),
              "docker": docker, "image": image_id, "receipts": str(receipts), "allow_model_code": True}
    write_json(config_path, config)
    wrappers = []
    for kind in ("scope", "final"):
        wrapper = controller / f"verify_{kind}.sh"
        # Include config identity in the controller-hashed executable wrapper.
        check = f"import hashlib; from pathlib import Path; assert hashlib.sha256(Path({str(config_path)!r}).read_bytes()).hexdigest() == {sha256(config_path)!r}"
        wrapper.write_text("#!/bin/sh\n" + shlex.join([sys.executable, "-I", "-c", check]) + " || exit 1\nexec " +
                           shlex.join([sys.executable, "-B", str(script), "live", "verify", kind, str(config_path)]) + "\n", encoding="utf-8")
        wrapper.chmod(0o700)
        wrappers.append(wrapper)
    negative = "\n".join((workspace / name).read_text(encoding="utf-8") for name in ("add.py", "multiply.py"))
    controls(assertions.read_text(encoding="utf-8"), negative, docker, image_id, receipts)
    worker = (sys.executable, "-B", str(script), "model-worker",
              "--receipts", str(receipts), "--endpoint", endpoint, "--model", model)
    result = run_loop(Config(workspace, prompt, workspace / "tasks/state.json", worker, *wrappers, 3, 60))
    write_json(output / "result.json", {"exit_code": result, "image": image_id})
    return result


def chapter6(output: Path, endpoint: str, model: str, docker: list[str], image: str, allow_model_code: bool) -> int:
    """Restricted addition task using chapter 6's retry primitive and original assertions."""
    if not allow_model_code:
        raise ValueError("Pass --allow-model-code to execute candidates in Docker")
    image_id = local_image(docker, image)
    output = fresh_directory(output)
    receipts = output / "receipts"
    receipts.mkdir()
    task = json.loads((REPO / "examples/tasks/model_task.json").read_text(encoding="utf-8"))
    write_json(output / "task.json", task)
    assertions = "\n".join(task["assertions"]) + "\n"
    controls(assertions, (FIXTURE / "add.py").read_text(encoding="utf-8"), docker, image_id, receipts)
    started, tokens, attempt = time.monotonic(), 0, 0

    def generate(objective, feedback):
        nonlocal tokens, attempt
        if time.monotonic() - started >= task["max_seconds"] or tokens >= task["max_tokens"]:
            raise RuntimeError("Time or token budget exhausted")
        attempt += 1
        payload = {"model": model, "temperature": 0, "max_tokens": min(1024, task["max_tokens"] - tokens),
                   "messages": [{"role": "system", "content": "Return only def add(a, b) with one arithmetic return expression, plain or fenced."},
                                {"role": "user", "content": objective + "\nFeedback: " + json.dumps(feedback)}]}
        write_json(receipts / f"request-{attempt}.json", payload)
        response = chat(endpoint, payload, timeout=max(1, min(30, int(task["max_seconds"] - (time.monotonic() - started)))))
        write_json(receipts / f"response-{attempt}.json", response)
        usage = response.get("usage") or {}
        counts = [usage.get("prompt_tokens"), usage.get("completion_tokens")]
        if any(type(value) is not int or value < 0 for value in counts):
            raise RuntimeError("Missing valid token usage; cannot enforce token budget")
        tokens += sum(counts)
        if tokens > task["max_tokens"]:
            raise RuntimeError("Token budget exhausted")
        return response["choices"][0]["message"]["content"]

    def check(_objective, content):
        try:
            candidate = normalize_code(content, "add")
        except (ValueError, SyntaxError) as exc:
            return False, {"status": "rejected_syntax", "detail": str(exc)}
        (receipts / f"candidate-{attempt}.py").write_text(candidate, encoding="utf-8")
        if time.monotonic() - started >= task["max_seconds"]:
            return False, {"status": "time_budget_exhausted"}
        result = docker_check(candidate + "\n" + assertions, docker, image_id, receipts)
        if time.monotonic() - started >= task["max_seconds"]:
            return False, {"status": "time_budget_exhausted"}
        return result["status"] == "passed", {key: result.get(key) for key in ("status", "stderr", "receipt")}

    try:
        result = run_until_done(task["objective"], generate, check, task["max_attempts"])
        result.update(state="verified" if result["solved"] else "escalated", action="report_only", tokens=tokens)
    except (OSError, RuntimeError, ValueError, KeyError, IndexError, TypeError) as exc:
        result = {"state": "escalated", "reason": str(exc), "tokens": tokens}
    write_json(output / "result.json", result)
    print(json.dumps(result, indent=2))
    return 0 if result["state"] == "verified" else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    for name in ("ralph", "chapter6"):
        run = commands.add_parser(name)
        run.add_argument("--output", type=Path, required=True)
        run.add_argument("--endpoint", default="http://127.0.0.1:18080/v1/chat/completions")
        run.add_argument("--model", default="loopeng-qwen3-4b")
        run.add_argument("--docker-command", default="docker", help="trusted CLI prefix, shell-split; never executed through a shell")
        run.add_argument("--image", default="python:3.12-slim-bookworm")
        run.add_argument("--allow-model-code", action="store_true")
    gate = commands.add_parser("verify")
    gate.add_argument("kind", choices=("scope", "final"))
    gate.add_argument("config", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.action == "verify":
            return verify(args.kind, args.config)
        driver = demo if args.action == "ralph" else chapter6
        return driver(args.output, args.endpoint, args.model, shlex.split(args.docker_command), args.image, args.allow_model_code)
    except (OSError, ValueError, subprocess.SubprocessError, SyntaxError) as exc:
        print(f"Local demo failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
