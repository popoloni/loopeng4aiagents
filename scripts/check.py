"""One offline validation entry point; no downloads, model calls or installations."""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def check_duplicates(root: Path) -> list[list[str]]:
    """Reject identical nonempty maintained files; caches and Git are excluded."""
    paths = [p for p in root.iterdir() if p.is_file() and not p.name.startswith(".")]
    for folder in ("loopeng", "examples", "tests", "scripts", "docs", "Code", "Equations", "imgs"):
        paths.extend(p for p in (root / folder).rglob("*") if p.is_file()
                     and "__pycache__" not in p.parts and not p.name.startswith("."))
    groups = {}
    for path in paths:
        content = path.read_bytes()
        if content:
            groups.setdefault(hashlib.sha256(content).hexdigest(), []).append(str(path.relative_to(root)))
    return [sorted(paths) for paths in groups.values() if len(paths) > 1]


def check_links(root: Path) -> list[str]:
    """Check local Markdown/HTML targets, excluding fenced examples and URLs.

    This checks file existence, not remote URLs or heading-anchor semantics.
    """
    files = list(root.glob("*.md"))
    for folder in ("docs", "examples", "loopeng"):
        files.extend((root / folder).rglob("*.md"))
    errors = []
    for path in sorted(files):
        body = re.sub(r"```.*?```|~~~.*?~~~", "", path.read_text(encoding="utf-8"), flags=re.S)
        targets = re.findall(r"\]\((<[^>]+>|[^)]+)\)", body)
        targets += re.findall(r'(?:src|href)=[\"\']([^\"\']+)[\"\']', body)
        for target in targets:
            target = target.strip()
            if target.startswith("<"):
                target = target[1:target.index(">")]
            else:
                target = target.split(' "', 1)[0].split(" '", 1)[0]
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            resolved = path.parent / unquote(parsed.path)
            if not resolved.exists():
                errors.append(f"{path.relative_to(root)}: missing {target}")
    return errors


def example_commands() -> list[list[str]]:
    commands = [
        ["economics", "--demo"],
        ["economics", "--scenario", "examples/economics/chapter3.json"],
        ["economics", "--local-tco-demo"],
        ["policies", "--demo"],
        ["policies", "--scenarios", "examples/local_policy/scenarios.json"],
        ["cases", "--case", "all"],
        ["ralph", "--demo"],
        ["engineering", "--demo"],
        ["engineering", "--task", "examples/tasks/example_task.json"],
        ["runtime", "pins"],
    ]
    return [[sys.executable, "-B", "-m", "loopeng", *args] for args in commands] + [
        [sys.executable, "-B", "-m", "examples.economics.local_tco"],
        ["bash", "scripts/ralph", "--demo"],
    ]


def run_command(command: list[str], root: Path = ROOT) -> bool:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHON_BIN=sys.executable)
    try:
        result = subprocess.run(command, cwd=root, env=env, capture_output=True,
                                text=True, timeout=120, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"FAIL {' '.join(command)}: {exc}", flush=True)
        return False
    print(f"{'PASS' if result.returncode == 0 else 'FAIL'} {' '.join(command)}", flush=True)
    # Keep the unittest count visible, and preserve diagnostics for every failure.
    if result.returncode or "unittest" in command:
        print(result.stdout, end="")
        print(result.stderr, end="")
    return result.returncode == 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checks", nargs="+", choices=("tests", "links", "duplicates", "assets", "examples"),
                        default=["tests", "links", "duplicates", "assets", "examples"])
    args = parser.parse_args(argv)
    outcomes = []
    if "tests" in args.checks:
        outcomes.append(run_command([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-v"]))
    if "links" in args.checks:
        errors = check_links(ROOT)
        print("\n".join(errors) if errors else "PASS local documentation links")
        outcomes.append(not errors)
    if "assets" in args.checks:
        outcomes.append(run_command(["bash", "scripts/check-assets.sh"]))
    if "duplicates" in args.checks:
        duplicates = check_duplicates(ROOT)
        print(f"FAIL duplicate files: {duplicates}" if duplicates else "PASS no identical nonempty maintained files")
        outcomes.append(not duplicates)
    if "examples" in args.checks:
        outcomes.extend(run_command(command) for command in example_commands())
    passed = all(outcomes)
    print(f"{'PASS' if passed else 'FAIL'} offline validation ({sum(outcomes)}/{len(outcomes)} checks)")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
