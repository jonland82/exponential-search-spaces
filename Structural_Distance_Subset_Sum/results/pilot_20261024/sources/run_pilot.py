"""Exploratory, reproducible pilot; not the frozen prospective experiment."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import platform
import random
from statistics import median
import sys
from time import perf_counter

from structural_subset_sum import (
    Limits, find_core, solve, solve_bitset, solve_dfs, solve_mitm,
)


HERE = Path(__file__).resolve().parent
CONFIG = {
    "status": "exploratory pilot; not a prospective novelty or speedup claim",
    "seed": 240_102_026,
    "sizes": [16, 24, 32],
    "injected_counts": [0, 4, 8, 12],
    "families": ["unrelated", "repeated"],
    "replicates": 2,
    "target_rules": [
        "independent fair-bit subset of the final indexed input",
        "uniform integer in inclusive [round(.30 total), round(.70 total)]",
    ],
    "label_oracle": "independent full indexed-half enumeration; no core information",
    "method_order": "reproducibly shuffled for every case",
    "timing": "one instrumented Python run per case and method, including preprocessing",
    "memory": "live residual record cap; no exact byte-memory measurement",
    "bitset": "decision-only baseline; separate declared width cap",
}


def make_weights(n, injected, family, rng):
    core = []
    total = 0
    for _ in range(n - injected):
        value = total + rng.randrange(3, max(4, total // 8 + 4))
        core.append(value)
        total += value
    if family == "repeated":
        noise = [core[len(core) // 2]] * injected
    else:
        noise = [rng.randrange(1, total + 1) for _ in range(injected)]
    weights = core + noise
    rng.shuffle(weights)
    return weights


def oracle_halves(weights):
    """Independent binary-mask enumeration, not the measured MITM builder."""
    middle = len(weights) // 2
    blocks = []
    for start, stop in ((0, middle), (middle, len(weights))):
        block = {}
        width = stop - start
        # Binary recurrence on the least significant chosen bit.
        totals = [0] * (1 << width)
        for mask in range(1 << width):
            if mask:
                bit = mask & -mask
                totals[mask] = totals[mask ^ bit] + weights[start + bit.bit_length() - 1]
            block[totals[mask]] = mask << start
        blocks.append(block)
    return blocks


def oracle_query(halves, target):
    left, right = halves
    for value, mask in left.items():
        other = right.get(target - value)
        if other is not None:
            return mask | other
    return None


def source_hashes():
    names = (
        "structural_subset_sum.py", "test_structural_subset_sum.py",
        "run_pilot.py", "THEORY.md", "README.md",
    )
    return {
        name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
        for name in names
    }


def check_result(weights, target, truth, result):
    if result.status == "unresolved":
        assert result.witness is None
        return
    assert (result.status == "yes") == truth, (weights, target, result)
    if result.status == "yes" and result.reason != "decision_only":
        assert result.witness is not None
        assert len(set(result.witness)) == len(result.witness)
        assert all(0 <= i < len(weights) for i in result.witness)
        assert sum(weights[i] for i in result.witness) == target


def summarize(cases, rows):
    by_case = {case["case_id"]: case for case in cases}
    methods = sorted({row["method"] for row in rows})
    summary = {
        "lists": len({case["list_id"] for case in cases}),
        "cases": len(cases),
        "truth_counts": dict(Counter(case["truth"] for case in cases)),
        "answers_checked": sum(row["status"] != "unresolved" for row in rows),
        "mismatches": 0,
        "methods": {},
        "families": {},
    }
    mitm = {row["case_id"]: row for row in rows if row["method"] == "mitm"}
    for method in methods:
        group = [row for row in rows if row["method"] == method]
        matched = [
            row for row in group
            if row["status"] != "unresolved"
            and mitm[row["case_id"]]["status"] != "unresolved"
        ]
        summary["methods"][method] = {
            "completed": sum(row["status"] != "unresolved" for row in group),
            "unresolved_reasons": dict(Counter(
                row["reason"] for row in group if row["status"] == "unresolved"
            )),
            "median_all_attempts_ms": 1000 * median(row["stats"]["total_seconds"] for row in group),
            "matched_mitm_cases": len(matched),
            "faster_than_mitm": sum(
                row["stats"]["total_seconds"] < mitm[row["case_id"]]["stats"]["total_seconds"]
                for row in matched
            ),
            "truth_strata": {},
        }
        for truth in ("yes", "no"):
            completed = [
                row for row in group
                if by_case[row["case_id"]]["truth"] == truth
                and row["status"] != "unresolved"
            ]
            summary["methods"][method]["truth_strata"][truth] = {
                "completed": len(completed),
                "median_completed_ms": (
                    1000 * median(row["stats"]["total_seconds"] for row in completed)
                    if completed else None
                ),
            }
    for family in CONFIG["families"]:
        # One full support observation per list; both target workloads may
        # otherwise repeat that same target-independent measurement.
        observations = {}
        for row in rows:
            case = by_case[row["case_id"]]
            if (
                row["method"] == "core_distinct"
                and case["family"] == family
                and row["stats"]["distinct_sums_complete"]
            ):
                observations[case["list_id"]] = row
        values = list(observations.values())
        summary["families"][family] = {
            "lists_with_full_support": len(values),
            "k_range": [min(row["stats"]["k"] for row in values), max(row["stats"]["k"] for row in values)],
            "M_range": [
                min(row["stats"]["distinct_exception_sums"] for row in values),
                max(row["stats"]["distinct_exception_sums"] for row in values),
            ],
            "median_selection_to_sum_ratio": median(
                2 ** row["stats"]["k"] / row["stats"]["distinct_exception_sums"]
                for row in values
            ),
        }
    return summary


def plot_results(output, cases, rows):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return False
    import math

    by_case = {case["case_id"]: case for case in cases}
    observations = {}
    for row in rows:
        case = by_case[row["case_id"]]
        if row["method"] == "core_distinct" and row["stats"]["distinct_sums_complete"]:
            observations[case["list_id"]] = (case, row)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), constrained_layout=True)
    colors = {"unrelated": "#315c88", "repeated": "#b66a2c"}
    for family in CONFIG["families"]:
        group = [(case, row) for case, row in observations.values() if case["family"] == family]
        axes[0].scatter(
            [row["stats"]["k"] for _, row in group],
            [math.log2(row["stats"]["distinct_exception_sums"]) for _, row in group],
            color=colors[family], alpha=0.75, label=family,
        )
    grid = list(range(13))
    axes[0].plot(grid, grid, "--", color="#777777", linewidth=1, label="M = 2^k")
    axes[0].plot(grid, [math.log2(k + 1) for k in grid], ":", color="#777777", label="M = k + 1")
    axes[0].set(xlabel="Actual deletion distance k", ylabel="log2 distinct exceptional sums M")
    axes[0].set_title("Exceptions can create very different residual supports")
    axes[0].legend(fontsize=8)
    full_M = {
        row["case_id"]: row["stats"]["distinct_exception_sums"]
        for row in rows
        if row["method"] == "core_distinct" and row["stats"]["distinct_sums_complete"]
    }
    for method, marker, label in (
        ("core_distinct", "o", "merge sums"),
        ("core_enumerate", "x", "enumerate selections"),
    ):
        group = [
            row for row in rows
            if row["method"] == method and row["case_id"] in full_M
            and row["status"] != "unresolved"
        ]
        axes[1].scatter(
            [full_M[row["case_id"]] for row in group],
            [1000 * row["stats"]["total_seconds"] for row in group],
            marker=marker, alpha=0.55, s=22, label=label,
        )
    axes[1].set(
        xscale="log", yscale="log",
        xlabel="Distinct exceptional sums M",
        ylabel="Total instrumented time (ms)",
    )
    axes[1].set_title("Early YES and preprocessing both affect elapsed cost")
    axes[1].legend(fontsize=8)
    fig.suptitle("Exploratory structural-distance pilot — 48 lists, 96 targets", fontsize=12)
    fig.savefig(output / "pilot.png", dpi=170)
    fig.savefig(output / "pilot.svg")
    plt.close(fig)
    return True


def write_report(output, summary, plotted):
    lines = [
        "# Exploratory structural-distance pilot",
        "",
        "**Status:** Development evidence for the first prototype. This is not the frozen prospective comparison.",
        "",
        f"The pilot used {summary['lists']} lists and {summary['cases']} list-target cases: "
        f"{summary['truth_counts'].get('yes', 0)} YES and {summary['truth_counts'].get('no', 0)} NO. "
        f"All {summary['answers_checked']} completed solver answers agreed with the independent exact labels; "
        "all returned witnesses were checked against original indices.",
        "",
        "Sizes are 16, 24, and 32; injected counts are 0, 4, 8, and 12; "
        "families have unrelated or repeated exceptions, with two lists per cell. "
        "Each list has a planted-subset target and an unfiltered uniform middle-range target, "
        "both labeled by an independent full half-enumeration oracle.",
        "",
        "## Completion and total elapsed cost",
        "",
        "Medians below include all attempted runs, including unresolved runs. "
        "The matched comparison includes only cases completed by both the method and MITM. "
        "One shuffled-order, instrumented Python run per case is descriptive timing evidence.",
        "",
        "| Method | Completed / 96 | Median all attempts (ms) | Faster than MITM / matched cases |",
        "|---|---:|---:|---:|",
    ]
    for method, item in summary["methods"].items():
        lines.append(
            f"| {method} | {item['completed']} | {item['median_all_attempts_ms']:.4f} | "
            f"{item['faster_than_mitm']} / {item['matched_mitm_cases']} |"
        )
    lines += [
        "",
        "Unresolved outcomes and their reasons are retained in the raw data and summary. "
        "The bitset method is decision-only and has a separate 8-million-bit width cap; "
        "the other methods return indexed YES witnesses. Its times do not include witness storage.",
        "",
        "## YES and NO workloads",
        "",
        "Each median below uses only completed runs in the stated truth stratum; "
        "different completion sets need not be matched.",
        "",
        "| Method | YES completed | YES median ms | NO completed | NO median ms |",
        "|---|---:|---:|---:|---:|",
    ]
    for method, item in summary["methods"].items():
        yes, no = item["truth_strata"]["yes"], item["truth_strata"]["no"]
        fmt = lambda value: "—" if value is None else f"{value:.4f}"
        lines.append(
            f"| {method} | {yes['completed']} | {fmt(yes['median_completed_ms'])} | "
            f"{no['completed']} | {fmt(no['median_completed_ms'])} |"
        )
    lines += [
        "",
        "## Measured structural distance and residual support",
        "",
        "Use one completed full support measurement per list. A root rejection or an interrupted "
        "support construction does not supply M.",
        "",
        "| Exceptional family | Lists with M | Actual k range | M range | Median 2^k / M |",
        "|---|---:|---:|---:|---:|",
    ]
    for family, item in summary["families"].items():
        lines.append(
            f"| {family} | {item['lists_with_full_support']} | {item['k_range']} | "
            f"{item['M_range']} | {item['median_selection_to_sum_ratio']:.2f} |"
        )
    lines += [
        "",
        "Repeated injected items duplicate a core value, so the detected exceptions create "
        "only k+1 sums. Unrelated exceptions can create nearly 2^k sums. "
        "A smaller support is a mechanism for reducing queries, but does not by itself establish "
        "a faster solver: generation has a cost, and selection enumeration can stop early on YES.",
        "",
        "## Limits and next experiment",
        "",
        "- No novelty claim or universal speedup follows from this pilot.",
        "- Core discovery and verification are included in structural-solver elapsed time.",
        "- State counters describe residual records and snapshots, not exact byte memory. "
        "Input/core storage and Python object overhead require separate profiling.",
        "- Explicit work units count different primitive operations in different methods. "
        "Bitset operations process many bits and are not comparable to one scalar query step.",
        "- Complete the literature audit, choose useful scales and budgets, profile bytes "
        "separately, and freeze a fresh comparison before interpreting practical advantages.",
        "- Compare alternative cores next: minimum deletion count need not minimize residual support.",
        "",
        "Configuration and source hashes are in [manifest.json](manifest.json). "
        "Inputs and oracle labels are in [cases.jsonl](cases.jsonl); "
        "measurements are in [runs.jsonl](runs.jsonl); "
        "aggregates are in [summary.json](summary.json).",
    ]
    if plotted:
        lines += ["", "![Exploratory residual support and elapsed cost](pilot.png)"]
    (output / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=HERE / "results" / "pilot_20261024")
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        parser.error("output already exists; choose a new directory to preserve prior measurements")
    output.mkdir(parents=True)
    limits = Limits(max_seconds=1.0)
    methods = {
        "core_distinct": lambda w, t: solve(w, t, method="distinct", limits=limits),
        "core_enumerate": lambda w, t: solve(w, t, method="enumerate", limits=limits),
        "mitm": lambda w, t: solve_mitm(w, t, limits=limits),
        "dfs": lambda w, t: solve_dfs(w, t, limits=limits),
        "bitset": lambda w, t: solve_bitset(w, t, limits=limits),
    }
    manifest = {
        "config": CONFIG, "limits": asdict(limits), "methods": list(methods),
        "python": sys.version, "platform": platform.platform(), "source_hashes": source_hashes(),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    cases, rows = [], []
    order_rng = random.Random(CONFIG["seed"])
    started = perf_counter()
    with (
        (output / "cases.jsonl").open("w", encoding="utf-8") as case_file,
        (output / "runs.jsonl").open("w", encoding="utf-8") as run_file,
    ):
        for n in CONFIG["sizes"]:
            for injected in CONFIG["injected_counts"]:
                for family in CONFIG["families"]:
                    for replicate in range(CONFIG["replicates"]):
                        list_id = f"n{n}-injected{injected}-{family}-r{replicate}"
                        rng = random.Random(f"{CONFIG['seed']}:{list_id}")
                        weights = make_weights(n, injected, family, rng)
                        descriptor = find_core(weights)
                        oracle_start = perf_counter()
                        halves = oracle_halves(weights)
                        oracle_seconds = perf_counter() - oracle_start
                        targets = (
                            ("planted", sum(w for w in weights if rng.getrandbits(1))),
                            ("uniform_middle", rng.randint(round(.30 * sum(weights)), round(.70 * sum(weights)))),
                        )
                        for target_rule, target in targets:
                            oracle_mask = oracle_query(halves, target)
                            truth = oracle_mask is not None
                            if oracle_mask is not None:
                                assert sum(w for i, w in enumerate(weights) if oracle_mask >> i & 1) == target
                            case = {
                                "case_id": f"{list_id}-{target_rule}", "list_id": list_id,
                                "n": n, "injected": injected, "family": family,
                                "replicate": replicate, "target_rule": target_rule,
                                "weights": weights, "target": target,
                                "max_weight_bits": max(w.bit_length() for w in weights),
                                "actual_k": len(descriptor.exceptions),
                                "truth": "yes" if truth else "no",
                                "oracle_witness_mask": oracle_mask,
                                "oracle_preprocessing_seconds": oracle_seconds,
                            }
                            cases.append(case)
                            case_file.write(json.dumps(case) + "\n")
                            order = list(methods)
                            order_rng.shuffle(order)
                            for method in order:
                                result = methods[method](weights, target)
                                check_result(weights, target, truth, result)
                                if result.stats["k"] is not None:
                                    assert result.stats["k"] == case["actual_k"]
                                row = {"case_id": case["case_id"], "method": method, **result.to_dict()}
                                rows.append(row)
                                run_file.write(json.dumps(row) + "\n")
                        print(f"Completed {list_id}", flush=True)
    assert source_hashes() == manifest["source_hashes"], "source changed during the pilot"
    summary = summarize(cases, rows)
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    plotted = plot_results(output, cases, rows)
    write_report(output, summary, plotted)
    print(f"{summary['answers_checked']} completed answers checked; 0 mismatches.")
    print(f"Saved {output}; elapsed {perf_counter() - started:.2f}s")


if __name__ == "__main__":
    main()
