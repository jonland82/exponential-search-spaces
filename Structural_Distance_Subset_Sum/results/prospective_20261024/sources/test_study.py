"""Check the study's conditioning and paired, censor-aware summaries."""

import unittest

from analyze_study import aggregate_runs, paired
from run_study import eligible, memory_subset, residue_sets, specs


class StudyTests(unittest.TestCase):
    def test_modular_filter_matches_independent_brute_residues(self):
        weights = [3, 7, 7, 19, 41]
        sums = {
            sum(w for i, w in enumerate(weights) if mask >> i & 1)
            for mask in range(1 << len(weights))
        }
        residues = residue_sets(weights)
        for target in range(100):
            expected = all(target % m in {s % m for s in sums} for m, _ in residues)
            self.assertEqual(eligible(target, residues), expected)
        self.assertTrue(all(eligible(target, residues) for target in sums))

    def test_predeclared_grid_and_memory_subset(self):
        grid = list(specs())
        self.assertEqual(len(grid), 60)
        self.assertEqual(len(set(grid)), 60)
        cases = [{
            "n": n, "injected": r, "family": f, "replicate": seed,
            "target_rule": "conditioned_no",
        } for n, r, f, seed in grid]
        selected = memory_subset(cases)
        self.assertEqual(len(selected), 4)
        self.assertEqual({case["family"] for case in selected}, {"unrelated", "repeated", "gadget", "generic"})

    def test_paired_summary_excludes_incomplete_repetitions(self):
        cases = [{"case_id": "a"}, {"case_id": "b"}]
        rows = []
        for case_id in ("a", "b"):
            for method in ("core_distinct", "dfs", "mitm", "bitset"):
                for repetition in range(3):
                    rows.append({
                        "case_id": case_id, "method": method, "repetition": repetition,
                        "status": "unresolved" if case_id == "b" and method == "core_distinct" and repetition == 1 else "no",
                        "stats": {
                            "total_seconds": 2 if method == "core_distinct" else 4,
                            "distinct_exception_sums": None,
                            "distinct_sums_complete": False,
                        },
                    })
        groups = aggregate_runs(rows, 3)
        self.assertTrue(groups[("b", "core_distinct")]["repeat_inconsistent"])
        result = paired(cases, groups, "core_distinct", "dfs")
        self.assertEqual(result, {"matched": 1, "wins": 1, "median_ratio": .5})
        result = paired(cases, groups, "core_distinct", "fastest_baseline")
        self.assertEqual(result["matched"], 1)


if __name__ == "__main__":
    unittest.main()
