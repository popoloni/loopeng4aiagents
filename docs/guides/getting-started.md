# Install and run the companion

[Home](../../README.md) · [Chapter coverage](../reference/coverage.md) · [Local-model setup](local-model.md)

## What is included

This repository includes runnable Python, synthetic example inputs, independent
tests, policy/governance templates and local-runtime setup tools. It does not
include model weights, native server binaries, Docker, Python itself, paid
provider credentials or the external course/framework installations described
in the book. The optional runtime tool obtains pinned public artifacts only
with explicit download consent. No sibling repository is required.

Start offline. Every offline example uses the Python standard library and
requires **Python 3.10 or newer**. The development validation uses Python 3.12;
this is not a certification of every future Python release. Git is needed by
the worktree tests; Bash is needed for the shell launcher/asset check. The
documented local-model path targets native macOS ARM64 or Linux x86-64;
generated candidate checks additionally need Docker.

## 1. Clone and select Python

```bash
git clone https://github.com/popoloni/loopeng4aiagents.git
cd loopeng4aiagents
python3 --version
git --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip check
```

Use a fresh virtual environment, not an existing directory with unrelated
dependencies. No `pip install` is needed for the runnable code. On Windows,
use the environment's Python executable or PowerShell activation instead of
`source`; Bash and the local native-model route require their own compatible
environment and are not established by this macOS validation.

Run all commands below from the repository root. Keep generated outputs outside
the checkout. Set `PYTHONDONTWRITEBYTECODE=1` if you prefer no bytecode caches;
on macOS `TMPDIR=/private/tmp` gives canonical temporary paths.

## 2. Verify the installation before using a model

```bash
python -B scripts/check.py
```

The offline gate runs unit tests, local documentation links, the asset inventory,
and every canonical offline demo. It installs no packages and downloads nothing.
Tests use mocks and synthetic fixtures by default; they do not start a model,
download packages, contact a paid API or authorize deployment. A passing unit
suite is not proof that your optional native runtime is installed correctly.

## 3. Choose a runnable chapter

| Chapter | Command / material | What to inspect |
| --- | --- | --- |
| 1: foundations | [Contract templates](../../examples/governance/) | Durable intent, evidence, authority, budgets and escalation |
| 2: organization | [Ownership/evidence templates](../../examples/governance/) | Fill real accountable owners and decisions; examples do not grant approval |
| 3: economics | `python -B -m loopeng economics --demo` | Cost per accepted outcome, retry routing, capacity and verifier leverage |
| 4: Ralph | `python -B -m loopeng ralph --demo` | Two fresh worker processes, persistent task state and independent final check |
| 5: policies | `python -B -m loopeng policies --demo` | Executor precedence, fail-fast gates, retry/resume and human halt |
| 6: use cases | `python -B -m loopeng cases --case all` | SQL, retrieval, data analysis, maintenance workflows, orchestration, coordination and support |

For details, see [chapter 3](../chapters/chapter-3.md), [chapter 4](../chapters/chapter-4.md),
[chapter 5](../chapters/chapter-5.md), and
[chapter 6](../chapters/chapter-6.md). The economics scenario represents hypothetical
manuscript inputs, not current API prices, measured savings or financial advice.

Additional canonical examples:

```bash
python -B -m loopeng engineering --demo
python -B -m loopeng engineering --task examples/tasks/example_task.json
python -B -m loopeng cases --case support
```

An offline example can exit 0 while reporting an intentional refusal, failed
candidate or human handoff. That means the demonstration ran correctly; read
its structured result rather than equating the process exit with acceptance.
The baseline code-repair demo deliberately rejects its first supplied candidate.
Offline replay is not model-generated work.

## 4. Optional: run against your local LLM

Follow [local-model guide](local-model.md) for exact commands to:

1. Create an external runtime from verified existing artifacts or explicitly
   download the pinned native server/model.
2. Check hashes, architecture and prerequisites.
3. Start the bounded loopback server, with Metal on Apple Silicon.
4. Run the shipped local-model examples and protected checks.
5. Preserve receipts, inspect failures, and stop only your owned processes.

Do not execute arbitrary generated code on a sensitive host. Python's isolated
mode and a subprocess timeout are not a security sandbox. The supplied restricted
live examples use an additional Docker execution boundary, and still do not
establish general production security.

The [earlier validation report](../validation/local-model.md) describes the first
external-harness experiment. The new setup guide documents the portable shipped
tools; keep those observations distinct.

## 5. Review and extend deliberately

- Copy scenario fixtures to a new path rather than changing the book's baseline.
- Keep independent checks outside a model's writable project.
- Record prompt, model/server versions, limits, actual results and interventions.
- Stop on scope violations or exhausted budgets; do not retry until prose says success.
- Do not replace missing business approval with a fixture's simulated approval.
- Use [coverage audit](../reference/coverage.md) for the distinction between
  executable examples, templates, external integrations and manuscript review notes.

The numbered [Code/ listings](../../Code/) are preserved excerpts. Do not execute
all of them as a shell script or assume they collectively install the external
stack. The tested reference entry points are listed above.

## If a command does not work

- **“No module named loopeng”:** your terminal is probably outside the repository.
  Change into the cloned `loopeng4aiagents` folder, which contains `loopeng/`,
  `examples/` and `README.md`, then retry. Do not try to fix this by installing an
  unrelated package with pip.
- **“python3: command not found”, or a version below 3.10:** install/select a
  compatible Python interpreter before continuing; an LLM server is not the fix.
- **Lots of JSON:** that is the normal report format. Start with one case and use
  its chapter walkthrough to identify the important fields.
- **A failed attempt inside a report:** check the final state. Several examples
  deliberately reject an initial candidate or hand off to a human. A final
  command traceback or nonzero test exit is different and needs investigation.
- **Unsure which command to choose:** use the [chapter walkthroughs](../README.md#chapters).
  A printed listing is not necessarily a standalone program.

## Earlier checkouts

The old `src/` aliases and duplicate fixtures have been removed. Use
`python -m loopeng` and task inputs in [examples/tasks/](../../examples/tasks/).
The historical reports retain the exact command paths used in those observations.
