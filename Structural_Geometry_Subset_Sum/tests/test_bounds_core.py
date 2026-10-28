import random
import unittest

from Structural_Geometry_Subset_Sum.budget import Meter, ResourceLimit
from Structural_Geometry_Subset_Sum.structures.large_base import describe
from Structural_Geometry_Subset_Sum.structures.exception_core import choose_core
from Structural_Geometry_Subset_Sum.structures.bounds_core import choose_fast, solve_bounds
from Structural_Geometry_Subset_Sum.bounds_solver import POLICIES, solve_bounds_portfolio


class BoundsCoreTests(unittest.TestCase):
    def test_exact_answers_against_exhaustive_subsets(self):
        rng = random.Random(8505)
        for _ in range(60):
            n = rng.randrange(1, 11)
            weights = [rng.randrange(1, 150) for _ in range(n)]
            reachable = {sum(w for i,w in enumerate(weights) if mask >> i & 1) for mask in range(1 << n)}
            for target in (0, sum(weights)//2, rng.randrange(sum(weights)+1), sum(weights)+1):
                g = describe(weights, target, rng.randrange(2, 70))
                plan, event = choose_fast(g, Meter(1000000), max_work=100000,
                    available_work=900000, max_dp_bits=70, max_history_bits=1500)
                original = choose_core(g, Meter(1000000), available_work=900000,
                    max_dp_bits=70, max_history_bits=1500)
                self.assertEqual(plan, original)
                self.assertIsNotNone(plan)
                results = {}
                for mode in ("bounds_only", "bounds_first", "fast_eager"):
                    parent = Meter(1000000)
                    result = solve_bounds(g, plan, parent, max_work=900000, mode=mode)
                    results[mode] = result
                    self.assertLessEqual(result["work"], plan.estimated_work)
                    self.assertEqual(parent.work, result["work"])
                    if mode != "bounds_only" or result["status"] != "unresolved":
                        self.assertEqual(result["status"], "yes" if target in reachable else "no")
                    if result["status"] == "no":
                        self.assertEqual(result["assignments"], result["total_assignments"])
                    if result["witness"] is not None:
                        self.assertEqual(len(result["witness"]), len(set(result["witness"])))
                        self.assertEqual(sum(weights[i] for i in result["witness"]), target)
                self.assertEqual(results["bounds_first"]["status"], results["fast_eager"]["status"])
                self.assertLessEqual(results["bounds_first"]["work"], results["fast_eager"]["work"])

    def test_bounds_gap_skips_build_but_interval_hole_is_unresolved(self):
        for target, expected in ((15, "no"), (20, "unresolved")):
            g = describe([10, 30], target, 10)
            plan, _ = choose_fast(g, Meter(10000), max_work=1000, available_work=9000)
            bounds = solve_bounds(g, plan, Meter(10000), max_work=9000, mode="bounds_only")
            self.assertEqual(bounds["status"], expected)
            self.assertEqual(bounds["core_builds"], 0)
            lazy = solve_bounds(g, plan, Meter(10000), max_work=9000, mode="bounds_first")
            self.assertEqual(lazy["status"], "no")
            self.assertEqual(lazy["core_builds"], int(target == 20))

    def test_partial_bounds_discovery_and_build_leave_unresolved(self):
        g = describe([100001, 200003, 300002, 145000, 265000], 450004, 100000)
        plan, _ = choose_fast(g, Meter(100000), max_work=10000, available_work=90000,
            max_dp_bits=1000, max_history_bits=10000)
        self.assertEqual(len(plan.exceptions), 2)
        for cap in (0, 1, 4, 8):
            for mode in ("bounds_only", "bounds_first", "fast_eager"):
                r = solve_bounds(g, plan, Meter(100000), max_work=cap, mode=mode)
                self.assertEqual(r["status"], "unresolved")
                self.assertLessEqual(r["work"], cap)
        parent = Meter(100000)
        missing, event = choose_fast(g, parent, max_work=1, available_work=90000)
        self.assertIsNone(missing)
        self.assertEqual(event["reason"], "discovery_cap")
        self.assertLess(parent.work, 100000)
        with self.assertRaises(ResourceLimit):
            solve_bounds(g, plan, Meter(100000, seconds=1e-12), max_work=90000, mode="bounds_first")

    def test_signed_zero_quotients_empty_core_and_gcd_grid(self):
        for weights,target,base,divisor in (([1,1,9,11,19],21,10,1),
                ([10,20,30],40,100,1), ([17*9,17*11,17*19,17*21],17*30,10,17)):
            g = describe(weights,target,base,divisor)
            plan, _ = choose_fast(g,Meter(100000),max_work=10000,available_work=90000)
            if weights == [10,20,30]:
                plan, _ = choose_fast(g,Meter(100000),max_work=10000,available_work=90000,
                    max_dp_bits=1,max_history_bits=1)
                self.assertEqual(plan.core, ())
            result = solve_bounds(g,plan,Meter(100000),max_work=90000,mode="bounds_first")
            self.assertEqual(result["status"], "yes")
            self.assertEqual(sum(weights[i] for i in result["witness"]), target)

    def test_portfolio_work_deadlines_and_original_index_witnesses(self):
        weights = [17*(1000000*i+i*i) for i in range(1,25)]
        target = sum(weights[::2])
        for policy in POLICIES:
            r = solve_bounds_portfolio(weights,target,policy,max_work=200000)
            self.assertNotEqual(r["status"], "no")
            if r["witness"] is not None:
                self.assertEqual(sum(weights[i] for i in r["witness"]),target)
            self.assertEqual(r["work"], sum(r["phase_work"].values()))
            for cap,seconds in ((1,None),(50,None),(100000,1e-12)):
                r = solve_bounds_portfolio(weights,target,policy,max_work=cap,seconds=seconds)
                self.assertEqual(r["status"], "unresolved")
                self.assertLessEqual(r["work"],cap)
                self.assertEqual(r["work"],sum(r["phase_work"].values()))


if __name__ == "__main__":
    unittest.main()
