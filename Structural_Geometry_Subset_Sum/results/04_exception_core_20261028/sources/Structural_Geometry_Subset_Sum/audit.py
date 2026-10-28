"""Independent arithmetic/event checks, exact truths and deterministic replay."""
from collections import defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path

from Structural_Geometry_Subset_Sum.budget import Meter
from Structural_Geometry_Subset_Sum.compat import independent_halves, independent_query
from Structural_Geometry_Subset_Sum.solver import POLICIES
from Structural_Geometry_Subset_Sum.structures.large_base import check, describe
from Structural_Geometry_Subset_Sum.study import (CONFIG, check_answer, check_manifest,
    diagnostic, read_jsonl, save_json, sha, signature, solve_case, summarize, verify)


def stable(result):
    result = dict(result)
    for name in ("seconds", "component_seconds", "overshoot_seconds"):
        result.pop(name, None)
    return json.loads(json.dumps(result))


def audit_event(event, config):
    saved = event["geometry"]
    if saved is None:
        assert event["status"] == "unresolved"
        return
    weights, target = event["weights"], event["target"]
    divisor, base = saved["divisor"], saved["base"]
    assert len(saved["p"]) == len(saved["r"]) == len(weights)
    assert target == divisor*saved["target"]
    assert all(w == divisor*(base*p+r) for w, p, r in zip(weights, saved["p"], saved["r"]))
    r_min = sum(min(0, value) for value in saved["r"])
    r_max = sum(max(0, value) for value in saved["r"])
    # Integer-only independent ceiling, including negative residuals.
    lo = max(0, (saved["target"]-r_max+base-1)//base)
    hi = min(sum(saved["p"]), (saved["target"]-r_min)//base)
    assert (r_min, r_max, lo, hi) == (saved["r_min"], saved["r_max"], saved["q_low"], saved["q_high"])
    assert saved["q_count"] == max(0, hi-lo+1)
    if event["status"] == "yes":
        chosen = event["witness"]
        assert chosen is not None and len(chosen) == len(set(chosen))
        assert sum(weights[i] for i in chosen) == target
    elif event["status"] == "no":
        if event["reason"] == "aggregate_gap":
            assert lo > hi
        else:
            assert event["reason"] == "aggregate_dp_exhausted"
            geometry = describe(weights, target, base, divisor)
            replay = check(geometry, Meter(1000000), max_work=1000000,
                max_dp_bits=config["max_dp_bits"], max_history_bits=config["max_history_bits"],
                max_q_count=config["max_q_count"])
            assert replay["status"] == "no"


def audit(output):
    protocol = verify(output)
    for name in ("data_hashes.json", "run_hashes.json", "memory_hashes.json", "analysis_hashes.json", "plot_hashes.json"):
        check_manifest(output, name)
    assert datetime.fromisoformat(json.loads((output / "generation.started.json").read_text())["utc"]) > datetime.fromisoformat(protocol["frozen_at_utc"])
    lists = read_jsonl(output / "lists.jsonl")
    cases = read_jsonl(output / "cases.jsonl")
    diagnostics = read_jsonl(output / "diagnostics.jsonl")
    assert len(lists) == 108 and len(cases) == 324 and len(diagnostics) == 324
    assert len({c["case_id"] for c in cases}) == 324
    signatures = {signature(row["weights"]) for row in lists}
    assert len(signatures) == 108 and not signatures & set(protocol["prior_signatures"])
    by_list = defaultdict(list)
    for case in cases:
        by_list[case["list_id"]].append(case)
    list_map = {row["list_id"]:row for row in lists}
    for index, (list_id, group) in enumerate(by_list.items()):
        weights = list_map[list_id]["weights"]
        assert all(case["weights"] == weights for case in group)
        assert {case["target_rule"] for case in group} == set(CONFIG["targets"])
        halves = independent_halves(weights)
        for case in group:
            mask = independent_query(halves, case["target"])
            assert mask == case["oracle_mask"]
            assert (mask is not None) == (case["truth"] == "yes")
        del halves
        if index % 18 == 0:
            print(f"independent truth: {index+1}/108 lists", flush=True)
    for case, row in zip(cases, diagnostics):
        assert row == json.loads(json.dumps(dict(case_id=case["case_id"], **diagnostic(case["weights"], case["target"]))))
    rows = read_jsonl(output / "runs.jsonl")
    expected = len(cases)*len(POLICIES)*(1+CONFIG["live_repeats"])
    assert len(rows) == expected == 5184
    assert len({(r["case_id"], r["mode"], r["repeat"], r["policy"]) for r in rows}) == expected
    case_map = {case["case_id"]:case for case in cases}
    checked_events, completed = 0, 0
    for index, row in enumerate(rows):
        case = case_map[row["case_id"]]
        assert row["list_id"] == case["list_id"] and row["family"] == case["family"] and row["n"] == case["n"]
        check_answer(case, row)
        completed += row["status"] != "unresolved"
        assert sum(row["component_seconds"].values()) <= row["seconds"]+1e-6
        assert row["work"] <= (case["work_cap"] if row["mode"] == "work" else CONFIG["live_work_cap"])
        if row["mode"] == "time" and row["status"] != "unresolved":
            assert row["seconds"] < CONFIG["live_seconds"]
        if row["policy"] == "portfolio":
            assert not row["events"]
        if row["policy"] == "detect_only":
            assert not row["counts"]["geometry_checks"]
        if row["policy"] != "selective_geometry":
            assert not row["counts"]["internal_yes"] and not row["counts"]["internal_no"]
        for event in row["events"]:
            audit_event(event, CONFIG["solver"])
            checked_events += 1
        if row["mode"] == "work":
            replay = solve_case(case, row["policy"], "work")
            expected_result = {name:value for name, value in row.items()
                if name not in ("case_id", "list_id", "family", "n", "mode", "repeat", "policy")}
            assert stable(replay) == stable(expected_result), (case["case_id"], row["policy"])
        if index % 864 == 0:
            print(f"event/resource audit: {index+1}/{len(rows)} runs", flush=True)
    profiles = read_jsonl(output / "memory_profiles.jsonl")
    assert len(profiles) == 32
    for profile in profiles:
        case = case_map[profile["case_id"]]
        assert profile["peak_traced_bytes"] >= 0
        assert stable(profile["result"]) == stable(solve_case(case, profile["policy"], "work"))
    summary = summarize(cases, rows, profiles)
    assert summary == json.loads((output / "summary.json").read_text())
    plot = json.loads((output / "geometry_plot.json").read_text())
    assert len(plot["panels"]) == 2
    for panel in plot["panels"]:
        if panel["geometry"] is not None:
            assert len(panel["points"]) <= CONFIG["plot_state_cap"]
            assert len(panel["points"]) == len({tuple(point) for point in panel["points"]})
    verify(output)
    save_json(output / "VALIDATION.json", dict(status="passed", cases=324, lists=108,
        policy_runs=5184, deterministic_replays=1296, completed_answers_checked=completed,
        geometry_events_checked=checked_events, memory_profiles=32, independent_truth=True,
        hashes_verified=True, auditor_sha256=sha(Path(__file__)),
        utc=datetime.now(timezone.utc).isoformat()))
    print(f"VALIDATED: 324 cases, 5184 runs, 1296 deterministic replays, {checked_events} geometric events", flush=True)
