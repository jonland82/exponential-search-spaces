"""Plot saved total completion times, with unresolved stops shown separately."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "Learned_Solvability_Subset_Sum/visualizations/runtime_histogram_20261030"
CSV = OUTPUT / "plotted_inputs.csv"
REFERENCES = ROOT / "Learned_Solvability_Subset_Sum/results/prospective_20261025/references.jsonl"
COLORS = ["#35796e", "#6b9f99", "#9c8c63", "#8498ae", "#6e5d99"]
ROUTES = [
    ("exact_reduction", "Exact reduction"),
    ("bitset", "Bitset"),
    ("core_enumerate", "Core enumeration"),
    ("dfs", "DFS"),
    ("mitm", "Meet-in-the-middle"),
]


def main() -> None:
    with CSV.open(newline="", encoding="utf-8") as stream:
        records = list(csv.DictReader(stream))
    assert len(records) == 576
    by_id = {row["case_id"]: row for row in records}
    assert len(by_id) == len(records)
    references = {}
    with REFERENCES.open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row["mode"] == "work" and row["case_id"] in by_id:
                assert row["case_id"] not in references
                references[row["case_id"]] = row
    assert len(references) == 576
    completed = {name: [] for name, _ in ROUTES}
    stopped = []
    for case_id, row in by_id.items():
        reference = references[case_id]
        elapsed = float(row["runtime_ms"])
        assert elapsed > 0 and np.isfinite(elapsed)
        assert np.isclose(elapsed, 1000 * reference["seconds"], rtol=1e-10)
        if reference["status"] == "unresolved":
            assert row["completed"] == "False"
            stopped.append(elapsed)
        else:
            assert row["completed"] == "True"
            route = reference["attempts"][-1]["method"] if reference["attempts"] else "exact_reduction"
            assert route in completed
            completed[route].append(elapsed)
    assert [len(completed[name]) for name, _ in ROUTES] == [129, 49, 17, 205, 30]
    assert len(stopped) == 146
    all_completed = np.array([time for times in completed.values() for time in times])
    median = float(np.median(all_completed))

    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 10,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.edgecolor": "#b8b8b2", "pdf.fonttype": 42,
    })
    fig = plt.figure(figsize=(10.4, 6.2), facecolor="#fbfaf7")
    grid = fig.add_gridspec(2, 1, height_ratios=[5.0, .7],
                           left=.105, right=.96, top=.79, bottom=.17, hspace=.13)
    ax = fig.add_subplot(grid[0])
    rug = fig.add_subplot(grid[1], sharex=ax)
    for panel in (ax, rug):
        panel.set_facecolor("#fbfaf7")
        panel.set_xscale("log")
        panel.set_xlim(.003, 25)
        panel.grid(axis="x", color="#e7e5e0", linewidth=.7)
        panel.set_axisbelow(True)
    bins = np.geomspace(.003, 25, 37)
    counts, _, _ = ax.hist([completed[name] for name, _ in ROUTES], bins=bins,
                           stacked=True, color=COLORS, edgecolor="#fbfaf7",
                           linewidth=.45,
                           label=[f"{label} ({len(completed[name])})" for name, label in ROUTES])
    assert int(counts[-1].sum()) == 430
    ax.axvline(median, color="#373b46", ls="--", lw=1.25, zorder=4)
    ax.text(median * 1.09, ax.get_ylim()[1] * .93, f"Median: {median:.2f} ms",
            fontsize=9, color="#373b46", va="top")
    ax.set_ylabel("Completed inputs per log-spaced bin")
    ax.legend(loc="upper left", ncol=2, frameon=False, fontsize=9,
              columnspacing=1.3, handlelength=1.3)
    ax.tick_params(labelbottom=False)
    rng = np.random.default_rng(20261030)
    rug.scatter(stopped, rng.uniform(.35, .65, len(stopped)), marker="|",
                s=75, lw=.8, color="#be5d48", alpha=.76)
    rug.set_yticks([.5], ["Unresolved\nstops (146)"])
    rug.set_ylim(0, 1)
    rug.spines["left"].set_visible(False)
    rug.spines["bottom"].set_visible(False)
    rug.tick_params(axis="y", length=0, labelsize=9)
    ticks = [.003, .01, .03, .1, .3, 1, 3, 10, 25]
    rug.set_xticks(ticks, [str(tick) for tick in ticks])
    rug.set_xlabel("Total observed elapsed time (milliseconds; log scale)", labelpad=6)
    fig.text(.065, .94, "Total completion time for solved subset-sum inputs",
             fontsize=18, weight="bold", color="#243044")
    fig.text(.065, .895, "430 of 576 saved inputs completed under the work-capped reference portfolio",
             fontsize=11, color="#586575")
    fig.text(.065, .85, "Each completed time includes preprocessing and all earlier attempted routes.",
             fontsize=10, color="#586575")
    fig.text(.065, .055,
             "The red marks are elapsed times at which 146 other runs stopped without an answer; their completion times are unknown.\n"
             "Counts describe completed inputs in this synthetic corpus, not the eventual runtime distribution of all 576 inputs.",
             fontsize=8.5, color="#586575", linespacing=1.5)
    for extension in ("png", "pdf"):
        fig.savefig(OUTPUT / f"subset_sum_completion_time_histogram.{extension}",
                    dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"completed=430, stopped=146, median_completed_ms={median:.6f}")
    print(OUTPUT / "subset_sum_completion_time_histogram.png")


if __name__ == "__main__":
    main()
