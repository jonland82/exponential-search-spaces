"""Independent RFE/refit audit and exact fresh-data / paid-trace validation."""
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from advanced_features import reduce_instance
from fit_development import read_jsonl
from geometric_models import INTERACTIONS
from neighbor_experiment import pool_run, probabilities, validate_row
from priority_experiment import aggregate
from prospective_study import feature_vectors
from pruning_experiment import (ARMS, CONFIG, PREVIOUS, analyze_sample, check_hashes,
    development_data, normalized_signature, verify)
from pruning_models import LOGISTIC
from run_pilot import check, independent_halves, independent_query, save_json, sha


def audit(output):
    protocol = verify(output)
    for manifest in ("data_hashes.json", "prediction_hashes.json", "priority_hashes.json"):
        check_hashes(output, manifest)
    assert datetime.fromisoformat(json.loads((output / "generation.started.json").read_text())["utc"]) > datetime.fromisoformat(protocol["frozen_at_utc"])
    saved = joblib.load(output / "models.joblib")
    selection = json.loads((output / "selection.json").read_text())
    development, x, y, groups, train, calibration = development_data()
    assert set(groups[train]) == set(protocol["training_lists"])
    assert set(groups[calibration]) == set(protocol["calibration_lists"])
    assert not set(groups[train]) & set(groups[calibration])
    previous_training = read_jsonl(PREVIOUS / "training_features.jsonl")
    assert [r["case_id"] for r in previous_training] == [c["case_id"] for c, keep in zip(development, train) if keep]
    tx = np.array([r["designs"]["combined"] for r in previous_training])
    np.testing.assert_array_equal(y[train], [r["label"] for r in previous_training])
    active, removed, selected = list(range(27)), [], {}
    for row in selection["trace"]:
        assert row["active"] == active
        with threadpool_limits(limits=1):
            fitted = make_pipeline(StandardScaler(), LogisticRegression(**LOGISTIC)).fit(tx[:, active], y[train])
        coefficients = fitted[-1].coef_[0]
        np.testing.assert_allclose(coefficients, row["coefficients"], atol=1e-12, rtol=0)
        assert abs(float(fitted[-1].intercept_[0])-row["intercept"]) < 1e-12
        if len(active) in (5, 10):
            selected[f"top{len(active)}"] = active.copy()
        if len(active) == 5:
            assert row["removed"] is None
            final_order = sorted(active, key=lambda i:(-abs(coefficients[active.index(i)]), i))
            break
        drop = min(zip(active, coefficients), key=lambda pair:(abs(pair[1]), pair[0]))[0]
        assert row["removed"] == drop
        removed.append(drop)
        active.remove(drop)
    assert len(selection["trace"]) == 23
    assert selected == selection["selected"] == saved["bank"].selected
    assert selection["ranking"] == final_order+list(reversed(removed))
    assert set(selected["top5"]) <= set(selected["top10"])
    for arm, columns in selected.items():
        assert selection["selected_names"][arm] == [selection["candidate_names"][i] for i in columns]
        assert selection["base_dependencies"][arm] == saved["bank"].dependencies(arm)

    geometry = saved["bank"].geometry
    feature_mean, feature_scale = geometry.scaler.mean_, geometry.scaler.scale_

    def full_design(rows):
        z = (rows-feature_mean)/feature_scale
        distance_rows = [[min(np.linalg.norm(row-center) for center in centers) for centers in geometry.centers] for row in z]
        products = [[row[i]*row[j] for i, j in INTERACTIONS] for row in z]
        return np.column_stack((rows, distance_rows, products))

    training_rows = read_jsonl(output / "training_features.jsonl")
    assert [r["case_id"] for r in training_rows] == [r["case_id"] for r in previous_training]
    for arm, columns in selected.items():
        np.testing.assert_array_equal(tx[:, columns], [r["designs"][arm] for r in training_rows])
        with threadpool_limits(limits=1):
            fitted = make_pipeline(StandardScaler(), LogisticRegression(**LOGISTIC)).fit(tx[:, columns], y[train])
        bundle = saved["bundles"][arm]
        np.testing.assert_allclose(fitted[-1].coef_, bundle["model"].fitted[-1].coef_, atol=1e-12, rtol=0)
        raw = np.clip(fitted.predict_proba(full_design(x[calibration])[:, columns])[:, 1], 1e-6, 1-1e-6)
        calibrator = LogisticRegression(**LOGISTIC).fit(np.log(raw/(1-raw)).reshape(-1, 1), y[calibration])
        np.testing.assert_allclose(calibrator.coef_, bundle["calibrator"].coef_, atol=1e-10, rtol=0)
    old_models = joblib.load(PREVIOUS / "models.joblib")
    for arm in ("baseline", "combined"):
        np.testing.assert_array_equal(probabilities(saved["bundles"][arm], x), probabilities(old_models["bundles"][arm], x))

    cases = read_jsonl(output / "cases.jsonl")
    lists = read_jsonl(output / "lists.jsonl")
    refs = {r["case_id"]:r for r in read_jsonl(output / "references.jsonl")}
    assert len(cases) == len(refs) == 1152 and len(lists) == 288
    assert len({c["case_id"] for c in cases}) == 1152
    signatures = {normalized_signature(r["weights"]) for r in lists}
    assert len(signatures) == 144 and not signatures & set(protocol["prior_signatures"])
    pairs, by_base = {}, defaultdict(list)
    for case in cases:
        weights, target = case["weights"], case["target"]
        kernel = reduce_instance(weights, target)
        expected, actual = asdict(kernel), dict(case["kernel"])
        expected.pop("seconds"); actual.pop("seconds")
        assert json.loads(json.dumps(expected)) == actual
        vectors, work, _, reuse = feature_vectors(weights, target, kernel)
        assert vectors == case["vectors"] and work == case["feature_work"]
        assert json.loads(json.dumps(reuse)) == case["reuse"]
        check(weights, target, case["truth"] == "yes", refs[case["case_id"]])
        check(weights, target, case["truth"] == "yes", reuse)
        assert refs[case["case_id"]]["work"] <= case["budget"]
        encoding_factor = case["scale"]
        assert all(w % encoding_factor == 0 for w in weights) and target % encoding_factor == 0
        pair = (tuple(w//encoding_factor for w in weights), target//encoding_factor, case["truth"], case["oracle_mask"])
        assert pairs.setdefault((case["base_list_id"], case["target_rule"]), pair) == pair
        if encoding_factor == 1:
            by_base[case["base_list_id"]].append(case)
    for index, group in enumerate(by_base.values()):
        halves = independent_halves(group[0]["weights"])
        for case in group:
            assert independent_query(halves, case["target"]) == case["oracle_mask"]
        del halves
        if index % 24 == 0:
            print(f"oracle audit: {index+1}/144 base lists", flush=True)
    result, records = analyze_sample(cases, list(refs.values()), saved)
    assert result == json.loads((output / "prediction_metrics.json").read_text())
    assert records == read_jsonl(output / "predictions.jsonl")
    fresh = np.array([c["vectors"]["hybrid"] for c in cases])
    expanded = full_design(fresh)
    np.testing.assert_allclose(expanded[:, 15:17], [r["prototype_distances"] for r in records], atol=1e-10, rtol=0)
    np.testing.assert_allclose(expanded[:, 17:], [r["interactions"] for r in records], atol=1e-10, rtol=0)
    for arm, columns in selected.items():
        np.testing.assert_allclose(saved["bank"].transform(fresh, arm), expanded[:, columns], atol=1e-10, rtol=0)
        bundle = saved["bundles"][arm]
        raw = np.clip(bundle["model"].fitted.predict_proba(expanded[:, columns])[:, 1], 1e-6, 1-1e-6)
        probability = bundle["calibrator"].predict_proba(np.log(raw/(1-raw)).reshape(-1, 1))[:, 1]
        np.testing.assert_allclose(probability, [r["probabilities"][arm] for r in records], atol=1e-10, rtol=0)
    for arm in ARMS:
        confusion = [[0, 0], [0, 0]]
        for case, row in zip(cases, records):
            if case["scale"] == 1:
                confusion[1-row["label"]][int(row["probabilities"][arm] < .5)] += 1
        assert confusion == result["models"]["unscaled"][arm]["all"]["confusion_easy_hard"]
    predictions = {r["case_id"]:r for r in records}
    cohorts = defaultdict(list)
    for case in cases:
        cohorts[case["cohort"]].append(case)
    rows = read_jsonl(output / "priority_runs.jsonl")
    assert len(rows) == 576
    assert len({(r["mode"], r["cohort"], r["fraction"], r["repeat"], r["policy"]) for r in rows}) == 576
    for row in rows:
        pool = cohorts[row["cohort"]]
        validate_row(row, pool, refs)
        if row["mode"] == "work":
            assert row == pool_run(pool, refs, saved, predictions, row["policy"], "work", row["fraction"], row["repeat"])
    assert aggregate(rows) == json.loads((output / "priority_summary.json").read_text())
    verify(output)
    save_json(output / "VALIDATION.json", dict(status="passed", cases=1152, base_lists=144, pool_runs=576,
        counter_replays_checked=288, selection_reproduced=True, independent_model_refits=True,
        selected_transforms_checked=True, original_controls_unchanged=True, oracle_replayed=True,
        hashes_verified=True, auditor_sha256=sha(Path(__file__)), utc=datetime.now(timezone.utc).isoformat()))
    print("VALIDATED: RFE/selected models, 1152 cases, 144 base lists, 576 pools and 288 counter replays.", flush=True)


if __name__ == "__main__":
    audit(Path(sys.argv[1]))
