"""Freeze, generate and evaluate Experiment 01 without changing earlier studies."""
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from math import gcd
from pathlib import Path
import platform
import random
import shutil
from statistics import median
import sys
import tracemalloc

from Structural_Geometry_Subset_Sum.budget import Meter
from Structural_Geometry_Subset_Sum.compat import (ROOT, independent_halves,
    independent_query, input_length, reduce_instance, weights_for)
from Structural_Geometry_Subset_Sum.solver import DEFAULTS, POLICIES, solve_instance
from Structural_Geometry_Subset_Sum.structures.large_base import detect


HERE = Path(__file__).resolve().parent
CONFIG = dict(seed=760281028, sizes=[20, 28, 36], replicates=4,
    families=["large_base", "large_base_one_outlier", "large_base_many_outliers",
        "near_equal", "random_wide", "superincreasing", "coverage", "few_values", "progression"],
    targets=["planted", "middle", "fractional_band"], policies=list(POLICIES),
    work_multiplier=32, live_seconds=.05, live_work_cap=2_000_000, live_repeats=3,
    solver=DEFAULTS, bootstrap_draws=1000, plot_state_cap=250000,
    primary="root_geometry minus portfolio live completions, repeat average",
    status="locally frozen exploratory structural efficiency experiment")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_json(path, value):
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2)
        handle.write("\n")


