"""Development comparison: five-feature variants, costs, reuse and grouped ML.

Exploratory development data, not the final prospective study. The common label
compares predictive information on the same solver task. Variant-specific runs
separately charge extraction and reuse full-core certificates before fallbacks.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
import json
from math import log2, sqrt
from pathlib import Path
import platform
import random
import shutil
import sys
from time import perf_counter

from advanced_features import (extract_advanced, lift_witness, query_advanced,
                               reduce_instance)
from features import FeatureConfig, extract, input_length, query
from run_pilot import (ROOT, check, correlation, independent_halves, independent_query,
                       portfolio, save_json, save_jsonl, sha, weights_for)


HERE = Path(__file__).resolve().parent
VARIANTS = ("original", "progression", "target_original", "target_progression")
CONFIG = {
    "status": "development comparison; not final prospective evidence",
    "seed": 620_251_026,
    "sizes": [24, 32, 36],
    "fractions": [0, 0.125, 0.25],
    "replicates": 4,
    "families": ["superincreasing", "coverage", "few_values", "small_support",
                 "interval_union", "progression", "near_equal", "random_wide", "filtered_modular"],
    "heldout_families": ["near_equal", "filtered_modular"],
    "larger_size": 36,
    "targets": ["planted", "uniform_middle", "odd_below_largest", "uniform_low"],
    "features": asdict(FeatureConfig()),
    "max_progression_steps": 16,
    "budget_multiplier": 8,
    "budget": "8 * features.input_length(original_weights, original_target)",
    "shared_solver": "exact target reduction, then feasibility-pilot fixed portfolio",
    "primary_comparison": "same solver-only label for all feature vectors; feature costs reported separately",
    "cost_policy": "shared exact prechecks first; if unresolved, prepay features, reuse full-core certificates, then fixed portfolio",
    "target_policy": "complement, prune overweight, force required items, repeat; range and gcd certificates",
    "split": "heldout families first; larger size next; other rep 0/1 train, 2 calibration, 3 test",
    "oracle": "independent full binary-mask half enumeration, destroyed before measured solving",
    "timing": "single measured run per case/policy; all orders seed-shuffled, descriptive only",
}


def split_for(n, family, replicate):
    if family in CONFIG["heldout_families"]:
        return "unseen_family"
    if n == CONFIG["larger_size"]:
        return "larger_size"
    return "train" if replicate < 2 else "calibration" if replicate == 2 else "test"


def conventional(weights, target):
    n, total = len(weights), sum(weights)
    mean = total / max(1, n)
    std = sqrt(sum((w - mean) ** 2 for w in weights) / max(1, n))
    return [float(n), float(input_length(weights, target)), log2(total + 1),
            log2(max(weights, default=0) + 1), log2(min(weights, default=0) + 1),
            len(set(weights)) / max(1, n), std / max(1, mean),
            target / max(1, total), min(target, total - target) / max(1, total),
            n / max(1, log2(max(weights, default=1) + 1))]


def full_core_query(features, advanced, target, cap):
    """Reuse only zero-deletion cores, with conservative query work charges.

    No exponential exceptional search is hidden here. If the next whole query
    cannot fit its declared upper-bound charge it is skipped, not partially run.
    """
    base = features.base if advanced else features
    n = len(base.weights)
    values = features.values
    used, attempts = 0, []
    for dimension, distance in enumerate(values):
        if distance != 0:
            continue
        if dimension in (0, 1):
            charge = 2 * n + 2
        elif dimension == 2:
            counts = Counter(base.weights)
            charge = n + 1
            combinations = 1
            for count in counts.values():
                combinations *= count + 1
            charge += combinations * (2 * len(counts) + 1)
        elif dimension == 3:
            charge = n + len(base.certificates[3].support) + 1
        elif advanced and features.progression is not None:
            charge = 8 * (n + 1)
        else:
            charge = n + 1 + sum(len(p) for p in base.certificates[4].prefixes)
        if used + charge > cap:
            continue
        used += charge
        witness = query_advanced(features, dimension, target) if advanced else query(features, dimension, target)
        status = "yes" if witness is not None else "no"
        attempts.append({"method": "reused_core", "dimension": dimension,
                         "status": status, "work": charge})
        return {"status": status, "witness": witness, "work": used, "attempts": attempts}
    return {"status": "unresolved", "witness": None, "work": used, "attempts": attempts}


def solve_policy(weights, target, kernel, cap, *, features=None,
                 advanced=False, target_aware=False):
    """Common exact solver or feature-cost/reuse policy; original-index witness."""
    started = perf_counter()
    needs_features = features is not None and kernel.status == "unresolved"
    feature_work = features.work if needs_features else 0
    feature_seconds = features.seconds if needs_features else 0
    # Features of the target kernel share the already-paid reduction with A.
    charge = kernel.work + feature_work
    times = kernel.seconds + feature_seconds
    attempts = []
    if charge >= cap:
        return {"status": "unresolved", "witness": None, "work": charge,
                "seconds": times, "feature_work": feature_work,
                "preprocess_work": kernel.work, "attempts": attempts,
                "extraction_exhausted": True, "reused": False}
    if kernel.status != "unresolved":
        return {"status": kernel.status, "witness": kernel.witness, "work": charge,
                "seconds": times, "feature_work": feature_work,
                "preprocess_work": kernel.work, "attempts": attempts,
                "extraction_exhausted": False, "reused": False}
    if features is not None:
        # List features query the original problem; target features query the
        # equivalent reduced problem. Both yield certified exact decisions.
        core_target = kernel.target if target_aware else target
        reuse = full_core_query(features, advanced, core_target, cap - charge)
        charge += reuse["work"]
        attempts.extend(reuse["attempts"])
        if reuse["status"] != "unresolved":
            witness = reuse["witness"]
            if witness is not None and target_aware:
                witness = lift_witness(kernel, witness)
            return {"status": reuse["status"], "witness": witness, "work": charge,
                    "seconds": times + perf_counter() - started,
                    "feature_work": feature_work, "preprocess_work": kernel.work,
                    "attempts": attempts, "extraction_exhausted": False, "reused": True}
    remaining = cap - charge
    result = portfolio(kernel.weights, kernel.target, remaining)
    witness = result["witness"]
    if witness is not None:
        witness = lift_witness(kernel, witness)
    attempts.extend(result["attempts"])
    return {"status": result["status"], "witness": witness,
            "work": charge + result["work"],
            "seconds": times + perf_counter() - started,
            "feature_work": feature_work, "preprocess_work": kernel.work,
            "attempts": attempts, "extraction_exhausted": False, "reused": False}


def summary_for(lists, cases, runs):
    groups = ("train", "calibration", "test", "larger_size", "unseen_family")
    summary = {"lists": len(lists), "cases": len(cases), "policy_runs": len(runs),
               "checked_completed": sum(r["status"] != "unresolved" for r in runs),
               "mismatches": 0, "splits": {}, "policies": {}, "features": {},
               "duplicate_sorted_lists": len(lists) - len({tuple(sorted(r["weights"])) for r in lists})}
    common = {r["case_id"]: r for r in runs if r["policy"] == "common"}
    for split in groups:
        group = [c for c in cases if c["split"] == split]
        summary["splits"][split] = {"cases": len(group),
            "lists": len({c["list_id"] for c in group}),
            "common_completed": sum(common[c["case_id"]]["status"] != "unresolved" for c in group),
            "preprocess_solved": sum(c["kernel"]["status"] != "unresolved" for c in group)}
    for name in VARIANTS:
        group = [r for r in runs if r["policy"] == name]
        summary["policies"][name] = {"completed": sum(r["status"] != "unresolved" for r in group),
            "extraction_exhausted": sum(r["extraction_exhausted"] for r in group),
            "reused_completions": sum(r["reused"] for r in group),
            "lost_vs_common": sum(common[r["case_id"]]["status"] != "unresolved" and r["status"] == "unresolved" for r in group),
            "gained_vs_common": sum(common[r["case_id"]]["status"] == "unresolved" and r["status"] != "unresolved" for r in group)}
        values = [c["features"][name] for c in cases]
        summary["features"][name] = {
            "coverage_fifth_correlation": correlation([v[1] for v in values], [v[4] for v in values]),
            "unique_vectors": len({tuple(v) for v in values}),
            "median_feature_ms": sorted(c["feature_seconds"][name] for c in cases)[len(cases) // 2] * 1000,
            "fifth_improved_vs_original": sum(c["features"][name][4] < c["features"]["original"][4] for c in cases),
            "different_vector_vs_original": sum(c["features"][name] != c["features"]["original"] for c in cases)}
    return summary


def generate(output):
    if output.exists():
        raise FileExistsError("development generation requires a fresh output directory")
    protected = [HERE / name for name in (
        "features.py", "advanced_features.py", "run_pilot.py", "run_development.py",
        "test_features.py", "test_pilot.py", "test_advanced_features.py", "test_development.py")]
    protected.append(ROOT / "Structural_Distance_Subset_Sum" / "structural_subset_sum.py")
    output.mkdir(parents=True)
    for path in protected:
        destination = output / "sources" / path.relative_to(ROOT)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
    protocol = {"config": CONFIG, "recorded_before_generation_utc": datetime.now(timezone.utc).isoformat(),
                "python": sys.version, "platform": platform.platform(),
                "source_hashes": {str(p.relative_to(ROOT)): sha(p) for p in protected}}
    save_json(output / "protocol.json", protocol)
    lists, cases, runs, signatures = [], [], [], set()
    for n in CONFIG["sizes"]:
        for family in CONFIG["families"]:
            for fraction in CONFIG["fractions"]:
                for replicate in range(CONFIG["replicates"]):
                    list_id = f"n{n}-{family}-r{round(n * fraction)}-s{replicate}"
                    rng = random.Random(f"{CONFIG['seed']}:{list_id}")
                    weights = weights_for(family, n, round(n * fraction), rng)
                    signature = tuple(sorted(weights))
                    if signature in signatures:
                        raise AssertionError("duplicate sorted list; no silent resampling")
                    signatures.add(signature)
                    split = split_for(n, family, replicate)
                    base = extract(weights, FeatureConfig(**CONFIG["features"]))
                    advanced = extract_advanced(weights, FeatureConfig(**CONFIG["features"]),
                                                max_steps=CONFIG["max_progression_steps"], base=base)
                    lists.append({"list_id": list_id, "family": family, "n": n,
                        "fraction": fraction, "replicate": replicate, "split": split,
                        "weights": weights, "original_features": base.values,
                        "progression_features": advanced.values,
                        "base_certificates": [asdict(c) for c in base.certificates],
                        "progression_certificate": asdict(advanced.progression) if advanced.progression else None,
                        "candidate_steps": advanced.candidate_steps})
                    total = sum(weights)
                    below = min(max(weights) - 1, 2 * total // 5)
                    below = max(1, below if below % 2 else below - 1)
                    targets = [sum(w for w in weights if rng.getrandbits(1)),
                               rng.randrange(3 * total // 10, 7 * total // 10 + 1),
                               below, rng.randrange(1, max(2, total // 10 + 1))]
                    started = perf_counter()
                    halves = independent_halves(weights)
                    truths = [independent_query(halves, target) for target in targets]
                    oracle_seconds = perf_counter() - started
                    del halves
                    for rule, target, mask in zip(CONFIG["targets"], targets, truths):
                        case_id = f"{list_id}-{rule}"
                        kernel = reduce_instance(weights, target)
                        target_base = extract(kernel.weights, FeatureConfig(**CONFIG["features"]))
                        target_advanced = extract_advanced(kernel.weights, FeatureConfig(**CONFIG["features"]),
                            max_steps=CONFIG["max_progression_steps"], base=target_base)
                        all_features = {"original": base, "progression": advanced,
                                        "target_original": target_base, "target_progression": target_advanced}
                        cap = CONFIG["budget_multiplier"] * input_length(weights, target)
                        case = {"case_id": case_id, "list_id": list_id, "family": family,
                                "n": n, "split": split, "target_rule": rule, "target": target,
                                "input_length": input_length(weights, target), "budget": cap,
                                "truth": "yes" if mask is not None else "no", "oracle_mask": mask,
                                "oracle_list_seconds": oracle_seconds, "kernel": asdict(kernel),
                                "features": {name: obj.values for name, obj in all_features.items()},
                                "feature_work": {name: obj.work for name, obj in all_features.items()},
                                "feature_seconds": {name: obj.seconds for name, obj in all_features.items()},
                                "conventional": conventional(weights, target),
                                "target_progression_certificate": (asdict(target_advanced.progression)
                                                                   if target_advanced.progression else None)}
                        cases.append(case)
                        policies = ["common"] + list(VARIANTS)
                        rng.shuffle(policies)
                        for policy in policies:
                            result = solve_policy(weights, target, kernel, cap,
                                features=all_features.get(policy),
                                advanced=policy in ("progression", "target_progression"),
                                target_aware=policy.startswith("target_"))
                            check(weights, target, mask is not None, result)
                            if result["work"] > cap and not result["extraction_exhausted"]:
                                raise AssertionError("solver work overrun")
                            runs.append({"case_id": case_id, "policy": policy, **result})
                    print(f"checked {list_id}: {len(lists)} lists, {len(cases)} cases", flush=True)
    for name, digest in protocol["source_hashes"].items():
        if sha(ROOT / name) != digest:
            raise AssertionError("source changed during generation")
    save_jsonl(output / "lists.jsonl", lists)
    save_jsonl(output / "cases.jsonl", cases)
    save_jsonl(output / "runs.jsonl", runs)
    summary = summary_for(lists, cases, runs)
    save_json(output / "summary.json", summary)
    artifacts = ("protocol.json", "lists.jsonl", "cases.jsonl", "runs.jsonl", "summary.json")
    save_json(output / "artifact_hashes.json", {name: sha(output / name) for name in artifacts})
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    generate(parser.parse_args().output)
