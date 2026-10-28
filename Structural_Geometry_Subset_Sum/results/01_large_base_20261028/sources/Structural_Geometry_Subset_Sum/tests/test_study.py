import random
import unittest

from Structural_Geometry_Subset_Sum.study import CONFIG, completion_difference, make_weights, signature
from Structural_Geometry_Subset_Sum.visualize import coordinate_cloud


class StudyTests(unittest.TestCase):
    def test_generators_are_positive_and_planted_decompositions_exact(self):
        for family in CONFIG["families"]:
            for replicate in range(4):
                weights, metadata = make_weights(family, 20, replicate, random.Random(f"test:{family}:{replicate}"))
                self.assertEqual(len(weights), 20)
                self.assertTrue(all(type(w) is int and w > 0 for w in weights))
                if "base" in metadata:
                    self.assertTrue(all(w == metadata["base"]*p+r
                        for w, p, r in zip(weights, metadata["p"], metadata["r"])))
        self.assertEqual(signature([3, 6, 9]), signature([18, 6, 12]))

    def test_coordinate_cloud_is_exact_until_its_diagnostic_cap(self):
        p, r = (0, 1, 2, 3), (1, -2, 3, -1)
        points, complete = coordinate_cloud(p, r, 100)
        expected = {(sum(p[i] for i in range(4) if mask >> i & 1),
                     sum(r[i] for i in range(4) if mask >> i & 1)) for mask in range(16)}
        self.assertTrue(complete)
        self.assertEqual(set(points), expected)
        points, complete = coordinate_cloud(p, r, 2)
        self.assertFalse(complete)
        self.assertEqual(len(points), 2)

    def test_bootstrap_keeps_one_lists_targets_and_repeats_together(self):
        rows = []
        for repeat in range(3):
            for target in range(3):
                for policy in ("root_geometry", "portfolio"):
                    rows.append(dict(list_id="one-list", repeat=repeat, mode="time", policy=policy,
                        status="yes" if policy == "root_geometry" else "unresolved"))
        result = completion_difference(rows, "root_geometry", "portfolio")
        self.assertAlmostEqual(result["repeat_average_difference"], 3)
        self.assertEqual(result["independent_lists"], 1)
        for value in result["list_bootstrap_95"]:
            self.assertAlmostEqual(value, 3)


if __name__ == "__main__":
    unittest.main()
