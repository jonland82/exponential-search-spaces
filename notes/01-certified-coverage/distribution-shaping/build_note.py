"""Build the standalone note without rerunning experiments or changing evidence."""

import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
STEM = "Distribution_Shaped_Difficulty_Buckets"


def main():
    report = json.loads((HERE / "validation.json").read_text(encoding="utf-8"))
    if report["status"] != "passed":
        raise RuntimeError("verification record is not passing")
    for name, expected in report["source_sha256"].items():
        if hashlib.sha256((HERE / name).read_bytes()).hexdigest() != expected:
            raise RuntimeError(f"source differs from verification record: {name}")
    source = (HERE / (STEM + ".tex")).read_text(encoding="utf-8")
    demo = report["synthetic_demo"]
    expected = {
        "TailChecks": str(report["exact_binomial_tail_checks"]),
        "NullChecks": str(report["enumerated_null_rejection_bounds"]),
        "QuantileChecks": str(report["target_quantile_inverse_checks"]),
        "RouterChecks": str(report["exact_subset_sum_router_checks"]),
        "TrainCount": str(demo["training"]),
        "ReferenceCount": str(demo["reference"]),
        "CalibrationCount": str(demo["calibration"]),
    }
    suffixes = ("Zero", "One", "Two", "Three")
    rows = demo["certified_buckets"]
    if len(rows) != 4 or [row["bucket"] for row in rows] != list(range(4)):
        raise RuntimeError("unexpected demonstration bucket layout")
    for suffix, row in zip(suffixes, rows):
        expected["Mass" + suffix] = f"{100 * row['true_population_mass']:.2f}"
        expected["Purity" + suffix] = f"{100 * row['true_hard_fraction']:.2f}"
        expected["Count" + suffix] = str(row["calibration_count"])
    for macro, value in expected.items():
        pattern = r"\\newcommand\{\\" + macro + r"\}\{([^}]+)\}"
        match = re.search(pattern, source)
        if match is None or match.group(1) != value:
            raise RuntimeError(f"paper evidence mismatch: {macro} should be {value}")
    engine = shutil.which("pdflatex")
    info = shutil.which("pdfinfo")
    if engine is None or info is None:
        raise RuntimeError("pdflatex and pdfinfo are required")
    scratch = (ROOT / ".build" / "latex" / "distribution-shaped-difficulty").resolve()
    if not scratch.is_relative_to(ROOT / ".build"):
        raise RuntimeError("unexpected build directory")
    scratch.mkdir(parents=True, exist_ok=True)
    command = [engine, "-interaction=nonstopmode", "-halt-on-error", "-file-line-error",
               "-no-shell-escape", "-output-directory=" + str(scratch), str(HERE / (STEM + ".tex"))]
    for number in (1, 2):
        result = subprocess.run(command, cwd=HERE, capture_output=True, text=True)
        (scratch / f"pass-{number}.txt").write_text(result.stdout + result.stderr, encoding="utf-8")
        if result.returncode:
            raise RuntimeError(f"LaTeX pass {number} failed:\n" + result.stdout[-6000:])
    log = (scratch / (STEM + ".log")).read_text(encoding="utf-8", errors="replace")
    if re.search(r"Overfull \\[hv]box|LaTeX Warning:.*(?:undefined|multiply defined)", log):
        raise RuntimeError("LaTeX layout/reference warning; inspect " + str(scratch / (STEM + ".log")))
    built = scratch / (STEM + ".pdf")
    metadata = subprocess.run([info, str(built)], capture_output=True, text=True, check=True).stdout
    match = re.search(r"^Pages:\s+(\d+)", metadata, re.MULTILINE)
    if match is None or not 1 <= int(match.group(1)) <= 6:
        raise RuntimeError("expected a short note of at most six pages:\n" + metadata)
    destination = HERE / (STEM + ".pdf")
    shutil.copyfile(built, destination)
    print(f"Built {match.group(1)} pages: {destination}")
    print("Verified source hashes, paper evidence, references, and layout warnings.")


if __name__ == "__main__":
    main()
