"""Single entry point for the repository's existing commands."""
import argparse
from importlib import import_module
import sys
from pathlib import Path

# Owned subprocesses invoke this entry point from isolated workspaces.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

COMMANDS = {
    "economics": "loopeng.economics.calculations",
    "policies": "loopeng.policies.local",
    "cases": "loopeng.cases.chapter6",
    "ralph": "loopeng.ralph.controller",
    "runtime": "loopeng.runtime.local_model",
    "live": "loopeng.runtime.live",
    "engineering": "loopeng.engineering",
    "model-worker": "loopeng.ralph.model_worker",
    "demo-worker": "loopeng.ralph.demo_worker",
}


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=COMMANDS)
    # Each existing parser owns all arguments following the command.
    command = parser.parse_args(args[:1]).command
    return import_module(COMMANDS[command]).main(args[1:])


if __name__ == "__main__":
    raise SystemExit(main())
