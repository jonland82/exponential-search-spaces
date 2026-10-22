"""Summarize probability-valued subset sum using held-out grouped predictions."""

from __future__ import annotations

import csv
import json
import math
import random
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from ml_experiment import PREFILTER_MODULI, SEED, all_sums, make_weights, suffix_residues


HERE = Path(__file__).parent
RNG = np.random.default_rng(20261023)
BOOTSTRAPS = 5000
THRESHOLDS = (0.01, 0.05, 0.10, 0.20, 0.50)


def read_rows() -> list[dict]:
    with (HERE / "ml_predictions.csv").open(newline="", encoding="utf-8") as handle:
        return [
            {
                **row,
                "group_id": int(row["group_id"]),
                "n": int(row["n"]),
                "exact_yes": int(row["exact_yes"]),
                "probability_yes": float(row["probability_yes"]),
            }
            for row in csv.DictReader(handle)
        ]


def grouped_arrays(rows: list[dict]) -> tuple[np.ndarray, np.ndarray]:
    ids = sorted({row["group_id"] for row in rows})
    grouped = {group_id: [] for group_id in ids}
    for row in rows:
        grouped[row["group_id"]].append(row)
    assert all(len(grouped[group_id]) == 4 for group_id in ids)
    y = np.array([[row["exact_yes"] for row in grouped[group_id]] for group_id in ids])
    p = np.array([[row["probability_yes"] for row in grouped[group_id]] for group_id in ids])
    return y, p


def interval(values: np.ndarray) -> list[float]:
    return [float(x) for x in np.quantile(values, [0.025, 0.975])]


def summarize(rows: list[dict]) -> dict:
    y, p = grouped_arrays(rows)
    groups, targets_per_group = y.shape
    indices = RNG.integers(0, groups, size=(BOOTSTRAPS, groups))
    by_group_yes = y.sum(axis=1)
    yes_samples = by_group_yes[indices].sum(axis=1) / (groups * targets_per_group)
    observed_yes_rate = float(y.mean())
    hoeffding_radius = math.sqrt(math.log(40) / (2 * groups))
    result = {
        "groups": groups,
        "targets": int(y.size),
        "observed_yes_rate": observed_yes_rate,
        "yes_rate_bootstrap_95_interval": interval(yes_samples),
        "yes_rate_hoeffding_95_interval": [max(0.0, observed_yes_rate - hoeffding_radius), min(1.0, observed_yes_rate + hoeffding_radius)],
        "thresholds": [],
    }
    for threshold in THRESHOLDS:
        proposed = p <= threshold
        wrong = proposed & (y == 1)
        proposals_by_group = proposed.sum(axis=1)
        wrong_by_group = wrong.sum(axis=1)
        proposals = int(proposed.sum())
        errors = int(wrong.sum())
        sampled_proposals = proposals_by_group[indices].sum(axis=1)
        sampled_errors = wrong_by_group[indices].sum(axis=1)
        conditional_risk = sampled_errors[sampled_proposals > 0] / sampled_proposals[sampled_proposals > 0]
        result["thresholds"].append({
            "p_yes_at_most": threshold,
            "proposed_no": proposals,
            "wrong_no": errors,
            "proposed_fraction": proposals / y.size,
            "observed_wrong_no_rate": errors / proposals if proposals else None,
            "wrong_no_rate_bootstrap_95_interval": interval(conditional_risk),
        })
    return result


