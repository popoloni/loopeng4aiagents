# Local loop operator checklist

**UNFILLED / HYPOTHETICAL / NOT APPROVED.** Every box starts unchecked. Attach
observations for your actual runtime. No checklist implies that Headroom, CCR,
DFlash, MLX, TurboQuant or the Kowalski framework is installed or bundled here.

- Run / operator / accountable owner / date: TBD
- Task contract, risk tier and admission decision: TBD
- [Preflight record](local-preflight.template.json) location: TBD
- [Verification plan](verification-plan.template.md) location: TBD
- [Evidence record](evidence-record.template.json) location: TBD

## Before admission

- [ ] Pin runtime, model hashes, quantization, harness, policy and verifier versions;
      record licenses, installation source and rollback configuration.
- [ ] Confirm the real request route and observed model identity with a disposable
      completion, beyond merely seeing a healthy process or HTTP response.
- [ ] Inspect egress, telemetry, plugins, cloud credentials and update behavior;
      record the isolation mechanism and exclusions for secrets and unrelated files.
- [ ] Establish a recoverable Git baseline in the intended workspace; preserve
      operator changes and keep plan, state and logs outside the rollback domain.
- [ ] Parse and review atomic tasks, dependencies, non-goals and final integration
      criteria; define external-effect IDs/preconditions or exclude external effects.
- [ ] Protect verifier/policy assets from worker writes and exercise known-bad cases.
- [ ] Set retry, resume, total attempt, duration, token and monetary budgets with
      actual enforcement; nest deadlines for the layers that are really deployed.
- [ ] Measure disk/memory headroom and workload-specific warning/stop thresholds;
      do not assume the book's 64 GB workstation thresholds apply here.
- [ ] Exercise stop/restore on a disposable run and confirm escalation capacity.
- [ ] Record actual task admission by the authorized owner; begin supervised when
      the task class, model, route or policy is new.

## During the run

- [ ] Correlate task, attempt, executor, effective policy, checkpoint and gate outputs.
- [ ] Separate correctness retry, usable-partial resume and authorization halt;
      feed exact gate failures into permitted retries and retain failed attempts.
- [ ] Observe inference latency, prompt/uncached tokens, cache/compression if present,
      memory and control outcomes. Mark unavailable measurements as unknown.
- [ ] Stop on budget exhaustion, missing authority, repeated instability, ambiguous
      intent, failed integration or an overloaded exception queue.
- [ ] Keep accepted work separate from provisional WIP; do not equate a model's
      completion message or task status with acceptance or permission to merge.

## Acceptance, incident and lifecycle review

- [ ] Run task and plan-level gates against the recorded candidate; review actual
      changed paths and any external effects, not only the worker's report.
- [ ] Record independent correctness and authorization decisions with identity/time.
- [ ] Preserve redacted evidence, configuration, consumption and human rework;
      calculate cost per accepted outcome only from comparable measured quantities.
- [ ] On incident, stop admissions, revoke worker credentials, preserve evidence,
      enumerate effects, contain/restore/compensate, add regression coverage and
      obtain the required explicit re-enablement decision.
- [ ] After model/harness/policy changes, run the internal problem pack; document
      shadow/canary evidence, promotion criteria and rollback thresholds.
- [ ] Set recertification date, named owner and retirement condition; curate lessons
      only from observed failures and retain opportunities for human learning.

Final disposition / unresolved checks / next owner: **not decided / TBD / TBD**.
