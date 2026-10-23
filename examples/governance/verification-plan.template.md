# Ordered verification plan

**UNFILLED / NOT EXECUTED / NOT APPROVED.** This defines a proposed evidence
pipeline; it does not run checks or provide a shell-command execution interface.

- Task ID / contract revision / accepted baseline: TBD
- Verifier owner, immutable revision/hash and OS protection mechanism: TBD
- Exact permitted targets and maximum blast radius: TBD
- Known-good, known-bad, adversarial and policy-violating calibration cases: TBD

Use fixed, owner-controlled executable interfaces. Record argument vectors, working
directory, environment references and timeouts explicitly; do not evaluate command
strings produced by the worker. An unavailable mandatory check is not a pass.

| Order | Gate | Exact check and expected result | Evidence URI / exit status | Result |
| --- | --- | --- | --- | --- |
| 1 | Shell/parse/build | TBD | TBD | Not run |
| 2 | Feature markers / interfaces | TBD | TBD | Not run |
| 3 | Required target change | TBD | TBD | Not run |
| 4 | Wiring / import / registration / reachability | TBD | TBD | Not run |
| 5 | Behavioral smoke and counterexamples | TBD | TBD | Not run |
| 6 | Task plugins: types, lint, security, schemas | TBD | TBD | Not run |
| 7 | Independent executable checker | TBD | TBD | Not run |
| 8 | Authorization: actual changed paths, effects, blast radius | TBD | TBD | Not evaluated |
| 9 | Plan-level integration suite | TBD | TBD | Not run |

For every required gate record start/end time, tool version, tested candidate
revision, result and retained output. Record a justified “not applicable” explicitly;
never silently omit a gate. Stop acceptance at the first failure. The final
integration suite runs after task gates, before declaring the plan complete.

- Already-done policy: TBD. If permitted, waive only gate 3 after proving the
  existing state; rerun all applicable correctness and authorization checks.
- Advisory model/human review: TBD. Record unavailable review; it cannot replace a
  mandatory gate. If human approval is required, it remains required separately.
- Verification failure: preserve exact evidence, restore safe baseline, retry only
  within the declared budget.
- Authority violation: contain/roll back the candidate and halt for human review;
  do not treat it as an ordinary model retry.
- Infrastructure failure: validate partial state before choosing resume or restart.
- Stale evidence: recheck candidate revision and external preconditions immediately
  before any authorized application.
- Final correctness decision: **not evaluated**.
- Separate application/merge/external-effect authorization: **not granted**.