def exact_small_instance_bounds(rows: list[dict]) -> list[dict]:
    """Evaluate certified bounds against exact q on held-out 16-item lists."""
    groups = {row["group_id"]: row for row in rows if row["split"] == "test" and row["n"] == 16}
    period = math.lcm(*PREFILTER_MODULI)
    records = []
    for group_id, row in sorted(groups.items()):
        rng = random.Random(f"ml:{SEED}:{group_id}:16:{row['family']}")
        weights = make_weights(16, row["family"], rng)
        total = sum(weights)
        lo, hi = round(0.30 * total), round(0.70 * total)
        masks = [(modulus, suffix_residues(weights, modulus)[0]) for modulus in PREFILTER_MODULI]
        allowed = [residue for residue in range(period) if all((mask >> (residue % modulus)) & 1 for modulus, mask in masks)]
        denominator = sum((hi - residue) // period - (lo - 1 - residue) // period for residue in allowed)
        assert denominator > 0

        # Exact attainable sums are used only to assess the bound, not to construct it.
        attainable = all_sums(weights)
        exact_numerator = sum(lo <= value <= hi for value in attainable)
        multiplicity_limit = math.prod(count + 1 for count in Counter(weights).values())
        certified_upper = min(1.0, multiplicity_limit / denominator)

        witness_rng = random.Random(f"witness:{SEED}:{group_id}")
        witnessed = set()
        for _ in range(512):
            selected = witness_rng.getrandbits(16)
            value = sum(weight for i, weight in enumerate(weights) if selected & (1 << i))
            if lo <= value <= hi:
                witnessed.add(value)
        certified_lower = len(witnessed) / denominator
        exact_q = exact_numerator / denominator
        assert certified_lower <= exact_q + 1e-12 <= certified_upper + 1e-12
        records.append({
            "group_id": group_id,
            "family": row["family"],
            "target_support_size": denominator,
            "distinct_reachable_targets": exact_numerator,
            "certified_lower_512_witnesses": certified_lower,
            "exact_q": exact_q,
            "certified_upper_multiplicity": certified_upper,
        })
    return records


def chart(data: dict) -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "figure.facecolor": "#F7F9FC",
        "axes.facecolor": "white",
        "axes.edgecolor": "#CAD4DF",
        "text.color": "#182A3E",
    })
    fig, axes = plt.subplots(1, 2, figsize=(14, 6.7), dpi=170)
    fig.subplots_adjust(left=0.16, right=0.96, top=0.76, bottom=0.21, wspace=0.34)
    fig.text(0.055, 0.965, "What probability can we actually claim?", fontsize=19, fontweight="bold", va="top")
    fig.text(0.055, 0.916, "Bars use exact YES/NO labels; whiskers are 95% list-level bootstrap intervals, not per-instance guarantees.", fontsize=10, color="#566B7F", va="top")

    ax = axes[0]
    labels = ["Held-out: 16–22 weights", "Unseen: 24 weights"]
    records = [data["test"], data["unseen_n24"]]
    ys = np.arange(2)
    means = np.array([entry["observed_yes_rate"] for entry in records])
    lo = np.array([entry["yes_rate_bootstrap_95_interval"][0] for entry in records])
    hi = np.array([entry["yes_rate_bootstrap_95_interval"][1] for entry in records])
    ax.barh(ys, means, color=["#2463A6", "#148A7B"], height=0.52)
    ax.errorbar(means, ys, xerr=[means - lo, hi - means], fmt="none", color="#182A3E", capsize=5, lw=1.7)
    for i, entry in enumerate(records):
        ax.text(0.54, i, f"{means[i]:.1%} YES\n{entry['targets']:,} targets, {entry['groups']} lists", va="center", fontsize=10)
    ax.set(yticks=ys, yticklabels=labels, xlim=(0, 0.95), xlabel="Chance a sampled target has a solution", title="Random target from the experiment")
    ax.set_xticks(np.arange(0, 1, 0.2), labels=[f"{int(x*100)}%" for x in np.arange(0, 1, 0.2)])
    ax.invert_yaxis()
    ax.grid(axis="x", alpha=0.25)
    ax.set_axisbelow(True)

    ax = axes[1]
    thresholds = data["test"]["thresholds"]
    xs = np.array([row["p_yes_at_most"] for row in thresholds])
    risks = np.array([row["observed_wrong_no_rate"] for row in thresholds])
    lows = np.array([row["wrong_no_rate_bootstrap_95_interval"][0] for row in thresholds])
    highs = np.array([row["wrong_no_rate_bootstrap_95_interval"][1] for row in thresholds])
    ax.errorbar(xs, risks, yerr=[risks - lows, highs - risks], color="#C34E52", marker="o", markersize=7, capsize=5, lw=2)
    ax.set(xlim=(0, 0.52), ylim=(0, max(0.27, float(highs.max()) * 1.16)), xlabel="Propose NO when predicted YES chance ≤ threshold", ylabel="Actually YES among proposed NO", title="Confidence cannot certify deletion")
    ax.set_xticks(xs, labels=[f"{x:.0%}" for x in xs])
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0%}"))
    ax.grid(alpha=0.25)
    for x, risk, entry in zip(xs, risks, thresholds):
        offset = (-44, 9) if x == 0.5 else (3, 9)
        ax.annotate(f"{entry['wrong_no']}/{entry['proposed_no']}", (x, risk), xytext=offset, textcoords="offset points", fontsize=9)
    fig.text(0.055, 0.09, "The left probability depends on the target sampling rule. The right estimates model error on new lists from these synthetic families.", fontsize=9.5, color="#50657B")
    fig.text(0.055, 0.058, "Neither interval makes a wrong NO safe for an individual input; certified pruning still requires an exact verifier.", fontsize=9.5, color="#B9444B", fontweight="bold")
    fig.savefig(HERE / "probability_bounds.png", dpi=170)
    plt.close(fig)


