"""Independent exact checks; run with python -m unittest -v test_bounds."""
from collections import Counter
import ast
import itertools
import math
from pathlib import Path
import random
import unittest

from bounds import (Targets, all_sums, collision_terms, collision_upper,
                    count_pairs, decision, exact_bitset_count, half_sums, partition,
                    residue_cap, selected_differences, study_targets,
                    support_interval)


def brute_sums(weights):
    return {sum(w for w, bit in zip(weights, bits) if bit)
            for bits in itertools.product((0, 1), repeat=len(weights))}


class Certificates(unittest.TestCase):
    def check_case(self, weights, targets):
        blocks, a, b = half_sums(weights)
        self.assertEqual(Counter(blocks[0]+blocks[1]), Counter(weights))
        self.assertTrue(set(blocks[0]).isdisjoint(blocks[1]))
        self.assertEqual(set(a), brute_sums(blocks[0]))
        self.assertEqual(set(b), brute_sums(blocks[1]))
        eligible = {t for t in range(targets.lo, targets.hi+1)
                    if t % targets.period in targets.residues}
        truth = len(brute_sums(weights) & eligible)
        for target in sorted(eligible)[::max(1, len(eligible)//5)]:
            self.assertEqual(decision(target, a, set(b)), target in brute_sums(weights))
        hist = Counter(x+y for x in a for y in b if x+y in eligible)
        m, j = sum(hist.values()), sum(r*(r-1)//2 for r in hist.values())
        self.assertEqual(count_pairs(a, b, targets), m)
        self.assertEqual(exact_bitset_count(weights, targets), truth)
        self.assertLessEqual(m, len(a)*len(b))
        self.assertLessEqual(len(a)*len(b), __import__('math').prod(
            c+1 for c in Counter(weights).values()))
        differences = sorted({y-x for x in a for y in a if y > x})
        terms = list(collision_terms(a, b, targets, differences))
        self.assertEqual(sum(term for _, term in terms), j)
        r, _ = residue_cap(a, b)
        self.assertLessEqual(max(hist.values(), default=0), r)
        self.assertLessEqual(j, collision_upper(m, r))
        for lower_j, upper_j in [(0, collision_upper(m, r)),
                                 (sum(v for _, v in terms[:3]), collision_upper(m, r)),
                                 (j, j)]:
            low, high = support_interval(m, lower_j, upper_j, r, targets.size)
            self.assertLessEqual(low, truth)
            self.assertLessEqual(truth, high)
        chosen = selected_differences(a, b, 8)
        self.assertEqual(len(chosen), len(set(chosen)))

    def test_exhaustive_small_weight_multisets(self):
        for n in range(1, 7):
            for weights in itertools.combinations_with_replacement(range(1, 5), n):
                for targets in [Targets(-2, sum(weights)+1),
                                Targets(1, max(1, sum(weights)-1), 3, (0, 1))]:
                    self.check_case(list(weights), targets)

    def test_1200_random_irregular_targets(self):
        rng = random.Random(2026102301)
        for _ in range(1200):
            weights = [rng.randint(1, 40) for _ in range(rng.randint(2, 10))]
            lo, hi = sorted(rng.sample(range(-5, sum(weights)+6), 2))
            period = rng.randint(1, 9)
            residues = tuple(sorted(rng.sample(range(period), rng.randint(1, period))))
            if not any(t % period in residues for t in range(lo, hi+1)):
                continue
            self.check_case(weights, Targets(lo, hi, period, residues))

    def test_documented_example_and_zero_cases(self):
        weights, targets = [10, 20, 30, 100], Targets(20, 120)
        a, b = sorted(all_sums([10, 20])), sorted(all_sums([30, 100]))
        self.assertEqual(count_pairs(a, b, targets), 9)
        self.assertEqual(support_interval(9, 1, 1, 2, 101), (8, 8))
        self.check_case(weights, targets)
        self.check_case([2, 2, 2], Targets(1, 1))
        self.check_case([2, 2, 2], Targets(6, 6))
        self.check_case([1, 2, 4, 8], Targets(0, 15))
        self.assertEqual(support_interval(0, 0, 0, 1, 1), (0, 0))
        self.assertEqual(exact_bitset_count([1, 100], Targets(1, 100), max_bits=10), None)

    def test_target_rule_and_uniform_rank_mapping(self):
        class FixedRank:
            def __init__(self, value):
                self.value = value
            def randrange(self, size):
                assert self.value < size
                return self.value
        for targets in [Targets(-7, 17, 5, (0, 2, 4)), Targets(3, 3, 8, (3,)),
                        study_targets([3, 3, 8, 12, 21])]:
            eligible = {t for t in range(targets.lo, targets.hi+1) if targets.contains(t)}
            self.assertEqual(len(eligible), targets.size)
            draws = [targets.sample(FixedRank(i)) for i in range(targets.size)]
            self.assertEqual(set(draws), eligible)
            self.assertEqual(len(draws), len(set(draws)))
        for weights in [[1], [3, 3, 8, 12, 21], [10, 20, 30, 100]]:
            targets = study_targets(weights)
            a, b = half_sums(weights)[1:]
            self.assertEqual(count_pairs(a, b, targets, True), count_pairs(a, b, targets))
            self.assertEqual(exact_bitset_count(weights, targets),
                             len({s for s in brute_sums(weights) if targets.contains(s)}))

    def test_invalid_certificates(self):
        for weights in [[], [0, 1], [-1, 2], [1.5, 2], [True, 2]]:
            with self.assertRaises(ValueError):
                partition(weights)
        for args in [(2, 1), (1, 2, 2, (3,)), (1, 2, 3, (0,))]:
            with self.assertRaises(ValueError):
                Targets(*args)
        with self.assertRaises(ValueError):
            list(collision_terms([0, 1], [0, 1], Targets(0, 2), [1, 1]))
        with self.assertRaises(ValueError):
            support_interval(0, 0, 0, 1, 1, lower=1)

    def test_collision_upper_against_integer_optimization(self):
        for cap in range(1, 8):
            best = [0]
            for m in range(1, 40):
                best.append(max(best[m-r]+r*(r-1)//2 for r in range(1, min(m, cap)+1)))
                self.assertEqual(collision_upper(m, cap), best[m])

    def test_generator_matches_preserved_snapshot(self):
        from run_study import make_weights
        source = Path(__file__).resolve().parent.parent/'subset_sum_refinement/upstream/subset-sum/ml_experiment.py'
        tree = ast.parse(source.read_text(encoding='utf-8'))
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'make_weights')
        namespace = {'math': math, 'random': random}
        exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), 'exec'), namespace)
        for n in [12, 16, 20, 22]:
            for family in ['independent', 'paired']:
                for index in range(20):
                    seed = f'generator-verification:{n}:{family}:{index}'
                    self.assertEqual(make_weights(n, family, random.Random(seed)),
                                     namespace['make_weights'](n, family, random.Random(seed)))


if __name__ == '__main__':
    unittest.main()
