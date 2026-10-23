# Companion coverage: all six chapters

Historical review date: 23 October 2026. Source links below follow the current
package layout; reported checks and manuscript observations predate the refactor. Chapters 1, 2, 4 and 5 below follow a full reading of their
manuscripts under `NDLE/new_chapters` in the author's ND book workspace, plus
the matching numbered listings, runnable source, prompts, state examples and
asset documentation in this repository. Manuscript locations below are source
line numbers, not printed page numbers. No manuscript edits were made.

**Coverage is not implementation equivalence.** “Code” means an existing runnable
mechanism; “template” means a human worksheet with no runtime enforcement;
“listing” means a printed excerpt; “external” means the referenced product,
framework, research or operational deployment is intentionally not bundled.

The new [governance worksheets](../../examples/governance/README.md) are explicitly
unfilled and unapproved. They do not establish that any organization or run has
passed the book's admission criteria.

## Scope and evidence boundary

The companion now contains runnable [Ralph orchestration](../../loopeng/ralph/controller.py),
[economics](../chapters/chapter-3.md), [chapter 5 control policies](../chapters/chapter-5.md),
[chapter 6 mechanisms and scenarios](../chapters/chapter-6.md), and
[pinned local runtime tooling](../../loopeng/runtime/local_model.py). The
[local model worker](../../loopeng/ralph/model_worker.py) and
[live demo](../../loopeng/runtime/live.py) add real scope/final checks and receipts.
These are bounded educational implementations, not the complete external stack.

This review read the four named manuscripts in full, all their numbered excerpts,
and the matching source. It also inspected the new chapter 5 policy module,
[five scenarios](../../examples/local_policy/scenarios.json) and
[eight tests](../../tests/test_local_loop_policy.py). Integration reports those eight
tests, economics tests and chapter 6 tests passing; this documentation review did
not rerun Python tests or a live model. Chapters 3 and 6 below point to their
separate detailed reviews; they were not independently reread in full here.
The [earlier local-model validation report](../validation/local-model.md) describes
its own measured run and limitations, not a benchmark of the full chapter 5 stack.

## Chapter 1 — Foundations and critical assessment

Source: `chapter01_foundations.tex` (1,549 lines).

