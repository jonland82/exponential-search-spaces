from dataclasses import replace
import random
import unittest

from Structural_Geometry_Subset_Sum.budget import Meter, ResourceLimit
from Structural_Geometry_Subset_Sum.structures.large_base import describe
from Structural_Geometry_Subset_Sum.structures.exception_core import choose_core, solve_core
from Structural_Geometry_Subset_Sum.exception_solver import POLICIES, solve_exceptions


class ExceptionCoreTests(unittest.TestCase):
    def test_complete_small_decisions_against_independent_mask_enumeration(self):
        rng = random.Random(841)
        for _ in range(30):
            n = rng.randrange(1, 10)
            weights = [rng.randrange(1, 100) for _ in range(n)]
            base = rng.randrange(2, 40)
            reachable = {sum(w for i, w in enumerate(weights) if mask >> i & 1) for mask in range(1 << n)}
            for target in (0, sum(weights)//2, rng.randrange(sum(weights)+1), sum(weights)+1):
                geometry = describe(weights, target, base)
                meter = Meter(1000000)
                plan = choose_core(geometry, meter, available_work=900000,
                    max_dp_bits=50, max_history_bits=1000)
                self.assertIsNotNone(plan)
                result = solve_core(geometry, plan, meter, max_work=900000)
                self.assertEqual(result["status"], "yes" if target in reachable else "no")
                self.assertEqual(result["core_builds"], 1)
                self.assertLessEqual(result["work"], plan.estimated_work)
                if result["witness"] is not None:
                    self.assertEqual(len(set(result["witness"])), len(result["witness"]))
                    self.assertEqual(sum(weights[i] for i in result["witness"]), target)
                if result["status"] == "no":
                    self.assertEqual(result["assignments"], 1 << len(plan.exceptions))

    def test_reuses_one_build_for_all_exception_assignments(self):
        weights = [100001, 200003, 300002, 145000, 265000]
        geometry = describe(weights, 450004, 100000)
        meter = Meter(100000)
        plan = choose_core(geometry, meter, available_work=90000, max_dp_bits=1000, max_history_bits=10000)
        self.assertEqual(len(plan.exceptions), 2)
        result = solve_core(geometry, plan, meter, max_work=90000)
        truth = any(sum(w for i, w in enumerate(weights) if mask >> i & 1) == geometry.target for mask in range(32))
        self.assertFalse(truth)
        self.assertEqual(result["status"], "no")
        self.assertEqual(result["core_builds"], 1)
        self.assertEqual(result["assignments"], 4)

    def test_signed_residuals_zero_quotients_duplicates_and_empty_core(self):
        for weights, target, base in (([1, 1, 9, 11, 19], 21, 10),
            ([9, 11, 19, 21], 30, 10), ([7, 13, 29], 20, 100)):
            geometry = describe(weights, target, base)
            meter = Meter(100000)
            plan = choose_core(geometry, meter, available_work=90000)
            result = solve_core(geometry, plan, meter, max_work=90000)
            self.assertEqual(result["status"], "yes")
            self.assertEqual(sum(weights[i] for i in result["witness"]), target)
        geometry = describe([10, 20, 30], 40, 100)
        meter = Meter(10000)
        plan = choose_core(geometry, meter, available_work=9000, max_dp_bits=1, max_history_bits=1)
        self.assertEqual(plan.core, ())
        result = solve_core(geometry, plan, meter, max_work=9000)
        self.assertEqual(result["status"], "yes")

    def test_partial_build_or_query_never_certifies_no(self):
        geometry = describe([100001, 200003, 300002, 145000, 265000], 450004, 100000)
        plan = choose_core(geometry, Meter(100000), available_work=90000, max_dp_bits=1000, max_history_bits=10000)
        for cap in (0, 1, 4, 8):
            result = solve_core(geometry, plan, Meter(100000), max_work=cap)
            self.assertEqual(result["status"], "unresolved")
        with self.assertRaises(ResourceLimit):
            solve_core(geometry, plan, Meter(100000, seconds=1e-12), max_work=90000)

    def test_gcd_grid_and_original_index_lifting(self):
        rng = random.Random(203)
        weights = [17*(1000000*rng.randrange(1, 7)+rng.randrange(-8, 9)) for _ in range(24)]
        weights[-3:] = [17*(8000000+q) for q in (310000, 330000, 360000)]
        for target in (sum(weights[::2]), sum(weights)-sum(weights[::3])):
            for policy in POLICIES:
                result = solve_exceptions(weights, target, policy, max_work=200000)
                if result["status"] == "yes" and result["witness"] is not None:
                    self.assertEqual(sum(weights[i] for i in result["witness"]), target)
                self.assertNotEqual(result["status"], "no")
                self.assertEqual(result["work"], sum(result["phase_work"].values()))

    def test_caps_and_live_deadlines_preserve_unresolved(self):
        weights = [1000000*i+i*i for i in range(1, 25)]
        for policy in POLICIES:
            for cap, seconds in ((1, None), (50, None), (100000, 1e-12)):
                result = solve_exceptions(weights, sum(weights[::2]), policy, max_work=cap, seconds=seconds)
                self.assertEqual(result["status"], "unresolved")
                self.assertLessEqual(result["work"], cap)
                self.assertEqual(result["work"], sum(result["phase_work"].values()))


if __name__ == "__main__":
    unittest.main()
