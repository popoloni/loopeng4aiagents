# Chapter 1: Foundations and critical assessment

[All chapters](../README.md) · [Next: chapter 2](chapter-2.md)

## What you will do

Design a small loop before trying to automate it. The result is a written
contract: what the worker may do, what proves success, and when it must stop.
**There is no chapter 1 application to install or run.** You need only a text editor.

## Start here: read, then fill a worksheet

1. Read [listing 001](../../Code/listing_001.txt) as an illustration of repeated
   execution. Do not paste it into a terminal: an unbounded repeat command is not
   the recommended runnable loop.
2. Open the [loop contract template](../../examples/governance/loop-contract.template.json).
3. Save a copy in your own project. Keep the repository's template unchanged.
4. Begin with `durable_intent.objective`, `acceptance_criteria`,
   `bounded_work.allowed_write_paths`, `resource_budgets` and
   `terminal_escalation.owner`. Complete the remaining fields before real use.

For a **hypothetical exercise**, choose “repair an integer addition function.”
Write down: the single file the worker may change; examples that must pass;
who owns those checks; a finite attempt/time budget; and who receives failures.
Do not write “keep trying until it works” as a stop rule.

## What a useful result looks like

Another reader should be able to answer:

- What counts as success, independently of what the worker says?
- Which changes and external actions are forbidden?
- What happens if a check fails or a budget runs out?
- Who can approve a scope change or accept the result?

`null` means unknown, not zero. An empty permission list grants nothing.
Leave approval fields unapproved during the exercise. Filling a JSON document
does not create runtime enforcement or grant authority.

## If you want to see a loop run

Continue to [chapter 4's offline demonstration](chapter-4.md). It supplies a
complete controller and worker, unlike a printed snippet. No LLM is needed.

## Where to go next

Use [chapter 2](chapter-2.md) to assign responsibilities around your contract.
The [coverage reference](../reference/coverage.md#chapter-1--foundations-and-critical-assessment)
explains which chapter concepts are implemented and which need organizational
or external-system work.
