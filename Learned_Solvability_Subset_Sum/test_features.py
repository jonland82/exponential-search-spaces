"""Independent finite checks of distances, exact sets and recovered witnesses."""

from itertools import combinations, product
import random
import unittest

from features import FeatureConfig, extract, query


def sums(weights, indices):
    reachable = {0}
    for i in indices:
        reachable |= {s + weights[i] for s in reachable}
    return reachable


def easy(weights, indices, dimension, config):
    values = sorted(weights[i] for i in indices)
    if dimension == 2:
        return len(set(values)) <= config.distinct_values
    total = 0
    for value in values:
        if dimension == 0 and value <= total:
            return False
        if dimension == 1 and value > total + 1:
            return False
        total += value
    return True


class FeatureTests(unittest.TestCase):
    def test_exact_distances_by_exhaustive_deletion(self):
        config = FeatureConfig(distinct_values=2, support_cap=7, interval_cap=2)
        for n in range(6):
            for weights in combinations(range(1, 9), n):
                features = extract(weights, config)
                for dim in range(3):
                    optimum = min(n - len(indices)
                                  for width in range(n + 1)
                                  for indices in combinations(range(n), width)
                                  if easy(features.weights, indices, dim, config))
                    self.assertEqual(features.values[dim], optimum, (weights, dim))
        for weights in product(range(1, 4), repeat=5):
            features = extract(weights, config)
            self.assertEqual(features.values[2],
                             min(weights.count(v) for v in set(weights)) if len(set(weights)) == 3 else 0)

    def test_certificates_and_all_small_targets(self):
        rng = random.Random(191)
        config = FeatureConfig(distinct_values=2, support_cap=12, interval_cap=3)
        inputs = [(), (2, 4, 6), (1, 2, 4, 8), (5, 5, 10, 10), (1, 1, 10, 10)]
        inputs += [tuple(rng.randrange(1, 18) for _ in range(rng.randrange(1, 10)))
                   for _ in range(90)]
        for weights in inputs:
            features = extract(weights, config)
            self.assertEqual(len(features.values), 5)
            for dimension, cert in enumerate(features.certificates):
                self.assertEqual(sorted(cert.indices + cert.exceptions), list(range(len(weights))))
                reachable = sums(weights, cert.indices)
                if dimension == 3:
                    self.assertLessEqual(len(cert.support), config.support_cap)
                    self.assertEqual({s * features.divisor for s, _ in cert.support}, reachable)
                if dimension == 4:
                    self.assertEqual(len(cert.prefixes), len(cert.indices) + 1)
                    for width, intervals in enumerate(cert.prefixes):
                        self.assertLessEqual(len(intervals), config.interval_cap)
                        represented = {s * features.divisor for lo, hi in intervals
                                       for s in range(lo, hi + 1)}
                        self.assertEqual(represented, sums(weights, cert.indices[:width]))
                for target in range(-1, sum(weights) + 2):
                    witness = query(features, dimension, target)
                    self.assertEqual(witness is not None, target in reachable,
                                     (weights, dimension, target))
                    if witness is not None:
                        self.assertEqual(len(witness), len(set(witness)))
                        self.assertTrue(set(witness) <= set(cert.indices))
                        self.assertEqual(sum(weights[i] for i in witness), target)

    def test_permutation_and_common_scaling(self):
        weights = [1, 1, 3, 5, 7, 18, 19, 45]
        reference = extract(weights).values
        self.assertEqual(extract(list(reversed(weights))).values, reference)
        self.assertEqual(extract([17 * w for w in weights]).values, reference)

    def test_invalid_inputs_and_caps(self):
        for weights in ([0], [-1], [True], [1.5]):
            with self.assertRaises(ValueError):
                extract(weights)
        for cap in (0, -1, True):
            with self.assertRaises(ValueError):
                FeatureConfig(support_cap=cap)


if __name__ == "__main__":
    unittest.main()
