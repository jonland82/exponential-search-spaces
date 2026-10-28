"""Separate frozen logistic follow-up: prototypes and structural interactions."""
from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import random
import shutil
from statistics import median
import sys

import joblib
import numpy as np
import sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from advanced_features import reduce_instance
from features import input_length
from fit_development import matrix, read_jsonl
from geometric_models import ARMS, INTERACTIONS, GeometricModel, PrototypeGeometry, design
from neighbor_experiment import (calibrated_bundle, evaluation_masks, normalized_signature,
    pool_run, probabilities, score, validate_row)
from priority_experiment import aggregate
from prospective_study import (CONFIG as OLD_CONFIG, DEVELOPMENT, cohort_for,
    feature_vectors, new_weights, reference, verify as verify_old)
from run_pilot import ROOT, check, independent_halves, independent_query, save_json, save_jsonl, sha


HERE = Path(__file__).resolve().parent
OLD = HERE / "results/prospective_20261025"
CONFIG = dict(seed=740281026, arms=list(ARMS), prototypes_per_class=3,
    kmeans=dict(random_state=740281026, n_init=10, max_iter=300, algorithm="lloyd"),
    interactions=[list(pair) for pair in INTERACTIONS],
    sizes=[24, 32, 38], families=OLD_CONFIG["families"], fractions=[0, .25], replicates=2,
    scales=[1, (1 << 24) + 1], targets=OLD_CONFIG["targets"],
    logistic=dict(C=1., max_iter=2000, random_state=630251026),
    fractions_pool=[.2, .5], repeats=3, pool_policies=["arrival", "distance_rule", *ARMS],
    bootstrap_draws=1000, primary="fresh unscaled Brier(combined) minus Brier(baseline)",
    status="separate local pre-generation freeze; previous evidence unchanged")


def development_data():
    cases = read_jsonl(DEVELOPMENT / "cases.jsonl")
    common = {r["case_id"]: r for r in read_jsonl(DEVELOPMENT / "runs.jsonl") if r["policy"] == "common"}
    x = matrix(cases, "hybrid")
    y = np.array([int(common[c["case_id"]]["status"] != "unresolved") for c in cases])
    groups = np.array([c["list_id"] for c in cases])
    train = np.array([c["split"] == "train" for c in cases])
    calibration = np.array([c["split"] == "calibration" for c in cases])
    assert not set(groups[train]) & set(groups[calibration])
    return cases, x, y, groups, train, calibration


def feature_names(arm):
    names = ["d_superincreasing", "d_coverage", "d_values", "d_support", "d_representation"]
    names += ["n", "input_length", "log2_total_plus_one", "log2_max_plus_one",
        "log2_min_plus_one", "distinct_fraction", "coefficient_of_variation",
        "target_fraction", "complement_min_target_fraction", "density_n_over_log2_max_plus_one"]
    if arm in ("prototypes", "combined"):
        names += ["prototype_distance_unresolved", "prototype_distance_completed"]
    if arm in ("interactions", "combined"):
        names += [f"standardized_d{i}_times_d{j}" for i, j in INTERACTIONS]
    return names


