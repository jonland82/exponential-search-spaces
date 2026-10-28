"""Post-hoc live 32L-cap diagnostic; never part of the original primary test."""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import random
from statistics import median

from Structural_Geometry_Subset_Sum.solver import POLICIES, solve_instance
from Structural_Geometry_Subset_Sum.study import (CONFIG, check_answer, check_manifest,
    completion_difference, manifest, read_jsonl, save_json, sha, verify)


def run(output):
    original = verify(output)
    check_manifest(output, "data_hashes.json")
    assert json.loads((output / "VALIDATION.json").read_text())["status"] == "passed"
    destination = output / "sensitivity_32L_live"
    destination.mkdir(exist_ok=False)
    source = Path(__file__)
    (destination / "sources").mkdir()
    (destination / "sources/time_sensitivity.py").write_bytes(source.read_bytes())
    protocol = dict(status="post-hoc budget sensitivity; reused inspected inputs, not a fresh prospective test",
        reason="original live safety work cap allowed the early core method to consume the deadline",
        fixed_before_timing_utc=datetime.now(timezone.utc).isoformat(),
        primary_protocol_sha256=sha(output / "protocol.json"), case_sha256=sha(output / "cases.jsonl"),
        primary_validation_sha256=sha(output / "VALIDATION.json"), source_sha256=sha(source),
        online_work_cap="the original prespecified deterministic 32L allowance",
        seconds=CONFIG["live_seconds"], repeats=3, unchanged_detector_and_solver=CONFIG["solver"],
        seed=CONFIG["seed"], policies=list(POLICIES))
    save_json(destination / "protocol.json", protocol)
    cases = read_jsonl(output / "cases.jsonl")
    rows = []
    with (destination / "runs.jsonl").open("x", encoding="utf-8") as handle:
        for repeat in range(3):
            ordered = list(cases)
            random.Random(f'{CONFIG["seed"]}:32L-live:{repeat}').shuffle(ordered)
            for index, case in enumerate(ordered):
                policies = list(POLICIES)
                random.Random(f'{CONFIG["seed"]}:32L-live:{repeat}:{case["case_id"]}').shuffle(policies)
                for policy in policies:
                    result = solve_instance(case["weights"], case["target"], policy,
                        max_work=case["work_cap"], seconds=CONFIG["live_seconds"], config=CONFIG["solver"])
                    check_answer(case, result)
                    row = dict(case_id=case["case_id"], list_id=case["list_id"], family=case["family"],
                        n=case["n"], mode="time", repeat=repeat, policy=policy, **result)
                    rows.append(row)
                    handle.write(json.dumps(row, separators=(",", ":"))+"\n")
                    handle.flush()
                if (index+1) % 108 == 0:
                    print(f"32L live repeat={repeat}: {index+1}/324 cases", flush=True)
    summary = dict(status=protocol["status"], policies={},
        root_vs_portfolio=completion_difference(rows, "root_geometry", "portfolio"),
        selective_vs_root=completion_difference(rows, "selective_geometry", "root_geometry"))
    for policy in POLICIES:
        group = [r for r in rows if r["policy"] == policy]
        totals = [sum(r["status"] != "unresolved" for r in group if r["repeat"] == repeat) for repeat in range(3)]
        summary["policies"][policy] = dict(completed_median=median(totals), completed_range=[min(totals), max(totals)],
            internal_yes=sum(r["counts"]["internal_yes"] for r in group),
            internal_no=sum(r["counts"]["internal_no"] for r in group),
            dfs_attempts=sum(any(a["method"] == "dfs" for a in r["attempts"]) for r in group),
            mitm_attempts=sum(any(a["method"] == "mitm" for a in r["attempts"]) for r in group))
    save_json(destination / "summary.json", summary)
    lines = ["# Post-hoc sensitivity: 32L work plus 50ms live deadline", "",
        "These are the previously inspected inputs, reused for a schedule/resource diagnostic. This was not prespecified as a primary endpoint or a new independent evaluation. The detector, exact checking, native algorithms and thresholds are unchanged. Only the live safety work cap is replaced by the original prespecified deterministic per-case 32L allowance.", "",
        "| Policy | Median completions [range] | Internal YES/NO | DFS attempts | MITM attempts |",
        "|---|---:|---|---:|---:|"]
    for policy, row in summary["policies"].items():
        lo, hi = row["completed_range"]
        lines.append(f'| {policy} | {row["completed_median"]} [{lo}, {hi}] | {row["internal_yes"]}/{row["internal_no"]} | {row["dfs_attempts"]} | {row["mitm_attempts"]} |')
    lines += ["", "Event and attempt counts sum three dependent repeats. All completion counts exclude late answers and pay online work/time. Bootstrap values in summary.json are descriptive conditional reuse, not a new prospective significance claim. This control tests sensitivity to the common portfolio schedule; it is not an optimized modern solver comparison."]
    (destination / "REPORT.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    manifest(destination, "artifact_hashes.json", ("protocol.json", "runs.jsonl", "summary.json", "REPORT.md"))
    audit(output)
    print((destination / "REPORT.md").read_text(encoding="utf-8"), flush=True)


def audit(output):
    verify(output)
    destination = output / "sensitivity_32L_live"
    check_manifest(destination, "artifact_hashes.json")
    protocol = json.loads((destination / "protocol.json").read_text())
    assert protocol["case_sha256"] == sha(output / "cases.jsonl")
    assert protocol["primary_protocol_sha256"] == sha(output / "protocol.json")
    assert protocol["primary_validation_sha256"] == sha(output / "VALIDATION.json")
    assert protocol["source_sha256"] == sha(Path(__file__)) == sha(destination / "sources/time_sensitivity.py")
    cases = {c["case_id"]:c for c in read_jsonl(output / "cases.jsonl")}
    rows = read_jsonl(destination / "runs.jsonl")
    assert len(rows) == 3888
    assert len({(r["case_id"], r["repeat"], r["policy"]) for r in rows}) == 3888
    from Structural_Geometry_Subset_Sum.audit import audit_event
    for row in rows:
        case = cases[row["case_id"]]
        check_answer(case, row)
        assert row["work"] <= case["work_cap"]
        assert row["status"] == "unresolved" or row["seconds"] < CONFIG["live_seconds"]
        for event in row["events"]:
            audit_event(event, CONFIG["solver"])
    save_json(destination / "VALIDATION.json", dict(status="passed", runs=3888,
        answers_and_events_checked=True, hashes_verified=True,
        original_input_truth_independently_audited=True, utc=datetime.now(timezone.utc).isoformat()))
    print("Sensitivity audit passed: 3888 paid live runs, all answers/events and provenance checked", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("run", "audit"))
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    globals()[args.stage](args.output)
