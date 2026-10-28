"""Validate paired cost labels, fitting, all counter runs and paid pool traces."""
from collections import defaultdict
from datetime import datetime, timezone
import argparse
import json
from pathlib import Path

import joblib
import numpy as np
from threadpoolctl import threadpool_limits

from Structural_Geometry_Subset_Sum.audit import audit_event
from Structural_Geometry_Subset_Sum.classifier_audit import canonical
from Structural_Geometry_Subset_Sum.compat import independent_halves, independent_query, reduce_instance
from Structural_Geometry_Subset_Sum.cost_gate import POLICIES, capped_cost, gate_score, solve_gate
from Structural_Geometry_Subset_Sum.cost_gate_study import (CONFIG, FAMILIES, check_answer,
    fit_model, paired_records, pool, report, select_threshold, summarize, verify)
from Structural_Geometry_Subset_Sum.study import check_manifest, read_jsonl, save_json, sha, signature


def stable(value):
    if isinstance(value, dict):
        return {k:stable(v) for k, v in value.items() if k not in
                ("seconds", "phase_seconds", "overshoot_seconds")}
    if isinstance(value, (list, tuple)):
        return [stable(v) for v in value]
    return value


def certificates(case, result):
    check_answer(case, result)
    geometry = result["geometry"]
    if geometry is not None:
        kernel = reduce_instance(case["weights"], case["target"])
        event = dict(geometry=geometry, weights=kernel.weights, target=kernel.target,
            status="no" if result["reason"] == "aggregate_gap" else "unresolved",
            reason=result["reason"], witness=None)
        audit_event(event, CONFIG["solver"])
    if result["checker_event"] is not None:
        audit_event(result["checker_event"], CONFIG["solver"])
        assert result["check_taken"] and result["decision_eligible"]


