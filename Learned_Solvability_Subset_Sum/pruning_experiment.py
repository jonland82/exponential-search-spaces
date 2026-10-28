"""Frozen top-five/top-ten logistic feature-pruning follow-up."""
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
from fit_development import read_jsonl
from geometric_experiment import (CONFIG as GEO_CONFIG, analyze_sample as geometric_analysis,
    bootstrap, check_hashes, development_data, feature_names, save_hashes, verify as verify_geometric)
from neighbor_experiment import calibrated_bundle, evaluation_masks, normalized_signature, pool_run, probabilities, validate_row
from priority_experiment import aggregate
from prospective_study import cohort_for, feature_vectors, new_weights, reference
from pruning_models import ARMS, LOGISTIC, PrunedModel, PruningGeometry, select_features
from run_pilot import ROOT, check, independent_halves, independent_query, save_json, save_jsonl, sha


HERE = Path(__file__).resolve().parent
PREVIOUS = HERE / "results/geometric_20261028"
CONFIG = dict(seed=750281026, bootstrap_seed=740281026, arms=list(ARMS),
    sizes=GEO_CONFIG["sizes"], families=GEO_CONFIG["families"], fractions=GEO_CONFIG["fractions"],
    replicates=GEO_CONFIG["replicates"], scales=GEO_CONFIG["scales"], targets=GEO_CONFIG["targets"],
    logistic=LOGISTIC, selection="one-at-a-time standardized-coefficient RFE, training rows only",
    counts=[5, 10], candidate_count=27, fractions_pool=[.2, .5], repeats=3,
    pool_policies=["arrival", "distance_rule", *ARMS], bootstrap_draws=1000,
    co_primary=["unscaled Brier(top5)-Brier(baseline)", "unscaled Brier(top10)-Brier(baseline)"],
    status="new training-only pruning freeze; previous evidence preserved")


def freeze(output):
    if output.exists():
        raise FileExistsError("use a fresh output directory")
    previous_protocol = verify_geometric(PREVIOUS)
    for manifest in ("data_hashes.json", "prediction_hashes.json", "priority_hashes.json"):
        check_hashes(PREVIOUS, manifest)
    validation = json.loads((PREVIOUS / "VALIDATION.json").read_text())
    assert validation["status"] == "passed" and validation["auditor_sha256"] == sha(HERE / "audit_geometric.py")
    prior = joblib.load(PREVIOUS / "models.joblib")
    development, x, y, groups, train, calibration = development_data()
    previous_training = read_jsonl(PREVIOUS / "training_features.jsonl")
    assert [r["case_id"] for r in previous_training] == [c["case_id"] for c, keep in zip(development, train) if keep]
    tx = np.array([r["designs"]["combined"] for r in previous_training])
    np.testing.assert_array_equal(y[train], [r["label"] for r in previous_training])
    selection = select_features(tx, y[train])
    bank = PruningGeometry(prior["bank"], selection["selected"])
    names = feature_names("combined")
    selection["candidate_names"] = names
    selection["selected_names"] = {arm:[names[i] for i in columns] for arm, columns in bank.selected.items()}
    selection["base_dependencies"] = {arm:bank.dependencies(arm) for arm in bank.selected}
    bundles = {arm:prior["bundles"][arm] for arm in ("baseline", "combined")}
    with threadpool_limits(limits=1):
        for arm, columns in bank.selected.items():
            fitted = make_pipeline(StandardScaler(), LogisticRegression(**LOGISTIC)).fit(tx[:, columns], y[train])
            bundles[arm] = calibrated_bundle(PrunedModel(bank, arm, fitted), x[calibration], y[calibration], len(columns))
    prior_files = sorted((HERE / "results").glob("*/lists.jsonl"))
    signatures = sorted({normalized_signature(r["weights"]) for p in prior_files for r in read_jsonl(p)})
    protected = [HERE / name for name in ("pruning_models.py", "pruning_experiment.py",
        "test_pruning.py", "audit_pruning.py", "PRUNING_PROTOCOL.md", "audit_geometric.py")]
    protected += [ROOT / name for name in previous_protocol["source_hashes"]]
    protected = list(dict.fromkeys(protected))
    inputs = [*prior_files, PREVIOUS / "protocol.json", PREVIOUS / "models.joblib",
        PREVIOUS / "training_features.jsonl", PREVIOUS / "feature_schema.json", PREVIOUS / "VALIDATION.json"]
    inputs += [ROOT / name for name in previous_protocol["input_hashes"]]
    output.mkdir(parents=True)
    for path in protected:
        dest = output / "sources" / path.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
    joblib.dump(dict(bank=bank, bundles=bundles, constant=prior["constant"]), output / "models.joblib")
    save_json(output / "selection.json", selection)
    save_json(output / "feature_schema.json", dict(baseline=names[:15], combined=names, **selection["selected_names"]))
    save_jsonl(output / "training_features.jsonl", [dict(case_id=row["case_id"], list_id=row["list_id"],
        label=row["label"], designs={arm:tx[i, columns].tolist() for arm, columns in bank.selected.items()})
        for i, row in enumerate(previous_training)])
    frozen_files = ("models.joblib", "selection.json", "feature_schema.json", "training_features.jsonl")
    protocol = dict(config=CONFIG, frozen_at_utc=datetime.now(timezone.utc).isoformat(),
        source_hashes={str(p.relative_to(ROOT)):sha(p) for p in protected},
        input_hashes={str(p.relative_to(ROOT)):sha(p) for p in inputs},
        frozen_hashes={name:sha(output / name) for name in frozen_files},
        prior_signatures=signatures, training_lists=sorted(set(groups[train])),
        calibration_lists=sorted(set(groups[calibration])), training_cases=int(train.sum()),
        python=sys.version, sklearn=sklearn.__version__, numpy=np.__version__, platform=platform.platform())
    save_json(output / "protocol.json", protocol)
    (output / "protocol.sha256").write_text(sha(output / "protocol.json") + "\n")
    print(f"FROZEN: selected top5/top10 from 27; {len(signatures)} prior lists excluded", flush=True)
    for arm, selected in selection["selected_names"].items():
        print(f"{arm}: {', '.join(selected)}", flush=True)


