"""Check budget bookkeeping and labels independently on small exact instances."""

import random
import unittest

from run_pilot import CONFIG, check, independent_halves, independent_query, portfolio, weights_for


class PilotTests(unittest.TestCase):
    def test_portfolio_answers_and_budget(self):
        rng = random.Random(117)
        for _ in range(25):
            weights = [rng.randrange(1, 40) for _ in range(rng.randrange(1, 9))]
            reachable = {0}
            for weight in weights:
                reachable |= {value + weight for value in reachable}
            halves = independent_halves(weights)
            for target in range(-1, sum(weights) + 2):
                self.assertEqual(independent_query(halves, target) is not None, target in reachable)
                for cap in (1, 10, 3000):
                    result = portfolio(weights, target, cap)
                    self.assertLessEqual(result["work"], cap)
                    self.assertEqual(sum(row["work"] for row in result["attempts"]), result["work"])
                    check(weights, target, target in reachable, result)
                    if cap == 3000:
                        self.assertNotEqual(result["status"], "unresolved")

    def test_filtered_gcd_resolves_target_specific_no(self):
        weights = [10, 14, 18, 43]
        result = portfolio(weights, 21, 100)
        self.assertEqual(result["status"], "no")
        self.assertEqual(len(result["attempts"]), 1)

    def test_generators(self):
        rng = random.Random(118)
        for family in CONFIG["families"]:
            for n in CONFIG["sizes"]:
                for replacements in (0, n // 4):
                    weights = weights_for(family, n, replacements, rng)
                    self.assertEqual(len(weights), n)
                    self.assertTrue(all(type(w) is int and w > 0 for w in weights))


if __name__ == "__main__":
    unittest.main()