| Named section / material | Existing companion and new worksheet | Assessment |
| --- | --- | --- |
| “Genealogy: From Prompt to Loop”; “The Ralph Wiggum precedent” | [Listing 001](../../Code/listing_001.txt); [chapter 1 figures](../../imgs/cph1/); [Ralph controller](../../loopeng/ralph/controller.py) as a bounded successor | Listing 001 belongs to chapter 1, not chapter 4. The infinite shell command is historical illustration, not the runnable recommendation. |
| “Anatomy of a Loop”; “The Loop Engineering Contract” (line 472) | [Loop contract template](../../examples/governance/loop-contract.template.json) maps durable intent, external state, bounded work, protected evidence, explicit authority, budgets, checkpoints and terminal escalation | Previously no reusable eight-control worksheet. The Ralph implementation covers only part of this contract; filling JSON does not enforce any control. |
| “Completion contracts” (line 695) | Same [contract template](../../examples/governance/loop-contract.template.json): outcome/criteria, verification, invariants, boundaries and stop conditions | Template coverage; positive budgets, real owners and executable evidence must be supplied. |
| “Context Engineering: Architecting the Flow of Information”; four pillars; intentional compaction | [Ralph prompt](../../examples/tasks/ralph_prompt.md) and [evidence record](../../examples/governance/evidence-record.template.json) provide orientation and provenance fields | Partial. No automatic research/planning handover, context freshness service or context-reset monitor is supplied. Those are optional harness integrations, not required reproductions of the conceptual discussion. |
| “Verification and the Worker–Evaluator Split”; “Loop driver versus quality gate” | [Ralph controller](../../loopeng/ralph/controller.py) invokes scope/final executables; [chapter 6 mechanisms](../../loopeng/engineering.py) include maker/checker and protected-file checks; [verification worksheet](../../examples/governance/verification-plan.template.md) | Code demonstrates independent checks. Hash checks and subprocess boundaries are not OS write protection. The offline Ralph demo scope verifier is an unconditional success stub. The new [live demo](../../loopeng/runtime/live.py) supplies real inventory/hash checks and final behavioral assertions; neither provides per-item correctness checkpoints. |
| “From deterministic failure to compound learning” | [Lesson example](../../Code/listing_004.txt); [ownership worksheet](../../examples/governance/ownership-and-escalation.template.md) records failure → review → regression | Template/listing, not automatic promotion of model-written lessons into trusted policy. Human curation is intentional. |
| “From /loop to /goal: Native Loop Primitives”; harness mapping; automation, connectors, sub-agents; process parking | Architectural discussion and [bibliography](../../BIBLIOGRAPHY.md) | External product capabilities. This repository does not implement native commands, schedulers, MCP integrations or a commercial harness. Product claims were not independently revalidated in this review. |
| “The Non-Determinism Problem” | [Loop tuple](../../Equations/equation_1_1.tex), [compounding drift](../../Equations/equation_1_2.tex) | Equation assets. The independent-error model is illustrative; no benchmark or universal context threshold is implied. |
| “The Four Levels of Autonomy Handover”; “Critical Assessment”; “Systemic Risks and Structural Degeneration”; “The Joint System” | [Ownership/lifecycle worksheet](../../examples/governance/ownership-and-escalation.template.md), [operator checklist](../../examples/governance/operator-checklist.template.md) | Policy, review and learning practice, not missing autonomous software. Includes review dates, retirement, escalation capacity and human understanding. Practitioner reports and hype/history remain cited external evidence. |

## Chapter 2 — The organization becomes a loop

Source: `chapter02_organization.tex` (818 lines). No code listings. Existing visual
material is in [chapter 2 figures](../../imgs/cph3/) and the conceptual
[exception-capacity equation](../../Equations/equation_2_1.tex).

| Named section / material | Companion coverage | Boundary / remaining work |
| --- | --- | --- |
| “The Loop Becomes the Unit of Production”; “Five Organizational Laws”; “The Loop-Native Development Team” | [Ownership worksheet](../../examples/governance/ownership-and-escalation.template.md) names all six functions and the accountable acceptance owner | Real assignments, separation of duties and evidence of functioning controls remain organizational work. No invented approvals or named personnel. |
| “What Happens to Hierarchy and Management?”; “Decision Rights Must Be Redesigned” | Same worksheet separates admission, operation, verification, scope changes, waivers and irreversible decisions | Explicit authority is not inferred from a role title or token budget. |
| “Three Enterprise Operating Models” | Figures and prose; worksheet can be used in centralized, embedded or federated teams | No enterprise platform, identity provider or policy engine bundled. These are intentional deployment choices. |
| “The New Management System: From Activity to Evidence” | Worksheet has outcome, flow, quality, control, economics and human-system measurement rows | Unmeasured fields remain unmeasured. No dashboard or observed productivity benefit is claimed. See the [economics implementation](../chapters/chapter-3.md) for calculations. |
| “Governance Moves into the Runtime”; “A Minimal Evidence Record” (line 537) | [Evidence record template](../../examples/governance/evidence-record.template.json) captures owner, intent/boundary, risk/authority, versions, context/access, actions/artifacts, criteria/results, retries/feedback, interventions/waivers and final disposition | Previously absent as a reusable record. No automatic collector, integrity store, access controls or retention service is included. The separate control-plane runlog in chapter 5 is not by itself this complete record. |
| “Data and Context Become Organizational Infrastructure”; “Context Has a Supply Chain” | Version, context-source and access-decision fields; freshness/ownership review in worksheet | No retrieval corpus, permission-aware search or source quality service bundled. |
| “The Workforce Impact”; “Failure Modes”; “Escalation Saturation” (line 699) | Ownership worksheet includes learning, exception arrival rate, reviewer minutes, queue age, backup and admission throttling | Capacity numbers must share a time window; the chapter's equation is conceptual, not a staffing forecast or simulator. |
| “A Transition Roadmap”; “A Practical Design Method for Leaders”; “The Leadership Paradox”; organizational readiness | Ownership worksheet and chapter 1 contract supply reusable design/review records | Human judgment and institutional change remain external. No NIST/ISO/EU compliance certification is asserted by these templates. |

