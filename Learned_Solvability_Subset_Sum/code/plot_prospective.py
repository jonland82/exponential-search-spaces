"""Presentation-only figures from hashed frozen-study results; no model fitting."""

import argparse
import json
from pathlib import Path
import shutil

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from prospective_study import ARMS
from run_pilot import save_json, sha


def plot(data, output):
    if output.exists():
        raise FileExistsError("figures require a fresh output directory")
    for manifest in ("prediction_hashes.json", "priority_hashes.json"):
        for name, digest in json.loads((data / manifest).read_text()).items():
            if sha(data / name) != digest:
                raise AssertionError("result hash mismatch")
    prediction = json.loads((data / "prediction_metrics.json").read_text())
    priority = json.loads((data / "priority_summary.json").read_text())
    cohorts = ["in_distribution", "larger_size", "prior_holdout", "unseen_family",
               "in_distribution_scaled", "larger_size_scaled", "prior_holdout_scaled", "unseen_family_scaled"]
    labels = ["Same families", "Larger inputs", "Earlier holdouts", "New families",
              "Same families, scaled", "Larger inputs, scaled", "Earlier holdouts, scaled", "New families, scaled"]
    indexed = {(r["mode"], r["cohort"], r["fraction"], r["policy"]): r for r in priority}
    policies = ["random", "short_input", "distance_rule", "five", "conventional", "hybrid"]
    short = ["Random", "Short input", "Distance rule", "Five + ML", "Ordinary + ML", "Combined + ML"]
    panels = [("work", .2, "Work-counter replay, 20% budget"),
              ("time", .2, "Live time, 20% budget"),
              ("time", .5, "Live time, 50% budget")]
    matrices = [np.array([[indexed[(mode, cohort, fraction, policy)]["median_solved"] -
                          indexed[(mode, cohort, fraction, "arrival")]["median_solved"]
                          for policy in policies] for cohort in cohorts])
                for mode, fraction, _ in panels]
    limit = max(1, max(abs(matrix).max() for matrix in matrices))
    fig, axes = plt.subplots(2, 2, figsize=(15, 10), constrained_layout=True)
    ax = axes[0, 0]
    ys = np.arange(len(cohorts))
    for number, (arm, label, color) in enumerate(zip(ARMS, ("Five distances", "Ordinary features", "Combined"),
                                                    ("#608997", "#b1845e", "#70568f"))):
        values = [prediction["models"][f"{arm}:logistic"][cohort]["all"]["brier"] for cohort in cohorts]
        ax.barh(ys + (number - 1) * .24, values, height=.23, label=label, color=color)
    ax.set_yticks(ys, labels)
    ax.invert_yaxis()
    ax.set_xlabel("Brier score (lower is better)")
    ax.set_title("Fresh prediction quality: frozen logistic models")
    ax.legend(fontsize=8)
    for ax, matrix, (_, _, title) in zip((axes[0, 1], axes[1, 0], axes[1, 1]), matrices, panels):
        im = ax.imshow(matrix, vmin=-limit, vmax=limit, cmap="RdBu", aspect="auto")
        ax.set_xticks(range(len(policies)), short, rotation=25, ha="right", fontsize=8)
        ax.set_yticks(range(len(cohorts)), labels, fontsize=8)
        ax.set_title(title)
        for row in range(matrix.shape[0]):
            for col in range(matrix.shape[1]):
                value = matrix[row, col]
                ax.text(col, row, f"{value:+g}", ha="center", va="center", fontsize=8,
                        color="white" if abs(value) > limit * .6 else "black")
        fig.colorbar(im, ax=ax, shrink=.75, label="Median completed cases minus arrival order")
    fig.suptitle("Paper VI: fresh frozen evaluation and paid prioritization", fontsize=15)
    output.mkdir(parents=True)
    fig.savefig(output / "overview.png", dpi=170)
    fig.savefig(output / "overview.pdf")
    plt.close(fig)
    source = Path(__file__).resolve()
    shutil.copy2(source, output / source.name)
    save_json(output / "figure_manifest.json", {"source_sha256": sha(source),
        "input_sha256": {name: sha(data / name) for name in ("prediction_metrics.json", "priority_summary.json")},
        "output_sha256": {name: sha(output / name) for name in ("overview.png", "overview.pdf")},
        "scope": "presentation only; logistic primary; no fresh model fitting or new statistical claims"})
    print(f"Saved standalone PNG/PDF overview to {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    plot(args.data, args.output)
