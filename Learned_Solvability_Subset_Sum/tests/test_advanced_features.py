from itertools import combinations
import random
import unittest

from advanced_features import (Progression, extract_advanced, lift_witness,
                               progression_query, query_advanced, reduce_instance)
from features import FeatureConfig, extract


def reachable(weights):
    values = {0}
    for weight in weights:
        values |= {s + weight for s in values}
    return values


class AdvancedTests(unittest.TestCase):
    def test_progression_all_small_targets_and_witnesses(self):
        for size in range(1, 9):
            for start in (1, 3, 11):
                for step in (1, 2, 7):
                    weights = tuple(start + i * step for i in range(size))
                    cert = Progression(tuple(range(size)), start, step)
                    truth = reachable(weights)
                    for target in range(-1, sum(weights) + 2):
                        witness = progression_query(weights, cert, target)
                        self.assertEqual(witness is not None, target in truth)
                        if witness is not None:
                            self.assertEqual(len(witness), len(set(witness)))
                            self.assertEqual(sum(weights[i] for i in witness), target)

    def test_advanced_dominates_original_and_retains_sound_core(self):
        rng = random.Random(602)
        for _ in range(60):
            weights = [rng.randrange(1, 31) for _ in range(rng.randrange(1, 10))]
            advanced = extract_advanced(weights, FeatureConfig(interval_cap=2))
            self.assertEqual(advanced.values[:4], advanced.base.values[:4])
            self.assertLessEqual(advanced.values[4], advanced.base.values[4])
            indices = (advanced.progression.indices if advanced.progression is not None
                       else advanced.base.certificates[4].indices)
            truth = reachable([weights[i] for i in indices])
            for target in range(sum(weights) + 2):
                witness = query_advanced(advanced, 4, target)
                self.assertEqual(witness is not None, target in truth)
                if witness is not None:
                    self.assertEqual(sum(weights[i] for i in witness), target)

    def test_recognizes_sparse_progression_and_missing_item(self):
        weights = [10**9 + 17 * i for i in range(20)]
        advanced = extract_advanced(weights)
        self.assertEqual(advanced.values[4], 0)
        self.assertGreater(advanced.base.values[4], 0)
        for indices in combinations(range(20), 2):
            target = sum(weights[i] for i in indices)
            witness = query_advanced(advanced, 4, target)
            self.assertIsNotNone(witness)
            self.assertEqual(sum(weights[i] for i in witness), target)
        reused = extract_advanced(weights, base=extract(weights))
        self.assertEqual(reused.values, advanced.values)
        self.assertEqual(reused.work, advanced.work)
        with self.assertRaises(ValueError):
            extract_advanced([1], base=extract([2]))

    def test_kernel_equivalence_and_lifted_witnesses(self):
        rng = random.Random(603)
        samples = [[], [1], [2, 4, 7], [4, 7, 10], [3, 3, 20], [10, 14, 18, 43]]
        samples += [[rng.randrange(1, 30) for _ in range(rng.randrange(1, 9))] for _ in range(70)]
        for weights in samples:
            truth = reachable(weights)
            for target in range(-1, sum(weights) + 2):
                kernel = reduce_instance(weights, target)
                if kernel.status != "unresolved":
                    self.assertEqual(kernel.status == "yes", target in truth)
                    if kernel.witness is not None:
                        self.assertEqual(sum(weights[i] for i in kernel.witness), target)
                else:
                    self.assertEqual(kernel.target in reachable(kernel.weights), target in truth)
                    for mask in range(1 << len(kernel.weights)):
                        indices = tuple(i for i in range(len(kernel.weights)) if mask >> i & 1)
                        if sum(kernel.weights[i] for i in indices) == kernel.target:
                            witness = lift_witness(kernel, indices)
                            self.assertEqual(sum(weights[i] for i in witness), target)
                            self.assertEqual(len(witness), len(set(witness)))

    def test_target_dependent_features(self):
        weights = [2, 3, 7, 8, 100]
        a, b = reduce_instance(weights, 9), reduce_instance(weights, 17)
        self.assertNotEqual((a.weights, a.target), (b.weights, b.target))
        for target in (9, 17, 103):
            kernel = reduce_instance(weights, target)
            if kernel.status == "unresolved":
                self.assertLessEqual(sum(kernel.weights), sum(weights))


if __name__ == "__main__":
    unittest.main()
