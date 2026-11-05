"""Finite checks supplementing the shaping, bucket, and exact-routing proofs.

The demonstration labels are synthetic, with known population probabilities.
They are not measured subset-sum runtimes or a solver performance study.
"""

from bisect import bisect_left, bisect_right
from copy import deepcopy
from fractions import Fraction
from itertools import combinations_with_replacement
import argparse
import hashlib
import json
import math
from pathlib import Path
import random

from algorithm import (DEFAULT_SHAPES, binomial_upper_tail, certify_counts,
                       check_frozen, fit, hard_label, identify, score,
                       solve_subset_sum, subset_features, target_cdf,
                       target_quantile, transport)


def direct_tail(n, k, p):
    p = Fraction(p)
    return sum((Fraction(math.comb(n, i)) * p**i * (1 - p)**(n - i)
                for i in range(max(0, k), n + 1)), Fraction(0))


def finite_bucket_truth(model, population):
    """Integrate randomized ties exactly for a finite uniform population."""
    total = len(population)
    mass = [Fraction(0) for _ in range(2 * model["bins"])]
    hard_mass = [Fraction(0) for _ in mass]
    for vector, hard in population:
        value = score(model, vector)
        group = int(value >= model["threshold"])
        reference = model["reference_scores"][group]
        if not reference:
            continue
        left, right = bisect_left(reference, value), bisect_right(reference, value)
        for local in range(model["bins"]):
            if right > left:
                lower = Fraction(local * len(reference), model["bins"])
                upper = Fraction((local + 1) * len(reference), model["bins"])
                overlap = max(Fraction(0), min(Fraction(right), upper) - max(Fraction(left), lower))
                probability = overlap / (right - left)
            else:
                rank = Fraction(left, len(reference))
                index = min(model["bins"] - 1, int(rank * model["bins"]))
                probability = Fraction(index == local)
            bucket = group * model["bins"] + local
            mass[bucket] += probability / total
            hard_mass[bucket] += probability * hard / total
    return mass, hard_mass


def synthetic_demo():
    # Each split is sampled independently, WITH replacement, from the same
    # finite population. Observation IDs identify draws, not feature values.
    seed = 20261104
    rng = random.Random(seed)
    population = [((i / 100,), int(i >= 60)) for i in range(101)]

    def sample(prefix, size):
        rows = []
        for i in range(size):
            vector, hard = rng.choice(population)
            rows.append({"id": prefix + str(i), "features": list(vector),
                         "cost": 100 if hard else 1})
        return rows

    training = sample("train-", 400)
    reference = sample("reference-", 1600)
    calibration = sample("calibration-", 2000)
    artifact = fit(training, reference, calibration, budget=10,
                   solver_id="synthetic-known-cost-v1", epsilon="0.1",
                   minimum_mass="0.05", delta="0.05", calibration_seed=seed + 1)
    mass, hard_mass = finite_bucket_truth(artifact["representation"], population)
    certificates = []
    for bucket in artifact["calibration"]["buckets"]:
        index = bucket["bucket"]
        if bucket["label"] == "unresolved":
            continue
        assert mass[index] >= Fraction(1, 20)
        purity = hard_mass[index] / mass[index]
        assert (purity >= Fraction(9, 10) if bucket["label"] == "hard"
                else purity <= Fraction(1, 10))
        certificates.append({"bucket": index, "label": bucket["label"],
                             "true_population_mass": float(mass[index]),
                             "true_hard_fraction": float(purity),
                             "calibration_count": bucket["count"]})
    assert any(row["label"] == "hard" for row in certificates)
    assert any(row["label"] == "easy" for row in certificates)
    # Target shapes change coordinates, while frozen rank-bucket membership
    # and its true conditional hardness remain unchanged.
    altered = deepcopy(artifact["representation"])
    altered["shapes"] = [dict(s) for s in DEFAULT_SHAPES]
    altered["shapes"][0]["mu"] = -0.7
    altered["shapes"][1]["sigma"] = 0.4
    for vector, _ in population:
        first = transport(artifact["representation"], vector, 0.37)
        second = transport(altered, vector, 0.37)
        assert first["bucket"] == second["bucket"]
        assert first["rank"] == second["rank"]
    # Serialization preserves exactly the frozen representation and decisions.
    restored = json.loads(json.dumps(artifact))
    check_frozen(restored)
    for vector, _ in population:
        assert identify(artifact, {"features": vector}, 0.37) == identify(
            restored, {"features": vector}, 0.37)
    broken = deepcopy(restored)
    broken["representation"]["threshold"] += 0.01
    try:
        check_frozen(broken)
    except ValueError:
        pass
    else:
        raise AssertionError("changed representation was accepted")
    return artifact, {"seed": seed, "population_size": len(population),
                      "training": len(training), "reference": len(reference),
                      "calibration": len(calibration), "certified_buckets": certificates,
                      "interpretation": "synthetic cost labels; no measured solver speedup"}


