# Portable local model and restricted chapter 4/6 examples

This repository supplies its own Python 3.10+ standard-library setup, launcher,
HTTP worker and command driver. No ESA checkout, OpenCode, pip package or sibling
Python environment is required. Run commands from the repository root with your
own Python interpreter. The setup supports native macOS ARM64 and Linux x86-64;
Windows, Linux ARM64 and CUDA configurations are not supplied.

The trusted controller and model server run on the host. Generated candidates
execute only in Docker in this example. Docker must already be installed and
running, and a suitable Python image must already exist locally. Nothing is
installed or pulled automatically by the driver. Linux's release binary may
require the distribution's OpenMP library (`libgomp.so.1`); missing system
libraries must be addressed separately using that system's approved setup.

## First-time prerequisites

First complete the [Python virtual-environment setup](getting-started.md).
Activate that environment in **each** terminal used below. The offline examples
need no pip packages; Docker is needed only for these live candidate checks.

If Docker is absent, follow the official [macOS installation guide](https://docs.docker.com/desktop/setup/install/mac-install/)
(choose Apple Silicon on an ARM Mac), or the [Linux Engine installation guide](https://docs.docker.com/engine/install/)
for your distribution. Start Docker and check that both client and server are
available. Installation and any applicable license approval remain your choice.

```bash
docker version
docker image inspect python:3.12-slim-bookworm
```

If the image is absent and you approve a network download, prepare it explicitly:

```bash
docker pull python:3.12-slim-bookworm
docker image inspect --format '{{.Id}} {{.Architecture}} {{json .RepoDigests}}' python:3.12-slim-bookworm
```

The tag can change: this prepares a compatible image, not a promise of the exact
historical image. Retain the displayed identity/digest with your evidence. The
driver resolves and records the installed immutable image ID before execution;
you may also pass your approved local ID/digest through `--image`. It never
pulls silently. Stop on a failed daemon/image check; do not remove the Docker
boundary to make a generated candidate run on the host.

## Pins and evidence

[local_model.py](../../loopeng/runtime/local_model.py) pins llama.cpp release **b11799**, source
commit `0756e83fc1529e207af783782905bc98a8ef0770`:

| Native target | Release archive | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| DarwinARM64 | `llama-b11799-bin-macos-arm64.tar.gz` | 16,136,376 | `51c3471c9212b41e51a6696c0b966628fa45d625385fdb024c4483e8d3154dca` |
| Linuxx64 | `llama-b11799-bin-ubuntu-x64.tar.gz` | 22,300,522 | `4920c65448350c28f8ce7b35eec91566807e0f111c25a0df2d5fc12a1ed1716a` |

The model is **Qwen3-4B Q4_K_M**, file `Qwen3-4B-Q4_K_M.gguf`, repository
revision `a9a60d009fa7ff9606305047c2bf77ac25dbec49`, 2,497,280,256 bytes,
SHA-256 `7485fe6f11af29433bc51cab58009521f205840f5b4ae3a32fa7f92e8534fdf5`.

Public artifact sources are
[llama.cpp b11799](https://github.com/ggml-org/llama.cpp/releases/tag/b11799)
and [the pinned Qwen revision](https://huggingface.co/Qwen/Qwen3-4B-GGUF/tree/a9a60d009fa7ff9606305047c2bf77ac25dbec49).
Both archive hashes were independently recomputed from retained local artifacts
during implementation. The pins and arithmetic acceptance rules derive from the
retained setup and [prior validation report](../validation/local-model.md). That
historical report describes the original external harness; these new commands
replace its sibling-checkout requirement. Archive verification establishes
identity, not new Linux inference results. In the historical shipped-workflow validation, offline tests and a live run of
both drivers passed on macOS ARM64 using existing artifacts and a local
Docker image. No installation or download was performed for this change.

Print pins without network access or filesystem writes:

```bash
python3 -B -m loopeng runtime pins
```

## Prepare a fresh external runtime

Choose new directories outside the checkout. Output paths inside the repository,
its ancestors, existing output directories and paths traversing symlinks are
rejected. On macOS use canonical paths (for example `/private/tmp` rather than
its `/tmp` symlink). Runtime failures and failed partial downloads are retained;
retry with a fresh directory after inspecting the failure. Never delete old
experiment evidence merely to reuse a command.

```bash
export LOOPENG_RUNTIME="$HOME/loopeng-runtime-01"
export LOOPENG_SERVER="$HOME/loopeng-server-01"
export LOOPENG_RUN="$HOME/loopeng-ralph-01"
```

For existing artifacts, set the two input paths yourself. The archive must match
the native host. Setup copies/extracts the small archive and verifies the model
in place, without copying or modifying it:

```bash
export LOOPENG_ARCHIVE=/absolute/path/to/llama-b11799-bin-macos-arm64.tar.gz
export LOOPENG_MODEL=/absolute/path/to/Qwen3-4B-Q4_K_M.gguf
python3 -B -m loopeng runtime setup --runtime "$LOOPENG_RUNTIME" \
  --archive "$LOOPENG_ARCHIVE" --model "$LOOPENG_MODEL"
```

On Linux x86-64 use `llama-b11799-bin-ubuntu-x64.tar.gz`. Explicit `--target
DarwinARM64` or `--target Linuxx64` is available for preparing artifacts for
another machine, but the launcher always checks the actual native host.

For a new reader who has no artifacts, the following **explicitly downloads**
the pinned native archive and model (about 2.5 GB) from the public sources:

```bash
python3 -B -m loopeng runtime setup --runtime "$LOOPENG_RUNTIME" --allow-download
export LOOPENG_MODEL="$LOOPENG_RUNTIME/Qwen3-4B-Q4_K_M.gguf"
```

A supplied `--model` can be combined with `--allow-download` to download only the
runtime archive. Each download has a socket timeout, exact size ceiling and hash
check; partials never become usable artifacts on failure. Setup validates archive
paths and local library symlinks before extracting. It retains the pinned archive
and writes a setup receipt. A later preflight compares **every** extracted file
and library link with that archive, rejects extra runtime files, and rehashes the
model. A setup receipt alone is never treated as proof of integrity.

```bash
python3 -B -m loopeng runtime preflight \
  --runtime "$LOOPENG_RUNTIME" --model "$LOOPENG_MODEL"
```

An existing runtime may also use `downloads/` for the pinned archive and
`llama_cpp/llama-b11799/` for the extracted release. Preflight and serve support
that layout directly, with the same integrity checks and no copying.

Allow disk space for the model, archive, extracted libraries, logs and receipts.
Memory needs depend on host and context; this is not a minimum-memory guarantee.
Model hashing on every launch reads the complete 2.5 GB file.

## Launch one owned server

In one terminal, run the bounded foreground launcher. CPU inference is the
explicit default; on Apple Silicon append **`--metal`** to request 99 GPU layers:

```bash
python3 -B -m loopeng runtime serve \
  --runtime "$LOOPENG_RUNTIME" --model "$LOOPENG_MODEL" \
  --evidence "$LOOPENG_SERVER" --port 18080 --metal \
  --startup-seconds 120 --max-seconds 2400 --grace 10
```

Omit `--metal` for Linux x86-64 or macOS CPU mode. The launcher rejects Metal on
other hosts. The observed Metal recipe is context 16,384, q8_0 K/V caches, six
threads, batch 256/microbatch 128 and one slot. Inspect the server log for actual
Metal offload; requesting layers is not proof of acceleration. CPU initialization
may require a larger `--startup-seconds` budget.

The launcher verifies artifacts before executing the binary, rejects an occupied
port, binds only `127.0.0.1`, disables built-in agent/MCP/web UI features, and uses
a minimal environment. Wait for `READY` and the readiness receipt before sending
requests. The served alias is `loopeng-qwen3-4b`; the default endpoint is
`http://127.0.0.1:18080/v1/chat/completions`. A health response establishes readiness,
not correctness of generated code. Only trusted local clients should access it.

Ctrl-C, SIGTERM, startup failure and the runtime limit all enter bounded cleanup:
terminate the exact child, wait the grace period, then kill that child if needed.
No PID-file reuse, broad process matching or unrelated-server shutdown occurs.
The launcher writes start/readiness/finish receipts plus stdout/stderr logs.
An uncatchable SIGKILL or host crash cannot run Python cleanup; inspect the recorded
PID and port before restarting. Logs have no automatic rotation, so choose a
finite runtime appropriate for the task and available disk space.

## Run the restricted live Ralph task

In another terminal, from the repository root, use a fresh output directory:
Shell exports are local to each terminal, so set the output variable again here.

```bash
export LOOPENG_RUN="$HOME/loopeng-ralph-01"
python3 -B -m loopeng live ralph \
  --output "$LOOPENG_RUN" \
  --endpoint http://127.0.0.1:18080/v1/chat/completions \
  --model loopeng-qwen3-4b --image python:3.12-slim-bookworm \
  --allow-model-code
```

If the configured container CLI has a prefix, pass it with `--docker-command
'docker --context YOUR_CONTEXT'`. The driver resolves an existing local image to
its immutable image ID, runs known-good strict arithmetic functions through the
same Docker path and all eight assertions, and requires exit 0. Then the defective
fixture must produce a Python traceback ending in `AssertionError`. Both controls
retain receipts and run before any model call. Timeouts and backend errors never
count as a known-bad baseline. A missing image or
unusable daemon is a setup failure; the driver never pulls an image. Container
architecture follows the installed image; native inference remains independent.

The [driver](../../loopeng/runtime/live.py) invokes the unchanged
[Ralph controller](../../loopeng/ralph/controller.py), with a fresh worker per iteration,
three iterations and 60 seconds per worker/verifier. The
[worker](../../loopeng/ralph/model_worker.py) makes one local HTTP request per pending
item, with a 30-second timeout, temperature 0 and a 1,024-token output limit.
The endpoint must be literal loopback HTTP; redirects and environment proxies
are disabled. Server/model options are supplied explicitly and never inferred
from another checkout.

The model can produce only an `add(a, b)` or `multiply(a, b)` function with one
return expression. Plain Python and a single whole fenced block are accepted;
prose, imports, calls, decorators, other names, altered signatures and unsupported
syntax are rejected. There are no model-directed tools, shell commands or paths.
The bridge writes only the current named function and marks one pending item done.
This is a deliberately narrow arithmetic bridge, not a general repository editor.

Scope verification rejects extra paths, symlinks and changed task inventory.
Prompt, wrappers, assertions and configuration reside outside the workspace;
wrappers pin configuration hashes, and checks pin trusted source/assertion hashes.
The original [eight arithmetic assertions](../../examples/local_model/assertions.py)
remain unchanged. A done claim or successful model response cannot replace these
gates. No deterministic repair or fallback candidate is supplied.

Candidate execution requires `--allow-model-code` and happens through stdin in a
unique disposable container with **no network and no host mounts**, read-only root,
unprivileged user, all capabilities dropped, no-new-privileges, 32 PIDs, 128 MiB
memory, one CPU, and a ten-second timeout. Cleanup attempts removal of only that
container, including after timeout; its receipt records cleanup errors. Docker
adds isolation but is not a guarantee against kernel/container escapes. The
trusted Python bridge itself is not OS-sandboxed; do not replace it with an
unrestricted worker and assume these file restrictions still hold.

Outputs retain positive/negative control results, requests/responses, candidates,
diffs, before/after states, container commands/results and final controller exit
code. Nonzero results remain failures for review. There is no commit, merge,
push or human acceptance step. Stop the owned server when finished and inspect
its finish receipt. Remove external runtime/work directories manually only after
reviewing or archiving their contents.

## Chapter 6 through the Docker boundary

The driver also supplies a restricted addition route using chapter 6's existing
retry primitive and the original two assertions and budgets from
[model_task.json](../../examples/tasks/model_task.json):

```bash
python3 -B -m loopeng live chapter6 \
  --output "$HOME/loopeng-chapter6-01" \
  --endpoint http://127.0.0.1:18080/v1/chat/completions \
  --model loopeng-qwen3-4b --image python:3.12-slim-bookworm \
  --allow-model-code
```

It runs positive/negative controls first, restricts generated code to `add(a, b)`,
passes verification feedback into subsequent requests, and enforces three
attempts, 90 seconds and 5,000 reported tokens. Invalid/missing token usage fails
closed. HTTP calls have a maximum 30-second timeout; Docker checks have a
ten-second timeout. An operation may extend past the remaining wall budget, but
a late result is never accepted. Generated Python executes only in Docker.
This route uses a separate restricted prompt/AST HTTP adapter, not the unchanged
`VLLMGenerator`. It accepts plain or fenced functions and uses the existing retry
primitive; it does not reproduce the original generator's exact prompts or
response parsing, or transparently replace that generator's execution backend.

## Validation and limits

```bash
python3 -B -m unittest discover -s tests -p 'test_local_model*.py' -v
python3 -B -m unittest discover -s tests -p 'test_ralph*.py' -v
python3 -B -m unittest discover -s tests -v
```

Network, child-server lifecycle and Docker calls are mocked in the new tests.
The existing Ralph integration tests still use real trusted offline worker
subprocesses. A live run is optional and requires separately prepared artifacts,
a running native server and a local Docker image; passing offline tests does not
establish model quality, Linux ABI compatibility or live GPU performance. The
historical live results remain described separately in the validation report.

See the [historical shipped-workflow observations](../validation/local-model.md#additional-retained-live-run-details)
for the recorded outcomes, token counts, runtime limitations and evidence packet.
These observations predate the package refactor.

Chapter 6's engineering command preserves the original acceptance rules; its direct model
mode still has its documented host-execution behavior. Use `python -m loopeng live chapter6`
for the Docker arithmetic route. The Docker boundary does not apply to unrelated
scripts. Chapter 5 integration is separate from this example.
