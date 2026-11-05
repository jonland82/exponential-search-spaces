"""Build the block-overlap paper from preserved checks and exact structural counts.

This builds illustrations, not a timing experiment. The original validation
record and the solver/verification sources are read without modification.
"""

import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

from solver import interval_overlap, prepare, solve


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
STEM = "Certified_Block_Overlap_in_Subset_Sum"
FIGURES = ("block_overlap_geometry.pdf", "block_overlap_scaling.pdf")
TEAL, ORANGE, MUTED = "#285a52", "#ad642e", "#637176"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_validation():
    report = json.loads((HERE / "validation.json").read_text(encoding="utf-8"))
    if report["status"] != "passed":
        raise RuntimeError("saved verification is not passing")
    for name, expected in report["source_sha256"].items():
        if digest(HERE / name) != expected:
            raise RuntimeError(f"source differs from saved verification: {name}")
    return report


def structural_counts(report):
    rows = []
    for groups in (1, 2, 4, 8, 16, 32, 64, 100):
        weights = tuple(d * 10**j for j in range(groups) for d in (2, 3, 4))
        represented = prepare(weights, 3)
        yes_target = 7 * (10**groups - 1) // 9
        no_target = 8 * 10**(groups - 1)
        yes, no = solve(represented, yes_target), solve(represented, no_target)
        assert represented.product == 1
        assert len(represented.blocks) == groups
        assert all(block.overlap == 1 and len(block.sums) == 8
                   for block in represented.blocks)
        assert yes.witness is not None
        assert sum(weights[i] for i in yes.witness) == yes_target
        assert yes.nodes == groups + 1
        assert no.witness is None and no.nodes == 1
        rows.append(dict(
            items=len(weights), blocks=groups,
            distinct_global_sums_by_proof=str(1 << len(weights)),
            retained_support_records=sum(len(block.sums) for block in represented.blocks),
            overlap_product=represented.product,
            candidate_blocks_scored=represented.intervals_checked,
            support_candidates_including_reconstruction=represented.support_candidates_constructed,
            yes_search_nodes=yes.nodes, no_search_nodes=no.nodes,
        ))
    last, saved = rows[-1], report["large_constructed_family"]
    expected_pairs = (
        ("items", "items"), ("blocks", "blocks"),
        ("distinct_global_sums_by_proof", "distinct_subset_sums_by_proof"),
        ("overlap_product", "overlap_product"),
        ("candidate_blocks_scored", "discovery_intervals_checked"),
        ("support_candidates_including_reconstruction",
         "support_candidates_constructed_including_reconstruction"),
        ("yes_search_nodes", "yes_search_nodes"), ("no_search_nodes", "no_search_nodes"),
    )
    for actual, expected in expected_pairs:
        if last[actual] != saved[expected]:
            raise RuntimeError(f"large-example evidence mismatch: {actual}")
    return rows


def save_figure(fig, name):
    fig.savefig(HERE / name, bbox_inches="tight",
                metadata={"CreationDate": None, "ModDate": None})
    plt.close(fig)


def make_figures(rows):
    plt.rcParams.update({
        "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
        "axes.spines.top": False, "axes.spines.right": False,
        "pdf.fonttype": 42, "savefig.facecolor": "white",
    })
    sums = (0, 20, 30, 40, 50, 60, 70, 90)
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.5), sharey=True,
                             layout="constrained")
    geometry = []
    for ax, width, residual in zip(axes, (9, 10), (38, 40)):
        eligible = [s for s in sums if residual - width <= s <= residual]
        overlap = interval_overlap(sums, width)
        direct = max(sum(z - width <= s <= z for s in sums) for z in sums)
        assert overlap == direct == len(eligible)
        geometry.append(dict(support=list(sums), lower_total=width,
                             residual=residual, eligible_sums=eligible, overlap=overlap))
        for row, value in enumerate(sums):
            color = ORANGE if value in eligible else TEAL
            ax.plot((value, value + width), (row, row), color=color, lw=5, alpha=.65)
            ax.scatter((value, value + width), (row, row), color=color, s=13, zorder=3)
        ax.plot((residual, residual), (-.6, 7.6), color="#343b3c",
                lw=.85, zorder=4)
        ax.scatter([residual] * len(eligible), [sums.index(s) for s in eligible],
                   marker="D", s=27, facecolor="white", edgecolor=ORANGE, zorder=5)
        ax.set_title(rf"$P={width}$: $\kappa={overlap}$, residual $r={residual}$",
                     loc="left", pad=10)
        ax.set_xlim(-4, 104)
        ax.set_ylim(-.65, 7.65)
        ax.set_yticks(range(len(sums)), labels=[str(s) for s in sums])
        ax.set_xlabel(r"Residual targets in $[s,s+P]$")
        ax.grid(axis="x", color="#e2e5e3", lw=.6)
        ax.set_axisbelow(True)
    axes[0].set_ylabel(r"Local sum $s$")
    save_figure(fig, FIGURES[0])

    n = [row["items"] for row in rows]
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.05), layout="constrained")
    axes[0].plot(n, n, color=ORANGE, marker="o", ms=3,
                 label=r"Global sums: $\log_2(2^n)=n$")
    axes[0].plot(n, [math.log2(row["retained_support_records"]) for row in rows],
                 color=TEAL, marker="s", ms=3, label=r"Stored local sums: $\log_2(8m)$")
    axes[0].set_title("A  Global and local support", loc="left")
    axes[0].set_ylabel(r"$\log_2$(number of sum records)")
    axes[0].yaxis.set_major_locator(MaxNLocator(integer=True, nbins=5))
    for key, label, color, marker in (
        ("support_candidates_including_reconstruction", "Support candidates processed", TEAL, "s"),
        ("candidate_blocks_scored", "Candidate blocks scored", MUTED, "^"),
        ("yes_search_nodes", "YES search nodes", ORANGE, "o"),
    ):
        axes[1].plot(n, [row[key] for row in rows], label=label,
                     color=color, marker=marker, ms=3)
    axes[1].set_yscale("log")
    axes[1].set_title("B  Paid construction and search", loc="left")
    axes[1].set_ylabel("Separate exact counters (log scale)")
    for ax in axes:
        ax.set_xlabel(r"Items $n=3m$")
        ax.grid(color="#e2e5e3", lw=.6)
        ax.set_axisbelow(True)
        ax.legend(frameon=False, fontsize=7, loc="upper left",
                  bbox_to_anchor=(0, -.28), borderaxespad=0)
    save_figure(fig, FIGURES[1])
    return geometry


