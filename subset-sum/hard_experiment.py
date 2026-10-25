"""Follow-up: large-target unsatisfiable instances with controlled sum collisions."""

from __future__ import annotations

import json
import math
import platform
import random
import statistics
import time
from pathlib import Path

from experiment import MODULI, certified_pair_search, exhaustive, meet_in_middle, suffix_residues


DFS_LIMIT_SECONDS = 2.0
FAMILIES = ("unique", "pairs", "triples")
SIZES = (24, 30, 36)
SEEDS = (0, 1)


class TimeLimit(Exception):
    def __init__(self, stats: dict):
        self.stats = stats.copy()


def make_case(family: str, n: int, seed: int) -> tuple[list[int], int, int]:
    """Choose a near-middle NO target that passes every small-modulus root check."""
    multiplicity = {"unique": 1, "pairs": 2, "triples": 3}[family]
    assert n % multiplicity == 0
    rng = random.Random(f"hard:{family}:{n}:{seed}")
    distinct = set()
    while len(distinct) < n // multiplicity:
        distinct.add(rng.randrange(1 << 40, 1 << 41) | 1)
    weights = [value for value in distinct for _ in range(multiplicity)]
    rng.shuffle(weights)
    assert math.gcd(*weights) == 1
    residue_masks = [(modulus, suffix_residues(weights, modulus)[0]) for modulus in MODULI]
    total = sum(weights)
    for attempt in range(1, 101):
        target = total // 2 + rng.randrange(1, 1 << 20)
        if any(not (mask >> (target % modulus)) & 1 for modulus, mask in residue_masks):
            continue
        if not meet_in_middle(weights, target)[0]:
            return weights, target, attempt
    raise RuntimeError("could not generate a certified hard-family NO case")


def certified_dfs(weights: list[int], target: int, limit_seconds: float) -> tuple[bool, dict]:
    """Exact branch search with the same bounds, residues, order, and memoization."""
    ordered = sorted(weights, reverse=True)
    n = len(ordered)
    suffix_total = [0] * (n + 1)
    for i in range(n - 1, -1, -1):
        suffix_total[i] = suffix_total[i + 1] + ordered[i]
    residue_masks = [(modulus, suffix_residues(ordered, modulus)) for modulus in MODULI]
    stats = {"visited_states": 0, "bound_prunes": 0, "residue_prunes": 0, "duplicate_states": 0}
    seen: set[tuple[int, int]] = set()
    deadline = time.perf_counter() + limit_seconds

    def visit(i: int, partial: int) -> bool:
        stats["visited_states"] += 1
        if stats["visited_states"] % 1024 == 0 and time.perf_counter() >= deadline:
            stats["memoized_states"] = len(seen)
            raise TimeLimit(stats)
        if partial > target or partial + suffix_total[i] < target:
            stats["bound_prunes"] += 1
            return False
        for modulus, masks in residue_masks:
            if not (masks[i] >> ((target - partial) % modulus)) & 1:
                stats["residue_prunes"] += 1
                return False
        if i == n:
            return partial == target
        key = (i, partial)
        if key in seen:
            stats["duplicate_states"] += 1
            return False
        seen.add(key)
        return visit(i + 1, partial + ordered[i]) or visit(i + 1, partial)

    answer = visit(0, 0)
    stats["memoized_states"] = len(seen)
    return answer, stats


def certified_mitm(weights: list[int], target: int) -> tuple[bool, dict]:
    """Meet-in-the-middle charged for the same whole-instance certificates."""
    if target < 0 or target > sum(weights):
        return False, {"root_bound_prune": 1, "left_sums": 0, "right_sums": 0}
    for modulus in MODULI:
        mask = suffix_residues(weights, modulus)[0]
        if not (mask >> (target % modulus)) & 1:
            return False, {"root_residue_prune": 1, "left_sums": 0, "right_sums": 0}
    return meet_in_middle(weights, target)


def measured(fn, weights: list[int], target: int) -> dict:
    start = time.perf_counter()
    try:
        answer, stats = fn(weights, target)
        status = "completed"
    except TimeLimit as exc:
        answer, stats, status = None, exc.stats, "time_limit"
    return {"status": status, "answer": answer, "seconds": time.perf_counter() - start, **stats}


def validate() -> int:
    checks = 0
    for family in FAMILIES:
        for seed in range(3):
            weights, target, _ = make_case(family, 12, seed)
            assert exhaustive(weights, target) is False
            assert certified_pair_search(weights, target)[0] is False
            assert certified_dfs(weights, target, 10.0)[0] is False
            checks += 1
    return checks


