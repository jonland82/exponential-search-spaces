"""Check witnesses, coverage, bounds, and failures against independent oracles."""

import itertools
import random
import unittest

from certified_approximation import (
    METHODS, _Context, _build_summary, _interval_distance, _query_pair,
    brute_force_distance, solve,
)


class CertifiedApproximationTests(unittest.TestCase):
    def check_result(self, weights, target, tolerance, method, greedy=False, max_states=65_536):
        optimum = brute_force_distance(weights, target)
        answer = solve(weights, target, tolerance, method, greedy=greedy, max_states=max_states)
        witnessed = sum(weight for i, weight in enumerate(weights) if answer.subset_mask >> i & 1)
        self.assertEqual(witnessed, answer.subset_sum)
        self.assertEqual(abs(witnessed - target), answer.upper)
        self.assertLessEqual(answer.lower, optimum)
        self.assertLessEqual(optimum, answer.upper)
        if answer.status == "certified":
            self.assertLessEqual(answer.width, tolerance)
        else:
            self.assertEqual(answer.status, "state_limit")
        if tolerance == 0 and answer.status == "certified":
            self.assertEqual(answer.lower, optimum)
            self.assertEqual(answer.upper, optimum)

    def test_exhaustive_small_lists(self):
        for n in range(5):
            for weights in itertools.combinations_with_replacement(range(1, 5), n):
                weights = list(weights)
                for target in range(-1, sum(weights) + 2):
                    for tolerance in (0, 1, 3):
                        for method in METHODS:
                            self.check_result(weights, target, tolerance, method)

    def test_random_and_large_integer_instances(self):
        rng = random.Random(20261022)
        for n in (8, 12, 16):
            for seed in range(5):
                scale = 1 if seed % 2 else 10**16
                weights = [rng.randrange(1, 100) * scale + rng.randrange(5) for _ in range(n)]
                target = rng.randrange(sum(weights) + 1)
                for tolerance in (0, 1, max(1, sum(weights) // 100)):
                    for greedy in (False, True):
                        for method in METHODS:
                            self.check_result(weights, target, tolerance, method, greedy)

    def test_summary_covers_every_true_sum(self):
        weights = [3, 7, 11, 19, 41, 83]
        actual = {sum(weight for i, weight in enumerate(weights) if mask >> i & 1) for mask in range(1 << len(weights))}
        for multiplicative in (False, True):
            context = _Context(weights, 91, 24, 1000)
            # Disable witness-based early termination to inspect the whole summary.
            context.check_witness = lambda: None
            reps, error = _build_summary(
                [(weight, 1 << i) for i, weight in enumerate(weights)], context,
                additive_step=4, multiplicative=multiplicative, total_items=len(weights),
            )
            self.assertLessEqual(error, 24)
            for value in actual:
                self.assertTrue(any(rep <= value <= rep + error for rep, _ in reps))
            for value, mask in reps:
                self.assertEqual(value, sum(weight for i, weight in enumerate(weights) if mask >> i & 1))

    def test_pair_query_matches_cartesian_product(self):
        rng = random.Random(17)
        for _ in range(250):
            left = [(x, 0) for x in sorted({0, *[rng.randrange(100) for _ in range(10)]})]
            right = [(x, 0) for x in sorted({0, *[rng.randrange(100) for _ in range(10)]})]
            target, error = rng.randrange(201), rng.randrange(20)
            context = _Context([left[-1][0] + right[-1][0]], target, 0, 1000)
            context.check_witness = lambda: None
            # Do not introduce complement witnesses unrelated to these synthetic lists.
            original_consider = context.consider
            context.consider = lambda rep: original_consider(rep, complement=False)
            lower = _query_pair(left, right, error, context)
            pairs = [a + b for a, _ in left for b, _ in right]
            self.assertEqual(lower, min(_interval_distance(target, value, error) for value in pairs))
            self.assertEqual(context.upper, min(abs(target - value) for value in pairs))

    def test_resource_limit_preserves_honest_bounds(self):
        for method in METHODS:
            self.check_result([11, 23, 47, 97, 199, 401], 333, 0, method, max_states=2)
            answer = solve([11, 23, 47, 97, 199, 401], 333, 0, method, greedy=False, max_states=2)
            self.assertEqual(answer.status, "state_limit")

    def test_invalid_inputs(self):
        for args in (([0], 1, 0), ([-1], 1, 0), ([1], 1, -1), ([1], 1.5, 0)):
            with self.assertRaises(ValueError):
                solve(*args)


if __name__ == "__main__":
    unittest.main()
