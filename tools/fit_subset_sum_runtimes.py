"""Retrospective distribution search on the saved runtime-histogram observations."""
from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
from sklearn.mixture import GaussianMixture
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Learned_Solvability_Subset_Sum/visualizations/runtime_histogram_20261030"
OUTPUT = SOURCE / "distribution_fits"
FAMILIES = {"Exponential": stats.expon, "Gamma": stats.gamma,
            "Weibull": stats.weibull_min, "Lognormal": stats.lognorm,
            "Log-logistic": stats.fisk, "Inverse Gaussian": stats.invgauss}
SEED = 20261030


def fit(name, t, final=False):
    if name in FAMILIES:
        d = FAMILIES[name]
        parameters = d.fit(t, floc=0)
        return dict(name=name, parameters=list(parameters), n_parameters=len(parameters) - 1)
    k = int(name.split()[0])
    g = GaussianMixture(k, n_init=20 if final else 4, random_state=SEED,
                        tol=1e-5 if final else 1e-4, max_iter=500,
                        reg_covar=1e-6).fit(np.log(t)[:, None])
    assert g.converged_, name
    order = np.argsort(g.means_[:, 0])
    return dict(name=name, weights=g.weights_[order].tolist(),
                mu=g.means_[order, 0].tolist(),
                sigma=np.sqrt(g.covariances_[order, 0, 0]).tolist(),
                n_parameters=3 * k - 1)


def logpdf(model, t):
    if model["name"] in FAMILIES:
        return FAMILIES[model["name"]].logpdf(t, *model["parameters"])
    from scipy.special import logsumexp
    terms = [np.log(w) + stats.norm.logpdf(np.log(t), mu, sigma) - np.log(t)
             for w, mu, sigma in zip(model["weights"], model["mu"], model["sigma"])]
    return logsumexp(terms, axis=0)


def cdf(model, t):
    if model["name"] in FAMILIES:
        return FAMILIES[model["name"]].cdf(t, *model["parameters"])
    return sum(w * stats.norm.cdf((np.log(t) - mu) / sigma)
               for w, mu, sigma in zip(model["weights"], model["mu"], model["sigma"]))


def search(records, label):
    t = np.array([float(r["runtime_ms"]) for r in records])
    groups = np.array([r["base_list_id"] for r in records])
    names = list(FAMILIES) + [f"{k} lognormals" for k in range(2, 9)]
    folds = []
    for repeat in range(2):
        lists = np.unique(groups)
        np.random.default_rng(SEED + repeat).shuffle(lists)
        for test_lists in np.array_split(lists, 6):
            test = np.isin(groups, test_lists)
            assert not set(groups[test]) & set(groups[~test])
            folds.append(test)
    results = []
    for name in names:
        model = fit(name, t, final=True)
        ll = float(logpdf(model, t).sum())
        assert np.isfinite(ll)
        fold_scores = []
        heldout_ll = total = 0
        for test in folds:
            trained = fit(name, t[~test])
            values = logpdf(trained, t[test])
            assert np.isfinite(values).all()
            heldout_ll += float(values.sum())
            total += int(test.sum())
            fold_scores.append(float(values.mean()))
        result = dict(model=model, log_likelihood=ll,
                      bic=model["n_parameters"] * np.log(len(t)) - 2 * ll,
                      aic=2 * model["n_parameters"] - 2 * ll,
                      heldout_log_likelihood_per_input=heldout_ll / total,
                      fold_mean_log_likelihood=fold_scores,
                      descriptive_ks_distance=float(stats.kstest(t, lambda x: cdf(model, x)).statistic))
        results.append(result)
        print(label, name, "BIC", round(result["bic"], 2), "heldout LL/input", round(heldout_ll / total, 4), flush=True)
    results.sort(key=lambda r: -r["heldout_log_likelihood_per_input"])
    return dict(label=label, n=len(t), base_lists=len(np.unique(groups)),
                cv_winner=results[0]["model"],
                bic_winner=min(results, key=lambda r: r["bic"])["model"], results=results)


