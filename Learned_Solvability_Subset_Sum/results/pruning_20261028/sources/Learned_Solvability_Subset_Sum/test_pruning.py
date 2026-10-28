"""Pruning invariants, real feature dependencies and online/offline parity."""
import unittest

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from geometric_models import PrototypeGeometry, design
from neighbor_experiment import inference_work
from pruning_models import LOGISTIC, PrunedModel, PruningGeometry, select_features


class PruningTests(unittest.TestCase):
    def setUp(self):
        self.x = np.array([[v+.01*j*v*v for j in range(15)] for v in (0, 1, 3, 4, 8, 9, 15, 16)])
        self.y = np.array([0, 1]*4)
        self.geometry = PrototypeGeometry(self.x, self.y, np.repeat(["a", "b", "c", "d"], 2), prototypes=1)

    def test_rfe_nested_survivors_and_complete_ranking(self):
        rng = np.random.default_rng(4321)
        x = rng.normal(size=(120, 27))
        y = (x[:, 0]+.05*rng.normal(size=len(x)) > 0).astype(int)
        first = select_features(x, y)
        self.assertEqual(sorted(first["ranking"]), list(range(27)))
        self.assertEqual(len(first["trace"]), 23)
        self.assertEqual(len(first["selected"]["top5"]), 5)
        self.assertEqual(len(first["selected"]["top10"]), 10)
        self.assertLessEqual(set(first["selected"]["top5"]), set(first["selected"]["top10"]))
        self.assertIn(0, first["selected"]["top5"])
        self.assertEqual(set(first["ranking"][:10]), set(first["selected"]["top10"]))
        self.assertEqual(first, select_features(x, y))

    def test_each_elimination_matches_the_weakest_standardized_coefficient(self):
        x = np.random.default_rng(9).normal(size=(60, 27))
        selection = select_features(x, np.tile([0, 1], 30))
        for row in selection["trace"][:-1]:
            weakest = min(range(len(row["active"])), key=lambda j:(abs(row["coefficients"][j]), row["active"][j]))
            self.assertEqual(row["removed"], row["active"][weakest])

    def test_selected_transform_matches_full_design_slicing(self):
        selected = dict(top5=[0, 9, 15, 17, 26], top10=[0, 2, 5, 9, 12, 15, 16, 17, 20, 26])
        bank = PruningGeometry(self.geometry, selected)
        full = design(self.x, self.geometry, "combined")
        for arm, columns in selected.items():
            np.testing.assert_allclose(bank.transform(self.x, arm), full[:, columns], atol=1e-12)
        self.assertEqual(bank.dependencies("top5"), list(range(15)))

    def test_no_derived_features_need_no_geometry_work(self):
        columns = [1, 3, 5, 7, 9]
        bank = PruningGeometry(self.geometry, dict(top5=columns))
        np.testing.assert_array_equal(bank.transform(self.x, "top5"), self.x[:, columns])
        self.assertEqual(bank.dependencies("top5"), columns)
        self.assertEqual(bank.work("top5"), 0)

    def test_selected_products_only_keep_their_base_dependencies(self):
        columns = [5, 6, 7, 17, 18]
        bank = PruningGeometry(self.geometry, dict(top5=columns))
        self.assertEqual(bank.dependencies("top5"), [0, 1, 2, 5, 6, 7])
        self.assertEqual(bank.work("top5"), 47)

    def test_selected_adapter_probabilities_and_paid_dimensions(self):
        bank = PruningGeometry(self.geometry, dict(top5=[0, 1, 7, 15, 18]))
        tx = bank.transform(self.x, "top5")
        fitted = make_pipeline(StandardScaler(), LogisticRegression(**LOGISTIC)).fit(tx, self.y)
        model = PrunedModel(bank, "top5", fitted)
        np.testing.assert_allclose(model.predict_proba(self.x), fitted.predict_proba(tx))
        saved = dict(bank=bank, bundles={"top5":dict(dimensions=5)})
        self.assertEqual(inference_work(saved, "top5"), 6*5+20+45+47+1)

    def test_invalid_subsets_are_rejected(self):
        for columns in ([0]*5, [0, 1, 2, 3, 27], [0, 1, 2]):
            with self.assertRaises(ValueError):
                PruningGeometry(self.geometry, dict(top5=columns))
        with self.assertRaises(ValueError):
            select_features(np.ones((10, 26)), np.tile([0, 1], 5))


if __name__ == "__main__":
    unittest.main()
