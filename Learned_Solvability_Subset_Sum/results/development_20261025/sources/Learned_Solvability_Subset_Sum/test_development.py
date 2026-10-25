import random
import unittest

from advanced_features import extract_advanced, reduce_instance
from features import FeatureConfig, extract
from run_development import (CONFIG, VARIANTS, full_core_query, solve_policy, split_for)
from run_pilot import check, independent_halves, independent_query


class DevelopmentTests(unittest.TestCase):
    def test_shared_and_reuse_policies_against_independent_labels(self):
        rng = random.Random(604)
        weights_list = [[10**6 + 7 * i for i in range(7)], [1, 1, 1, 50, 50]]
        weights_list += [[rng.randrange(1, 30) for _ in range(7)] for _ in range(12)]
        for weights in weights_list:
            halves = independent_halves(weights)
            base = extract(weights)
            advanced = extract_advanced(weights, base=base)
            for target in (0, 1, sum(weights) // 3, sum(weights) // 2, sum(weights)):
                kernel = reduce_instance(weights, target)
                tb = extract(kernel.weights)
                ta = extract_advanced(kernel.weights, base=tb)
                features = dict(zip(VARIANTS, (base, advanced, tb, ta)))
                truth = independent_query(halves, target) is not None
                for cap in (1, 1000, 100_000):
                    for policy in ("common",) + VARIANTS:
                        result = solve_policy(weights, target, kernel, cap,
                            features=features.get(policy),
                            advanced=policy in ("progression", "target_progression"),
                            target_aware=policy.startswith("target_"))
                        check(weights, target, truth, result)
                        if not result["extraction_exhausted"]:
                            self.assertLessEqual(result["work"], cap)
                            self.assertEqual(result["work"], result["feature_work"] +
                                result["preprocess_work"] + sum(a["work"] for a in result["attempts"]))
                        if cap == 100_000:
                            self.assertNotEqual(result["status"], "unresolved")

    def test_progression_reuse_finishes_exactly_within_charge(self):
        weights = [10**9 + 17 * i for i in range(24)]
        advanced = extract_advanced(weights)
        target = sum(weights[::2])
        result = full_core_query(advanced, True, target, 8 * 25)
        self.assertEqual(result["status"], "yes")
        self.assertEqual(sum(weights[i] for i in result["witness"]), target)
        self.assertLessEqual(result["work"], 8 * 25)

    def test_group_split_precedence(self):
        for family in CONFIG["families"]:
            for n in CONFIG["sizes"]:
                for replicate in range(4):
                    split = split_for(n, family, replicate)
                    if family in CONFIG["heldout_families"]:
                        self.assertEqual(split, "unseen_family")
                    elif n == 36:
                        self.assertEqual(split, "larger_size")
                    else:
                        self.assertEqual(split, ("train", "train", "calibration", "test")[replicate])


if __name__ == "__main__":
    unittest.main()
