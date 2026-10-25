"""Presentation-only 3D views of frozen inputs, certified types and completion.

PCA is fitted for display only, without labels. No predictor or solver is fitted
or rerun. Full-list structural extraction avoids empty-kernel false memberships.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import csv
import json
from pathlib import Path
import shutil

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from advanced_features import extract_advanced
from run_pilot import sha


HERE = Path(__file__).resolve().parent
TYPES = ["Superincreasing", "Complete coverage", "Few distinct values",
         "Small reachable support", "Interval / arithmetic progression",
         "Other solved input", "Hard within budget; no certified full type"]
SHORT = ["SI", "COV", "VAL", "SUP", "REP", "OTHER", "HARD"]
COLORS = ["#1976b9", "#009e73", "#b46d10", "#a04499", "#00a8b5", "#758195", "#d83b3e"]
FAMILY_DIMENSION = dict(superincreasing=0, coverage=1, few_values=2,
                        small_support=3, interval_union=4, progression=4)


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def prepare(data):
    for name, digest in json.loads((data / "data_hashes.json").read_text()).items():
        if sha(data / name) != digest:
            raise AssertionError(f"input hash changed: {name}")
    cases = rows(data / "cases.jsonl")
    reference = {r["case_id"]: r for r in rows(data / "references.jsonl") if r["mode"] == "work"}
    if len(cases) != 1152 or len(reference) != len(cases):
        raise AssertionError("expected the complete frozen reference comparison")
    full_features = {}
    records = []
    for case in cases:
        key = tuple(case["weights"])
        if key not in full_features:
            full_features[key] = extract_advanced(key).values
        full = full_features[key]
        memberships = [i for i, distance in enumerate(full) if distance == 0]
        run = reference[case["case_id"]]
        completed = run["status"] != "unresolved"
        preferred = FAMILY_DIMENSION.get(case["family"])
        # Choose one display color; all overlapping exact memberships are kept.
        primary = (preferred if preferred in memberships else memberships[0]) if memberships else (5 if completed else 6)
        successes = [a["method"] for a in run["attempts"] if a["status"] != "unresolved"]
        method = successes[-1] if successes else ("exact target reduction" if completed else "budget/state limit")
        records.append(dict(case_id=case["case_id"], list_id=case["list_id"],
                            base_list_id=case["base_list_id"], family=case["family"],
                            n=case["n"], scale=case["scale"], cohort=case["cohort"],
                            target_rule=case["target_rule"], target=str(case["target"]),
                            weights=[str(w) for w in case["weights"]], budget=case["budget"],
                            completed=completed, status=run["status"], truth=case["truth"],
                            work=run["work"], completion_method=method,
                            primary_type=primary, primary_label=TYPES[primary],
                            exact_memberships=memberships, full_distances=list(full),
                            model_distances=case["vectors"]["five"],
                            kernel_n=len(case["kernel"]["weights"]),
                            kernel_status=case["kernel"]["status"],
                            probability=case["predictions"]["hybrid:logistic"],
                            label=("E-" if completed else "H-") + SHORT[primary]))
    mask = np.array([r["scale"] == 1 for r in records])
    views, projection = {}, {}
    for name, matrix in (("combined", np.array([c["vectors"]["hybrid"] for c in cases], dtype=float)),
                         ("distances", np.array([c["vectors"]["five"] for c in cases], dtype=float))):
        scaler = StandardScaler().fit(matrix[mask])
        pca = PCA(n_components=3, svd_solver="full").fit(scaler.transform(matrix[mask]))
        coordinates = pca.transform(scaler.transform(matrix))
        ratios = pca.explained_variance_ratio_
        title = "All 15 model features" if name == "combined" else "Five model distances"
        views[name] = dict(title=f"{title}: 3D PCA ({100*sum(ratios):.1f}% variance retained)",
                           axes=[f"PC {i+1} ({100*v:.1f}% variance)" for i, v in enumerate(ratios)],
                           coordinates=coordinates.tolist())
        projection[name] = dict(standardization_mean=scaler.mean_.tolist(),
                                standardization_scale=scaler.scale_.tolist(),
                                components=pca.components_.tolist(),
                                explained_variance_ratio=ratios.tolist(),
                                fitting_rows=int(mask.sum()), labels_used=False)
    coordinates = np.array([[c["n"], c["vectors"]["conventional"][3], c["vectors"]["conventional"][7]]
                            for c in cases], dtype=float)
    views["interpretable"] = dict(title="Original input summaries: size, weight magnitude, target position",
                                  axes=["Number of weights n", "log2(maximum weight + 1)", "Target / total weight"],
                                  coordinates=coordinates.tolist())
    for name, view in views.items():
        if np.asarray(view["coordinates"]).shape != (1152, 3) or not np.isfinite(view["coordinates"]).all():
            raise AssertionError("invalid projection")
    return records, views, projection


def summaries(records):
    answer = {}
    for name, subset in (("unscaled", [r for r in records if r["scale"] == 1]), ("all_encodings", records)):
        answer[name] = dict(cases=len(subset), base_lists=len({r["base_list_id"] for r in subset}),
                            completed=sum(r["completed"] for r in subset),
                            unresolved=sum(not r["completed"] for r in subset),
                            primary_types={TYPES[i]: sum(r["primary_type"] == i for r in subset) for i in range(7)},
                            exact_membership_counts={TYPES[i]: sum(i in r["exact_memberships"] for r in subset) for i in range(5)},
                            unresolved_but_certified=[r["case_id"] for r in subset if not r["completed"] and r["exact_memberships"]],
                            other_completion_methods=dict(Counter(r["completion_method"] for r in subset if r["primary_type"] == 5)))
    return answer


def static_plot(output, records, views):
    selected = [i for i, r in enumerate(records) if r["scale"] == 1]
    coordinates = np.asarray(views["combined"]["coordinates"])
    fig = plt.figure(figsize=(14, 8.8), facecolor="#fbfaf7")
    ax = fig.add_axes([.015, .13, .69, .72], projection="3d", facecolor="#fbfaf7")
    for kind in range(7):
        for completed, marker in ((True, "o"), (False, "x")):
            indices = [i for i in selected if records[i]["primary_type"] == kind and records[i]["completed"] == completed]
            if not indices:
                continue
            xyz = coordinates[indices]
            ax.scatter(xyz[:, 0], xyz[:, 1], xyz[:, 2], color=COLORS[kind], marker=marker,
                       s=28 if completed else 37, alpha=.75 if completed else .95,
                       linewidths=.55 if completed else 1.4, depthshade=False)
    ax.view_init(elev=23, azim=-53)
    ax.set_xlabel(views["combined"]["axes"][0], labelpad=10)
    ax.set_ylabel(views["combined"]["axes"][1], labelpad=10)
    ax.set_zlabel(views["combined"]["axes"][2], labelpad=9)
    ax.tick_params(labelsize=9)
    fig.text(.055, .945, "Paper VI  |  Easy and hard inputs in a representative 3D space", fontsize=18, weight="bold", color="#26231f")
    fig.text(.055, .91, views["combined"]["title"] + "  |  576 unscaled cases, 144 weight lists", fontsize=11, color="#595751")
    handles = [Line2D([], [], linestyle="", marker="o", color=COLORS[i], markersize=8,
                      label=TYPES[i].replace("Hard within budget; no certified full type", "Hard: no certified full type")) for i in range(7)]
    fig.legend(handles=handles, title="Color = structural type", loc="upper left",
               bbox_to_anchor=(.72, .83), frameon=False, fontsize=10, title_fontsize=11)
    shape_handles = [Line2D([], [], linestyle="", marker="o", color="#333333", markersize=7,
                           label="Easy: finished within 8L"),
                     Line2D([], [], linestyle="", marker="x", color="#333333", markersize=8,
                           label="Hard: unresolved within 8L")]
    fig.legend(handles=shape_handles, title="Shape = measured solver outcome", loc="upper left",
               bbox_to_anchor=(.72, .49), frameon=False, fontsize=10, title_fontsize=11)
    easy = sum(records[i]["completed"] for i in selected)
    missed = sum(not records[i]["completed"] and bool(records[i]["exact_memberships"]) for i in selected)
    fig.text(.735, .15, f"{easy} easy / {len(selected)-easy} unresolved\n\n{missed} known-type inputs are crosses:\nthe original solver missed a known\neasy structure within its budget.\n\nClasses can overlap; hover in the\ninteractive view to see every match.",
             fontsize=10, linespacing=1.5, color="#595751")
    fig.text(.055, .065, "PCA uses features only; labels do not determine point positions. Projection can hide differences or overlap inputs.", fontsize=10, color="#595751")
    fig.text(.055, .035, "'Hard' means this solver exceeded its budget. 'Other solved' does not establish a new polynomial-time class.", fontsize=10, color="#595751")
    fig.savefig(output / "input_space.png", dpi=180, facecolor=fig.get_facecolor())
    fig.savefig(output / "input_space.pdf", facecolor=fig.get_facecolor())
    plt.close(fig)


def prediction_overlay(records):
    """Join already saved predictions by case ID; never fit or infer a model."""
    study = HERE / "results/neighbors_20261025"
    source = study / "old_predictions_exploratory.jsonl"
    models = {"baseline": "Original combined", "hard": "Add hard-distance",
              "both": "Add both distances", "distances": "Two distances only",
              "knn": "Five nearest lists"}
    sources = {}
    if source.exists():
        hashes = json.loads((study / "artifact_hashes.json").read_text())
        for name in ("old_predictions_exploratory.jsonl", "protocol.json", "INDEPENDENT_VALIDATION.json"):
            path = study / name
            if sha(path) != hashes[name]:
                raise AssertionError(f"prediction source hash changed: {name}")
            sources[str(path.relative_to(HERE.parent))] = sha(path)
        by_id = {row["case_id"]: row for row in rows(source)}
        if all(record["case_id"] in by_id for record in records):
            predictions = [dict(by_id[record["case_id"]], probabilities={
                model: by_id[record["case_id"]]["probabilities"][model] for model in models})
                for record in records]
        else:
            predictions = None
    else:
        predictions = None
    if predictions is None:
        models = {"baseline": "Original combined"}
        sources = {}
        predictions = [dict(case_id=r["case_id"], label=int(r["completed"]),
                            probabilities={"baseline": r["probability"]}) for r in records]
    for record, prediction in zip(records, predictions):
        if prediction["label"] != int(record["completed"]):
            raise AssertionError("prediction overlay label mismatch")
        if abs(prediction["probabilities"]["baseline"] - record["probability"]) > 1e-12:
            raise AssertionError("baseline prediction differs from original plot")
        if set(prediction["probabilities"]) != set(models):
            raise AssertionError("missing prediction model")
        if any(not np.isfinite(p) or not 0 <= p <= 1 for p in prediction["probabilities"].values()):
            raise AssertionError("invalid saved probability")
    return dict(models=models, records=predictions, threshold=.5,
                scope="Original prospective sample; neighbor-model comparisons are exploratory reuse.",
                sources=sources)


def render_interactive(records, views, overlay):
    """Render the offline interface; keep data and coordinates supplied by callers."""
    template = HERE / "input_space_template.html"
    stub = go.Figure(go.Scatter3d(x=[], y=[], z=[]))
    stub.update_layout(paper_bgcolor="#111b2b", plot_bgcolor="#111b2b")
    embedded = pio.to_html(stub, full_html=False, include_plotlyjs=True, div_id="input-space",
                           default_height="100%", config=dict(displaylogo=False, displayModeBar=False))
    content = template.read_text(encoding="utf-8").replace("__PLOT__", embedded)
    for token, value in (("__DATA__", records), ("__VIEWS__", views), ("__TYPES__", TYPES), ("__COLORS__", COLORS), ("__PREDICTIONS__", overlay)):
        content = content.replace(token, json.dumps(value, separators=(",", ":")))
    return content



def build(data, output):
    if output.exists():
        raise FileExistsError("choose a fresh visualization directory")
    records, views, projection = prepare(data)
    overlay = prediction_overlay(records)
    summary = summaries(records)
    output.mkdir(parents=True)
    content = render_interactive(records, views, overlay)
    (output / "input_space.html").write_text(content, encoding="utf-8")
    (output / "points.json").write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    (output / "prediction_overlay.json").write_text(json.dumps(overlay, indent=2) + "\n", encoding="utf-8")
    (output / "projection.json").write_text(json.dumps(dict(projections=projection, summary=summary), indent=2) + "\n", encoding="utf-8")
    with (output / "points.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = ["case_id", "family", "n", "scale", "completed", "primary_label", "all_exact_types", "completion_method", "pc1", "pc2", "pc3"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for i, record in enumerate(records):
            row = {k: record[k] for k in fields if k in record}
            row["all_exact_types"] = "; ".join(TYPES[t] for t in record["exact_memberships"])
            row.update(zip(("pc1", "pc2", "pc3"), views["combined"]["coordinates"][i]))
            writer.writerow(row)
    static_plot(output, records, views)
    shutil.copyfile(Path(__file__), output / Path(__file__).name)
    shutil.copyfile(HERE / "input_space_template.html", output / "input_space_template.html")
    (output / "views.json").write_text(json.dumps(views, separators=(",", ":")) + "\n", encoding="utf-8")
    readme = f'''# Easy and hard inputs in a 3D representative space

[Interactive plot](input_space.html) | [PNG](input_space.png) | [PDF](input_space.pdf)

Default: {summary['unscaled']['cases']} unscaled cases from 144 lists,
{summary['unscaled']['completed']} completed and {summary['unscaled']['unresolved']} unresolved
under the frozen 8L work allowance. Circles indicate completed exact decisions;
crosses indicate unresolved runs. Colors identify exact full-list classes.

The interactive view supports rotation, zoom, type toggles, easy/hard filtering,
paired scaled encodings, and point labels/inspection. Choose among 15-feature
PCA, five-distance PCA, and directly interpretable input axes. HTML includes
Plotly and the data, so no server or internet connection is required.
Prediction lenses color saved estimates or mistakes, with a selectable model,
missed-hard/false-hard focus and optional faint context. Neighbor overlays on
this original sample are exploratory reuse, separate from the fresh follow-up.

Classes overlap: hover/click shows every certified type. Display ties prefer a
matching intended generator class, then coordinate order. Generator names alone
are never treated as certificates. Full-list features are extracted separately:
zero distances on an empty reduced kernel do not create spurious memberships.

Nine unscaled progression-class inputs are known easy structurally but unresolved
by the original reference portfolio. The plot preserves both facts. Other solved
inputs do not establish new polynomial-time classes; unresolved runs do not
establish intrinsic hardness.

PCA is standardized and fitted on unscaled feature rows, with no labels used.
Projection is a visualization, not a retrained completion model or a proof that
classes are separable. Paired encodings and targets from one list are dependent.

`points.csv`/`points.json` preserve per-input labels; `projection.json` records
PCA transforms, variance and counts. `manifest.json` records input/output hashes.
This adds no new solver measurements and changes no frozen evidence.
'''
    (output / "README.md").write_text(readme, encoding="utf-8")
    artifacts = [p for p in output.iterdir() if p.is_file()]
    manifest = dict(created_utc=datetime.now(timezone.utc).isoformat(),
                    source_sha256=sha(Path(__file__)),
                    template_sha256=sha(HERE / "input_space_template.html"),
                    inputs={name: sha(data / name) for name in ("data_hashes.json", "cases.jsonl", "references.jsonl")},
                    structural_sources={name: sha(HERE / name) for name in ("features.py", "advanced_features.py")},
                    outputs={p.name: sha(p) for p in artifacts}, summary=summary, prediction_sources=overlay["sources"],
                    scope="presentation only; unsupervised PCA; no predictor fitting or solver reruns")
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print("Projection variance:", {k: sum(v["explained_variance_ratio"]) for k, v in projection.items()})
    print(f"Saved interactive HTML and PNG/PDF to {output}")


def refresh_presentation(data, output):
    """Refresh an audited presentation without recalculating scientific artifacts."""
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for name, digest in manifest["outputs"].items():
        if sha(output / name) != digest:
            raise AssertionError(f"presentation artifact was modified: {name}")
    for name, digest in manifest["inputs"].items():
        if sha(data / name) != digest:
            raise AssertionError(f"frozen input changed: {name}")
    for name, digest in manifest["structural_sources"].items():
        if sha(HERE / name) != digest:
            raise AssertionError(f"structural source changed: {name}")
    for name, digest in manifest.get("prediction_sources", {}).items():
        if sha(HERE.parent / name) != digest:
            raise AssertionError(f"saved prediction source changed: {name}")
    records = json.loads((output / "points.json").read_text(encoding="utf-8"))
    view_path = output / "views.json"
    if view_path.exists():
        views = json.loads(view_path.read_text(encoding="utf-8"))
    else:
        # The first version stored these exact coordinates only inside its HTML.
        old_html = (output / "input_space.html").read_text(encoding="utf-8")
        payload = old_html.rsplit("\nconst DATA=", 1)[1]
        views = json.loads(payload.split(", VIEWS=", 1)[1].split(", TYPES=", 1)[0])
    with (output / "points.csv").open(encoding="utf-8", newline="") as handle:
        exported = list(csv.DictReader(handle))
    if len(exported) != len(records):
        raise AssertionError("point data count mismatch")
    for i, row in enumerate(exported):
        if row["case_id"] != records[i]["case_id"]:
            raise AssertionError("point identity changed")
        if [float(row[k]) for k in ("pc1", "pc2", "pc3")] != views["combined"]["coordinates"][i]:
            raise AssertionError("stored PCA coordinates changed")
    for name, view in views.items():
        coordinates = np.asarray(view["coordinates"])
        if coordinates.shape != (len(records), 3) or not np.isfinite(coordinates).all():
            raise AssertionError(f"invalid stored view: {name}")
    overlay = prediction_overlay(records)
    (output / "input_space.html").write_text(render_interactive(records, views, overlay), encoding="utf-8")
    (output / "prediction_overlay.json").write_text(json.dumps(overlay, indent=2) + "\n", encoding="utf-8")
    readme_path = output / "README.md"
    readme = readme_path.read_text(encoding="utf-8").split("\n## Prediction overlays", 1)[0]
    readme += '''
## Prediction overlays

The default Mistakes lens distinguishes correct easy, correct hard, missed hard
and false hard predictions. Shape always preserves the observed solver outcome:
circle = completed; cross = unresolved. The Predictions lens colors the model's
easy/hard estimate; Structure restores certified-type colors.

Choose a saved model and focus on all mistakes, missed hard cases, false hard
cases or correct predictions. Faint context keeps the rest of the eligible cloud
visible, without including it in focused counts or CSV exports. Legend entries
also select a category. Click a point for predicted/observed labels, probabilities,
all model estimates, empirical neighbor distances, weights and exact types.

Prediction threshold is fixed at p(easy)=0.5. Overview statistics refer to inputs
eligible under encoding, structural-type and observed-outcome filters, before
the mistake focus. Changing models or focus preserves point positions, camera
and axis ranges. The frame changes only with projection or included encodings.
The CSV export includes the selected model, probability, prediction and mistake
category. PNG exports preserve the active lens, model, focus and category legend.

These are the original prospective inputs. Neighbor models were motivated by
this sample's plot: their overlays are exploratory reuse, not the fresh follow-up
test. Only saved predictions are joined by case ID; no model is refitted or
solver rerun. `prediction_overlay.json` and `manifest.json` record provenance.
The original points, coordinates, static PNG/PDF and experimental evidence stay
byte-for-byte unchanged.
'''
    readme_path.write_text(readme, encoding="utf-8")
    shutil.copyfile(HERE / "input_space_template.html", output / "input_space_template.html")
    shutil.copyfile(Path(__file__), output / Path(__file__).name)
    view_path.write_text(json.dumps(views, separators=(",", ":")) + "\n", encoding="utf-8")
    manifest["source_sha256"] = sha(Path(__file__))
    manifest["template_sha256"] = sha(HERE / "input_space_template.html")
    manifest["presentation_updated_utc"] = datetime.now(timezone.utc).isoformat()
    names = set(manifest["outputs"]) | {"views.json", "input_space_template.html", "prediction_overlay.json"}
    manifest["prediction_sources"] = overlay["sources"]
    manifest["outputs"] = {name: sha(output / name) for name in sorted(names)}
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Refreshed interactive design at {output}; preserved all labels, coordinates, CSV, PNG and PDF.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=HERE / "results/prospective_20261025")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--refresh-presentation", action="store_true",
                        help="Refresh an existing audited HTML interface without fitting or regenerating data.")
    args = parser.parse_args()
    if args.refresh_presentation:
        refresh_presentation(args.data, args.output)
    else:
        build(args.data, args.output)
