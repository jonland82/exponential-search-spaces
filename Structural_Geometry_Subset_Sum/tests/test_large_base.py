from dataclasses import replace
import random
import unittest

from Structural_Geometry_Subset_Sum.budget import Meter, ResourceLimit
from Structural_Geometry_Subset_Sum.compat import Limits, solve_dfs
from Structural_Geometry_Subset_Sum.solver import DEFAULTS, POLICIES, shared_dfs, solve_instance
from Structural_Geometry_Subset_Sum.structures.large_base import candidates, check, describe, detect


def reachable(weights):
    sums = {0:()}
    for index, weight in enumerate(weights):
        for value, chosen in list(sums.items()):
            sums.setdefault(value+weight, chosen+(index,))
    return sums


class GeometryTests(unittest.TestCase):
    def test_bounds_and_dp_against_independent_enumeration(self):
        rng = random.Random(4381)
        for trial in range(12):
            weights = tuple(rng.randrange(1, 28) for _ in range(7))
            sums = reachable(weights)
            for base in (2, 3, 8, 31):
                for target in range(-1, sum(weights)+2, 3):
                    geometry = describe(weights, target, base)
                    self.assertTrue(all(w == base*p+r for w, p, r in zip(weights, geometry.p, geometry.r)))
                    result = check(geometry, Meter(100000), max_work=100000,
                        max_q_count=1000, max_dp_bits=10_000_000, max_history_bits=100_000_000)
                    self.assertEqual(result["status"] == "yes", target in sums)
                    self.assertIn(result["status"], ("yes", "no"))
                    if result["witness"] is not None:
                        self.assertEqual(sum(weights[i] for i in result["witness"]), target)

    def test_signed_residuals_zero_quotients_and_duplicate_weights(self):
        weights = (1, 1, 7, 9, 15, 15)
        geometry = describe(weights, 24, 8)
        self.assertIn(0, geometry.p)
        self.assertTrue(any(r < 0 for r in geometry.r))
        self.assertTrue(any(r > 0 for r in geometry.r))
        result = check(geometry, Meter(100000), max_q_count=100)
        self.assertEqual(result["status"], "yes")
        self.assertEqual(len(set(result["witness"])), len(result["witness"]))

    def test_gap_certificate_and_gcd_grid(self):
        weights = (1001, 1999, 3002, 3997)
        geometry = describe(weights, 4500, 1000)
        self.assertEqual(geometry.q_count, 0)
        result = check(geometry, Meter(100))
        self.assertEqual((result["status"], result["reason"]), ("no", "aggregate_gap"))
        scaled = describe(tuple(w*7 for w in weights), 4500*7, 1000, divisor=7)
        self.assertEqual(scaled.p, geometry.p)
        self.assertEqual(scaled.r, geometry.r)

    def test_resource_interruption_never_becomes_no(self):
        geometry = describe((7, 11, 13, 19, 23), 31, 8)
        result = check(geometry, Meter(100000), max_work=1, max_q_count=100)
        self.assertEqual(result["status"], "unresolved")
        result = check(geometry, Meter(100000), max_dp_bits=1)
        self.assertEqual(result["status"], "unresolved")
        meter = Meter(100000, seconds=1e-12)
        with self.assertRaises(ResourceLimit):
            check(geometry, meter, max_q_count=100)

    def test_bounded_blind_detector(self):
        weights = tuple((1 << 24)*(i % 6+1)+(i % 7-3) for i in range(24))
        meter = Meter(100000)
        bases = candidates(weights, meter)
        self.assertLessEqual(len(bases), 24)
        self.assertIn(1 << 24, bases)
        geometry, count = detect(weights, sum(weights)//2, meter)
        self.assertLessEqual(count, 24)
        self.assertTrue(all(w == geometry.divisor*(geometry.base*p+r)
            for w, p, r in zip(weights, geometry.p, geometry.r)))
        self.assertEqual(detect((6, 12), 7, Meter(1000)), (None, 0))

    def test_shared_dfs_matches_existing_native_traversal(self):
        rng = random.Random(94)
        for n in (6, 8, 10):
            weights = tuple(rng.randrange(1, 60) for _ in range(n))
            for target in (0, 31, sum(weights)//2, sum(weights)+1):
                for cap in (20, 10000):
                    limits = Limits(max_work=cap, max_states=32768)
                    original = solve_dfs(weights, target, limits=limits)
                    adapted = shared_dfs(weights, target, limits, Meter(100000))
                    self.assertEqual((adapted.status, adapted.witness, adapted.reason),
                        (original.status, original.witness, original.reason))
                    self.assertEqual(adapted.stats["work"], original.stats["work"])

    def test_all_policies_small_decisions_and_witness_maps(self):
        rng = random.Random(238)
        for n in (8, 12):
            weights = tuple(rng.randrange(1, 100) for _ in range(n))
            sums = reachable(weights)
            for target in (-1, 0, sum(weights)//3, 2*sum(weights)//3, sum(weights)):
                for policy in POLICIES:
                    result = solve_instance(weights, target, policy, max_work=1000000)
                    self.assertEqual(result["status"] == "yes", target in sums)
                    self.assertIn(result["status"], ("yes", "no"))
                    if result["witness"] is not None:
                        self.assertEqual(sum(weights[i] for i in result["witness"]), target)
                    self.assertLessEqual(sum(result["component_seconds"].values()), result["seconds"]+1e-6)

    def test_internal_checks_and_original_index_witnesses(self):
        base = 1 << 16
        weights = tuple(base*(i % 4+1)+(i % 5-2) for i in range(15))+(base*6+base//3,)
        target = weights[-1]+weights[1]+weights[2]+weights[5]
        sums = reachable(weights)
        config = dict(DEFAULTS, max_bitset_bits=1, max_states=128, max_dp_bits=2000,
            stride=2, minimum_remaining=4, checkpoint_cap=32)
        result = solve_instance(weights, target, "selective_geometry", max_work=20000, config=config)
        self.assertTrue(any(event["depth"] > 0 for event in result["events"]))
        self.assertEqual(result["status"] == "yes", target in sums)
        self.assertIn(result["status"], ("yes", "no"))
        self.assertGreater(result["counts"]["internal_no"]+result["counts"]["internal_yes"], 0)

    def test_tiny_budgets_and_late_answers_are_unresolved(self):
        for policy in POLICIES:
            result = solve_instance((3, 5, 9, 12), 17, policy, max_work=1)
            self.assertEqual((result["status"], result["witness"]), ("unresolved", None))
            self.assertLessEqual(result["work"], 1)
            result = solve_instance((3, 5, 9, 12), 17, policy, max_work=10000, seconds=1e-12)
            self.assertEqual((result["status"], result["witness"]), ("unresolved", None))


if __name__ == "__main__":
    unittest.main()
