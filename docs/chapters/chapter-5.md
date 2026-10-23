# Chapter 5: Building a full local AI loop

[All chapters](../README.md) · [Previous: chapter 4](chapter-4.md) · [Next: chapter 6](chapter-6.md)

## Choose your starting point

This chapter has three different practical routes. **Start with the first.**

| You want to… | Use | Needs a model? |
| --- | --- | --- |
| Understand retry, resume and stop decisions | This page's offline policy demo | No |
| Try this companion's small local-model tasks | [Local-model guide](../guides/local-model.md) | Yes |
| Install the full stack described in the chapter | [Kowalski Loop](https://github.com/popoloni/kowalski_loop) | Yes |

Kowalski Loop is a separate project by the same author, Enrico Papalini.
It contains the full stack, including the supervisor, routing, compression and
local inference integrations. It is not bundled here. Passing this companion's
tests does not validate that separate installation.

## 1. Run the policy demo

Use Python 3.10+ from the cloned repository root. No LLM, Docker, credentials
or pip packages are needed. See [Getting started](../guides/getting-started.md)
if necessary.

```bash
python3 -B -m loopeng policies --demo
```

The output is a JSON list of five situations. Read each `name` and
`transition.action`:

| Situation | Expected action | Meaning |
| --- | --- | --- |
| `verified_change` | `advance` | The scenario permits moving on |
| `failed_behavior` | `retry_with_evidence` | Try again using the failure evidence |
| `timeout_progress` | `resume` | Continue usable partial work within a separate budget |
| `unauthorized_change` | `halt_for_human` | Checks cannot replace permission |
| `budget_spent` | `escalate` | Stop automatic attempts |

These are **decisions only**. `executed: false` means no rollback, commit,
deployment or repair was carried out. A human halt is a correct result in the
unauthorized scenario, not a broken demo.

## 2. Find the scenario inputs

Open [scenarios.json](../../examples/local_policy/scenarios.json). Each scenario
provides a task, synthetic check results and consumed budgets.

```bash
python3 -B -m loopeng policies --scenarios examples/local_policy/scenarios.json
```

To experiment, save a separate copy and pass its path to `--scenarios`.
The gates are supplied booleans for teaching: `true` is not evidence that a
real project check ran. The implementation is [local.py](../../loopeng/policies/local.py).

## 3. Only then choose a live route

For the small companion workflow, use the [native runtime guide](../guides/local-model.md),
including its explicit Metal option on Apple Silicon and Docker candidate checks.

For the full Kowalski Loop stack, follow its own
[installation guide](https://github.com/popoloni/kowalski_loop/blob/main/INSTALL.md)
and [loop documentation](https://github.com/popoloni/kowalski_loop/blob/main/LOOP.md).
Do not mix that project's commands/configuration with this repository's CLI.
Its runtime requirements and operations belong to that project.

## Check your understanding and the code

```bash
python3 -B -m unittest discover -s tests -p 'test_local_loop_policy.py' -v
```

Expect `OK`. The [policy reference](../reference/chapter-5-details.md) explains
gate order, executor precedence and exact budget rules. For hardware/energy cost
calculations, use [chapter 3's local-cost example](chapter-3.md#3-optional-local-hardware-costs).