def plot(records, searches):
    fig, axes = plt.subplots(2, 1, figsize=(11.5, 9.2), facecolor="#fbfaf7")
    bins = np.geomspace(.003, 25, 37)
    for ax, search_result in zip(axes, searches):
        subset = records if search_result["label"] == "All recorded stopping/completion times" else [r for r in records if r["completed"] == "True"]
        t = np.array([float(r["runtime_ms"]) for r in subset])
        ax.set_facecolor("#fbfaf7")
        ax.hist(t, bins=bins, color="#b7c4d4", edgecolor="#fbfaf7", label=f"Observed ({len(t)} inputs)")
        candidates = [search_result["cv_winner"],
                      next(r["model"] for r in search_result["results"] if r["model"]["name"] == "Lognormal")]
        for model, color, style in zip(candidates, ["#008878", "#d65c49"], ["-", "--"]):
            expected = len(t) * np.diff(cdf(model, bins))
            ax.stairs(expected, bins, color=color, lw=2, ls=style,
                      label=f"{model['name']}: expected bin counts")
        ax.set_xscale("log")
        ax.set_xlim(bins[0], bins[-1])
        ax.set_ylabel("Input count per log-spaced bin")
        ax.set_title(search_result["label"], loc="left", fontweight="bold", pad=12)
        ax.legend(frameon=False, fontsize=9, loc="upper left")
        ax.spines[["top", "right"]].set_visible(False)
        ax.set_xlabel("Elapsed time (milliseconds; logarithmic axis)")
    fig.suptitle("Distribution search for saved subset-sum runtimes", fontsize=18, fontweight="bold", y=.975)
    fig.text(.085, .025, "Selection: 2 repeats of 6-fold validation holding out entire weight lists; 13 candidate models.\n"
             "Top includes 146 unresolved stops; bottom is conditional on completion. Neither estimates their unknown completion times.", fontsize=9)
    fig.tight_layout(rect=[.02, .075, 1, .94], h_pad=2.8)
    for ext in ["png", "pdf"]:
        fig.savefig(OUTPUT / f"distribution_comparison.{ext}", dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    original_manifest = json.loads((SOURCE / "manifest.json").read_text())
    for relative_path, digest in original_manifest["sources"].items():
        assert hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest() == digest
    path = SOURCE / "plotted_inputs.csv"
    records = list(csv.DictReader(path.open(encoding="utf-8", newline="")))
    raw = [json.loads(s) for s in (ROOT / "Learned_Solvability_Subset_Sum/results/prospective_20261025/references.jsonl").read_text().splitlines()]
    refs = {r["case_id"]: r for r in raw if r["mode"] == "work"}
    for r in records:
        assert float(r["runtime_ms"]) == 1000 * refs[r["case_id"]]["seconds"]
        assert (r["completed"] == "True") == (refs[r["case_id"]]["status"] != "unresolved")
    assert len(records) == 576
    with threadpool_limits(limits=1):
        searches = [search(records, "All recorded stopping/completion times"),
                    search([r for r in records if r["completed"] == "True"], "Completed inputs only")]
    report = dict(source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                  units="milliseconds", logarithm="natural", support="t > 0",
                  selection="Maximum held-out log likelihood per input; 2 repeats, 6 folds, disjoint base weight lists.",
                  limitations=["Retrospective descriptive fit, not a general subset-sum runtime law.",
                               "Unresolved stops are included only as observed stopping times, not censored latent completion-time estimates.",
                               "BIC/AIC are descriptive iid criteria; inputs within lists are dependent; selection uses grouped validation.",
                               "No confirmatory goodness-of-fit p-values after model selection.",
                               "Completed-only fit is conditional on completion under the saved policy and caps."],
                  searches=searches)
    (OUTPUT / "fit_results.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    with (OUTPUT / "model_comparison.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["dataset", "model", "parameters", "bic", "aic", "heldout_log_likelihood_per_input", "descriptive_ks_distance"])
        writer.writeheader()
        for s in searches:
            for r in s["results"]:
                writer.writerow(dict(dataset=s["label"], model=r["model"]["name"], parameters=r["model"]["n_parameters"],
                                     **{key: r[key] for key in ["bic", "aic", "heldout_log_likelihood_per_input", "descriptive_ks_distance"]}))
    plot(records, searches)
    for s in searches:
        print("WINNER", s["label"], json.dumps(s["cv_winner"]), flush=True)


if __name__ == "__main__":
    main()
