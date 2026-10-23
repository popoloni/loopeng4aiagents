# Chapter 3: Economics of loop engineering

[All chapters](../README.md) · [Previous: chapter 2](chapter-2.md) · [Next: chapter 4](chapter-4.md)

## What you will run

A calculator for the book's worked economic case: context costs, accepted
outcomes, bounded retries, capacity and verification value.
It uses **hypothetical inputs**, not current prices or measured savings.

You need Python 3.10+ only. No LLM, Docker, API key or pip packages.
If Python is not ready, follow [Getting started](../guides/getting-started.md).
Open a terminal in your cloned `loopeng4aiagents` folder; all commands below
run from that repository root.

## 1. Run the worked case

```bash
python3 -B -m loopeng economics --demo
```

The output is JSON: named fields containing the calculation results.
Start with `manuscript_display`; you do not need to understand every field yet.

| Field | Expected value | Meaning |
| --- | --- | --- |
| `context_costs.full` | `"9.72"` | Full replay under the supplied assumptions |
| `context_costs.compact` | `"3.42"` | The case's compacted-context calculation |
| `context_costs.fresh` | `"2.94"` | The case's fresh-context calculation |
| `accepted_cost` | `"188.24"` | Candidate cost 128 divided by acceptance probability 0.68 |
| `retry_costs` | `["350.00", "232.50", "181.88", "142.28", "144.75"]` | Expected costs for zero through four autonomous attempts |

The fourth attempt increases cost in this scenario. That is the lesson:
more retries are not automatically better. Decimal outputs are strings to
preserve precision; quotation marks are intentional, not an error.

## 2. Find the inputs

Open [chapter3.json](../../examples/economics/chapter3.json).
Run that complete input directly:

```bash
python3 -B -m loopeng economics --scenario examples/economics/chapter3.json
```

This mode evaluates the supplied scenario; the demo also adds introductory
calculations and the rounded `manuscript_display` summary.

To explore alternatives, save a copy outside the repository and pass its path
with `--scenario`. Change one input at a time and update its assumptions.
Keep every required field; unknown keys, invalid probabilities and missing
values are rejected. Inputs use JSON numbers, not quoted numeric strings.

## 3. Optional: local hardware costs

```bash
python3 -B -m loopeng economics --local-tco-demo
```

Look for `monthly_fixed_display: "69.44"`: 2,500 spread over 36 months.
Other inputs are illustrative. This is arithmetic, not a measurement of your
machine or proof that local inference is cheaper.

## Check the implementation

```bash
python3 -B -m unittest discover -s tests -p 'test_economics.py' -v
```

A successful test run ends with `OK`. Tests validate calculations and input
rules, not the truth of business assumptions.

The implementation is [calculations.py](../../loopeng/economics/calculations.py).
For all equations, rounding rules, sensitivity results and unresolved manuscript
assumptions, use the [detailed economics reference](../reference/chapter-3-details.md).
Do not add separate context and retry illustrations to an already complete
cost ledger: they are different views, not automatically additive costs.
