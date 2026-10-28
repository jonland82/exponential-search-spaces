"""Experiment 02: freeze, grouped training/calibration, fresh tests and paid pools."""
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
import argparse
import json
from pathlib import Path
import platform
import random
import shutil
import sys

import joblib
import numpy as np
import sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from Structural_Geometry_Subset_Sum.classifier_features import (ARMS, POLICIES,
    SCHEMAS, LEGACY_CONFIG, base_features, calibrated_bundle, design,
    doubling_feature, geometry_features, new_weights, pending_after_shared_checks,
    probabilities, reference, score)
from Structural_Geometry_Subset_Sum.classifier_pool import run_pool
from Structural_Geometry_Subset_Sum.compat import (ROOT, independent_halves,
    independent_query, input_length, reduce_instance)
from Structural_Geometry_Subset_Sum.study import (check_manifest, make_weights,
    manifest, read_jsonl, save_json, save_jsonl, sha, signature)


HERE = Path(__file__).resolve().parent
STRUCTURED = ("large_base", "large_base_one_outlier", "large_base_many_outliers")
FAMILIES = list(LEGACY_CONFIG["families"])+list(STRUCTURED)
CONFIG = dict(seed=770281028, sizes=[24, 32, 36], families=FAMILIES,
    replicates=dict(train=2, calibration=1, test=3),
    targets=["planted", "middle", "fractional_band"],
    logistic=dict(C=1., max_iter=2000, random_state=630251026),
    model_arms=list(ARMS), policies=list(POLICIES),
    candidate_cap=24, detector_work_cap=1_000_000,
    reference_work_multiplier=8, pool_fractions=[.2, .5], repeats=3,
    per_case_seconds=.020, bootstrap_draws=2000,
    primary="Brier on test cases unresolved after reduction, five-core reuse and aggregate-gap check",
    co_primary=["geometry18 minus baseline15", "doubling19 minus baseline15"],
    status="new locally frozen experiment; all models retrained on identical expanded training lists")


def utc():
    return datetime.now(timezone.utc).isoformat()


def freeze(output):
    if output.exists():
        raise FileExistsError("use a new output directory")
    sources = [HERE/name for name in ("classifier_features.py", "classifier_pool.py",
        "classifier_study.py", "classifier_audit.py", "tests/test_classifier.py",
        "experiments/02_literature_classifier/PROTOCOL.md", "budget.py", "compat.py",
        "structures/large_base.py", "study.py", "solver.py")]
    sources += [ROOT/"Learned_Solvability_Subset_Sum"/name for name in
        ("features.py", "advanced_features.py", "run_pilot.py", "run_development.py",
         "fit_development.py", "prospective_study.py", "priority_experiment.py",
         "neighbor_experiment.py", "neighbor_models.py", "geometric_experiment.py", "geometric_models.py")]
    sources += [ROOT/"Structural_Distance_Subset_Sum/structural_subset_sum.py"]
    prior = sorted(p for p in ROOT.rglob("lists.jsonl") if not
        {"sources", "upstream", "reruns", ".git", ".build"}.intersection(p.relative_to(ROOT).parts))
    seen = sorted({signature(row["weights"]) for p in prior for row in read_jsonl(p)})
    output.mkdir(parents=True)
    for source in sources:
        dest = output/"sources"/source.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
    protocol = dict(config=CONFIG, frozen_at_utc=utc(),
        source_hashes={str(p.relative_to(ROOT)):sha(p) for p in sources},
        input_hashes={str(p.relative_to(ROOT)):sha(p) for p in prior}, prior_signatures=seen,
        feature_schema=SCHEMAS, python=sys.version, platform=platform.platform(),
        numpy=np.__version__, sklearn=sklearn.__version__)
    save_json(output/"protocol.json", protocol)
    (output/"protocol.sha256").write_text(sha(output/"protocol.json")+"\n")
    print(f"FROZEN before generation: three logistic designs; {len(seen)} previous lists excluded", flush=True)


