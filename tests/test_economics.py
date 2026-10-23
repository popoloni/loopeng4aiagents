"""Executable manuscript comparisons, model invariants, and hostile input checks."""
import copy
from decimal import Decimal as D
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from loopeng.economics import calculations as e

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "examples/economics/chapter3.json"


class ChapterCaseTests(unittest.TestCase):
    def setUp(self):
        self.scenario = e.load_scenario(CASE)
        self.report = e.evaluate(self.scenario)

    def test_context_manuscript_and_tokens(self):
        for policy, tokens, cost in (("full", 3060000, "9.72"),
                                    ("compact", 960000, "3.42"),
                                    ("fresh", 800000, "2.94")):
            with self.subTest(policy=policy):
                result = self.report["context"][policy]
                self.assertEqual(result["input_tokens"], tokens)
                self.assertEqual(result["output_tokens"], 36000)
                self.assertEqual(result["cost"], D(cost))

    def test_introductory_cohorts(self):
        first, second = e.demo()["introductory_cohorts"]
        self.assertEqual(first["total_cost"], 4000)
        self.assertEqual(first["acceptance"], D(".7"))
        self.assertEqual(e.money(first["cost_per_accepted"]), "57.14")
        self.assertEqual(e.money(second["cost_per_accepted"]), "71.43")

    def test_accepted_baseline_and_sensitivity(self):
        outcome = self.report["outcome"]
        self.assertEqual(outcome["human_baseline"], 720)
        self.assertEqual(e.money(outcome["cost_per_accepted"]), "188.24")
        self.assertEqual(e.money(e.cost_per_accepted(128, D(".30"))), "426.67")
        threshold = outcome["break_even_acceptance"]
        self.assertAlmostEqual(float(threshold), 0.17777777777777778)
        self.assertAlmostEqual(float(e.cost_per_accepted(128, threshold)), 720)
        costs = [row["cost_per_accepted"] for row in self.report["sensitivity"]["acceptance"]]
        self.assertEqual(costs, sorted(costs, reverse=True))

    def test_retry_exact_and_manuscript_rounding(self):
        policies = self.report["retry_policies"]
        self.assertEqual([p["expected_cost"] for p in policies],
                         list(map(D, ["350", "232.50", "181.8750", "142.275000", "144.75000000"])))
        self.assertEqual([e.money(p["expected_cost"]) for p in policies],
                         ["350.00", "232.50", "181.88", "142.28", "144.75"])
        self.assertEqual(self.report["least_cost_prefix"], 3)
        self.assertEqual(policies[3]["human_probability"], D(".0495"))
        self.assertTrue(policies[3]["retry_below_break_even"])
        self.assertFalse(policies[4]["retry_below_break_even"])
        self.assertEqual(policies[4]["incremental_break_even_cost"], 70)

    def test_capacity_and_verifier(self):
        self.assertEqual(self.report["capacity_before"], {"capacity": 52, "bottlenecks": ["verification"]})
        self.assertEqual(self.report["capacity_after"], {"capacity": 64, "bottlenecks": ["release"]})
        self.assertEqual(self.report["verifier"], {"leverage": 4, "break_even_cost": 80000, "net_direct_benefit": 60000})
        rows = self.report["sensitivity"]["verifier"]
        self.assertEqual([r["leverage"] for r in rows], [4, 2, 1, D(".8")])
        self.assertEqual(rows[2]["net_direct_benefit"], 0)

    def test_zero_and_one_turn_context(self):
        for n in (0, 1, 2, 40):
            result = e.context_cost(n, 18000, 3000, 900, 3, 15)
            self.assertEqual(result["input_tokens"], sum(18000 + i * 3000 for i in range(n)))
        self.assertEqual(e.context_cost(0, 0, 0, 0, 0, 0)["cost"], 0)
        self.assertEqual(e.context_cost(1, 18000, 3000, 900, 3, 15, policy="compact", retained_tokens=6000)["input_tokens"], 24000)

    def test_retry_edge_probabilities_and_ties(self):
        self.assertEqual(e.retry_policies([], 350)[0]["expected_cost"], 350)
        never = e.retry_policies([{"cost": 20, "success": 0}], 350)
        self.assertEqual(never[-1]["expected_cost"], 370)
        certain = e.retry_policies([{"cost": 20, "success": 1}, {"cost": 999, "success": 0}], 350)
        self.assertEqual(certain[-1]["expected_cost"], 20)
        tie = e.retry_policies([{"cost": 70, "success": D(".2")}], 350)
        self.assertEqual(tie[-1]["expected_cost"], 350)
        self.assertFalse(tie[-1]["retry_below_break_even"])

    def test_capacity_ties_zero_and_generation_only_investment(self):
        capacities = dict.fromkeys(e.STAGES, 0)
        self.assertEqual(e.bottleneck(capacities)["bottlenecks"], list(e.STAGES))
        capacities = self.scenario["capacity_before"].copy()
        capacities["generation"] = 10000
        self.assertEqual(e.bottleneck(capacities)["capacity"], 52)

    def test_cohort_statistics_have_explicit_population(self):
        result = e.cohort_metrics([10, 20, 30, 100], 2)
        self.assertEqual(result["candidate_mean"], 40)
        self.assertEqual(result["candidate_median"], 25)
        self.assertEqual(result["candidate_p90"], 100)
        self.assertEqual(result["cost_per_accepted"], 80)
        self.assertEqual(e.cohort_metrics([4], 1)["candidate_p90"], 4)

    def test_no_feasible_acceptance_break_even(self):
        self.scenario["outcome"]["candidate_cost"] = 721
        self.assertFalse(e.evaluate(self.scenario)["outcome"]["break_even_feasible"])

    def test_input_is_not_mutated(self):
        before = copy.deepcopy(self.scenario)
        e.evaluate(self.scenario)
        self.assertEqual(before, self.scenario)


