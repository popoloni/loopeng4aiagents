# Chapter 4: The Ralph loop

[All chapters](../README.md) · [Previous: chapter 3](chapter-3.md) · [Next: chapter 5](chapter-5.md)

## What you will run

A controller that gives a worker one task item at a time, retains progress and
checks completion. Start with the **offline demonstration**: its worker is
scripted, not an LLM.

You need Python 3.10+ and a Unix-style shell (as on macOS/Linux) for this demo's
verifier scripts. No model, Docker or API key.
Use [Getting started](../guides/getting-started.md) if Python is not ready.
Open a terminal in the cloned repository root.

## 1. Run the demonstration

```bash
python3 -B -m loopeng ralph --demo
```

Expect:

```text
Ralph iteration 1/3
Completed item first
Ralph iteration 2/3
Completed item second
COMPLETE: all items and controller checks passed.
```

The controller starts a fresh worker process for each item. It reads the saved
task state between iterations and runs the final verifier before accepting
completion. The demo uses a temporary workspace that is cleaned up afterward;
it does not edit your project or leave a finished application to open.

## 2. Understand the pieces

| Piece | File to read | Role |
| --- | --- | --- |
| Controller | [controller.py](../../loopeng/ralph/controller.py) | Applies iteration/time bounds and invokes checks |
| Offline worker | [demo_worker.py](../../loopeng/ralph/demo_worker.py) | Completes the demonstration's scripted items |
| Prompt template | [ralph_prompt.md](../../examples/tasks/ralph_prompt.md) | Instructions for a worker you supply |
| State template | [ralph_state.example.json](../../examples/tasks/ralph_state.example.json) | Ordered task IDs and pending/done status |

The printed [listings 002–019](../../Code/) explain patterns; they are not a
complete installation. Use the command above rather than pasting fragments
together.

A worker saying “done” is not sufficient. The controller requires valid state,
scope verification and a successful final check. However, the offline demo's
scope verifier is a success stub: it teaches the lifecycle, not real project
scope enforcement.

## 3. Optional: use a real local model

Follow the [local-model guide](../guides/local-model.md). Its restricted Ralph
task supplies a real scope checker and independent arithmetic assertions.
It requires a separately prepared native server/model and Docker for candidate
execution. Those prerequisites are unnecessary for the offline demo.

For a custom project, you must supply a worker and two real verifiers. The CLI's
`--help` lists the options:

```bash
python3 -B -m loopeng ralph --help
```

Keep the state inside the worker workspace, but the prompt and verifiers outside
it. The controller is not an OS sandbox, does not prove each item correct before
the final check, and does not automatically commit or roll back changes.

## Check the controller

```bash
python3 -B -m unittest discover -s tests -p 'test_ralph_loop.py' -v
```

Expect `OK` at the end. A nonzero worker/check exit in your own task is a failure
to investigate, not permission to disable the check. See the
[coverage reference](../reference/coverage.md#chapter-4--the-ralph-loop) for the
differences between the printed patterns and the runnable controller.
