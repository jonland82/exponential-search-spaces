"""Probability prediction for exact subset sum, with grouped evaluation and PNG charts."""

from __future__ import annotations

import csv
import itertools
import json
import math
import random
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import PercentFormatter
from sklearn.ensemble import RandomForestClassifier
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    roc_auc_score,
    roc_curve,
)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from experiment import suffix_residues


HERE = Path(__file__).parent
SEED = 20261022
GROUPS = 1200
OOD_GROUPS = 240
TARGETS_PER_LIST = 4
N_VALUES = (16, 18, 20, 22)
FAMILIES = ("independent", "paired")
PREFILTER_MODULI = (8, 10, 16, 32)

FEATURES = (
    "n",
    "log2_mean_weight",
    "log2_weight_std",
    "log2_total_weight",
    "log_density_proxy",
    "unique_fraction",
    "max_multiplicity",
    "coefficient_variation",
    "min_max_ratio",
    "small8_distinct_fraction",
    "large8_distinct_fraction",
    "residue16_coverage",
    "residue32_coverage",
    "residue64_coverage",
    "target_fraction_of_total",
    "target_distance_from_middle",
)
BASELINE_FEATURES = (
    "log_density_proxy",
    "unique_fraction",
    "target_fraction_of_total",
)


def all_sums(weights: list[int]) -> set[int]:
    sums = {0}
    for weight in weights:
        sums |= {value + weight for value in sums}
    return sums


def validate_exact_labels() -> None:
    rng = random.Random(SEED + 2)
    for _ in range(20):
        weights = [rng.randint(1, 100) for _ in range(10)]
        target = rng.randint(0, sum(weights))
        left = all_sums(weights[:5])
        right = all_sums(weights[5:])
        mitm = any(target - part in right for part in left)
        brute = any(sum(weight for weight, take in zip(weights, bits) if take) == target
                    for bits in itertools.product((0, 1), repeat=len(weights)))
        assert mitm == brute, (weights, target)


def little_sum_fraction(weights: list[int]) -> float:
    return len(all_sums(weights)) / (1 << len(weights))


def list_features(weights: list[int]) -> dict[str, float]:
    n = len(weights)
    counts = Counter(weights)
    mean = sum(weights) / n
    variance = sum((weight - mean) ** 2 for weight in weights) / n
    std = math.sqrt(variance)
    effective_log_states = sum(math.log2(count + 1) for count in counts.values())
    sorted_weights = sorted(weights)
    return {
        "n": float(n),
        "log2_mean_weight": math.log2(mean + 1),
        "log2_weight_std": math.log2(std + 1),
        "log2_total_weight": math.log2(sum(weights) + 1),
        "log_density_proxy": effective_log_states - math.log2(std * math.sqrt(n) + 1),
        "unique_fraction": len(counts) / n,
        "max_multiplicity": float(max(counts.values())),
        "coefficient_variation": std / mean,
        "min_max_ratio": min(weights) / max(weights),
        "small8_distinct_fraction": little_sum_fraction(sorted_weights[:8]),
        "large8_distinct_fraction": little_sum_fraction(sorted_weights[-8:]),
        "residue16_coverage": suffix_residues(weights, 16)[0].bit_count() / 16,
        "residue32_coverage": suffix_residues(weights, 32)[0].bit_count() / 32,
        "residue64_coverage": suffix_residues(weights, 64)[0].bit_count() / 64,
    }