def freeze(output):
    if output.exists():
        raise FileExistsError("use a fresh output directory")
    verify_old(OLD)
    cases, x, y, groups, train, calibration = development_data()
    geometry = PrototypeGeometry(x[train], y[train], groups[train],
        prototypes=CONFIG["prototypes_per_class"], seed=CONFIG["seed"])
    out_of_list = geometry.class_distances(x[train], groups[train])
    bundles, training = {}, {}
    with threadpool_limits(limits=1):
        for arm in ARMS:
            tx = design(x[train], geometry, arm, distances=out_of_list)
            fitted = make_pipeline(StandardScaler(), LogisticRegression(**CONFIG["logistic"])).fit(tx, y[train])
            # Keep baseline's original direct adapter to avoid geometry overhead.
            model = fitted if arm == "baseline" else GeometricModel(geometry, arm, fitted)
            bundles[arm] = calibrated_bundle(model, x[calibration], y[calibration], tx.shape[1])
            training[arm] = tx
    original = joblib.load(OLD / "models.joblib")["hybrid:logistic"]
    np.testing.assert_allclose(probabilities(bundles["baseline"], x),
        probabilities(original, x), rtol=0, atol=1e-12)
    # Snapshot every prior list file, including the nearest-neighbor follow-up.
    prior_files = sorted((HERE / "results").glob("*/lists.jsonl"))
    signatures = sorted({normalized_signature(r["weights"])
        for path in prior_files for r in read_jsonl(path)})
    protected = [HERE / name for name in ("geometric_models.py", "geometric_experiment.py",
        "test_geometric.py", "validate_geometric.py", "GEOMETRIC_PROTOCOL.md",
        "neighbor_experiment.py", "neighbor_models.py")]
    protected += [ROOT / name for name in json.loads((OLD / "protocol.json").read_text())["source_hashes"]]
    protected = list(dict.fromkeys(protected))
    output.mkdir(parents=True)
    for source in protected:
        destination = output / "sources" / source.relative_to(ROOT)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    joblib.dump(dict(bank=geometry, bundles=bundles, constant=float(y[train].mean())), output / "models.joblib")
    save_jsonl(output / "training_features.jsonl", [dict(case_id=c["case_id"], list_id=c["list_id"],
        label=int(label), designs={arm:training[arm][i].tolist() for arm in ARMS})
        for i, (c, label) in enumerate(zip(np.array(cases, dtype=object)[train], y[train]))])
    save_json(output / "feature_schema.json", {arm:feature_names(arm) for arm in ARMS})
    inputs = [*prior_files, DEVELOPMENT / "cases.jsonl", DEVELOPMENT / "runs.jsonl", OLD / "models.joblib"]
    protocol = dict(config=CONFIG, frozen_at_utc=datetime.now(timezone.utc).isoformat(),
        source_hashes={str(p.relative_to(ROOT)):sha(p) for p in protected},
        input_hashes={str(p.relative_to(ROOT)):sha(p) for p in inputs},
        model_sha256=sha(output / "models.joblib"),
        training_features_sha256=sha(output / "training_features.jsonl"),
        feature_schema_sha256=sha(output / "feature_schema.json"),
        prior_signatures=signatures, training_lists=sorted(set(groups[train])),
        calibration_lists=sorted(set(groups[calibration])), training_cases=int(train.sum()),
        training_unresolved_cases=int((1-y[train]).sum()), python=sys.version,
        sklearn=sklearn.__version__, numpy=np.__version__, platform=platform.platform())
    save_json(output / "protocol.json", protocol)
    (output / "protocol.sha256").write_text(sha(output / "protocol.json") + "\n")
    print(f"FROZEN: {len(bundles)} logistic arms, 15/17/25/27 features; {len(signatures)} prior normalized lists excluded", flush=True)


def verify(output):
    protocol = json.loads((output / "protocol.json").read_text())
    assert sha(output / "protocol.json") == (output / "protocol.sha256").read_text().strip()
    assert protocol["config"] == CONFIG
    for filename, key in (("models.joblib", "model_sha256"),
                          ("training_features.jsonl", "training_features_sha256"),
                          ("feature_schema.json", "feature_schema_sha256")):
        assert sha(output / filename) == protocol[key], filename
    for name, digest in protocol["source_hashes"].items():
        assert sha(ROOT / name) == sha(output / "sources" / name) == digest, name
    for name, digest in protocol["input_hashes"].items():
        assert sha(ROOT / name) == digest, name
    return protocol


def save_hashes(output, manifest, names):
    save_json(output / manifest, {name:sha(output / name) for name in names})


def check_hashes(output, manifest):
    for name, digest in json.loads((output / manifest).read_text()).items():
        assert sha(output / name) == digest, name


