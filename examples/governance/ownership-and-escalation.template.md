# Ownership, evidence and escalation worksheet

**UNFILLED / HYPOTHETICAL / NOT APPROVED.** Replace `TBD` with real assignments
and evidence. Role names describe responsibilities, not six mandatory hires.
This worksheet does not grant access or authorize execution.

- Loop / mission / contract revision: TBD
- Business outcome, non-goals and risk tier: TBD
- Accountable delegation and acceptance owner: TBD
- Validity period, next review, expiry and retirement trigger: TBD

| Function | Named person or team | Decision rights | Backup | Evidence required |
| --- | --- | --- | --- | --- |
| Intent Owner | TBD | Outcome, constraints, scope | TBD | Reviewed contract and counterexamples |
| Loop Engineer / Operator | TBD | Configure and stop execution within granted scope | TBD | Configuration, budgets, run state |
| Domain Builder | TBD | Propose implementation and architecture | TBD | Candidate diff and rationale |
| Independent Verifier | TBD | Assess evidence; cannot silently waive required gates | TBD | Protected checks, calibration and outputs |
| Platform / Governance Steward | TBD | Identity, environments, policy and retention | TBD | Enforced controls and access decisions |
| Human Escalation Owner | TBD | Resolve exceptions within explicit authority | TBD | Structured handoff and recorded decision |

- Separation of duties and conflicts if roles are combined: TBD
- Who may approve a scope change, waiver, merge, deployment or external effect: TBD
- Actual approval record (identity, time, scope and revision): **none**
- Retention/access/redaction policy for the [evidence record](evidence-record.template.json): TBD

## Escalation contract

| Trigger | Required response | Assigned owner / channel | Response target |
| --- | --- | --- | --- |
| Missing authority, denied path or excessive blast radius | Halt; preserve evidence; contain candidate | TBD | TBD |
| Required verifier unavailable or contradictory evidence | Reject acceptance; diagnose or hand off | TBD | TBD |
| Retry, resume, time, token or monetary budget exhausted | Stop; preserve safe baseline and failed attempts | TBD | TBD |
| Ambiguous intent or unavailable dependency | Leave task unresolved; request a bounded decision | TBD | TBD |
| Exception queue exceeds capacity | Reduce admissions/scope; preserve unresolved queue | TBD | TBD |
| Incident or unaccounted external effect | Stop admissions; revoke credentials; contain effects | TBD | TBD |

Handoff fields: run/task ID; contract and policy revisions; current checkpoint;
exact failure/exit code; changed paths and external operation IDs; budgets consumed
and remaining; attempts already tried; impact/severity; decision required; recipient;
time sent and acknowledged; deadline; disposition. Store identifiers, not credentials.

- Exception arrival rate and measurement window: TBD
- Available qualified reviewer minutes in the same window: TBD
- Expected handling minutes per exception and maximum queue age: TBD
- Queue limit, admission throttle and backup route if owner unavailable: TBD
- Resume authority and required new evidence: TBD

## Balanced review and lifecycle

| Dimension | Baseline / measurement window / source | Target | Observed result |
| --- | --- | --- | --- |
| Outcome: user/business task success | TBD | TBD | Unmeasured |
| Flow: lead time, review queue, batch size, recovery | TBD | TBD | Unmeasured |
| Quality: defects, false acceptance, evidence completeness | TBD | TBD | Unmeasured |
| Control: retries, interventions, denials, time to safe stop | TBD | TBD | Unmeasured |
| Economics: cost per accepted outcome including review/rework | TBD | TBD | Unmeasured |
| Human system: understanding, trust, learning, exception load | TBD | TBD | Unmeasured |

- Context owners, freshness checks and contradiction resolution: TBD
- Verified failure → proposed lesson → human review → regression check: TBD
- Apprenticeship/manual practice preserved for this workflow: TBD
- Recertification and retirement procedure, including scheduler shutdown: TBD
- Owner review outcome and date: **not reviewed**
