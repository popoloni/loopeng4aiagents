# Chapter 6: Choosing the right loop

[All chapters](../README.md) · [Previous: chapter 5](chapter-5.md)

## What to read and what to run

The numbered [book listings](../../Code/) are small pieces of an algorithm.
They are **not complete applications**. For example,
[listing 060](../../Code/listing_060.txt) defines a support loop, but does not
supply a ticket or implementations of retrieval, drafting, checking and billing.

The runnable [casebook](../../loopeng/cases/chapter6.py) supplies complete,
scripted examples. Start there. You need Python 3.10+ only: **no model, Docker,
API key or pip packages**. See [Getting started](../guides/getting-started.md)
if Python is not ready. Run the following from the cloned repository root.

## 1. Start with the customer-support case

```bash
python3 -B -m loopeng cases --case support
```

This simulates a refund request. It retrieves fixture evidence, rejects an
incorrect cancellation timeline, corrects that claim, then hands the refund
recommendation to a billing specialist because autonomous financial authority
is zero. The richer casebook supplements the compact listing with explicit
state and handoff records; it is not simply executing the text file.

The output is JSON. Look under `cases` → `support`:

| Field | What to expect | How to read it |
| --- | --- | --- |
| `attempts` | Failed timeline claim, then a passing correction | Verification affects the next attempt |
| `reasoning_retries` | `1` | One correction was needed |
| `state` | `"escalated"` | Correct human handoff, not a failed program |
| `external_actions` | `[]` | No real refund or customer message |

At the top level, `mode: "offline_fixture"` and
`real_external_side_effects: false` identify this as a simulation.

## 2. Compare approval with completion

```bash
python3 -B -m loopeng cases --case support --support-scenario approved
python3 -B -m loopeng cases --case support --support-scenario unconfirmed
```

The first ends with `state: "resolved"`: simulated human approval **and** a
matching simulated billing confirmation. The second ends with
`state: "awaiting_confirmation"`: approval alone cannot prove a refund happened.
Neither command sends money. All receipts are invented teaching data.

Read the inputs in [fixtures.json](../../examples/chapter6/fixtures.json), under
`support`. Do not run the JSON or the printed listing as a Python script.

## 3. Try one other case at a time

```bash
python3 -B -m loopeng cases --case sql
```

The first query refers to a nonexistent table; SQLite rejects it. The second
uses the supplied schema and passes a separate result check. Look for
`cases.sql.state: "verified"`, `result.attempts: 2`, and actual rows
`[["Ada", 2000], ["Cy", 600]]` (amounts in cents).
The initial failure is intentional; the candidates are scripted, not LLM output.

Use the same command with another case name:

| Case | What it demonstrates |
| --- | --- |
| `checker` | Independent checks reject an answer hardcoded for visible data |
| `memory` | Retrieval filters stale/restricted records and can abstain |
| `data` | Reconcile [payments.csv](../../examples/chapter6/payments.csv) with explicit rules |
| `maintenance` | Triage, CI, dependency and other report-only maintenance decisions |
| `orchestra` | Staged retries/fallbacks still need a real verifier |
| `coordination` | Overlapping loops must yield to one owner |

For example: `python3 -B -m loopeng cases --case data`.
Once individual results make sense, `--case all` runs them together, but prints
much more output. A refusal or handoff can be the correct case outcome.

## 4. Optional: a different demonstration—code repair

```bash
python3 -B -m loopeng engineering --demo
```

This is not the support case. It checks two supplied Python addition candidates:
the first fails an assertion, the second passes. Expect `state: "verified"`,
`attempts: 2`, and `action: "report_only"`. A traceback **inside the first
history entry** is intentional evidence, not an unhandled final crash.

This command executes trusted supplied Python in a subprocess. It is not a
security sandbox: do not replace the candidates with untrusted code on your host.
Its input form is [example_task.json](../../examples/tasks/example_task.json).

## 5. Optional: connect a real LLM

Only after the offline examples, follow the [local-model guide](../guides/local-model.md).
Its restricted chapter 6 arithmetic task runs model-generated code through
Docker checks. It does **not** connect every casebook example to an LLM or
turn the support simulation into a real ticket/billing service.

## Check the examples

```bash
python3 -B -m unittest discover -s tests -p 'test_chapter6_examples.py' -v
python3 -B -m unittest discover -s tests -p 'test_loop_engineering.py' -v
```

Expect `OK` at the end of each run. For the exact mapping of listings 042–060,
other support scenarios and boundaries, use the
[chapter 6 reference](../reference/chapter-6-details.md).
The external course's notebooks, learned models, datasets and measured results
are not reproduced by these offline demonstrations.
