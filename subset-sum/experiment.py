"""Small, reproducible exact subset-sum experiment. No third-party packages."""

from __future__ import annotations

import argparse
import json
import platform
import random
import statistics
import time
import tracemalloc
from pathlib import Path


TARGET_LIMIT = 100_000_000  # At most 12.5 MB for the target-indexed bitset.
MODULI = (8, 10, 16, 32)


def exhaustive(weights: list[int], target: int) -> bool:
    """Independent oracle used only on small inputs."""
    for mask in range(1 << len(weights)):
        total = 0
        for i, weight in enumerate(weights):
            if mask & (1 << i):
                total += weight
        if total == target:
            return True
    return False


def bitset_dp(weights: list[int], target: int) -> tuple[bool, dict]:
    bits = 1
    cap = (1 << (target + 1)) - 1
    for weight in weights:
        bits = (bits | (bits << weight)) & cap
    return bool((bits >> target) & 1), {"reachable_sums": bits.bit_count()}


def reachable_sums(weights: list[int], target: int) -> tuple[set[int], int]:
    sums = {0}
    attempts = 0
    for weight in weights:
        attempts += len(sums)
        sums |= {value + weight for value in sums if value + weight <= target}
    return sums, attempts


def meet_in_middle(weights: list[int], target: int) -> tuple[bool, dict]:
    ordered = sorted(weights, reverse=True)
    middle = len(ordered) // 2
    left, left_attempts = reachable_sums(ordered[:middle], target)
    right, right_attempts = reachable_sums(ordered[middle:], target)
    answer = any(target - value in right for value in left)
    return answer, {
        "left_sums": len(left),
        "right_sums": len(right),
        "sum_generation_attempts": left_attempts + right_attempts,
    }


def suffix_residues(weights: list[int], modulus: int) -> list[int]:
    """Bit i is set exactly when a suffix subset has residue i."""
    full_mask = (1 << modulus) - 1
    masks = [0] * (len(weights) + 1)
    masks[-1] = 1
    for i in range(len(weights) - 1, -1, -1):
        old = masks[i + 1]
        shift = weights[i] % modulus
        rotated = ((old << shift) | (old >> (modulus - shift))) & full_mask
        masks[i] = old | rotated
    return masks


def certified_pair_search(weights: list[int], target: int) -> tuple[bool, dict]:
    """Exact half-sum summary plus memoized, certified search of the other half."""
    ordered = sorted(weights, reverse=True)
    split = (len(ordered) + 1) // 2
    suffix_total = [0] * (len(ordered) + 1)
    for i in range(len(ordered) - 1, -1, -1):
        suffix_total[i] = suffix_total[i + 1] + ordered[i]
    residue_masks = [(modulus, suffix_residues(ordered, modulus)) for modulus in MODULI]
    seen: set[tuple[int, int]] = set()
    stats = {
        "tail_sums": 0,
        "tail_generation_attempts": 0,
        "visited_states": 0,
        "bound_prunes": 0,
        "residue_prunes": 0,
        "duplicate_states": 0,
        "paired_lookups": 0,
    }
    # A root certificate avoids constructing a paired summary at all.
    if target < 0 or target > suffix_total[0]:
        stats["visited_states"] = 1
        stats["bound_prunes"] = 1
        stats["memoized_states"] = 0
        return False, stats
    for modulus, masks in residue_masks:
        if not (masks[0] >> (target % modulus)) & 1:
            stats["visited_states"] = 1
            stats["residue_prunes"] = 1
            stats["memoized_states"] = 0
            return False, stats
    tail, tail_attempts = reachable_sums(ordered[split:], target)
    stats["tail_sums"] = len(tail)
    stats["tail_generation_attempts"] = tail_attempts

    def visit(i: int, partial: int) -> bool:
        stats["visited_states"] += 1
        if partial > target or partial + suffix_total[i] < target:
            stats["bound_prunes"] += 1
            return False
        for modulus, masks in residue_masks:
            if not (masks[i] >> ((target - partial) % modulus)) & 1:
                stats["residue_prunes"] += 1
                return False
        if i == split:
            stats["paired_lookups"] += 1
            return target - partial in tail
        key = (i, partial)
        if key in seen:
            stats["duplicate_states"] += 1
            return False
        seen.add(key)
        # Try including a large item first; ordering changes speed, not correctness.
        return visit(i + 1, partial + ordered[i]) or visit(i + 1, partial)

    answer = visit(0, 0)
    stats["memoized_states"] = len(seen)
    return answer, stats


def bounded_dfs(weights: list[int], target: int) -> tuple[bool, dict]:
    """Ablation: identical item order and memoization, without pairing or residues."""
    ordered = sorted(weights, reverse=True)
    suffix_total = [0] * (len(ordered) + 1)
    for i in range(len(ordered) - 1, -1, -1):
        suffix_total[i] = suffix_total[i + 1] + ordered[i]
    seen: set[tuple[int, int]] = set()
    stats = {"visited_states": 0, "bound_prunes": 0, "duplicate_states": 0}

    def visit(i: int, partial: int) -> bool:
        stats["visited_states"] += 1
        if partial > target or partial + suffix_total[i] < target:
            stats["bound_prunes"] += 1
            return False
        if i == len(ordered):
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


