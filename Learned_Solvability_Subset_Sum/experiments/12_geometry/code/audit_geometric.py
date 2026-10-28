"""Corrected independent geometric audit; see results/geometric_20261028/AUDIT_NOTE.md."""
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import joblib
import numpy as np
from sklearn.cluster import KMeans
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from geometric_experiment import (ARMS, CONFIG, analyze_sample, check_hashes,
    development_data, feature_names, normalized_signature, verify)
from neighbor_experiment import pool_run, probabilities, validate_row
from priority_experiment import aggregate
from prospective_study import feature_vectors
from advanced_features import reduce_instance
from fit_development import read_jsonl
from run_pilot import check, independent_halves, independent_query, save_json, sha


def audit(output):
    protocol = verify(output)
    for manifest in ("data_hashes.json", "prediction_hashes.json", "priority_hashes.json"):
        check_hashes(output, manifest)
    assert datetime.fromisoformat(json.loads((output / "generation.started.json").read_text())["utc"]) > datetime.fromisoformat(protocol["frozen_at_utc"])
    saved = joblib.load(output / "models.joblib")
    geometry = saved["bank"]
    development, x, y, groups, train, calibration = development_data()
    tx, ty, tg = x[train], y[train], groups[train]
    assert set(tg) == set(protocol["training_lists"])
    assert set(groups[calibration]) == set(protocol["calibration_lists"])
    assert not set(tg) & set(groups[calibration])
    np.testing.assert_array_equal(geometry.raw, tx)
    np.testing.assert_array_equal(geometry.y, ty)
    np.testing.assert_array_equal(geometry.groups, tg)
    mean, scale = tx.mean(axis=0), tx.std(axis=0)
    scale[scale == 0] = 1
    np.testing.assert_allclose(geometry.scaler.mean_, mean, rtol=0, atol=1e-12)
    np.testing.assert_allclose(geometry.scaler.scale_, scale, rtol=0, atol=1e-12)
    z = (tx-mean)/scale

    def refit_centers(exclude=None):
        centers = []
        for label in (0, 1):
            ids = [i for i in range(len(tx)) if ty[i] == label and tg[i] != exclude]
            counts = {g:sum(tg[i] == g for i in ids) for g in set(tg[ids])}
            weights = [1/counts[tg[i]] for i in ids]
            k = min(CONFIG["prototypes_per_class"], len(np.unique(z[ids], axis=0)))
            with threadpool_limits(limits=1):
                fitted = KMeans(n_clusters=k, **CONFIG["kmeans"]).fit(z[ids], sample_weight=weights)
            centers.append(fitted.cluster_centers_)
        return centers

    all_centers = refit_centers()
    for expected, actual in zip(all_centers, geometry.centers):
        np.testing.assert_allclose(expected, actual, atol=1e-12, rtol=0)

    def distances(query, centers):
        return np.array([[min(np.linalg.norm((row-mean)/scale-c) for c in label_centers)
            for label_centers in centers] for row in query])

    out_of_list = np.empty((len(tx), 2))
    for group in sorted(set(tg)):
        ids = np.flatnonzero(tg == group)
        out_of_list[ids] = distances(tx[ids], refit_centers(group))

    def make_design(rows, arm, d):
        parts = [rows]
        if arm in ("prototypes", "combined"):
            parts.append(d)
        if arm in ("interactions", "combined"):
            standardized = (rows-mean)/scale
            parts.append(np.array([[row[i]*row[j] for i in range(5) for j in range(i+1, 5)]
                for row in standardized]))
        return np.column_stack(parts)

    training_rows = read_jsonl(output / "training_features.jsonl")
    assert [r["case_id"] for r in training_rows] == [c["case_id"] for c, keep in zip(development, train) if keep]
    assert [r["label"] for r in training_rows] == ty.tolist()
    cx, cy = x[calibration], y[calibration]
    cd = distances(cx, all_centers)
    for arm in ARMS:
        features = make_design(tx, arm, out_of_list)
        np.testing.assert_allclose(features, [r["designs"][arm] for r in training_rows], atol=1e-12, rtol=0)
        assert features.shape[1] == len(feature_names(arm))
        with threadpool_limits(limits=1):
            fitted = make_pipeline(StandardScaler(), LogisticRegression(**CONFIG["logistic"])).fit(features, ty)
        model = saved["bundles"][arm]["model"]
        actual = model if arm == "baseline" else model.fitted
        np.testing.assert_allclose(fitted[-1].coef_, actual[-1].coef_, atol=1e-9, rtol=0)
        raw = np.clip(fitted.predict_proba(make_design(cx, arm, cd))[:, 1], 1e-6, 1-1e-6)
        calibrator = LogisticRegression(**CONFIG["logistic"]).fit(np.log(raw/(1-raw)).reshape(-1, 1), cy)
        np.testing.assert_allclose(calibrator.coef_, saved["bundles"][arm]["calibrator"].coef_, atol=1e-9, rtol=0)

    cases = read_jsonl(output / "cases.jsonl")
    lists = read_jsonl(output / "lists.jsonl")
    refs = {r["case_id"]:r for r in read_jsonl(output / "references.jsonl")}
    assert len(cases) == len(refs) == 1152 and len(lists) == 288
    assert len({c["case_id"] for c in cases}) == len(cases)
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
    fresh_x = np.array([c["vectors"]["hybrid"] for c in cases])
    fd = distances(fresh_x, all_centers)
    np.testing.assert_allclose(fd, [r["prototype_distances"] for r in records], atol=1e-10, rtol=0)
    for arm in ARMS:
        bundle = saved["bundles"][arm]
        model = bundle["model"] if arm == "baseline" else bundle["model"].fitted
        raw = np.clip(model.predict_proba(make_design(fresh_x, arm, fd))[:, 1], 1e-6, 1-1e-6)
        p = bundle["calibrator"].predict_proba(np.log(raw/(1-raw)).reshape(-1, 1))[:, 1]
        np.testing.assert_allclose(p, [r["probabilities"][arm] for r in records], atol=1e-10, rtol=0)
        unscaled = [r for c, r in zip(cases, records) if c["scale"] == 1]
        confusion = [[0, 0], [0, 0]]
        for row in unscaled:
            confusion[1-row["label"]][int(row["probabilities"][arm] < .5)] += 1
        assert confusion == result["models"]["unscaled"][arm]["all"]["confusion_easy_hard"]
    predictions = {r["case_id"]:r for r in records}
    cohorts = defaultdict(list)
    for case in cases:
        cohorts[case["cohort"]].append(case)
    rows = read_jsonl(output / "priority_runs.jsonl")
    expected_runs = 2*len(cohorts)*2*3*len(CONFIG["pool_policies"])
    assert len(rows) == expected_runs
    assert len({(r["mode"], r["cohort"], r["fraction"], r["repeat"], r["policy"]) for r in rows}) == expected_runs
    for row in rows:
        pool = cohorts[row["cohort"]]
        validate_row(row, pool, refs)
        if row["mode"] == "work":
            assert row == pool_run(pool, refs, saved, predictions, row["policy"], "work", row["fraction"], row["repeat"])
    assert aggregate(rows) == json.loads((output / "priority_summary.json").read_text())
    verify(output)
    save_json(output / "VALIDATION.json", dict(status="passed", cases=len(cases), base_lists=144,
        pool_runs=len(rows), counter_replays_checked=len(rows)//2, independent_geometry=True,
        independent_model_refits=True, oracle_replayed=True, predictions_reproduced=True,
        hashes_verified=True, auditor_sha256=sha(Path(__file__)), utc=datetime.now(timezone.utc).isoformat()))
    print(f"VALIDATED: 1152 cases, 144 base lists, {len(rows)} pools; independent geometry/refits and exact truth.", flush=True)


if __name__ == "__main__":
    audit(Path(sys.argv[1]))