def verify(output):
    protocol = json.loads((output / "protocol.json").read_text())
    assert sha(output / "protocol.json") == (output / "protocol.sha256").read_text().strip()
    assert protocol["config"] == CONFIG
    for name, digest in protocol["frozen_hashes"].items():
        assert sha(output / name) == digest, name
    for name, digest in protocol["source_hashes"].items():
        assert sha(ROOT / name) == sha(output / "sources" / name) == digest, name
    for name, digest in protocol["input_hashes"].items():
        assert sha(ROOT / name) == digest, name
    return protocol


def simultaneous_interval(cases, y, p, baseline):
    groups = defaultdict(list)
    for i, case in enumerate(cases):
        groups[case["base_list_id"]].append(i)
    loss = (p-y)**2-(baseline-y)**2
    sums = np.array([loss[ids].sum() for ids in groups.values()])
    counts = np.array([len(ids) for ids in groups.values()])
    draws = np.random.default_rng(CONFIG["bootstrap_seed"]).integers(0, len(groups), (1000, len(groups)))
    delta = sums[draws].sum(axis=1)/counts[draws].sum(axis=1)
    return dict(difference=float(loss.mean()), list_bootstrap_97_5_percentile=np.quantile(delta, [.0125, .9875]).tolist(),
        multiplicity="two co-primary endpoints, Bonferroni-adjusted percentile level", conditional_on_fitted_models=True)


def analyze_sample(cases, refs, saved):
    result, records = geometric_analysis(cases, refs, saved)
    y = np.array([r["label"] for r in records])
    scores = {arm:np.array([r["probabilities"][arm] for r in records]) for arm in ARMS}
    result["paired_vs_full27"] = {}
    for name, mask in evaluation_masks(cases).items():
        subcases = [c for c, keep in zip(cases, mask) if keep]
        result["paired_vs_full27"][name] = {arm:bootstrap(subcases, y[mask], scores[arm][mask], scores["combined"][mask])
            for arm in ("top5", "top10")}
    mask = np.array([c["scale"] == 1 for c in cases])
    subcases = [c for c, keep in zip(cases, mask) if keep]
    result["co_primary"] = {arm:simultaneous_interval(subcases, y[mask], scores[arm][mask], scores["baseline"][mask])
        for arm in ("top5", "top10")}
    return result, records


