# Repository refactor validation

Date: 23 October 2026. This report covers the uncommitted refactor after the
[previous validation](local-model.md), not a new release or production certification.

**Latest update:** the compatibility layer described in the original observations
below has now been removed. See [deduplication validation](#deduplication-validation).

## Organization

- [loopeng/](../../loopeng/) owns implementations by domain: economics, Ralph,
  policies, use cases and native runtime. `python -m loopeng COMMAND` is the
  canonical interface; each domain retains its existing arguments.
- [examples/](../../examples/) owns inputs and worksheets, including canonical
  [task fixtures](../../examples/tasks/).
- At the time of this validation, `src/` contained compatibility aliases and legacy fixture
  paths, not a second implementation. Regression tests enforce module identity,
  command parity and identical legacy/canonical fixture content.
- [Documentation](../README.md) separates guides, chapter explanations,
  reference material and historical validation. The root README is navigation,
  not a second copy of the guides.
- [scripts/check.py](../../scripts/check.py) is the single offline validation
  gate. Live tests remain explicit, bounded and separate.

The original numbered assets and manuscript were not edited. All **142 files**
under `Code/`, `Equations/` and `imgs/` matched their pre-refactor SHA-256 hashes.
Existing pending additions were retained and reorganized; no commit or push was
performed.

## Verification and iteration

The baseline had 115 passing tests. The first integration run passed its 126
tests and all offline examples but correctly failed the navigation gate while
documentation was being moved. All missing link targets were resolved. Further
compatibility regressions brought the suite to 128 tests; no original assertions
were weakened or removed to obtain a pass.

A fresh Python **3.12.4** virtual environment with no project packages installed
ran the final gate in both the working repository and a copied checkout without
Git metadata, virtual environments or caches:

```bash
python -B scripts/check.py
```

| Check | Final observed result |
| --- | --- |
| Unit/integration/compatibility tests | 128 passed; clean-copy run 5.752 seconds |
| Complete offline gate | 15/15 checks passed |
| Canonical commands | Economics demo/scenario/TCO, policies demo/scenarios, all cases, Ralph, engineering demo/task, runtime pins passed |
| Additional examples | TCO module and legacy Bash Ralph entry point passed |
| Navigation | Local Markdown/HTML target existence passed; remote URLs and heading anchors are not covered by this gate |
| Book assets | Inventory passed; all 142 retained asset hashes unchanged |
| Compatibility | Legacy imports retain actual module identity; CLI forwarding, output parity, external-working-directory launch and protected source hashes passed |
| Runtime setup | Fresh native archive extraction and full model/runtime preflight passed |
| Diagnostics and whitespace | No reported editor errors; `git diff --check` passed |

## Repeated live local-model checks

The new canonical commands were exercised using the freshly prepared runtime,
not just tested with mocks:

```bash
python -B -m loopeng runtime serve ... --metal --startup-seconds 60 --max-seconds 240 --grace 10
python -B -m loopeng live ralph --output /new/external/ralph --allow-model-code
python -B -m loopeng live chapter6 --output /new/external/chapter6 --allow-model-code
```

These abbreviated commands identify the observations; use the
[complete setup guide](../guides/local-model.md) for runnable setup commands.

- Reused verified Qwen3-4B Q4_K_M weights and the b11799 Darwin ARM64 archive.
  No model, server, package or container image downloads were needed.
- Served alias `loopeng-qwen3-4b`, loopback port 18080, requested Metal 99 layers,
  context 16,384, q8_0 K/V, six threads, batch 256/microbatch 128.
  This is a correctness smoke test, not a fresh CPU/GPU performance benchmark.
- Ralph: two fresh model workers, both items done, protected scope checks and
  all eight independent arithmetic assertions passed; exit 0. Each worker
  reported 144 tokens. The second response reported 106 cached prompt tokens.
- Chapter 6: first attempt passed both original assertions, 71 reported tokens,
  `verified`, `report_only`; exit 0. It remains the restricted arithmetic
  adapter, not a claim about unrestricted code generation or the original HTTP
  adapter's exact prompts.
- Both routes passed positive controls and required actual assertion failures
  from known-bad fixtures before making model calls. No candidate was manually
  repaired and no retry or prompt intervention was needed.
- Candidate execution used the existing Docker image
  `sha256:3c4d812a6efe003770aafbdba65f9c1960ba8234ab23a133934205a70bdcda77`,
  no network/host mounts, read-only root, unprivileged user, bounded resources
  and timeouts. Its amd64-on-ARM64 warning was retained. Native inference ran
  outside that container; container isolation is not a general security proof.
- The owned server stopped on SIGTERM, exit 0 after 61.967 seconds. No listener
  remained on port 18080 and no owned candidate containers remained.

## Evidence and limits

Raw logs, clean checkout, asset hashes, setup/runtime receipts and model request,
response and verification receipts are retained on the validation workstation in
`/private/tmp/loopeng-refactor-validation.4PFZOE/`. This temporary evidence path
is not required to run the repository. Earlier observations remain in their
separate historical report and packets.

Only Python 3.12.4 on macOS ARM64 was executed in this refactor validation.
Linux inference, network downloads, other Python runtime versions, production
integrations and course benchmarks were not revalidated. Passing examples do
not grant deployment authority. The fact-grounded Python procedure drove the
baseline, compatibility regressions, failure-preserving gate and clean-copy
verification rather than relying on file moves alone.

## Deduplication validation

Following approval to break old paths, the entire former `src/` layer was removed:
nine Python aliases, its package marker, the redundant Bash launcher and four
copied task/prompt fixtures. Canonical implementations remain under `loopeng/`,
task inputs under `examples/tasks/`, and the sole Bash convenience launcher under
`scripts/ralph`. Runtime workers and verifiers now invoke `loopeng/__main__.py`
directly from isolated workspaces; the complete canonical source tree remains
protected by hashes. Current links/imports were migrated. Historical command
transcripts remain explicitly historical rather than being silently rewritten.

The first rerun exposed stale test-only imports/paths; these were corrected.
Four compatibility-only tests were retired because their API was intentionally
removed; the five canonical entry-point/protection tests remain, and a new
duplicate-detection regression was added. All original domain behavior and
acceptance assertions remain tested.

- **125 tests passed**, and the expanded offline gate passed **16/16 checks**.
- No byte-identical nonempty maintained files were found. Duplicate detection is
  now a permanent gate across code, examples, tests, docs and book assets; empty
  files, hidden metadata and Python caches are excluded. This is an exact-content
  check, not a proof that no two distinct teaching examples discuss the same idea.
- All 142 original book asset hashes remained unchanged; editor diagnostics and
  whitespace checks passed.
- Both canonical live routes passed again using the retained native Metal runtime:
  Ralph completed two workers and eight assertions; chapter 6 passed its two
  assertions on the first attempt. No candidate repairs or relaxed checks.
- The owned server stopped cleanly after SIGTERM; no test containers or listener
  remained. No artifacts were downloaded.

Offline log: `/private/tmp/loopeng-dedup-final.log`. Live receipts:
`/private/tmp/loopeng-dedup-live.nVx9zY/`. Removed tracked files remain recoverable
from Git; the previous complete pre-removal snapshot is retained at
`/private/tmp/loopeng-refactor-validation.4PFZOE/checkout/`. Ignored old bytecode
was moved outside the repository into the live evidence directory rather than
retained as an empty-looking source tree. No commit or push was performed.
