"""Checks for supervised feature leakage, geometry and paid inference parity."""
import unittest

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from geometric_models import ARMS, INTERACTIONS, GeometricModel, PrototypeGeometry, design
from neighbor_experiment import calibrated_bundle, inference_work, probabilities


class GeometricTests(unittest.TestCase):
    def setUp(self):
        self.x = np.array([[v + .1*j*v*v for j in range(15)]
            for v in (0, 1, 3, 4, 8, 9, 15, 16)], dtype=float)
        self.y = np.array([0, 1]*4)
        self.groups = np.array(["a", "a", "b", "b", "c", "c", "d", "d"])
        self.geometry = PrototypeGeometry(self.x, self.y, self.groups, prototypes=1)

    def test_one_prototype_is_class_mean_and_distances_match(self):
        z = self.geometry.scaler.transform(self.x)
        for label, center in enumerate(self.geometry.centers):
            np.testing.assert_allclose(center[0], z[self.y == label].mean(axis=0), atol=1e-12)
        query = self.x[:1]
        expected = [np.linalg.norm(z[0]-z[self.y == label].mean(axis=0)) for label in (0, 1)]
        np.testing.assert_allclose(self.geometry.class_distances(query)[0], expected)

    def test_own_list_excludes_both_labels_and_all_related_targets(self):
        d = self.geometry.class_distances(self.x[:2], self.groups[:2])
        z = self.geometry.scaler.transform(self.x)
        for row in range(2):
            for label in (0, 1):
                keep = (self.groups != "a") & (self.y == label)
                expected = np.linalg.norm(z[row]-z[keep].mean(axis=0))
                self.assertAlmostEqual(d[row, label], expected, places=12)

    def test_list_balancing_prevents_duplicate_target_weighting(self):
        x = np.vstack((self.x, self.x[:1], self.x[:1]))
        expanded = PrototypeGeometry(x, np.r_[self.y, 0, 0],
            np.concatenate((self.groups, ["a", "a"])), prototypes=1)
        for original, duplicate in zip(self.geometry.centers, expanded.centers):
            np.testing.assert_allclose(self.geometry.scaler.inverse_transform(original),
                expanded.scaler.inverse_transform(duplicate), atol=1e-10)

    def test_interactions_are_all_ten_unique_structural_products(self):
        self.assertEqual(len(INTERACTIONS), 10)
        z = self.geometry.scaler.transform(self.x)
        values = self.geometry.interaction_values(self.x)
        for column, (i, j) in enumerate(INTERACTIONS):
            self.assertLess(i, j)
            np.testing.assert_allclose(values[:, column], z[:, i]*z[:, j])
        changed = self.x.copy()
        changed[:, 5:] += 1000
        np.testing.assert_allclose(values, self.geometry.interaction_values(changed))

    def test_design_dimensions_and_precomputed_out_of_list_features(self):
        distances = self.geometry.class_distances(self.x, self.groups)
        for arm, size in zip(ARMS, (15, 17, 25, 27)):
            values = design(self.x, self.geometry, arm, distances=distances)
            self.assertEqual(values.shape, (8, size))
            np.testing.assert_array_equal(values[:, :15], self.x)
            if arm in ("prototypes", "combined"):
                np.testing.assert_array_equal(values[:, 15:17], distances)

    def test_online_adapter_and_paid_cost(self):
        for arm, dimensions in zip(ARMS[1:], (17, 25, 27)):
            tx = design(self.x, self.geometry, arm, exclude_groups=self.groups)
            fitted = make_pipeline(StandardScaler(), LogisticRegression()).fit(tx, self.y)
            model = GeometricModel(self.geometry, arm, fitted)
            expected = fitted.predict_proba(design(self.x, self.geometry, arm))
            np.testing.assert_allclose(model.predict_proba(self.x), expected)
            bundle = calibrated_bundle(model, self.x, self.y, dimensions)
            self.assertTrue(np.isfinite(probabilities(bundle, self.x)).all())
            saved = dict(bank=self.geometry, bundles={arm:bundle})
            self.assertEqual(inference_work(saved, arm), 6*dimensions+20+self.geometry.work(arm))
        self.assertGreater(self.geometry.work("combined"), self.geometry.work("prototypes"))
        self.assertEqual(self.geometry.work("interactions"), 55)

    def test_prototype_count_is_bounded_and_reproducible(self):
        first = PrototypeGeometry(self.x, self.y, self.groups, prototypes=3)
        second = PrototypeGeometry(self.x, self.y, self.groups, prototypes=3)
        for a, b in zip(first.centers, second.centers):
            self.assertLessEqual(len(a), 3)
            np.testing.assert_array_equal(a, b)

    def test_missing_class_or_empty_excluded_class_rejected(self):
        with self.assertRaises(ValueError):
            PrototypeGeometry(self.x, np.ones(8), self.groups)
        with self.assertRaises(ValueError):
            PrototypeGeometry(self.x[:, :14], self.y, self.groups)
        small = PrototypeGeometry(self.x[:2], self.y[:2], self.groups[:2], prototypes=3)
        with self.assertRaises(ValueError):
            small.class_distances(self.x[:1], ["a"])


if __name__ == "__main__":
    unittest.main()