def instance_chart(records: list[dict]) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 6.8), dpi=170)
    fig.patch.set_facecolor("#F7F9FC")
    fig.subplots_adjust(left=0.075, right=0.97, top=0.78, bottom=0.21, wspace=0.17)
    fig.text(0.055, 0.965, "Can simple rules bound the chance of a solution?", fontsize=19, fontweight="bold", color="#182A3E", va="top")
    fig.text(0.055, 0.917, "Each vertical line is one held-out 16-item list. All probabilities use its own target range and modular prefilter.", fontsize=10, color="#566B7F", va="top")
    for ax, family, title in zip(axes, ("independent", "paired"), ("Independent weights", "Repeated pairs")):
        subset = sorted((row for row in records if row["family"] == family), key=lambda row: row["exact_q"])
        xs = np.arange(1, len(subset) + 1)
        lower = np.array([row["certified_lower_512_witnesses"] for row in subset])
        exact = np.array([row["exact_q"] for row in subset])
        upper = np.array([row["certified_upper_multiplicity"] for row in subset])
        ax.vlines(xs, lower, upper, color="#C4CFD9", lw=2.0, zorder=1)
        ax.scatter(xs, lower, s=24, color="#148A7B", label="Lower bound from 512 sampled subsets", zorder=3)
        ax.scatter(xs, exact, s=33, color="#233E60", label="Exact target fraction", zorder=4)
        ax.scatter(xs, upper, s=28, color="#D57B3C", label="Upper bound from repeated-value counts", zorder=3)
        ax.set(xlim=(0, len(subset) + 1), ylim=(-0.03, 1.05), xlabel="Lists sorted by exact target fraction", title=f"{title}  •  {len(subset)} lists")
        ax.set_yticks(np.arange(0, 1.01, 0.2), labels=[f"{x:.0%}" for x in np.arange(0, 1.01, 0.2)])
        ax.grid(axis="y", alpha=0.2)
        ax.set_axisbelow(True)
        ax.text(0.03, 0.96, f"Median: exact {np.median(exact):.1%}  •  upper {np.median(upper):.1%}", transform=ax.transAxes,
                va="top", fontsize=9, color="#283D52", bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.85})
    axes[0].set_ylabel("Probability a sampled target is reachable")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, 0.10), ncol=3, frameon=False, fontsize=10)
    fig.text(0.055, 0.047, "Blue truth is computed by enumerating sums for evaluation only. The teal and orange bounds remain valid without that enumeration.", fontsize=9.5, color="#50657B")
    fig.savefig(HERE / "instance_probability_bounds.png", dpi=170)
    plt.close(fig)


