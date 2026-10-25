"""Predict each feature pipeline's exact completion including its extraction cost.

Each policy defines a separate label/task. Compare five distances, conventional
features and their hybrid only within the same task. Cross-task Brier differences
alone are not evidence of one feature vector's predictive superiority.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import shutil

import numpy as np
import sklearn

from fit_development import (CONFIG as MODEL_CONFIG, cluster_difference, fit_model,
                             matrix, metrics, read_jsonl)
from run_development import VARIANTS
from run_pilot import save_json, save_jsonl, sha


CONFIG = {
    "status": "exploratory end-to-end development prediction; not final evaluation",
    "tasks": list(VARIANTS),
    "target": "exact completion under 8L including shared prechecks, feature extraction and certificate reuse",
    "predictors": ["constant", "five", "conventional", "hybrid"],
    "model_config": MODEL_CONFIG,
    "comparison": "feature sets compared within each fixed cost/reuse policy's label",
    "inference_cost": "not charged; downstream learned prioritization and inference cost remain untested",
}


def report(result):
    lines = ["# End-to-end completion prediction", "", CONFIG["status"] + ".", "",
             "Each task's labels include that feature pipeline's extraction and certificate "
             "reuse costs under 8L. Predictors are compared against the same labels within "
             "each row. Cross-row scores refer to different label distributions.", "",
             "Calibrated forest Brier scores; lower is better.", "",
             "| Cost/reuse task | Evaluation | Constant | Five | Conventional | Hybrid |",
             "|---|---|---:|---:|---:|---:|"]
    for task in VARIANTS:
        for split in ("test", "larger_size", "unseen_family"):
            scores = [result["tasks"][task][name][split]["calibrated"]["brier"]
                      for name in ("constant", "five:forest", "conventional:forest", "hybrid:forest")]
            lines.append(f"| {task} | {split} | " + " | ".join(f"{s:.4f}" for s in scores) + " |")
    lines += ["", "These predictions concern the predeclared exact-solving pipelines; no "
              "learned execution or prioritization policy has been deployed. Prediction "
              "inference cost is not part of the training labels. Preprocessing-only "
              "completions are included, and unresolved-kernel subgroups are reported separately.", "",
              "Training, calibration, list splits and held-out domains match the common-label "
              "development comparison. No final prospective evidence or asymptotic claim is made."]
    return "\n".join(lines) + "\n"


def fit(data, output):
    if output.exists():
        raise FileExistsError("end-to-end fitting requires a fresh output directory")
    hashes = json.loads((data / "artifact_hashes.json").read_text())
    for name, digest in hashes.items():
        if sha(data / name) != digest:
            raise AssertionError(f"data hash mismatch: {name}")
    cases, runs = read_jsonl(data / "cases.jsonl"), read_jsonl(data / "runs.jsonl")
    by_policy = {(r["case_id"], r["policy"]): r for r in runs}
    split = np.array([c["split"] for c in cases])
    training, calibration = split == "train", split == "calibration"
    list_splits = defaultdict(set)
    for case in cases:
        list_splits[case["list_id"]].add(case["split"])
    if any(len(values) != 1 for values in list_splits.values()):
        raise AssertionError("list leakage")
    output.mkdir(parents=True)
    sources = [Path(__file__).resolve(), Path(__file__).with_name("fit_development.py")]
    for source in sources:
        shutil.copy2(source, output / source.name)
    save_json(output / "fit_protocol.json", {"config": CONFIG, "input_hashes": hashes,
        "source_hashes": {p.name: sha(p) for p in sources},
        "numpy": np.__version__, "sklearn": sklearn.__version__})
    result, predictions = {"tasks": {}, "paired_differences": {}}, []
    unresolved = np.array([c["kernel"]["status"] == "unresolved" for c in cases])
    for task in VARIANTS:
        y = np.array([int(by_policy[(c["case_id"], task)]["status"] != "unresolved") for c in cases])
        x_five, x_conventional = matrix(cases, task), matrix(cases, "conventional")
        matrices = {"five": x_five, "conventional": x_conventional,
                    "hybrid": np.concatenate([x_five, x_conventional], axis=1)}
        specs = [("constant", "prior")] + [(name, kind) for name in matrices for kind in ("logistic", "forest")]
        result["tasks"][task], scores = {}, {}
        for feature_set, kind in specs:
            name = "constant" if feature_set == "constant" else f"{feature_set}:{kind}"
            if feature_set == "constant":
                raw = calibrated = np.full(len(cases), y[training].mean())
            else:
                raw, calibrated = fit_model(matrices[feature_set], y, training, calibration, kind)
            scores[name] = calibrated
            result["tasks"][task][name] = {}
            for split_name in ("train", "calibration", "test", "larger_size", "unseen_family"):
                mask = split == split_name
                result["tasks"][task][name][split_name] = {
                    "raw": metrics(y[mask], raw[mask]),
                    "calibrated": metrics(y[mask], calibrated[mask]),
                    "unresolved_kernel": metrics(y[mask & unresolved], calibrated[mask & unresolved])}
            predictions.extend({"case_id": c["case_id"], "list_id": c["list_id"],
                                "split": c["split"], "task": task, "model": name,
                                "label": int(y[i]), "raw": float(raw[i]),
                                "calibrated": float(calibrated[i])} for i, c in enumerate(cases))
        result["paired_differences"][task] = {
            comparison: {split_name: cluster_difference(cases, y, scores[first], scores[second], split_name)
                         for split_name in ("test", "larger_size", "unseen_family")}
            for comparison, first, second in (
                ("five_minus_conventional", "five:forest", "conventional:forest"),
                ("hybrid_minus_conventional", "hybrid:forest", "conventional:forest"))}
        print(f"fitted end-to-end task {task}", flush=True)
    save_json(output / "metrics.json", result)
    save_jsonl(output / "predictions.jsonl", predictions)
    (output / "REPORT.md").write_text(report(result), encoding="utf-8")
    for source in sources:
        if sha(source) != sha(output / source.name):
            raise AssertionError("fitting source changed")
    artifacts = ("fit_protocol.json", "metrics.json", "predictions.jsonl", "REPORT.md")
    save_json(output / "artifact_hashes.json", {name: sha(output / name) for name in artifacts})
    print((output / "REPORT.md").read_text(), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    fit(args.data, args.output)
