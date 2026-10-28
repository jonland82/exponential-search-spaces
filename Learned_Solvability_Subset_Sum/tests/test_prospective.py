from copy import deepcopy
from dataclasses import asdict
import random
import unittest

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from advanced_features import reduce_instance
from prospective_study import (CONFIG, NEW_FAMILIES, cohort_for, feature_vectors,
                               infer, limited_portfolio, new_weights, reference)
from priority_experiment import PHASES, live_pool, rank_cases, replay_pool
from run_pilot import check, independent_halves, independent_query, portfolio


def fixture(weights, target, number):
    kernel = reduce_instance(weights, target)
    vectors, work, times, reuse = feature_vectors(weights, target, kernel)
    case = {"case_id": f"case{number}", "list_id": f"list{number}",
            "base_list_id": f"base{number}", "cohort": "in_distribution",
            "weights": weights, "target": target, "kernel": asdict(kernel),
            "budget": 8 * (30 * len(weights) + 50), "vectors": vectors,
            "feature_work": work, "feature_seconds": times, "reuse": reuse,
            "truth": "yes" if independent_query(independent_halves(weights), target) is not None else "no",
            "predictions": {f"{arm}:logistic": 0.8 for arm in ("five", "conventional", "hybrid")},
            "inference_work": {f"{arm}:logistic": 100 for arm in ("five", "conventional", "hybrid")}}
    result = reference(weights, target, kernel, case["budget"])
    check(weights, target, case["truth"] == "yes", result)
    return case, result


class ProspectiveTests(unittest.TestCase):
    def test_fresh_generators_and_cohort_isolation(self):
        rng = random.Random(701)
        for family in CONFIG["families"]:
            for n in CONFIG["sizes"]:
                for replacements in (0, n // 4):
                    weights = new_weights(family, n, replacements, rng)
                    self.assertEqual(len(weights), n)
                    self.assertTrue(all(type(w) is int and w > 0 for w in weights))
        self.assertEqual(cohort_for(38, "random_wide", 1), "larger_size")
        self.assertEqual(cohort_for(24, "near_equal", 1), "prior_holdout")
        for family in NEW_FAMILIES:
            self.assertEqual(cohort_for(38, family, 1), "unseen_family")
            self.assertEqual(cohort_for(24, family, 17), "unseen_family_scaled")

    def test_work_reference_matches_development_schedule(self):
        rng = random.Random(702)
        for _ in range(25):
            weights = [rng.randrange(1, 100) for _ in range(10)]
            target = rng.randrange(sum(weights) + 1)
            for cap in (1, 30, 300, 3000):
                a = limited_portfolio(weights, target, cap)
                b = portfolio(weights, target, cap)
                self.assertEqual((a["status"], a["witness"], a["work"]),
                                 (b["status"], b["witness"], b["work"]))
                check(weights, target, independent_query(independent_halves(weights), target) is not None, a)

    def test_counter_pool_pays_all_costs_and_clips_budget(self):
        rng = random.Random(703)
        pairs = [fixture([rng.randrange(1, 300) for _ in range(9)], 500 + i * 11, i) for i in range(8)]
        cases, refs = [p[0] for p in pairs], {p[0]["case_id"]: p[1] for p in pairs}
        for fraction in (.001, .03, .2, .5, 1):
            for policy in CONFIG["pool_policies"]:
                result = replay_pool(cases, refs, policy, fraction, 0)
                self.assertLessEqual(result["spent"], result["budget"])
                self.assertEqual(result["spent"], sum(result["costs"].values()))
                self.assertEqual(len(set(result["solved_ids"])), result["solved"])
                self.assertTrue(set(result["solved_ids"]) <= {c["case_id"] for c in cases})
        # Extraction cannot be used for free when planning alone exceeds budget.
        expensive = deepcopy(cases)
        for case in expensive:
            case["feature_work"]["five"] = 10**12
        result = replay_pool(expensive, refs, "five", .5, 0)
        self.assertEqual(result["exhausted_phase"], "features")
        self.assertFalse(result["attempts"])

    def test_rank_does_not_use_truth_or_observed_runtime(self):
        cases = [{"case_id": "a", "budget": 20, "truth": "no", "runtime": 1},
                 {"case_id": "b", "budget": 10, "truth": "yes", "runtime": 10}]
        scores = {"a": .9, "b": .6}
        first = [r["case_id"] for r in rank_cases(cases, "hybrid", scores)]
        for case in cases:
            case["truth"] = "yes" if case["truth"] == "no" else "no"
            case["runtime"] *= 100
        self.assertEqual(first, [r["case_id"] for r in rank_cases(cases, "hybrid", scores)])
        self.assertEqual(first, ["b", "a"])

    def test_frozen_inference_and_cost_are_valid(self):
        x = np.array([[0, 1], [1, 0], [2, 3], [3, 2], [4, 5], [5, 4]], dtype=float)
        y = np.array([0, 0, 0, 1, 1, 1])
        model = make_pipeline(StandardScaler(), LogisticRegression()).fit(x, y)
        raw = np.clip(model.predict_proba(x)[:, 1], 1e-6, 1 - 1e-6)
        logits = np.log(raw / (1 - raw)).reshape(-1, 1)
        calibrator = LogisticRegression().fit(logits, y)
        bundle = {"model": model, "calibrator": calibrator}
        probabilities, work, elapsed = infer(bundle, x.tolist())
        np.testing.assert_allclose(probabilities, calibrator.predict_proba(logits)[:, 1])
        self.assertEqual(work, [32] * len(x))
        self.assertGreaterEqual(elapsed, 0)

    def test_live_deadline_discards_late_work(self):
        case, _ = fixture([1, 2, 4], 3, 1)
        result = live_pool([case], {}, "arrival", 0, 0)
        self.assertEqual(result["solved"], 0)
        self.assertGreaterEqual(result["overshoot_seconds"], 0)


if __name__ == "__main__":
    unittest.main()
