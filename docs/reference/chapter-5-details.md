# Chapter 5: detailed reference

[Start with the chapter 5 walkthrough](../chapters/chapter-5.md).
This page preserves the technical mappings, assumptions and limits for deeper reading.

## Exact policy boundaries

Direct execution must be explicit. Unset mode and agent mode select the agent;
an edit strategy overrides direct; an explicit rewrite uses direct; otherwise a
target also supplied as context uses the agent when its size is strictly above
the declared threshold. The demo's 10,000-byte threshold is an authored example,
not a measured or universal manuscript constant.

The gate runner requires all nine gates in order. Each callable must return an
actual boolean; exceptions and truthy prose fail closed. The first failure stops
later calls. The CLI fixture supplies **synthetic** booleans to illustrate
ordering, not a fake claim that real commands or plugins ran. Library users must
provide actual project-owned checks. An already-done task may make its change
gate pass under an explicit idempotence policy; other gates must still run.

Counters are evaluated after an attempt: `attempts_used` includes it.
Retry/resume counters count continuations already granted; the returned budget
reserves the next continuation. The caller increments attempts and actual
elapsed time before evaluating the following result. A successful last allowed
attempt can advance, but a result at or after the duration deadline escalates.
An authorization violation always halts, including when tests pass.

Only TIMEOUT/AGENT_ERROR with externally established usable progress can resume.
Verification failure uses the hard-retry budget even if some bytes look useful.
The example does not assess whether a checkpoint really is safe: that requires
the real project checks and ownership described in the chapter.

## Deliberately not implemented here

This policy example does not implement live Claude Code Router/Headroom,
DFlash/MLX serving, security isolation, hardware power metering, automatic
rollback/commit, arbitrary verification plugins or a production control plane.
Those are external integration and operations work, not prerequisites for
running these safe reference examples. Use the chapter coverage audit for the
remaining manuscript-specific dependencies and review findings.