def verify(output):
    protocol = json.loads((output/"protocol.json").read_text())
    assert protocol["config"] == CONFIG
    assert sha(output/"protocol.json") == (output/"protocol.sha256").read_text().strip()
    for name, digest in protocol["source_hashes"].items():
        assert sha(ROOT/name) == sha(output/"sources"/name) == digest, name
    for name, digest in protocol["input_hashes"].items():
        assert sha(ROOT/name) == digest, name
    return protocol


def make_case(list_row, target, target_rule, oracle_mask):
    weights = list_row["weights"]
    kernel = reduce_instance(weights, target)
    cap = CONFIG["reference_work_multiplier"]*input_length(weights, target)
    base = base_features(weights, target, kernel)
    geometry = geometry_features(kernel.weights, kernel.target)
    doubling = doubling_feature(kernel.weights)
    ref = reference(weights, target, kernel, cap)
    truth = "yes" if oracle_mask is not None else "no"
    for result in (dict(status=kernel.status, witness=kernel.witness), base["reuse"], ref):
        if result["status"] != "unresolved":
            assert result["status"] == truth
        if result["status"] == "yes" and result["witness"] is not None:
            assert sum(weights[i] for i in result["witness"]) == target
    if geometry["exact_no"]:
        assert truth == "no"
    return dict(case_id=f'{list_row["list_id"]}-{target_rule}',
        **{key:list_row[key] for key in ("list_id", "split", "n", "family", "cohort")},
        target_rule=target_rule, weights=weights, target=target, oracle_mask=oracle_mask,
        truth=truth, budget=cap, kernel=asdict(kernel), base=base, geometry=geometry,
        doubling=doubling, reference=ref, label=int(ref["status"] != "unresolved"))


