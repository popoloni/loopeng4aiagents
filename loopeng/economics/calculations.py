"""Chapter 3 hypothetical economics; standard library, Python 3.10+.

Decimal arithmetic preserves the case's half-cent rounding. No live prices,
production acceptance estimates, or business recommendations are inferred.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import json
from pathlib import Path
import sys
from typing import Any

STAGES = ("specification", "generation", "verification", "integration", "release", "operations")
MAX_VALUE = Decimal("1e18")
MIN_NONZERO = Decimal("1e-18")
MAX_ITEMS = 10000


def number(value: Any, name: str, *, positive: bool = False,
           maximum: Decimal = MAX_VALUE) -> Decimal:
    """Reject booleans, strings, nonfinite numbers and unsupported magnitudes."""
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise ValueError(f"{name} must be a number")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f"{name} must be a finite number") from exc
    if not result.is_finite() or result < 0 or result > maximum or (positive and result == 0):
        interval = "(0" if positive else "[0"
        raise ValueError(f"{name} must be finite and in {interval}, {maximum}]")
    if result and result < MIN_NONZERO:
        raise ValueError(f"{name} nonzero magnitude must be at least {MIN_NONZERO}")
    return result


def count(value: Any, name: str, *, positive: bool = False) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    number(value, name, positive=positive, maximum=Decimal(MAX_ITEMS))
    return value


def probability(value: Any, name: str, *, positive: bool = False) -> Decimal:
    return number(value, name, positive=positive, maximum=Decimal(1))


def fields(value: Any, required: set[str], name: str) -> dict:
    if not isinstance(value, dict) or set(value) != required:
        raise ValueError(f"{name} must contain exactly: {', '.join(sorted(required))}")
    return value


def items(value: Any, name: str, *, nonempty: bool = True) -> list:
    if not isinstance(value, list) or len(value) > MAX_ITEMS or (nonempty and not value):
        raise ValueError(f"{name} must be a list with {'1' if nonempty else '0'}..{MAX_ITEMS} items")
    return value


def context_cost(turns: int, static_tokens: Any, history_tokens: Any,
                 output_tokens: Any, input_per_million: Any, output_per_million: Any,
                 *, policy: str = "full", retained_tokens: Any = 0) -> dict:
    """eq:quadratic-context; fixed retained context is charged on every turn."""
    n = count(turns, "turns")
    s, t, o, pi, po, retained = [number(v, k) for k, v in (
        ("static_tokens", static_tokens), ("history_tokens", history_tokens),
        ("output_tokens", output_tokens), ("input_per_million", input_per_million),
        ("output_per_million", output_per_million), ("retained_tokens", retained_tokens))]
    if policy not in ("full", "compact", "fresh"):
        raise ValueError("policy must be full, compact, or fresh")
    if policy == "full" and retained:
        raise ValueError("full replay does not take retained_tokens")
    inputs = n * s + Decimal(n * (n - 1) // 2) * t if policy == "full" else n * (s + retained)
    outputs = n * o
    return {"input_tokens": inputs, "output_tokens": outputs,
            "cost": (pi * inputs + po * outputs) / 1000000}


def cost_per_accepted(candidate_cost: Any, acceptance: Any) -> Decimal:
    """eq:cost-per-accepted; zero acceptance has no defined finite estimate."""
    return number(candidate_cost, "candidate_cost") / probability(acceptance, "acceptance", positive=True)


def cohort_metrics(costs: list, accepted: int) -> dict:
    """All candidate costs / accepted count; distribution describes candidates."""
    values = sorted(number(v, "candidate cost") for v in items(costs, "costs"))
    n = len(values)
    a = count(accepted, "accepted", positive=True)
    if a > n:
        raise ValueError("accepted cannot exceed candidate count")
    total = sum(values, Decimal(0))
    return {"sample_size": n, "accepted": a, "acceptance": Decimal(a) / n,
            "total_cost": total, "cost_per_accepted": total / a,
            "candidate_mean": total / n,
            "candidate_median": (values[(n - 1) // 2] + values[n // 2]) / 2,
            "candidate_p90": values[(9 * n + 9) // 10 - 1]}


def retry_policies(attempts: list, human_escalation: Any) -> list[dict]:
    """eq:retry-cost, each prefix including immediate human escalation.

    Probabilities are conditional on all earlier failures, not independent priors.
    """
    human = number(human_escalation, "human_escalation")
    survival, spent = Decimal(1), Decimal(0)
    result = [{"attempts": 0, "expected_cost": human, "human_probability": survival}]
    for k, attempt in enumerate(items(attempts, "attempts", nonempty=False), 1):
        fields(attempt, {"cost", "success"}, f"attempt {k}")
        cost = number(attempt["cost"], "attempt cost")
        p = probability(attempt["success"], "conditional success")
        spent += survival * cost
        survival *= 1 - p
        result.append({"attempts": k, "expected_cost": spent + survival * human,
                       "human_probability": survival,
                       "incremental_break_even_cost": p * human,
                       "retry_below_break_even": cost < p * human})
    return result


def bottleneck(capacities: dict) -> dict:
    """eq:bottleneck: an upper capacity bound, not realized demand or queue time."""
    fields(capacities, set(STAGES), "capacities")
    values = {k: number(v, k) for k, v in capacities.items()}
    minimum = min(values.values())
    return {"capacity": minimum, "bottlenecks": [k for k in STAGES if values[k] == minimum]}


def verification_leverage(rework_reduction: Any, failure_reduction: Any, cost: Any) -> dict:
    """eq:verification-leverage, with benefits and cost in the same period."""
    benefit = number(rework_reduction, "rework_reduction") + number(failure_reduction, "failure_reduction")
    full_cost = number(cost, "verifier cost", positive=True)
    return {"leverage": benefit / full_cost, "break_even_cost": benefit,
            "net_direct_benefit": benefit - full_cost}


def energy_cost(energy_kwh: Any, price_per_kwh: Any) -> Decimal:
    """Chapter 5 eq:local-energy-run-cost, in a consistent currency."""
    return number(energy_kwh, "energy_kwh") * number(price_per_kwh, "price_per_kwh")


def local_fixed_cost(hardware: Any, residual: Any, months: int,
                     maintenance: Any = 0, idle: Any = 0) -> Decimal:
    """eq:local-fixed-cost; maintenance and idle are monthly allocated costs."""
    purchase = number(hardware, "hardware")
    resale = number(residual, "residual")
    life = count(months, "months", positive=True)
    if resale > purchase:
        raise ValueError("residual cannot exceed hardware purchase cost")
    return ((purchase - resale) / life + number(maintenance, "maintenance")
            + number(idle, "idle"))


def local_cloud_costs(fixed: Any, volume: Any, local_rate: Any, cloud_rate: Any) -> dict:
    """Monthly infrastructure costs; volume and both rates need a common unit.

    Project accounted token events are not directly comparable to API tokens.
    Any common-unit normalization is an external assumption, not proven here.
    """
    base = number(fixed, "fixed")
    amount = number(volume, "volume")
    local = number(local_rate, "local_rate")
    cloud = number(cloud_rate, "cloud_rate")
    return {"local_cost": base + amount * local, "cloud_cost": amount * cloud}


def local_cloud_break_even(fixed: Any, local_rate: Any, cloud_rate: Any) -> Decimal | None:
    """eq:local-cloud-break-even; None when cloud_rate - local_rate <= 0.

    None means no finite positive-volume crossover from the formula. With
    zero fixed cost, equality at zero (or all volumes for equal rates) remains
    possible; it does not establish a positive-volume local cost advantage.
    """
    base = number(fixed, "fixed")
    difference = number(cloud_rate, "cloud_rate") - number(local_rate, "local_rate")
    return base / difference if difference > 0 else None


def operational_carbon(energy_kwh: Any, grid_kg_per_kwh: Any) -> Decimal:
    """eq:local-carbon: operational kg CO2e, excluding embodied emissions."""
    return number(energy_kwh, "energy_kwh") * number(grid_kg_per_kwh, "grid_kg_per_kwh")


def local_tco_demo() -> dict:
    """Hypothetical chapter 5 arithmetic; no measurements or live tariffs."""
    fixed = local_fixed_cost(2500, 0, 36)
    volume, local, cloud = 100, Decimal("0.10"), Decimal("2.00")
    return {
        "hypothetical": True,
        "assumptions": [
            "Chapter 5 hardware example: 2500 currency units, zero residual, 36 months; maintenance and idle set to zero only for this example.",
            "Illustrative run: 1 kWh, electricity 0.25 currency/kWh, grid intensity 0.4 kg CO2e/kWh; these are not measurements or live rates.",
            "Illustrative monthly volume 100 common normalized units; local rate 0.10 and cloud rate 2.00 currency/unit.",
            "Accounted token events include replay/cache accounting and are incomparable directly with API-billed tokens; no normalization is established by this demo.",
            "Infrastructure arithmetic excludes acceptance differences, rework and human review; no business or environmental superiority is inferred.",
            "Allocate shared hardware explicitly and avoid double-counting idle energy; carbon boundaries must match and exclude embodied emissions here."
        ],
        "monthly_fixed_cost": fixed,
        "monthly_fixed_display": money(fixed),
        "energy_cost": energy_cost(1, Decimal("0.25")),
        "operational_carbon_kg": operational_carbon(1, Decimal("0.4")),
        "monthly_costs": local_cloud_costs(fixed, volume, local, cloud),
        "break_even_volume": local_cloud_break_even(fixed, local, cloud),
        "equal_rates_break_even": local_cloud_break_even(fixed, local, local),
    }


def evaluate(scenario: dict) -> dict:
    """Validate a complete explicit scenario and calculate all five chapter models."""
    fields(scenario, {"hypothetical", "assumptions", "monthly_tasks", "context", "outcome",
                      "retry", "capacity_before", "capacity_after", "verifier", "sensitivity"}, "scenario")
    if scenario["hypothetical"] is not True:
        raise ValueError("hypothetical must be true: this model is an illustrative calculation")
    assumptions = items(scenario["assumptions"], "assumptions")
    if any(not isinstance(a, str) or not a.strip() for a in assumptions):
        raise ValueError("assumptions must be nonempty strings")
    count(scenario["monthly_tasks"], "monthly_tasks", positive=True)
    ctx = fields(scenario["context"], {"turns", "static_tokens", "history_tokens", "output_tokens",
                 "input_per_million", "output_per_million", "compact_tokens", "external_state_tokens"}, "context")
    common = {k: v for k, v in ctx.items() if k not in ("compact_tokens", "external_state_tokens")}
    contexts = {"full": context_cost(**common),
                "compact": context_cost(**common, policy="compact", retained_tokens=ctx["compact_tokens"]),
                "fresh": context_cost(**common, policy="fresh", retained_tokens=ctx["external_state_tokens"])}
    outcome = fields(scenario["outcome"], {"candidate_cost", "acceptance", "human_hours", "hourly_rate"}, "outcome")
    baseline = number(outcome["human_hours"], "human_hours", positive=True) * number(outcome["hourly_rate"], "hourly_rate", positive=True)
    candidate = number(outcome["candidate_cost"], "candidate_cost")
    accepted = cost_per_accepted(candidate, outcome["acceptance"])
    retry = fields(scenario["retry"], {"attempts", "human_escalation"}, "retry")
    policies = retry_policies(**retry)
    verifier = fields(scenario["verifier"], {"rework_reduction", "failure_reduction", "cost"}, "verifier")
    leverage = verification_leverage(**verifier)
    sensitivity = fields(scenario["sensitivity"], {"acceptance_rates", "verifier_costs"}, "sensitivity")
    acceptance_curve = [{"acceptance": probability(p, "sensitivity acceptance", positive=True),
                         "cost_per_accepted": cost_per_accepted(candidate, p)}
                        for p in items(sensitivity["acceptance_rates"], "acceptance_rates")]
    verifier_curve = [{"cost": number(c, "sensitivity verifier cost", positive=True),
                      **verification_leverage(verifier["rework_reduction"], verifier["failure_reduction"], c)}
                     for c in items(sensitivity["verifier_costs"], "verifier_costs")]
    return {"hypothetical": True, "assumptions": assumptions,
            "monthly_tasks": scenario["monthly_tasks"], "context": contexts,
            "outcome": {"human_baseline": baseline, "cost_per_accepted": accepted,
                        "break_even_acceptance": candidate / baseline,
                        "break_even_feasible": candidate <= baseline},
            "retry_policies": policies,
            "least_cost_prefix": min(policies, key=lambda row: row["expected_cost"])["attempts"],
            "capacity_before": bottleneck(scenario["capacity_before"]),
            "capacity_after": bottleneck(scenario["capacity_after"]),
            "verifier": leverage,
            "sensitivity": {"acceptance": acceptance_curve, "verifier": verifier_curve},
            "limits": ["Hypothetical arithmetic, not financial advice or a production recommendation.",
                       "Candidate ledger and retry ledger are separate views; do not add them.",
                       "Capacity is per week; monthly demand does not establish realized throughput.",
                       "Three-hour review scenario lacks staffing and baseline review allowance.",
                       "Correlated maker/verifier blind spots invalidate acceptance evidence; no numeric correction is supplied.",
                       "Human burden and quality thresholds require separate evidence and guardrails."]}


def _unique_object(pairs: list) -> dict:
    result: dict = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_scenario(path: Path) -> dict:
    """Strict JSON: reject duplicate keys, NaN, infinity, oversized documents."""
    def invalid_constant(value: str) -> None:
        raise ValueError(f"nonfinite JSON constant: {value}")

    with path.open("r", encoding="utf-8") as stream:
        content = stream.read(1_000_001)
    if len(content) > 1_000_000:
        raise ValueError("scenario exceeds 1,000,000 characters")
    return json.loads(content, parse_float=Decimal, parse_constant=invalid_constant,
                      object_pairs_hook=_unique_object)


def money(value: Decimal) -> str:
    """Round only for display, half up to cents."""
    return format(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), ".2f")


def demo() -> dict:
    """Run the checked-in transcription, plus the chapter's introductory cohort."""
    path = Path(__file__).resolve().parents[2] / "examples" / "economics" / "chapter3.json"
    result = evaluate(load_scenario(path))
    result["introductory_cohorts"] = [cohort_metrics([8 + 22 + 10] * 100, 70),
                                      cohort_metrics([25] * 100, 35)]
    result["manuscript_display"] = {
        "context_costs": {k: money(v["cost"]) for k, v in result["context"].items()},
        "accepted_cost": money(result["outcome"]["cost_per_accepted"]),
        "retry_costs": [money(v["expected_cost"]) for v in result["retry_policies"]],
        "adverse_acceptance_cost": money(cost_per_accepted(128, Decimal("0.30")))}
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--demo", action="store_true", help="reproduce the chapter's hypothetical case")
    choice.add_argument("--local-tco-demo", action="store_true", help="chapter 5 hypothetical infrastructure arithmetic")
    choice.add_argument("--scenario", type=Path, help="complete JSON scenario (see examples/economics)")
    args = parser.parse_args(argv)
    try:
        if args.local_tco_demo:
            result = local_tco_demo()
        else:
            result = demo() if args.demo else evaluate(load_scenario(args.scenario))
        print(json.dumps(result, indent=2, default=str, allow_nan=False))
    except (ValueError, OSError, RecursionError, InvalidOperation) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    sys.exit(main())