## Chapter 3 — Economics of loop engineering

The separate [chapter 3 review and runnable guide](../chapters/chapter-3.md) maps the complete
manuscript's equations and regulated-maintenance worked case to
[calculations.py](../../loopeng/economics/calculations.py), the [editable case](../../examples/economics/chapter3.json)
and [tests](../../tests/test_economics.py). It covers context costs, accepted-outcome
cost, bounded retry economics, bottleneck capacity, verification leverage and
sensitivity analysis. The [local TCO example](../../examples/economics/local_tco.py)
also supports chapter 5's energy/amortization discussion.

These are implemented calculations under declared hypothetical assumptions.
The detailed guide reports numerical agreement for the reproduced worked values
and distinguishes underspecified cases from executable formulas. Provider prices,
real acceptance rates, staffing capacity and production savings must be measured
or supplied; no benchmark or financial forecast is bundled. This section relies
on that detailed chapter review, rather than an independent full reread here.

## Chapter 4 — The Ralph loop

Source: `chapter04_ralph_loop.tex` (1,324 lines). Actual numbered range:
[002](../../Code/listing_002.txt)–[019](../../Code/listing_019.txt), 18 listings;
[figures](../../imgs/cph2/). No standalone numbered equation assets.

| Named section / listings | Coverage | Remaining limitation |
| --- | --- | --- |
| “The Core Architecture”; “The One-Item-Per-Iteration Rule”; “The Iteration Cycle”; listings 002–007 | [Controller](../../loopeng/ralph/controller.py), [prompt](../../examples/tasks/ralph_prompt.md), [state example](../../examples/tasks/ralph_state.example.json), [offline worker](../../loopeng/ralph/demo_worker.py) | Fresh process per attempt, persistent item statuses, at most one pending→done transition, iteration and per-process timeout bounds. No claim that status transitions prove exactly one code change; scope must be independently checked. |
| “Implementation Pattern I: The External Bash Loop”; [008](../../Code/listing_008.txt), [009](../../Code/listing_009.txt) | [Bash launcher](../../scripts/ralph) delegates to the Python controller | Intentional implementation adaptation: explicit CLI paths, item inventory validation, scope checks after each attempt, verifiers outside workspace. Not a byte-for-byte execution of the printed Bash. See mismatches below. |
| “Implementation Pattern II: The Stop-Hook Loop” | Conceptual sequence only | Tool-specific hook/plugin is external; not needed to make the stronger fresh-process reference runnable. Promise-only stopping is not equivalent to protected acceptance. |
| “Implementation Pattern III: The Editor-Native Manual Loop”; [010](../../Code/listing_010.txt)–[012](../../Code/listing_012.txt) | Session-start contract, reusable prompt and clipboard launcher preserved as text | No installed editor integration or runnable clipboard helper. Manual new-chat discipline remains an intentional human step. Packaging the helper is lower priority than evidence/recovery gaps. |
| “The Combined Ralph System”; “Building a Ralph Workspace”; [013](../../Code/listing_013.txt)–[019](../../Code/listing_019.txt) | Tree, scaffold, rules, lesson, TypeScript task examples, branch/run and review commands | These do not constitute a runnable TypeScript project: no package manifest, greeting implementation or project-specific test gate is supplied. They illustrate how to adapt a real project. No automatic commit, rollback or curated lesson store in the reference controller. |
| “Safety, Budgets, and Human Escalation”; “Troubleshooting”; “Reset, Learn, Restart” | Controller exits nonzero and retains state; live driver adds machine-readable receipts/result; [contract](../../examples/governance/loop-contract.template.json), [handoff worksheet](../../examples/governance/ownership-and-escalation.template.md) | The generic controller lacks a complete durable terminal-outcome record, whole-run deadline, token/cost enforcement and same-failure cutoff. Live-driver receipts are narrower evidence; retained state is not a transactional verified Git checkpoint. |
| “What Ralph Does Well/Does Not Solve”; “Maintainability”; “Tuning”; “Choosing the Right Ralph Variant”; “Where the Minimal Loop Begins to Strain” | Reference behavior and explicit scope limits | Architecture and operational guidance. Do not expand the small controller into an implicit full framework or claim unattended production readiness from the demo. |

