"""Deterministic sample worker; the controller starts this afresh per item."""

import argparse
import json
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    _prompt = sys.stdin.read()
    state_path = Path("tasks/state.json")
    state = json.loads(state_path.read_text(encoding="utf-8"))
    for item in state["items"]:
        if item["status"] == "pending":
            item["status"] = "done"
            result = Path("result.txt")
            previous = result.read_text(encoding="utf-8") if result.exists() else ""
            result.write_text(previous + ("," if previous else "") + item["id"], encoding="utf-8")
            state_path.write_text(json.dumps(state), encoding="utf-8")
            print(f"Completed item {item['id']}")
            return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