def write_document(data: dict) -> None:
    test = data["test"]
    ood = data["unseen_n24"]
    one_percent = test["thresholds"][0]
    examples = data["instance_bounds_n16"]
    median_lower = float(np.median([row["certified_lower_512_witnesses"] for row in examples]))
    median_exact = float(np.median([row["exact_q"] for row in examples]))
    median_upper = float(np.median([row["certified_upper_multiplicity"] for row in examples]))
    lines = [
        "# Probability-valued subset sum: a precise extension",
        "",
        "This technical record supplies the derivations, chart, and per-list measurements behind [companion Note III](../Probability_Valued_Subset_Sum.html).",
        "",
        "For a fixed list of $n$ positive weights $w=(w_1,\\ldots,w_n)$ and an integer target $t$, let $x_i\\in\\{0,1\\}$ indicate whether weight $w_i$ is chosen. The existence answer",
        "$Y(w,t)=\\mathbf{1}\\{t=\\sum_i x_iw_i\\text{ for some }x_i\\in\\{0,1\\}\\}$ is still exactly 0 or 1; $\\mathbf{1}\\{\\cdot\\}$ is 1 when its condition holds and 0 otherwise.",
        "To make the **outcome** a probability, specify a distribution $\\mu$ for a random target $T$ on a nonempty finite set $D$, with $\\mu(t)=\\Pr(T=t)$:",
        "",
        "$$",
        "A(w)=\\left\\{\\sum_i x_iw_i:x_i\\in\\{0,1\\}\\right\\},",
        "\\qquad q_\\mu(w)=\\Pr_{T\\sim\\mu}[T\\in A(w)]=\\sum_{t\\in A(w)\\cap D}\\mu(t).",
        "$$",
        "",
        "For uniform $T$ on $D$, $q_\\mu(w)=|A(w)\\cap D|/|D|$: the fraction of possible targets that have a solution.",
        "For a nonuniform target distribution, count probability mass instead of targets.",
        "This is a new, well-defined quantity; it does not make a particular target's YES/NO answer uncertain.",
        "",
        "## Certified bounds",
        "",
        "Let $L\\subseteq A(w)\\cap D$ contain *distinct witnessed sums*. For each positive modulus $m$, let $R_m(w)$ be the set of residues modulo $m$ reachable by subsets. Choose a finite set $M$ of such moduli. For any target set $B\\subseteq D$, write $\\mu(B)=\\sum_{t\\in B}\\mu(t)$ for its probability mass. Set",
        "",
        "$$",
        "U=D\\cap\\bigcap_{m\\in M}\\{t:t\\bmod m\\in R_m(w)\\},",
        "\\qquad \\mu(L)\\le q_\\mu(w)\\le\\mu(U).",
        "$$",
        "",
        "The lower bound is exact because every witnessed sum is reachable. The upper bound is exact because every reachable sum passes every residue test.",
        "More exact summaries can enlarge $L$; more sound certificates can shrink $U$.",
        "When pairing partial-sum summaries, count the *distinct union* of pair sums; multiplying counts would double-count collisions.",
        "With uniform $D$, these bounds are $|L|/|D|$ and $|U|/|D|$.",
        "For each distinct weight value indexed by $j$, let $c_j$ be its multiplicity; that value can be selected in only $c_j+1$ ways. A second upper bound for uniform $D$ is $q_\\mu(w)\\le\\min(1,\\prod_j(c_j+1)/|D|)$.",
        "Use the minimum of this and the residue bound. Computing a tight bound has a cost; a loose bound alone does not speed up search.",
        "",
        "For a requested tolerance $\\varepsilon>0$, the interval $[\\mu(L),\\mu(U)]$ certifies an additive-$\\varepsilon$ answer once $\\mu(U)-\\mu(L)\\le\\varepsilon$.",
        "For **exact** $q_\\mu$, the gap must close to zero. As in the original coverage model, the work of finding witnesses and certificates must be counted.",
        "",
        "### A check on held-out 16-item lists",
        "",
        f"For the {len(examples)} held-out $n=16$ lists, we reconstructed each list and its target sampling rule, then enumerated attainable sums **only to assess the bounds**.",
        "The lower bound uses 512 randomly chosen subsets as witnesses; the upper bound uses only value multiplicities and the number of eligible targets.",
        f"Across lists, the median certified interval endpoints were {median_lower:.1%} and {median_upper:.1%}, while the median exact target fraction was {median_exact:.1%}.",
        "The upper bound can be useful when attainable sums are sparse relative to eligible targets; the witness lower bound remains loose with this small budget.",
        "These medians summarize different lists, so they are not themselves a single certified interval.",
        "",
        "![Exact target fractions and certified bounds for held-out 16-item lists](instance_probability_bounds.png)",
        "",
        "## What the classifier estimates",
        "",
        "The trained model outputs $\\widehat p(w,t)$, its estimated YES chance from a feature vector $\\phi(w,t)$. With the full instance fixed, the existence answer is $Y(w,t)\\in\\{0,1\\}$.",
        "For a random list-target pair $(W,T)$ from the synthetic input distribution, the statistical target is $\\Pr(Y(W,T)=1\\mid\\phi(W,T)=\\phi(w,t))$.",
        "Calibration can make this reliable *on average* for that distribution; it is not a deterministic bound for one target.",
        "It can prioritize which targets or regions deserve exact checking, or help stratify estimates of $q_\\mu$.",
        "",
        "If $m$ targets are drawn independently from $\\mu$ for one fixed list and labeled exactly, let $\\widehat q$ be the fraction labeled YES. For any $\\varepsilon>0$, it obeys",
        "",
        "$$",
        "\\Pr(|\\widehat q-q_\\mu(w)|>\\varepsilon)\\le 2e^{-2m\\varepsilon^2}.",
        "$$",
        "",
        "The probability is over the $m$ target draws. This is a sampling guarantee, not a fast subset-sum algorithm: exact labels may still be expensive.",
        "",
        "## Existing held-out evidence, now interpreted probabilistically",
        "",
        "The existing experiment draws four targets per independent list, conditionally on passing simple modular checks.",
        "Its YES frequency therefore estimates success under **that target rule**, averaged over the generated lists; it is not $q_\\mu(w)$ for any one list.",
        "Because this rule already rejects targets excluded by the tested moduli, those same residue screens give a vacuous upper bound for its conditional target distribution.",
        f"On {test['groups']} held-out lists ({test['targets']} targets), the observed YES rate was {test['observed_yes_rate']:.1%}; a 95% list-level bootstrap interval is "
        f"[{test['yes_rate_bootstrap_95_interval'][0]:.1%}, {test['yes_rate_bootstrap_95_interval'][1]:.1%}].",
        f"Treating each list's four-target average as one independent bounded observation, Hoeffding gives a wider distribution-free 95% interval "
        f"[{test['yes_rate_hoeffding_95_interval'][0]:.1%}, {test['yes_rate_hoeffding_95_interval'][1]:.1%}] for the mean success rate across the test schedule.",
        f"For {ood['groups']} unseen $n=24$ lists ({ood['targets']} targets), the rate was {ood['observed_yes_rate']:.1%}; the analogous interval is "
        f"[{ood['yes_rate_bootstrap_95_interval'][0]:.1%}, {ood['yes_rate_bootstrap_95_interval'][1]:.1%}].",
        "",
        f"Among the {one_percent['proposed_no']} held-out targets given $\\widehat p\\le 1\\%$, {one_percent['wrong_no']} actually had a solution: "
        f"an observed missed-YES rate of {one_percent['observed_wrong_no_rate']:.1%}, with a 95% list-level bootstrap interval "
        f"[{one_percent['wrong_no_rate_bootstrap_95_interval'][0]:.1%}, {one_percent['wrong_no_rate_bootstrap_95_interval'][1]:.1%}].",
        "These bootstrap intervals describe sampling uncertainty across lists. They are **not sound per-instance bounds** and cannot certify pruning.",
        "In particular, a bootstrap interval may be $[0,0]$ when a sample contains zero errors; that does not establish zero future error risk.",
        "",
        "![Target success probability and classifier error intervals](probability_bounds.png)",
        "",
        "**Promising direction:** build cheap, instance-specific $L$ and $U$ that close quickly for useful target distributions; use the classifier to choose where exact effort is spent.",
        "Then compare total bound-building cost and interval width against direct exact methods.",
        "The present experiment establishes a statistical signal, not a new exact subset-sum algorithm.",
        "",
        "Reproduce the empirical intervals and chart with `python subset-sum/probability_extension.py` after running `ml_experiment.py`.",
    ]
    (HERE / "PROBABILITY_EXTENSION.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = read_rows()
    instance_bounds = exact_small_instance_bounds(rows)
    data = {
        "bootstrap_replicates": BOOTSTRAPS,
        "bootstrap_seed": 20261023,
        "test": summarize([row for row in rows if row["split"] == "test"]),
        "unseen_n24": summarize([row for row in rows if row["split"] == "unseen_n24"]),
        "instance_bounds_n16": instance_bounds,
    }
    (HERE / "probability_bounds.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    chart(data)
    instance_chart(instance_bounds)
    write_document(data)
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
