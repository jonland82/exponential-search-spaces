"""Reproducible tolerance sweep for certified closest-subset-sum bounds.

Run from the repository root. The numerical benchmark needs only Python's
standard library; plotting additionally uses matplotlib. No solver sees an
oracle answer. Generation, validation, memory tracing, and plotting are not timed.
"""

from __future__ import annotations

import argparse
import json
import platform
import random
import statistics
import time
import tracemalloc
from fractions import Fraction
from pathlib import Path

from certified_approximation import DEFAULT_MAX_STATES, METHODS, brute_force_distance, solve
from experiment import make_case as original_case
from hard_experiment import make_case as hard_case


HERE = Path(__file__).parent
FAMILIES = ("narrow", "wide", "mixed_no", "modular_no", "unique", "pairs", "isolated", "clustered")
TOLERANCES = ("1e-2", "1e-4", "1e-6", "exact")
LABELS = {
    "paired_additive": "Paired additive",
    "sequential_additive": "Sequential additive",
    "trimmed_multiplicative": "Multiplicative trim",
    "exact_mitm": "Exact-half MITM",
}


def make_case(family: str, n: int, seed: int) -> tuple[list[int], int]:
    if family in ("narrow", "wide", "mixed_no", "modular_no"):
        return original_case(family, n, seed)
    if family in ("unique", "pairs"):
        weights, target, _ = hard_case(family, n, seed)
        return weights, target
    rng = random.Random(f"closest:{family}:{n}:{seed}")
    if family == "isolated":
        # A superincreasing control: a unique closest subset, separated by 1000.
        # Descending greedy is effective here; this is NOT a hardness claim.
        weights = [1000 * 3**i for i in range(n)]
        target = sum(weight for weight in weights if rng.randrange(2)) + 1
    elif family == "clustered":
        # Many selections with the same cardinality have sums in a narrow band.
        weights = [10**9 + rng.randrange(21) for _ in range(n)]
        target = (n // 2) * 10**9 + 10 * (n // 2) + 1
    else:
        raise ValueError(family)
    rng.shuffle(weights)
    return weights, target


def verify(result, weights: list[int], target: int, optimum: int) -> None:
    actual = sum(weight for i, weight in enumerate(weights) if result.subset_mask >> i & 1)
    assert actual == result.subset_sum
    assert abs(actual - target) == result.upper
    assert result.lower <= optimum <= result.upper
    assert result.subset_mask < 1 << len(weights)
    if result.status == "certified":
        assert result.width <= result.tolerance
    else:
        assert result.status == "state_limit"


def measured(weights, target, tolerance, method, greedy, optimum, repeats, max_states):
    timings = []
    first = None
    for _ in range(repeats):
        start = time.perf_counter()
        answer = solve(weights, target, tolerance, method, greedy=greedy, max_states=max_states)
        timings.append(time.perf_counter() - start)
        verify(answer, weights, target, optimum)
        if first is None:
            first = answer.as_dict()
        else:
            assert answer.as_dict() == first
        if answer.status != "certified":
            break  # Do not spend three runs rediscovering the same state cap.
    tracemalloc.start()
    try:
        memory_answer = solve(weights, target, tolerance, method, greedy=greedy, max_states=max_states)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert memory_answer.as_dict() == first
    return {
        **first,
        "seconds": statistics.median(timings),
        "timing_runs": len(timings),
        "peak_traced_mib": peak / 1024**2,
        "witness_excess": first["upper"] - optimum,
    }


def run(*, quick=False, repeats=3, max_states=DEFAULT_MAX_STATES, checkpoint=None):
    sizes, seeds = ((12, 16), (0,)) if quick else ((16, 24, 32), (0, 1))
    families = ("wide", "unique", "isolated", "clustered") if quick else FAMILIES
    data = {
        "complete": False,
        "date": "2026-10-22",
        "python": platform.python_version(),
        "machine": platform.platform(),
        "sizes": sizes,
        "seeds": seeds,
        "families": families,
        "tolerance_fractions_of_total": TOLERANCES,
        "repeats": repeats,
        "max_summary_states": max_states,
        "cases": [],
        "rows": [],
    }
    for family in families:
        for n in sizes:
            for seed in seeds:
                weights, target = make_case(family, n, seed)
                # A separate exact closest-sum oracle, not the old YES/NO solver.
                oracle = solve(weights, target, 0, "exact_mitm", greedy=False, max_states=1 << ((n + 1) // 2))
                assert oracle.status == "certified" and oracle.width == 0
                optimum = oracle.upper
                verify(oracle, weights, target, optimum)
                if n <= 16:
                    assert brute_force_distance(weights, target) == optimum
                case_id = f"{family}:{n}:{seed}"
                data["cases"].append({
                    "id": case_id, "family": family, "n": n, "seed": seed,
                    "weights": weights, "target": target, "total": sum(weights),
                    "exact_distance": optimum, "oracle": oracle.as_dict(),
                })
                modes = (True, False) if n == max(sizes) else (True,)
                for greedy in modes:
                    for label in TOLERANCES:
                        tolerance = 0 if label == "exact" else int(Fraction(label) * sum(weights))
                        # Rotate execution order to reduce a fixed method-order bias.
                        offset = (seed + TOLERANCES.index(label)) % len(METHODS)
                        order = METHODS[offset:] + METHODS[:offset]
                        results = {
                            method: measured(weights, target, tolerance, method, greedy, optimum, repeats, max_states)
                            for method in order
                        }
                        data["rows"].append({
                            "case_id": case_id, "family": family, "n": n, "seed": seed,
                            "greedy": greedy, "tolerance_label": label, "tolerance": tolerance,
                            "results": results,
                        })
                if checkpoint:
                    checkpoint.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
                print(f"{case_id:20} optimum distance={optimum} done", flush=True)
    data["complete"] = True
    return data


def summary(data: dict) -> dict:
    groups = []
    largest = max(data["sizes"])
    for greedy in (True, False):
        for label in TOLERANCES:
            rows = [r for r in data["rows"] if r["n"] == largest and r["greedy"] == greedy and r["tolerance_label"] == label]
            methods = {}
            for method in METHODS:
                successful = [r["results"][method] for r in rows if r["results"][method]["status"] == "certified"]
                methods[method] = {
                    "certified": len(successful), "total": len(rows),
                    "median_seconds": statistics.median(x["seconds"] for x in successful) if successful else None,
                    "median_peak_traced_mib": statistics.median(x["peak_traced_mib"] for x in successful) if successful else None,
                    "greedy_stops": sum(x["reason"] == "greedy_witness" for x in successful),
                    "median_width": statistics.median(x["width"] for x in successful) if successful else None,
                }
            comparisons = {}
            for baseline in METHODS[1:]:
                matched = [r for r in rows if all(r["results"][m]["status"] == "certified" for m in ("paired_additive", baseline))]
                ratios = [r["results"][baseline]["seconds"] / r["results"]["paired_additive"]["seconds"] for r in matched]
                comparisons[baseline] = {
                    "matched": len(matched),
                    "paired_faster": sum(ratio > 1 for ratio in ratios),
                    "median_baseline_over_paired": statistics.median(ratios) if ratios else None,
                }
            groups.append({"greedy": greedy, "tolerance_label": label, "n": largest, "methods": methods, "comparisons": comparisons})
    return {"groups": groups}


def write_report(data: dict, path: Path) -> None:
    largest = max(data["sizes"])
    groups = summary(data)["groups"]
    total_results = sum(len(row["results"]) for row in data["rows"])
    limits = sum(result["status"] == "state_limit" for row in data["rows"] for result in row["results"].values())
    detail = next(g for g in groups if not g["greedy"] and g["tolerance_label"] == "1e-4")
    sequential = detail["comparisons"]["sequential_additive"]
    sequential_ratio = (
        "unavailable (no jointly certified inputs)"
        if sequential["median_baseline_over_paired"] is None
        else f"{sequential['median_baseline_over_paired']:.3f}"
    )
    lines = [
        "# Does pairing add value to certified approximation?", "",
        "Series navigation: [reading order](../index.html#arc) · [Note IV: pairing in certified approximation](../Certified_Approximation_of_Subset_Sum.html).", "",
        '**Central question:** "If we only need to get close to the target, and know how close, can our framework avoid much of the exponential search?"', "",
        "This experiment supports [Note IV](../Certified_Approximation_of_Subset_Sum.html). "
        "Its added-value question is whether pairing error-bounded summaries improves on applying "
        "the same approximation rule sequentially. The [mathematical specification](APPROXIMATION_SPEC.md) "
        "supplies a common correctness contract using established approximation ideas.", "",
        "## The controlled comparison", "",
        f"With common greedy disabled, n={largest}, and epsilon=1e-4, pairing is faster than sequential "
        f"additive trimming on {sequential['paired_faster']} of {sequential['matched']} jointly certified inputs. "
        f"The median per-input sequential/paired time ratio is {sequential_ratio}. "
        f"Paired summaries certify {detail['methods']['paired_additive']['certified']} of "
        f"{detail['methods']['paired_additive']['total']} inputs within the per-summary state cap; "
        f"sequential additive certifies {detail['methods']['sequential_additive']['certified']}. "
        "This is the comparison that isolates the organization of the summaries while holding "
        "the additive approximation rule fixed. The paper treats its negative timing finding and "
        "the resource-limit exception as the result, scoped to the tested setting. The full sweep below "
        "also retains regimes where pairing helps, including exact half-summary organization.", "",
        "## Experimental contract", "",
        "Find a subset on either side of a fixed target. Return its actual sum and deterministic bounds "
        "on the minimum absolute distance. A result is certified when upper minus lower is at most the absolute tolerance. "
        "Tolerance is floor(epsilon * sum(weights)); epsilon is 1e-2, 1e-4, 1e-6, or zero. "
        "The absolute tolerance may already be zero on small-weight inputs.", "",
        "Four Python implementations retain original-item witnesses and use exact integer arithmetic: "
        "paired additive summaries, sequential additive summaries (the pairing ablation), a multiplicatively "
        "trimmed sequential list adapted to the full sum range, and exact-half meet-in-the-middle. "
        "The conventional multiplicative trimming baseline is adapted from "
        "[these lecture notes](https://courses.grainger.illinois.edu/cs473/fa2015/w/lec/slides/10_notes.pdf); "
        "it is not a benchmark of the fastest published approximation algorithms. "
        "All four can stop as soon as a witness lies within tolerance, since zero is always a lower bound.", "",
        f"There are {len(data['cases'])} generated list-target instances across sizes {list(data['sizes'])}, "
        f"with seeds {list(data['seeds'])}. Every method receives the same descending item order. "
        "The main comparison includes the same greedy witness search for all methods; the largest size also "
        "runs without it. The ablation still permits witness-based stopping during summary construction. "
        "Exact optima are computed separately and never supplied to a solver. "
        "All lists with at most 16 items are additionally checked by independent Gray-code enumeration.", "",
        "Families reuse narrow, wide planted, mixed no-solution, modular no-solution, and the prior "
        "41-bit unique/pair hard cases. Two added controls are superincreasing weights with a unique nearest subset "
        "(isolated, deliberately easy for descending greedy) and nearly equal billion-scale weights "
        "with many sums near the target (clustered). Raw weights, seeds, targets, optima, returned witnesses, "
        "bounds, merge counts, and method outcomes are all recorded.", "",
        f"A method may retain at most {data['max_summary_states']:,} representatives in one summary. "
        f"Of {total_results} method outcomes, {limits} hit that cap. These return honest partial bounds "
        "and are counted as failures to reach the requested tolerance, not as fast successful answers. "
        "The cap is on an individual summary, not total memory; paired methods hold both halves.", "",
        f"Successful times are medians of {data['repeats']} uninstrumented runs. "
        "State-limit outcomes are timed once. Peak Python-traced memory is measured in a separate run "
        "and is not process RSS. Input generation, oracle computation, verification, and plotting are excluded "
        "from solver timing. Execution order rotates across tolerances and seeds. "
        f"Environment: Python {data['python']}, {data['machine']}.", "",
        f"## Largest-size results (n={largest})", "",
        "Each cell is median milliseconds among certified outcomes, followed by certified/total counts. "
        "Different success counts mean the timing medians cover different subsets of inputs. "
        "The matched comparisons below avoid that ambiguity.", "",
        "| Greedy | epsilon | Paired additive | Sequential additive | Multiplicative trim | Exact-half MITM |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for group in groups:
        cells = []
        for method in METHODS:
            result = group["methods"][method]
            ms = "n/a" if result["median_seconds"] is None else f"{1000 * result['median_seconds']:.3f}"
            cells.append(f"{ms} ({result['certified']}/{result['total']})")
        lines.append(f"| {'on' if group['greedy'] else 'off'} | {group['tolerance_label']} | " + " | ".join(cells) + " |")
    lines += [
        "", "## Matched comparisons", "",
        "Ratios are per-input baseline time divided by paired time, then their median is taken. "
        "A ratio above one favors pairing. Only jointly certified inputs enter a ratio; failures remain "
        "visible in the table above. Tiny greedy-only times should not be read as stable algorithmic differences.", "",
        "| Greedy | epsilon | Baseline | Paired faster / matched | Median baseline / paired |",
        "|---|---|---|---:|---:|",
    ]
    for group in groups:
        for baseline, result in group["comparisons"].items():
            ratio = "n/a" if result["median_baseline_over_paired"] is None else f"{result['median_baseline_over_paired']:.3f}"
            lines.append(f"| {'on' if group['greedy'] else 'off'} | {group['tolerance_label']} | {LABELS[baseline]} | {result['paired_faster']}/{result['matched']} | {ratio} |")
    lines += [
        "", "## Family detail and memory", "",
        f"Largest size (n={largest}), epsilon=1e-4, common greedy off. "
        "Cells show separate medians over certified outcomes, with success counts. "
        "Memory is peak traced MiB; approximate merges exclude exact duplicate merging. "
        "A witness may meet tolerance before the method needs to merge any unequal sums.", "",
        "| Family | Paired ms (count) | MITM ms (count) | Paired MiB | MITM MiB | Paired approximate merges |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for family in data["families"]:
        rows = [r for r in data["rows"] if r["n"] == largest and not r["greedy"] and r["tolerance_label"] == "1e-4" and r["family"] == family]
        paired = [r["results"]["paired_additive"] for r in rows if r["results"]["paired_additive"]["status"] == "certified"]
        mitm = [r["results"]["exact_mitm"] for r in rows if r["results"]["exact_mitm"]["status"] == "certified"]
        def med(entries, key, scale=1):
            return "n/a" if not entries else f"{statistics.median(x[key] for x in entries) * scale:.3f}"
        lines.append(
            f"| {family} | {med(paired, 'seconds', 1000)} ({len(paired)}/{len(rows)}) | "
            f"{med(mitm, 'seconds', 1000)} ({len(mitm)}/{len(rows)}) | "
            f"{med(paired, 'peak_traced_mib')} | {med(mitm, 'peak_traced_mib')} | {med(paired, 'approximate_merges')} |"
        )
    coarse = next(g for g in groups if g["greedy"] and g["tolerance_label"] == "1e-2")
    comparison = detail["comparisons"]["exact_mitm"]
    ratio_label = (
        "unavailable (no jointly certified inputs)"
        if comparison["median_baseline_over_paired"] is None
        else f"{comparison['median_baseline_over_paired']:.3f}"
    )
    lines += [
        "", "## Observed outcomes", "",
        f"At epsilon=1e-2 on the largest inputs, the shared greedy search alone certifies "
        f"{coarse['methods']['paired_additive']['greedy_stops']} of {coarse['methods']['paired_additive']['total']} inputs "
        "before the methods diverge. These outcomes do not demonstrate a compression advantage.", "",
        f"With common greedy disabled and epsilon=1e-4, pairing is faster than exact-half MITM on "
        f"{comparison['paired_faster']} of {comparison['matched']} jointly certified largest-size inputs. "
        f"The median per-input MITM/paired ratio is {ratio_label}. "
        "Read this alongside the sequential-additive comparison and merge counts to distinguish "
        "the effects of grouping, approximation, and witness-based stopping.",
        "",
        f"At that same setting, pairing is faster than sequential additive trimming on "
        f"{sequential['paired_faster']} of {sequential['matched']} jointly certified inputs. "
        "This comparison does not establish a consistent additional timing benefit from pairing; "
        f"the paired method certifies {detail['methods']['paired_additive']['certified']} of "
        f"{detail['methods']['paired_additive']['total']} inputs within the cap, while sequential additive "
        f"certifies {detail['methods']['sequential_additive']['certified']}. "
        "At zero tolerance, paired additive and exact-half MITM construct the same exact summaries. "
        "The experiment supports a benefit from controlled approximation on some families, "
        "without establishing a new general advantage from pairing.",
    ]
    lines += [
        "", "![Runtime and certification counts as tolerance changes](approximation_tradeoff.png)", "",
        "## Interpretation and limits", "",
        "The main contribution is the controlled negative timing finding: the key approximation comparison "
        "identifies no consistent additional timing benefit from pairing over the same additive rule used "
        "sequentially, alongside its state-cap exception. Approximation can make coverage cheaper without "
        "pairing being responsible for the savings. The result limits the tested framework's demonstrated "
        "added value from pairing; it is not an impossibility result or a statistical finding of equivalence.", "",
        "The additive invariant supplies deterministic correctness and a polynomial bound in n and inverse "
        "normalized tolerance when resources are unrestricted. This specializes established approximation "
        "ideas. Correct certification makes the accuracy contracts comparable; a separate runtime "
        "comparison establishes whether their organization adds a computational benefit.", "",
        "The sequential additive control is essential: a win over multiplicative trimming alone could be "
        "caused by the error allocation rule rather than by pairing. A cheap common witness can also "
        "answer a loose-tolerance question before any compression occurs. Positive tolerances do not "
        "guarantee faster execution on every input. These are small synthetic families and two seeds, "
        "with deterministic accuracy guarantees and descriptive runtime summaries, not statistical confidence intervals.", "",
        "## Reproduce", "",
        "```powershell", "python -m unittest discover -s subset-sum -p test_certified_approximation.py -v",
        "python subset-sum/approximation_experiment.py", "python build_papers.py", "```", "",
        "Use `--quick` for a separate smoke dataset, `--no-plots` to avoid a matplotlib dependency, "
        "or `--report-only` to regenerate the report and plots from the saved full dataset. "
        "Full measurements are in [approximation_results.json](approximation_results.json); "
        "aggregate comparisons are in [approximation_summary.json](approximation_summary.json).", "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def plot(data: dict, path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    groups = summary(data)["groups"]
    labels = ("exact", "1e-6", "1e-4", "1e-2")
    colors = ("#6e5943", "#3e716c", "#a16b48", "#596782")
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), layout="constrained")
    for column, greedy in enumerate((True, False)):
        selected = {group["tolerance_label"]: group for group in groups if group["greedy"] == greedy}
        for method, color in zip(METHODS, colors):
            entries = [selected[label]["methods"][method] for label in labels]
            times = [1000 * entry["median_seconds"] if entry["median_seconds"] is not None else float("nan") for entry in entries]
            axes[0, column].plot(labels, times, marker="o", color=color, label=LABELS[method])
            axes[1, column].plot(labels, [entry["certified"] for entry in entries], marker="o", color=color)
        axes[0, column].set(title=f"Common greedy {'on' if greedy else 'off'}", ylabel="Median time on successes (ms)", yscale="log")
        axes[1, column].set(ylabel="Inputs certified", xlabel="Allowed error as a fraction of total weight", ylim=(-0.5, len([c for c in data['cases'] if c['n'] == max(data['sizes'])]) + .5))
        for axis in axes[:, column]:
            axis.grid(alpha=.2)
    axes[0, 0].legend(fontsize=8)
    fig.suptitle(f"Fixed-target approximation, n={max(data['sizes'])}; failures excluded from time medians")
    fig.savefig(path, dpi=180)
    plt.close(fig)


def write_tex_table(data: dict, path: Path) -> None:
    lines = [r"\begin{tabular}{llrrrr}", r"\toprule", r"Greedy & $\varepsilon$ & Paired & Sequential & Mult. trim & MITM\\", r"\midrule"]
    for group in summary(data)["groups"]:
        if group["tolerance_label"] == "1e-6":
            continue
        cells = []
        for method in METHODS:
            result = group["methods"][method]
            ms = "--" if result["median_seconds"] is None else f"{1000 * result['median_seconds']:.2f}"
            cells.append(f"{ms} ({result['certified']}/{result['total']})")
        label = {"1e-2": "$10^{-2}$", "1e-4": "$10^{-4}$", "exact": "$0$"}[group["tolerance_label"]]
        lines.append(("On" if group["greedy"] else "Off") + " & " + label + " & " + " & ".join(cells) + r"\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--max-states", type=int, default=DEFAULT_MAX_STATES)
    parser.add_argument("--no-plots", action="store_true")
    parser.add_argument("--report-only", action="store_true")
    args = parser.parse_args()
    if args.repeats < 1 or args.max_states < 1:
        parser.error("repeats and max-states must be positive")
    suffix = "_quick" if args.quick else ""
    raw = HERE / f"approximation_results{suffix}.json"
    data = json.loads(raw.read_text(encoding="utf-8")) if args.report_only else run(
        quick=args.quick, repeats=args.repeats, max_states=args.max_states, checkpoint=raw,
    )
    if not data["complete"]:
        raise RuntimeError("dataset is incomplete; rerun the experiment")
    raw.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    (HERE / f"approximation_summary{suffix}.json").write_text(json.dumps(summary(data), indent=2) + "\n", encoding="utf-8")
    write_report(data, HERE / f"APPROXIMATION_RESULTS{suffix}.md")
    write_tex_table(data, HERE / f"approximation_results_table{suffix}.tex")
    if not args.no_plots:
        plot(data, HERE / f"approximation_tradeoff{suffix}.png")
    print(f"Wrote {raw.name}: {len(data['cases'])} lists, {len(data['rows'])} comparisons", flush=True)


if __name__ == "__main__":
    main()
