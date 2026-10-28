"""Soundness, finite-budget behavior and equivalence of frozen scalar inference."""
import json
from pathlib import Path
import random
import unittest

from advanced_features import extract_advanced
from branch_pruning import POLICIES, bounded_check, load_scorers, solve_branch


def reachable(weights):
    values = {0}
    for w in weights:
        values |= {x + w for x in values}
    return values


class BranchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scorers = load_scorers()

    def test_saved_prediction_equivalence(self):
        path = Path(__file__).parent / 'results/prospective_20261025/cases.jsonl'
        for line in path.read_text().splitlines():
            case = json.loads(line)
            for name, scorer in self.scorers.items():
                self.assertAlmostEqual(scorer(case['vectors'][name]),
                                       case['predictions'][name + ':logistic'], places=11)

    def test_core_exception_exhaustion_and_witnesses(self):
        rng = random.Random(828105)
        families = [[3 + 4*i for i in range(10)], [3]*5 + [7]*5,
                    [1, 3, 9, 27, 81, 243], [2, 2, 3, 3, 4, 5, 8]]
        families += [[rng.randrange(1, 120) for _ in range(10)] for _ in range(24)]
        for weights in families:
            truth = reachable(weights)
            features = extract_advanced(weights)
            for target in list(range(0, sum(weights) + 1, max(1, sum(weights)//15))) + [-1]:
                result = bounded_check(features, target, max_exceptions=10)
                self.assertEqual(result['status'], 'yes' if target in truth else 'no')
                if result['status'] == 'yes':
                    witness = result['witness']
                    self.assertEqual(len(witness), len(set(witness)))
                    self.assertEqual(sum(weights[i] for i in witness), target)

    def test_all_policies_match_exhaustive_truth(self):
        rng = random.Random(129811)
        for _ in range(16):
            weights = [rng.randrange(1, 400) for _ in range(12)]
            truth = reachable(weights)
            for target in (sum(weights)//2, rng.randrange(sum(weights)+1), -1, 0):
                for policy in POLICIES:
                    result = solve_branch(weights, target, policy, self.scorers,
                                          node_cap=20000, minimum_remaining=2, stride=2)
                    self.assertEqual(result['status'], 'yes' if target in truth else 'no')

    def test_budget_exhaustion_never_becomes_no(self):
        weights = [1000 + 2*i for i in range(12)] + [1001]
        for policy in POLICIES:
            timed = solve_branch(weights, 4567, policy, self.scorers, seconds=0)
            self.assertEqual(timed['status'], 'unresolved')
            capped = solve_branch(weights, 4567, policy, self.scorers,
                                  node_cap=1, checkpoints=0)
            self.assertEqual(capped['status'], 'unresolved')

    def test_structural_no_covers_whole_subtree(self):
        weights = [1000 + 2*i for i in range(12)]
        # Target passes gcd/range/reduction but lies between all k-item AP bands.
        result = solve_branch(weights, 1500, 'always_native', self.scorers)
        self.assertEqual(result['status'], 'no')
        self.assertEqual(result['counts']['structural_no'], 1)
        self.assertEqual(result['counts']['structural_no_leaves'], 2**len(weights))


if __name__ == '__main__':
    unittest.main()