def generate(output):
    protocol = verify(output)
    if (output / "generation.started.json").exists():
        raise FileExistsError("generation already started; preserve this experiment")
    save_json(output / "generation.started.json", dict(utc=datetime.now(timezone.utc).isoformat()))
    signatures = set(protocol["prior_signatures"])
    lists, cases, references, proposals = [], [], [], []
    for n in CONFIG["sizes"]:
        for family in CONFIG["families"]:
            for fraction in CONFIG["fractions"]:
                for replicate in range(CONFIG["replicates"]):
                    base = f"geometric-n{n}-{family}-r{round(n*fraction)}-s{replicate}"
                    for proposal in range(32):
                        rng = random.Random(f'{CONFIG["seed"]}:{base}:{proposal}')
                        weights = new_weights(family, n, round(n*fraction), rng)
                        signature = normalized_signature(weights)
                        accepted = signature not in signatures
                        proposals.append(dict(base_list_id=base, proposal=proposal, accepted=accepted))
                        if accepted:
                            signatures.add(signature)
                            break
                    else:
                        raise RuntimeError(f"No nonoverlapping input for {base}")
                    total = sum(weights)
                    below = max(1, min(max(weights)-1, 2*total//5))
                    below = below if below % 2 else max(1, below-1)
                    targets = [sum(w for w in weights if rng.getrandbits(1)),
                        rng.randrange(3*total//10, 7*total//10+1), below,
                        rng.randrange(1, max(2, total//10+1))]
                    halves = independent_halves(weights)
                    truths = [independent_query(halves, target) for target in targets]
                    del halves
                    for scale in CONFIG["scales"]:
                        scaled = [w*scale for w in weights]
                        list_id = f"{base}-scale{scale}"
                        cohort = cohort_for(n, family, scale)
                        lists.append(dict(list_id=list_id, base_list_id=base, n=n, family=family,
                            fraction=fraction, replicate=replicate, scale=scale, cohort=cohort, weights=scaled))
                        for rule, target, mask in zip(CONFIG["targets"], targets, truths):
                            target *= scale
                            kernel = reduce_instance(scaled, target)
                            budget = 8*input_length(scaled, target)
                            vectors, work, seconds, reuse = feature_vectors(scaled, target, kernel)
                            case = dict(case_id=f"{list_id}-{rule}", list_id=list_id, base_list_id=base,
                                n=n, family=family, scale=scale, cohort=cohort, target_rule=rule,
                                weights=scaled, target=target, budget=budget,
                                truth="yes" if mask is not None else "no", oracle_mask=mask,
                                kernel=asdict(kernel), vectors=vectors, feature_work=work,
                                feature_seconds=seconds, reuse=reuse)
                            result = reference(scaled, target, kernel, budget)
                            check(scaled, target, mask is not None, result)
                            check(scaled, target, mask is not None, reuse)
                            cases.append(case)
                            references.append(dict(case_id=case["case_id"], **result))
                    print(f"generated {base}: {len(cases)} cases", flush=True)
    verify(output)
    names = ("lists.jsonl", "cases.jsonl", "references.jsonl", "proposals.jsonl")
    for name, rows in zip(names, (lists, cases, references, proposals)):
        save_jsonl(output / name, rows)
    save_hashes(output, "data_hashes.json", names)


def bootstrap(cases, y, prediction, baseline):
    groups = defaultdict(list)
    for i, case in enumerate(cases):
        groups[case["base_list_id"]].append(i)
    loss = (prediction-y)**2 - (baseline-y)**2
    sums = np.array([loss[ids].sum() for ids in groups.values()])
    counts = np.array([len(ids) for ids in groups.values()])
    draws = np.random.default_rng(CONFIG["seed"]).integers(
        0, len(groups), (CONFIG["bootstrap_draws"], len(groups)))
    delta = sums[draws].sum(axis=1) / counts[draws].sum(axis=1)
    return dict(difference=float(loss.mean()),
        list_bootstrap_95_percentile=np.quantile(delta, [.025, .975]).tolist(),
        base_lists=len(groups), conditional_on_fitted_models=True)


def analyze_sample(cases, references, saved):
    refs = {r["case_id"]:r for r in references}
    y = np.array([int(refs[c["case_id"]]["status"] != "unresolved") for c in cases])
    x = np.array([c["vectors"]["hybrid"] for c in cases])
    distances = saved["bank"].class_distances(x)
    products = saved["bank"].interaction_values(x)
    scores = {arm:probabilities(bundle, x) for arm, bundle in saved["bundles"].items()}
    scores.update(constant_prior=np.full(len(cases), saved["constant"]), always_easy=np.ones(len(cases)))
    records = [dict(case_id=c["case_id"], base_list_id=c["base_list_id"], label=int(y[i]),
        prototype_distances=distances[i].tolist(), interactions=products[i].tolist(),
        probabilities={arm:float(p[i]) for arm, p in scores.items()}) for i, c in enumerate(cases)]
    result = dict(models={}, paired={}, counts=dict(cases=len(cases),
        base_lists=len({c["base_list_id"] for c in cases}), completed=int(y.sum()), unresolved=int((1-y).sum())))
    for name, mask in evaluation_masks(cases).items():
        subcases = [c for c, keep in zip(cases, mask) if keep]
        kernel = mask & np.array([c["kernel"]["status"] == "unresolved" for c in cases])
        reuse = kernel & np.array([c["reuse"]["status"] == "unresolved" for c in cases])
        result["models"][name] = {arm:dict(all=score(y[mask], p[mask]),
            unresolved_kernel=score(y[kernel], p[kernel]), unresolved_after_reuse=score(y[reuse], p[reuse]))
            for arm, p in scores.items()}
        result["paired"][name] = {arm:bootstrap(subcases, y[mask], p[mask], scores["baseline"][mask])
            for arm, p in scores.items() if arm != "baseline"}
    return result, records


def prediction_report(result):
    lines = ["# New geometric features: calibrated logistic regression", "",
        "Fresh inputs generated after freezing all four models. Completion means the fixed exact portfolio finishes within 8L, not reachability or intrinsic hardness. Training-list-only geometry; entire-own-list exclusions for training prototypes; disjoint sigmoid calibration. See GEOMETRIC_PROTOCOL.md and feature_schema.json.", "",
        "| Model | Features | Accuracy | Hard precision | Hard recall | Brier (lower better) |",
        "|---|---:|---:|---:|---:|---:|"]
    for arm in ARMS:
        row = result["models"]["unscaled"][arm]["all"]
        lines.append(f'| {arm} | {len(feature_names(arm))} | {row["accuracy_at_half"]:.3%} | {row["hard_precision"]:.3%} | {row["hard_recall"]:.3%} | {row["brier"]:.5f} |')
    lines += ["", "## Combined versus baseline by cohort", "",
        "| Cohort | Cases | Baseline Brier | Combined Brier | Difference [conditional 95% interval] |",
        "|---|---:|---:|---:|---|"]
    for name, models in result["models"].items():
        difference = result["paired"][name]["combined"]
        lo, hi = difference["list_bootstrap_95_percentile"]
        base, combined = models["baseline"]["all"], models["combined"]["all"]
        lines.append(f'| {name} | {base["n"]} | {base["brier"]:.5f} | {combined["brier"]:.5f} | {difference["difference"]:+.5f} [{lo:+.5f}, {hi:+.5f}] |')
    lines += ["", "Primary endpoint is combined-minus-baseline Brier on fresh unscaled cases; negative favors the new features. All 1,000 bootstrap draws resample base lists. Intervals condition on these fixed fitted models, not retraining. Other arms and cohorts are secondary; no multiplicity-adjusted claims. Full subgroup/shortcut metrics, confusion matrices, probabilities and raw added features are saved. Paid prioritization is separate from prediction quality and from branch-level checking."]
    return "\n".join(lines) + "\n"


def analyze(output):
    verify(output)
    check_hashes(output, "data_hashes.json")
    saved = joblib.load(output / "models.joblib")
    result, records = analyze_sample(read_jsonl(output / "cases.jsonl"), read_jsonl(output / "references.jsonl"), saved)
    save_json(output / "prediction_metrics.json", result)
    save_jsonl(output / "predictions.jsonl", records)
    (output / "PREDICTION_REPORT.md").write_text(prediction_report(result), encoding="utf-8")
    save_hashes(output, "prediction_hashes.json", ("prediction_metrics.json", "predictions.jsonl", "PREDICTION_REPORT.md"))
    print(prediction_report(result), flush=True)


def priority_report(rows):
    lines = ["# Paid geometric-feature prioritization", "",
        "All online feature, prototype-distance, interaction, inference, sorting, exact-core reuse, solver and witness costs are charged. These whole-input pools are not the earlier branch-checking experiment. Totals sum independently budgeted cohorts per repeat, then take the median and range of three repeats.", "",
        "| Mode | Budget fraction | Policy | Median completions [range] | Planning exhaustions / runs |",
        "|---|---:|---|---:|---:|"]
    for mode in ("work", "time"):
        for fraction in CONFIG["fractions_pool"]:
            for arm in CONFIG["pool_policies"]:
                group = [r for r in rows if (r["mode"], r["fraction"], r["policy"]) == (mode, fraction, arm)]
                totals = [sum(r["solved"] for r in group if r["repeat"] == i) for i in range(CONFIG["repeats"])]
                exhausted = sum(r["exhausted_phase"] in ("features", "inference", "sorting", "core_queries") for r in group)
                lines.append(f'| {mode} | {fraction} | {arm} | {median(totals)} [{min(totals)}, {max(totals)}] | {exhausted} / {len(group)} |')
    lines += ["", "Work units are heterogeneous declared counters, not CPU/bit operations. Time results include cooperative deadlines and exclude late answers. Timing ranges are descriptive; repeats and scaled encodings are dependent. Offline training/model loading is excluded. No prediction certifies NO. Per-cohort metrics and full phase/attempt traces are preserved; do not infer general speedups from an isolated timing difference."]
    return "\n".join(lines) + "\n"


def priorities(output):
    verify(output)
    check_hashes(output, "data_hashes.json")
    check_hashes(output, "prediction_hashes.json")
    saved = joblib.load(output / "models.joblib")
    cases = read_jsonl(output / "cases.jsonl")
    refs = {r["case_id"]:r for r in read_jsonl(output / "references.jsonl")}
    predictions = {r["case_id"]:r for r in read_jsonl(output / "predictions.jsonl")}
    groups = defaultdict(list)
    for case in cases:
        groups[case["cohort"]].append(case)
    rows = []
    save_json(output / "priority.started.json", dict(utc=datetime.now(timezone.utc).isoformat()))
    with (output / "priority_runs.jsonl").open("x", encoding="utf-8") as handle:
        for mode in ("work", "time"):
            for cohort, pool in sorted(groups.items()):
                for fraction in CONFIG["fractions_pool"]:
                    for repeat in range(CONFIG["repeats"]):
                        arms = CONFIG["pool_policies"].copy()
                        random.Random(f'{CONFIG["seed"]}:{mode}:{cohort}:{fraction}:{repeat}').shuffle(arms)
                        for arm in arms:
                            row = pool_run(pool, refs, saved, predictions, arm, mode, fraction, repeat)
                            validate_row(row, pool, refs)
                            rows.append(row)
                            handle.write(json.dumps(row, separators=(",", ":")) + "\n")
                            handle.flush()
                        print(f"paid pools: {mode} {cohort} fraction={fraction} repeat={repeat}", flush=True)
    verify(output)
    save_json(output / "priority_summary.json", aggregate(rows))
    (output / "PRIORITY_REPORT.md").write_text(priority_report(rows), encoding="utf-8")
    save_hashes(output, "priority_hashes.json", ("priority_runs.jsonl", "priority_summary.json", "PRIORITY_REPORT.md"))
    print(priority_report(rows), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("freeze", "generate", "analyze", "priorities"))
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()
    globals()[arguments.stage](arguments.output)
