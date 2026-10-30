"""Plot an illustrative route-mixture curve without optimizing a density fit."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Learned_Solvability_Subset_Sum/visualizations/runtime_histogram_20261030"
CSV = OUT / "plotted_inputs.csv"
REFERENCES = ROOT / "Learned_Solvability_Subset_Sum/results/prospective_20261025/references.jsonl"
ROUTES = [
    ("exact_reduction", "Exact reduction", "#35796e", .45),
    ("bitset", "Bitset", "#6b9f99", .60),
    ("core_enumerate", "Core enumeration", "#9c8c63", .75),
    ("dfs", "DFS", "#8498ae", .70),
    ("mitm", "Meet-in-the-middle", "#6e5d99", .50),
]


def main() -> None:
    with CSV.open(newline="", encoding="utf-8") as stream:
        records = list(csv.DictReader(stream))
    assert len(records) == 576
    by_id = {row["case_id"]: row for row in records}
    references = {}
    with REFERENCES.open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row["mode"] == "work" and row["case_id"] in by_id:
                references[row["case_id"]] = row
    assert len(references) == 576
    route_times = {name: [] for name, *_ in ROUTES}
    for case_id, row in by_id.items():
        reference = references[case_id]
        if reference["status"] == "unresolved":
            continue
        route = reference["attempts"][-1]["method"] if reference["attempts"] else "exact_reduction"
        route_times[route].append(float(row["runtime_ms"]))
    completed = np.array([t for times in route_times.values() for t in times])
    assert len(completed) == 430
    assert [len(route_times[name]) for name, *_ in ROUTES] == [129, 49, 17, 205, 30]

    bins = np.geomspace(.003, 25, 37)
    delta = np.log(bins[1] / bins[0])
    x = np.geomspace(bins[0], bins[-1], 1000)
    total = np.zeros_like(x)
    components = []
    for name, label, color, sigma in ROUTES:
        tau = float(np.median(route_times[name]))
        count = len(route_times[name])
        z = (np.log(x) - np.log(tau)) / sigma
        curve = count * delta * np.exp(-.5 * z * z) / (sigma * np.sqrt(2 * np.pi))
        components.append((label, color, curve, tau, sigma, count))
        total += curve

    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 10,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.edgecolor": "#b8b8b2", "pdf.fonttype": 42,
    })
    fig, ax = plt.subplots(figsize=(10.3, 6.1), facecolor="#fbfaf7")
    ax.set_facecolor("#fbfaf7")
    fig.subplots_adjust(left=.095, right=.965, top=.79, bottom=.19)
    observed, _, _ = ax.hist(completed, bins=bins, color="#d9d7d2",
                             edgecolor="#fbfaf7", linewidth=.5,
                             label="Observed completions (430)")
    assert int(observed.sum()) == 430
    for label, color, curve, *_ in components:
        ax.plot(x, curve, color=color, lw=1.45, ls="--", alpha=.9, label=label)
    ax.plot(x, total, color="#242a35", lw=3.0, label="No-fit route mixture")
    ax.set_xscale("log")
    ax.set_xlim(bins[0], bins[-1])
    ax.set_ylim(0, max(max(observed), max(total)) * 1.14)
    ax.grid(axis="x", color="#e7e5e0", linewidth=.7)
    ax.set_axisbelow(True)
    ax.set_xticks([.003, .01, .03, .1, .3, 1, 3, 10, 25],
                  [".003", ".01", ".03", ".1", ".3", "1", "3", "10", "25"])
    ax.set_xlabel("Total completion time (milliseconds; log scale)")
    ax.set_ylabel("Inputs per log-spaced bin")
    ax.legend(loc="upper left", ncol=2, frameon=False, fontsize=8.5,
              handlelength=2.1, columnspacing=1.5)
    fig.text(.055, .94, "A structural guess for the smooth completion-time shape",
             fontsize=17.5, weight="bold", color="#243044")
    fig.text(.055, .89, "Gray: saved histogram  |  Black: route mixture  |  Dashed: route contributions",
             fontsize=10.5, color="#586575")
    fig.text(.055, .845, "Route weights and medians use saved runs; log-spreads were chosen by hand, with no fit.",
             fontsize=10, color="#586575")
    fig.text(.055, .055,
             "Only completed inputs appear. The 146 unresolved stops have unknown completion times.\n"
             "Smooth curves are illustrative; the exact route identity alone does not determine their shapes.",
             fontsize=8.7, color="#586575", linespacing=1.5)
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"subset_sum_analytical_completion_sketch.{ext}",
                    dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)
    for label, _, _, tau, sigma, count in components:
        print(f"{label}: count={count}, median_ms={tau:.6f}, chosen_log_sigma={sigma:.2f}")
    print(f"log_bin_width={delta:.6f}")
    print(OUT / "subset_sum_analytical_completion_sketch.png")


if __name__ == "__main__":
    main()
