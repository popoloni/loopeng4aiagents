# Chapter 3: detailed reference

[Start with the chapter 3 walkthrough](../chapters/chapter-3.md).
This page preserves the technical mappings, assumptions and limits for deeper reading.

## Chapter-to-code mapping

| Manuscript location | API | Arithmetic and interpretation |
|---|---|---|
| `eq:quadratic-context` | `context_cost` | `I(N) = N*S + N*(N-1)*T/2`; cost = `(input_price*I + output_price*N*o)/1,000,000` with CLI prices per million tokens |
| `eq:cost-per-accepted` | `cost_per_accepted` | Complete candidate cost divided by independent acceptance probability |
| Accepted-outcome measurement practice and introductory example | `cohort_metrics` | Sum of **all** candidate costs divided by accepted count; sample size, acceptance, candidate mean, median, nearest-rank p90 |
| `eq:retry-cost` | `retry_policies` | Sum of each incremental cost weighted by the probability of reaching that attempt, plus terminal failure probability times human escalation cost |
| Retry decision paragraph | `retry_policies` | Append an attempt when `c < p*C_H`, conditional on reaching it; equality is break-even |
| `eq:bottleneck` | `bottleneck` | Minimum of specification, generation, verification, integration, release and operations capacity; report every tied constraint |
| `eq:verification-leverage` | `verification_leverage` | `(rework_reduction + failure_reduction)/verifier_cost`; equal periods required |
| `sec:econ-case-study`, five decisions and sensitivities | `evaluate`, `demo` | Complete case, every retry prefix, acceptance and verifier-cost sweeps, capacity before/after, and break-even thresholds |

Prices are USD in the supplied case, but the APIs accept any consistent
currency. Costs and capacity periods must not be mixed. No token-price service,
benchmark score or model-provider API is consulted.

## Reproduced results

| Calculation | Computed result | Chapter display |
|---|---|---|
| Introductory candidate ledger | 8 + 22 + 10 = 40 | $40 |
| Introductory cohort | 4,000 / 70 = 57.142857… | $57.14 |
| Cheaper-attempt comparison | 25 / 0.35 = 71.428571… | $71.43 |
| Full replay at 40 turns | 3,060,000 input + 36,000 output tokens | $9.72 |
| Compacted context at 40 turns | 960,000 input + 36,000 output tokens | $3.42 |
| Fresh context at 40 turns | 800,000 input + 36,000 output tokens | $2.94 |
| Human end-to-end baseline | 8 × 90 | $720 |
| One-shot accepted outcome | 128 / 0.68 = 188.235294… | $188.24 |
| Immediate human escalation | 350 | $350 |
| One autonomous attempt | 75 + 0.45 × 350 = 232.5 | $232.50 |
| Two autonomous attempts | 75 + 0.45 × 45 + 0.2475 × 350 = 181.875 | $181.88 |
| Three autonomous attempts | 95.25 + 0.2475 × 120 + 0.0495 × 350 = 142.275 | $142.28 |
| Four autonomous attempts | 124.95 + 0.0495 × 120 + 0.0396 × 350 = 144.75 | $144.75 |
| Weekly capacity before / after | Verification 52 / release 64 | 52 / 64 |
| Quarterly verifier leverage | (28,000 + 52,000) / 20,000 = 4 | 4.0 |
| Quarterly verifier break-even cost | 80,000, leverage = 1 | approximately $80,000 |
| Adverse acceptance | 128 / 0.30 = 426.666667… | $426.67 |

**No numerical mismatches** were found in these reproducible worked values.
Decimal arithmetic uses Python's default 28 significant digits. Display rounds
half up to two decimal places only at the end; in particular, 181.875 becomes
181.88 and 142.275 becomes 142.28. Intermediate retry results are not rounded.

## Assumptions and ambiguities preserved

* Only full replay has an explicit context equation. The alternative numbers
  imply `N*(S+6000)` for compaction and `N*(S+2000)` for fresh context. Both
  additional contexts are charged on **every** turn, including the first.
  A growing-then-capped history would give a different total; it is not silently
  substituted. No compaction-generation or cache-write charge is specified.
  The manuscript calls fresh context the "cheapest measured policy", but these
  figures are calculated from hypothetical case assumptions, not measurements
  of policy performance. This implementation makes no measured-policy claim.
