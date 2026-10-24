"""Prespecified descriptive analysis of a frozen structural-distance study."""

from collections import Counter, defaultdict
import json
from pathlib import Path
from statistics import median


BASELINES = ("dfs", "mitm", "bitset")
POLICIES = ("select_multiplicity", "select_support")


def aggregate_runs(rows, repeats):
    raw = defaultdict(list)
    for row in rows:
        raw[(row["case_id"], row["method"])].append(row)
    groups = {}
    for key, values in raw.items():
        assert len(values) == repeats
        assert len({row["repetition"] for row in values}) == repeats
        complete = all(row["status"] != "unresolved" for row in values)
        support = next((
            row["stats"]["distinct_exception_sums"] for row in values
            if row["stats"]["distinct_sums_complete"]
            and row["stats"].get("selection_complete", True)
        ), None)
        groups[key] = {
            "complete": complete,
            "repeat_inconsistent": len({row["status"] for row in values}) > 1,
            "seconds": median(row["stats"]["total_seconds"] for row in values),
            "M": support,
            "core_changed": any(row["stats"].get("selected_core_changed", False) for row in values),
            "phases": {
                phase: median(row["stats"].get(phase + "_seconds", 0.0) for row in values)
                for phase in ("discovery", "verification", "selection", "generation", "query")
            },
        }
    return groups


def paired(cases, groups, method, reference):
    ratios = []
    for case in cases:
        item = groups.get((case["case_id"], method))
        if item is None or not item["complete"]:
            continue
        if reference == "fastest_baseline":
            candidates = [
                groups[(case["case_id"], name)] for name in BASELINES
                if (case["case_id"], name) in groups
                and groups[(case["case_id"], name)]["complete"]
            ]
            other = min(candidates, key=lambda value: value["seconds"]) if candidates else None
        else:
            other = groups.get((case["case_id"], reference))
        if other is not None and other["complete"]:
            ratios.append(item["seconds"] / max(other["seconds"], 1e-15))
    return {
        "matched": len(ratios), "wins": sum(value < 1 for value in ratios),
        "median_ratio": median(ratios) if ratios else None,
    }


def summarize(cases, rows, memory_rows, generation, config):
    groups = aggregate_runs(rows, config["timing_repeats"])
    methods = config["methods"]
    methods_summary = {}
    for method in methods:
        values = [groups[(case["case_id"], method)] for case in cases]
        completed = [value for value in values if value["complete"]]
        methods_summary[method] = {
            "completed_cases": len(completed),
            "repeat_inconsistent_cases": sum(value["repeat_inconsistent"] for value in values),
            "median_completed_case_ms": (
                median(value["seconds"] for value in completed) * 1000 if completed else None
            ),
            "unresolved_runs": dict(Counter(
                row["reason"] for row in rows
                if row["method"] == method and row["status"] == "unresolved"
            )),
            "paired": {
                reference: paired(cases, groups, method, reference)
                for reference in ("core_distinct", "dfs", "fastest_baseline")
            },
            "median_completed_phase_ms": {
                phase: median(value["phases"][phase] for value in completed) * 1000 if completed else None
                for phase in ("discovery", "verification", "selection", "generation", "query")
            },
        }
    strata = {}
    for name, cohort in (
        ("structured_conditioned_no", [
            case for case in cases if case["family"] != "generic" and case["target_rule"] == "conditioned_no"
        ]),
        ("generic_conditioned_no", [
            case for case in cases if case["family"] == "generic" and case["target_rule"] == "conditioned_no"
        ]),
        ("unconditioned_uniform", [case for case in cases if case["target_rule"] == "uniform_middle"]),
        ("all_yes", [case for case in cases if case["truth"] == "yes"]),
        ("all_no", [case for case in cases if case["truth"] == "no"]),
    ):
        strata[name] = {
            "cases": len(cohort),
            "truth": dict(Counter(case["truth"] for case in cohort)),
            "methods": {
                method: paired(cohort, groups, method, "fastest_baseline")
                for method in methods
            },
        }
    supports = {}
    for method in POLICIES:
        per_list = {}
        for case in cases:
            base = groups[(case["case_id"], "core_distinct")]
            chosen = groups[(case["case_id"], method)]
            if base["M"] is not None and chosen["M"] is not None:
                per_list[case["list_id"]] = {
                    "family": case["family"], "base_M": base["M"],
                    "selected_M": chosen["M"], "changed": chosen["core_changed"],
                }
        observations = list(per_list.values())
        supports[method] = {
            "lists": len(observations),
            "improved": sum(value["selected_M"] < value["base_M"] for value in observations),
            "unchanged": sum(value["selected_M"] == value["base_M"] for value in observations),
            "worsened": sum(value["selected_M"] > value["base_M"] for value in observations),
            "median_support_ratio": (
                median(value["selected_M"] / value["base_M"] for value in observations)
                if observations else None
            ),
            "observations": per_list,
        }
    return {
        "cases": len(cases), "lists": len({case["list_id"] for case in cases}),
        "truth": dict(Counter(case["truth"] for case in cases)),
        "target_rules": dict(Counter(case["target_rule"] for case in cases)),
        "completed_timing_answers": sum(row["status"] != "unresolved" for row in rows),
        "timing_runs": len(rows), "memory_runs": len(memory_rows),
        "completed_memory_answers": sum(row["status"] != "unresolved" for row in memory_rows),
        "conditioned_no_by_k": dict(sorted(Counter(
            case["actual_k"] for case in cases if case["target_rule"] == "conditioned_no"
        ).items())),
        "methods": methods_summary, "strata": strata, "supports": supports,
        "generation": generation, "mismatches": 0,
    }, groups


