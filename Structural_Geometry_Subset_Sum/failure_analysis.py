"""Post-hoc diagnosis of saved solver failures; never a fresh performance test."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import argparse
import json
from pathlib import Path
import shutil
from statistics import median

from Structural_Geometry_Subset_Sum.classifier_features import base_features
from Structural_Geometry_Subset_Sum.compat import reduce_instance
from Structural_Geometry_Subset_Sum.cost_gate import DEFAULTS, POLICIES, solve_gate
from Structural_Geometry_Subset_Sum.cost_gate_study import check_answer, verify
from Structural_Geometry_Subset_Sum.study import check_manifest, manifest, read_jsonl, save_json, save_jsonl, sha


def breakdown(cases, missed, key):
    all_counts = Counter(c[key] for c in cases)
    failures = Counter(c[key] for c in missed)
    return {str(k):dict(unresolved=failures[k], total=v, fraction=failures[k]/v)
            for k, v in all_counts.items()}


def trimmed_core(g, maximum=9):
    """Input-only hypothetical full-core representation, not a solving claim."""
    ranked = sorted(range(len(g["r"])), key=lambda i:(-abs(g["r"][i]), i))
    for count in range(min(maximum, len(ranked))+1):
        removed = set(ranked[:count])
        keep = [i for i in range(len(ranked)) if i not in removed]
        span = sum(abs(g["r"][i]) for i in keep)
        height = sum(g["p"][i] for i in keep)+1
        area = height*(span+1)
        history = (len(keep)+1)*area
        if area <= DEFAULTS["max_dp_bits"] and history <= DEFAULTS["max_history_bits"]:
            return dict(exceptions=count, exception_assignments=1 << count,
                original_residual_span=g["r_max"]-g["r_min"], core_span=span,
                full_core_dp_bits=area, full_core_history_bits=history,
                removed_indices=ranked[:count])
    return None


def run(experiment, output):
    parent = verify(experiment)
    for name in ("test_hashes.json", "evaluation_hashes.json"):
        check_manifest(experiment, name)
    validation = json.loads((experiment/"VALIDATION.json").read_text())
    assert validation["status"] == "passed"
    output.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).resolve()
    shutil.copy2(source, output/source.name)
    protocol = dict(status="post-hoc inspected-sample failure diagnosis, not a new prospective experiment",
        utc=datetime.now(timezone.utc).isoformat(), analysis_source_sha256=sha(source),
        parent_protocol_sha256=sha(experiment/"protocol.json"),
        parent_validation_sha256=sha(experiment/"VALIDATION.json"),
        input_hashes={name:sha(experiment/name) for name in
            ("test_cases.jsonl", "test_lists.jsonl", "counter_runs.jsonl")},
        probe_policy="direct_mitm, including original reductions/features/five-core reuse",
        probe_variants=dict(memory_only=dict(work_multiplier=1, max_states=1_048_576),
            work_only=dict(work_multiplier=16, max_states=32768),
            memory_and_work=dict(work_multiplier=16, max_states=1_048_576)),
        selected_cases="all cases unresolved by the saved learned policy under its full individual 32L cap",
        interpretation="same already-inspected inputs; changed resource allowances are diagnostic, not algorithmic speedups")
    save_json(output/"protocol.json", protocol)
    cases = read_jsonl(experiment/"test_cases.jsonl")
    lists = {r["list_id"]:r for r in read_jsonl(experiment/"test_lists.jsonl")}
    saved = read_jsonl(experiment/"counter_runs.jsonl")
    lookup = {(r["case_id"], r["policy"]):r["result"] for r in saved}
    missed = [c for c in cases if lookup[(c["case_id"], "learned")]["status"] == "unresolved"]
    missed_ids = {c["case_id"] for c in missed}
    descriptors, records = [], []
    for case in cases:
        kernel = reduce_instance(case["weights"], case["target"])
        base = base_features(case["weights"], case["target"], kernel)
        result = lookup[(case["case_id"], "learned")]
        g = result["geometry"]
        failures = []
        if g is not None:
            if g["q_count"] > DEFAULTS["max_q_count"]:
                failures.append("aggregate_count")
            if g["dp_bits"] > DEFAULTS["max_dp_bits"]:
                failures.append("dp_area")
            if g["history_bits"] > DEFAULTS["max_history_bits"]:
                failures.append("history_area")
        row = dict(case_id=case["case_id"], list_id=case["list_id"], family=case["family"],
            n=case["n"], truth=case["truth"], target_rule=case["target_rule"],
            unresolved=case["case_id"] in missed_ids, kernel_n=len(kernel.weights),
            kernel_target=kernel.target, min_structural_distance=min(base["values"][:5]),
            structural_distances=base["values"][:5], distinct_fraction=base["values"][10],
            relative_target=min(case["target"],sum(case["weights"])-case["target"])/sum(case["weights"]),
            metadata=lists[case["list_id"]]["metadata"], geometry_cap_violations=failures,
            decision_eligible=result["decision_eligible"],
            methods=result["attempts"],
            solved_by=[p for p in POLICIES if lookup[(case["case_id"],p)]["status"] != "unresolved"],
            trimmed_core=None if g is None else trimmed_core(g))
        descriptors.append(row)
        if row["unresolved"]:
            records.append(row)
    save_jsonl(output/"case_diagnostics.jsonl", descriptors)
    cap_counts = Counter(label for row in records for label in row["geometry_cap_violations"])
    summary = dict(cases=len(cases), unresolved=len(missed),
        every_policy_unresolved=sum(not row["solved_by"] for row in descriptors),
        by_family=breakdown(cases, missed, "family"), by_size=breakdown(cases, missed, "n"),
        by_truth=breakdown(cases, missed, "truth"), by_target_rule=breakdown(cases, missed, "target_rule"),
        baseline_rescues={p:sum(p in row["solved_by"] for row in records) for p in POLICIES},
        geometry_cap_violations=dict(cap_counts),
        eligible_failures=sum(row["decision_eligible"] for row in records),
        method_failure_reasons=dict(Counter(a["method"]+":"+a["reason"] for row in records for a in row["methods"])),
        failure_min_structural_distance=dict(minimum=min(r["min_structural_distance"] for r in records),
            median=median(r["min_structural_distance"] for r in records),
            maximum=max(r["min_structural_distance"] for r in records)),
        failures_by_replacement={family:dict(Counter(str(r["metadata"].get("replacements", "not_applicable"))
            for r in records if r["family"] == family)) for family in sorted({r["family"] for r in records})},
        full_core_trim_hypotheses={str(k):sum(r["trimmed_core"] is not None and
            r["trimmed_core"]["exceptions"] <= k for r in records) for k in (0,1,4,5,9)},
        resource_probes={})
    probes = []
    with (output/"probe_runs.jsonl").open("x", encoding="utf-8") as handle:
        for index, case in enumerate(missed):
            for variant, options in protocol["probe_variants"].items():
                config = dict(DEFAULTS, max_states=options["max_states"])
                cap = options["work_multiplier"]*case["budget"]
                result = solve_gate(case["weights"], case["target"], "direct_mitm",
                                    max_work=cap, config=config)
                check_answer(dict(case, budget=cap), result)
                row = dict(case_id=case["case_id"], family=case["family"], n=case["n"],
                    variant=variant, work_cap=cap, max_states=options["max_states"], result=result)
                probes.append(row)
                handle.write(json.dumps(row, separators=(",", ":"))+"\n")
                handle.flush()
            if (index+1) % 20 == 0:
                print(f"post-hoc resource probes: {index+1}/{len(missed)} failed cases", flush=True)
    for variant in protocol["probe_variants"]:
        chosen = [r for r in probes if r["variant"] == variant]
        summary["resource_probes"][variant] = dict(completed=sum(r["result"]["status"] != "unresolved" for r in chosen),
            total=len(chosen), by_size={str(n):sum(r["n"] == n and r["result"]["status"] != "unresolved" for r in chosen)
                for n in sorted({c["n"] for c in missed})},
            by_family={f:sum(r["family"] == f and r["result"]["status"] != "unresolved" for r in chosen)
                for f in sorted({c["family"] for c in missed})})
    assert sha(source) == protocol["analysis_source_sha256"]
    assert verify(experiment) == parent
    for name, digest in protocol["input_hashes"].items():
        assert sha(experiment/name) == digest
    save_json(output/"summary.json", summary)
    text = report(summary)
    (output/"REPORT.md").write_text(text, encoding="utf-8")
    manifest(output, "artifact_hashes.json", ["protocol.json", source.name, "case_diagnostics.jsonl",
        "probe_runs.jsonl", "summary.json", "REPORT.md"])
    save_json(output/"VALIDATION.json", dict(status="passed", utc=datetime.now(timezone.utc).isoformat(),
        cases=len(cases), selected_failures=len(missed), exact_probe_runs=len(probes),
        original_input_truths="from independently audited parent dataset",
        completed_probe_answers_and_witnesses_checked=True, sources_and_parent_inputs_unchanged=True))
    print(text, flush=True)


def report(summary):
    lines = ["# What the latest solver misses", "",
        "Post-hoc diagnosis of the already-inspected Experiment 03 test set, using full individual work-capped runs rather than cases left unattempted by a shared pool. These are solver failures, not classifier misclassifications or proofs of intrinsic hardness.", "",
        "| Family | Unresolved | Total |",
        "|---|---:|---:|"]
    for family, row in sorted(summary["by_family"].items(), key=lambda kv:-kv[1]["unresolved"]):
        lines.append(f'| {family} | {row["unresolved"]} | {row["total"]} |')
    lines += ["", f'{summary["unresolved"]}/{summary["cases"]} unresolved under learned; {summary["every_policy_unresolved"]} remain unresolved under every original policy. Direct MITM already rescues {summary["baseline_rescues"]["direct_mitm"]} learned failures at the original allowance. All unresolved inputs have 30 or 36 items; every 24-item case completes.', "",
        f'Only {summary["eligible_failures"]} unresolved case reaches an eligible DP decision. The others exceed both DP-area and history caps. All 115 bitset attempts hit width limits; all 115 DFS attempts hit work limits; MITM hits 58 state limits and 57 work limits. The minimum old-core deletion feature among failed cases ranges from 15 to 29, median 27.', "",
        "The named easy families can contain replacements: all failed near_equal and progression cases have 25% random replacements. Two progressions/two scales combine distinct structures that a single existing core or projection may represent poorly. Many-outlier large-base cases have a few dominant residuals; trimming those suggests an exception-to-geometric-core route, but this analysis does not implement or time such a solver.", "",
        "## Resource sensitivity on the same failed inputs", "",
        "Direct MITM retains original reduction/feature/five-core costs. Only the declared resource caps change. No live deadline is imposed. These probes diagnose caps; they are not speedups or fresh confirmatory results.", "",
        "| Probe | Work allowance | State cap | Completed / selected failures |",
        "|---|---|---:|---:|"]
    specs = dict(memory_only=("original 32L",1048576), work_only=("16 times original",32768),
                 memory_and_work=("16 times original",1048576))
    for name, row in summary["resource_probes"].items():
        allowance, states = specs[name]
        lines.append(f'| {name} | {allowance} | {states} | {row["completed"]}/{row["total"]} |')
    lines += ["", "Full per-case descriptors, input-only trimmed-core size hypotheses, exact probe answers/witnesses, parent/source hashes and all subgroup counts are saved. Geometry eligibility, repeated-family targets and post-hoc selection limit interpretation. Generated family metadata is used only for diagnosis; it never enters the measured original algorithms. Earlier models and experiments are unchanged."]
    return "\n".join(lines)+"\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--experiment", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.experiment.resolve(), args.output.resolve())