def write_values(report):
    large = report["large_constructed_family"]
    values = dict(
        ExhaustiveInputs=report["exhaustive_inputs"],
        PartitionChecks=report["partition_optimality_checks"],
        RandomInputs=report["random_inputs"],
        TargetChecks=report["target_checks"],
        LargeItems=large["items"], LargeBlocks=large["blocks"],
        LargeIntervals=large["discovery_intervals_checked"],
        LargeCandidates=large["support_candidates_constructed_including_reconstruction"],
        LargeYesNodes=large["yes_search_nodes"], LargeNoNodes=large["no_search_nodes"],
    )
    text = "% Generated from hash-checked validation.json; do not hand edit.\n"
    text += "".join(r"\newcommand{\%s}{%s}" % (name, f"{value:,}") + "\n"
                    for name, value in values.items())
    (HERE / "paper_values.tex").write_text(text, encoding="utf-8")


def main():
    report = load_validation()
    rows = structural_counts(report)
    geometry = make_figures(rows)
    write_values(report)
    inputs = ("solver.py", "verify.py", "validation.json", "build_note.py", STEM + ".tex")
    outputs = (*FIGURES, "paper_values.tex")
    evidence = dict(
        kind="paper illustrations and deterministic structural counts; no timing measurements",
        source_sha256={name: digest(HERE / name) for name in inputs},
        artifact_sha256={name: digest(HERE / name) for name in outputs},
        geometry=geometry, decimal_family=dict(block_limit=3, rows=rows),
        verification=report,
    )
    (HERE / "paper_evidence.json").write_text(
        json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    engine, info = shutil.which("pdflatex"), shutil.which("pdfinfo")
    if not engine or not info:
        raise RuntimeError("pdflatex and pdfinfo are required")
    scratch = (ROOT / ".build/latex/block-overlap").resolve()
    if not scratch.is_relative_to(ROOT / ".build"):
        raise RuntimeError("unexpected build directory")
    scratch.mkdir(parents=True, exist_ok=True)
    command = [engine, "-interaction=nonstopmode", "-halt-on-error",
               "-file-line-error", "-no-shell-escape",
               "-output-directory=" + str(scratch), str(HERE / (STEM + ".tex"))]
    for number in (1, 2):
        run = subprocess.run(command, cwd=HERE, capture_output=True, text=True)
        (scratch / f"pass-{number}.txt").write_text(run.stdout + run.stderr, encoding="utf-8")
        if run.returncode:
            raise RuntimeError(f"LaTeX pass {number} failed:\n" + run.stdout[-5000:])
    log = (scratch / (STEM + ".log")).read_text(encoding="utf-8", errors="replace")
    if re.search(r"Overfull \\[hv]box|LaTeX Warning:.*(?:undefined|multiply defined)", log):
        raise RuntimeError("LaTeX layout/reference warning; inspect " + str(scratch))
    pdf = scratch / (STEM + ".pdf")
    metadata = subprocess.check_output([info, str(pdf)], text=True)
    pages = re.search(r"^Pages:\s+(\d+)", metadata, re.MULTILINE)
    if pages is None or not 1 <= int(pages.group(1)) <= 6:
        raise RuntimeError("paper must have at most six pages:\n" + metadata)
    shutil.copy2(pdf, HERE / pdf.name)
    print(f"Built {pdf.name}: {pages.group(1)} pages; source hashes, exact plot "
          "counts, layout, and references checked.")


if __name__ == "__main__":
    main()
