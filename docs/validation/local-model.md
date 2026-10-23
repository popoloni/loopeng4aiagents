# Local-model validation: chapters 4 and 6

[Home](../../README.md) · [Chapter 6 notes](../chapters/chapter-6.md) · [Asset guide](../reference/assets.md)

For the now-shipped installation and commands, start with
[Getting started](../guides/getting-started.md) and [Local model setup](../guides/local-model.md).
All commands, paths, test counts and outcomes below record pre-refactor runs; they are historical evidence, not current installation instructions or new refactor results. The original experiment below is retained as history. See the
[shipped-workflow validation](#shipped-workflow-and-expanded-companion-validation)
for the subsequent implementation and checks.

## Scope and result

Validated on 23 October 2026 against source commit
`54e04308729843774a470e829af521d7aa9a97fb`, using Python 3.12.4 on macOS
ARM64 and the existing native Metal model runtime. No model downloads or package
installations were needed. The controllers and their tests were not modified.

| Check | Observed result |
| --- | --- |
| Unit tests | 32 passed |
| Chapter 6 offline demo | Exit 0; wrong replay candidate rejected, next candidate accepted |
| Chapter 6 example task | Exit 0 |
| Chapter 4 Python demo | Exit 0; two worker processes and final checks passed |
| Chapter 4 Bash demo | Exit 0 |
| Asset inventory | 60 listings, 24 equations, six chapter figure directories, ten chapter 6 figures |
| Chapter 6 live local model | Verified on first attempt; supplied two assertions passed |
| Chapter 6 independent candidate review | Four additional checks passed: zero, two negatives, mixed signs and large integers |
| Chapter 4 initial live bridge | Three responses rejected for missing Markdown fences; budget exhausted, state preserved |
| Chapter 4 corrected external bridge | Two fresh workers completed two items; scope and eight final assertions passed |

These are small local reference tasks, not a reproduction of the external course,
a general model benchmark, or evidence that every illustrative listing is an
executable application. Chapter 5's numbered excerpts are not a bundled runnable
local stack. No remote provider, production task, human approval, merge or push
was involved.

## Reused runtime

- Server: verified llama.cpp b11799, Darwin ARM64, commit `0756e83fc`.
- Model: Qwen3-4B Q4_K_M, 2,497,280,256 bytes, SHA-256
  `7485fe6f11af29433bc51cab58009521f205840f5b4ae3a32fa7f92e8534fdf5`.
- Server executable SHA-256:
  `981b460a278e9a0c880cef32d6fab42785a119084456b16845304cf38c32cf69`.
- Loopback chat-completions endpoint:
  `http://127.0.0.1:18080/v1/chat/completions`; served alias `esa-qwen3-4b`.
- Native Metal GPU layers 99; context 16,384; q8_0 K/V caches;
  six threads; batch 256/microbatch 128.
- Model-facing requests used temperature 0 and a 1,024-token output limit.
- Existing Python environment:
  `/Users/enricopapalini/local_repos/esa_ai_test_env`.
- Existing runtime:
  `/Users/enricopapalini/local_repos/esa_ai_native_runtime_darwin_01`.

The last two paths identify this workstation, not bundled dependencies.
This repository's Python code requires only the standard library. OpenCode
was not used in this observation: chapter 6 has its own HTTP adapter and chapter 4
used an external restricted HTTP worker.

The class and CLI options retain the name vLLM, but the observed llama.cpp
chat-completions response was compatible for this task. This does not establish
compatibility with all OpenAI-compatible servers or optional protocol features.

## Execution isolation and evidence

The repository's ordinary candidate subprocess is **not a security sandbox**.
For this audit an external harness intercepted chapter 6's candidate subprocess,
recorded HTTP requests/responses, and sent the same generated source plus
assertions to a disposable Docker Python container. The repository's source,
generation logic and assertions were unchanged, but this was an **instrumented
CLI run**, not the default host-execution environment.

Candidate containers used no host mounts, networking disabled, a read-only root
filesystem, an unprivileged user, all capabilities dropped, no-new-privileges,
32 PIDs, 128 MiB RAM and one CPU. Container execution was bounded and exact owned
containers were removed afterward. Docker is an additional isolation layer, not
a claim of protection against every kernel/container escape.

The existing `python:3.12-slim-bookworm` image was reused without pulling.
It was amd64 on an ARM64 Docker host, producing an architecture warning; only
these tiny candidate checks used that image. **Inference ran natively with Metal,
not under x86 emulation.** The model server and trusted controller/bridge ran on
the host. The bridge accepted only narrowly checked function syntax and wrote
only named files in a disposable workspace.

## Chapter 6: actual model output

The original [model task](../../examples/tasks/model_task.json) asked for integer addition,
with at most three attempts, 90 seconds and a 5,000-token budget. Its verifier
kept the two original assertions. The model returned a complete addition function;
the CLI reported `state=verified`, `attempts=1`, `action=report_only`.
Reported usage was 66 prompt tokens and 17 completion tokens.

No replay candidate or reference implementation was substituted. A successful
HTTP call alone was not counted as success: the generated code executed against
the original assertions.

A separate review ran four additional integer cases (zero, two negatives, mixed
signs and a large integer) against the captured candidate and passed all four.
The supplied two-case task was not changed.

## Chapter 4: actual workers and the retained failure

At the time of this original audit, Ralph had no bundled live-model worker. This audit supplied an external bridge
for a deliberately small two-item task: implement addition, then multiplication.
The bridge read the current pending item, made a real model call, structurally
checked its output, wrote the allowed function file and marked exactly that item
done. The controller independently checked file scope and final behavior.

The first bridge required Markdown fences. All three model responses contained
plain Python instead. They were refused before changing state; Ralph returned
`BUDGET_EXHAUSTED` with exit 1. This was a response-format integration failure,
not an observed arithmetic failure or a controller defect.

A separately retained bridge revision accepted either a fenced block or the
entire plain response, subject to the **same** Python AST allowlist and exact
function signature. Mixed prose or unsupported syntax remained rejected.
The original bridge, requests/responses and failure were retained.

A new workspace with the same task and checks then passed in two fresh worker
processes. Each response reported 91 prompt tokens and 12 completion tokens.
The controller verified only the declared files were present, the state item
inventory was unchanged and no symlinks appeared. Its protected final verifier
ran eight assertions spanning positive/negative values, zero and a large integer.
The controller reported `COMPLETE: all items and controller checks passed.`

There was no manual repair of generated function bodies, no deterministic
fallback and no weakening of verifier assertions. The bridge's AST restrictions
are specific to these simple functions; they are not a general-purpose coding agent.

## Historical baseline commands

From the repository root, with Python 3.12 selected for matching this observation:

```bash
export PYTHONDONTWRITEBYTECODE=1
export TMPDIR=/private/tmp  # macOS; /tmp on Linux
python3 -B -m unittest discover -s tests -v
python3 -B src/loop_engineering.py --demo
python3 -B src/loop_engineering.py --task src/example_task.json
python3 -B src/ralph_loop.py --demo
bash src/ralph.sh --demo
bash scripts/check-assets.sh
```

To create a separate Python environment on a fresh host, use an approved Python
3.12 installation and `python3.12 -m venv ../loopeng_env`, then activate it.
No pip installation is required for these checks. Do not overwrite an existing
environment or copy a macOS venv into Linux.

## Historical live-run commands

Start your verified local server separately and check health before the task.
On the original workstation, the existing ESA launcher can be reused with a
**new** evidence directory:

```bash
python3 -B ../esa_ai/practice/native_client/run_local_model_d8.py \
  --runtime-root ../esa_ai_native_runtime_darwin_01 \
  --server-binary ../esa_ai_native_runtime_darwin_01/llama_cpp/llama-b11799/llama-server \
  --n-gpu-layers 99 --ctx-size 16384 \
  --cache-type-k q8_0 --cache-type-v q8_0 \
  --threads 6 --batch-size 256 --ubatch-size 128 \
  --max-runtime-seconds 2400 --shutdown-grace-seconds 10 \
  --evidence ../loopeng_server_NEW
```

This command depends on sibling installations and is not a dependency bundled
in this repository. For another host, provide your own verified runtime paths.

The native chapter 6 interface is:

```bash
python3 -B src/loop_engineering.py --task src/model_task.json \
  --vllm-model esa-qwen3-4b \
  --vllm-endpoint http://127.0.0.1:18080/v1/chat/completions \
  --allow-model-code
```

**Do not run that default command on a sensitive host:** it executes generated
Python without isolation. Use an isolated environment you control, or inspect and
reuse the recorded external Docker harness. The direct command above documents
the repository interface; the audit additionally set `PYTHONPATH` to its external
`sitecustomize.py` instrumentation and a receipt directory. Do not accidentally
leave that audit-specific `PYTHONPATH` active for unrelated Python programs.

For Ralph, prepare a fresh disposable state/workspace and supply your own worker,
prompt, scope verifier and final verifier through the [documented CLI](../chapters/chapter-4.md).
Keep prompt/verifiers outside the worker workspace. A worker's done claim must
not replace executable final checks. The retained worker and commands below
show precisely what was used; copying an old completed state is not a fresh run.

## Retained local packet and limits

Durable audit packet on the original workstation:
`/Users/enricopapalini/local_repos/loopeng4aiagents_validation_01/`.

It contains the external harness, chapter 6 request/response and candidate,
initial and retry Ralph workspaces, worker/verification receipts, source hashes,
runtime identities, launch/shutdown evidence and summary. These are local
artifacts, not files shipped by this Git repository. The original baseline logs
were recorded at `/private/tmp/loopeng-baseline.ykQlg3/`.

Both owned model-server launches finished with exit 0 after SIGTERM. No further
inference is needed for this audit. The Python fact-grounded procedure separated
the observed external-bridge parsing failure from the unchanged controllers;
no repository implementation fix was justified by these checks.

Review the packet's exact commands and versions before replay; create new output
paths and pending states, and never overwrite failed evidence. Stop only the
owned server and verify its finish receipt and cleared port. Do not infer an
automatic commit, merge, deployment or human acceptance from passing checks.

The scope is the two controllers, supplied offline demonstrations, repository
unit tests/assets, and small live arithmetic tasks. The other chapter 6 patterns
were unit-tested, not each exercised against a model or external production
service. Repeated success rates, complex repository editing, cost economics,
learned embeddings, course notebook reproduction and production security remain
unestablished.

## Shipped-workflow and expanded companion validation

Later on 23 October 2026, the companion gained its own runtime setup/launcher,
restricted HTTP worker, Docker-backed live driver, chapter 3 economic model,
chapter 5 policy examples, chapter 6 casebook and governance worksheets. These
are new working-tree additions after the commit identified above, not features
of that historical commit. No commit or push was performed for this addition.

### Clean-environment checks

A new Python 3.12.4 virtual environment with no project packages installed ran
a copied checkout outside the repository, without its Git metadata or caches:

| Check | Observed result |
| --- | --- |
| Full unit/integration suite | 115 tests passed in 2.838 seconds |
| Chapter 3 demo and JSON scenario | Exit 0; reproduced the worked numerical values documented in [chapter 3](../chapters/chapter-3.md) |
| Local TCO CLI and module example | Both exit 0 |
| Chapter 5 demo and scenario-file modes | Both exit 0; decisions are report-only |
| Chapter 6 all-case runner and support case | Both exit 0; synthetic fixtures and expected refusals/handoffs |
| Ralph Python and Bash demonstrations | Exit 0 |
| Existing chapter 6 demo and example task | Both exit 0 |
| Runtime pins | Exit 0, no network |
| Fresh runtime setup using retained archive/model, then preflight | Exit 0; native archive extracted to a new external directory and model reused in place |
| Documentation links / JSON inputs / Python 3.10 syntax parsing | Passed; syntax parsing is not a Python 3.10 runtime test |
| Asset inventory / editor diagnostics / whitespace check | Passed |

No model, package or container image was downloaded for these checks. Download
handling has offline tests, but a new reader's network download and Linux
inference route were not exercised in this validation.

### Live commands included at the time of the shipped-workflow validation

The shipped [launcher](../../loopeng/runtime/local_model.py) served the retained, verified
b11799 Darwin ARM64 binary and Qwen weights with Metal 99, alias
`loopeng-qwen3-4b`, context 16,384 and q8_0 K/V. The shipped
[driver](../../loopeng/runtime/live.py) ran both commands against that server:

- **Ralph:** two fresh model workers completed `add` and `multiply`; scope and
  all eight final arithmetic assertions passed; controller exit 0.
- **Chapter 6:** the restricted addition task passed on attempt 1, using the
  original two task assertions; reported usage was 71 tokens; state `verified`,
  action `report_only`.
- Both routes first passed a known-good arithmetic control and required an
  actual `AssertionError` from their defective fixture. A missing Docker image,
  daemon failure or timeout cannot count as a valid negative control.
- The owned server stopped on signal with exit 0 after 32.371 seconds; the
  validation owner confirmed no listener on port 18080 and no owned containers.

The chapter 6 command is a **restricted adaptation** using the existing retry
primitive, a narrow arithmetic prompt/AST policy and original assertions. It
does not exercise the original `VLLMGenerator` unchanged. The original CLI's
host execution remains unchanged. This new safe route does not turn all chapter
6 examples into live-model experiments or strengthen two assertions into a
general correctness proof.

Candidate checks used the already-installed immutable image
`sha256:3c4d812a6efe003770aafbdba65f9c1960ba8234ab23a133934205a70bdcda77`.
That image is amd64 and emitted an architecture warning on the ARM64 Docker
host; only tiny candidate checks used it. Inference remained native Metal.
No generated candidate was manually repaired, and no assertion was weakened.

Live receipts are retained on the validation workstation under
`/Users/enricopapalini/local_repos/loopeng4aiagents_shipped_validation_01/`
(`ralph`, `chapter6`, `server`). Clean-environment logs and the independent fresh
setup check are under `/private/tmp/loopeng-expanded-validation.5bUxxR/`.
These evidence locations are not runtime dependencies. A reader needs only
this repository and the explicitly documented external prerequisites.

The Python fact-grounded procedure informed the input checks, negative tests,
clean-environment execution and separation of measured outcomes from synthetic
examples. Consult [chapter coverage](../reference/coverage.md) for remaining external
integrations and manuscript editorial findings; the manuscript and original
numbered excerpts were not rewritten.

## Additional retained live-run details

In the recorded pre-refactor validation on 23 October 2026, both shipped commands passed against one owned native Darwin
ARM64 b11799 server with `--metal`, reusing the pinned model. Both positive
controls passed and both negative controls produced actual `AssertionError`s.
Ralph completed two fresh workers and all eight final assertions (144 reported
tokens per worker). Chapter 6 passed its original two assertions on the first
attempt (71 reported tokens). The server exited 0 after Ctrl-C, the port had no
listener, and no owned candidate containers remained. Default server verbosity
did not emit per-layer offload diagnostics: this run records the requested Metal
configuration without independently measuring GPU acceleration. The reused
Python container image was Linux amd64 on an ARM64 Docker host and emitted an
architecture warning; inference ran natively.

The external packet named `loopeng4aiagents_shipped_validation_01` on the
validation workstation retains `server/`, `ralph/` and `chapter6/` receipts. It
is not a runtime dependency or bundled benchmark. These arithmetic checks do not
establish general code generation quality, repeated success rates or Linux
inference performance.
