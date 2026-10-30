"""Make the compact, vector runtime figure used in the structural-route note.

This reads saved presentation data only; it does not run a solver or refit a model.
"""
from __future__ import annotations

import ast
import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Learned_Solvability_Subset_Sum/visualizations/runtime_histogram_20261030/plotted_inputs.csv"
HARD = ROOT / "subset-sum/hard_results.json"
OUTPUT = ROOT / "OpenAI_Subset_Sum_Connections/Runtime_Distribution_Histogram.pdf"
INK, TEAL, GRAY, RED, PURPLE = "#26231f", "#38796e", "#89929a", "#bd5845", "#755b99"


def main() -> None:
    with DATA.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 576
    times = np.array([float(row["runtime_ms"]) for row in rows])
    done = np.array([row["completed"] == "True" for row in rows])
    members = [ast.literal_eval(row["exact_memberships"]) for row in rows]
    certified = np.array([bool(item) for item in members])
    flagged = np.array([row["ml_flags_unresolved"] == "True" for row in rows])
    assert np.isfinite(times).all() and np.all(times > 0)
    assert (done.sum(), (~done).sum()) == (430, 146)

    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 7.8,
        "axes.labelcolor": INK, "text.color": INK, "xtick.color": INK,
        "ytick.color": INK, "axes.edgecolor": "#bbb6ae",
        "axes.spines.top": False, "axes.spines.right": False,
        "pdf.fonttype": 42,
    })
    fig = plt.figure(figsize=(7.05, 5.15), facecolor="white")
    gs = fig.add_gridspec(3, 1, height_ratios=[2.35, 1.9, 1.2],
                          left=.215, right=.99, top=.955, bottom=.095, hspace=.42)
    ax = fig.add_subplot(gs[0])
    classes = fig.add_subplot(gs[1], sharex=ax)
    hard_ax = fig.add_subplot(gs[2])
    for panel in (ax, classes, hard_ax):
        panel.set_xscale("log")
        panel.grid(axis="x", color="#e9e5e0", linewidth=.55)
        panel.set_axisbelow(True)
        panel.tick_params(length=2, pad=2)

    bins = np.geomspace(.003, 25, 37)
    groups = (done & certified, done & ~certified, ~done)
    counts, _, bars = ax.hist([times[group] for group in groups], bins=bins,
                             stacked=True, color=[TEAL, GRAY, RED],
                             edgecolor="white", linewidth=.25,
                             label=[f"Certified & completed ({groups[0].sum()})",
                                    f"Other completed ({groups[1].sum()})",
                                    "Unresolved stop (146)"])
    assert int(counts[-1].sum()) == 576
    for bar in bars[-1]:
        bar.set_hatch("///")
        bar.set_edgecolor("#f6ebe7")
    ax.set_xlim(.003, 25)
    ax.set_ylim(0, max(counts[-1]) * 1.26)
    ax.set_ylabel("Inputs per log-spaced bin")
    ax.set_title("A   Saved portfolio: 576 inputs", loc="left", fontsize=8.5, weight="bold", pad=5)
    ax.legend(loc="upper left", frameon=False, fontsize=6.8, handlelength=1.2,
              labelspacing=.24, borderaxespad=.2)
    ax.tick_params(labelbottom=False)

    lanes = [
        ("Superincreasing", np.array([0 in m for m in members]), TEAL),
        ("Complete coverage", np.array([1 in m for m in members]), TEAL),
        ("Few distinct values", np.array([2 in m for m in members]), TEAL),
        ("Small reachable support", np.array([3 in m for m in members]), TEAL),
        ("Interval / progression", np.array([4 in m for m in members]), TEAL),
        ("ML flags unresolved", flagged, PURPLE),
        ("ML misses unresolved", ~flagged & ~done, RED),
    ]
    rng = np.random.default_rng(20261030)
    for y, (label, mask, color) in enumerate(lanes):
        classes.axhline(y, color="#e9e5e0", lw=.5)
        for completed, marker in ((True, "o"), (False, ">")):
            idx = np.flatnonzero(mask & (done == completed))
            classes.scatter(times[idx], y + rng.uniform(-.12, .12, len(idx)),
                            s=9 if completed else 14, marker=marker,
                            color=color if completed else RED,
                            alpha=.63 if completed else .85,
                            edgecolors="none", zorder=3)
    classes.set_yticks(range(len(lanes)), [f"{label} ({mask.sum()})" for label, mask, _ in lanes])
    classes.set_ylim(6.5, -.6)
    classes.tick_params(axis="y", length=0, labelsize=7)
    classes.set_xticks([.003, .01, .03, .1, .3, 1, 3, 10, 25],
                       [".003", ".01", ".03", ".1", ".3", "1", "3", "10", "25"])
    classes.set_xlabel("Elapsed milliseconds (log scale)", labelpad=2)
    classes.set_title("B   Exact classes and saved ML flags; groups overlap", loc="left",
                      fontsize=8.5, weight="bold", pad=4)
    classes.legend(handles=[Line2D([], [], marker="o", color=TEAL, ls="", markersize=3.5,
                                   label="Completed"),
                            Line2D([], [], marker=">", color=RED, ls="", markersize=4,
                                   label="Unresolved at stop")],
                   loc="upper right", ncol=2, frameon=False, fontsize=6.5,
                   handletextpad=.2, columnspacing=.6, borderaxespad=.1)

    hard_rows = json.loads(HARD.read_text(encoding="utf-8"))["rows"]
    assert len(hard_rows) == 18
    for y, family in enumerate(("unique", "pairs", "triples")):
        subset = [r for r in hard_rows if r["family"] == family]
        for row in subset:
            offset = {24: -.08, 30: 0, 36: .08}[row["n"]] + (-.015 if row["seed"] == 0 else .015)
            hard_ax.scatter(row["meet_in_middle"]["seconds"] * 1000,
                            y + offset - .10, s=13, color="#37668e", marker="o", zorder=3)
            dfs = row["certified_dfs"]
            stop = dfs["status"] == "time_limit"
            hard_ax.scatter(dfs["seconds"] * 1000, y + offset + .10,
                            s=19, color=RED if stop else "#ab8545",
                            marker=">" if stop else "D", zorder=3)
    hard_ax.axvline(2000, color=RED, ls="--", lw=.7)
    hard_ax.set_yticks([0, 1, 2], ["Unique weights", "Repeated pairs", "Repeated triples"])
    hard_ax.set_ylim(2.45, -.55)
    hard_ax.tick_params(axis="y", length=0, labelsize=7)
    hard_ax.set_xlim(.15, 3500)
    hard_ax.set_xticks([.2, 1, 10, 100, 1000], [".2", "1", "10", "100", "1,000"])
    hard_ax.set_xlabel("Historical milliseconds (separate scale)", labelpad=2)
    hard_ax.set_title("C   Constructed hard NO cases: separate historical benchmark", loc="left",
                      fontsize=8.5, weight="bold", pad=4)
    hard_ax.legend(handles=[Line2D([], [], marker="o", color="#37668e", ls="", markersize=3.5,
                                   label="MITM"),
                            Line2D([], [], marker="D", color="#ab8545", ls="", markersize=3.5,
                                   label="DFS finished"),
                            Line2D([], [], marker=">", color=RED, ls="", markersize=4,
                                   label="DFS stopped (9)")],
                   loc="upper left", ncol=3, frameon=False, fontsize=6.4,
                   handletextpad=.2, columnspacing=.6, borderaxespad=.1)
    fig.savefig(OUTPUT, facecolor="white")
    plt.close(fig)
    print(OUTPUT)


if __name__ == "__main__":
    main()
