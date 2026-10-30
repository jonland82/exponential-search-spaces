"""Plot saved subset-sum runtimes and classifications without rerunning solvers."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "Learned_Solvability_Subset_Sum/visualizations/runtime_histogram_20261030"
STUDY = ROOT / "Learned_Solvability_Subset_Sum/results/prospective_20261025"
POINTS = ROOT / "Learned_Solvability_Subset_Sum/visualizations/input_space_20261025/points.json"
HARD = ROOT / "subset-sum/hard_results.json"
TEAL, GRAY, RED, PURPLE = "#008878", "#8898af", "#d65c49", "#7651b4"
INK, BG = "#243044", "#fbfaf7"


def jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    # Check frozen raw inputs before joining the saved presentation labels.
    for name, digest in json.loads((STUDY / "data_hashes.json").read_text()).items():
        assert hashlib.sha256((STUDY / name).read_bytes()).hexdigest() == digest, name
    cases = {r["case_id"]: r for r in jsonl(STUDY / "cases.jsonl")}
    references = {r["case_id"]: r for r in jsonl(STUDY / "references.jsonl") if r["mode"] == "work"}
    points = [r for r in json.loads(POINTS.read_text()) if r["scale"] == 1]
    assert len(points) == 576 and len({r["case_id"] for r in points}) == 576
    records = []
    for p in points:
        c, r = cases[p["case_id"]], references[p["case_id"]]
        assert p["completed"] == (r["status"] != "unresolved")
        assert p["probability"] == c["predictions"]["hybrid:logistic"]
        assert p["exact_memberships"] == [i for i, d in enumerate(p["full_distances"]) if d == 0]
        records.append(dict(case_id=p["case_id"], base_list_id=p["base_list_id"],
                            family=p["family"], n=p["n"], runtime_ms=r["seconds"] * 1000,
                            completed=p["completed"], primary_type=p["primary_type"],
                            exact_memberships=p["exact_memberships"],
                            probability_complete=p["probability"],
                            ml_flags_unresolved=p["probability"] < .5))
    t = np.array([r["runtime_ms"] for r in records])
    done = np.array([r["completed"] for r in records])
    certified = np.array([bool(r["exact_memberships"]) for r in records])
    flagged = np.array([r["ml_flags_unresolved"] for r in records])
    assert np.isfinite(t).all() and (t > 0).all()
    assert (int(done.sum()), int((~done).sum())) == (430, 146)
    groups = [done & certified, done & ~certified, ~done]
    assert np.all(np.sum(groups, axis=0) == 1)

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.labelcolor": INK, "text.color": INK,
                         "xtick.color": INK, "ytick.color": INK,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.edgecolor": "#c2c8cd", "pdf.fonttype": 42})
    fig = plt.figure(figsize=(14.6, 14.2), facecolor=BG)
    grid = fig.add_gridspec(3, 1, height_ratios=[3.3, 2.9, 2.1],
                           left=.205, right=.965, top=.86, bottom=.19, hspace=.56)
    ax = fig.add_subplot(grid[0])
    loc = fig.add_subplot(grid[1], sharex=ax)
    stress = fig.add_subplot(grid[2])
    for a in [ax, loc, stress]:
        a.set_facecolor(BG)
        a.set_xscale("log")
        a.grid(axis="x", color="#e4e5e3", linewidth=.7, zorder=0)
        a.set_axisbelow(True)
    fig.text(.055, .955, "Where subset-sum inputs fall in runtime", fontsize=23, weight="bold")
    fig.text(.055, .925, "Saved measurements from this repository  |  logarithmic runtime axes", fontsize=12, color="#5e6977")
    fig.text(.055, .895, "576 unscaled inputs from 144 lists; n = 24, 32, 38. No solver or model was rerun.", fontsize=10.5)

    bins = np.geomspace(.003, 25, 37)
    assert np.histogram(t, bins=bins)[0].sum() == len(t)
    labels = [f"Completed, certified full-list class ({groups[0].sum()})",
              f"Completed, other inputs ({groups[1].sum()})",
              f"Unresolved at stop ({groups[2].sum()})"]
    counts, _, containers = ax.hist([t[g] for g in groups], bins=bins, stacked=True,
                                    color=[TEAL, GRAY, RED], label=labels,
                                    edgecolor=BG, linewidth=.6)
    for bar in containers[-1]:
        bar.set_hatch("////")
        bar.set_edgecolor("#faf3ec")
    assert int(counts[-1].sum()) == 576
    ax.set_xlim(.003, 25)
    ax.set_ylabel("Input count\nper log-spaced bin", labelpad=12)
    ax.set_title("A   Runtime histogram: frozen exact-reference portfolio", loc="left", fontsize=12, weight="bold", pad=14)
    ax.legend(loc="upper left", frameon=False, fontsize=9)
    ax.set_ylim(0, max(counts[-1]) * 1.32)
    ax.text(.99, .96, "430 completed  /  146 unresolved", transform=ax.transAxes,
            ha="right", va="top", weight="bold", fontsize=10)
    ax.text(.99, .85, "Hatched times end without an answer;\ncompletion runtimes are unknown.",
            transform=ax.transAxes, ha="right", va="top", fontsize=9, color="#9f493d")
    ax.tick_params(labelbottom=False)

    lanes = [("Superincreasing", np.array([0 in r["exact_memberships"] for r in records]), TEAL),
             ("Complete coverage", np.array([1 in r["exact_memberships"] for r in records]), TEAL),
             ("Few distinct values", np.array([2 in r["exact_memberships"] for r in records]), TEAL),
             ("Small reachable support", np.array([3 in r["exact_memberships"] for r in records]), TEAL),
             ("Interval / progression", np.array([4 in r["exact_memberships"] for r in records]), TEAL),
             ("ML flags unresolved", flagged, PURPLE),
             ("ML misses unresolved", ~flagged & ~done, RED)]
    rng = np.random.default_rng(20261030)
    for y, (label, mask, color) in enumerate(lanes):
        loc.axhline(y, color="#e6e7e4", lw=.65, zorder=0)
        for completed, marker in [(True, "o"), (False, ">")]:
            indices = np.flatnonzero(mask & (done == completed))
            jitter = rng.uniform(-.13, .13, len(indices))
            loc.scatter(t[indices], y + jitter, s=19 if completed else 30,
                        marker=marker, color=color if completed else RED,
                        alpha=.6 if completed else .78, edgecolors="none", zorder=3)
    loc.set_yticks(range(len(lanes)), [f"{label}  ({int(mask.sum())})" for label, mask, _ in lanes])
    loc.set_ylim(6.55, -.6)
    loc.tick_params(axis="y", length=0, labelsize=9)
    loc.set_xlabel("Saved elapsed runtime per input (milliseconds)", labelpad=8)
    ticks = [.003, .01, .03, .1, .3, 1, 3, 10, 25]
    loc.set_xticks(ticks, [str(x) for x in ticks])
    loc.set_title("B   Class locations and saved ML flags (groups overlap)", loc="left", fontsize=12, weight="bold", pad=16)
    loc.legend(handles=[Line2D([], [], marker="o", color=TEAL, ls="", markersize=5, label="Completed"),
                        Line2D([], [], marker=">", color=RED, ls="", markersize=6, label="Unresolved at stop")],
               loc="upper right", ncol=2, frameon=False, fontsize=9)

    hard = json.loads(HARD.read_text())["rows"]
    assert len(hard) == 18
    for y, family in enumerate(["unique", "pairs", "triples"]):
        subset = [r for r in hard if r["family"] == family]
        for r in subset:
            offset = {24: -.12, 30: 0, 36: .12}[r["n"]] + (-.025 if r["seed"] == 0 else .025)
            stress.scatter(r["meet_in_middle"]["seconds"] * 1000, y + offset - .12,
                           s=32, color="#2969a3", marker="o", zorder=3)
            d = r["certified_dfs"]
            stopped = d["status"] == "time_limit"
            stress.scatter(d["seconds"] * 1000, y + offset + .12,
                           s=44, color=RED if stopped else "#b18b43",
                           marker=">" if stopped else "D", zorder=3)
    stress.axvline(2000, color=RED, ls="--", lw=1, alpha=.6)
    stress.text(1850, -.57, "2-second DFS stop", color="#a64739", fontsize=9, ha="right")
    stress.set_yticks([0, 1, 2], ["Unique weights  (6)", "Repeated pairs  (6)", "Repeated triples  (6)"])
    stress.set_ylim(2.5, -.65)
    stress.tick_params(axis="y", length=0, labelsize=9)
    stress.set_xlim(.15, 3500)
    stress.set_xticks([.2, 1, 10, 100, 1000, 2000], ["0.2", "1", "10", "100", "1,000", "2,000"])
    stress.set_xlabel("Historical benchmark elapsed runtime (milliseconds; separate scale)", labelpad=8)
    stress.set_title("C   Constructed hard NO cases: separate historical benchmark", loc="left", fontsize=12, weight="bold", pad=17)
    stress.legend(handles=[Line2D([], [], marker="o", color="#2969a3", ls="", markersize=5, label="Meet-in-the-middle: all 18 finish"),
                           Line2D([], [], marker="D", color="#b18b43", ls="", markersize=5, label="Certified DFS: finished"),
                           Line2D([], [], marker=">", color=RED, ls="", markersize=6, label="DFS: stopped, no answer (9)")],
                  loc="upper left", bbox_to_anchor=(0, -.42), frameon=False, ncol=3, fontsize=8.5, columnspacing=1.2)

    fig.text(.055, .033,
             "A–B: elapsed time of work-capped runs (8L allowance + state/bitset caps); includes exact preprocessing, excludes ML acquisition.\n"
             "ML flag: original combined logistic model, p(completion) < 0.5; 118 unresolved + 23 completed flagged, 28 unresolved missed.\n"
             "C: 41-bit odd weights, n = 24/30/36, two seeds; targets pass root bounds/residue checks. Different solvers/study; not pooled into A.\n"
             "These are sampled synthetic inputs. Unresolved runs and ML flags do not establish intrinsic hardness or new complexity classes.",
             fontsize=8.5, color="#596573", linespacing=1.55)
    for ext in ["png", "pdf"]:
        fig.savefig(OUTPUT / f"subset_sum_runtime_histogram.{ext}", dpi=190, facecolor=BG)
    plt.close(fig)

    with (OUTPUT / "plotted_inputs.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    sources = [POINTS, HARD, STUDY / "cases.jsonl", STUDY / "references.jsonl", STUDY / "data_hashes.json"]
    manifest = dict(sources={p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
                    inputs=len(records), base_lists=len({r["base_list_id"] for r in records}),
                    completed=int(done.sum()), unresolved=int((~done).sum()),
                    certified_completed=int(groups[0].sum()), other_completed=int(groups[1].sum()),
                    ml_flagged_unresolved=int((flagged & ~done).sum()),
                    ml_flagged_completed=int((flagged & done).sum()),
                    ml_missed_unresolved=int((~flagged & ~done).sum()),
                    histogram_counts=counts[-1].astype(int).tolist(), histogram_bin_edges_ms=bins.tolist(),
                    measurement="Saved wall-clock seconds from mode=work, repeat=0, scale=1; unresolved are stopping times.",
                    model="Saved hybrid:logistic; p(completion) < 0.5 flags unresolved.",
                    new_solver_runs=0, new_model_fits=0)
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in manifest.items() if k not in ["sources", "histogram_counts", "histogram_bin_edges_ms"]}, indent=2))
    print(OUTPUT / "subset_sum_runtime_histogram.png")


if __name__ == "__main__":
    main()