* The $128 candidate ledger includes all listed categories but has no component
  allocation. The implementation does not invent review minutes or subtract
  an assumed review allowance. Context cost is illustrative and is not added
  again to the already complete candidate ledger.
* The $350 terminal human escalation and $720 human end-to-end baseline are
  distinct manuscript assumptions. Neither is substituted for the other.
  The retry-policy view and one-shot $128/0.68 view are separate ledgers and
  must not be added. Conditional probabilities account for earlier failures;
  the formula does not assert that attempts are independent.
* The minimum-cost prefix is three attempts **for the supplied costs and
  probabilities**, before latency, risk and human guardrails. The model does
  not discover new routes or recommend a provider. Ties choose the shortest
  prefix. An unreachable retry after certain success has no cost effect even
  though its conditional break-even calculation can still be displayed.
* Monthly demand is 100, while the capacities are weekly. The minimum-capacity
  result is a capacity bound, not evidence that 52 or 64 tasks actually arrive
  each week. There is no fabricated monthly savings or quarterly payback claim.
* The chapter's three-hours-of-review scenario lacks reviewer staffing and
  the original review allowance. Three hours at the stated $90/hour would
  cost $270 **if that rate applies to reviewers**, but neither incremental
  candidate cost nor review capacity can be established from the supplied
  data. The claim that review becomes binding cannot be numerically reproduced.
* A shared maker/verifier blind spot invalidates the acceptance evidence.
  The chapter supplies no correlation adjustment; the CLI reports this limit
  instead of manufacturing a corrected probability.
* The chapter requests distribution metrics but does not define their sample
  population or a p90 convention. `cohort_metrics` explicitly reports the
  **candidate-cost** distribution (including failed candidates), with
  nearest-rank p90. It cannot infer an accepted-outcome cost distribution
  without candidate-to-outcome attribution. The introductory comparison treats
  its candidates as equal-cost observations solely to reproduce its example.
* Benchmark percentages, cited workforce effects, contributor value, surplus
  sharing and organizational scenarios are contextual evidence, not parameters
  for a synthetic ROI formula. Human burden, learning, quality and operational
  guardrails remain separate assessments, as required by the chapter.

## Sensitivity and break-even

The JSON fixture sweeps acceptance over 10%, 30%, 50%, 68%, and 100%, holding
the $128 ledger fixed. Only 68% and 30% are manuscript case points. Against the
$720 human baseline, equality is at `128/720 = 17.777777…%` acceptance. This is
an algebraic threshold, not a safe operating target; below it the simplified
route is more costly. If candidate cost exceeds the baseline, the report marks
break-even as infeasible because the required acceptance exceeds 100%.

Verifier-cost sensitivity holds quarterly avoided costs at $80,000 and tries
$20,000, $40,000, $80,000 and $100,000: leverage is 4, 2, 1 and 0.8. At $80,000
the direct benefit is zero, not strictly positive. Benefit estimates, false
positives, maintenance, latency and escaped defects must be remeasured.

Every prefix of the retry sequence is evaluated, including no autonomous
attempts. The blind fourth attempt costs $120 versus its conditional
break-even cost of `0.20*350 = $70`; its expected overall cost increase is
`0.0495*(120-70) = $2.475`. Before/after capacity calculations show that more
generation alone does not relieve the verification constraint. `context_cost`
can also be called at different turn counts to compare replay and fixed-context
curves; tests check its cumulative-input formula against per-turn summation.

## Validation and limits

Inputs reject booleans masquerading as numbers, numeric strings, NaN/infinity,
negative costs/tokens/capacities, out-of-range probabilities, duplicate JSON
keys, missing/unknown fields, and invalid counts. Zero is valid for no turns,
free cost, no capacity, no retry success, and zero avoided loss. It is invalid
for acceptance denominators, accepted cohort counts, human baseline hours or
rate, and verifier-cost denominators. Retry probabilities may include both 0
and 1; one-shot acceptance is strictly greater than zero and at most 1.

Numerical inputs have an implementation bound of 10^18, and any nonzero input
must be at least 10^-18. Counts and list lengths are at most 10,000; scenario
files are at most 1,000,000 characters. These are computational bounds, not
claims about business feasibility. Empty retry lists support immediate human
handling; sensitivity and assumption lists must be nonempty.

