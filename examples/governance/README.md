# Governance worksheets

These are **unfilled, hypothetical design templates**, not approved policies,
execution configurations, audit evidence, or attestations of compliance. No
controller in this repository loads or enforces them. `null` means unknown or
unassigned; an empty list grants nothing; unchecked boxes mean not demonstrated.
Do not turn missing measurements into zeroes or copy illustrative book outcomes
into a real run record.

| Chapter | Worksheet | Use |
| --- | --- | --- |
| 1 | [Loop contract](loop-contract.template.json) | Specify all eight controls before delegating a task. |
| 2 | [Ownership and escalation](ownership-and-escalation.template.md) | Assign actual decision rights, capacity and lifecycle responsibility. |
| 2 | [Evidence record](evidence-record.template.json) | Capture observed actions, checks, versions and disposition for one run. |
| 5 | [Preflight](local-preflight.template.json) | Record route, runtime, isolation and recovery checks. |
| 5 | [Verification plan](verification-plan.template.md) | Define ordered gates and distinguish acceptance from authority. |
| 5 | [Operator checklist](operator-checklist.template.md) | Operate, stop, recover and review a bounded local run. |

Copy a worksheet to your own controlled project location, replace every applicable
placeholder, and attach evidence. Have the named owner review the resulting
contract under the project's actual policy. Record authorization separately from
test success. Keep secrets out of every worksheet; use secret identifiers only.

The JSON documents are records, not JSON Schemas. In particular they are not
compatible task inputs for the [Ralph state reader](../../loopeng/ralph/controller.py),
the [chapter 6 task CLI](../../loopeng/engineering.py), or the external Kowalski
framework without a deliberate adapter. The repository's source examples do not
provide an OS sandbox or organizational governance service.

See the [chapter coverage review](../../docs/reference/coverage.md) for manuscript
locations, implementation gaps and the external-stack boundary.