def prediction_report(result, selection):
    lines = ["# Training-only pruning: fresh logistic comparison", "",
        "RFE selected features using only the 84 development training lists. Models were frozen before fresh generation; calibration uses separate lists. Lower Brier is better. Completion labels concern the exact reference's 8L work budget, not reachability or branch-checker benefit.", "",
        "| Model | Inputs | Accuracy | Hard precision | Hard recall | Brier |",
        "|---|---:|---:|---:|---:|---:|"]
    for arm in ARMS:
        row = result["models"]["unscaled"][arm]["all"]
        size = 15 if arm == "baseline" else 27 if arm == "combined" else int(arm[3:])
        lines.append(f'| {arm} | {size} | {row["accuracy_at_half"]:.3%} | {row["hard_precision"]:.3%} | {row["hard_recall"]:.3%} | {row["brier"]:.5f} |')
    lines += ["", "## Two co-primary comparisons against original baseline", "",
        "| Model | Brier difference | Conditional 95% interval | Bonferroni-level 97.5% interval |",
        "|---|---:|---|---|"]
    for arm in ("top5", "top10"):
        row = result["co_primary"][arm]
        lo, hi = result["paired"]["unscaled"][arm]["list_bootstrap_95_percentile"]
        alo, ahi = row["list_bootstrap_97_5_percentile"]
        lines.append(f'| {arm} | {row["difference"]:+.5f} | [{lo:+.5f}, {hi:+.5f}] | [{alo:+.5f}, {ahi:+.5f}] |')
    lines += ["", "## Frozen selected features", ""]
    for arm in ("top5", "top10"):
        lines += [f'**{arm}:** ' + ", ".join(selection["selected_names"][arm]) + ".", ""]
    lines += ["The top5 set is nested within top10. Rankings describe this fixed RFE procedure on correlated candidate features, not universal feature importance. All learned policies still pay original feature acquisition and identical core reuse. Selected prototype distances depend on all 15 base inputs; selected products depend on both original coordinates.", "",
        "## Secondary cohort comparisons", "", "| Cohort | Cases | Baseline Brier | Full27 | Top10 | Top5 |",
        "|---|---:|---:|---:|---:|---:|"]
    for name, models in result["models"].items():
        values = [models[arm]["all"]["brier"] for arm in ARMS]
        lines.append(f'| {name} | {models["baseline"]["all"]["n"]} | ' + " | ".join(f"{value:.5f}" for value in values) + " |")
    lines += ["", "Bootstrap intervals resample base lists with targets/encodings together and condition on fixed models/selection. They exclude retraining/selection uncertainty. The two co-primary comparisons have conservative 97.5% per-comparison levels; all remaining subgroup/full27 comparisons are secondary. Full calibration, confusion, unresolved-shortcut subgroup and full27-paired metrics are saved. Paid solver timing is a separate endpoint; no default model is changed."]
    return "\n".join(lines) + "\n"


def analyze(output):
    verify(output)
    check_hashes(output, "data_hashes.json")
    saved = joblib.load(output / "models.joblib")
    result, records = analyze_sample(read_jsonl(output / "cases.jsonl"), read_jsonl(output / "references.jsonl"), saved)
    selection = json.loads((output / "selection.json").read_text())
    save_json(output / "prediction_metrics.json", result)
    save_jsonl(output / "predictions.jsonl", records)
    (output / "PREDICTION_REPORT.md").write_text(prediction_report(result, selection), encoding="utf-8")
    save_hashes(output, "prediction_hashes.json", ("prediction_metrics.json", "predictions.jsonl", "PREDICTION_REPORT.md"))
    print(prediction_report(result, selection), flush=True)


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
                    base = f"pruning-n{n}-{family}-r{round(n*fraction)}-s{replicate}"
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




def priority_report(rows):
    lines = ["# Paid feature-pruned logistic prioritization", "",
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