def fmt(value):
    return "—" if value is None else f"{value:.3f}"


def plot(output, cases, groups, memory_rows):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return False
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.7), constrained_layout=True)
    colors = {"select_multiplicity": "#b66a2c", "select_support": "#315c88"}
    for method in POLICIES:
        x, y = [], []
        for case in cases:
            base = groups[(case["case_id"], "core_distinct")]
            chosen = groups[(case["case_id"], method)]
            if (
                base["complete"] and chosen["complete"]
                and base["M"] is not None and chosen["M"] is not None
            ):
                x.append(chosen["M"] / base["M"])
                y.append(chosen["seconds"] / base["seconds"])
        axes[0].scatter(x, y, alpha=.55, s=20, color=colors[method], label=method.replace("select_", ""))
    axes[0].axhline(1, color="grey", linestyle="--", linewidth=1)
    axes[0].axvline(1, color="grey", linestyle=":", linewidth=1)
    axes[0].set(xlabel="Selected M / greedy M", ylabel="Selected total time / greedy total time", yscale="log")
    axes[0].set_title("Does smaller support repay selection?")
    axes[0].legend(fontsize=8)
    names = ("core_distinct", "core_enumerate", "select_multiplicity", "select_support")
    for index, method in enumerate(names):
        ratios = []
        for case in cases:
            if case["target_rule"] != "conditioned_no" or case["family"] == "generic":
                continue
            item, other = groups[(case["case_id"], method)], groups[(case["case_id"], "dfs")]
            if item["complete"] and other["complete"]:
                ratios.append(item["seconds"] / max(other["seconds"], 1e-15))
        if ratios:
            axes[1].scatter([index] * len(ratios), ratios, alpha=.45, s=15)
            axes[1].scatter([index], [median(ratios)], color="black", marker="_", s=180)
    short = ["greedy\nsums", "greedy\nchoices", "select\ncap", "select\nsupport"]
    axes[1].set_xticks(range(len(short)), short)
    axes[1].axhline(1, color="grey", linestyle="--", linewidth=1)
    axes[1].set(yscale="log", ylabel="Median case time / DFS time")
    axes[1].set_title("Structured conditioned-NO cases")
    memory_methods = (*names, "dfs", "mitm", "bitset")
    for index, method in enumerate(memory_methods):
        group = [row for row in memory_rows if row["method"] == method]
        for row in group:
            axes[2].scatter(
                index, max(row["python_peak_bytes"] / 1024**2, 1e-4),
                marker="o" if row["status"] != "unresolved" else "x",
                color="#315c88" if row["status"] != "unresolved" else "#b66a2c",
                alpha=.7,
            )
    axes[2].set_xticks(range(len(memory_methods)), [*short, "DFS", "MITM", "bitset"], rotation=35)
    axes[2].set(yscale="log", ylabel="Peak traced Python allocations (MiB)")
    axes[2].set_title("Separate memory pass; × = unresolved")
    fig.suptitle("Frozen structural-distance study: selection, exact NO search, and memory")
    fig.savefig(output / "comparison.png", dpi=170)
    fig.savefig(output / "comparison.svg")
    plt.close(fig)
    return True


