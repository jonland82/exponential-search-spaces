"""Freeze fitted models, generate fresh inputs, and evaluate exact completion.

Commands are separate: freeze precedes generation of any new evaluation list.
All source/model/config hashes are verified between stages. No model selection,
calibration or hyperparameter fitting uses the fresh evaluation labels.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from math import exp, gcd
from pathlib import Path
import platform
import random
import shutil
import sys
from time import perf_counter

import joblib
import numpy as np
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from advanced_features import extract_advanced, lift_witness, reduce_instance
from features import FeatureConfig, input_length
from fit_development import CONFIG as FIT_CONFIG, cluster_difference, matrix, metrics, read_jsonl
from run_development import conventional, full_core_query
from run_pilot import (CONFIG as PILOT_CONFIG, ROOT, check, independent_halves,
                       independent_query, portfolio, save_json, save_jsonl, sha,
                       weights_for)
from structural_subset_sum import Limits, solve, solve_bitset, solve_dfs, solve_mitm


HERE = Path(__file__).resolve().parent
DEVELOPMENT = HERE / "results" / "development_20261025"
TRAIN_FAMILIES = ("superincreasing", "coverage", "few_values", "small_support",
                  "interval_union", "progression", "random_wide")
PRIOR_HOLDOUT = ("near_equal", "filtered_modular")
NEW_FAMILIES = ("block_pairs", "two_scale", "two_progressions")
ARMS = ("five", "conventional", "hybrid")
CONFIG = {
    "version": 1, "seed": 710_251_026,
    "status": "locally frozen fresh evaluation; not externally registered preregistration",
    "sizes": [24, 32, 38], "fractions": [0, 0.25], "replicates": 2,
    "families": list(TRAIN_FAMILIES + PRIOR_HOLDOUT + NEW_FAMILIES),
    "scales": [1, (1 << 24) + 1],
    "targets": ["planted", "uniform_middle", "odd_below_largest", "uniform_low"],
    "features": {"distinct_values": 2, "support_cap": 128, "interval_cap": 8},
    "max_steps": 16, "budget_multiplier": 8,
    "per_case_seconds": 0.020, "timing_repeats": 3,
    "max_states": PILOT_CONFIG["max_states"], "max_bitset_bits": PILOT_CONFIG["max_bitset_bits"],
    "arms": list(ARMS), "primary_model": "logistic", "secondary_model": "forest",
    "forest": FIT_CONFIG["forest"], "logistic": FIT_CONFIG["logistic"],
    "model_seed": FIT_CONFIG["seed"],
    "calibration": "sigmoid on clipped raw logit, development calibration lists only",
    "training": "development split=train only; calibration split=calibration only",
    "primary_prediction": "same exact reference pipeline finishes within 8L work units; feature cost evaluated in pool policy",
    "primary_comparison": "hybrid logistic minus conventional logistic Brier, in_distribution/unscaled",
    "secondary_evaluations": "larger size, prior holdouts, new families, paired gcd-preserving scaling; forests secondary",
    "bootstrap": "1000 resamples of base weight lists, model fits fixed",
    "max_duplicate_proposals": 32,
    "pool_work_fractions": [0.2, 0.5], "pool_time_fractions": [0.2, 0.5],
    "pool_repeats": 3,
    "pool_policies": ["arrival", "random", "short_input", "distance_rule",
                      "five", "conventional", "hybrid"],
    "work_ranking": "predicted common completion probability divided by declared 8L allowance",
    "time_ranking": "predicted common work-completion probability; transfer to time is secondary",
    "pool_costs": "all exact prechecks, unresolved-input feature extraction, inference, sorting, core reuse and returned-witness checks",
    "work_accounting": "declared heterogeneous counters; counter-budget replay and live cooperative wall-clock are separate endpoints",
    "pool_reference": "same precheck-first pool semantics for all policies; no feature extraction on already-solved cases",
    "retry": "each residual instance attempted at most once; resource exhaustion never becomes NO",
}

PROTECTED = (
    "features.py", "advanced_features.py", "run_pilot.py", "run_development.py",
    "fit_development.py", "prospective_study.py", "priority_experiment.py",
    "test_prospective.py", "PROSPECTIVE_PROTOCOL.md",
)


def encode_signature(weights):
    import hashlib
    return hashlib.sha256(json.dumps(sorted(weights), separators=(",", ":")).encode()).hexdigest()


def conventional_cost(weights):
    # A declared scale for scans, sorting-independent summary statistics and logs.
    # It is not a CPU or uniform bit-operation count.
    return 12 * len(weights) + 80


def new_weights(family, n, replacements, rng):
    if family not in NEW_FAMILIES:
        return weights_for(family, n, replacements, rng)
    if family == "block_pairs":
        weights, total = [], 0
        for _ in range(n // 2):
            base = total + rng.randrange(1 << 20, 1 << 21)
            weights.extend((base, base + rng.randrange(1, 32)))
            total = sum(weights)
    elif family == "two_scale":
        weights = [rng.randrange(1, 65) for _ in range(n // 2)]
        weights += [rng.randrange(1 << 29, 1 << 30) for _ in range(n - len(weights))]
    else:
        a, b = rng.randrange(1 << 26, 1 << 27), rng.randrange(1 << 29, 1 << 30)
        h, j = rng.randrange(2, 18), rng.randrange(19, 37)
        weights = [a + h * i for i in range(n // 2)]
        weights += [b + j * i for i in range(n - len(weights))]
    for i in rng.sample(range(n), replacements):
        weights[i] = rng.randrange(1 << 29, 1 << 31)
    rng.shuffle(weights)
    return weights


def cohort_for(n, family, scale):
    if family in NEW_FAMILIES:
        base = "unseen_family"
    elif family in PRIOR_HOLDOUT:
        base = "prior_holdout"
    elif n == max(CONFIG["sizes"]):
        base = "larger_size"
    else:
        base = "in_distribution"
    return base + ("_scaled" if scale != 1 else "")


def prior_signatures():
    found = set()
    for relative in ("pilot_20261025/lists.jsonl", "development_20261025/lists.jsonl"):
        for row in read_jsonl(HERE / "results" / relative):
            found.add(encode_signature(row["weights"]))
    return sorted(found)


def data_hashes():
    hashes = json.loads((DEVELOPMENT / "artifact_hashes.json").read_text())
    for name, digest in hashes.items():
        if sha(DEVELOPMENT / name) != digest:
            raise AssertionError("development data changed")
    return hashes


def fit_bundles():
    cases = read_jsonl(DEVELOPMENT / "cases.jsonl")
    runs = read_jsonl(DEVELOPMENT / "runs.jsonl")
    common = {r["case_id"]: r for r in runs if r["policy"] == "common"}
    labels = np.array([int(common[c["case_id"]]["status"] != "unresolved") for c in cases])
    training = np.array([c["split"] == "train" for c in cases])
    calibration = np.array([c["split"] == "calibration" for c in cases])
    bundles = {}
    for arm in ARMS:
        feature_name = "target_progression" if arm == "five" else arm
        x = matrix(cases, feature_name)
        for kind in ("logistic", "forest"):
            if kind == "logistic":
                model = make_pipeline(StandardScaler(), LogisticRegression(
                    random_state=CONFIG["model_seed"], **CONFIG["logistic"]))
            else:
                model = RandomForestClassifier(random_state=CONFIG["model_seed"], **CONFIG["forest"])
            model.fit(x[training], labels[training])
            raw = np.clip(model.predict_proba(x[calibration])[:, 1], 1e-6, 1 - 1e-6)
            logits = np.log(raw / (1 - raw)).reshape(-1, 1)
            calibrator = LogisticRegression(C=1.0, max_iter=2000, random_state=CONFIG["model_seed"])
            calibrator.fit(logits, labels[calibration])
            bundles[f"{arm}:{kind}"] = {"model": model, "calibrator": calibrator, "dimensions": x.shape[1]}
    bundles["constant"] = float(labels[training].mean())
    return bundles


def infer(bundle, vectors, *, count_work=True):
    """Batch inference with measured library time and a declared counter charge."""
    if not vectors:
        return [], [], 0.0
    started = perf_counter()
    x = np.asarray(vectors, dtype=float)
    raw = bundle["model"].predict_proba(x)[:, 1]
    clipped = np.clip(raw, 1e-6, 1 - 1e-6)
    logits = np.log(clipped / (1 - clipped)).reshape(-1, 1)
    calibrated = bundle["calibrator"].predict_proba(logits)[:, 1]
    elapsed = perf_counter() - started
    if not count_work:
        return calibrated.tolist(), [], elapsed
    model = bundle["model"]
    if hasattr(model, "estimators_"):
        # Logging these decision paths is outside measured prediction time.
        # Each visited decision plus a per-tree averaging/leaf scale is charged.
        paths, _ = model.decision_path(x)
        work = (np.diff(paths.indptr) + 4 * len(model.estimators_) + 20).tolist()
    else:
        work = [6 * x.shape[1] + 20] * len(vectors)
    return calibrated.tolist(), work, elapsed


def freeze(output):
    if output.exists():
        raise FileExistsError("freeze requires a new study directory")
    hashes = data_hashes()
    paths = [HERE / name for name in PROTECTED]
    paths.append(ROOT / "Structural_Distance_Subset_Sum" / "structural_subset_sum.py")
    output.mkdir(parents=True)
    for path in paths:
        dest = output / "sources" / path.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
    bundles = fit_bundles()
    joblib.dump(bundles, output / "models.joblib")
    protocol = {"config": CONFIG, "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
                "python": sys.version, "platform": platform.platform(), "numpy": np.__version__,
                "sklearn": sklearn.__version__, "development_hashes": hashes,
                "model_sha256": sha(output / "models.joblib"),
                "source_hashes": {str(p.relative_to(ROOT)): sha(p) for p in paths},
                "prior_signatures": prior_signatures()}
    save_json(output / "protocol.json", protocol)
    (output / "protocol.sha256").write_text(sha(output / "protocol.json") + "\n")
    print(f"Frozen six fitted/calibrated models, sources and protocol at {output}", flush=True)


def verify(output):
    protocol = json.loads((output / "protocol.json").read_text())
    if sha(output / "protocol.json") != (output / "protocol.sha256").read_text().strip():
        raise AssertionError("protocol hash mismatch")
    if protocol["config"] != CONFIG or data_hashes() != protocol["development_hashes"]:
        raise AssertionError("configuration/development data changed after freeze")
    if sha(output / "models.joblib") != protocol["model_sha256"]:
        raise AssertionError("model hash mismatch")
    for name, digest in protocol["source_hashes"].items():
        if sha(ROOT / name) != digest or sha(output / "sources" / name) != digest:
            raise AssertionError(f"source changed after freeze: {name}")
    return protocol


def limited_portfolio(weights, target, cap, seconds=None):
    """Same work schedule as the development portfolio; optional shared deadline."""
    if seconds is None:
        return portfolio(weights, target, cap)
    started, used, attempts = perf_counter(), 0, []
    # All these kernels already passed exact target reductions, but retain the
    # development portfolio's filtered check and charge for an identical schedule.
    from run_pilot import filtered_answer
    status, witness, work = filtered_answer(weights, target, cap)
    used += work
    attempts.append({"method": "filtered_range_gcd", "status": status, "work": work})
    if status != "unresolved":
        return {"status": status, "witness": witness, "work": used,
                "seconds": perf_counter() - started, "attempts": attempts}
    methods = [("bitset", solve_bitset),
               ("core_enumerate", lambda w, t, **kw: solve(w, t, method="enumerate", **kw)),
               ("dfs", solve_dfs), ("mitm", solve_mitm)]
    for position, (name, method) in enumerate(methods):
        share = (cap - used) // (len(methods) - position)
        remaining_seconds = seconds - (perf_counter() - started)
        if share < 1 or remaining_seconds <= 0:
            continue
        result = method(weights, target, limits=Limits(
            max_work=share, max_states=CONFIG["max_states"], max_seconds=remaining_seconds,
            max_bitset_bits=CONFIG["max_bitset_bits"]))
        used += result.stats["work"]
        attempts.append({"method": name, "status": result.status,
                         "reason": result.reason, "work": result.stats["work"]})
        if result.status != "unresolved":
            return {"status": result.status, "witness": result.witness, "work": used,
                    "seconds": perf_counter() - started, "attempts": attempts}
    return {"status": "unresolved", "witness": None, "work": used,
            "seconds": perf_counter() - started, "attempts": attempts}


def reference(weights, target, kernel, cap, seconds=None):
    started = perf_counter()
    if kernel.work >= cap:
        return {"status": "unresolved", "witness": None, "work": kernel.work,
                "seconds": kernel.seconds, "attempts": []}
    if kernel.status != "unresolved":
        return {"status": kernel.status, "witness": kernel.witness, "work": kernel.work,
                "seconds": kernel.seconds, "attempts": []}
    remaining_seconds = None if seconds is None else seconds - kernel.seconds
    if remaining_seconds is not None and remaining_seconds <= 0:
        return {"status": "unresolved", "witness": None, "work": kernel.work,
                "seconds": kernel.seconds, "attempts": []}
    result = limited_portfolio(kernel.weights, kernel.target, cap - kernel.work, remaining_seconds)
    witness = result["witness"]
    if witness is not None:
        witness = lift_witness(kernel, witness)
    return {**result, "witness": witness, "work": result["work"] + kernel.work,
            "seconds": kernel.seconds + perf_counter() - started}


def feature_vectors(weights, target, kernel):
    started = perf_counter()
    ordinary = conventional(weights, target)
    ordinary_seconds = perf_counter() - started
    advanced = extract_advanced(kernel.weights, FeatureConfig(**CONFIG["features"]),
                                max_steps=CONFIG["max_steps"])
    vectors = {"five": list(advanced.values), "conventional": ordinary,
               "hybrid": list(advanced.values) + ordinary}
    work = {"five": advanced.work, "conventional": conventional_cost(weights),
            "hybrid": advanced.work + conventional_cost(weights)}
    times = {"five": advanced.seconds, "conventional": ordinary_seconds,
             "hybrid": advanced.seconds + ordinary_seconds}
    # Query only unresolved kernels, and allow enough logging work to determine
    # full-core outcomes. Pool policies pay this query charge before using it.
    reuse = ({"status": "unresolved", "witness": None, "work": 0, "attempts": []}
             if kernel.status != "unresolved" else
             full_core_query(advanced, True, kernel.target, 8 * input_length(weights, target)))
    if reuse["witness"] is not None:
        reuse["witness"] = lift_witness(kernel, reuse["witness"])
    return vectors, work, times, reuse


def generate(output):
    protocol = verify(output)
    if (output / "cases.jsonl").exists() or (output / "generation.started.json").exists():
        raise FileExistsError("generation cannot overwrite an existing/started stage")
    save_json(output / "generation.started.json", {"utc": datetime.now(timezone.utc).isoformat()})
    signatures = set(protocol["prior_signatures"])
    lists, cases, references, proposals = [], [], [], []
    bundles = joblib.load(output / "models.joblib")
    for n in CONFIG["sizes"]:
        for family in CONFIG["families"]:
            for fraction in CONFIG["fractions"]:
                for replicate in range(CONFIG["replicates"]):
                    base_id = f"n{n}-{family}-r{round(n*fraction)}-s{replicate}"
                    weights = None
                    for proposal in range(CONFIG["max_duplicate_proposals"]):
                        rng = random.Random(f"{CONFIG['seed']}:{base_id}:{proposal}")
                        candidate = new_weights(family, n, round(n * fraction), rng)
                        proposed = [encode_signature([w * scale for w in candidate]) for scale in CONFIG["scales"]]
                        accepted = all(sig not in signatures for sig in proposed)
                        proposals.append({"base_list_id": base_id, "proposal": proposal, "accepted": accepted})
                        if accepted:
                            weights = candidate
                            signatures.update(proposed)
                            break
                    if weights is None:
                        print(f"missing duplicate-free slot {base_id}", flush=True)
                        continue
                    total = sum(weights)
                    below = min(max(weights) - 1, 2 * total // 5)
                    below = max(1, below if below % 2 else below - 1)
                    targets = [sum(w for w in weights if rng.getrandbits(1)),
                               rng.randrange(3 * total // 10, 7 * total // 10 + 1), below,
                               rng.randrange(1, max(2, total // 10 + 1))]
                    oracle_started = perf_counter()
                    halves = independent_halves(weights)
                    truths = [independent_query(halves, target) for target in targets]
                    oracle_seconds = perf_counter() - oracle_started
                    del halves
                    for scale in CONFIG["scales"]:
                        scaled = [w * scale for w in weights]
                        list_id = f"{base_id}-scale{scale}"
                        cohort = cohort_for(n, family, scale)
                        lists.append({"list_id": list_id, "base_list_id": base_id, "family": family,
                            "n": n, "fraction": fraction, "replicate": replicate, "scale": scale,
                            "cohort": cohort, "weights": scaled})
                        for rule, target_base, truth_mask in zip(CONFIG["targets"], targets, truths):
                            target = target_base * scale
                            case_id = f"{list_id}-{rule}"
                            kernel = reduce_instance(scaled, target)
                            cap = CONFIG["budget_multiplier"] * input_length(scaled, target)
                            vectors, work, times, reuse = feature_vectors(scaled, target, kernel)
                            from dataclasses import asdict
                            case = {"case_id": case_id, "list_id": list_id, "base_list_id": base_id,
                                "n": n, "family": family, "scale": scale, "cohort": cohort,
                                "target_rule": rule, "target": target, "weights": scaled,
                                "budget": cap, "truth": "yes" if truth_mask is not None else "no",
                                "oracle_mask": truth_mask, "oracle_base_list_seconds": oracle_seconds,
                                "kernel": asdict(kernel), "vectors": vectors, "feature_work": work,
                                "feature_seconds": times, "reuse": reuse}
                            for arm in ARMS:
                                for kind in ("logistic", "forest"):
                                    score, inference_work, inference_seconds = infer(bundles[f"{arm}:{kind}"], [vectors[arm]])
                                    case.setdefault("predictions", {})[f"{arm}:{kind}"] = score[0]
                                    case.setdefault("inference_work", {})[f"{arm}:{kind}"] = inference_work[0]
                            check(scaled, target, truth_mask is not None, reuse)
                            cases.append(case)
                            unlimited = reference(scaled, target, kernel, cap)
                            check(scaled, target, truth_mask is not None, unlimited)
                            references.append({"case_id": case_id, "mode": "work", "repeat": 0, **unlimited})
                            for repeat in range(CONFIG["timing_repeats"]):
                                # Repeat preprocessing too; no oracle tables coexist with timing.
                                live_kernel = reduce_instance(scaled, target)
                                timed = reference(scaled, target, live_kernel, cap, CONFIG["per_case_seconds"])
                                check(scaled, target, truth_mask is not None, timed)
                                references.append({"case_id": case_id, "mode": "time", "repeat": repeat, **timed})
                    print(f"checked {base_id}: {len(lists)} encodings, {len(cases)} cases", flush=True)
    verify(output)
    save_jsonl(output / "lists.jsonl", lists)
    save_jsonl(output / "cases.jsonl", cases)
    save_jsonl(output / "references.jsonl", references)
    save_jsonl(output / "proposals.jsonl", proposals)
    artifacts = ("lists.jsonl", "cases.jsonl", "references.jsonl", "proposals.jsonl")
    save_json(output / "data_hashes.json", {name: sha(output / name) for name in artifacts})
    print(f"Completed fresh generation: {len(lists)} encoded lists, {len(cases)} cases", flush=True)


def analyze(output):
    verify(output)
    for name, digest in json.loads((output / "data_hashes.json").read_text()).items():
        if sha(output / name) != digest:
            raise AssertionError("fresh data hash mismatch")
    cases, refs = read_jsonl(output / "cases.jsonl"), read_jsonl(output / "references.jsonl")
    work_refs = {r["case_id"]: r for r in refs if r["mode"] == "work"}
    y = np.array([int(work_refs[c["case_id"]]["status"] != "unresolved") for c in cases])
    cohorts = sorted({c["cohort"] for c in cases})
    bundles = joblib.load(output / "models.joblib")
    scores = {name: np.array([c["predictions"][name] for c in cases])
              for name in cases[0]["predictions"]}
    scores["constant"] = np.full(len(cases), bundles["constant"])
    result = {"cases": len(cases), "encoded_lists": len({c["list_id"] for c in cases}),
              "base_lists": len({c["base_list_id"] for c in cases}),
              "completed_reference_answers_checked": sum(r["status"] != "unresolved" for r in refs),
              "mismatches": 0, "models": {}, "paired": {}}
    for name, probabilities in scores.items():
        result["models"][name] = {}
        for cohort in cohorts:
            mask = np.array([c["cohort"] == cohort for c in cases])
            unresolved = mask & np.array([c["kernel"]["status"] == "unresolved" for c in cases])
            result["models"][name][cohort] = {
                "all": metrics(y[mask], probabilities[mask]),
                "unresolved_kernel": metrics(y[unresolved], probabilities[unresolved])}
    # Resample base lists: scaled encodings and targets never become independent units.
    clustered = [{"list_id": c["base_list_id"], "split": c["cohort"]} for c in cases]
    for first, second in (("hybrid:logistic", "conventional:logistic"),
                          ("hybrid:forest", "conventional:forest"),
                          ("five:logistic", "conventional:logistic")):
        result["paired"][first + " minus " + second] = {
            cohort: paired_interval(clustered, y, scores[first], scores[second], cohort) for cohort in cohorts}
    save_json(output / "prediction_metrics.json", result)
    lines = ["# Fresh frozen prediction comparison", "", CONFIG["status"] + ".", "",
             "Logistic regression is the primary model; forests are prespecified secondary models. "
             "Brier scores concern the same 8L exact-reference completion event; lower is better. "
             "The practical pool experiment separately pays all model feature and inference costs.", "",
             "| Cohort | Cases | Five | Conventional | Combined | Combined minus conventional |",
             "|---|---:|---:|---:|---:|---:|"]
    for cohort in cohorts:
        values = [result["models"][f"{arm}:logistic"][cohort]["all"]["brier"] for arm in ARMS]
        diff = result["paired"]["hybrid:logistic minus conventional:logistic"][cohort]
        lines.append(f"| {cohort} | {result['models']['five:logistic'][cohort]['all']['n']} | "
                     + " | ".join(f"{v:.4f}" for v in values) + f" | {diff['difference']:+.4f} |")
    lines += ["", "This local freeze used development training and calibration lists only. "
              "All models and the protocol were hashed before these inputs were generated. "
              "Scaled pairs preserve mathematical answers and change encoding/solver behavior; "
              "they are not independent problems or a generic claim about arbitrary bit-length shifts. "
              "New-family and larger-size cohorts are reported separately. Bootstrap intervals "
              "resample base lists, holding the fitted models fixed. No asymptotic tractability claim follows."]
    (output / "PREDICTION_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    save_json(output / "prediction_hashes.json", {name: sha(output / name) for name in (
        "prediction_metrics.json", "PREDICTION_REPORT.md")})
    print((output / "PREDICTION_REPORT.md").read_text(), flush=True)


def paired_interval(cases, labels, first, second, cohort):
    groups = defaultdict(list)
    for i, case in enumerate(cases):
        if case["split"] == cohort:
            groups[case["list_id"]].append(i)
    blocks = list(groups.values())
    losses = np.square(first - labels) - np.square(second - labels)
    sums = np.array([losses[indices].sum() for indices in blocks])
    sizes = np.array([len(indices) for indices in blocks])
    rng = np.random.default_rng(CONFIG["seed"])
    draws = rng.integers(0, len(blocks), (1000, len(blocks)))
    sampled = sums[draws].sum(axis=1) / sizes[draws].sum(axis=1)
    return {"difference": float(sums.sum() / sizes.sum()),
            "list_bootstrap_95_percentile": np.quantile(sampled, [.025, .975]).tolist(),
            "base_lists": len(blocks), "conditional_on_models": True}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("freeze", "generate", "analyze"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    {"freeze": freeze, "generate": generate, "analyze": analyze}[args.stage](args.output)
