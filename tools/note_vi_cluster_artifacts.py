"""Build a companion note's figure and descriptive statistics from frozen evidence.

Run from any directory; --pdf also builds the three-page LaTeX note. No model,
PCA transform, or solver is fitted or rerun.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "Learned_Solvability_Subset_Sum/results/prospective_20261025"
VIEW = ROOT / "Learned_Solvability_Subset_Sum/visualizations/input_space_20261025"
OUTPUT = ROOT / "notes/06-learned-solvability"
STEM = "Why_Unresolved_Inputs_Cluster"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def load_evidence():
    data_hashes = read_json(STUDY / "data_hashes.json")
    presentation = read_json(VIEW / "manifest.json")
    inputs = {}
    for folder, names, hashes in (
        (STUDY, ("cases.jsonl", "references.jsonl"), data_hashes),
        (VIEW, ("points.json", "views.json", "projection.json"), presentation["outputs"]),
    ):
        for name in names:
            path = folder / name
            digest = sha(path)
            if digest != hashes[name]:
                raise AssertionError(f"frozen evidence changed: {path}")
            inputs[path.relative_to(ROOT).as_posix()] = digest
    cases = read_rows(STUDY / "cases.jsonl")
    points = read_json(VIEW / "points.json")
    refs = {r["case_id"]: r for r in read_rows(STUDY / "references.jsonl") if r["mode"] == "work"}
    if len(cases) != len(points) or len(cases) != 1152:
        raise AssertionError("unexpected frozen sample")
    for case, point in zip(cases, points):
        if case["case_id"] != point["case_id"] or point["completed"] != (refs[case["case_id"]]["status"] != "unresolved"):
            raise AssertionError("point identity or outcome changed")
    indices = [i for i, c in enumerate(cases) if c["scale"] == 1]
    selected = [cases[i] for i in indices]
    points = [points[i] for i in indices]
    geometry = read_json(VIEW / "projection.json")["projections"]["combined"]
    matrix = np.array([c["vectors"]["hybrid"] for c in selected], dtype=float)
    standardized = (matrix - geometry["standardization_mean"]) / geometry["standardization_scale"]
    xyz = np.array(read_json(VIEW / "views.json")["combined"]["coordinates"])[indices]
    reconstructed = standardized @ np.array(geometry["components"]).T
    if not np.allclose(xyz, reconstructed, rtol=0, atol=1e-12):
        raise AssertionError("saved PCA coordinates do not match the frozen transform")
    return selected, points, standardized, xyz, geometry, inputs


def neighborhoods(matrix, groups, hard):
    """One nearest target per other base list, then five nearest distinct lists."""
    distances = np.linalg.norm(matrix[:, None, :] - matrix[None, :, :], axis=2)
    names = np.unique(groups)
    closest = np.column_stack([
        np.flatnonzero(groups == group)[np.argmin(distances[:, groups == group], axis=1)]
        for group in names
    ])
    list_distances = np.take_along_axis(distances, closest, axis=1)
    list_distances[groups[:, None] == names[None, :]] = np.inf
    # Ties select the first frozen target row, then lexicographic base-list ID.
    nearest = np.take_along_axis(closest, np.argsort(list_distances, axis=1, kind="stable")[:, :5], axis=1)
    if np.any(groups[nearest] == groups[:, None]):
        raise AssertionError("own-list neighbor leakage")
    if any(len(set(row)) != 5 for row in groups[nearest]):
        raise AssertionError("neighbors are not five distinct lists")
    neighbor_hard = hard[nearest]
    p = float(hard.mean())
    incoming_p = float(neighbor_hard.mean())
    joint = float((hard[:, None] * neighbor_hard).mean())
    covariance = joint - p * incoming_p
    conditional = float(neighbor_hard[hard].mean())
    if not np.isclose(conditional, incoming_p + covariance / p, atol=1e-14):
        raise AssertionError("finite-graph covariance identity failed")
    counts = neighbor_hard[hard].sum(axis=1)
    return dict(
        query_count=len(hard), hard_queries=int(hard.sum()), k=5,
        hard_query_neighbor_positions=int(hard.sum() * 5),
        hard_neighbor_positions=int(neighbor_hard[hard].sum()),
        conditional_hard_fraction=conditional, global_hard_fraction=p,
        enrichment_ratio=conditional / p,
        incoming_hard_positions=int(neighbor_hard.sum()),
        total_neighbor_positions=int(neighbor_hard.size),
        incoming_hard_fraction=incoming_p, edge_label_covariance=covariance,
        hard_queries_with_an_easy_neighbor=int((counts < 5).sum()),
        hard_queries_with_majority_hard_neighbors=int((counts >= 3).sum()),
        hard_neighbor_count_histogram={str(i): int((counts == i).sum()) for i in range(6)},
        neighbor_index_sha256=hashlib.sha256(nearest.astype("<i8").tobytes()).hexdigest(),
    )


def figure(points, xyz, geometry):
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "pdf.fonttype": 42})
    colors = ["#1976b9", "#009e73", "#b46d10", "#a04499", "#00a8b5", "#8591a2", "#cf3e4e"]
    labels = ["Superincreasing", "Complete coverage", "Few distinct values", "Small reachable support",
              "Intervals / progressions", "Other completed", "Unclassified, unresolved"]
    fig = plt.figure(figsize=(8.6, 3.8), facecolor="white")
    ax = fig.add_axes([.025, .08, .61, .9], projection="3d", facecolor="white")
    for kind in range(7):
        for completed, marker in ((True, "o"), (False, "x")):
            indices = [i for i, p in enumerate(points) if p["primary_type"] == kind and p["completed"] == completed]
            if indices:
                coords = xyz[indices]
                ax.scatter(*coords.T, color=colors[kind], marker=marker,
                           s=11 if completed else 21, alpha=.7 if completed else .95,
                           linewidths=.35 if completed else .9, depthshade=False)
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.set_pane_color((.98, .985, .99, 1))
        axis._axinfo["grid"].update(color="#dfe5ed", linewidth=.5)
    ratios = geometry["explained_variance_ratio"]
    ax.set_xlabel(f"PC 1 ({ratios[0]:.1%})", labelpad=0, fontsize=8)
    ax.set_ylabel(f"PC 2 ({ratios[1]:.1%})", labelpad=0, fontsize=8)
    ax.set_zlabel(f"PC 3 ({ratios[2]:.1%})", labelpad=0, fontsize=8)
    ax.tick_params(labelsize=7, pad=0)
    ax.view_init(elev=23, azim=-53)
    ax.set_box_aspect((1.15, 1.15, .8))
    handles = [Line2D([], [], linestyle="", marker="o", color=colors[i], markersize=5, label=label)
               for i, label in enumerate(labels)]
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(.655, .94), frameon=False,
               fontsize=8, title="Color: certified full-input type*", title_fontsize=8, labelspacing=.65)
    fig.text(.675, .38, "Shape: observed portfolio outcome", fontsize=8, weight="bold", color="#26364b")
    fig.text(.675, .30, "Circle: completed (430)", fontsize=8, color="#43536b")
    fig.text(.675, .24, "Cross: unresolved (146)", fontsize=8, color="#43536b")
    fig.text(.675, .08, "*One display type; memberships overlap.\nGray/red have no certificate among\nthe five full-input structural types.", fontsize=7, color="#65738a", linespacing=1.5)
    fig.savefig(OUTPUT / "cluster_geometry.png", dpi=240, facecolor="white")
    plt.close(fig)


def build(pdf=False):
    cases, points, z, xyz, geometry, inputs = load_evidence()
    hard = np.array([not p["completed"] for p in points])
    groups = np.array([c["base_list_id"] for c in cases])
    full = neighborhoods(z, groups, hard)
    projected = neighborhoods(xyz, groups, hard)
    if (len(points), len(np.unique(groups)), int(hard.sum())) != (576, 144, 146):
        raise AssertionError("unexpected plotted sample counts")
    if (full["hard_neighbor_positions"], projected["hard_neighbor_positions"]) != (586, 587):
        raise AssertionError("neighborhood counts differ from the audited calculation")
    cross = {
        f"{'certified' if certified else 'uncertified'}_{'completed' if completed else 'unresolved'}":
            sum(bool(p["exact_memberships"]) == certified and p["completed"] == completed for p in points)
        for certified in (True, False) for completed in (True, False)
    }
    evidence = dict(
        scope="Descriptive reuse of original unscaled prospective sample; no solver reruns or model fitting.",
        geometry="Original 15 features; use the saved plot standardization fitted on 576 unscaled rows, not the later training-bank geometry.",
        neighbor_rule="Euclidean; nearest frozen target per base list; exclude entire own base list; choose five distinct lists; target ties use frozen row order, list ties lexicographic ID.",
        input_sha256=inputs, full15=full, pca3=projected,
        pca_retained_variance=float(sum(geometry["explained_variance_ratio"])),
        certificate_outcome_counts=cross,
    )
    (OUTPUT / "cluster_evidence.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    macros = {
        "ClusterCases": len(points), "ClusterLists": len(np.unique(groups)), "ClusterHard": int(hard.sum()),
        "ClusterPositions": full["hard_query_neighbor_positions"], "ClusterHardPositions": full["hard_neighbor_positions"],
        "ClusterRate": f"{100 * full['conditional_hard_fraction']:.2f}", "ClusterBaseRate": f"{100 * hard.mean():.2f}",
        "ClusterEnrichment": f"{full['enrichment_ratio']:.2f}", "ClusterPcaRate": f"{100 * projected['conditional_hard_fraction']:.2f}",
        "ClusterPcaVariance": f"{100 * evidence['pca_retained_variance']:.1f}",
        "ClusterMixed": full["hard_queries_with_an_easy_neighbor"],
        "ClusterIncomingRate": f"{100 * full['incoming_hard_fraction']:.2f}",
    }
    (OUTPUT / "cluster_values.tex").write_text(
        "% Generated from frozen evidence by tools/note_vi_cluster_artifacts.py.\n" +
        "".join(f"\\newcommand{{\\{key}}}{{{value}}}\n" for key, value in macros.items()), encoding="utf-8")
    figure(points, xyz, geometry)
    if pdf:
        build_dir = ROOT / ".build/latex/06-unresolved-clusters"
        build_dir.mkdir(parents=True, exist_ok=True)
        for _ in range(2):
            result = subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error",
                                     f"-output-directory={build_dir}", str(OUTPUT / (STEM + ".tex"))],
                                    cwd=OUTPUT, capture_output=True)
            if result.returncode:
                print(result.stdout.decode("utf-8", errors="replace")[-6000:])
                result.check_returncode()
        log = (build_dir / (STEM + ".log")).read_text(encoding="utf-8", errors="replace")
        pages = re.search(r"\((\d+) pages?,\s*\d+ bytes\)", log)
        if pages is None or int(pages[1]) != 3 or "Overfull" in log:
            raise AssertionError("note must have exactly three pages with no overfull boxes")
        shutil.copyfile(build_dir / (STEM + ".pdf"), OUTPUT / (STEM + ".pdf"))
    print(f"Verified frozen evidence; rebuilt figure and statistics: {full['hard_neighbor_positions']}/{full['hard_query_neighbor_positions']} unresolved neighbors.")
    if pdf:
        print(f"Built {OUTPUT.relative_to(ROOT) / (STEM + '.pdf')}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", action="store_true", help="Also compile the companion PDF with pdflatex.")
    build(parser.parse_args().pdf)