def make_case(family: str, n: int, seed: int) -> tuple[list[int], int]:
    rng = random.Random(f"{family}:{n}:{seed}")
    if family == "narrow":
        weights = [rng.randint(1, 25) for _ in range(n)]
        target = sum(weight for weight in weights if rng.randrange(2))
    elif family == "wide":
        weights = [rng.randint(1 << 44, (1 << 45) - 1) for _ in range(n)]
        target = sum(weight for weight in weights if rng.randrange(2))
    elif family == "mixed":
        large = [rng.randint(1_000_000, 9_000_000) for _ in range(n // 4)]
        small = [rng.randint(1, 25) for _ in range(n - len(large))]
        weights = large + small
        target = sum(weight for weight in weights if rng.randrange(2))
    elif family == "mixed_no":
        large = [1_000_000 * rng.randint(1, 9) for _ in range(n // 4)]
        small = [rng.randint(1, 25) for _ in range(n - len(large))]
        weights = large + small
        target = sum(weight for weight in large if rng.randrange(2)) + 50_000
    elif family == "modular_no":
        weights = [10 * rng.randint(100, 1000) for _ in range(n - 1)] + [1]
        halfway = sum(weights) // 2
        target = halfway - (halfway % 10) + 2
    else:
        raise ValueError(family)
    rng.shuffle(weights)
    return weights, target


def measured(fn, weights: list[int], target: int) -> dict:
    timings = []
    answer = None
    stats = None
    for _ in range(3):
        start = time.perf_counter()
        this_answer, this_stats = fn(weights, target)
        timings.append(time.perf_counter() - start)
        if answer is not None:
            assert this_answer == answer
        answer, stats = this_answer, this_stats
    tracemalloc.start()
    check_answer, _ = fn(weights, target)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert check_answer == answer
    return {
        "answer": answer,
        "seconds": statistics.median(timings),
        "peak_traced_mib": peak / (1024 * 1024),
        **stats,
    }


def validate() -> int:
    checks = 0
    for n in (8, 12, 16):
        for seed in range(8):
            for family in ("narrow", "wide", "mixed", "mixed_no", "modular_no"):
                weights, target = make_case(family, n, seed)
                expected = exhaustive(weights, target)
                assert meet_in_middle(weights, target)[0] == expected
                assert certified_pair_search(weights, target)[0] == expected
                if family != "wide":
                    assert bounded_dfs(weights, target)[0] == expected
                if target <= TARGET_LIMIT:
                    assert bitset_dp(weights, target)[0] == expected
                checks += 1
    return checks


def run() -> dict:
    validation_count = validate()
    sizes = {
        "narrow": (24, 36, 48),
        "wide": (24, 30, 36),
        "mixed": (24, 36, 48),
        "mixed_no": (24, 36, 48),
        "modular_no": (24, 36, 48),
    }
    rows = []
    for family, family_sizes in sizes.items():
        for n in family_sizes:
            for seed in range(2):
                weights, target = make_case(family, n, seed)
                results = {
                    "meet_in_middle": measured(meet_in_middle, weights, target),
                    "certified_pair_search": measured(certified_pair_search, weights, target),
                }
                if family != "wide":
                    results["bounded_dfs"] = measured(bounded_dfs, weights, target)
                if target <= TARGET_LIMIT:
                    results["bitset_dp"] = measured(bitset_dp, weights, target)
                answers = {result["answer"] for result in results.values()}
                assert len(answers) == 1, (family, n, seed, results)
                if family in ("modular_no", "mixed_no"):
                    assert answers == {False}
                else:
                    assert answers == {True}
                rows.append({
                    "family": family,
                    "n": n,
                    "seed": seed,
                    "target": target,
                    "answer": answers.pop(),
                    "results": results,
                })
                print(f"{family:10} n={n:2} seed={seed} done", flush=True)
    return {
        "validation_cases": validation_count,
        "machine": platform.platform(),
        "python": platform.python_version(),
        "target_limit": TARGET_LIMIT,
        "moduli": MODULI,
        "rows": rows,
    }


def write_report(data: dict, path: Path) -> None:
    lines = [
        "# First subset-sum experiments",
        "",
        "Series navigation: [reading order](../index.html#arc) · [Note IV: pairing in certified approximation](../notes/04-certified-approximation/Certified_Approximation_of_Subset_Sum.html).",
        "",
        "These measurements support [companion Note II](../notes/02-subset-sum-stress-test/Subset_Sum_as_a_Stress_Test.html), which interprets the exact-search results alongside the later hard-case and classifier experiments.",
        "",
        "All runs used Python " + data["python"] + " on " + data["machine"] + ".",
        f"All applicable exact implementations agreed with exhaustive search on {data['validation_cases']} small cases.",
        "Each time is the median of three uninstrumented runs, then the table takes the median of two fixed seeds.",
        "Peak memory is measured separately using Python `tracemalloc`; it is not total process memory.",
        "Targets above 100,000,000 skip bitset dynamic programming (DP) to avoid a large target-sized allocation.",
        "Unpaired bounded depth-first search (DFS) is omitted on wide inputs because it may explore exponentially many distinct states.",
        "",
        "In the table, $n$ is the number of weights, MITM means meet-in-the-middle, and ms means milliseconds. Pair / MITM and Pair / DFS divide the paired solver's time by each baseline's time; a ratio below 1 favors pairing. `n/a` means the solver was not run or the ratio is unavailable.",
        "",
        "**Input families.** `narrow`: weights 1–25, planted target; `wide`: 45-bit weights, planted target; "
        "`mixed`: one quarter million-scale weights and three quarters weights 1–25, planted target; "
        "`mixed_no`: one quarter million-multiple weights and three quarters weights 1–25, "
        "with a target 50,000 above a large-weight subset sum; "
        "`modular_no`: all weights multiples of ten except one 1, with a target ending in 2. "
        "The last two families have no solution; `modular_no` has global greatest common divisor (gcd) 1.",
        "",
        "| Input family | $n$ | Answer | Bitset DP (ms) | MITM (ms) | Bounded DFS (ms) | Certified pair (ms) | Pair / MITM | Pair / DFS |",
        "|---|---:|:---:|---:|---:|---:|---:|---:|---:|",
    ]
    for family in ("narrow", "wide", "mixed", "mixed_no", "modular_no"):
        sizes = sorted({row["n"] for row in data["rows"] if row["family"] == family})
        for n in sizes:
            group = [row for row in data["rows"] if row["family"] == family and row["n"] == n]
            median = lambda name: statistics.median(row["results"][name]["seconds"] for row in group)
            mitm = median("meet_in_middle")
            paired = median("certified_pair_search")
            dp = f"{1000 * median('bitset_dp'):.3f}" if "bitset_dp" in group[0]["results"] else "n/a"
            dfs_time = median("bounded_dfs") if "bounded_dfs" in group[0]["results"] else None
            dfs = f"{1000 * dfs_time:.3f}" if dfs_time is not None else "n/a"
            pair_dfs = f"{paired / dfs_time:.3f}×" if dfs_time is not None else "n/a"
            lines.append(
                f"| {family} | {n} | {'yes' if group[0]['answer'] else 'no'} | {dp} | {1000 * mitm:.3f} | {dfs} | {1000 * paired:.3f} | {paired / mitm:.3f}× | {pair_dfs} |"
            )
    lines += [
        "",
        "The certified pair search first checks whole-instance bounds and residues. If they pass, "
        "it stores all distinct sums of one half, then explores the other half. "
        "It merges equal partial sums, rejects sums outside exact lower/upper bounds, and rejects "
        "unreachable target residues modulo 8, 10, 16, or 32. Each rejection is sound. "
        "The simple meet-in-middle baseline also merges duplicate sums and discards sums above the target.",
        "Bounded DFS uses the same item order and exact interval bounds as the pair search, "
        "but no paired tail or residue checks. This separates early discovery of a planted solution "
        "from gains due to the added mechanisms.",
        "",
        "**Why the rejections are exact.** A positive-weight branch with partial sum above the target, "
        "or with partial sum plus all remaining weights below it, cannot succeed. If the needed "
        "remainder has no attainable suffix residue modulo any tested modulus, it cannot succeed "
        "either. A paired lookup succeeds exactly when the complement is among the stored tail sums.",
        "",
        "## Interpretation",
        "",
        "- Narrow weights favor bitset DP. Wide weights favor meet-in-the-middle. The paired solver does not beat either on those families.",
        "- On mixed inputs, pairing beats meet-in-the-middle, but plain bounded DFS is faster still. "
        "Early discovery or interval pruning explains the apparent gain; pairing has not earned its cost.",
        "- On `modular_no`, the residue-10 check rejects at the root before any tail summary is built. "
        "This is an exact polynomial-cost certificate, but it is a simple known arithmetic test that a stronger baseline could also use.",
        "- No learned proposal model was used. These results isolate exact representation and certification first.",
        "",
        "The next useful test is a family where bounded DFS and meet-in-the-middle both do substantial work, "
        "while a compact paired summary plus a nontrivial verifier saves time over both.",
        "",
        "Raw per-run times, traced memory, and operation counts are in [results.json](results.json). "
        "These small constructed families show behavior, not a new worst-case bound or a claim against optimized solvers.",
        "",
        "Reproduce with `python subset-sum/experiment.py` from the repository root.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).parent)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    data = run()
    (args.output_dir / "results.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    write_report(data, args.output_dir / "RESULTS.md")