## Chapter 5 — Building a full local AI loop

Source: `chapter05_local_ai_loop.tex` (1,782 lines). All 22 excerpts in
[020](../../Code/listing_020.txt)–[041](../../Code/listing_041.txt) are present, plus
[figures](../../imgs/cph5/) and [equations](../../Equations/).

| Named section / listings | Coverage | Missing companion vs intentional external scope |
| --- | --- | --- |
| “The Reference Architecture”; “The invariant loop kernel”; [020](../../Code/listing_020.txt), [021](../../Code/listing_021.txt) | Abstract mode interface and supervisor pseudocode | The [policy module](../../loopeng/policies/local.py) now implements routing, ordered gates and outcome decisions. A complete durable kernel composing task selection, execution and Git recovery belongs to the external framework; it is not required to run the companion examples. |
| “Step Zero: Define the Trust Boundary”; prompt injection; [022](../../Code/listing_022.txt) | Credential-unset excerpt; [contract](../../examples/governance/loop-contract.template.json), [preflight](../../examples/governance/local-preflight.template.json) and [operator checklist](../../examples/governance/operator-checklist.template.md) | Templates record controls; OS isolation, egress enforcement and secret handling require the actual deployment. Unsetting two variables alone does not prove local-only routing. |
| “Hardware Sizing and Backend Selection”; “Energy and Total Cost of Local Execution” | Equation/figure assets; preflight capacity fields and operator measurement guidance | DFlash/MLX/TurboQuant runtimes, weights and the source telemetry dataset are external. Hardware thresholds and energy observations are environment-specific. The [economics implementation](../chapters/chapter-3.md) covers calculations; do not reuse accounted token events as API-billed tokens. |
| “Installation as a Reproducible Supply Chain”; “Installation: Build a Controlled Local Runtime”; [023](../../Code/listing_023.txt)–[028](../../Code/listing_028.txt) | Version-sensitive setup excerpts | External [Kowalski repository](https://github.com/popoloni/kowalski_loop), Homebrew, Node, harness/router, proxy, backends and model downloads. No vendored full stack. The [pinned local runtime tooling](../../loopeng/runtime/local_model.py) provides a different, narrower route. |
| Both “Start and Verify the Local Services” sections; [029](../../Code/listing_029.txt)–[031](../../Code/listing_031.txt) | External wrappers/CLI/health examples; new preflight record | The [local runtime tooling](../../loopeng/runtime/local_model.py) supplies pinned artifact checks and serving health checks; the [live demo](../../loopeng/runtime/live.py) supplies a real diagnostic workflow. External `llmstack`, its doctor, watchdog, dashboard and these wrapper scripts are not bundled. |
| “Configuration as a Control Plane”; nested deadlines; stability profiles; [032](../../Code/listing_032.txt)–[034](../../Code/listing_034.txt) | Registry and core configuration excerpts; preflight deadline/profile fields | The registry is illustrative, including an `example/…` model. The companion has a pinned llama.cpp launcher and validates its policy inputs; it does not provide the external multi-backend registry, stability profiles or nested router/proxy deadline manager. |
| “The Plan Is the Durable Source of Intent”; [035](../../Code/listing_035.txt), [036](../../Code/listing_036.txt) | Atomic tokenizer task excerpt and external init command | The companion provides synthetic tokenizer policy scenarios and a separate real arithmetic fixture with protected final assertions. It does not parse the external plan schema, implement its tokenizer task or bundle its init wizard. |
| “Choose the Executor per Task”; [037](../../Code/listing_037.txt) | Precedence pseudocode | Implemented and tested in [local.py](../../loopeng/policies/local.py): default agent, explicit direct, edit/rewrite precedence and large self-context promotion. It returns a decision using supplied byte sizes; dispatch to a full coding harness remains external. The authored 10,000-byte default differs from listing 033's configurable 12,000-byte example, as the notes disclose. |
| “Verification Is the Loop”; [038](../../Code/listing_038.txt) | New [ordered verification worksheet](../../examples/governance/verification-plan.template.md); existing Ralph scope/final hooks and chapter 6 check helpers are partial mechanisms | The [policy gate runner](../../loopeng/policies/local.py) requires all nine gates in order, fails closed on exceptions/non-booleans and stops on first failure. CLI booleans are explicitly synthetic. Real shell/marker/wiring/plugin callbacks and final-plan scheduling remain project integrations. Already-done may relax only the change gate. |
| “Retries, Resumes, Rollback, and Escalation”; outcome taxonomy; “The Life of One Task” | Worksheet specifies different transitions; small controller only retains state | Separate retry/resume counters, attempt/time limits and authorization halt are implemented and tested in [local.py](../../loopeng/policies/local.py). Usable progress is supplied by the caller; repository actions remain recommendations with `executed: false`. Actual checkpoint restoration, WIP validation/commits and durable recovery orchestration remain external. |
| “Production Controls Beyond Repository Edits” | Contract/evidence/checklist fields for operation IDs, preconditions, effect classification, retention and incident response | Real refund/message/provisioning executors, idempotency stores, leases and compensation are external. Do not implement real external actions merely to illustrate these controls. |
| “Loop Modes and Human Authority”; “loop_strategy: The Pluggable Policy Layer” | Executable budget and authority decisions in [policy module](../../loopeng/policies/local.py) | The four arrival modes, persistent priority queue, shallow strategy merge and named presets belong to the external framework. The companion does not claim those mechanisms or need them for its pure policy examples. |
| “Observability: The Second Loop”; [039](../../Code/listing_039.txt) | Illustrative successful runlog; unfilled [evidence record](../../examples/governance/evidence-record.template.json) | Structured policy output is synthetic; the [live demo](../../loopeng/runtime/live.py) writes real request/response/diff/check/result receipts. Full per-task append-only JSONL, cross-service correlation, compression/cache/speculation telemetry and dashboard remain external. Printed sample is not observed evidence. |
| “Validation: From a Fast Demo to an Engineering Claim”; end-to-end procedure; [040](../../Code/listing_040.txt), [041](../../Code/listing_041.txt) | Operator checklist; separate [local validation report](../validation/local-model.md) | Existing two-function observations do not reproduce the external five-task Agent Problem Pack, 35B route results, multi-turn DFlash benchmark or clean-machine installation. Those are intentionally external evidence. |
| “Failure Modes and Their Design Responses”; “Managing Model, Harness, and Policy Drift”; “Production admission gate” | Preflight, verification and operator worksheets cover versions, calibration, recovery drills, promotion and recertification | No automatic shadow/canary rollout or production admission system. Actual approval and workload evidence remain unfilled. |

## Chapter 6 — Choosing the right loop

The separate [chapter 6 guide](../chapters/chapter-6.md) maps listings 042–060 to the
[core mechanisms](../../loopeng/engineering.py), [scenario runner](../../loopeng/cases/chapter6.py),
[fixtures](../../examples/chapter6/fixtures.json) and
[scenario tests](../../tests/test_chapter6_examples.py). Runnable examples cover
bounded feedback, maker/checker, context/retrieval/tool use, isolated work,
coordination, cost, guardrails, production patterns and support handoff. Tests
are reported passing by integration; scenario refusal/handoff is a valid result,
not an implementation failure.

The [course relationship guide](course-relationship.md) separates these companion
adaptations from the external course notebooks, learned embeddings, datasets and
measured results. Offline replay and lexical scoring do not reproduce those
experiments; simulated authority does not authorize real customer actions. This
section points to the detailed chapter review rather than claiming an independent
full reread of chapter 6.

## Exact discrepancies and manuscript issues for later editorial work

1. **Listing attribution:** [README](../../README.md) and [asset guide](assets.md)
   originally assigned 001–019 to chapter 4. Chapter 1 contains
   [001](../../Code/listing_001.txt) at line 175; chapter 4 begins with
   [002](../../Code/listing_002.txt) at line 17. Correct map: chapter 1 = 001,
   chapter 4 = 002–019. **Corrected in both companion indexes during integration**;
   no manuscript change was needed. The excerpts themselves are not stale: extracting the
   listing blocks in reading order produced 41 matches after trimming outer
   whitespace, with no content differences for chapters 1, 2, 4 and 5.
2. **Duplicate section:** chapter 5 has the exact heading “Start and Verify the
   Local Services” at lines **752 and 887**. The first contains commands and
   preflight; the second contains additional admission/control guidance. They
   overlap but are not identical prose. Consolidate or retitle during a later
   manuscript edit; retain both sets of requirements.
3. **Ralph prompt path:** chapter 4 lines **439 and 442**, also
   [008](../../Code/listing_008.txt), redirect from root-level `CLAUDE.md`, while
   the workspace tree/scaffold at lines **943 and 957**, also
   [013](../../Code/listing_013.txt)/[014](../../Code/listing_014.txt), place that
   prompt under `scripts/ralph/CLAUDE.md`. Following the scaffold does not create
   the file the printed driver reads.
4. **Incomplete Ralph scaffold:** chapter 4's printed driver requires
   `tasks/state.json` and two executable verifier scripts (lines 422–431);
   “Building a Ralph Workspace” does not create them. It also supplies no
   TypeScript package setup for the greeting/farewell quality gates.
5. **Ralph state-schema mismatch:** [008](../../Code/listing_008.txt) tests
   `schema_version`, top-level `status=complete` and `open_items=0`.
   The runnable [state example](../../examples/tasks/ralph_state.example.json) and
   [reader](../../loopeng/ralph/controller.py) instead require an ordered, nonempty `items`
   array of unique IDs with `pending`/`done` status. These are deliberate runnable
   safeguards, but the schemas are not interchangeable.
6. **Timeout guarantee mismatch:** chapter 4 lines **437–444** silently run
   without a timeout when the `timeout` executable is absent, whereas line 481
   says the timeout bounds a hung attempt. The Python controller supplies a
   subprocess timeout independently of that shell utility. It still has no
   single whole-run wall-clock budget or OS sandbox.
7. **Acceptance timing and checkpoints:** the printed Bash runs scope checking
   only after its complete-state predicate passes, and skips it on worker failure;
   the runnable controller checks after each attempt. The chapter describes
   verified commits/checkpoints, but the runnable controller neither commits nor
   rolls back and only runs final correctness verification when all items are
   marked done. Its offline demo's scope executable simply exits zero. The new
   live demo adds real inventory/hash scope checks, final assertions and receipts,
   but neither demonstrates per-item correctness checkpoints or Git recovery.
8. **Uninitialized pseudocode state:** chapter 5 lines **156–179** /
   [021](../../Code/listing_021.txt) reads `decision.done` even if the first
   `strategy.permits_another_attempt()` is false. It can also retain a prior
   task's decision if translated literally. Initialize an explicit incomplete
   decision for every task and handle zero permitted attempts in real code.
9. **Installation pinning tension:** “Installation as a Reproducible Supply
   Chain” requires pinned inputs (line 647 onward), but
   [023](../../Code/listing_023.txt)–[026](../../Code/listing_026.txt) use latest
   installation/upgrade commands, an unpinned clone and unversioned packages.
   These are illustrative July 2026 setup instructions, not a reproducible lock
   manifest. The chapter explicitly warns that interfaces may age.
10. **External repository ambiguity:** chapter 5's “repository”, wrappers,
    `llmstack.cli`, model registry and logs refer to the external Kowalski stack,
    not this companion. An HTTP model adapter and two successful local tasks
    must not be described as including Headroom/CCR/DFlash/MLX or reproducing
    that framework's measurements.

All active figure references in the four reviewed manuscripts resolve to existing
companion files. Commented-out TikZ originals are retained source, not duplicate
active sections. The existing [asset guide](assets.md) separately documents
the chapter 6 figure-directory discrepancy; chapter 6 was outside this full-text
review.

## Remaining integration boundaries

The companion's executable policy ordering, executor precedence, separate
retry/resume budgets and bounded transition decisions are **implemented**. The
five synthetic scenarios deliberately perform no Git, shell or deployment action.
They need no full checkpoint kernel to fulfill that documented teaching scope.

| Boundary | What remains external or project-specific | Action if deploying that capability |
| --- | --- | --- |
| Full request path | Claude Code, CCR translation, Headroom compression, DFlash/MLX/TurboQuant servers, compatible target/draft models | Use the external Kowalski release and its installation guide; pin versions/hashes and verify every actual hop. The companion's pinned llama.cpp route is narrower. |
| Transactional supervisor | Durable queue/modes, priority selection, policy merging, accepted/WIP Git checkpoints and automatic recovery | Integrate a real supervisor only in an owned isolated workspace; prove restoration preserves plan/logs and operator changes. The pure policy decisions do not execute their suggested actions. |
| Real project gates | Marker, change, wiring, smoke, plugin, independent-checker and final-plan implementations | Supply protected callbacks and a known-good/bad calibration set. Do not promote synthetic fixture booleans into acceptance evidence. |
| Per-item correctness | Ralph enforces item status protocol and scope, then final correctness when all items are done | If per-item verified checkpoints are required, add a protected per-item checker before recording accepted progress. The live arithmetic demo's final assertions do not establish this guarantee. |
| Whole-run resource enforcement | Ralph per-process timeout/iteration bounds; policy module evaluates supplied elapsed time/counters | A production supervisor must measure and persist counters and enforce a single deadline plus token/cost ceilings. Pure policy calculations do not interrupt processes. |
| Operational telemetry | Companion receipts exist; full inference/control correlation, append-only task runlog, Headroom/cache/speculation/power metrics and dashboard do not | Collect actual deployed-service measurements, define counting methods and mark unsupported metrics unknown. Do not infer published energy or benchmark results from local arithmetic demos. |
| External effects and organizational control | Idempotency stores, precondition rechecks, compensation, identity/egress controls, retention, incident handling and human approvals | Complete the governance worksheets with real owners and evidence; bind each requirement to an actual control. No template grants authority. |

The highest-priority additions **if scope expands beyond teaching examples** are
per-item protected correctness, durable terminal evidence/whole-run enforcement,
and safely isolated recovery integration. None requires silently bundling the
entire external framework. The lower-priority editor clipboard helper remains a
printed excerpt, and tool-specific stop hooks remain external.

## Historical checks performed for the coverage review

- Read all four complete manuscripts and all 41 matching numbered excerpts.
- Compared extracted listing contents against files: 41 matches, no differences
  after trimming outer whitespace; chapter counts 1, 0, 18 and 22.
- Checked duplicate active section headings and active figure path existence.
- Parsed the three new JSON templates and checked local Markdown link targets.
- Ran the existing asset inventory and a whitespace/diff check; no Python tests
  or live model runs were required for these non-executable worksheets.
