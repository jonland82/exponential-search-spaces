"""Independent correctness and resource tests for costed core selection."""

import itertools
import random
import unittest

from core_selection import _RetainedSupportBudget, candidate_pool, solve_selected
from structural_subset_sum import Core, Limits, _Budget, _Limit, find_core, verify_core
from test_structural_subset_sum import brute_sums


def selection_budget():
    budget = _Budget(Limits())
    budget.stats.update(
        swap_pairs_considered=0, candidate_verifications=0,
        valid_alternatives=0, candidate_pool_size=0,
    )
    return budget


class CoreSelectionTests(unittest.TestCase):
    def test_exact_answers_and_indexed_witnesses_exhaustively(self):
        for n in range(6):
            for weights in itertools.combinations_with_replacement(range(1, 5), n):
                truth = brute_sums(weights)
                for target in range(-1, sum(weights) + 2):
                    for policy in ("multiplicity", "support"):
                        answer = solve_selected(weights, target, policy=policy)
                        self.assertEqual(answer.status == "yes", target in truth)
                        self.assertIn(answer.status, ("yes", "no"))
                        if answer.status == "yes":
                            self.assertEqual(len(answer.witness), len(set(answer.witness)))
                            self.assertEqual(sum(weights[i] for i in answer.witness), target)

    def test_pool_contains_only_verified_maximum_cores_and_rank_is_local_optimum(self):
        rng = random.Random(871099)
        for _ in range(150):
            weights = [rng.randrange(1, 25) for _ in range(8)]
            base = find_core(weights)
            budget = selection_budget()
            pool = candidate_pool(weights, base, budget)
            self.assertLessEqual(len(pool), 4)
            self.assertIn(base, [entry[1] for entry in pool])
            for _, candidate in pool:
                self.assertEqual(len(candidate.indices), len(base.indices))
                self.assertTrue(verify_core(weights, candidate))
            # Independently scan every single-index replacement.
            caps = []
            for remove in base.indices:
                for add in base.exceptions:
                    indices = tuple(sorted(
                        [i for i in base.indices if i != remove] + [add],
                        key=lambda i: (weights[i], i),
                    ))
                    extras = tuple(i for i in range(len(weights)) if i not in indices)
                    candidate = Core(indices, extras, sum(weights[i] for i in indices))
                    if verify_core(weights, candidate):
                        counts = {}
                        for i in extras:
                            counts[weights[i]] = counts.get(weights[i], 0) + 1
                        cap = 1
                        for count in counts.values():
                            cap *= count + 1
                        caps.append(cap)
            if caps:
                self.assertLessEqual(pool[0][0][0], min(caps))

    def test_known_support_improvement_and_probe_reuse(self):
        weights = [1, 1, 1, 2, 3]
        for policy in ("multiplicity", "support"):
            answer = solve_selected(weights, 4, policy=policy)
            self.assertEqual([weights[i] for i in answer.core_indices], [2, 3])
            self.assertEqual(answer.stats["distinct_exception_sums"], 4)
            self.assertTrue(answer.stats["selected_core_changed"])
            self.assertEqual(answer.stats["k"], 3)
        answer = solve_selected(weights, 4, policy="support")
        self.assertEqual(answer.stats["generation_seconds"], 0.0)
        self.assertGreater(answer.stats["support_probes"], 1)
        self.assertLessEqual(
            answer.stats["distinct_exception_sums"],
            max(answer.stats["support_probe_sizes"]),
        )

    def test_limits_do_not_publish_an_unfinished_selection_as_no(self):
        for policy in ("multiplicity", "support"):
            answer = solve_selected(
                [1, 1, 1, 2, 3], 4, policy=policy,
                limits=Limits(max_work=1),
            )
            self.assertEqual(answer.status, "unresolved")
            self.assertFalse(answer.stats["distinct_sums_complete"])
            self.assertIsNone(answer.stats["distinct_exception_sums"])
        answer = solve_selected(
            [1, 1, 1, 2, 3], 4, policy="support", limits=Limits(max_states=2)
        )
        self.assertEqual(answer.status, "unresolved")
        self.assertFalse(answer.stats["selection_complete"])
        self.assertIsNone(answer.stats["distinct_exception_sums"])
        budget = _Budget(Limits(max_states=5))
        offset = _RetainedSupportBudget(budget, 3)
        with self.assertRaises(_Limit):
            offset.states(3)

    def test_random_large_integer_inputs_and_policies(self):
        rng = random.Random(817231)
        for _ in range(30):
            weights = [rng.randrange(1, 10**30) for _ in range(10)]
            truth = brute_sums(weights)
            for target in (rng.choice(list(truth)), sum(weights) // 2):
                for policy in ("multiplicity", "support"):
                    answer = solve_selected(weights, target, policy=policy)
                    self.assertEqual(answer.status == "yes", target in truth)
        with self.assertRaises(ValueError):
            solve_selected([1, 2], 1, policy="oracle")


if __name__ == "__main__":
    unittest.main()
