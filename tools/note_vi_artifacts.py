"""Generate Paper VI's tables/values from hashed saved evidence; never rerun solvers."""

from collections import defaultdict
import hashlib
import json
from pathlib import Path
import shutil
from statistics import median
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.paper_catalog import PAPERS, directory
from Learned_Solvability_Subset_Sum import resolve_source

STUDY = ROOT / "Learned_Solvability_Subset_Sum/results/prospective_20261025"
BRANCH = ROOT / "Learned_Solvability_Subset_Sum/results/branch_pruning_20261025"


def sha(path):
    return hashlib.sha256(resolve_source(path).read_bytes()).hexdigest()


def read_rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def verify():
    protocol = json.loads((STUDY / "protocol.json").read_text())
    if sha(STUDY / "protocol.json") != (STUDY / "protocol.sha256").read_text().strip():
        raise AssertionError("protocol hash mismatch")
    if sha(STUDY / "models.joblib") != protocol["model_sha256"]:
        raise AssertionError("frozen model changed")
    for name, expected in protocol["source_hashes"].items():
        if sha(ROOT / name) != expected or sha(STUDY / "sources" / name) != expected:
            raise AssertionError(f"protected source changed: {name}")
    for name, expected in protocol["development_hashes"].items():
        if sha(ROOT / "Learned_Solvability_Subset_Sum/results/development_20261025" / name) != expected:
            raise AssertionError("training/development evidence changed")
    for manifest in ("data_hashes.json", "prediction_hashes.json", "priority_hashes.json"):
        for name, expected in json.loads((STUDY / manifest).read_text()).items():
            if sha(STUDY / name) != expected:
                raise AssertionError(f"saved result changed: {name}")
    figure = STUDY / "figures"
    figure_manifest = json.loads((figure / "figure_manifest.json").read_text())
    for name, expected in figure_manifest["input_sha256"].items():
        if sha(STUDY / name) != expected:
            raise AssertionError("figure input changed")
    for name, expected in figure_manifest["output_sha256"].items():
        if sha(figure / name) != expected:
            raise AssertionError("figure output changed")
    return protocol


