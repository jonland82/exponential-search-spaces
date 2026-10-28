"""Exploratory feature/label feasibility pilot, not a trained-model evaluation."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from math import gcd, sqrt
from pathlib import Path
import platform
import random
import shutil
from statistics import median
import sys
from time import perf_counter

from features import FEATURE_NAMES, FeatureConfig, extract, input_length

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "Structural_Distance_Subset_Sum"))
from structural_subset_sum import Limits, solve, solve_bitset, solve_dfs, solve_mitm


CONFIG = {
    "status": "exploratory feasibility pilot; no fitted model or prospective performance claim",
    "seed": 610_251_026,
    "sizes": [16, 24, 32],
    "replacement_fractions": [0, 0.125, 0.25],
    "replicates": 2,
    "families": ["superincreasing", "coverage", "few_values", "small_support",
                 "interval_union", "progression", "near_equal", "random_wide", "filtered_modular"],
    "targets": ["planted", "uniform_middle", "odd_below_largest"],
    "features": asdict(FeatureConfig()),
    "budget_multipliers": [8, 32],
    "budget": "multiplier * input_length(weights, target) instrumented work units",
    "portfolio": ["filtered_range_gcd", "bitset", "core_enumerate", "dfs", "mitm"],
    "schedule": "preprocess, then divide remaining work among remaining methods; carry unused work forward",
    "max_states": 32_768,
    "max_bitset_bits": 1_000_000,
    "timing": "one run per case, budget, and cost policy; descriptive only",
    "policies": ["without_features", "with_features"],
    "label": "portfolio completes under its budget and memory caps; not reachability",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_json(path, value):
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2)
        handle.write("\n")


def save_jsonl(path, rows):
    with path.open("x", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, separators=(",", ":")) + "\n")


def weights_for(family, n, replacements, rng):
    if family == "superincreasing":
        weights, total = [], 0
        for _ in range(n):
            value = total + rng.randrange(1 << 20, 1 << 21)
            weights.append(value)
            total += value
    elif family == "coverage":
        weights, total = [1], 1
        for _ in range(n - 1):
            value = rng.randrange(1, min(total + 1, 64) + 1)
            weights.append(value)
            total += value
    elif family == "few_values":
        a, b = rng.randrange(1 << 29, 1 << 30), rng.randrange(1 << 29, 1 << 30)
        weights = [a] * (n // 2) + [b] * (n - n // 2)
    elif family == "small_support":
        weights = [rng.randrange(1, 6) for _ in range(n)]
    elif family == "interval_union":
        base = rng.randrange(1 << 29, 1 << 30)
        weights = [1] * (n - 4) + [base] * 4
    elif family == "progression":
        start = rng.randrange(1 << 20, 1 << 21)
        step = rng.randrange(2, 19)
        weights = [start + step * i for i in range(n)]
    elif family == "near_equal":
        base = rng.randrange(1 << 29, 1 << 30)
        weights = [base + rng.randrange(17) for _ in range(n)]
    elif family == "random_wide":
        weights = [rng.randrange(1 << 29, 1 << 30) for _ in range(n)]
    elif family == "filtered_modular":
        weights = [2 * rng.randrange(1 << 28, 1 << 29) for _ in range(n - 1)]
        weights.append(sum(weights) + 1)
    else:
        raise ValueError(family)
    for i in rng.sample(range(n), replacements):
        weights[i] = rng.randrange(1 << 29, 1 << 31)
    rng.shuffle(weights)
    return weights


def independent_halves(weights):
    """Full binary-mask recurrence, independent of the measured MITM builder."""
    midpoint = len(weights) // 2
    out = []
    for start, stop in ((0, midpoint), (midpoint, len(weights))):
        totals = [0] * (1 << (stop - start))
        block = {0: 0}
        for mask in range(1, len(totals)):
            bit = mask & -mask
            totals[mask] = totals[mask ^ bit] + weights[start + bit.bit_length() - 1]
            block[totals[mask]] = mask << start
        out.append(block)
    return out


def independent_query(halves, target):
    for value, mask in halves[0].items():
        other = halves[1].get(target - value)
        if other is not None:
            return mask | other
    return None


def filtered_answer(weights, target, cap):
    """A target-dependent exact shortcut outside the five list features."""
    work, divisor, total = 0, 0, 0
    for weight in weights:
        if work == cap:
            return "unresolved", None, work
        work += 1
        if weight <= target:
            total += weight
            divisor = gcd(divisor, weight)
    if target == 0:
        return "yes", (), work
    if target < 0 or target > total or (divisor and target % divisor):
        return "no", None, work
    return "unresolved", None, work


def portfolio(weights, target, cap):
    start = perf_counter()
    attempts, used = [], 0
    status, witness, work = filtered_answer(weights, target, cap)
    attempts.append({"method": "filtered_range_gcd", "status": status, "work": work})
    used += work
    if status != "unresolved":
        return {"status": status, "witness": witness, "work": used,
                "seconds": perf_counter() - start, "attempts": attempts}
    methods = [
        ("bitset", solve_bitset),
        ("core_enumerate", lambda w, t, **kwargs: solve(w, t, method="enumerate", **kwargs)),
        ("dfs", solve_dfs), ("mitm", solve_mitm),
    ]
    for position, (name, method) in enumerate(methods):
        share = (cap - used) // (len(methods) - position)
        if share < 1:
            continue
        result = method(weights, target, limits=Limits(
            max_work=share, max_states=CONFIG["max_states"],
            max_bitset_bits=CONFIG["max_bitset_bits"]))
        used += result.stats["work"]
        attempts.append({"method": name, "status": result.status,
                         "reason": result.reason, "work": result.stats["work"],
                         "seconds": result.stats["total_seconds"]})
        if result.status != "unresolved":
            return {"status": result.status, "witness": result.witness, "work": used,
                    "seconds": perf_counter() - start, "attempts": attempts}
    return {"status": "unresolved", "witness": None, "work": used,
            "seconds": perf_counter() - start, "attempts": attempts}


def check(weights, target, truth, result):
    if result["status"] == "unresolved":
        if result["witness"] is not None:
            raise AssertionError("unresolved returned a witness")
        return
    if (result["status"] == "yes") != truth:
        raise AssertionError((weights, target, truth, result))
    witness = result["witness"]
    # The reused bitset method explicitly provides a decision without a witness.
    if result["status"] == "yes" and witness is not None:
        if (len(set(witness)) != len(witness) or
                any(not 0 <= i < len(weights) for i in witness) or
                sum(weights[i] for i in witness) != target):
            raise AssertionError("invalid indexed witness")


def correlation(xs, ys):
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    vx, vy = sum((x - mx) ** 2 for x in xs), sum((y - my) ** 2 for y in ys)
    if vx == 0 or vy == 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sqrt(vx * vy)


def summarize(lists, cases, runs):
    case_map = {c["case_id"]: c for c in cases}
    summary = {"lists": len(lists), "cases": len(cases), "portfolio_runs": len(runs),
               "completed_answers_checked": sum(r["status"] != "unresolved" for r in runs),
               "answer_mismatches": 0, "features": {}, "budgets": {},
               "unique_feature_vectors": len({tuple(row["features"]) for row in lists}),
               "duplicate_sorted_lists": len(lists) - len({tuple(sorted(row["weights"])) for row in lists})}
    for dim, name in enumerate(FEATURE_NAMES):
        values = [row["features"][dim] for row in lists]
        summary["features"][name] = {"min": min(values), "max": max(values),
            "median": median(values), "distinct_values": len(set(values)),
            "zero_distance_lists": values.count(0)}
    summary["feature_correlations"] = {
        a + ":" + b: correlation([r["features"][i] for r in lists], [r["features"][j] for r in lists])
        for i, a in enumerate(FEATURE_NAMES) for j, b in enumerate(FEATURE_NAMES) if i < j}
    summary["feature_extraction"] = {
        "median_ms": 1000 * median(r["feature_seconds"] for r in lists),
        "max_ms": 1000 * max(r["feature_seconds"] for r in lists),
        "median_work": median(r["feature_work"] for r in lists),
        "max_work": max(r["feature_work"] for r in lists)}
    for multiplier in CONFIG["budget_multipliers"]:
        for policy in CONFIG["policies"]:
            group = [r for r in runs if r["multiplier"] == multiplier and r["policy"] == policy]
            per_list, per_features = defaultdict(list), defaultdict(list)
            for r in group:
                c = case_map[r["case_id"]]
                per_list[c["list_id"]].append(r["solved"])
                per_features[tuple(c["features"])].append(r["solved"])
            # Empirical in-sample majority ceiling, not an estimate of test accuracy.
            ceiling = sum(max(sum(v), len(v) - sum(v)) for v in per_features.values()) / len(group)
            key = f"{multiplier}L:{policy}"
            summary["budgets"][key] = {
                "completed": sum(r["solved"] for r in group),
                "unresolved": sum(not r["solved"] for r in group),
                "mixed_outcome_lists": sum(len(set(v)) > 1 for v in per_list.values()),
                "empirical_feature_majority_ceiling": ceiling,
                "feature_cost_exceeds_budget": sum(r["feature_cost_exceeds_budget"] for r in group),
                "median_total_ms": 1000 * median(r["total_seconds"] for r in group),
                "families": {f: {"cases": sum(case_map[r["case_id"]]["family"] == f for r in group),
                                 "completed": sum(r["solved"] for r in group if case_map[r["case_id"]]["family"] == f)}
                             for f in CONFIG["families"]},
                "sizes": {str(n): {"cases": sum(case_map[r["case_id"]]["n"] == n for r in group),
                                   "completed": sum(r["solved"] for r in group if case_map[r["case_id"]]["n"] == n)}
                          for n in CONFIG["sizes"]},
            }
        without = {r["case_id"]: r for r in runs if r["multiplier"] == multiplier and r["policy"] == "without_features"}
        with_features = [r for r in runs if r["multiplier"] == multiplier and r["policy"] == "with_features"]
        summary["budgets"][f"{multiplier}L:cost_comparison"] = {
            "lost_completions": sum(without[r["case_id"]]["solved"] and not r["solved"] for r in with_features),
            "gained_completions": sum(not without[r["case_id"]]["solved"] and r["solved"] for r in with_features),
            "note": "Same solver schedule, no learned policy; allocation changes can affect completion."}
    return summary


def report(summary):
    lines = ["# Paper VI feasibility pilot", "", CONFIG["status"] + ".", "",
             f"{summary['lists']} weight lists, {summary['cases']} targets, "
             f"{summary['portfolio_runs']} portfolio runs. "
             f"{summary['completed_answers_checked']} completed decisions independently checked; "
             "zero disagreements. Every returned witness checked against original indices.", "",
             "## Five features", "", "| Feature | Min | Median | Max | Zero-distance lists |",
             "|---|---:|---:|---:|---:|"]
    for name, row in summary["features"].items():
        lines.append(f"| {name} | {row['min']} | {row['median']} | {row['max']} | {row['zero_distance_lists']} |")
    lines += ["", f"Unique feature vectors: {summary['unique_feature_vectors']}. "
              f"Duplicate sorted lists: {summary['duplicate_sorted_lists']}.", "",
              "## Budget feasibility", "",
              "L is the documented self-delimiting input-length proxy. Work counters include "
              "a conservative feature-extraction charge and the existing solvers' counters; "
              "they are not equal-cost bit operations. A separate state cap and bitset width cap apply.", "",
              "| Budget / policy | Completed | Unresolved | Lists with target-dependent outcomes |",
              "|---|---:|---:|---:|"]
    for key, row in summary["budgets"].items():
        if "completed" in row:
            lines.append(f"| {key} | {row['completed']} | {row['unresolved']} | {row['mixed_outcome_lists']} |")
    lines += ["", "## Interpretation boundary", "",
              "No model has been trained. The feature majority ceiling is an in-sample "
              "descriptive statistic, not a held-out accuracy result. Target-blind features "
              "can estimate an average over targets but cannot distinguish targets on the same list. "
              "All families are synthetic, the seed count is small, and timings are single-run measurements.", "",
              "The with-features policy prepays extraction separately for every target. "
              "The without-features policy uses the identical schedule with no extraction charge. "
              "There is no learned policy in this comparison. Extraction is completed offline even "
              "when its work charge exceeds the per-case budget, in which case no solver runs.", "",
              "Full inputs, oracle witnesses, certificates, attempts, work counts, timings, "
              "source snapshots and hashes are retained beside this report."]
    return "\n".join(lines) + "\n"


def run(output):
    if output.exists():
        raise FileExistsError("pilot requires a fresh output directory")
    paths = [HERE / name for name in ("features.py", "run_pilot.py", "test_features.py", "test_pilot.py")]
    paths.append(ROOT / "Structural_Distance_Subset_Sum" / "structural_subset_sum.py")
    output.mkdir(parents=True)
    for path in paths:
        destination = output / "sources" / path.relative_to(ROOT)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
    protocol = {"config": CONFIG, "recorded_before_generation_utc": datetime.now(timezone.utc).isoformat(),
                "python": sys.version, "platform": platform.platform(),
                "source_hashes": {str(p.relative_to(ROOT)): sha(p) for p in paths}}
    save_json(output / "protocol.json", protocol)
    (output / "protocol.sha256").write_text(sha(output / "protocol.json") + "\n", encoding="utf-8")
    rng = random.Random(CONFIG["seed"])
    lists, cases, runs = [], [], []
    for n in CONFIG["sizes"]:
        for family in CONFIG["families"]:
            for fraction in CONFIG["replacement_fractions"]:
                for replicate in range(CONFIG["replicates"]):
                    weights = weights_for(family, n, round(n * fraction), rng)
                    list_id = f"n{n}-{family}-r{round(n * fraction)}-s{replicate}"
                    features = extract(weights, FeatureConfig(**CONFIG["features"]))
                    lists.append({"list_id": list_id, "family": family, "n": n,
                        "replacements": round(n * fraction), "replicate": replicate,
                        "weights": weights, "features": features.values,
                        "divisor": features.divisor, "feature_work": features.work,
                        "feature_seconds": features.seconds,
                        "certificates": [asdict(c) for c in features.certificates]})
                    total = sum(weights)
                    below = min(max(weights) - 1, (2 * total) // 5)
                    below = max(1, below if below % 2 else below - 1)
                    targets = [sum(w for w in weights if rng.getrandbits(1)),
                               rng.randrange((3 * total) // 10, (7 * total) // 10 + 1), below]
                    oracle_started = perf_counter()
                    halves = independent_halves(weights)
                    truth_records = []
                    for rule, target in zip(CONFIG["targets"], targets):
                        mask = independent_query(halves, target)
                        truth_records.append((rule, target, mask))
                    oracle_seconds = perf_counter() - oracle_started
                    del halves
                    for rule, target, mask in truth_records:
                        case_id = f"{list_id}-{rule}"
                        length = input_length(weights, target)
                        cases.append({"case_id": case_id, "list_id": list_id, "n": n,
                            "family": family, "target_rule": rule, "target": target,
                            "input_length": length, "features": features.values,
                            "truth": "yes" if mask is not None else "no",
                            "oracle_witness_mask": mask, "oracle_list_seconds": oracle_seconds})
                        for multiplier in CONFIG["budget_multipliers"]:
                            budget = multiplier * length
                            policies = list(CONFIG["policies"])
                            rng.shuffle(policies)
                            for policy in policies:
                                charge = features.work if policy == "with_features" else 0
                                if charge >= budget:
                                    result = {"status": "unresolved", "witness": None,
                                              "work": 0, "seconds": 0.0, "attempts": []}
                                else:
                                    result = portfolio(weights, target, budget - charge)
                                check(weights, target, mask is not None, result)
                                runs.append({"case_id": case_id, "multiplier": multiplier,
                                    "policy": policy, "budget": budget, "feature_charge": charge,
                                    "feature_cost_exceeds_budget": charge > budget,
                                    "solved": result["status"] != "unresolved",
                                    "total_work": charge + result["work"],
                                    "total_seconds": result["seconds"] + (features.seconds if charge else 0),
                                    **result})
                    print(f"checked {list_id}: {len(lists)} lists, {len(runs)} runs", flush=True)
    # Fail if code drifted during execution; snapshots remain the source of record.
    for name, digest in protocol["source_hashes"].items():
        if sha(ROOT / name) != digest:
            raise RuntimeError(f"source changed during pilot: {name}")
    save_jsonl(output / "lists.jsonl", lists)
    save_jsonl(output / "cases.jsonl", cases)
    save_jsonl(output / "runs.jsonl", runs)
    summary = summarize(lists, cases, runs)
    save_json(output / "summary.json", summary)
    (output / "REPORT.md").write_text(report(summary), encoding="utf-8")
    artifacts = ["protocol.json", "lists.jsonl", "cases.jsonl", "runs.jsonl", "summary.json", "REPORT.md"]
    save_json(output / "artifact_hashes.json", {name: sha(output / name) for name in artifacts})
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