def generate(output, evaluation=False):
    protocol = verify(output)
    prefix = "test" if evaluation else "development"
    if evaluation:
        check_manifest(output, "model_hashes.json")
        check_manifest(output, "development_hashes.json")
    save_json(output/f"{prefix}.started.json", dict(utc=utc(),
        model_sha256=sha(output/"models.joblib") if evaluation else None))
    seen = set(protocol["prior_signatures"])
    if evaluation:
        seen.update(signature(r["weights"]) for r in read_jsonl(output/"development_lists.jsonl"))
    lists, cases, proposals = [], [], []
    splits = ["test"] if evaluation else ["train", "calibration"]
    for split in splits:
        for n in CONFIG["sizes"]:
            for family in FAMILIES:
                for replicate in range(CONFIG["replicates"][split]):
                    list_id = f"literature-{split}-n{n}-{family}-s{replicate}"
                    for proposal in range(64):
                        rng = random.Random(f'{CONFIG["seed"]}:{list_id}:{proposal}')
                        variant = rng.randrange(4)  # base type/size independent of split
                        if family in STRUCTURED:
                            weights, metadata = make_weights(family, n, variant, rng)
                        else:
                            replacements = round(n*.25) if rng.getrandbits(1) else 0
                            weights = new_weights(family, n, replacements, rng)
                            metadata = dict(replacements=replacements)
                        code = signature(weights)
                        accepted = code not in seen
                        proposals.append(dict(list_id=list_id, proposal=proposal, accepted=accepted))
                        if accepted:
                            seen.add(code)
                            break
                    else:
                        raise RuntimeError(f"no unused list for {list_id}")
                    cohort = "large_base" if family in STRUCTURED else "legacy_families"
                    row = dict(list_id=list_id, split=split, n=n, family=family, cohort=cohort,
                               replicate=replicate, weights=weights, metadata=metadata)
                    lists.append(row)
                    total = sum(weights)
                    planted = sum(w for w in weights if rng.getrandbits(1))
                    middle = rng.randrange(3*total//10, 7*total//10+1)
                    fractional = (metadata["base"]*(sum(metadata["p"])//2)+metadata["base"]//2
                                  if "base" in metadata else total//2+1)
                    halves = independent_halves(weights)
                    for rule, target in zip(CONFIG["targets"], (planted, middle, fractional)):
                        mask = independent_query(halves, target)
                        cases.append(make_case(row, target, rule, mask))
                    del halves
                    if len(lists) % 15 == 0:
                        print(f"{prefix}: {len(lists)} lists / {len(cases)} cases", flush=True)
    names = [f"{prefix}_lists.jsonl", f"{prefix}_cases.jsonl", f"{prefix}_proposals.jsonl"]
    for name, rows in zip(names, (lists, cases, proposals)):
        save_jsonl(output/name, rows)
    # A conventional combined filename allows future freezes to exclude all lists.
    if evaluation:
        save_jsonl(output/"lists.jsonl", read_jsonl(output/"development_lists.jsonl")+lists)
        names.append("lists.jsonl")
    manifest(output, f"{prefix}_hashes.json", names)


def fit(output):
    verify(output)
    check_manifest(output, "development_hashes.json")
    assert not (output/"test.started.json").exists()
    cases = read_jsonl(output/"development_cases.jsonl")
    train = np.array([c["split"] == "train" for c in cases])
    calibration = ~train
    y = np.array([c["label"] for c in cases])
    assert not {c["list_id"] for c, keep in zip(cases, train) if keep} & {
        c["list_id"] for c, keep in zip(cases, calibration) if keep}
    bundles, coefficients = {}, {}
    with threadpool_limits(limits=1):
        for arm in ARMS:
            x = np.array([design(c, arm) for c in cases])
            model = make_pipeline(StandardScaler(), LogisticRegression(**CONFIG["logistic"]))
            model.fit(x[train], y[train])
            bundles[arm] = calibrated_bundle(model, x[calibration], y[calibration], x.shape[1])
            coefficients[arm] = dict(names=SCHEMAS[arm],
                standardized_coefficients=model[-1].coef_[0].tolist(),
                intercept=model[-1].intercept_.tolist(),
                train_cases=int(train.sum()), calibration_cases=int(calibration.sum()))
    joblib.dump(bundles, output/"models.joblib")
    save_json(output/"coefficients.json", coefficients)
    save_json(output/"model_freeze.json", dict(frozen_at_utc=utc(),
        protocol_sha256=sha(output/"protocol.json"),
        training_lists=sorted({c["list_id"] for c, keep in zip(cases, train) if keep}),
        calibration_lists=sorted({c["list_id"] for c, keep in zip(cases, calibration) if keep}),
        model_sha256=sha(output/"models.joblib"), development_hashes_sha256=sha(output/"development_hashes.json")))
    manifest(output, "model_hashes.json", ["models.joblib", "coefficients.json", "model_freeze.json"])
    print(f"MODELS FROZEN before test generation: {train.sum()} train / {calibration.sum()} calibration cases", flush=True)


def paired_interval(cases, labels, p, baseline):
    groups = defaultdict(list)
    for i, case in enumerate(cases):
        groups[case["list_id"]].append(i)
    if not groups:
        return None
    losses = (p-labels)**2-(baseline-labels)**2
    sums = np.array([losses[ids].sum() for ids in groups.values()])
    counts = np.array([len(ids) for ids in groups.values()])
    draws = np.random.default_rng(CONFIG["seed"]).integers(0, len(groups),
        (CONFIG["bootstrap_draws"], len(groups)))
    delta = sums[draws].sum(axis=1)/counts[draws].sum(axis=1)
    return dict(difference=float(losses.mean()), lists=len(groups),
        list_bootstrap_95=np.quantile(delta, [.025, .975]).tolist(),
        bonferroni_two_comparison_97_5=np.quantile(delta, [.0125, .9875]).tolist(),
        conditional_on_fixed_fits=True)


def predictive_summary(cases, bundles):
    y = np.array([c["label"] for c in cases])
    p = {arm:probabilities(bundles[arm], [design(c, arm) for c in cases]) for arm in ARMS}
    masks = dict(all=np.ones(len(cases), dtype=bool),
        after_shared_exact_checks=np.array([pending_after_shared_checks(c) for c in cases]))
    masks.update({name:np.array([c["cohort"] == name for c in cases])
                  for name in sorted({c["cohort"] for c in cases})})
    masks.update({f"family:{name}":np.array([c["family"] == name for c in cases])
                  for name in FAMILIES})
    summary = {}
    for name, mask in masks.items():
        subset = [c for c, keep in zip(cases, mask) if keep]
        summary[name] = dict(models={arm:score(y[mask], prob[mask]) for arm, prob in p.items()},
            versus_baseline15={arm:paired_interval(subset, y[mask], p[arm][mask], p["baseline15"][mask])
                for arm in ARMS[1:]})
    records = [dict(case_id=c["case_id"], label=int(y[i]), pending=pending_after_shared_checks(c),
        probabilities={arm:float(prob[i]) for arm, prob in p.items()}) for i, c in enumerate(cases)]
    return summary, records


def aggregate_pools(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[(row["mode"], row["cohort"], row["fraction"], row["policy"])].append(row)
    result = []
    for (mode, cohort, fraction, policy), group in sorted(groups.items()):
        values = [r["solved"] for r in group]
        result.append(dict(mode=mode, cohort=cohort, fraction=fraction, policy=policy,
            median_solved=float(np.median(values)), min_solved=min(values), max_solved=max(values),
            repeats=len(group), mean_costs={phase:float(np.mean([r["costs"][phase] for r in group]))
                for phase in group[0]["costs"]},
            max_overshoot_seconds=max(r["overshoot_seconds"] for r in group)))
    return result


def report(summary, pools, cases):
    pending = summary["after_shared_exact_checks"]
    lines = ["# Literature-derived features in logistic regression", "",
        "New disjoint expanded training/calibration/test lists; every model uses identical training labels and C=1. The label remains original exact-portfolio completion within 8L, not reachability or geometric-check benefit. Models were frozen before test generation.", "",
        "## Primary: cases remaining after identical exact shortcuts", "",
        "Reduction, all five existing zero-deletion cores and aggregate-gap NO checks define this subgroup. Exact geometric certificates receive no ML credit. Lower Brier is better.", "",
        "| Model | Cases | Brier | Accuracy | Hard recall | Brier difference vs 15 | Adjusted 97.5% interval |",
        "|---|---:|---:|---:|---:|---:|---|"]
    for arm in ARMS:
        m = pending["models"][arm]
        delta = pending["versus_baseline15"].get(arm)
        interval = "--" if delta is None else "["+", ".join(f"{v:+.5f}" for v in delta["bonferroni_two_comparison_97_5"])+"]"
        diff = "--" if delta is None else f'{delta["difference"]:+.5f}'
        lines.append(f'| {arm} | {m["n"]} | {m.get("brier", float("nan")):.5f} | {m.get("accuracy_at_half", 0):.1%} | {m.get("hard_recall", 0):.1%} | {diff} | {interval} |')
    lines += ["", "## Secondary predictive cohorts", "",
        "| Cohort | Cases | Baseline15 Brier | Geometry18 | Doubling19 |",
        "|---|---:|---:|---:|---:|"]
    for name in ("all", "legacy_families", "large_base"):
        models = summary[name]["models"]
        lines.append(f'| {name} | {models["baseline15"]["n"]} | '+" | ".join(f'{models[a]["brier"]:.5f}' for a in ARMS)+" |")
    lines += ["", "## Paid prioritization", "",
        "Median completions over three paired arrival orders, including acquisition, inference, exact reuse, sorting, solving and witness checking. Live pools use actual recomputation and cooperative deadlines; late answers are excluded. Work counters are heterogeneous operations, not CPU/bit complexity.", "",
        "cheap15 skips geometric discovery. matched15 pays discovery and uses its exact gap certificate, but predicts from the original 15 inputs. geometry18 has the same exact shortcuts plus three geometric inputs. doubling19 additionally pays distinct-weight additive doubling. Comparing geometry18 with matched15 isolates the learned features; comparison with cheap15 measures their complete package.", "",
        "| Mode | Cohort | Budget fraction | cheap15 | matched15 | geometry18 | doubling19 |",
        "|---|---|---:|---:|---:|---:|---:|"]
    index = {(r["mode"], r["cohort"], r["fraction"], r["policy"]):r for r in pools}
    for key in sorted({k[:3] for k in index}):
        lines.append(f"| {key[0]} | {key[1]} | {key[2]} | "+" | ".join(str(index[(*key, p)]["median_solved"]) for p in POLICIES)+" |")
    gaps = sum(c["geometry"]["exact_no"] and c["kernel"]["status"] == "unresolved"
        and c["base"]["reuse"]["status"] == "unresolved" for c in cases)
    lines += ["", f"Test cases: {len(cases)} from {len({c['list_id'] for c in cases})} independent lists; {pending['models']['baseline15']['n']} remain after all shared checks; {gaps} additional exact aggregate-gap answers after the five cores.", "",
        "## Limits", "",
        "These are proposed operational descriptors motivated by decomposable-knapsack and small-doubling results, not published proven difficulty predictors. Candidate discovery is bounded and heuristic. Models use the same expanded mixture, so this is a feature comparison rather than a direct retest of the earlier fitted model. There is no paired scaled-encoding or unseen-family generalization claim. Bootstrap intervals keep targets from each list together, condition on fitted models, and omit retraining uncertainty; subgroup endpoints and timing comparisons are descriptive. The two primary comparisons use conservative Bonferroni-level intervals. Three repeat orders are not independent datasets. No learned prediction certifies NO or prunes a branch. No large-base DP is run in this classifier experiment. No default model or paper is changed."]
    return "\n".join(lines)+"\n"


def evaluate(output):
    verify(output)
    for name in ("development_hashes.json", "model_hashes.json", "test_hashes.json"):
        check_manifest(output, name)
    save_json(output/"evaluation.started.json", dict(utc=utc()))
    cases = read_jsonl(output/"test_cases.jsonl")
    bundles = joblib.load(output/"models.joblib")
    with threadpool_limits(limits=1):
        summary, records = predictive_summary(cases, bundles)
        predictions = {r["case_id"]:r["probabilities"] for r in records}
        save_json(output/"prediction_metrics.json", summary)
        save_jsonl(output/"predictions.jsonl", records)
        groups = defaultdict(list)
        for case in cases:
            groups[case["cohort"]].append(case)
        rows = []
        with (output/"pool_runs.jsonl").open("x", encoding="utf-8") as handle:
            for mode in ("work", "time"):
                for cohort, group in sorted(groups.items()):
                    for fraction in CONFIG["pool_fractions"]:
                        for repeat in range(CONFIG["repeats"]):
                            policies = list(POLICIES)
                            random.Random(f'{CONFIG["seed"]}:{mode}:{cohort}:{fraction}:{repeat}').shuffle(policies)
                            for policy in policies:
                                row = run_pool(group, bundles, predictions, policy, mode, fraction,
                                    repeat, CONFIG["seed"], CONFIG["per_case_seconds"])
                                rows.append(row)
                                handle.write(json.dumps(row, separators=(",", ":"))+"\n")
                                handle.flush()
                            print(f"paid pools: {mode} {cohort} {fraction} repeat {repeat}", flush=True)
    pools = aggregate_pools(rows)
    save_json(output/"pool_summary.json", pools)
    (output/"REPORT.md").write_text(report(summary, pools, cases), encoding="utf-8")
    manifest(output, "evaluation_hashes.json", ["prediction_metrics.json", "predictions.jsonl",
        "pool_runs.jsonl", "pool_summary.json", "REPORT.md"])
    print((output/"REPORT.md").read_text(), flush=True)


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("stage", choices=("freeze", "development", "fit", "test", "evaluate", "all"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    stages = dict(freeze=freeze, development=lambda p:generate(p), fit=fit,
                  test=lambda p:generate(p, True), evaluate=evaluate)
    for name in stages if args.stage == "all" else [args.stage]:
        stages[name](args.output.resolve())


if __name__ == "__main__":
    main()
