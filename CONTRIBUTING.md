# Contributing

Corrections to broken links, transcription errors and chapter-to-asset mappings
are welcome. Include the chapter and listing, equation or figure filename in an
issue; for an excerpt, include the surrounding passage or expected behavior.

## Architecture and ownership

[loopeng/](loopeng/) is the canonical implementation. Its single
`python -m loopeng COMMAND` entry point dispatches to domain implementations:

| Domain | Responsibility | Commands |
| --- | --- | --- |
| [economics/](loopeng/economics/) | Hypothetical cost, capacity and local TCO arithmetic | `economics` |
| [ralph/](loopeng/ralph/) | Persistent task controller and worker interfaces | `ralph`, `demo-worker`, `model-worker` |
| [policies/](loopeng/policies/) | Pure routing, gates and retry/resume decisions | `policies` |
| [cases/](loopeng/cases/) | Chapter 6 synthetic applications | `cases` |
| [engineering.py](loopeng/engineering.py) | Shared chapter 6 mechanisms and code-repair CLI | `engineering` |
| [runtime/](loopeng/runtime/) | Pinned native runtime and restricted live drivers | `runtime`, `live` |

Keep domain behavior in these packages, with one implementation and one canonical
command interface. Do not add compatibility copies or duplicate fixtures.
Store editable task inputs in
[examples/tasks/](examples/tasks/) and other fixtures under [examples/](examples/).
A controller owns budgets and acceptance; a worker's prose or done claim cannot
replace independent executable checks. Keep prompts, verifier code and approval
decisions outside a worker's writable boundary.

Documentation has one canonical home for each purpose:
[guides](docs/guides/) explain setup and operation,
[chapters](docs/chapters/) explain mechanisms and limitations,
[reference](docs/reference/) maps assets, coverage and attribution, and
[validation](docs/validation/) preserves observed evidence.
Keep the [README](README.md) a short entry point and the
[documentation index](docs/README.md) the complete navigation map.
Use a short moved-link stub only when an old reader-facing URL needs continuity;
do not maintain duplicate guides.

Coordinate changes across implementation, fixtures, tests and documentation.
When multiple contributors work concurrently, agree file ownership before editing
and leave integration reports to their assigned owner. Preserve existing pending
work and retained failures. Keep publisher-facing names in [Code/](Code/),
[Equations/](Equations/) and [imgs/](imgs/) stable unless all references are
coordinated. Printed excerpts remain historical/pedagogical assets, distinct
from runnable implementations.

## Validation

Run the complete offline gate from the repository root:

```bash
python3 -B scripts/check.py
```

The gate runs unit tests, duplicate-file detection, local documentation link checks, asset checks and every
canonical offline demo. It uses no package installation or downloads.
For a focused iteration, use the relevant test file through standard-library
discovery, for example:

```bash
python3 -B -m unittest discover -s tests -p 'test_economics.py' -v
bash scripts/check-assets.sh
```

Document new environment requirements and add focused checks that prove changed
behavior. Git is needed for worktree tests and Bash for the asset check.
The suite uses synthetic fixtures and mocked local-model paths; it does not
reproduce course benchmarks or prove optional runtime compatibility.

Keep hypothetical economics, synthetic fixtures, real model observations and
human approval distinct. Record actual commands, versions, outcomes and limits;
label older command paths as historical rather than rewriting past evidence.
Report new results only after the corresponding checks run.

Optional live tests use fresh external output directories, bounded resources
and preserved failure evidence. Follow the [local-model guide](docs/guides/local-model.md)
and never weaken independent checks to obtain a pass. Do not commit credentials,
model weights, generated outputs or third-party course material. Attribute
external research and link to primary sources.
