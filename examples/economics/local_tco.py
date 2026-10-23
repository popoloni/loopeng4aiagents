"""Run from the repository root: python -B -m examples.economics.local_tco.

All non-hardware inputs are invented illustrative assumptions. Project
accounted token events cannot be compared directly with API-billed tokens.
"""
from loopeng.economics.calculations import main


if __name__ == "__main__":
    raise SystemExit(main(["--local-tco-demo"]))