def build():
    protocol = verify()
    output = directory(next(p for p in PAPERS if p["number"] == "VI"))
    cases = read_rows(STUDY / "cases.jsonl")
    refs = read_rows(STUDY / "references.jsonl")
    pools = read_rows(STUDY / "priority_runs.jsonl")
    prediction = json.loads((STUDY / "prediction_metrics.json").read_text())
    if prediction["mismatches"] != 0 or len(pools) != 672 or len(cases) != 1152:
        raise AssertionError("unexpected/inconsistent evidence counts")
    values = {
        "SixBaseLists": len({c["base_list_id"] for c in cases}),
        "SixEncodings": len({c["list_id"] for c in cases}),
        "SixCases": len(cases), "SixReferenceRuns": len(refs),
        "SixReferenceCorrect": sum(r["status"] != "unresolved" for r in refs),
        "SixReferenceStopped": sum(r["status"] == "unresolved" for r in refs),
        "SixPoolRuns": len(pools),
        "SixPrimaryFive": f"{prediction['models']['five:logistic']['in_distribution']['all']['brier']:.4f}",
        "SixPrimaryOrdinary": f"{prediction['models']['conventional:logistic']['in_distribution']['all']['brier']:.4f}",
        "SixPrimaryCombined": f"{prediction['models']['hybrid:logistic']['in_distribution']['all']['brier']:.4f}",
        "SixAccuracyCombined": f"{100*prediction['models']['hybrid:logistic']['in_distribution']['all']['accuracy_at_half']:.1f}",
        "SixAccuracyOrdinary": f"{100*prediction['models']['conventional:logistic']['in_distribution']['all']['accuracy_at_half']:.1f}",
    }
    primary = prediction["paired"]["hybrid:logistic minus conventional:logistic"]["in_distribution"]
    values.update(SixPrimaryDifference=f"{primary['difference']:+.4f}",
                  SixPrimaryLow=f"{primary['list_bootstrap_95_percentile'][0]:+.4f}",
                  SixPrimaryHigh=f"{primary['list_bootstrap_95_percentile'][1]:+.4f}")
    totals = defaultdict(lambda: defaultdict(int))
    for row in pools:
        totals[(row["mode"], row["fraction"], row["policy"])][row["repeat"]] += row["solved"]
    labels = [("in_distribution", "Same families"), ("in_distribution_scaled", "Same, scaled"),
              ("larger_size", "Larger inputs"), ("larger_size_scaled", "Larger, scaled"),
              ("prior_holdout", "Prior holdouts"), ("prior_holdout_scaled", "Holdouts, scaled"),
              ("unseen_family", "New families"), ("unseen_family_scaled", "New, scaled")]
    rows = [r"\begin{tabular}{lrrrrr}", r"\toprule",
            r"Cohort & Cases & Five & Ordinary & Combined & Difference\\", r"\midrule"]
    secondary = [r"\begin{tabular}{lrrr}", r"\toprule",
                 r"Cohort & Five & Ordinary & Combined\\", r"\midrule"]
    for key, label in labels:
        entries = [prediction["models"][f"{arm}:logistic"][key]["all"] for arm in ("five", "conventional", "hybrid")]
        diff = prediction["paired"]["hybrid:logistic minus conventional:logistic"][key]["difference"]
        rows.append(f"{label} & {entries[0]['n']} & " + " & ".join(f"{e['brier']:.4f}" for e in entries)
                    + f" & {diff:+.4f}" + r"\\")
        forest = [prediction["models"][f"{arm}:forest"][key]["all"]["brier"] for arm in ("five", "conventional", "hybrid")]
        secondary.append(label + " & " + " & ".join(f"{v:.4f}" for v in forest) + r"\\")
    rows += [r"\bottomrule", r"\end{tabular}"]
    secondary += [r"\bottomrule", r"\end{tabular}"]
    (output / "prediction_table.tex").write_text("\n".join(rows) + "\n", encoding="utf-8")
    (output / "forest_table.tex").write_text("\n".join(secondary) + "\n", encoding="utf-8")
    policy_names = ("arrival", "random", "short_input", "distance_rule", "five", "conventional", "hybrid")
    table = [r"\begin{tabular}{llrrrrrrr}", r"\toprule",
             r"Budget & Share & Arrival & Random & Short & Rule & Five & Ordinary & Combined\\", r"\midrule"]
    for mode, mode_label in (("time", "Live time"), ("work", "Work counter")):
        for fraction in (.2, .5):
            counts = [int(median(totals[(mode, fraction, policy)].values())) for policy in policy_names]
            table.append(f"{mode_label} & {round(fraction*100)}\\% & " + " & ".join(map(str, counts)) + r"\\")
        if mode == "time":
            table.append(r"\midrule")
    table += [r"\bottomrule", r"\end{tabular}"]
    (output / "policy_table.tex").write_text("\n".join(table) + "\n", encoding="utf-8")
    for mode, key_mode in (("time", "Time"), ("work", "Work")):
        for fraction, key_fraction in ((.2, "Tight"), (.5, "Loose")):
            for policy, key_policy in (("arrival", "Arrival"), ("conventional", "Ordinary"), ("hybrid", "Combined")):
                samples = list(totals[(mode, fraction, policy)].values())
                values[f"Six{key_mode}{key_fraction}{key_policy}"] = int(median(samples))
                if mode == "time" and fraction == .2:
                    values[f"Six{key_policy}Low"] = min(samples)
                    values[f"Six{key_policy}High"] = max(samples)
    live_conv = values["SixTimeTightOrdinary"]
    live_both = values["SixTimeTightCombined"]
    values["SixTimeGain"] = live_both - live_conv
    values["SixTimeGainPercent"] = f"{100*(live_both-live_conv)/live_conv:.1f}"
    values["SixOvershootMs"] = f"{1000*max(r.get('overshoot_seconds', 0) for r in pools):.2f}"
    values["SixCombinedPlanningStops"] = sum(r["mode"] == "work" and r["policy"] == "hybrid" and
        r["exhausted_phase"] in ("features", "inference", "sorting", "core_queries") for r in pools)
    branch_inputs = branch_artifacts(output, values)
    text = "% Generated from hashed saved evidence; do not edit measured values.\n"
    for name, value in values.items():
        formatted = f"{value:,}".replace(",", "{,}") if isinstance(value, int) else value
        text += f"\\newcommand{{\\{name}}}{{{formatted}}}\n"
    (output / "study_values.tex").write_text(text, encoding="utf-8")
    shutil.copyfile(STUDY / "figures/overview.pdf", output / "study_overview.pdf")
    prediction_plot(output, prediction, labels)
    generated = ("prediction_table.tex", "policy_table.tex", "forest_table.tex", "branch_table.tex", "study_values.tex",
                 "study_overview.pdf", "prediction_plot.pdf", "prediction_plot.png")
    evidence = {"frozen_at_utc": protocol["frozen_at_utc"], "values": values,
                "inputs": {name: sha(STUDY / name) for name in ("protocol.json", "data_hashes.json",
                    "prediction_metrics.json", "priority_runs.jsonl", "priority_summary.json")},
                "branch_inputs": branch_inputs,
                "outputs": {name: sha(output / name) for name in generated},
                "note": "artifact build only; no experiments, training or timing rerun"}
    (output / "paper_evidence.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print("Verified frozen Paper VI evidence; generated tables, values and copied the saved figure.")


def prediction_plot(output, prediction, labels):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6.6, 3.8), constrained_layout=True)
    for number, (arm, title, color) in enumerate(zip(
            ("five", "conventional", "hybrid"), ("Five distances", "Ordinary features", "Combined"),
            ("#608997", "#b1845e", "#70568f"))):
        values = [prediction["models"][f"{arm}:logistic"][key]["all"]["brier"] for key, _ in labels]
        ax.barh([i + (number - 1) * .23 for i in range(len(labels))], values,
                height=.22, label=title, color=color)
    ax.set_yticks(range(len(labels)), [label for _, label in labels], fontsize=8.5)
    ax.tick_params(axis="x", labelsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("Brier score (lower is better)", fontsize=9)
    ax.legend(fontsize=8, loc="upper right")
    fig.savefig(output / "prediction_plot.pdf")
    fig.savefig(output / "prediction_plot.png", dpi=180)
    plt.close(fig)


def branch_artifacts(output, values):
    """Audit the independent follow-up and derive every quoted branch result."""
    manifest = json.loads((BRANCH / "artifact_hashes.json").read_text())
    for name, expected in manifest.items():
        if sha(BRANCH / name) != expected:
            raise AssertionError(f"branch result changed: {name}")
    protocol = json.loads((BRANCH / "protocol.json").read_text())
    if protocol["model_sha256"] != sha(STUDY / "models.joblib"):
        raise AssertionError("branch experiment did not use the frozen model")
    for name, expected in protocol["sources"].items():
        if sha(ROOT / name) != expected or sha(BRANCH / "sources" / name) != expected:
            raise AssertionError(f"branch source changed: {name}")
    cases = read_rows(BRANCH / "cases.jsonl")
    runs = [row for path in sorted(BRANCH.glob("runs_*.jsonl")) for row in read_rows(path)]
    case_map = {c["case_id"]: c for c in cases}
    if len(cases) != 216 or len(runs) != 6048:
        raise AssertionError("unexpected branch evidence counts")
    for row in runs:
        case = case_map[row["case_id"]]
        if row["status"] != "unresolved" and row["status"] != case["truth"]:
            raise AssertionError("incorrect saved branch decision")
        if row["status"] == "yes" and sum(case["weights"][i] for i in row["witness"]) != case["target"]:
            raise AssertionError("invalid branch witness")
    summary = json.loads((BRANCH / "summary.json").read_text())
    policies = [("dfs", "DFS"), ("always_native", "Always, native"),
                ("distance_native", "Distance rule, native"), ("always_matched", "Always, matched"),
                ("distance_matched", "Distance rule, matched"),
                ("conventional", "Ordinary ML"), ("hybrid", "Combined ML")]
    table = [r"\begin{tabular}{lrrrrr}", r"\toprule",
             r"Policy & Live & Node cap & Nodes & Seconds\\", r"\midrule"]
    for policy, label in policies:
        live = summary["by_mode"]["live"][policy]["median"]
        node = summary["by_mode"]["nodes"][policy]["median"]
        live_repeats = [sum(r["status"] != "unresolved" for r in runs if
                           (r["mode"], r["policy"], r["repeat"]) == ("live", policy, repeat))
                        for repeat in range(3)]
        node_runs = [r for r in runs if r["mode"] == "nodes" and r["policy"] == policy]
        if live["completed"] != median(live_repeats) or node["completed"] != sum(
                r["status"] != "unresolved" for r in node_runs):
            raise AssertionError("branch summary differs from raw records")
        table.append(f"{label} & {int(live['completed'])} & {int(node['completed'])} & "
                     + f"{int(node['total_nodes']):,}".replace(",", r"\,")
                     + f" & {node['total_seconds']:.3f}" + r"\\")
    table += [r"\bottomrule", r"\end{tabular}"]
    (output / "branch_table.tex").write_text("\n".join(table) + "\n", encoding="utf-8")
    nodes = {p: {r["case_id"]: r for r in runs if r["mode"] == "nodes" and r["policy"] == p}
             for p in ("dfs", "hybrid")}
    hybrid = list(nodes["hybrid"].values())
    root_no = sum(r["counts"]["structural_no"] for r in hybrid if r["counts"]["nodes"] == 1)
    gains = [r for r in hybrid if r["status"] != "unresolved" and nodes["dfs"][r["case_id"]]["status"] == "unresolved"]
    values.update(SixBranchLists=len({c["list_id"] for c in cases}), SixBranchCases=len(cases),
                  SixBranchRuns=len(runs), SixBranchLiveDfs=int(summary["by_mode"]["live"]["dfs"]["median"]["completed"]),
                  SixBranchLiveCombined=int(summary["by_mode"]["live"]["hybrid"]["median"]["completed"]),
                  SixBranchLiveRule=int(summary["by_mode"]["live"]["distance_native"]["median"]["completed"]),
                  SixBranchInternalNo=sum(r["counts"]["structural_no"] for r in hybrid)-root_no,
                  SixBranchGains=len(gains),
                  SixBranchRootGains=sum(r["counts"]["nodes"] == 1 for r in gains),
                  SixBranchInternalGains=sum(r["counts"]["nodes"] > 1 for r in gains),
                  SixBranchDiagnosticNodes=summary["diagnostics"]["hybrid"]["completion"]["n"],
                  SixBranchDiagnosticAccuracy=f"{100*summary['diagnostics']['hybrid']['completion']['accuracy']:.1f}",
                  SixBranchNoPrecision=f"{100*summary['diagnostics']['hybrid']['no']['precision']:.1f}",
                  SixBranchOvershootMs=f"{1000*max(r['overshoot'] for r in runs):.3f}")
    for baseline, name in (("dfs", "Dfs"), ("distance_native", "Rule")):
        lo, hi = summary["live_paired"][baseline]["list_bootstrap_95_percentile"]
        values[f"SixBranch{name}Low"] = f"{lo:.1f}"
        values[f"SixBranch{name}High"] = f"{hi:.1f}"
    paired = summary["paired"]["dfs"]
    values.update(SixBranchCommonCases=paired["both_complete"],
                  SixBranchCommonCombinedTime=f"{paired['hybrid_seconds']:.3f}",
                  SixBranchCommonDfsTime=f"{paired['baseline_seconds']:.3f}")
    return {name: sha(BRANCH / name) for name in manifest} | {"artifact_hashes.json": sha(BRANCH / "artifact_hashes.json")}


if __name__ == "__main__":
    build()