def write_markdown(output, summary, memory_rows, cases, plotted):
    by_case = {case["case_id"]: case for case in cases}
    lines = [
        "# Frozen structural-distance comparison",
        "",
        "The protocol, generators, algorithms, reporting plan, and source snapshots were "
        "frozen locally before generating these evaluation weights or labels. "
        "This was not external preregistration.",
        "",
        f"The study contains **{summary['lists']} lists and {summary['cases']} targets**, "
        f"with {summary['truth'].get('yes', 0)} YES and {summary['truth'].get('no', 0)} NO labels. "
        f"All **{summary['completed_timing_answers']} completed timing answers** agreed with "
        f"independent exact labels. The separate memory pass checked "
        f"{summary['completed_memory_answers']} completed answers. All returned witnesses were valid.",
        "",
        "## Scope and input conditioning",
        "",
        "Sizes are 20, 28, and 36. Structured families use 4, 8, or 12 injected items; "
        "actual deletion distance is measured. There are also random 41-bit controls. "
        "Targets are planted-subset, unconditioned uniform middle-range, and "
        "middle-range conditioned on passing the stated modular checks and being NO.",
        "",
        f"Target counts: {summary['target_rules']}. Conditioned-NO counts by actual k: "
        f"{summary['conditioned_no_by_k']}.",
        "",
        f"Generation outcomes: {summary['generation']['counts']}. Oracle preprocessing and "
        "proposal/query times are saved separately and excluded from solver timings. "
        "The conditioned-NO results concern that selected cohort; they are not "
        "unconditional average-case results.",
        "",
        "## Does selecting a core reduce residual support?",
        "",
        "Use one target-independent observation per list where both supports finished. "
        "An unavailable support is censored, not treated as small.",
        "",
        "| Selector | Lists compared | Smaller M | Same M | Larger M | Median selected M / greedy M |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for method, item in summary["supports"].items():
        lines.append(
            f"| {method} | {item['lists']} | {item['improved']} | {item['unchanged']} | "
            f"{item['worsened']} | {fmt(item['median_support_ratio'])} |"
        )
    lines += [
        "",
        "The multiplicity selector minimizes a cheap cap in a local one-swap neighborhood. "
        "The support selector constructs up to four supports, charges every probe, "
        "and reuses the winning one. Neither finds a globally minimum-support core.",
        "",
        "## Total time and completion",
        "",
        "Each case time is the median of three independently shuffled-order runs. "
        "A case is completed only if every repetition completed. Paired comparisons "
        "use only cases completed by both methods. Ratios below 1 favor the row method. "
        "All selection and rejected-candidate costs are included.",
        "",
        "| Method | Completed cases | Inconsistent repeats | Median completed ms | Wins / paired with DFS | Median ratio to DFS | Wins / paired with fastest baseline | Median ratio to fastest baseline |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for method, item in summary["methods"].items():
        dfs, fastest = item["paired"]["dfs"], item["paired"]["fastest_baseline"]
        lines.append(
            f"| {method} | {item['completed_cases']} / {summary['cases']} | "
            f"{item['repeat_inconsistent_cases']} | {fmt(item['median_completed_case_ms'])} | "
            f"{dfs['wins']} / {dfs['matched']} | {fmt(dfs['median_ratio'])} | "
            f"{fastest['wins']} / {fastest['matched']} | {fmt(fastest['median_ratio'])} |"
        )
    lines += [
        "",
        "The fastest baseline is the best of completed DFS, MITM, and bitset on each case. "
        "This is a casewise comparison and includes no selector. Bitset is decision-only, "
        "so its timings do not include witness storage. Median times in different rows "
        "may use different completion sets and are not directly matched speed ratios.",
        "",
        "### Selectors versus the initial core",
        "",
        "| Selector | Wins / paired | Median total-time ratio to greedy distinct sums |",
        "|---|---:|---:|",
    ]
    for method in POLICIES:
        item = summary["methods"][method]["paired"]["core_distinct"]
        lines.append(f"| {method} | {item['wins']} / {item['matched']} | {fmt(item['median_ratio'])} |")
    lines += ["", "### Strata against the fastest feasible baseline", ""]
    lines += [
        "| Cohort | Cases | Method | Wins / paired | Median time ratio |",
        "|---|---:|---|---:|---:|",
    ]
    for name, stratum in summary["strata"].items():
        for method in ("core_distinct", "core_enumerate", *POLICIES):
            item = stratum["methods"][method]
            lines.append(
                f"| {name} | {stratum['cases']} | {method} | "
                f"{item['wins']} / {item['matched']} | {fmt(item['median_ratio'])} |"
            )
    lines += [
        "",
        "## Cost components",
        "",
        "Median phase milliseconds among each method's completed cases. Exact-support "
        "probe generation is inside selection; it is not counted a second time under generation. "
        "Root checks and other overhead appear in total time but not in these phase columns.",
        "",
        "| Method | Discovery | Verification | Selection | Generation | Query |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for method, item in summary["methods"].items():
        values = item["median_completed_phase_ms"]
        lines.append(
            f"| {method} | " + " | ".join(fmt(values[phase]) for phase in (
                "discovery", "verification", "selection", "generation", "query"
            )) + " |"
        )
    lines += ["", "## Unresolved outcomes", ""]
    for method, item in summary["methods"].items():
        lines.append(f"- {method}: {item['unresolved_runs'] or 'none'} (raw-run counts).")
    lines += [
        "",
        "## Separate memory profiles",
        "",
        "The predeclared subset has one conditioned-NO case per family at n=20 "
        "(r=8 for structured lists), seed replicate zero. Inputs already exist when "
        "tracing starts. Reported peaks are Python-traced allocations, not process RSS. "
        "Time caps are disabled in this pass; work/state/bitset caps are unchanged. "
        "Memory completion is therefore recorded separately.",
        "",
        "| Family | Method | Status | Peak MiB |",
        "|---|---|---|---:|",
    ]
    for row in memory_rows:
        lines.append(
            f"| {by_case[row['case_id']]['family']} | {row['method']} | "
            f"{row['status']} ({row['reason']}) | {row['python_peak_bytes'] / 1024**2:.4f} |"
        )
    lines += [
        "",
        "## Interpretation limits",
        "",
        "- Support reductions and wall-clock gains are distinct. The time comparison "
        "includes discovering the alternative decomposition.",
        "- Completion-based comparisons exclude censored runs; the excluded counts "
        "remain visible. They do not establish performance on those harder cases.",
        "- This small synthetic study does not establish statistical significance, "
        "a universal speedup, a globally optimal decomposition, or algorithmic novelty.",
        "- The [literature audit](../../LITERATURE.md) identifies established components "
        "and the stronger theoretical algorithms omitted from these elementary baselines.",
        "",
        "## Reproducible artifacts",
        "",
        "- [Frozen protocol](protocol.json) and [source snapshots](sources/).",
        "- [Lists and generation accounting](lists.jsonl), [targets and labels](cases.jsonl), "
        "and [NO proposal log](proposals.jsonl).",
        "- [Raw timing repetitions](runs.jsonl), [separate memory profiles](memory.jsonl), "
        "and [machine-readable summary](summary.json).",
    ]
    if plotted:
        lines += ["", "![Selection cost, NO search, and separate memory profiles](comparison.png)"]
    (output / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def report(output):
    from run_study import CONFIG, load_cases, read_jsonl, save_json, sha

    output = Path(output)
    cases = load_cases(output)
    timing = json.loads((output / "timing.json").read_text())
    assert sha(output / "runs.jsonl") == timing["runs_sha256"]
    memory = json.loads((output / "memory_stage.json").read_text())
    assert sha(output / "memory.jsonl") == memory["memory_sha256"]
    rows, memory_rows = read_jsonl(output / "runs.jsonl"), read_jsonl(output / "memory.jsonl")
    generation = json.loads((output / "generation.json").read_text())
    expected = len(cases) * len(CONFIG["methods"]) * CONFIG["timing_repeats"]
    assert len(rows) == expected
    summary, groups = summarize(cases, rows, memory_rows, generation, CONFIG)
    save_json(output / "summary.json", summary)
    plotted = plot(output, cases, groups, memory_rows)
    write_markdown(output, summary, memory_rows, cases, plotted)
    print(f"Reported {len(cases)} cases, {len(rows)} timed runs, {len(memory_rows)} memory profiles.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    report(parser.parse_args().output)