def audit(output):
    protocol = verify(output)
    for name in ("development_hashes.json", "model_hashes.json", "test_hashes.json", "evaluation_hashes.json"):
        check_manifest(output, name)
    frozen = json.loads((output/"model_freeze.json").read_text())
    test_start = json.loads((output/"test.started.json").read_text())
    assert protocol["frozen_at_utc"] < frozen["utc"] < test_start["utc"]
    assert test_start["model_sha256"] == frozen["model_sha256"] == sha(output/"gate.json")
    assert not set(frozen["training_lists"]) & set(frozen["calibration_lists"])
    development = read_jsonl(output/"development_cases.jsonl")
    cases = read_jsonl(output/"test_cases.jsonl")
    all_cases = development+cases
    case_map = {c["case_id"]:c for c in all_cases}
    lists = read_jsonl(output/"lists.jsonl")
    expected_lists = len(FAMILIES)*len(CONFIG["sizes"])*sum(CONFIG["replicates"].values())
    assert len(lists) == expected_lists and len(case_map) == len(all_cases) == 3*len(lists)
    seen = set(protocol["prior_signatures"])
    grouped = defaultdict(list)
    for case in all_cases:
        grouped[case["list_id"]].append(case)
    for index, row in enumerate(lists):
        code = signature(row["weights"])
        assert code not in seen
        seen.add(code)
        group = grouped[row["list_id"]]
        assert len(group) == 3 and {c["split"] for c in group} == {row["split"]}
        assert all(c["weights"] == row["weights"] for c in group)
        halves = independent_halves(row["weights"])
        for case in group:
            mask = independent_query(halves, case["target"])
            assert mask == case["oracle_mask"]
            assert ("yes" if mask is not None else "no") == case["truth"]
        del halves
        if (index+1) % 48 == 0:
            print(f"independent exact truths: {index+1}/{len(lists)} lists", flush=True)
    pairs = read_jsonl(output/"development_pairs.jsonl")
    assert len(pairs) == len(development)
    for index, (case, saved) in enumerate(zip(development, pairs)):
        assert case["case_id"] == saved["case_id"]
        repeated = paired_records(case)
        assert stable(repeated) == stable(saved)
        for result in saved["runs"].values():
            certificates(case, result)
        delta = capped_cost(saved["runs"]["never"], case["budget"])-capped_cost(saved["runs"]["always"], case["budget"])
        assert (saved["saving"], saved["label"], saved["absolute_saving"]) == (delta, int(delta > 0), abs(delta))
        if saved["eligible"]:
            assert saved["runs"]["never"]["gate_features"] == saved["runs"]["always"]["gate_features"]
        if (index+1) % 144 == 0:
            print(f"paired action labels: {index+1}/{len(development)} cases", flush=True)
    model = json.loads((output/"gate.json").read_text())
    diagnostics = json.loads((output/"fit_diagnostics.json").read_text())
    rebuilt, fitted, fitting = fit_model(pairs)
    rebuilt, thresholds = select_threshold([c for c in development if c["split"] == "calibration"], rebuilt)
    assert canonical(rebuilt) == model
    assert canonical(thresholds) == diagnostics["thresholds"]
    for key, value in fitting.items():
        assert diagnostics[key] == value
    stored_fit = joblib.load(output/"fitted.joblib")
    if fitted is not None:
        np.testing.assert_array_equal(fitted[-1].coef_, stored_fit[-1].coef_)
        x = np.array([p["features"] for p in pairs if p["eligible"]])
        np.testing.assert_allclose([gate_score(model, row) for row in x], stored_fit.predict_proba(x)[:, 1], atol=1e-12, rtol=0)
    else:
        assert stored_fit is None and "constant" in model
    rows = read_jsonl(output/"counter_runs.jsonl")
    assert len(rows) == len(cases)*len(POLICIES)
    assert len({(r["case_id"], r["policy"]) for r in rows}) == len(rows)
    lookup = {}
    for index, row in enumerate(rows):
        case = case_map[row["case_id"]]
        result = row["result"]
        certificates(case, result)
        repeated = solve_gate(case["weights"], case["target"], row["policy"], max_work=case["budget"], model=model)
        assert stable(repeated) == stable(result)
        lookup[(case["case_id"], row["policy"])] = result
        if (index+1) % 576 == 0:
            print(f"test counter replay: {index+1}/{len(rows)} runs", flush=True)
    groups = defaultdict(list)
    for case in cases:
        groups[case["cohort"]].append(case)
    pools = read_jsonl(output/"pool_runs.jsonl")
    expected_pools = 2*len(groups)*len(CONFIG["pool_fractions"])*CONFIG["repeats"]*len(POLICIES)
    assert len(pools) == expected_pools
    keys = [(r["mode"],r["cohort"],r["fraction"],r["repeat"],r["policy"]) for r in pools]
    assert len(set(keys)) == len(keys)
    work_replays = 0
    for row in pools:
        accepted = []
        assert row["solved"] == len(row["solved_ids"]) == len(set(row["solved_ids"]))
        for attempt in row["attempts"]:
            case = case_map[attempt["case_id"]]
            result = attempt["result"]
            certificates(case, result)
            within = (attempt["accepted_at"] <= row["budget"] and
                (row["mode"] == "work" or result["seconds"] < attempt["allowance"]))
            assert attempt["accepted"] == within
            if row["mode"] == "work":
                assert result["work"] <= attempt["allowance"]
            if within and result["status"] != "unresolved":
                accepted.append(attempt["case_id"])
        assert accepted == row["solved_ids"]
        if row["mode"] == "work":
            assert row["spent"] == sum(a["result"]["work"] for a in row["attempts"]) <= row["budget"]
            repeated = pool(groups[row["cohort"]], row["policy"], "work", row["fraction"], row["repeat"], model, lookup)
            assert stable(repeated) == stable(row)
            work_replays += 1
    summary = summarize(cases, rows, pools)
    assert canonical(summary) == json.loads((output/"summary.json").read_text())
    assert report(summary, diagnostics, model) == (output/"REPORT.md").read_text(encoding="utf-8")
    result = dict(status="passed", utc=datetime.now(timezone.utc).isoformat(),
        auditor_sha256=sha(Path(__file__)), lists=len(lists), cases=len(all_cases),
        development_action_pairs=len(pairs), test_counter_replays=len(rows),
        pool_runs=len(pools), deterministic_pool_replays=work_replays,
        checks="hashes; exact truth; group separation; paired costs/labels; weighted refit; threshold replay; folded-score parity; all counter replays; certificates/witnesses; pool accounting/deadlines; reconstructed summaries")
    path = output/"VALIDATION.json"
    if path.exists():
        saved = json.loads(path.read_text())
        assert saved["status"] == "passed" and saved["auditor_sha256"] == result["auditor_sha256"]
        print("All checks passed again; original validation preserved", flush=True)
    else:
        save_json(path, result)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        audit(args.output.resolve())