def save_jsonl(path, rows):
    with path.open("x", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, separators=(",", ":"))+"\n")


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def signature(weights):
    divisor = gcd(*weights)
    return hashlib.sha256(json.dumps(sorted(w//divisor for w in weights), separators=(",", ":")).encode()).hexdigest()


def freeze(output):
    if output.exists():
        raise FileExistsError("use a fresh experiment output directory")
    sources = [p for p in HERE.rglob("*.py") if "results" not in p.relative_to(HERE).parts]
    sources += [HERE / name for name in ("THEORY.md", "LITERATURE.md", "experiments/01_large_base/PROTOCOL.md")]
    sources += [ROOT / "Learned_Solvability_Subset_Sum" / name for name in ("features.py", "advanced_features.py", "run_pilot.py")]
    sources += [ROOT / "Structural_Distance_Subset_Sum/structural_subset_sum.py"]
    sources = sorted(set(sources))
    prior = [p for p in ROOT.rglob("lists.jsonl") if not
        {"sources", "upstream", "reruns", ".git", ".build"}.intersection(p.relative_to(ROOT).parts)]
    prior = sorted(prior)
    seen = sorted({signature(row["weights"]) for path in prior for row in read_jsonl(path)})
    output.mkdir(parents=True)
    for path in sources:
        target = output / "sources" / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    protocol = dict(config=CONFIG, frozen_at_utc=datetime.now(timezone.utc).isoformat(),
        source_hashes={str(p.relative_to(ROOT)):sha(p) for p in sources},
        input_hashes={str(p.relative_to(ROOT)):sha(p) for p in prior}, prior_signatures=seen,
        python=sys.version, platform=platform.platform())
    save_json(output / "protocol.json", protocol)
    (output / "protocol.sha256").write_text(sha(output / "protocol.json")+"\n")
    print(f"FROZEN: four policies, {len(sources)} source files, {len(seen)} prior normalized lists excluded", flush=True)


def verify(output):
    protocol = json.loads((output / "protocol.json").read_text())
    assert protocol["config"] == CONFIG
    assert sha(output / "protocol.json") == (output / "protocol.sha256").read_text().strip()
    for name, digest in protocol["source_hashes"].items():
        assert sha(ROOT / name) == sha(output / "sources" / name) == digest, name
    for name, digest in protocol["input_hashes"].items():
        assert sha(ROOT / name) == digest, name
    return protocol


def manifest(output, filename, names):
    save_json(output / filename, {name:sha(output / name) for name in names})


def check_manifest(output, filename):
    for name, digest in json.loads((output / filename).read_text()).items():
        assert sha(output / name) == digest, name


def make_weights(family, n, replicate, rng):
    metadata = {}
    if family.startswith("large_base"):
        bits = 24+8*(replicate//2)
        base = (1 << bits) if replicate % 2 == 0 else rng.randrange(1 << bits, 1 << (bits+1))
        weights = [base*rng.randrange(1, 7)+rng.randrange(-8, 9) for _ in range(n)]
        count = (1 if family == "large_base_one_outlier" else
                 (n+7)//8 if family == "large_base_many_outliers" else 0)
        maximum = max(weights)
        for j, index in enumerate(rng.sample(range(n), count)):
            weights[index] = maximum+(j+1)*base+rng.randrange(base//4, 2*base//5+1)
        metadata = dict(base=base, base_kind="power_two" if replicate % 2 == 0 else "arbitrary",
            base_bits=bits, outliers=count, residual_radius=8)
    elif family == "near_equal":
        base = rng.randrange(1 << 29, 1 << 30)
        weights = [base+rng.randrange(-1024, 1025) for _ in range(n)]
        metadata = dict(base=base, base_kind="arbitrary", residual_radius=1024, outliers=0)
    else:
        weights = weights_for(family, n, 0, rng)
    rng.shuffle(weights)
    if "base" in metadata:
        base = metadata["base"]
        metadata["p"] = [(w+base//2)//base for w in weights]
        metadata["r"] = [w-base*p for w, p in zip(weights, metadata["p"])]
    return weights, metadata


def diagnostic(weights, target):
    kernel = reduce_instance(weights, target)
    if kernel.status != "unresolved":
        return dict(kernel_status=kernel.status, geometry=None)
    divisor = gcd(*kernel.weights)
    normalized = tuple(w//divisor for w in kernel.weights)
    residual = kernel.target//divisor
    meter = Meter(100000)
    geometry, count = detect(normalized, residual, meter, CONFIG["solver"]["candidate_cap"])
    return dict(kernel_status=kernel.status, weights=normalized, target=residual,
        candidates=count, acquisition_work=meter.work,
        geometry=None if geometry is None else geometry.record())


def generate(output):
    protocol = verify(output)
    save_json(output / "generation.started.json", dict(utc=datetime.now(timezone.utc).isoformat()))
    seen = set(protocol["prior_signatures"])
    lists, cases, proposals, diagnostics = [], [], [], []
    for n in CONFIG["sizes"]:
        for family in CONFIG["families"]:
            for replicate in range(CONFIG["replicates"]):
                list_id = f"geometry-n{n}-{family}-s{replicate}"
                for proposal in range(32):
                    rng = random.Random(f'{CONFIG["seed"]}:{list_id}:{proposal}')
                    weights, metadata = make_weights(family, n, replicate, rng)
                    code = signature(weights)
                    accepted = code not in seen
                    proposals.append(dict(list_id=list_id, proposal=proposal, accepted=accepted))
                    if accepted:
                        seen.add(code)
                        break
                else:
                    raise RuntimeError(f"no unused input for {list_id}")
                total = sum(weights)
                planted = sum(w for w in weights if rng.getrandbits(1))
                middle = rng.randrange(3*total//10, 7*total//10+1)
                fractional = (metadata["base"]*(sum(metadata["p"])//2)+metadata["base"]//2
                    if "base" in metadata else total//2+1)
                lists.append(dict(list_id=list_id, n=n, family=family, replicate=replicate,
                    weights=weights, metadata=metadata))
                halves = independent_halves(weights)
                for rule, target in zip(CONFIG["targets"], (planted, middle, fractional)):
                    mask = independent_query(halves, target)
                    case_id = f"{list_id}-{rule}"
                    cases.append(dict(case_id=case_id, list_id=list_id, n=n, family=family,
                        replicate=replicate, target_rule=rule, weights=weights, target=target,
                        work_cap=CONFIG["work_multiplier"]*input_length(weights, target),
                        truth="yes" if mask is not None else "no", oracle_mask=mask))
                    diagnostics.append(dict(case_id=case_id, **diagnostic(weights, target)))
                del halves
                if len(lists) % 12 == 0:
                    print(f"generated {len(lists)}/108 lists, {len(cases)} cases", flush=True)
    verify(output)
    names = ("lists.jsonl", "cases.jsonl", "proposals.jsonl", "diagnostics.jsonl")
    for name, rows in zip(names, (lists, cases, proposals, diagnostics)):
        save_jsonl(output / name, rows)
    manifest(output, "data_hashes.json", names)


def check_answer(case, result):
    assert result["status"] in ("yes", "no", "unresolved")
    if result["status"] == "unresolved":
        assert result["witness"] is None
    else:
        assert (result["status"] == "yes") == (case["truth"] == "yes"), case["case_id"]
        witness = result["witness"]
        if witness is not None:
            assert len(witness) == len(set(witness))
            assert all(0 <= index < len(case["weights"]) for index in witness)
            assert sum(case["weights"][i] for i in witness) == case["target"]


def solve_case(case, policy, mode):
    return solve_instance(case["weights"], case["target"], policy,
        max_work=case["work_cap"] if mode == "work" else CONFIG["live_work_cap"],
        seconds=None if mode == "work" else CONFIG["live_seconds"], config=CONFIG["solver"])


def run(output):
    verify(output)
    check_manifest(output, "data_hashes.json")
    cases = read_jsonl(output / "cases.jsonl")
    save_json(output / "runs.started.json", dict(utc=datetime.now(timezone.utc).isoformat()))
    with (output / "runs.jsonl").open("x", encoding="utf-8") as handle:
        for mode in ("work", "time"):
            for repeat in range(1 if mode == "work" else CONFIG["live_repeats"]):
                ordered = list(cases)
                random.Random(f'{CONFIG["seed"]}:{mode}:{repeat}').shuffle(ordered)
                for index, case in enumerate(ordered):
                    policies = list(POLICIES)
                    random.Random(f'{CONFIG["seed"]}:{mode}:{repeat}:{case["case_id"]}').shuffle(policies)
                    for policy in policies:
                        result = solve_case(case, policy, mode)
                        check_answer(case, result)
                        row = dict(case_id=case["case_id"], list_id=case["list_id"], family=case["family"],
                            n=case["n"], mode=mode, repeat=repeat, policy=policy, **result)
                        handle.write(json.dumps(row, separators=(",", ":"))+"\n")
                        handle.flush()
                    if (index+1) % 54 == 0:
                        print(f"{mode} repeat={repeat}: {index+1}/324 cases", flush=True)
    verify(output)
    manifest(output, "run_hashes.json", ("runs.jsonl",))


def memory(output):
    verify(output)
    check_manifest(output, "data_hashes.json")
    cases = read_jsonl(output / "cases.jsonl")
    profiles = []
    for family in ("large_base", "large_base_one_outlier", "random_wide", "coverage"):
        subset = [c for c in cases if c["n"] == 36 and c["family"] == family and c["replicate"] == 0
            and c["target_rule"] in ("planted", "fractional_band")]
        assert len(subset) == 2
        for case in subset:
            for policy in POLICIES:
                tracemalloc.start()
                result = solve_case(case, policy, "work")
                _, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                check_answer(case, result)
                profiles.append(dict(case_id=case["case_id"], policy=policy,
                    peak_traced_bytes=peak, result=result))
    save_jsonl(output / "memory_profiles.jsonl", profiles)
    manifest(output, "memory_hashes.json", ("memory_profiles.jsonl",))
    print("Saved 32 separate Python-allocation profiles", flush=True)


def quantile(values, probability):
    values = sorted(values)
    position = probability*(len(values)-1)
    lower = int(position)
    return values[lower]+(values[min(lower+1, len(values)-1)]-values[lower])*(position-lower)


def completion_difference(rows, first, second):
    values = defaultdict(float)
    for row in rows:
        if row["mode"] == "time" and row["policy"] in (first, second):
            values[row["list_id"]] += (1 if row["policy"] == first else -1)*(row["status"] != "unresolved")/CONFIG["live_repeats"]
    block = list(values.values())
    rng = random.Random(CONFIG["seed"])
    draws = [sum(rng.choices(block, k=len(block))) for _ in range(CONFIG["bootstrap_draws"])]
    return dict(repeat_average_difference=sum(block), list_bootstrap_95=[quantile(draws, .025), quantile(draws, .975)],
        independent_lists=len(block), conditional_on_policies_and_observed_timings=True)


def summarize(cases, rows, profiles):
    result = dict(cases=len(cases), lists=len({c["list_id"] for c in cases}), runs=len(rows),
        truth_counts={value:sum(c["truth"] == value for c in cases) for value in ("yes", "no")},
        policies={}, families={}, sizes={}, comparisons={})
    for mode in ("work", "time"):
        result["policies"][mode] = {}
        for policy in POLICIES:
            group = [r for r in rows if r["mode"] == mode and r["policy"] == policy]
            repeats = sorted({r["repeat"] for r in group})
            completed = [sum(r["status"] != "unresolved" for r in group if r["repeat"] == repeat) for repeat in repeats]
            total_seconds = [sum(r["seconds"] for r in group if r["repeat"] == repeat) for repeat in repeats]
            fields = dict(completed_median=median(completed), completed_range=[min(completed), max(completed)],
                capped_seconds_median=median(total_seconds),
                root_yes=sum(r["counts"]["root_yes"] for r in group), root_no=sum(r["counts"]["root_no"] for r in group),
                internal_yes=sum(r["counts"]["internal_yes"] for r in group), internal_no=sum(r["counts"]["internal_no"] for r in group),
                discovery_seconds=sum(r["component_seconds"]["detection"] for r in group),
                checker_seconds=sum(r["component_seconds"]["checker"] for r in group),
                max_overshoot_seconds=max(r["overshoot_seconds"] for r in group),
                peak_history_logical_bits=max(r["peak_history_bits"] for r in group))
            result["policies"][mode][policy] = fields
        for dimension in ("family", "n"):
            dest = result["families" if dimension == "family" else "sizes"].setdefault(mode, {})
            for value in sorted({c[dimension] for c in cases}):
                dest[str(value)] = {}
                for policy in POLICIES:
                    group = [r for r in rows if r["mode"] == mode and r["policy"] == policy and r[dimension] == value]
                    totals = [sum(r["status"] != "unresolved" for r in group if r["repeat"] == repeat)
                        for repeat in sorted({r["repeat"] for r in group})]
                    dest[str(value)][policy] = median(totals)
    for first, second in (("root_geometry", "portfolio"), ("selective_geometry", "root_geometry"), ("detect_only", "portfolio")):
        comparison = completion_difference(rows, first, second)
        per_case = defaultdict(lambda:defaultdict(list))
        for row in rows:
            if row["mode"] == "time" and row["policy"] in (first, second):
                per_case[row["case_id"]][row["policy"]].append(row)
        ratios = []
        for group in per_case.values():
            if all(len(group[p]) == 3 and all(r["status"] != "unresolved" for r in group[p]) for p in (first, second)):
                ratios.append(median(r["seconds"] for r in group[second])/max(1e-12, median(r["seconds"] for r in group[first])))
        comparison.update(jointly_completed_all_repeats=len(ratios), median_second_over_first_seconds=None if not ratios else median(ratios))
        result["comparisons"][first+"_vs_"+second] = comparison
    result["memory_profiles"] = len(profiles)
    result["peak_python_traced_bytes"] = {policy:max(r["peak_traced_bytes"] for r in profiles if r["policy"] == policy) for policy in POLICIES}
    return result


def report(summary):
    lines = ["# Experiment 01: large-base structural geometry", "",
        f'{summary["lists"]} fresh lists, {summary["cases"]} cases, {summary["runs"]} policy runs. Source/config freeze preceded generation. No fitted model or oracle parameter enters solving.', "",
        "| Policy | Work completions | Live median [range] | Median capped live seconds | Root YES/NO, live | Internal YES/NO, live |",
        "|---|---:|---:|---:|---|---|"]
    for policy in POLICIES:
        work, live = summary["policies"]["work"][policy], summary["policies"]["time"][policy]
        lo, hi = live["completed_range"]
        lines.append(f'| {policy} | {work["completed_median"]} | {live["completed_median"]} [{lo}, {hi}] | {live["capped_seconds_median"]:.4f} | {live["root_yes"]}/{live["root_no"]} | {live["internal_yes"]}/{live["internal_no"]} |')
    lines += ["", "Root/internal counts above sum three dependent timing repeats; completion medians are totals per repeat. Capped seconds include unresolved runs and are not uncensored solution times.", "",
        "## Paired completion comparisons", "", "| Comparison | Repeat-average difference | Conditional list-bootstrap 95% interval | Joint completions | Median comparator/policy time |",
        "|---|---:|---|---:|---:|"]
    for name, row in summary["comparisons"].items():
        lo, hi = row["list_bootstrap_95"]
        ratio = row["median_second_over_first_seconds"]
        lines.append(f'| {name} | {row["repeat_average_difference"]:+.2f} | [{lo:+.2f}, {hi:+.2f}] | {row["jointly_completed_all_repeats"]} | {"NA" if ratio is None else f"{ratio:.3f}"} |')
    lines += ["", "Only root_geometry versus portfolio is primary. Bootstrap resamples whole base lists, not targets or timing repeats. Joint timing ratios require both policies to finish the case in all three repeats. Secondary comparisons are unadjusted; machine timings do not establish general asymptotic speedups.", "",
        "## Live family completions", "", "| Family | Portfolio | Detection only | Root geometry | Selective geometry |", "|---|---:|---:|---:|---:|"]
    for family, group in summary["families"]["time"].items():
        lines.append(f'| {family} | '+" | ".join(str(group[p]) for p in POLICIES)+" |")
    lines += ["", "## Separate peak allocation profiles", "", "| Policy | Maximum traced MiB |", "|---|---:|"]
    for policy, peak in summary["peak_python_traced_bytes"].items():
        lines.append(f'| {policy} | {peak/(1 << 20):.3f} |')
    lines += ["", "Memory is Python-traced allocation from 32 separate fixed-case/work-budget profiles, not process RSS or same-success uncensored memory. Logical DP/history bounds are representation estimates. All discovery, checking and native solver work is charged; counters are heterogeneous, not CPU/bit operations. Returned witnesses and completed decisions are checked against independent truth. Bounds and discovery are elementary implementations motivated by decomposable-knapsack literature; the generator is not asserted to inherit that literature's branching lower bounds.", "",
        "Raw events, phase costs, attempts, overshoots and family/size metrics are retained. The companion geometric plot illustrates aggregate coordinates without fitting PCA or using labels to choose a detector. No paper or earlier model is changed."]
    return "\n".join(lines)+"\n"


def analyze(output):
    verify(output)
    for name in ("data_hashes.json", "run_hashes.json", "memory_hashes.json"):
        check_manifest(output, name)
    summary = summarize(read_jsonl(output / "cases.jsonl"), read_jsonl(output / "runs.jsonl"), read_jsonl(output / "memory_profiles.jsonl"))
    save_json(output / "summary.json", summary)
    (output / "REPORT.md").write_text(report(summary), encoding="utf-8")
    manifest(output, "analysis_hashes.json", ("summary.json", "REPORT.md"))
    print(report(summary), flush=True)


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("freeze", "generate", "run", "memory", "analyze", "plot"))
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.stage == "plot":
        from Structural_Geometry_Subset_Sum.visualize import plot
        plot(args.output)
    else:
        globals()[args.stage](args.output)
