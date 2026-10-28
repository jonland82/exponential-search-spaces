import random
import unittest

import numpy as np

from Structural_Geometry_Subset_Sum.cost_gate import (
    POLICIES, INFERENCE_WORK, capped_cost, gate_score, solve_gate)
from Structural_Geometry_Subset_Sum.cost_gate_study import (
    CONFIG, fit_model, pool, check_answer)


class CostGateTests(unittest.TestCase):
    def test_all_policies_exact_under_small_independent_enumeration(self):
        rng = random.Random(234)
        for _ in range(12):
            weights = [rng.randrange(1, 60) for _ in range(8)]
            reachable = {sum(w for i, w in enumerate(weights) if mask >> i & 1) for mask in range(256)}
            for target in (sum(weights)//2, sum(weights)//3, sum(weights)+1):
                case = dict(weights=weights, target=target, truth="yes" if target in reachable else "no", budget=100000)
                for policy in POLICIES:
                    result = solve_gate(weights, target, policy, max_work=case["budget"],
                        model=dict(constant=1., threshold=.5))
                    check_answer(case, result)
                    self.assertEqual(result["status"], case["truth"])

    def test_matched_decision_features_and_paid_inference(self):
        rng = random.Random(648)
        weights = [1000000*rng.randrange(1, 7)+rng.randrange(-8, 9) for _ in range(24)]
        target = sum(weights[::2])
        results = {p:solve_gate(weights, target, p, max_work=100000,
            model=dict(constant=1., threshold=.5)) for p in ("never", "always", "simple", "learned")}
        self.assertTrue(all(r["decision_eligible"] for r in results.values()))
        for result in results.values():
            self.assertEqual(result["gate_features"], results["never"]["gate_features"])
            for phase in ("preprocessing", "features", "cores", "geometry", "doubling"):
                self.assertEqual(result["phase_work"][phase], results["never"]["phase_work"][phase])
        self.assertFalse(results["never"]["check_taken"])
        self.assertTrue(results["learned"]["check_taken"])
        self.assertEqual(results["learned"]["phase_work"]["decision"], INFERENCE_WORK)
        self.assertEqual(results["always"]["phase_work"]["decision"], 1)
        self.assertEqual(results["learned"]["status"], "yes")

    def test_work_and_time_exhaustion_never_supply_a_false_no(self):
        weights = [1000000*i+3*i*i for i in range(1, 25)]
        for policy in POLICIES:
            for cap, seconds in ((1, None), (50, None), (100000, 1e-12)):
                result = solve_gate(weights, sum(weights[::2]), policy, max_work=cap,
                    seconds=seconds, model=dict(constant=1., threshold=.5))
                self.assertEqual(result["status"], "unresolved")
                self.assertLessEqual(result["work"], cap)
                self.assertEqual(sum(result["phase_work"].values()), result["work"])

    def test_weighted_fit_scalar_parity_and_degenerate_training(self):
        pairs = [dict(split="train", eligible=True, saving=(-1 if i < 6 else 1)*(i+10),
            label=int(i >= 6), absolute_saving=i+10,
            features=[float(i), float(i*i)]+[float(j) for j in range(17)]) for i in range(12)]
        model, fitted, diagnostics = fit_model(pairs)
        x = [r["features"] for r in pairs]
        np.testing.assert_allclose([gate_score(model, v) for v in x], fitted.predict_proba(x)[:, 1], atol=1e-12, rtol=0)
        self.assertEqual(diagnostics["positive"], 6)
        self.assertEqual(diagnostics["negative"], 6)
        for subset in ([], pairs[:3], pairs[-3:]):
            constant, fitted, _ = fit_model(subset)
            self.assertIsNone(fitted)
            self.assertIn(constant["constant"], (0., 1.))
        self.assertEqual(capped_cost(dict(status="unresolved", work=5), 100), 100)
        self.assertEqual(capped_cost(dict(status="yes", work=5), 100), 5)

    def test_pool_clipped_work_is_recomputed_and_late_answers_excluded(self):
        cases = [dict(case_id=f"c{i}", cohort="test", weights=[3, 8, 13, 21],
            target=11, truth="yes", budget=10000) for i in range(3)]
        for policy in POLICIES:
            model = dict(constant=0., threshold=.5)
            first = pool(cases, policy, "work", .001, 0, model)
            second = pool(cases, policy, "work", .001, 0, model)
            self.assertLessEqual(first["spent"], first["budget"])
            self.assertEqual(first["solved_ids"], second["solved_ids"])
            self.assertEqual(first["spent"], second["spent"])
            timed = pool(cases, policy, "time", 1e-10, 0, model)
            self.assertEqual(timed["solved"], 0)


if __name__ == "__main__":
    unittest.main()
