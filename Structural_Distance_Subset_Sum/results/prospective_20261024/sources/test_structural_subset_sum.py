"""Independent exact checks of optimality, witnesses, coverage, and budgets."""

import itertools
import random
import unittest

from structural_subset_sum import (
    Core, Limits, _Budget, _exception_sums, find_core, solve,
    solve_bitset, solve_dfs, solve_mitm, verify_core,
)


def brute_sums(weights):
    sums = {}
    for mask in range(1 << len(weights)):
        value = sum(w for i, w in enumerate(weights) if mask >> i & 1)
        sums[value] = mask
    return sums


def brute_core_minima(weights):
    minima = {0: 0}
    for length in range(1, len(weights) + 1):
        for indices in itertools.combinations(range(len(weights)), length):
            values = sorted(weights[i] for i in indices)
            total = 0
            for value in values:
                if value <= total:
                    break
                total += value
            else:
                minima[length] = min(minima.get(length, total), total)
    return minima


class StructuralSubsetSumTests(unittest.TestCase):
    def check_answer(self, weights, target, result, truth):
        self.assertIn(result.status, ("yes", "no"))
        self.assertEqual(result.status == "yes", target in truth)
        if result.status == "yes" and result.reason != "decision_only":
            self.assertIsNotNone(result.witness)
            self.assertEqual(len(result.witness), len(set(result.witness)))
            self.assertTrue(all(0 <= i < len(weights) for i in result.witness))
            self.assertEqual(sum(weights[i] for i in result.witness), target)
        if result.core_indices is not None:
            core = Core(
                result.core_indices, result.exceptional_indices,
                sum(weights[i] for i in result.core_indices),
            )
            self.assertTrue(verify_core(weights, core))

    def test_greedy_optimality_and_all_prefix_minima_exhaustively(self):
        for n in range(8):
            for weights in itertools.combinations_with_replacement(range(1, 6), n):
                core = find_core(weights)
                self.assertTrue(verify_core(weights, core))
                minima = brute_core_minima(weights)
                self.assertEqual(len(core.indices), max(minima))
                total = 0
                self.assertEqual(minima[0], total)
                for length, index in enumerate(core.indices, 1):
                    total += weights[index]
                    self.assertEqual(total, minima[length], (weights, length))

    def test_exact_answers_for_all_targets_on_small_multisets(self):
        for n in range(6):
            for weights in itertools.combinations_with_replacement(range(1, 5), n):
                truth = brute_sums(weights)
                for target in range(-1, sum(weights) + 2):
                    for method in ("distinct", "enumerate"):
                        result = solve(weights, target, method=method)
                        self.check_answer(weights, target, result, truth)
                    for baseline in (solve_mitm, solve_dfs, solve_bitset):
                        self.check_answer(
                            weights, target, baseline(weights, target), truth
                        )

    def test_shuffled_random_lists_and_large_integer_witnesses(self):
        rng = random.Random(20261024)
        for n in (6, 9, 12):
            for seed in range(12):
                scale = 1 if seed % 2 else 10**40
                weights = [rng.randrange(1, 80) * scale + rng.randrange(7) for _ in range(n)]
                rng.shuffle(weights)
                truth = brute_sums(weights)
                targets = [
                    rng.choice(list(truth)),
                    rng.randrange(sum(weights) + 1),
                    sum(weights) // 2,
                ]
                for target in targets:
                    for method in ("distinct", "enumerate"):
                        self.check_answer(
                            weights, target,
                            solve(weights, target, method=method), truth,
                        )
                    for baseline in (solve_mitm, solve_dfs):
                        self.check_answer(
                            weights, target, baseline(weights, target), truth
                        )

    def test_distinct_sum_coverage_and_indexed_representatives(self):
        for weights in ([3, 3, 3, 3], [1, 2, 3, 5], [], [10**50, 10**50, 7]):
            budget = _Budget(Limits())
            actual = _exception_sums(weights, tuple(range(len(weights))), budget)
            self.assertEqual([s for s, _ in actual], sorted(brute_sums(weights)))
            for value, mask in actual:
                self.assertEqual(
                    value, sum(w for i, w in enumerate(weights) if mask >> i & 1)
                )
            self.assertEqual(budget.stats["distinct_exception_sums"], len(actual))
            self.assertTrue(budget.stats["distinct_sums_complete"])

    def test_many_repeated_exceptions_and_nonrecursive_large_core(self):
        weights = [3] * 81
        result = solve(weights, 123)
        self.assertEqual(result.stats["k"], 80)
        self.assertEqual(result.stats["distinct_exception_sums"], 81)
        self.check_answer(weights, 123, result, {123})
        weights = [1 << i for i in range(1200)]
        target = weights[-1] + weights[600] + weights[0]
        for method in ("distinct", "enumerate"):
            result = solve(weights, target, method=method)
            self.assertEqual(result.stats["k"], 0)
            self.check_answer(weights, target, result, {target})

    def test_maximum_core_need_not_minimize_residual_support(self):
        weights = [1, 1, 1, 2, 3]
        greedy = find_core(weights)
        self.assertEqual([weights[i] for i in greedy.indices], [1, 2])
        self.assertEqual(max(brute_core_minima(weights)), 2)
        alternative = Core((0, 4), (1, 2, 3), 4)
        self.assertTrue(verify_core(weights, alternative))
        greedy_M = len(brute_sums([weights[i] for i in greedy.exceptions]))
        alternative_M = len(brute_sums([weights[i] for i in alternative.exceptions]))
        self.assertEqual((greedy_M, alternative_M), (6, 5))

    def test_limits_never_become_false_no_and_completed_M_is_honest(self):
        weights = [2, 5, 6, 11, 23]
        for solver in (
            lambda w, t, **kw: solve(w, t, method="distinct", **kw),
            lambda w, t, **kw: solve(w, t, method="enumerate", **kw),
            solve_mitm, solve_dfs, solve_bitset,
        ):
            result = solver(weights, 17, limits=Limits(max_work=1))
            self.assertEqual(result.status, "unresolved")
            self.assertIsNone(result.witness)
        result = solve(weights, 17, limits=Limits(max_states=1))
        self.assertEqual(result.status, "unresolved")
        self.assertEqual(result.reason, "state_limit")
        self.assertIsNone(result.stats["distinct_exception_sums"])
        self.assertFalse(result.stats["distinct_sums_complete"])
        result = solve(weights, 17, limits=Limits(max_seconds=1e-12))
        self.assertEqual(result.status, "unresolved")
        result = solve_bitset([2, 5, 11], 7, limits=Limits(max_bitset_bits=4))
        self.assertEqual((result.status, result.reason), ("unresolved", "bitset_limit"))

    def test_verified_partition_and_invalid_inputs(self):
        self.assertFalse(verify_core([1, 2], Core((0, 0), (), 2)))
        self.assertFalse(verify_core([1, 2], Core((0,), (3,), 1)))
        self.assertFalse(verify_core([1, 2], Core((0, 1), (), 4)))
        for weights in ([0], [-2], [True], [1.5]):
            with self.assertRaises(ValueError):
                solve(weights, 1)
        with self.assertRaises(ValueError):
            solve([1], 1.0)
        with self.assertRaises(ValueError):
            solve([1], 1, method="approximate")
        for kwargs in ({"max_states": 0}, {"max_work": -1}, {"max_seconds": float("nan")}):
            with self.assertRaises(ValueError):
                Limits(**kwargs)


if __name__ == "__main__":
    unittest.main()