def constant_model(hard, calibration_size):
    def rows(prefix, size):
        return [{"id": prefix + str(i), "features": [0.0] * 12,
                 "hard": hard} for i in range(size)]
    return fit(rows("t", 20), rows("r", 40), rows("c", calibration_size),
               budget=1, solver_id="artificial-routing-test", iterations=20,
               calibration_seed=77)


def run():
    tail_checks = 0
    for n in range(17):
        for p in (Fraction(0), Fraction(1, 4), Fraction(1, 2), Fraction(3, 4), Fraction(1)):
            for k in range(-1, n + 3):
                assert binomial_upper_tail(n, k, p) == direct_tail(n, k, p)
                tail_checks += 1
    # Exact type-I control, evaluated by summing the entire binomial law.
    null_checks = 0
    for n in range(1, 41):
        for p0 in (Fraction(1, 20), Fraction(1, 2), Fraction(9, 10)):
            for alpha in (Fraction(1, 20), Fraction(1, 100)):
                rejection_probability = sum(
                    (Fraction(math.comb(n, k)) * p0**k * (1 - p0)**(n - k)
                     for k in range(n + 1)
                     if binomial_upper_tail(n, k, p0) <= alpha), Fraction(0))
                assert rejection_probability <= alpha
                null_checks += 1
    assert certify_counts([(0, 0)], 20)["buckets"][0]["label"] == "unresolved"
    assert certify_counts([(1, 1)], 1)["buckets"][0]["label"] == "unresolved"
    assert hard_label({"hard": True, "cost": 10, "censored": True}, 10) == 1
    assert hard_label({"cost": 10**20 + 1}, 10**20) == 1
    assert hard_label({"cost": 10**20}, 10**20) == 0
    try:
        hard_label({"cost": 10, "censored": True}, 10)
    except ValueError:
        pass
    else:
        raise AssertionError("unlabelled censored observation was accepted")
    quantile_checks = 0
    for shape in DEFAULT_SHAPES:
        for i in range(1, 1000):
            rank = i / 1000
            z = target_quantile(shape, rank)
            assert shape["lower"] < z < shape["upper"]
            assert abs(target_cdf(shape, z) - rank) < 1e-10
            quantile_checks += 1
    # Tied scores must be randomized within their entire empirical CDF jump.
    constant = constant_model(False, 500)
    model = constant["representation"]
    ranks = [transport(model, (0.0,) * 12, (i + 0.5) / 100)["rank"] for i in range(100)]
    assert all(abs(rank - (i + 0.5) / 100) < 1e-12 for i, rank in enumerate(ranks))
    assert transport(model, (0.0,) * 12, 0)["bucket"] == 0
    assert transport(model, (0.0,) * 12, 0.999999)["bucket"] == 1
    # Empty source groups abstain rather than inventing a fitted distribution.
    absent = deepcopy(model)
    absent["reference_scores"] = [[], []]
    assert transport(absent, (0.0,) * 12, 0.5)["bucket"] is None
    artifact, demonstration = synthetic_demo()
    # Predictions of all three kinds must preserve exact subset-sum answers.
    models = [constant, constant_model(True, 500), constant_model(False, 1)]
    labels_seen = set()
    for item in models:
        labels_seen.add(identify(item, {"features": [0.0] * 12}, 0.37)["label"])
    assert labels_seen == {"easy", "hard", "unresolved"}
    exact_checks = 0
    routes_seen = set()
    for n in range(6):
        for weights in combinations_with_replacement(range(1, 5), n):
            values = {sum(w for i, w in enumerate(weights) if mask & (1 << i))
                      for mask in range(1 << n)}
            for target in range(-1, sum(weights) + 2):
                for fitted in models:
                    answer = solve_subset_sum(fitted, weights, target, 0.37)
                    routes_seen.add(answer["route"])
                    assert (answer["answer"] == "YES") == (target in values)
                    if answer["witness"] is not None:
                        assert sum(weights[i] for i in answer["witness"]) == target
                    exact_checks += 1
    assert routes_seen == {"exact_range", "meet_in_middle", "certified_block_search"}
    # Feature extraction handles scaled binary inputs without casting huge
    # weights to floating point, and retains target information.
    big = 1 << 2048
    assert all(math.isfinite(v) for v in subset_features([big, 3 * big], 2 * big))
    assert subset_features([2, 3], 1) != subset_features([2, 3], 4)
    root = Path(__file__).resolve().parent
    return {
        "status": "passed", "kind": "proof checks and synthetic known-population demonstration",
        "exact_binomial_tail_checks": tail_checks,
        "enumerated_null_rejection_bounds": null_checks,
        "target_quantile_inverse_checks": quantile_checks,
        "exact_subset_sum_router_checks": exact_checks,
        "routing_labels_tested": sorted(labels_seen), "exact_routes_tested": sorted(routes_seen),
        "synthetic_demo": demonstration,
        "source_sha256": {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                          for name in ("algorithm.py", "verify.py")},
    }, artifact


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--demo-model", type=Path)
    args = parser.parse_args()
    report, artifact = run()
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    if args.demo_model:
        args.demo_model.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(rendered, end="")