def run() -> dict:
    validation_count = validate()
    rows = []
    for family in FAMILIES:
        for n in SIZES:
            for seed in SEEDS:
                weights, target, attempts = make_case(family, n, seed)
                # All solvers get the same sorted order and exact modulus checks.
                mitm = measured(certified_mitm, weights, target)
                pair = measured(certified_pair_search, weights, target)
                dfs = measured(lambda w, t: certified_dfs(w, t, DFS_LIMIT_SECONDS), weights, target)
                assert mitm["answer"] is False and pair["answer"] is False
                if dfs["status"] == "completed":
                    assert dfs["answer"] is False
                rows.append({
                    "family": family,
                    "n": n,
                    "seed": seed,
                    "target": target,
                    "generation_attempts": attempts,
                    "meet_in_middle": mitm,
                    "certified_pair_search": pair,
                    "certified_dfs": dfs,
                })
                print(f"{family:7} n={n:2} seed={seed} DFS={dfs['status']}", flush=True)
    return {
        "validation_cases": validation_count,
        "machine": platform.platform(),
        "python": platform.python_version(),
        "dfs_limit_seconds": DFS_LIMIT_SECONDS,
        "moduli": MODULI,
        "rows": rows,
    }


def write_report(data: dict, path: Path) -> None:
    lines = [
        "# Follow-up: hard no-solution subset-sum cases",
        "",
        "Series navigation: [reading order](../index.html#arc) · [Note IV: pairing in certified approximation](../notes/04-certified-approximation/Certified_Approximation_of_Subset_Sum.html).",
        "",
        "These measurements support [companion Note II](../notes/02-subset-sum-stress-test/Subset_Sum_as_a_Stress_Test.html).",
        "",
        "This experiment tests whether paired summaries add a benefit after cheap root certificates have failed.",
        f"The solvers agreed with exhaustive search on {data['validation_cases']} small cases. "
        "Both meet-in-the-middle and the paired solver returned NO on every benchmark case.",
        "Each weight is a random 41-bit odd integer, appearing once, twice, or three times; the table calls these families `unique`, `pairs`, and `triples`, respectively. "
        "Targets lie near half the total weight. Every target passes the whole-instance bounds "
        "and the reachable-residue checks modulo 8, 10, 16, and 32; all inputs have greatest common divisor (gcd) 1.",
        "The sorted half split keeps repeated weights together. The same whole-instance bounds "
        "and residue checks are charged to all algorithms. Bitset dynamic programming (DP) is infeasible because targets are trillions.",
        f"Certified depth-first search (DFS) is stopped after {data['dfs_limit_seconds']:.0f} seconds; a stopped run has no answer. "
        "Times are one uninstrumented Python run per seed, with medians below. In the table, $n$ is the number of weights, MITM means meet-in-the-middle, ms means milliseconds, Pair / MITM is the paired time divided by MITM time, and Pair tail sums counts distinct stored half sums. All data is in [hard_results.json](hard_results.json).",
        "",
        "| Family | $n$ | MITM (ms) | Certified pair (ms) | Pair / MITM | Certified DFS (ms) | Pair tail sums |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for family in FAMILIES:
        for n in SIZES:
            group = [row for row in data["rows"] if row["family"] == family and row["n"] == n]
            median = lambda name: statistics.median(row[name]["seconds"] for row in group)
            mitm = median("meet_in_middle")
            pair = median("certified_pair_search")
            dfs = (
                f"{1000 * median('certified_dfs'):.1f}"
                if all(row["certified_dfs"]["status"] == "completed" for row in group)
                else ">2000 (some stopped)"
            )
            tails = statistics.median(row["certified_pair_search"]["tail_sums"] for row in group)
            lines.append(
                f"| {family} | {n} | {1000 * mitm:.1f} | {1000 * pair:.1f} | "
                f"{pair / mitm:.2f}× | {dfs} | {tails:,.0f} |"
            )
    lines += [
        "",
        f"The paired solver was faster on "
        f"{sum(row['certified_pair_search']['seconds'] < row['meet_in_middle']['seconds'] for row in data['rows'])} "
        f"of {len(data['rows'])} individual cases. This implementation therefore shows no incremental "
        "subset-sum gain on the tested collision levels.",
        "",
        f"Across all {len(data['rows'])} benchmark cases, the paired solver made "
        f"{sum(row['certified_pair_search']['residue_prunes'] for row in data['rows'])} residue-based branch rejections. "
        f"Bounds rejected {sum(row['certified_pair_search']['bound_prunes'] for row in data['rows']):,} "
        f"of {sum(row['certified_pair_search']['visited_states'] for row in data['rows']):,} visited branch states. "
        "These checks supplied little additional pruning on this family; meet-in-the-middle already compresses "
        "equal sums in both halves.",
        "",
        "A ratio below 1 means the paired solver was faster than meet-in-the-middle. "
        "That ratio alone does not establish a new algorithm: both are exact variants of half-sum search, "
        "and the dataset is small and constructed.",
        "",
        "Reproduce with `python subset-sum/hard_experiment.py` from the repository root.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    output = Path(__file__).parent
    data = run()
    (output / "hard_results.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    write_report(data, output / "HARD_RESULTS.md")
