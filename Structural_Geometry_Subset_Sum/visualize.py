"""A scientific plot of exact aggregate coordinates, outside solver budgets."""
import json

from Structural_Geometry_Subset_Sum.study import CONFIG, check_manifest, manifest, read_jsonl, save_json, verify


def coordinate_cloud(p, r, limit):
    states = {(0, 0)}
    for a, b in zip(p, r):
        states |= {(q+a, s+b) for q, s in states}
        if len(states) > limit:
            # Deterministic diagnostic sample; never an exact NO certificate.
            return sorted(states)[:limit], False
    return sorted(states), True


def plot(output):
    verify(output)
    check_manifest(output, "data_hashes.json")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    diagnostics = read_jsonl(output / "diagnostics.jsonl")
    selected = [row for row in diagnostics if row["case_id"] in (
        "geometry-n20-large_base-s0-planted", "geometry-n20-large_base-s0-fractional_band")]
    assert len(selected) == 2
    panels = []
    figure, axes = plt.subplots(1, 2, figsize=(10, 4.3), layout="constrained")
    for ax, row in zip(axes, selected):
        geometry = row["geometry"]
        if geometry is None:
            ax.text(.5, .5, "Solved by exact preprocessing", ha="center", transform=ax.transAxes)
            panels.append(dict(case_id=row["case_id"], geometry=None))
            continue
        points, complete = coordinate_cloud(geometry["p"], geometry["r"], CONFIG["plot_state_cap"])
        ax.scatter([point[0] for point in points], [point[1] for point in points], s=2, alpha=.3, color="#2879a5", rasterized=True)
        lower, upper = geometry["r_min"], geometry["r_max"]
        base, target = geometry["base"], geometry["target"]
        ax.plot([(target-lower)/base, (target-upper)/base], [lower, upper], color="#bd4f2b", linewidth=2, label="Mq+s=target")
        ax.set(xlabel="Aggregate q = sum(p_i x_i)", ylabel="Residual s = sum(r_i x_i)",
            title="Planted target" if row["case_id"].endswith("planted") else "Fractional-band target")
        ax.grid(alpha=.15)
        ax.legend(fontsize=8, loc="upper left")
        ax.text(.02, .02, f'Feasible integer q count: {geometry["q_count"]}\n'+
            ("Exact reachable coordinates" if complete else "Partial diagnostic coordinates"),
            transform=ax.transAxes, fontsize=8, va="bottom")
        panels.append(dict(case_id=row["case_id"], geometry=geometry, points=points, complete=complete))
    figure.suptitle("Large weights projected into aggregate and residual coordinates", fontsize=12)
    figure.savefig(output / "aggregate_geometry.png", dpi=180)
    figure.savefig(output / "aggregate_geometry.pdf")
    plt.close(figure)
    save_json(output / "geometry_plot.json", dict(panels=panels,
        note="Diagnostic only; fixed first list/targets. No PCA, model fitting, or online oracle use."))
    manifest(output, "plot_hashes.json", ("aggregate_geometry.png", "aggregate_geometry.pdf", "geometry_plot.json"))
    print("Saved aggregate_geometry.png/PDF and exact coordinate provenance", flush=True)