Historical validation before the package refactor used Python 3.12.4: **20 unittest tests passed**, including
all reproduced values, sensitivity, break-even, boundary cases, invalid JSON,
CLI success and clean error exits. The editor reported no diagnostics in the
owned Python files. The editor test tool did not discover tests, so the focused
standard-library discovery command in the walkthrough was used. Python 3.10 syntax is
checked separately; execution on a Python 3.10 interpreter was not available.

## Chapter 5 local infrastructure extension

The Energy/TCO section of `chapter05_local_ai_loop.tex`, lines 375–630,
`sec:local-execution-tco`, applies the chapter 3 framework to local execution.
The following functions share the same numeric validation as the chapter 3
models. They perform arithmetic only; they do not collect measurements.

| Chapter 5 equation | Function | Units and formula |
|---|---|---|
| `eq:local-energy-run-cost` | `energy_cost` | kWh × currency/kWh |
| `eq:local-fixed-cost` | `local_fixed_cost` | `(hardware - residual)/months + maintenance + idle`, currency/month |
| Local/cloud cost comparison | `local_cloud_costs` | Local `fixed + volume*local_rate`; cloud `volume*cloud_rate`, currency/month |
| `eq:local-cloud-break-even` | `local_cloud_break_even` | `fixed/(cloud_rate-local_rate)`, common monthly volume units |
| `eq:local-carbon` | `operational_carbon` | kWh × kg CO2e/kWh, operational kg CO2e |
| `eq:local-cloud-accepted-cost` | Existing `cost_per_accepted` | Complete per-attempt cost / task-specific acceptance; separate from infrastructure volume calculations |

Run either form of the hypothetical example:

```sh
python -B -m loopeng economics --local-tco-demo
python -B -m examples.economics.local_tco
```

The [example entry point](../../examples/economics/local_tco.py) delegates to the
module's `local_tco_demo`. It reproduces the chapter's hardware calculation:
`2500/36 = 69.444444…`, displayed as **69.44 per month**. Residual, maintenance
and idle costs are zero solely for this amortization example. All other demo
inputs are invented and declared: 1 kWh, electricity price 0.25 currency/kWh,
grid intensity 0.4 kg CO2e/kWh, monthly volume 100 normalized units, local rate
0.10 and cloud rate 2.00 currency/unit. They are neither tariffs nor measured
workload results. No arithmetic mismatch was found in the hardware example.

The chapter expresses volume in millions of accounted tokens, but explicitly
warns that project accounted token events include replay and cache accounting
and **cannot be compared directly with API-billed tokens or unique tokens**.
The API therefore uses a caller-declared common volume unit. The example's
normalized units are hypothetical; it does not derive a conversion, reuse the
chapter's measured token count as API volume, or establish a local/cloud
advantage. A real comparison needs counting algorithms, consistent system
boundaries, and task-specific acceptance evidence.

For a nonpositive cloud-minus-local rate, break-even returns `None` (JSON
`null`): the formula has no finite positive-volume crossover establishing a
local advantage. With zero fixed cost and equal rates, costs coincide at every
volume; with zero fixed cost and a higher local rate, they coincide only at
zero. These degenerate equalities are not positive-volume break-even claims.
With positive rate savings and zero fixed cost, the formula returns zero.

Months must be a positive integer; residual cannot exceed purchase price.
Maintenance, idle, energy, tariffs, grid factors and volume must be nonnegative
and finite. Zero volume still incurs local fixed cost. Shared hardware needs
an explicit allocation rule; idle energy must not be charged twice. Carbon
covers operational energy only, not embodied hardware emissions. Wall-plug,
component, networking and cooling boundaries must match before comparison.
Neither route is asserted to be greener or economically preferable.

The subsequent pre-refactor focused suite contained **28 tests**, adding the 69.44 amortization
regression, residual/maintenance/idle arithmetic, energy and carbon, cost-curve
crossing, denominator and zero-fixed-cost cases, invalid inputs, and both local
example CLI entry points. The separate control-policy implementation is explained
in the [chapter 5 walkthrough](../chapters/chapter-5.md).
