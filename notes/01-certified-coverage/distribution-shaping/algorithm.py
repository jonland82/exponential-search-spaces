"""Chosen-shape representations with independently certified difficulty buckets.

Labels describe a named solver exceeding a fixed budget. Training learns that
label from inexpensive features; reference scores define a rank transport;
independent calibration certifies mass and purity using exact binomial tests.
The optional subset-sum router changes the exact solving route, never the answer.
"""

import argparse
from bisect import bisect_left, bisect_right
from fractions import Fraction
from functools import lru_cache
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random
from statistics import NormalDist
import sys


FEATURE_NAMES = (
    "items", "encoding_bits", "maximum_bits", "normalized_total_log2",
    "target_fraction", "target_boundary_distance", "duplicate_fraction",
    "greedy_exception_fraction", "gcd_log2", "target_gcd_mismatch",
    "target_outside_range", "maximum_normalized_gap_fraction",
)
DEFAULT_SHAPES = (
    {"mu": -1.0, "sigma": 0.35, "lower": 0.05, "upper": 1.0},
    {"mu": 1.6, "sigma": 0.2, "lower": 2.0, "upper": 12.0},
)


def _digest(value):
    data = json.dumps(value, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def subset_features(weights, target):
    weights = tuple(weights)
    if type(target) is not int or any(type(w) is not int or w <= 0 for w in weights):
        raise ValueError("positive integer weights and an integer target required")
    n = len(weights)
    divisor = 0
    for w in weights:
        divisor = math.gcd(divisor, w)
    divisor = divisor or 1
    ordered = sorted(w // divisor for w in weights)
    total = sum(weights)
    normalized_total = sum(ordered)
    fraction = min(max(target, 0), total) / total if total else 0.0
    accepted_total = exceptions = 0
    for w in ordered:
        if w > accepted_total:
            accepted_total += w
        else:
            exceptions += 1
    gap = max((b - a for a, b in zip(ordered, ordered[1:])), default=0)
    bits = (2 * n.bit_length() + 1 + sum(2 * w.bit_length() + 1 for w in weights)
            + 2 * abs(target).bit_length() + 2)
    return (
        float(n), float(bits), float(max((w.bit_length() for w in weights), default=0)),
        math.log2(normalized_total + 1), fraction, min(fraction, 1 - fraction),
        (n - len(set(weights))) / max(1, n), exceptions / max(1, n),
        math.log2(divisor), float(target % divisor != 0),
        float(target < 0 or target > total), gap / max(1, normalized_total),
    )


def features(record):
    if "features" in record:
        values = tuple(float(v) for v in record["features"])
    else:
        values = subset_features(record["weights"], record["target"])
    if not values or not all(math.isfinite(v) for v in values):
        raise ValueError("nonempty finite feature vector required")
    return values


def hard_label(record, budget):
    cost = None
    if "cost" in record:
        try:
            cost = Fraction(str(record["cost"]))
        except (ValueError, ZeroDivisionError) as error:
            raise ValueError("cost must be finite and nonnegative") from error
        if cost < 0:
            raise ValueError("cost must be finite and nonnegative")
    if "hard" in record:
        if type(record["hard"]) is not bool:
            raise ValueError("hard must be an explicit boolean")
        label = record["hard"]
        if cost is not None and not record.get("censored", False):
            if label != (cost > Fraction(str(budget))):
                raise ValueError("hard label disagrees with observed complete cost")
        return int(label)
    if record.get("censored", False):
        raise ValueError("censored costs require an explicit budget-exceedance label")
    if cost is None:
        raise ValueError("a complete cost or explicit hard label is required")
    return int(cost > Fraction(str(budget)))


def fit_score(rows, budget, iterations=300, learning_rate=0.2, cost_weight_cap=None):
    vectors = [features(row) for row in rows]
    if not vectors:
        raise ValueError("training data cannot be empty")
    dimension = len(vectors[0])
    if any(len(v) != dimension for v in vectors):
        raise ValueError("inconsistent feature dimensions")
    means = [sum(v[j] for v in vectors) / len(vectors) for j in range(dimension)]
    scales = [math.sqrt(sum((v[j] - means[j]) ** 2 for v in vectors) / len(vectors))
              or 1.0 for j in range(dimension)]
    design = [[1.0] + [(v[j] - means[j]) / scales[j] for j in range(dimension)]
              for v in vectors]
    labels = [hard_label(row, budget) for row in rows]
    if cost_weight_cap is not None and (not math.isfinite(cost_weight_cap)
                                       or cost_weight_cap < 1):
        raise ValueError("cost_weight_cap must be finite and at least one")
    sample_weights = []
    for row in rows:
        weight = 1.0
        if cost_weight_cap is not None:
            cost = float(row.get("cost", 1.0))
            if not math.isfinite(cost) or cost < 0:
                raise ValueError("invalid training cost")
            weight = min(cost_weight_cap, max(1.0, cost))
        sample_weights.append(weight)
    normalizer = sum(sample_weights)
    coefficients = [0.0] * (dimension + 1)
    for _ in range(iterations):
        gradient = [0.0] * len(coefficients)
        for vector, label, weight in zip(design, labels, sample_weights):
            linear = sum(a * b for a, b in zip(coefficients, vector))
            probability = 1 / (1 + math.exp(-max(-40, min(40, linear))))
            error = weight * (probability - label)
            for j, value in enumerate(vector):
                gradient[j] += error * value
        for j in range(len(coefficients)):
            coefficients[j] -= learning_rate * gradient[j] / normalizer
    return {"means": means, "scales": scales, "coefficients": coefficients}


def score(model, vector):
    predictor = model["predictor"]
    if len(vector) != len(predictor["means"]):
        raise ValueError("feature dimension differs from fitted model")
    linear = predictor["coefficients"][0] + sum(
        a * ((v - mean) / scale) for a, v, mean, scale in zip(
            predictor["coefficients"][1:], vector,
            predictor["means"], predictor["scales"]))
    return 1 / (1 + math.exp(-max(-40, min(40, linear))))


def _normal_limits(shape):
    mu, sigma, lower, upper = (float(shape[k]) for k in ("mu", "sigma", "lower", "upper"))
    if not all(math.isfinite(v) for v in (mu, sigma, lower, upper)):
        raise ValueError("shape parameters must be finite")
    if sigma <= 0 or not 0 < lower < upper:
        raise ValueError("shape requires sigma>0 and 0<lower<upper")
    normal = NormalDist()
    left = normal.cdf((math.log(lower) - mu) / sigma)
    right = normal.cdf((math.log(upper) - mu) / sigma)
    if right - left < 1e-12:
        raise ValueError("truncated lognormal has numerically negligible probability")
    return left, right


def target_quantile(shape, rank):
    left, right = _normal_limits(shape)
    probability = left + rank * (right - left)
    probability = max(1e-15, min(1 - 1e-15, probability))
    value = math.exp(shape["mu"] + shape["sigma"] * NormalDist().inv_cdf(probability))
    return max(shape["lower"], min(shape["upper"], value))


def target_cdf(shape, value):
    if value <= shape["lower"]:
        return 0.0
    if value >= shape["upper"]:
        return 1.0
    left, right = _normal_limits(shape)
    probability = NormalDist().cdf((math.log(value) - shape["mu"]) / shape["sigma"])
    return (probability - left) / (right - left)


def transport(model, vector, tie_break):
    """Apply the FROZEN partition; tie_break is an independent U[0,1) draw.

    Buckets use reference ranks. Changing target shapes alone leaves these
    bucket identities unchanged for the same vector and tie_break.
    """
    if not 0 <= tie_break < 1:
        raise ValueError("tie_break must be in [0,1)")
    probability = score(model, vector)
    group = int(probability >= model["threshold"])
    reference = model["reference_scores"][group]
    if not reference:
        return {"score": probability, "group": group, "rank": None,
                "coordinate": None, "bucket": None}
    left, right = bisect_left(reference, probability), bisect_right(reference, probability)
    rank = (left + tie_break * (right - left)) / len(reference)
    rank = max(model["rank_clip"], min(1 - model["rank_clip"], rank))
    local = min(model["bins"] - 1, int(rank * model["bins"]))
    return {"score": probability, "group": group, "rank": rank,
            "coordinate": target_quantile(model["shapes"][group], rank),
            "bucket": group * model["bins"] + local}


def binomial_upper_tail(n, k, probability):
    """P[Bin(n,p)>=k] with exact rational arithmetic; endpoints included."""
    probability = Fraction(probability)
    if type(n) is not int or n < 0 or not 0 <= probability <= 1:
        raise ValueError("invalid binomial arguments")
    if k <= 0:
        return Fraction(1)
    if k > n or probability == 0:
        return Fraction(0)
    if probability == 1:
        return Fraction(1)
    a, b = probability.numerator, probability.denominator
    remainder = b - a
    term = math.comb(n, k) * a**k * remainder**(n - k)
    total = term
    for index in range(k, n):
        term = term * (n - index) * a // ((index + 1) * remainder)
        total += term
    return Fraction(total, b**n)


def certify_counts(counts, total, epsilon="0.1", minimum_mass="0.05", delta="0.05"):
    """Simultaneous mass and hard/easy purity tests for fixed buckets."""
    epsilon, gamma, delta = map(Fraction, (epsilon, minimum_mass, delta))
    if not 0 < epsilon < Fraction(1, 2) or not 0 < gamma < 1 or not 0 < delta < 1:
        raise ValueError("require 0<epsilon<1/2, 0<minimum_mass<1, 0<delta<1")
    if total < 1 or not counts or sum(n for n, _ in counts) > total:
        raise ValueError("invalid calibration counts")
    alpha = delta / (3 * len(counts))
    results = []
    for bucket, (n, hard) in enumerate(counts):
        if type(n) is not int or type(hard) is not int or not 0 <= hard <= n:
            raise ValueError("invalid bucket counts")
        hard_pass = bool(n and binomial_upper_tail(n, hard, 1 - epsilon) <= alpha)
        easy_pass = bool(n and binomial_upper_tail(n, n - hard, 1 - epsilon) <= alpha)
        mass_pass = binomial_upper_tail(total, n, gamma) <= alpha
        label = "hard" if hard_pass else "easy" if easy_pass else "unresolved"
        if not mass_pass:
            label = "unresolved"
        results.append({"bucket": bucket, "count": n, "hard_count": hard,
                        "mass_pass": mass_pass, "hard_pass": hard_pass,
                        "easy_pass": easy_pass, "label": label})
    return {"total": total, "epsilon": str(epsilon), "minimum_mass": str(gamma),
            "delta": str(delta), "per_test_alpha": str(alpha), "buckets": results}


def fit(train, reference, calibration, *, budget, solver_id, bins=2,
        threshold=0.5, epsilon="0.1", minimum_mass="0.05", delta="0.05",
        shapes=None, iterations=300, learning_rate=0.2, cost_weight_cap=None,
        calibration_seed=20261104):
    """Three disjoint roles; calibration labels never train the representation."""
    train, reference, calibration = map(list, (train, reference, calibration))
    if not solver_id or not math.isfinite(budget) or budget < 0:
        raise ValueError("a solver identity and finite nonnegative budget are required")
    if type(bins) is not int or bins < 1 or not 0 < threshold < 1:
        raise ValueError("invalid bins or score threshold")
    if type(iterations) is not int or iterations < 1 or not math.isfinite(learning_rate) or learning_rate <= 0:
        raise ValueError("invalid training controls")
    if not reference or not calibration:
        raise ValueError("reference and calibration splits cannot be empty")
    seen = set()
    for split in (train, reference, calibration):
        for row in split:
            if "id" in row:
                if row["id"] in seen:
                    raise ValueError("repeated observation id across training/reference/calibration")
                seen.add(row["id"])
            if "solver_id" in row and row["solver_id"] != solver_id:
                raise ValueError("mixed solver identities")
    chosen_shapes = [dict(s) for s in (shapes or DEFAULT_SHAPES)]
    if len(chosen_shapes) != 2:
        raise ValueError("two target components required")
    for shape in chosen_shapes:
        _normal_limits(shape)
    if chosen_shapes[0]["upper"] >= chosen_shapes[1]["lower"]:
        raise ValueError("easy and hard target supports must be disjoint and ordered")
    model = {
        "format_version": 1, "solver_id": solver_id, "budget": float(budget),
        "predictor": fit_score(train, budget, iterations, learning_rate, cost_weight_cap),
        "threshold": threshold, "bins": bins, "rank_clip": 1e-9 / bins,
        "shapes": chosen_shapes, "reference_scores": [[], []],
        "split_sizes": {"train": len(train), "reference": len(reference),
                        "calibration": len(calibration)},
        "training_cost_weight_cap": cost_weight_cap,
        "split_sha256": {name: _digest(rows) for name, rows in
                         (("train", train), ("reference", reference))},
    }
    for row in reference:
        probability = score(model, features(row))
        model["reference_scores"][int(probability >= threshold)].append(probability)
    for values in model["reference_scores"]:
        values.sort()
    # Representation and bucket definitions are now frozen before any
    # calibration feature, label, or randomized tie is examined.
    fingerprint = _digest(model)
    rng = random.Random(calibration_seed)
    counts = [[0, 0] for _ in range(2 * bins)]
    for row in calibration:
        assigned = transport(model, features(row), rng.random())
        label = hard_label(row, budget)
        if assigned["bucket"] is not None:
            counts[assigned["bucket"]][0] += 1
            counts[assigned["bucket"]][1] += label
    certified = certify_counts(counts, len(calibration), epsilon, minimum_mass, delta)
    return {"representation": model, "fingerprint": fingerprint,
            "calibration": certified, "calibration_seed": calibration_seed,
            "calibration_sha256": _digest(calibration),
            "calibration_fingerprint": _digest(certified)}


def check_frozen(artifact):
    if _digest(artifact["representation"]) != artifact["fingerprint"]:
        raise ValueError("representation changed after calibration; recalibrate")
    if _digest(artifact["calibration"]) != artifact["calibration_fingerprint"]:
        raise ValueError("calibration record changed after certification")


def identify(artifact, record, tie_break=None):
    check_frozen(artifact)
    if tie_break is None:
        tie_break = random.SystemRandom().random()
    assigned = transport(artifact["representation"], features(record), tie_break)
    assigned["label"] = ("unresolved" if assigned["bucket"] is None else
                         artifact["calibration"]["buckets"][assigned["bucket"]]["label"])
    return assigned


@lru_cache(maxsize=1)
def _exact_module():
    location = Path(__file__).resolve().parent.parent / "block-overlap" / "solver.py"
    spec = importlib.util.spec_from_file_location("coverage_exact_block_overlap", location)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _meet_in_middle(weights, target):
    module = _exact_module()
    middle = len(weights) // 2
    left, _ = module.support(list(enumerate(weights[:middle])))
    right, _ = module.support(list(enumerate(weights[middle:], start=middle)))
    i, j = 0, len(right) - 1
    while i < len(left) and j >= 0:
        value = left[i][0] + right[j][0]
        if value == target:
            mask = left[i][1] | right[j][1]
            return tuple(k for k in range(len(weights)) if mask & (1 << k))
        if value < target:
            i += 1
        else:
            j -= 1
    return None


def solve_subset_sum(artifact, weights, target, tie_break=None):
    """Exact router: easy bucket -> guarded block route; otherwise MITM.

    The guard K<=2^ceil(n/2) prevents a mistaken easy prediction from giving
    the block route a worse exponential upper bound than the MITM fallback.
    This is a correctness-preserving reference router, not a speedup claim.
    """
    weights = tuple(weights)
    vector = subset_features(weights, target)
    assigned = identify(artifact, {"features": vector}, tie_break)
    route = "meet_in_middle"
    if target < 0 or target > sum(weights):
        witness, route = None, "exact_range"
    elif assigned["label"] == "easy":
        module = _exact_module()
        representation = module.prepare(weights, 3)
        if representation.product <= 1 << ((len(weights) + 1) // 2):
            witness = module.solve(representation, target).witness
            route = "certified_block_search"
        else:
            witness = _meet_in_middle(weights, target)
    else:
        witness = _meet_in_middle(weights, target)
    if witness is not None:
        if len(witness) != len(set(witness)) or sum(weights[i] for i in witness) != target:
            raise AssertionError("invalid exact-solver witness")
    return {"answer": "YES" if witness is not None else "NO", "witness": witness,
            "route": route, "difficulty": assigned}


def _read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()
            if line.strip()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    fit_parser = commands.add_parser("fit")
    for name in ("train", "reference", "calibration", "output"):
        fit_parser.add_argument("--" + name, type=Path, required=True)
    fit_parser.add_argument("--solver-id", required=True)
    fit_parser.add_argument("--budget", type=float, required=True)
    fit_parser.add_argument("--config", type=Path,
                            help="JSON keyword options: shapes, bins, epsilon, minimum_mass, delta, etc.")
    predict_parser = commands.add_parser("predict")
    predict_parser.add_argument("--model", type=Path, required=True)
    predict_parser.add_argument("--input", type=Path, required=True)
    predict_parser.add_argument("--output", type=Path, required=True)
    predict_parser.add_argument("--seed", type=int)
    predict_parser.add_argument("--run-exact", action="store_true")
    args = parser.parse_args()
    if args.command == "fit":
        options = json.loads(args.config.read_text(encoding="utf-8")) if args.config else {}
        artifact = fit(_read_jsonl(args.train), _read_jsonl(args.reference),
                       _read_jsonl(args.calibration), budget=args.budget,
                       solver_id=args.solver_id, **options)
        args.output.write_text(json.dumps(artifact, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    else:
        artifact = json.loads(args.model.read_text(encoding="utf-8"))
        rng = random.Random(args.seed) if args.seed is not None else random.SystemRandom()
        outputs = []
        for row in _read_jsonl(args.input):
            output = (solve_subset_sum(artifact, row["weights"], row["target"], rng.random())
                      if args.run_exact else identify(artifact, row, rng.random()))
            outputs.append({"id": row.get("id"), **output})
        args.output.write_text("".join(json.dumps(row, allow_nan=False) + "\n" for row in outputs),
                               encoding="utf-8")


if __name__ == "__main__":
    main()
