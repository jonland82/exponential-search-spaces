"""Validate saved pilot hashes, certificates, answers and budget bookkeeping."""

from dataclasses import asdict
import json
from pathlib import Path
import sys

from features import FeatureConfig, extract, input_length
from run_pilot import CONFIG, check, sha, summarize


def read_rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def validate(output):
    protocol = json.loads((output / "protocol.json").read_text(encoding="utf-8"))
    if sha(output / "protocol.json") != (output / "protocol.sha256").read_text().strip():
        raise AssertionError("protocol hash mismatch")
    if protocol["config"] != CONFIG:
        raise AssertionError("validator configuration differs from recorded pilot")
    artifacts = json.loads((output / "artifact_hashes.json").read_text())
    for name, digest in artifacts.items():
        if sha(output / name) != digest:
            raise AssertionError(f"artifact hash mismatch: {name}")
    for name, digest in protocol["source_hashes"].items():
        if sha(output / "sources" / name) != digest:
            raise AssertionError(f"source snapshot hash mismatch: {name}")
    lists = read_rows(output / "lists.jsonl")
    cases = read_rows(output / "cases.jsonl")
    runs = read_rows(output / "runs.jsonl")
    by_list = {row["list_id"]: row for row in lists}
    by_case = {row["case_id"]: row for row in cases}
    if len(by_list) != len(lists) or len(by_case) != len(cases):
        raise AssertionError("duplicate IDs")
    for row in lists:
        features = extract(row["weights"], FeatureConfig(**protocol["config"]["features"]))
        if list(features.values) != row["features"] or features.work != row["feature_work"]:
            raise AssertionError("feature mismatch")
        expected = json.loads(json.dumps([asdict(c) for c in features.certificates]))
        if expected != row["certificates"] or features.divisor != row["divisor"]:
            raise AssertionError("certificate mismatch")
    for case in cases:
        weights = by_list[case["list_id"]]["weights"]
        if case["input_length"] != input_length(weights, case["target"]):
            raise AssertionError("input-length mismatch")
        mask = case["oracle_witness_mask"]
        if (mask is not None) != (case["truth"] == "yes"):
            raise AssertionError("oracle truth mismatch")
        if mask is not None and (mask < 0 or mask >> len(weights) or
                sum(w for i, w in enumerate(weights) if mask >> i & 1) != case["target"]):
            raise AssertionError("invalid oracle witness")
    run_ids = set()
    for row in runs:
        case = by_case[row["case_id"]]
        weights = by_list[case["list_id"]]["weights"]
        key = (row["case_id"], row["multiplier"], row["policy"])
        if key in run_ids:
            raise AssertionError("duplicate run")
        run_ids.add(key)
        check(weights, case["target"], case["truth"] == "yes", row)
        charge = by_list[case["list_id"]]["feature_work"] if row["policy"] == "with_features" else 0
        if row["feature_charge"] != charge or row["budget"] != row["multiplier"] * case["input_length"]:
            raise AssertionError("budget or charge mismatch")
        if row["total_work"] != charge + row["work"] or row["work"] != sum(a["work"] for a in row["attempts"]):
            raise AssertionError("work mismatch")
        if row["solved"] != (row["status"] != "unresolved"):
            raise AssertionError("completion label mismatch")
        if charge < row["budget"] and row["total_work"] > row["budget"]:
            raise AssertionError("solver overran budget")
        if charge >= row["budget"] and (row["solved"] or row["attempts"]):
            raise AssertionError("solver ran after feature budget exhaustion")
    expected_runs = len(cases) * len(CONFIG["budget_multipliers"]) * len(CONFIG["policies"])
    if len(runs) != expected_runs:
        raise AssertionError("missing runs")
    if summarize(lists, cases, runs) != json.loads((output / "summary.json").read_text()):
        raise AssertionError("summary mismatch")
    print(f"Validated {len(lists)} feature certificates, {len(cases)} cases, {len(runs)} runs, "
          "all recorded hashes and the full summary. Saved NO truths are oracle records; "
          "this validator does not repeat full half enumeration.")


if __name__ == "__main__":
    validate(Path(sys.argv[1]))
