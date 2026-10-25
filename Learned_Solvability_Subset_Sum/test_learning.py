import unittest

try:
    import numpy as np
    from fit_development import fit_model, matrix, metrics
    HAVE_ML = True
except ImportError:
    HAVE_ML = False


@unittest.skipUnless(HAVE_ML, "optional requirements-ml.txt dependencies not installed")
class LearningTests(unittest.TestCase):
    def test_test_labels_cannot_affect_fitting_or_calibration(self):
        x = np.arange(20, dtype=float).reshape(10, 2)
        y = np.array([0, 0, 1, 1, 0, 1, 0, 1, 0, 1])
        training = np.array([True] * 4 + [False] * 6)
        calibration = np.array([False] * 4 + [True] * 4 + [False] * 2)
        raw_a, cal_a = fit_model(x, y, training, calibration, "logistic")
        altered = y.copy()
        altered[8:] = 1 - altered[8:]
        raw_b, cal_b = fit_model(x, altered, training, calibration, "logistic")
        np.testing.assert_array_equal(raw_a, raw_b)
        np.testing.assert_array_equal(cal_a, cal_b)

    def test_feature_matrix_excludes_oracle_and_completion_labels(self):
        rows = [{"features": {"target_progression": [1, 2, 3, 4, 5]},
                 "conventional": [6, 7], "oracle_mask": 123, "truth": "yes"}]
        original = matrix(rows, "hybrid")
        rows[0]["oracle_mask"], rows[0]["truth"] = None, "no"
        np.testing.assert_array_equal(original, matrix(rows, "hybrid"))
        self.assertEqual(matrix(rows, "target_progression").shape[1], 5)

    def test_probability_metrics_handle_one_class_evaluation(self):
        score = metrics([1, 1], [0.9, 0.8])
        self.assertIsNone(score["auc"])
        self.assertAlmostEqual(score["brier"], 0.025)
        self.assertGreater(score["log_loss"], 0)


if __name__ == "__main__":
    unittest.main()
