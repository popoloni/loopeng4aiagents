# Chapter 2: The organization becomes a loop

[All chapters](../README.md) · [Previous: chapter 1](chapter-1.md) · [Next: chapter 3](chapter-3.md)

## What you will do

Decide who owns a loop, who checks its work, and who handles exceptions.
**This is a worksheet exercise, not a program.** There is no server, model,
package installation or terminal command required.

## Start with one concrete task

Use the small task you chose in [chapter 1](chapter-1.md), or choose a familiar
workflow such as preparing a refund recommendation. Do not begin by designing
an entire automated organization.

1. Open the [ownership and escalation worksheet](../../examples/governance/ownership-and-escalation.template.md)
   and save a copy in your own project.
2. Fill the outcome and accountable-owner fields.
3. Assign the six responsibilities in its table. They are functions, not a
   requirement to hire six people; record conflicts if one person holds several.
4. Fill the escalation rows: trigger, recipient, response target and backup.
5. Identify who may approve a merge, payment, deployment or policy exception.

## Record evidence separately from permission

Open the [evidence-record template](../../examples/governance/evidence-record.template.json).
For a real run, record its task ID, granted scope, versions, checks and final
disposition. For a paper exercise, label the record hypothetical and leave
unobserved results unknown.

For example, “the refund recommendation passed its checks” is evidence about
the recommendation. It is **not** permission to send money. Someone must own
that decision, and the execution needs its own confirmation.

## What a useful result looks like

You should have an ownership worksheet and a plan for collecting run evidence.
A colleague should know where a failed task goes, what decision is needed and
who is allowed to resume it. An unacknowledged handoff is not a resolved task.

These files are human records. No controller loads them automatically, and
completing them is not compliance certification or production approval.

## Try the idea in a simulation

[Chapter 6's support walkthrough](chapter-6.md) demonstrates a correct human
handoff and the difference between approval and execution confirmation.
For the cost of review and exceptions, continue to [chapter 3](chapter-3.md).
See the [coverage reference](../reference/coverage.md#chapter-2--the-organization-becomes-a-loop)
for organizational topics beyond the worksheets.
