"""Restricted arithmetic worker: model text can replace only add/multiply functions."""
from __future__ import annotations

import argparse
import ast
import difflib
import json
import re
import sys
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

from loopeng.runtime.local_model import external_path, write_json
from loopeng.ralph.controller import read_items


ALLOWED = (ast.Module, ast.FunctionDef, ast.arguments, ast.arg, ast.Return,
           ast.BinOp, ast.Add, ast.Mult, ast.Sub, ast.Name, ast.Load, ast.Constant)


def normalize_code(content: str, name: str) -> str:
    if name not in ("add", "multiply") or not isinstance(content, str) or len(content) > 16384:
        raise ValueError("Invalid candidate name, type or length")
    match = re.fullmatch(r"\s*```(?:python)?\s*\n(.*?)```\s*", content, re.DOTALL | re.IGNORECASE)
    code = (match.group(1) if match else content).strip() + "\n"
    tree = ast.parse(code)
    if len(tree.body) != 1 or not isinstance(tree.body[0], ast.FunctionDef):
        raise ValueError("Expected exactly one function")
    func = tree.body[0]
    args = func.args
    if (func.name != name or func.decorator_list or func.returns or func.type_comment
            or getattr(func, "type_params", []) or args.posonlyargs or args.kwonlyargs
            or args.vararg or args.kwarg or args.defaults or args.kw_defaults
            or [arg.arg for arg in args.args] != ["a", "b"]
            or any(arg.annotation for arg in args.args)
            or len(func.body) != 1 or not isinstance(func.body[0], ast.Return)):
        raise ValueError("Expected undecorated function(a, b) containing one return")
    for node in ast.walk(tree):
        if not isinstance(node, ALLOWED):
            raise ValueError(f"Unsupported syntax: {type(node).__name__}")
        if isinstance(node, ast.Name) and node.id not in ("a", "b"):
            raise ValueError("Only parameter names are allowed")
        if isinstance(node, ast.Constant) and (type(node.value) is not int or abs(node.value) > 10**30):
            raise ValueError("Only bounded integer constants are allowed")
    return code


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Model endpoint redirects are disabled")


def chat(endpoint: str, payload: dict, timeout: int = 30) -> dict:
    url = urllib.parse.urlsplit(endpoint)
    if (url.scheme != "http" or url.hostname not in ("127.0.0.1", "::1")
            or url.username or url.password or url.query or url.fragment
            or url.path != "/v1/chat/completions"):
        raise ValueError("Use a literal loopback HTTP chat-completions endpoint")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    request = urllib.request.Request(endpoint, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with opener.open(request, timeout=timeout) as response:
        raw = response.read(1024 * 1024 + 1)
    if len(raw) > 1024 * 1024:
        raise ValueError("Model response exceeds 1 MiB")
    return json.loads(raw)


def check_workspace(workspace: Path) -> None:
    expected = {"add.py", "multiply.py", "tasks", "tasks/state.json"}
    entries = list(workspace.rglob("*"))
    if workspace.is_symlink() or any(path.is_symlink() for path in entries):
        raise ValueError("Workspace symlinks are forbidden")
    if {p.relative_to(workspace).as_posix() for p in entries} != expected:
        raise ValueError("Workspace inventory changed")
    if not (workspace / "tasks").is_dir() or any(not (workspace / p).is_file() for p in ("add.py", "multiply.py", "tasks/state.json")):
        raise ValueError("Unexpected workspace file types")
    items = read_items(workspace / "tasks/state.json")
    if [name for name, _ in items] != ["add", "multiply"]:
        raise ValueError("Task inventory changed")


def work(workspace: Path, receipts: Path, endpoint: str, model: str, prompt: str) -> int:
    check_workspace(workspace)
    receipts = external_path(receipts)
    if receipts.is_relative_to(workspace.resolve()) or workspace.resolve().is_relative_to(receipts):
        raise ValueError("Receipts must be separate from the worker workspace")
    if not receipts.is_dir() or receipts.is_symlink():
        raise ValueError("Receipts must be an existing real directory")
    state_path = workspace / "tasks/state.json"
    state_before = state_path.read_text(encoding="utf-8")
    state = json.loads(state_before)
    item = next((item for item in state["items"] if item["status"] == "pending"), None)
    if item is None:
        return 0
    name = item["id"]
    path = workspace / (name + ".py")
    before = path.read_text(encoding="utf-8")
    receipt = receipts / ("worker-" + uuid.uuid4().hex)
    receipt.mkdir()
    payload = {"model": model, "temperature": 0, "max_tokens": 1024,
               "messages": [{"role": "system", "content": "Return only the requested Python function, plain or fenced. No tools."},
                            {"role": "user", "content": prompt + "\nCurrent item: " + name + "\nCurrent code:\n" + before}]}
    write_json(receipt / "request.json", payload)
    (receipt / "state-before.json").write_text(state_before, encoding="utf-8")
    try:
        response = chat(endpoint, payload)
        write_json(receipt / "response.json", response)
        code = normalize_code(response["choices"][0]["message"]["content"], name)
        (receipt / "candidate.py").write_text(code, encoding="utf-8")
        (receipt / "diff.patch").write_text("".join(difflib.unified_diff(before.splitlines(True), code.splitlines(True), fromfile=name + ".py.before", tofile=name + ".py.after")), encoding="utf-8")
        # Recheck after the HTTP call before any mutation; no model-directed paths.
        check_workspace(workspace)
        if state_path.read_text(encoding="utf-8") != state_before or path.read_text(encoding="utf-8") != before:
            raise ValueError("Workspace changed during request")
        path.write_text(code, encoding="utf-8")
        item["status"] = "done"
        write_json(state_path, state)
        write_json(receipt / "state-after.json", state)
        print(json.dumps({"item": name, "receipt": str(receipt), "usage": response.get("usage")}))
    except Exception as exc:
        write_json(receipt / "failure.json", {"error_type": type(exc).__name__, "message": str(exc)[:500]})
        raise
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipts", type=Path, required=True)
    parser.add_argument("--endpoint", default="http://127.0.0.1:18080/v1/chat/completions")
    parser.add_argument("--model", default="loopeng-qwen3-4b")
    args = parser.parse_args(argv)
    try:
        return work(Path.cwd(), args.receipts, args.endpoint, args.model, sys.stdin.read())
    except (OSError, ValueError, KeyError, IndexError, TypeError, SyntaxError) as exc:
        print(f"Restricted worker refused candidate: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
