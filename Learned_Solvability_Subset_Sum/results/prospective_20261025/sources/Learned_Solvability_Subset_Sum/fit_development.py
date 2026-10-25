"""Fixed exploratory ML comparison on grouped development data.

Primary prediction labels are common exact-portfolio completion, not subset-sum
reachability. Train/calibration/test lists are disjoint. Calibration never sees
test labels; held-out families and larger sizes are not used in fitting.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import platform
import shutil

import numpy as np
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from run_development import CONFIG as DATA_CONFIG, VARIANTS
from run_pilot import save_json, save_jsonl, sha


CONFIG = {
    "status": "exploratory development-model comparison; no prospective performance claim",
    "seed": 630_251_026,
    "models": ["logistic", "forest"],
    "forest": {"n_estimators": 200, "max_depth": 8, "min_samples_leaf": 4, "n_jobs": 1},
    "logistic": {"C": 1.0, "max_iter": 2000},
    "calibration": "logistic sigmoid on clipped logit scores; fitted only on calibration lists",
    "feature_sets": list(VARIANTS) + ["conventional", "hybrid"],
    "hybrid": "target_progression's five distances plus ten conventional features",
    "ablations": "forest: drop each coordinate of target_progression; diagnostic four-input models",
    "primary_label": "shared portfolio finishes under 8L work budget, excluding ML features",
    "cost_labels": "not used for this predictive-information comparison; reported separately",
    "bootstrap": "500 resamples of weight lists within each evaluation split; fixed model predictions",
    "reliability_bins": 10,
}


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def metrics(labels, probabilities):
    labels, probabilities = np.asarray(labels), np.asarray(probabilities)
    if len(labels) == 0:
        return {"n": 0}
    bins = []
    ece = 0.0
    assignments = np.minimum((probabilities * 10).astype(int), 9)
    for number in range(10):
        mask = assignments == number
        if not mask.any():
            continue
        predicted = float(probabilities[mask].mean())
        observed = float(labels[mask].mean())
        count = int(mask.sum())
        ece += count / len(labels) * abs(predicted - observed)
        bins.append({"bin": number, "n": count, "predicted": predicted, "observed": observed})
    return {"n": len(labels), "success_rate": float(labels.mean()),
            "mean_prediction": float(probabilities.mean()),
            "brier": float(brier_score_loss(labels, probabilities)),
            "log_loss": float(log_loss(labels, probabilities, labels=[0, 1])),
            "auc": float(roc_auc_score(labels, probabilities)) if len(set(labels)) == 2 else None,
            "accuracy_at_half": float(((probabilities >= 0.5) == labels).mean()),
            "ece": float(ece), "bins": bins}


def cluster_difference(cases, labels, first, second, split):
    """Brier(first) - Brier(second); negative favors first. Conditional on fits."""
    groups = defaultdict(list)
    for i, case in enumerate(cases):
        if case["split"] == split:
            groups[case["list_id"]].append(i)
    blocks = list(groups.values())
    if not blocks:
        return None
    losses = np.square(first - labels) - np.square(second - labels)
    sums = np.array([losses[indices].sum() for indices in blocks])
    sizes = np.array([len(indices) for indices in blocks])
    rng = np.random.default_rng(CONFIG["seed"])
    samples = rng.integers(0, len(blocks), size=(500, len(blocks)))
    differences = sums[samples].sum(axis=1) / sizes[samples].sum(axis=1)
    return {"difference": float(sums.sum() / sizes.sum()),
            "list_bootstrap_95_percentile": [float(v) for v in np.quantile(differences, [0.025, 0.975])],
            "lists": len(blocks), "conditional_on_fitted_models": True}


def matrix(cases, name):
    if name == "conventional":
        return np.array([c["conventional"] for c in cases], dtype=float)
    if name == "hybrid":
        return np.array([c["features"]["target_progression"] + c["conventional"] for c in cases], dtype=float)
    if name.startswith("drop_"):
        dimension = int(name.split("_")[1])
        return np.delete(matrix(cases, "target_progression"), dimension, axis=1)
    return np.array([c["features"][name] for c in cases], dtype=float)


def fit_model(x, y, training, calibration, kind):
    if len(set(y[training])) != 2 or len(set(y[calibration])) != 2:
        raise ValueError("training and calibration must each contain both completion labels")
    if kind == "logistic":
        model = make_pipeline(StandardScaler(), LogisticRegression(
            random_state=CONFIG["seed"], **CONFIG["logistic"]))
    else:
        model = RandomForestClassifier(random_state=CONFIG["seed"], **CONFIG["forest"])
    model.fit(x[training], y[training])
    raw = model.predict_proba(x)[:, 1]
    clipped = np.clip(raw, 1e-6, 1 - 1e-6)
    logits = np.log(clipped / (1 - clipped)).reshape(-1, 1)
    calibrator = LogisticRegression(C=1.0, max_iter=2000, random_state=CONFIG["seed"])
    calibrator.fit(logits[calibration], y[calibration])
    calibrated = calibrator.predict_proba(logits)[:, 1]
    return raw, calibrated


def render_report(result):
    lines = ["# Five-feature development comparison", "", CONFIG["status"] + ".", "",
             "The prediction label is completion by the same exact solver portfolio under "
             "the 8L budget for every feature set. Feature extraction is excluded from this "
             "common label to compare predictive information. Separate operational runs charge "
             "extraction, reuse certificates and apply the same fallback portfolio.", "",
             "## Calibrated probability quality", "",
             "Brier score: lower is better. Evaluation includes every target. "
             "Additional unresolved-kernel-only metrics and raw/calibrated scores are in metrics.json.", "",
             "| Model | Same-distribution test | Larger size | Unseen families |",
             "|---|---:|---:|---:|"]
    names = ["constant"] + [f"{name}:forest" for name in CONFIG["feature_sets"]]
    for name in names:
        scores = [result["models"][name][split]["calibrated"]["brier"]
                  for split in ("test", "larger_size", "unseen_family")]
        lines.append(f"| {name} | " + " | ".join(f"{score:.4f}" for score in scores) + " |")
    lines += ["", "## Interpretation", "",
              "All targets from a weight list share a split. Calibration uses separate lists. "
              "Near-equal and filtered-modular families, and size n=36, never enter training or "
              "calibration. Unseen-family evaluation also includes n=36; its smaller-size "
              "subgroup is recorded separately to distinguish family and size shifts.", "",
              "Confidence intervals resample lists with model predictions held fixed; they do not "
              "include uncertainty from retraining. Model and feature choices are development "
              "choices informed by the earlier feasibility pilot. No final prospective test or "
              "claim of polynomial asymptotic performance is made.", "",
              "The raw predictions, calibration comparisons, four-input ablations, paired "
              "Brier differences, dependency versions and source/data hashes are retained. "
              "No learned budget-prioritization policy has been tested yet."]
    return "\n".join(lines) + "\n"


def fit(data, output):
    if output.exists():
        raise FileExistsError("model fitting requires a fresh output directory")
    hashes = json.loads((data / "artifact_hashes.json").read_text())
    for name, digest in hashes.items():
        if sha(data / name) != digest:
            raise AssertionError(f"data hash mismatch: {name}")
    protocol = json.loads((data / "protocol.json").read_text())
    if protocol["config"] != DATA_CONFIG:
        raise AssertionError("data configuration mismatch")
    cases, runs = read_jsonl(data / "cases.jsonl"), read_jsonl(data / "runs.jsonl")
    common = {r["case_id"]: r for r in runs if r["policy"] == "common"}
    y = np.array([int(common[c["case_id"]]["status"] != "unresolved") for c in cases])
    split = np.array([c["split"] for c in cases])
    training, calibration = split == "train", split == "calibration"
    list_splits = defaultdict(set)
    for case in cases:
        list_splits[case["list_id"]].add(case["split"])
    if any(len(values) != 1 for values in list_splits.values()):
        raise AssertionError("list leakage across splits")
    # Verify sorted-list signatures, not only IDs, do not cross groups.
    lists = read_jsonl(data / "lists.jsonl")
    signatures = defaultdict(set)
    for row in lists:
        signatures[tuple(sorted(row["weights"]))].add(row["split"])
    if any(len(values) != 1 for values in signatures.values()):
        raise AssertionError("duplicate list leakage")
    output.mkdir(parents=True)
    source = Path(__file__).resolve()
    shutil.copy2(source, output / source.name)
    save_json(output / "fit_protocol.json", {"config": CONFIG, "input_hashes": hashes,
        "source_hash": sha(source), "numpy": np.__version__, "sklearn": sklearn.__version__,
        "python": platform.python_version()})
    result = {"models": {}, "paired_differences": {},
              "split_counts": {name: int((split == name).sum()) for name in set(split)}}
    predictions = []
    scores = {}
    model_specs = [(name, kind) for name in CONFIG["feature_sets"] for kind in CONFIG["models"]]
    model_specs += [(f"drop_{dimension}", "forest") for dimension in range(5)]
    model_specs.insert(0, ("constant", "prior"))
    for feature_set, kind in model_specs:
        name = "constant" if feature_set == "constant" else f"{feature_set}:{kind}"
        if feature_set == "constant":
            raw = calibrated = np.full(len(cases), y[training].mean())
        else:
            raw, calibrated = fit_model(matrix(cases, feature_set), y, training, calibration, kind)
        scores[name] = calibrated
        result["models"][name] = {}
        for split_name in ("train", "calibration", "test", "larger_size", "unseen_family"):
            mask = split == split_name
            unresolved = mask & np.array([c["kernel"]["status"] == "unresolved" for c in cases])
            smaller = mask & np.array([c["n"] < DATA_CONFIG["larger_size"] for c in cases])
            result["models"][name][split_name] = {
                "raw": metrics(y[mask], raw[mask]),
                "calibrated": metrics(y[mask], calibrated[mask]),
                "unresolved_kernel": metrics(y[unresolved], calibrated[unresolved]),
                "smaller_sizes_only": metrics(y[smaller], calibrated[smaller])}
        predictions.extend({"case_id": c["case_id"], "list_id": c["list_id"],
                            "split": c["split"], "model": name, "label": int(y[i]),
                            "raw": float(raw[i]), "calibrated": float(calibrated[i])}
                           for i, c in enumerate(cases))
        print(f"fitted {name}", flush=True)
    comparisons = [("progression:forest", "original:forest"),
                   ("target_original:forest", "original:forest"),
                   ("target_progression:forest", "original:forest"),
                   ("target_progression:forest", "conventional:forest"),
                   ("hybrid:forest", "conventional:forest")]
    for first, second in comparisons:
        result["paired_differences"][f"{first} minus {second}"] = {
            name: cluster_difference(cases, y, scores[first], scores[second], name)
            for name in ("test", "larger_size", "unseen_family")}
    save_json(output / "metrics.json", result)
    save_jsonl(output / "predictions.jsonl", predictions)
    (output / "REPORT.md").write_text(render_report(result), encoding="utf-8")
    make_chart(result, output)
    if sha(source) != sha(output / source.name):
        raise AssertionError("model source changed during fit")
    artifacts = ("fit_protocol.json", "metrics.json", "predictions.jsonl", "REPORT.md", "comparison.png")
    save_json(output / "artifact_hashes.json", {name: sha(output / name) for name in artifacts})
    print((output / "REPORT.md").read_text(), flush=True)


def make_chart(result, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    names = ["original:forest", "progression:forest", "target_original:forest",
             "target_progression:forest", "conventional:forest", "hybrid:forest"]
    labels = ["Original five", "Progression five", "Target five", "Target + progression five",
              "Conventional", "Hybrid"]
    fig, axes = plt.subplots(1, 3, figsize=(14, 4), constrained_layout=True)
    for ax, split_name, title in zip(axes, ("test", "larger_size", "unseen_family"),
                                    ("Disjoint-list test", "Larger size (n=36)", "Unseen families")):
        values = [result["models"][name][split_name]["calibrated"]["brier"] for name in names]
        ax.barh(labels, values, color=["#596b85", "#4b88a2", "#5e9a88", "#207c72", "#aa7857", "#775f9a"])
        baseline = result["models"]["constant"][split_name]["calibrated"]["brier"]
        ax.axvline(baseline, color="black", linestyle="--", linewidth=1, label="Constant prior")
        ax.invert_yaxis()
        ax.set_title(title)
        ax.set_xlabel("Calibrated Brier score (lower is better)")
        ax.legend(fontsize=8)
    fig.suptitle("Paper VI development data: common solver-completion label", fontsize=13)
    fig.savefig(output / "comparison.png", dpi=170)
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    fit(args.data, args.output)