class LocalTcoTests(unittest.TestCase):
    def test_hardware_manuscript_69_44_per_month(self):
        fixed = e.local_fixed_cost(2500, 0, 36)
        self.assertEqual(fixed, D(2500) / 36)
        self.assertEqual(e.money(fixed), "69.44")

    def test_residual_maintenance_and_idle(self):
        self.assertEqual(e.local_fixed_cost(2500, 500, 20, 10, 5), 115)
        self.assertEqual(e.local_fixed_cost(2500, 2500, 36), 0)

    def test_energy_and_carbon_hypothetical(self):
        self.assertEqual(e.energy_cost(D("2.5"), D(".20")), D(".50"))
        self.assertEqual(e.operational_carbon(D("2.5"), D(".4")), 1)
        self.assertEqual(e.energy_cost(0, 1), 0)
        self.assertEqual(e.operational_carbon(1, 0), 0)

    def test_cost_curves_cross_at_break_even(self):
        volume = e.local_cloud_break_even(100, 1, 3)
        self.assertEqual(volume, 50)
        self.assertEqual(e.local_cloud_costs(100, volume, 1, 3), {"local_cost": 150, "cloud_cost": 150})
        for v in (0, 49, 51):
            costs = e.local_cloud_costs(100, v, 1, 3)
            self.assertEqual(costs["local_cost"] > costs["cloud_cost"], v < volume)

    def test_no_finite_break_even_and_zero_fixed_degeneracies(self):
        for fixed in (0, 100):
            for local, cloud in ((1, 1), (2, 1), (0, 0)):
                with self.subTest(fixed=fixed, local=local, cloud=cloud):
                    self.assertIsNone(e.local_cloud_break_even(fixed, local, cloud))
        self.assertEqual(e.local_cloud_break_even(0, 1, 2), 0)

    def test_invalid_fixed_cost_inputs(self):
        for args in ((2500, 2501, 36), (2500, 0, 0), (2500, 0, -1),
                     (2500, 0, 1.5), (2500, 0, True), (-1, 0, 36),
                     (2500, -1, 36), (2500, 0, 36, -1), (2500, 0, 36, 0, -1)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                e.local_fixed_cost(*args)

    def test_invalid_energy_carbon_rates_and_volume(self):
        for function, args in ((e.energy_cost, [1, 1]), (e.operational_carbon, [1, 1]),
                               (e.local_cloud_costs, [1, 1, 1, 1]),
                               (e.local_cloud_break_even, [1, 1, 1])):
            for index in range(len(args)):
                for invalid in (-1, float("inf"), float("nan"), True, "1"):
                    values = args.copy()
                    values[index] = invalid
                    with self.subTest(function=function.__name__, index=index, invalid=invalid), self.assertRaises(ValueError):
                        function(*values)

    def test_local_demo_and_example(self):
        report = e.local_tco_demo()
        self.assertTrue(report["hypothetical"])
        self.assertEqual(report["monthly_fixed_display"], "69.44")
        self.assertIsNone(report["equal_rates_break_even"])
        for module, args in (("loopeng", ["economics", "--local-tco-demo"]),
                             ("examples.economics.local_tco", [])):
            result = subprocess.run([sys.executable, "-B", "-m", module, *args], cwd=ROOT,
                                    text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["monthly_fixed_display"], "69.44")


class ValidationTests(unittest.TestCase):
    def test_numeric_domain(self):
        for value in (-1, True, "1", None, float("nan"), float("inf"), -float("inf"),
                      D("NaN"), D("sNaN"), D("Infinity"), 10**19, D("1e-19")):
            with self.subTest(value=str(value)), self.assertRaises(ValueError):
                e.number(value, "test")
        self.assertEqual(e.number(0, "test"), 0)
        self.assertEqual(e.number(D("1e-18"), "test"), D("1e-18"))

    def test_zero_denominators_and_probability_bounds(self):
        for p in (0, -0.1, 1.01, True):
            with self.subTest(p=p), self.assertRaises(ValueError):
                e.cost_per_accepted(128, p)
        self.assertEqual(e.cost_per_accepted(0, 1), 0)
        for cost in (0, -1):
            with self.assertRaises(ValueError):
                e.verification_leverage(1, 1, cost)
        self.assertEqual(e.verification_leverage(0, 0, 1)["leverage"], 0)

    def test_counts_and_cohort_bounds(self):
        for n in (-1, 1.5, True, 10001):
            with self.subTest(n=n), self.assertRaises(ValueError):
                e.context_cost(n, 1, 1, 1, 1, 1)
        for costs, accepted in (([], 0), ([1], 0), ([1], 2), ([1], True), ([-1], 1)):
            with self.subTest(costs=costs, accepted=accepted), self.assertRaises(ValueError):
                e.cohort_metrics(costs, accepted)

    def test_strict_schema(self):
        for path, value in ((["extra"], 1), (["hypothetical"], False), (["assumptions"], [""]),
                            (["monthly_tasks"], 0), (["context", "turns"], 2.5),
                            (["outcome", "human_hours"], 0), (["outcome", "hourly_rate"], -1),
                            (["capacity_before", "verification"], -1),
                            (["sensitivity", "acceptance_rates"], []),
                            (["sensitivity", "verifier_costs"], [0]),
                            (["retry", "attempts"], [{"cost": 1, "success": 2}])):
            scenario = e.load_scenario(CASE)
            target = scenario
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value
            with self.subTest(path=path), self.assertRaises(ValueError):
                e.evaluate(scenario)
        with self.assertRaises(ValueError):
            e.bottleneck({"generation": 10})
        with self.assertRaises(ValueError):
            e.context_cost(1, 1, 1, 1, 1, 1, policy="unknown")
        with self.assertRaises(ValueError):
            e.context_cost(1, 1, 1, 1, 1, 1, retained_tokens=1)

    def test_invalid_json(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "scenario.json"
            for content in ('{"x": NaN}', '{"x": Infinity}', '{"x":1,"x":2}', '{', ' ' * 1000001):
                path.write_text(content, encoding="utf-8")
                with self.subTest(content=content[:40]), self.assertRaises(ValueError):
                    e.load_scenario(path)


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, "-B", str(ROOT / "loopeng/__main__.py"), "economics", *args],
                              cwd=ROOT, text=True, capture_output=True, check=False)

    def test_demo(self):
        result = self.run_cli("--demo")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["manuscript_display"]["retry_costs"], ["350.00", "232.50", "181.88", "142.28", "144.75"])
        self.assertTrue(report["hypothetical"])

    def test_scenario(self):
        result = self.run_cli("--scenario", str(CASE))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["least_cost_prefix"], 3)

    def test_missing_file_and_exclusive_modes(self):
        for args in (("--scenario", "/nonexistent/economics.json"), (), ("--demo", "--scenario", str(CASE))):
            result = self.run_cli(*args)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn("Traceback", result.stderr)

    def test_invalid_scenario_clean_error(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.json"
            for content in ('[]', '{"hypothetical":false}', '{"x":NaN}'):
                path.write_text(content, encoding="utf-8")
                result = self.run_cli("--scenario", str(path))
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
