"""Check the saved classifier study, including exact arithmetic and all work pools."""
from collections import defaultdict
from datetime import datetime, timezone
import argparse
import json
from math import log1p
from pathlib import Path

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from Structural_Geometry_Subset_Sum.classifier_features import (ARMS, POLICIES,
    MODEL_FOR, base_features, design, geometry_features, probabilities,
    pending_after_shared_checks, reference)
from Structural_Geometry_Subset_Sum.classifier_pool import run_pool, witness_cost
from Structural_Geometry_Subset_Sum.classifier_study import (CONFIG, FAMILIES,
    aggregate_pools, predictive_summary, report, verify)
from Structural_Geometry_Subset_Sum.compat import (independent_halves,
    independent_query, input_length, reduce_instance)
from Structural_Geometry_Subset_Sum.study import (check_manifest, read_jsonl,
    save_json, sha, signature)


def canonical(value):
    return json.loads(json.dumps(value))


def stable(value):
    if isinstance(value, dict):
        return {k:stable(v) for k, v in value.items() if
            k not in ("seconds", "recorded_feature_seconds")}
    if isinstance(value, (list, tuple)):
        return [stable(v) for v in value]
    return value


def arithmetic(case):
    saved = case["geometry"]
    g = saved["geometry"]
    if g is None:
        assert saved["values"] == [0., 0., 0.] and not saved["exact_no"]
    else:
        weights, target = case["kernel"]["weights"], case["kernel"]["target"]
        divisor, base = g["divisor"], g["base"]
        assert len(weights) == len(g["p"]) == len(g["r"])
        assert all(w == divisor*(base*p+r) for w, p, r in zip(weights, g["p"], g["r"]))
        assert target == divisor*g["target"]
        r_low, r_high = sum(min(0, r) for r in g["r"]), sum(max(0, r) for r in g["r"])
        lo = max(0, (g["target"]-r_high+base-1)//base)
        hi = min(sum(g["p"]), (g["target"]-r_low)//base)
        count, area = max(0, hi-lo+1), max(0, hi+1)*(r_high-r_low+1)
        assert (r_low, r_high, lo, hi) == (g["r_min"], g["r_max"], g["q_low"], g["q_high"])
        assert (count, area) == (g["q_count"], g["dp_bits"])
        expected = [log1p((r_high-r_low)/base), log1p(count), log1p(area)]
        np.testing.assert_array_equal(saved["values"], expected)
        assert saved["exact_no"] == (count == 0)
        if count == 0:
            assert case["truth"] == "no"
    distinct = set(case["kernel"]["weights"])
    sums = {a+b for a in distinct for b in distinct}
    doubling = case["doubling"]
    assert doubling["distinct"] == len(distinct)
    assert doubling["sumset_size"] == len(sums)
    assert doubling["value"] == (len(sums)/len(distinct) if distinct else 0)


def refit(development, bundles):
    y = np.array([c["label"] for c in development])
    train = np.array([c["split"] == "train" for c in development])
    for arm in ARMS:
        x = np.array([design(c, arm) for c in development])
        model = make_pipeline(StandardScaler(), LogisticRegression(**CONFIG["logistic"]))
        model.fit(x[train], y[train])
        raw = np.clip(model.predict_proba(x[~train])[:, 1], 1e-6, 1-1e-6)
        calibrator = LogisticRegression(**CONFIG["logistic"]).fit(
            np.log(raw/(1-raw)).reshape(-1, 1), y[~train])
        np.testing.assert_allclose(model[-1].coef_, bundles[arm]["model"][-1].coef_, atol=1e-12, rtol=0)
        np.testing.assert_allclose(calibrator.coef_, bundles[arm]["calibrator"].coef_, atol=1e-12, rtol=0)
        rebuilt = dict(model=model, calibrator=calibrator, dimensions=x.shape[1])
        np.testing.assert_allclose(probabilities(rebuilt, x), probabilities(bundles[arm], x), atol=1e-12, rtol=0)


def audit(output):
    protocol = verify(output)
    for name in ("development_hashes.json", "model_hashes.json", "test_hashes.json", "evaluation_hashes.json"):
        check_manifest(output, name)
    model_freeze = json.loads((output/"model_freeze.json").read_text())
    test_start = json.loads((output/"test.started.json").read_text())
    assert protocol["frozen_at_utc"] < model_freeze["frozen_at_utc"] < test_start["utc"]
    assert test_start["model_sha256"] == model_freeze["model_sha256"] == sha(output/"models.joblib")
    development = read_jsonl(output/"development_cases.jsonl")
    cases = read_jsonl(output/"test_cases.jsonl")
    all_cases = development+cases
    lists = read_jsonl(output/"lists.jsonl")
    assert len(lists) == len(CONFIG["sizes"])*len(FAMILIES)*sum(CONFIG["replicates"].values())
    assert len(all_cases) == 3*len(lists)
    assert len({c["case_id"] for c in all_cases}) == len(all_cases)
    seen = set(protocol["prior_signatures"])
    by_list = defaultdict(list)
    for case in all_cases:
        by_list[case["list_id"]].append(case)
    for i, row in enumerate(lists):
        code = signature(row["weights"])
        assert code not in seen
        seen.add(code)
        group = by_list[row["list_id"]]
        assert len(group) == 3
        assert {c["split"] for c in group} == {row["split"]}
        halves = independent_halves(row["weights"])
        for case in group:
            mask = independent_query(halves, case["target"])
            assert ("yes" if mask is not None else "no") == case["truth"]
            assert mask == case["oracle_mask"]
            kernel = reduce_instance(case["weights"], case["target"])
            assert stable(as_record(kernel)) == stable(case["kernel"])
            assert case["budget"] == 8*input_length(case["weights"], case["target"])
            ref = reference(case["weights"], case["target"], kernel, case["budget"])
            assert stable(ref) == stable(case["reference"])
            assert case["label"] == int(ref["status"] != "unresolved")
            base = base_features(case["weights"], case["target"], kernel)
            assert stable(base) == stable(case["base"])
            assert stable(geometry_features(kernel.weights, kernel.target)) == stable(case["geometry"])
            arithmetic(case)
        del halves
        if (i+1) % 30 == 0:
            print(f"audited exact truths/features/labels: {i+1}/{len(lists)} lists", flush=True)
    bundles = joblib.load(output/"models.joblib")
    refit(development, bundles)
    summary, records = predictive_summary(cases, bundles)
    assert canonical(summary) == json.loads((output/"prediction_metrics.json").read_text())
    assert canonical(records) == read_jsonl(output/"predictions.jsonl")
    predictions = {r["case_id"]:r["probabilities"] for r in records}
    case_map = {c["case_id"]:c for c in cases}
    groups = defaultdict(list)
    for case in cases:
        groups[case["cohort"]].append(case)
    rows = read_jsonl(output/"pool_runs.jsonl")
    assert len(rows) == 2*len(groups)*2*3*len(POLICIES)
    keys = [(r["mode"], r["cohort"], r["fraction"], r["repeat"], r["policy"]) for r in rows]
    assert len(set(keys)) == len(keys)
    replays = 0
    for row in rows:
        assert row["solved"] == len(row["solved_ids"]) == len(set(row["solved_ids"]))
        assert row["solved_ids"] == [e["case_id"] for e in row["events"] if e["status"] != "unresolved"]
        assert set(row["solved_ids"]).issubset(case_map)
        for event in row["events"]+row["attempts"]:
            case = case_map[event["case_id"]]
            status = event.get("returned_status", event["status"])
            if status != "unresolved":
                assert status == case["truth"]
                witness_cost(case["weights"], case["target"], status, event.get("witness"))
            if event.get("source") == "aggregate_gap":
                assert row["policy"] != "cheap15" and case["geometry"]["exact_no"]
            if row["mode"] == "time" and "source" in event:
                assert event["accepted_at_seconds"] <= row["budget"]
            if row["mode"] == "time" and event.get("status") != "unresolved" and "within_case_deadline" in event:
                assert event["within_case_deadline"] and event["seconds"] <= event["allowance_seconds"]
        if row["mode"] == "work":
            assert row["spent"] <= row["budget"] and row["spent"] == sum(row["costs"].values())
            replay = run_pool(groups[row["cohort"]], bundles, predictions, row["policy"], "work",
                row["fraction"], row["repeat"], CONFIG["seed"], CONFIG["per_case_seconds"])
            assert canonical(replay) == row
            replays += 1
        else:
            assert sum(row["costs"].values()) <= row["spent"]+1e-6
    pools = aggregate_pools(rows)
    assert canonical(pools) == json.loads((output/"pool_summary.json").read_text())
    assert report(summary, pools, cases) == (output/"REPORT.md").read_text(encoding="utf-8")
    record = dict(status="passed", audited_at_utc=datetime.now(timezone.utc).isoformat(),
        auditor_sha256=sha(Path(__file__)), lists=len(lists), development_cases=len(development),
        test_cases=len(cases), pending_test_cases=sum(pending_after_shared_checks(c) for c in cases),
        pool_runs=len(rows), deterministic_pool_replays=replays,
        checks="source/input/model/data/result hashes; exact truth; descriptor arithmetic; labels; refits/calibration; predictions; summaries; paid answers/deadlines; all deterministic pools")
    destination = output/"VALIDATION.json"
    if destination.exists():
        old = json.loads(destination.read_text())
        assert old["status"] == "passed" and old["auditor_sha256"] == record["auditor_sha256"]
        print("All checks passed again; original validation record preserved", flush=True)
    else:
        save_json(destination, record)
    print(json.dumps(record, indent=2), flush=True)


def as_record(kernel):
    from dataclasses import asdict
    return asdict(kernel)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        audit(args.output.resolve())
