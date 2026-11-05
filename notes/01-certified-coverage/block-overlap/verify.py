"""Independent finite checks of the block-overlap theorem and implementation.

These checks supplement the proof. They are not performance benchmarks.
"""

import argparse
from functools import lru_cache
import hashlib
from itertools import combinations_with_replacement
import json
from pathlib import Path
import random

from solver import interval_overlap, prepare, solve


def brute_support(weights):
    return {sum(w for i, w in enumerate(weights) if mask & (1 << i))
            for mask in range(1 << len(weights))}


def brute_best_product(weights, limit):
    """Enumerate all cut sets; compute overlaps without the sliding window."""
    weights = tuple(sorted(weights))
    n = len(weights)
    if not n:
        return 1

    @lru_cache(None)
    def score(start, stop):
        values = brute_support(weights[start:stop])
        width = sum(weights[:start])
        return max(sum(end - width <= s <= end for s in values)
                   for end in values)

    optimum = 1 << n
    for cuts in range(1 << (n - 1)):
        ends = [i for i in range(1, n) if cuts & (1 << (i - 1))] + [n]
        start = 0
        product = 1
        for stop in ends:
            if stop - start > limit:
                break
            product *= score(start, stop)
            start = stop
        else:
            optimum = min(optimum, product)
    return optimum


def check_targets(weights, representation, targets, expected):
    checked = 0
    for target in targets:
        result = solve(representation, target)
        assert (result.witness is not None) == (target in expected), (weights, target)
        if result.witness is not None:
            assert len(result.witness) == len(set(result.witness))
            assert all(0 <= i < len(weights) for i in result.witness)
            assert sum(weights[i] for i in result.witness) == target
        bound = (len(representation.blocks) + 1) * representation.product
        assert result.nodes <= bound
        assert result.children + 1 <= bound
        checked += 1
    return checked


def run():
    # Closed endpoints matter: two sums distance exactly width both qualify.
    assert interval_overlap([0, 3], 3) == 2
    assert interval_overlap([0, 3], 2) == 1
    exhaustive_inputs = partition_checks = target_checks = 0
    for n in range(7):
        for weights in combinations_with_replacement(range(1, 6), n):
            expected = brute_support(weights)
            previous = 1 << n
            for limit in (1, 2, 3):
                representation = prepare(weights, limit)
                assert representation.product == brute_best_product(weights, limit)
                assert representation.product <= previous
                previous = representation.product
                partition_checks += 1
                target_checks += check_targets(
                    weights, representation, range(-1, sum(weights) + 2), expected)
            exhaustive_inputs += 1

    seed = 20261104
    rng = random.Random(seed)
    random_inputs = 120
    for _ in range(random_inputs):
        weights = tuple(rng.randrange(1, 31) for _ in range(rng.randrange(13)))
        expected = brute_support(weights)
        representation = prepare(weights, rng.randrange(1, 5))
        target_checks += check_targets(
            weights, representation, range(-1, sum(weights) + 2), expected)

    # No global sum enumeration here: the proved decimal construction supplies
    # known YES/NO targets and an exact count of distinct sums.
    groups = 100
    weights = tuple(d * 10**j for j in range(groups) for d in (2, 3, 4))
    representation = prepare(weights, 3)
    yes_target = 7 * (10**groups - 1) // 9
    no_target = 8 * 10**(groups - 1)
    yes = solve(representation, yes_target)
    no = solve(representation, no_target)
    assert representation.product == 1
    assert len(representation.blocks) == groups
    assert yes.witness is not None and sum(weights[i] for i in yes.witness) == yes_target
    assert yes.nodes == groups + 1
    assert no.witness is None and no.nodes == 1
    # Check the digit argument independently for the first three blocks.
    for count in range(1, 4):
        small = weights[:3 * count]
        values = brute_support(small)
        assert len(values) == 1 << len(small)
        assert all(all(int(digit) in (0, 2, 3, 4, 5, 6, 7, 9)
                       for digit in str(value)) for value in values)

    # Large blocks can force product=1 on arbitrary inputs, but constructing
    # their supports incurs the work that the theorem explicitly charges.
    arbitrary = (2, 5, 6, 9, 11, 12)
    full = prepare(arbitrary, len(arbitrary))
    assert full.product == 1
    for bad in ((0,), (-1,), (1.5,)):
        try:
            prepare(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid weight accepted")

    root = Path(__file__).resolve().parent
    return {
        "status": "passed",
        "kind": "finite correctness checks; no timing or empirical speedup claims",
        "exhaustive_domain": "all sorted multisets of 0..6 items with values 1..5",
        "exhaustive_inputs": exhaustive_inputs,
        "partition_optimality_checks": partition_checks,
        "random_inputs": random_inputs,
        "random_seed": seed,
        "target_checks": target_checks,
        "large_constructed_family": {
            "items": len(weights), "blocks": groups,
            "distinct_subset_sums_by_proof": str(1 << len(weights)),
            "overlap_product": representation.product,
            "discovery_intervals_checked": representation.intervals_checked,
            "support_candidates_constructed_including_reconstruction":
                representation.support_candidates_constructed,
            "yes_search_nodes": yes.nodes, "no_search_nodes": no.nodes,
        },
        "source_sha256": {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                          for name in ("solver.py", "verify.py")},
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = json.dumps(run(), indent=2) + "\n"
    if args.output:
        args.output.write_text(report, encoding="utf-8")
    print(report, end="")
