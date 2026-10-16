# Loop Engineering for AI Agents

<p align="center">
  <img src="imgs/cover.jpg" alt="Cover of Loop Engineering for AI Agents by Enrico Papalini" width="320">
</p>

Companion repository for *Loop Engineering for AI Agents* by Enrico Papalini, published by Packt. The book was developed under the working title *Non-Deterministic Loop Engineering*; older asset names and manuscript references may still use that title.

Loop engineering is the design of a system that turns an objective into bounded, verifiable work: select a task, supply context, act, check the result, retain useful state, and decide whether to continue, stop, or ask a human. This repository supplies the book's figures, equations, illustrative listings, and runnable chapter 4 and chapter 6 reference scripts. It is **not** a reproduction of third-party experiments or a production agent framework.

**Quick links:** [Runnable source code (`src/`)](src/) · [Book bibliography (clickable citations)](BIBLIOGRAPHY.md) · [Original numbered listings (`Code/`)](Code/)

## Find material by chapter

| Book chapter | Topic | Companion material |
| --- | --- | --- |
| 1 | Foundations and critical assessment | [Figures](imgs/cph1/) · [Equations](Equations/equation_1_1.tex) |
| 2 | The organization becomes a loop | [Figures](imgs/cph3/) · [Equation](Equations/equation_2_1.tex) |
| 3 | Economics of loop engineering | [Figures](imgs/cph4/) · [Equations](Equations/equation_3_1.tex) |
| 4 | The Ralph loop | [Figures](imgs/cph2/) · [Listings 001–019](Code/) · [Working controller](src/ralph_loop.py) |
| 5 | Building a full local AI loop | [Figures](imgs/cph5/) · [Equations](Equations/equation_5_1.tex) · [Listings 020–041](Code/) |
| 6 | Choosing the right loop | [Figures](imgs/cph6/) · [Equations](Equations/equation_6_1.tex) · [Listings 042–060](Code/) |

The listing numbers follow reading order across the book. For a fuller description of the folders, naming conventions, and the chapter 6 image-path discrepancy, see the [asset guide](docs/asset-guide.md).

The [bibliography](BIBLIOGRAPHY.md) follows the manuscript's chapter order and links each cited work to its source. The [source directory](src/) contains executable chapter 4 and chapter 6 implementations and example tasks; the numbered [book listings](Code/) are reference excerpts, not complete runnable programs.

## How to use this repository

1. Start with the chapter you are reading and use the table above to locate its assets.
2. Open a listing as text (for example, [the bounded retry loop](Code/listing_042.txt)); read it alongside the surrounding explanation in the book. Listings include pseudocode, shell fragments, JSON examples, and excerpts. They are **not** a single application and may require project-specific setup, dependencies, credentials, and review before use.
3. Use the figures as visual references and the equations as LaTeX source. File paths remain close to the publisher's numbered/source-asset convention to keep cross-references stable.

The assets have no install step. For a local consistency check, run `bash scripts/check-assets.sh` from the repository root.

## Run the chapter 4 Ralph loop

The [Python controller](src/ralph_loop.py) and [Bash launcher](src/ralph.sh) require Python 3.10+ and only the standard library. Run the offline demonstration with either entry point:

```bash
python3 src/ralph_loop.py --demo
bash src/ralph.sh --demo
```

The demo starts a new worker process for each of two plan items, persists JSON state between runs, and accepts completion only after separate scope and final checks pass. The deterministic [demo worker](src/ralph_demo_worker.py) uses no model or credentials. For your own project, copy the [prompt template](src/ralph_prompt.md) and [state example](src/ralph_state.example.json), supply a worker executable that reads its prompt on standard input, and provide executable scope and final verifier programs owned outside the worker's writable area:

```bash
bash src/ralph.sh --workspace /path/to/project \
  --prompt /path/to/ralph_prompt.md --state /path/to/project/tasks/state.json \
  --worker /path/to/worker \
  --scope-verifier /path/to/protected/verify_scope.sh \
  --final-verifier /path/to/protected/verify_final.sh \
  --max-iterations 10 --timeout 300
```

The state file must be inside the worker workspace; the prompt and verifiers must be outside it. The controller enforces at most one completed item per iteration, a per-worker timeout, an iteration limit, and unchanged prompt/verifier files. Worker prose or a completion promise alone never stops it. Verifiers must implement real project checks; the controller does not invent them, sandbox the worker, or automatically commit, push, or merge. Run an unattended worker only in an isolated environment with narrowly scoped credentials. The older *ai-auto_eng* Ralph appendix informed the mechanics; the current chapter's structured-state and controller-owned verification rules govern this implementation.

## Run the chapter 6 loop

The standard-library [standalone script](src/loop_engineering.py) requires Python 3.10+ and provides callable implementations of listings 042–060. Its CLI composes retry, executable verification, a time/attempt budget, and escalation. It runs without a model or extra dependencies using a supplied sequence of candidate programs and real executable assertions:

```bash
python3 src/loop_engineering.py --demo
python3 src/loop_engineering.py --task src/example_task.json
python3 -m unittest discover -s tests -v
```

The offline demo first checks a wrong `add()` implementation, records its assertion failure, then checks the next supplied candidate and accepts it. The replay source does not generate or repair code itself; model mode passes real feedback to the generator. A failed verification escalates rather than auto-acting. The script also exposes an optional adapter for the local vLLM chat-completions server used by the course:

```bash
python3 src/loop_engineering.py --task src/model_task.json --vllm-model YOUR_SERVED_MODEL --allow-model-code
```

The default endpoint is `http://127.0.0.1:8000/v1/chat/completions`; override it with `--vllm-endpoint` and set `VLLM_API_KEY` if the server requires a key. Model mode requires a running local server. **The subprocess timeout is not a security sandbox**: `--allow-model-code` explicitly opts into executing generated Python, so use only an isolated environment you control. The script does not automatically merge branches or carry out external actions. Its offline retrieval/triage scorer is lexical, not the course's learned embedding model. See the [chapter 6 implementation notes](docs/chapter-6.md) for the mapping and limitations.

## Chapter 6 and the measured course

Chapter 6 was informed by Fareed Khan's independent [*Agentic Loop Engineering: Executed and Measured* course](https://github.com/FareedKhan-dev/agentic-loop-engineering-course). Its 18 notebooks measure feedback, context, verification, retrieval, tools, isolation, coordination, cost, safety, and production patterns. The chapter uses those experiments as an evidence catalogue for selecting the smallest useful loop, while adding the book's own selection and operating guidance. Use the [chapter 6 listing index](docs/chapter-6.md) to find an individual mechanism. See [course relationship and attribution](docs/course-relationship.md) before treating any quoted result as a general benchmark. The course's notebooks, datasets, results, and runtime are **not** bundled here; use the original repository for reproduction.

## License and contributions

The repository contains an [Apache License 2.0](LICENSE). See [CONTRIBUTING.md](CONTRIBUTING.md) for corrections and asset updates. The book and this repository serve different purposes; possessing these assets does not grant a license to reproduce the full book text. Packt is the book publisher, not the maintainer of the independent course linked above.
