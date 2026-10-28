"""Audit saved development certificates, budgets, hashes and prediction labels."""

from dataclasses import asdict
import json
from pathlib import Path
import sys

from advanced_features import extract_advanced, reduce_instance
from features import FeatureConfig, extract
from run_development import CONFIG, VARIANTS, split_for, summary_for
from run_pilot import check, sha


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def normalized(value):
    return json.loads(json.dumps(value))


def manifest(directory):
    hashes = json.loads((directory / "artifact_hashes.json").read_text())
    for name, digest in hashes.items():
        if sha(directory / name) != digest:
            raise AssertionError(f"hash mismatch: {directory / name}")
    return hashes


def validate(data):
    hashes = manifest(data)
    protocol = json.loads((data / "protocol.json").read_text())
    if protocol["config"] != CONFIG:
        raise AssertionError("development configuration changed")
    for name, digest in protocol["source_hashes"].items():
        if sha(data / "sources" / name) != digest:
            raise AssertionError(f"source snapshot mismatch: {name}")
    lists, cases, runs = rows(data / "lists.jsonl"), rows(data / "cases.jsonl"), rows(data / "runs.jsonl")
    by_list, by_case = {r["list_id"]: r for r in lists}, {r["case_id"]: r for r in cases}
    if len(by_list) != len(lists) or len(by_case) != len(cases):
        raise AssertionError("duplicate IDs")
    config = FeatureConfig(**CONFIG["features"])
    original = {}
    for row in lists:
        base = extract(row["weights"], config)
        advanced = extract_advanced(row["weights"], config, base=base,
                                    max_steps=CONFIG["max_progression_steps"])
        original[row["list_id"]] = (base, advanced)
        if list(base.values) != row["original_features"] or list(advanced.values) != row["progression_features"]:
            raise AssertionError("list feature mismatch")
        if normalized([asdict(c) for c in base.certificates]) != row["base_certificates"]:
            raise AssertionError("base certificate mismatch")
        if normalized(asdict(advanced.progression) if advanced.progression else None) != row["progression_certificate"]:
            raise AssertionError("progression certificate mismatch")
        if row["split"] != split_for(row["n"], row["family"], row["replicate"]):
            raise AssertionError("list split mismatch")
    for case in cases:
        source = by_list[case["list_id"]]
        weights = source["weights"]
        if case["split"] != source["split"]:
            raise AssertionError("target split leakage")
        kernel = reduce_instance(weights, case["target"])
        recorded_kernel = dict(case["kernel"])
        recorded_kernel.pop("seconds")
        expected_kernel = asdict(kernel)
        expected_kernel.pop("seconds")
        if normalized(expected_kernel) != recorded_kernel:
            raise AssertionError("kernel mismatch")
        target_base = extract(kernel.weights, config)
        target_advanced = extract_advanced(kernel.weights, config, base=target_base,
                                          max_steps=CONFIG["max_progression_steps"])
        obj = dict(zip(VARIANTS, original[case["list_id"]] + (target_base, target_advanced)))
        for variant, features in obj.items():
            if list(features.values) != case["features"][variant] or features.work != case["feature_work"][variant]:
                raise AssertionError("case feature mismatch")
        mask = case["oracle_mask"]
        if (mask is not None) != (case["truth"] == "yes"):
            raise AssertionError("oracle truth mismatch")
        if mask is not None and (mask < 0 or mask >> len(weights) or
                sum(w for i, w in enumerate(weights) if mask >> i & 1) != case["target"]):
            raise AssertionError("invalid oracle witness")
    run_index = {}
    for run in runs:
        key = run["case_id"], run["policy"]
        if key in run_index:
            raise AssertionError("duplicate policy run")
        run_index[key] = run
        case = by_case[run["case_id"]]
        check(by_list[case["list_id"]]["weights"], case["target"], case["truth"] == "yes", run)
        expected_feature_work = (case["feature_work"][run["policy"]]
                                 if run["policy"] != "common" and case["kernel"]["status"] == "unresolved" else 0)
        if run["feature_work"] != expected_feature_work or run["preprocess_work"] != case["kernel"]["work"]:
            raise AssertionError("cost charge mismatch")
        if run["work"] != expected_feature_work + run["preprocess_work"] + sum(a["work"] for a in run["attempts"]):
            raise AssertionError("work accounting mismatch")
        if not run["extraction_exhausted"] and run["work"] > case["budget"]:
            raise AssertionError("budget overrun")
        if run["status"] == "yes" and run["witness"] is None:
            if not run["attempts"] or run["attempts"][-1].get("reason") != "decision_only":
                raise AssertionError("missing witness outside bitset decision")
    if len(runs) != len(cases) * (len(VARIANTS) + 1):
        raise AssertionError("missing policy runs")
    if summary_for(lists, cases, runs) != json.loads((data / "summary.json").read_text()):
        raise AssertionError("summary mismatch")
    print(f"Validated {len(lists)} lists, {len(cases)} reductions/five-feature variants, "
          f"{len(runs)} exact-policy runs and all data/source hashes.")

    # Optional ML validation requires the pinned ML dependencies.
    from fit_development import metrics
    for subdir in ("ml", "end_to_end"):
        directory = data / subdir
        manifest(directory)
        fit_protocol = json.loads((directory / "fit_protocol.json").read_text())
        if fit_protocol["input_hashes"] != hashes:
            raise AssertionError("model used different input data")
        if subdir == "ml":
            if sha(directory / "fit_development.py") != fit_protocol["source_hash"]:
                raise AssertionError("fit source snapshot mismatch")
        else:
            for name, digest in fit_protocol["source_hashes"].items():
                if sha(directory / name) != digest:
                    raise AssertionError("end-to-end source snapshot mismatch")
        predictions = rows(directory / "predictions.jsonl")
        groups = {}
        for row in predictions:
            case = by_case[row["case_id"]]
            task = "common" if subdir == "ml" else row["task"]
            label = int(run_index[(row["case_id"], task)]["status"] != "unresolved")
            if row["label"] != label or row["split"] != case["split"] or row["list_id"] != case["list_id"]:
                raise AssertionError("prediction label/group mismatch")
            if not all(0 <= row[name] <= 1 for name in ("raw", "calibrated")):
                raise AssertionError("invalid predicted probability")
            key = (task, row["model"], row["split"])
            groups.setdefault(key, []).append(row)
        saved = json.loads((directory / "metrics.json").read_text())
        for (task, model, split), group in groups.items():
            if len({r["case_id"] for r in group}) != len(group):
                raise AssertionError("duplicate model prediction")
            expected_n = sum(c["split"] == split for c in cases)
            if len(group) != expected_n:
                raise AssertionError("missing model predictions")
            score = saved["models"][model][split] if subdir == "ml" else saved["tasks"][task][model][split]
            for kind in ("raw", "calibrated"):
                if metrics([r["label"] for r in group], [r[kind] for r in group]) != score[kind]:
                    raise AssertionError("saved probability metric mismatch")
        print(f"Validated {len(predictions)} {subdir} predictions and their raw/calibrated metrics.")


if __name__ == "__main__":
    validate(Path(sys.argv[1]))
