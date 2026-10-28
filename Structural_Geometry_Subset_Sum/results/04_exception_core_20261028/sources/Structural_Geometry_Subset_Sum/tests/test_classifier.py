from itertools import product
import random
import unittest

import numpy as np

from Structural_Geometry_Subset_Sum.classifier_features import (ARMS, POLICIES,
    SCHEMAS, design, doubling_feature, geometry_features, pending_after_shared_checks)
from Structural_Geometry_Subset_Sum.classifier_pool import run_pool
from Structural_Geometry_Subset_Sum.classifier_study import (CONFIG, make_case, paired_interval)
from Structural_Geometry_Subset_Sum.structures.large_base import describe


class LiteratureClassifierTests(unittest.TestCase):
    def test_integer_aggregate_range_contains_every_exact_solution(self):
        rng = random.Random(821)
        for _ in range(40):
            weights = [rng.randrange(1, 80) for _ in range(7)]
            base = rng.randrange(2, 30)
            for selected in product((0, 1), repeat=len(weights)):
                target = sum(w*x for w, x in zip(weights, selected))
                g = describe(weights, target, base)
                q = sum(p*x for p, x in zip(g.p, selected))
                self.assertLessEqual(g.q_low, q)
                self.assertGreaterEqual(g.q_high, q)
                self.assertEqual(g.base*q+sum(r*x for r, x in zip(g.r, selected)), target)

    def test_features_are_invariant_to_order_and_common_integer_scaling(self):
        weights = [1000003, 2000001, 3000004, 4000002, 1000004]
        target = weights[0]+weights[2]
        original = geometry_features(weights, target)
        for other, t in ((list(reversed(weights)), target), ([w*17 for w in weights], target*17)):
            saved = geometry_features(other, t)
            np.testing.assert_array_equal(saved["values"], original["values"])
            self.assertEqual(saved["exact_no"], original["exact_no"])
            self.assertEqual(doubling_feature(other)["value"], doubling_feature(weights)["value"])

    def test_doubling_distinct_set_and_diagonal(self):
        row = doubling_feature([3, 3, 6, 9, 9])
        self.assertEqual(row["distinct"], 3)
        self.assertEqual(row["sumset_size"], 5)
        self.assertEqual(row["value"], 5/3)
        self.assertEqual(doubling_feature([])["value"], 0)
        self.assertEqual(doubling_feature([4, 4])["value"], 1)

    def test_exact_gap_removed_from_ml_subgroup_and_paid_equally(self):
        rng = random.Random(481)
        weights = [1000000*rng.randrange(1, 7)+rng.randrange(1, 17) for _ in range(24)]
        row = dict(list_id="test", split="test", n=len(weights), family="large_base", cohort="test", weights=weights)
        case = make_case(row, 1000000*(sum(w//1000000 for w in weights)//2)+500000, "gap", None)
        self.assertTrue(case["geometry"]["exact_no"])
        self.assertFalse(pending_after_shared_checks(case))
        predictions = {case["case_id"]:{arm:.5 for arm in ARMS}}
        for policy in POLICIES[1:]:
            saved = run_pool([case], {}, predictions, policy, "work", 100, 0, CONFIG["seed"])
            self.assertEqual(saved["solved"], 1)
            self.assertEqual(saved["events"][0]["source"], "aggregate_gap")
            self.assertGreater(saved["costs"]["geometry"], 0)
            self.assertEqual(saved["costs"]["inference"], 0)

    def test_schema_and_counter_replay_under_tight_pool_cap(self):
        weights = [1000003, 2000001, 3000004, 4000002, 1000004, 2000006]
        row = dict(list_id="test", split="test", n=len(weights), family="large_base", cohort="test", weights=weights)
        mask = 1 | (1 << 2)
        case = make_case(row, weights[0]+weights[2], "planted", mask)
        for arm in ARMS:
            self.assertEqual(len(design(case, arm)), len(SCHEMAS[arm]))
        predictions = {case["case_id"]:{arm:.5 for arm in ARMS}}
        for policy in POLICIES:
            first = run_pool([case], {}, predictions, policy, "work", .01, 0, CONFIG["seed"])
            second = run_pool([case], {}, predictions, policy, "work", .01, 0, CONFIG["seed"])
            self.assertEqual(first, second)
            self.assertLessEqual(first["spent"], first["budget"])
            self.assertEqual(first["spent"], sum(first["costs"].values()))

    def test_bootstrap_preserves_correlated_targets(self):
        cases = [dict(list_id="one") for _ in range(3)]
        result = paired_interval(cases, np.zeros(3), np.ones(3), np.zeros(3))
        self.assertEqual(result["lists"], 1)
        self.assertEqual(result["list_bootstrap_95"], [1., 1.])
        self.assertEqual(result["bonferroni_two_comparison_97_5"], [1., 1.])


if __name__ == "__main__":
    unittest.main()