def make_weights(n: int, family: str, rng: random.Random) -> list[int]:
    multiplicity = 1 if family == "independent" else 2
    effective_bits = (n // multiplicity) * math.log2(multiplicity + 1)
    scale = max(32, round(2 ** (effective_bits + rng.uniform(-4, 4))))
    low = max(1, scale // 4)
    unique = [rng.randint(low, scale) for _ in range(n // multiplicity)]
    weights = [weight for weight in unique for _ in range(multiplicity)]
    rng.shuffle(weights)
    return weights


def make_group(group_id: int, n: int, family: str) -> list[dict]:
    rng = random.Random(f"ml:{SEED}:{group_id}:{n}:{family}")
    weights = make_weights(n, family, rng)
    total = sum(weights)
    ordered = sorted(weights, reverse=True)
    left = all_sums(ordered[: n // 2])
    right = all_sums(ordered[n // 2 :])
    root_masks = [(modulus, suffix_residues(weights, modulus)[0]) for modulus in PREFILTER_MODULI]
    base = list_features(weights)
    rows = []
    for target_index in range(TARGETS_PER_LIST):
        for attempt in range(1000):
            target = rng.randint(round(0.30 * total), round(0.70 * total))
            if all((mask >> (target % modulus)) & 1 for modulus, mask in root_masks):
                break
        else:
            raise RuntimeError("could not draw target passing cheap certificates")
        answer = any(target - part in right for part in left)
        features = {
            **base,
            "target_fraction_of_total": target / total,
            "target_distance_from_middle": abs(target / total - 0.5),
        }
        rows.append({
            "group_id": group_id,
            "n": n,
            "family": family,
            "target_index": target_index,
            "target": target,
            "label": int(answer),
            "features": features,
        })
    return rows


def generate() -> tuple[list[dict], list[dict]]:
    groups = []
    for family in FAMILIES:
        for n in N_VALUES:
            groups.extend((n, family) for _ in range(GROUPS // (len(FAMILIES) * len(N_VALUES))))
    rng = random.Random(SEED)
    rng.shuffle(groups)
    in_distribution = []
    for group_id, (n, family) in enumerate(groups):
        in_distribution.extend(make_group(group_id, n, family))
        if (group_id + 1) % 300 == 0:
            print(f"generated {group_id + 1}/{GROUPS} training-range lists", flush=True)
    out_distribution = []
    ood_families = [FAMILIES[i % 2] for i in range(OOD_GROUPS)]
    rng.shuffle(ood_families)
    for i, family in enumerate(ood_families):
        out_distribution.extend(make_group(GROUPS + i, 24, family))
    return in_distribution, out_distribution


def matrix(rows: list[dict], names=FEATURES) -> np.ndarray:
    return np.asarray([[row["features"][name] for name in names] for row in rows], dtype=float)


def labels(rows: list[dict]) -> np.ndarray:
    return np.asarray([row["label"] for row in rows], dtype=int)


def split_groups(rows: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    ids = list(range(GROUPS))
    random.Random(SEED + 1).shuffle(ids)
    train_ids = set(ids[:840])
    calibration_ids = set(ids[840:1020])
    train = [row for row in rows if row["group_id"] in train_ids]
    calibration = [row for row in rows if row["group_id"] in calibration_ids]
    test = [row for row in rows if row["group_id"] not in train_ids | calibration_ids]
    assert len({row["group_id"] for row in train}) == 840
    assert not ({row["group_id"] for row in train} & {row["group_id"] for row in test})
    return train, calibration, test


def fit_models(train: list[dict], calibration: list[dict]):
    forest = RandomForestClassifier(
        n_estimators=300,
        min_samples_leaf=8,
        max_features=0.75,
        n_jobs=-1,
        random_state=SEED,
    )
    forest.fit(matrix(train), labels(train))
    raw_cal = forest.predict_proba(matrix(calibration))[:, 1]
    calibrator = IsotonicRegression(y_min=0.001, y_max=0.999, out_of_bounds="clip")
    calibrator.fit(raw_cal, labels(calibration))
    baseline = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, random_state=SEED))
    baseline.fit(matrix(train, BASELINE_FEATURES), labels(train))
    return forest, calibrator, baseline


def predict(forest, calibrator, baseline, rows: list[dict]) -> tuple[np.ndarray, np.ndarray]:
    raw = forest.predict_proba(matrix(rows))[:, 1]
    calibrated = np.asarray(calibrator.predict(raw))
    simple = baseline.predict_proba(matrix(rows, BASELINE_FEATURES))[:, 1]
    return calibrated, simple


def score(y: np.ndarray, probabilities: np.ndarray) -> dict:
    hard = (probabilities >= 0.5).astype(int)
    cm = confusion_matrix(y, hard, labels=[0, 1])
    return {
        "samples": int(len(y)),
        "positive_rate": float(np.mean(y)),
        "auc": float(roc_auc_score(y, probabilities)) if len(np.unique(y)) == 2 else None,
        "average_precision": float(average_precision_score(y, probabilities)),
        "brier": float(brier_score_loss(y, probabilities)),
        "accuracy": float(accuracy_score(y, hard)),
        "balanced_accuracy": float(balanced_accuracy_score(y, hard)),
        "tn": int(cm[0, 0]),
        "fp": int(cm[0, 1]),
        "fn": int(cm[1, 0]),
        "tp": int(cm[1, 1]),
    }


def threshold_stats(y: np.ndarray, p: np.ndarray, thresholds=(0.01, 0.05, 0.10, 0.20, 0.50)) -> list[dict]:
    rows = []
    for threshold in thresholds:
        proposed = p <= threshold
        count = int(proposed.sum())
        wrong = int(np.sum((y == 1) & proposed))
        true_no = count - wrong
        rows.append({
            "threshold": threshold,
            "proposed_no": count,
            "coverage": count / len(y),
            "wrong_yes": wrong,
            "no_precision": true_no / count if count else None,
            "no_recall": true_no / int(np.sum(y == 0)),
        })
    return rows


def style() -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "axes.labelcolor": "#233347",
        "text.color": "#17263A",
        "axes.edgecolor": "#D3DBE3",
        "figure.facecolor": "#F7F9FC",
        "axes.facecolor": "#FFFFFF",
        "grid.color": "#E7EDF3",
        "savefig.facecolor": "#F7F9FC",
    })


BLUE = "#2463A6"
TEAL = "#148A7B"
ORANGE = "#D57B3C"
RED = "#C34E52"


def figure_heading(fig, title: str, subtitle: str) -> None:
    fig.text(0.055, 0.975, title, fontsize=19, fontweight="bold", va="top")
    fig.text(0.055, 0.937, subtitle, fontsize=10, color="#5B6B7C", va="top")


def draw_overview(y: np.ndarray, p: np.ndarray, baseline_p: np.ndarray, metrics: dict, baseline_metrics: dict, path: Path) -> None:
    style()
    fig, axes = plt.subplots(2, 2, figsize=(14, 9), dpi=170)
    fig.subplots_adjust(top=0.87, bottom=0.14, left=0.07, right=0.97, hspace=0.34, wspace=0.23)
    figure_heading(
        fig,
        "Can a model predict subset-sum existence?",
        f"Held-out lists: {metrics['samples']:,} targets  •  YES rate {metrics['positive_rate']:.1%}  •  "
        f"forest AUC {metrics['auc']:.3f}  •  Brier {metrics['brier']:.3f}  •  accuracy {metrics['accuracy']:.1%}",
    )

    ax = axes[0, 0]
    bins = np.linspace(0, 1, 21)
    ax.hist(p[y == 0], bins=bins, color=TEAL, alpha=0.78, label="Actually NO")
    ax.hist(p[y == 1], bins=bins, color=ORANGE, alpha=0.72, label="Actually YES")
    ax.axvline(0.5, color="#35465C", linestyle="--", lw=1)
    ax.set(title="Predicted chance of YES", xlabel="Predicted probability of a solution", ylabel="Test cases", xlim=(0, 1))
    ax.legend(frameon=False)

    ax = axes[0, 1]
    ax.plot([0, 1], [0, 1], color="#9AA8B6", linestyle="--", label="Perfect calibration")
    for probs, color, name in ((p, BLUE, "Forest + calibration"), (baseline_p, ORANGE, "Simple density model")):
        xs, ys, sizes = [], [], []
        for lo, hi in zip(np.linspace(0, 1, 11)[:-1], np.linspace(0, 1, 11)[1:]):
            sel = (probs >= lo) & (probs < hi if hi < 1 else probs <= hi)
            if sel.sum() >= 8:
                xs.append(float(np.mean(probs[sel])))
                ys.append(float(np.mean(y[sel])))
                sizes.append(float(sel.sum()))
        ax.plot(xs, ys, color=color, marker="o", lw=2, label=name)
        ax.scatter(xs, ys, s=np.asarray(sizes) * 0.18, color=color, alpha=0.25)
    ax.set(title="Are the probabilities trustworthy?", xlabel="Mean predicted YES probability", ylabel="Observed YES fraction", xlim=(0, 1), ylim=(0, 1))
    ax.legend(frameon=False, fontsize=8)

    ax = axes[1, 0]
    for probs, color, name, auc in ((p, BLUE, "Forest", metrics["auc"]), (baseline_p, ORANGE, "Density model", baseline_metrics["auc"])):
        fpr, tpr, _ = roc_curve(y, probs)
        ax.plot(fpr, tpr, color=color, lw=2, label=f"{name}: AUC {auc:.3f}")
    ax.plot([0, 1], [0, 1], color="#AAB6C2", linestyle="--", label="Chance")
    ax.set(title="Ranking YES above NO", xlabel="False-positive rate", ylabel="True-positive rate", xlim=(0, 1), ylim=(0, 1))
    ax.legend(loc="lower right", frameon=False, fontsize=9)

    ax = axes[1, 1]
    cm = np.array([[metrics["tn"], metrics["fp"]], [metrics["fn"], metrics["tp"]]])
    ax.imshow(cm, cmap="Blues", vmin=0, vmax=max(1, cm.max()))
    for i in range(2):
        for j in range(2):
            ax.text(j, i, f"{cm[i, j]:,}", ha="center", va="center", fontsize=18, fontweight="bold", color="white" if cm[i, j] > cm.max() / 2 else "#20334A")
    ax.set(xticks=[0, 1], yticks=[0, 1], xticklabels=["Predict NO", "Predict YES"], yticklabels=["Actually NO", "Actually YES"], title="At the 50% decision threshold")
    ax.tick_params(length=0)
    fig.text(0.055, 0.058, "AUC is the area under the ranking curve; Brier is mean squared probability error (lower is better).", fontsize=9, color="#657789")
    fig.text(0.055, 0.025, "Labels are exact meet-in-the-middle answers. Train, calibration, and test use disjoint input lists; targets pass cheap modular checks.", fontsize=9, color="#657789")
    fig.savefig(path, dpi=170)
    plt.close(fig)


def draw_thresholds(y: np.ndarray, p: np.ndarray, stats: list[dict], path: Path) -> None:
    style()
    grid = np.linspace(0, 0.5, 101)
    coverage, wrong, precision = [], [], []
    for q in grid:
        sel = p <= q
        n = int(sel.sum())
        w = int(np.sum(y[sel] == 1))
        coverage.append(n / len(y))
        wrong.append(w)
        precision.append((n - w) / n if n else np.nan)
    fig, axes = plt.subplots(1, 2, figsize=(14, 6.8), dpi=170)
    fig.subplots_adjust(top=0.79, bottom=0.28, left=0.075, right=0.97, wspace=0.26)
    figure_heading(fig, "What happens if we trust a predicted NO?", "Lower thresholds propose fewer states for elimination, but any mistaken YES would make an uncertified solver wrong.")
    ax = axes[0]
    ax.plot(grid, coverage, color=BLUE, lw=2.6)
    ax.set(title="How much of the test set is proposed NO?", xlabel="Propose NO when predicted YES chance ≤ threshold", ylabel="Fraction proposed NO", xlim=(0, 0.5), ylim=(0, 1))
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    for row in stats:
        ax.scatter(row["threshold"], row["coverage"], color=BLUE, s=30)
    ax.grid(alpha=0.7)

    ax = axes[1]
    ax.plot(grid, wrong, color=RED, lw=2.6)
    ax.set(title="How many real YES cases would be lost?", xlabel="Propose NO when predicted YES chance ≤ threshold", ylabel="Wrongly proposed NO (count)", xlim=(0, 0.5), ylim=(0, max(1, max(wrong) * 1.05)))
    for row in stats:
        ax.scatter(row["threshold"], row["wrong_yes"], color=RED, s=30)
    ax.grid(alpha=0.7)

    table_lines = ["Threshold    Proposed NO    Wrong YES    NO precision"]
    for row in stats:
        value = "n/a" if row["no_precision"] is None else f"{row['no_precision']:.1%}"
        table_lines.append(f"{row['threshold']:>7.0%}          {row['proposed_no']:>4} / {len(y)}           {row['wrong_yes']:>3}              {value}")
    fig.text(0.075, 0.20, "\n".join(table_lines), family="DejaVu Sans Mono", fontsize=10, va="top", linespacing=1.5,
             bbox={"boxstyle": "round,pad=0.65", "facecolor": "#EAF0F7", "edgecolor": "none"})
    fig.text(0.97, 0.12, "The classifier proposes. An exact verifier must certify every removal.", ha="right", fontsize=10, color=RED, fontweight="bold")
    fig.savefig(path, dpi=170)
    plt.close(fig)


def draw_generalization(test_rows: list[dict], test_y: np.ndarray, test_p: np.ndarray, ood_rows: list[dict], ood_y: np.ndarray, ood_p: np.ndarray, forest, path: Path) -> None:
    style()
    categories = []
    for label, rows, y, p in (("In-range: independent", test_rows, test_y, test_p), ("In-range: paired", test_rows, test_y, test_p), ("Unseen 24 weights: independent", ood_rows, ood_y, ood_p), ("Unseen 24 weights: paired", ood_rows, ood_y, ood_p)):
        family = "paired" if label.endswith("paired") else "independent"
        sel = np.asarray([row["family"] == family for row in rows])
        categories.append((label, score(y[sel], p[sel])))
    fig, axes = plt.subplots(1, 2, figsize=(15, 7.3), dpi=170)
    fig.subplots_adjust(top=0.82, bottom=0.27, left=0.20, right=0.97, wspace=0.65)
    figure_heading(fig, "Does the prediction survive new lists?", "Left: held-out lists and a larger unseen size. Right: influential features; the log density proxy compares selection patterns with weight spread.")
    names = [name for name, _ in categories]
    aucs = [entry["auc"] for _, entry in categories]
    briers = [entry["brier"] for _, entry in categories]
    ys = np.arange(len(names))
    ax = axes[0]
    colors = [BLUE, TEAL, ORANGE, RED]
    ax.barh(ys, aucs, color=colors, alpha=0.85)
    for i, (auc, brier) in enumerate(zip(aucs, briers)):
        ax.text(auc - 0.02, i, f"AUC {auc:.3f}  ·  Brier {brier:.3f}", ha="right", va="center", fontsize=8.5, color="white", fontweight="bold")
    ax.set(yticks=ys, yticklabels=names, xlim=(0, 1), xlabel="ROC AUC (higher is better)", title="Performance by input type")
    ax.axvline(0.5, color="#AAB6C2", linestyle="--")
    ax.invert_yaxis()
    ax.spines[["top", "right"]].set_visible(False)

    ax = axes[1]
    importances = forest.feature_importances_
    order = np.argsort(importances)[-8:]
    names_for_chart = {"coefficient_variation": "weight std / mean", "min_max_ratio": "min / max weight"}
    labels_short = [names_for_chart.get(FEATURES[i], FEATURES[i].replace("_", " ")) for i in order]
    ax.barh(np.arange(len(order)), importances[order], color=TEAL, alpha=0.85)
    ax.set(yticks=np.arange(len(order)), yticklabels=labels_short, xlabel="Forest split importance", title="Which list properties mattered?")
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(0.20, 0.13, f"In-range test: {len(test_y):,} targets  •  Unseen 24-weight lists: {len(ood_y):,} targets  •  Probabilities calibrated on separate lists.", fontsize=10, color="#50657B")
    fig.text(0.20, 0.095, "AUC = ranking area; Brier = mean squared probability error; log2 = base-2 log; std = standard deviation.", fontsize=9, color="#50657B")
    fig.text(0.20, 0.06, "Good ranking across families does not prove individual NO predictions safe; inspect the threshold chart before using them for pruning.", fontsize=9, color=RED)
    fig.savefig(path, dpi=170)
    plt.close(fig)


def write_summary(data: dict, path: Path) -> None:
    m = data["test"]["forest"]
    b = data["test"]["density_baseline"]
    ood = data["unseen_n24"]["forest"]
    very_low = data["test"]["no_thresholds"][0]
    lines = [
        "# Subset-sum probability classifier",
        "",
        "Series navigation: [reading order](../index.html#arc) · [Note IV: pairing in certified approximation](../Certified_Approximation_of_Subset_Sum.html).",
        "",
        "This experiment is discussed in [companion Note II](../Subset_Sum_as_a_Stress_Test.html) and reinterpreted for the random-target question in [Note III](../Probability_Valued_Subset_Sum.html).",
        "",
        "A random forest predicts the probability that a target can be formed from a list of positive integers. "
        "Every label is computed exactly by meet-in-the-middle. Targets are sampled independently of labels "
        "from the middle 40% of each list's total sum, then required to pass simple modular certificates. "
        "The model sees only summary features of the list and target, not the exact subset sums.",
        "",
        "Here $n$ is the number of weights, and the predicted YES chance in the charts is the model's estimate, not a certificate. ROC AUC (area under the receiver operating characteristic curve) measures how well the score ranks YES above NO; 0.5 is chance ranking and 1 is perfect ranking. Brier score is the mean squared difference between predicted YES chances and exact 0/1 labels, so lower is better.",
        "The chart's `log2` means base-2 logarithm, `std` means standard deviation, and coefficient of variation is standard deviation divided by mean weight. The log density proxy compares the number of possible count patterns with the spread of the weights; it is only a model feature, not a certificate. `independent` lists use separately sampled weights, while `paired` lists repeat each sampled value twice.",
        "",
        f"- Training: {data['counts']['train']:,} targets; calibration: {data['counts']['calibration']:,}; "
        f"held-out test: {data['counts']['test']:,}. Splits use disjoint input lists.",
        f"- Held-out YES rate: {m['positive_rate']:.1%}. Forest AUC {m['auc']:.3f}, "
        f"Brier {m['brier']:.3f}, accuracy {m['accuracy']:.1%}.",
        f"- Simple density-model AUC {b['auc']:.3f}, Brier {b['brier']:.3f}. "
        f"On unseen n=24 lists, forest AUC {ood['auc']:.3f}, Brier {ood['brier']:.3f}.",
        f"- Even at a predicted YES chance of at most {very_low['threshold']:.0%}, {very_low['wrong_yes']} of "
        f"{very_low['proposed_no']} proposed NO answers are actually YES.",
        "",
        "## Charts",
        "",
        "![Predicted probabilities, calibration, ROC, and confusion matrix](classifier_overview.png)",
        "",
        "![Proposed NO coverage and errors by probability threshold](classifier_thresholds.png)",
        "",
        "![Performance across input families and feature importance](classifier_generalization.png)",
        "",
        "## Interpretation",
        "",
        "The classifier can rank cases by likelihood, but a predicted NO is not a proof. "
        "False NO predictions are exactly the dangerous errors for certified elimination. "
        "The threshold chart counts them explicitly; the framework still needs an exact verifier.",
        "",
        "The forest performs about as well as the simple density-based classifier. "
        "This suggests most of its signal comes from density, rather than a new property of the pairing framework. "
        "The comparison is not against an optimized learned solver. "
        "The input families are synthetic, the probability calibration is specific to their sampling distribution, "
        "and the model has not been shown to reduce exact solution time.",
        "",
        "Reproduce with `python subset-sum/ml_experiment.py` after installing [requirements-ml.txt](requirements-ml.txt). "
        "Raw scores and thresholds are in [ml_results.json](ml_results.json); each held-out prediction is in "
        "[ml_predictions.csv](ml_predictions.csv).",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    validate_exact_labels()
    rows, unseen = generate()
    train, calibration, test = split_groups(rows)
    forest, calibrator, baseline = fit_models(train, calibration)
    test_p, test_baseline = predict(forest, calibrator, baseline, test)
    unseen_p, unseen_baseline = predict(forest, calibrator, baseline, unseen)
    test_y, unseen_y = labels(test), labels(unseen)
    results = {
        "seed": SEED,
        "counts": {"train": len(train), "calibration": len(calibration), "test": len(test), "unseen_n24": len(unseen)},
        "families": FAMILIES,
        "train_n": N_VALUES,
        "features": FEATURES,
        "test": {"forest": score(test_y, test_p), "density_baseline": score(test_y, test_baseline), "no_thresholds": threshold_stats(test_y, test_p)},
        "unseen_n24": {"forest": score(unseen_y, unseen_p), "density_baseline": score(unseen_y, unseen_baseline), "no_thresholds": threshold_stats(unseen_y, unseen_p)},
    }
    for name, subset, y, p, simple in (("test", test, test_y, test_p, test_baseline), ("unseen_n24", unseen, unseen_y, unseen_p, unseen_baseline)):
        results[name]["by_family"] = {}
        for family in FAMILIES:
            sel = np.asarray([row["family"] == family for row in subset])
            results[name]["by_family"][family] = {"forest": score(y[sel], p[sel]), "density_baseline": score(y[sel], simple[sel])}
    (HERE / "ml_results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    with (HERE / "ml_predictions.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["split", "group_id", "family", "n", "target", "exact_yes", "probability_yes", "density_baseline_probability"])
        for split_name, subset, probs, simple in (("test", test, test_p, test_baseline), ("unseen_n24", unseen, unseen_p, unseen_baseline)):
            for row, probability, simple_probability in zip(subset, probs, simple):
                writer.writerow([split_name, row["group_id"], row["family"], row["n"], row["target"], row["label"], f"{probability:.8f}", f"{simple_probability:.8f}"])
    draw_overview(test_y, test_p, test_baseline, results["test"]["forest"], results["test"]["density_baseline"], HERE / "classifier_overview.png")
    draw_thresholds(test_y, test_p, results["test"]["no_thresholds"], HERE / "classifier_thresholds.png")
    draw_generalization(test, test_y, test_p, unseen, unseen_y, unseen_p, forest, HERE / "classifier_generalization.png")
    write_summary(results, HERE / "ML_RESULTS.md")
    print(json.dumps({"test": results["test"], "unseen_n24": results["unseen_n24"]["forest"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
