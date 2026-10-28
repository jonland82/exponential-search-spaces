"""Stage the series index, available papers and supporting evidence."""

import argparse
import os
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.paper_catalog import PAPERS, artifact, directory


def sync_downloads(output, papers=PAPERS):
    """Keep historical root PDF/TeX URLs current on the single Pages branch."""
    for paper in papers:
        if not paper["published"]:
            continue
        shutil.copy2(artifact(paper, ".pdf"), output / (paper["stem"] + ".pdf"))
        text = artifact(paper, ".tex").read_text(encoding="utf-8")
        def rebase(match):
            target = directory(paper) / match[2]
            relative = Path(os.path.relpath(target.resolve(), ROOT)).as_posix()
            return match[1] + relative + match[3]
        text = re.sub(r"(\\(?:input|includegraphics)(?:\[[^\]]*\])?\{)([^}]+)(\})", rebase, text)
        (output / (paper["stem"] + ".tex")).write_text(text, encoding="utf-8")


def prepare(output):
    output = output.resolve()
    if output.exists():
        raise FileExistsError("Choose a new output folder; existing staged sites are preserved.")
    output.mkdir(parents=True)
    for name in ("index.html", "paper.css", ".nojekyll", "README.md", "CONTRIBUTING.md", ".gitattributes", ".gitignore", "build_papers.py"):
        shutil.copy2(ROOT / name, output / name)
    for name in ("fonts", "tools", "subset-sum", "Subset_Sum_Refinement_Experiment",
                 "Structural_Distance_Subset_Sum", "Learned_Solvability_Subset_Sum",
                 "Structural_Geometry_Subset_Sum"):
        shutil.copytree(
            ROOT / name, output / name,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.aux", "*.log", "*.out"),
        )
    (output / "notes").mkdir(exist_ok=True)
    shutil.copy2(ROOT / "notes/README.md", output / "notes/README.md")
    for paper in PAPERS:
        destination = output / "notes" / paper["folder"]
        shutil.copytree(directory(paper), destination,
                        ignore=shutil.ignore_patterns("*.aux", "*.log", "*.out", "*.synctex.gz"))
        if not paper["published"]:
            assert not (destination / (paper["stem"] + ".html")).exists()
            continue
        # Root HTML redirects and downloads preserve earlier published URLs.
        shutil.copy2(ROOT / (paper["stem"] + ".html"), output / (paper["stem"] + ".html"))
    sync_downloads(output)
    for paper in PAPERS:
        if not paper["published"]:
            assert not (output / "notes" / paper["folder"] / (paper["stem"] + ".html")).exists()
    html_count = sum(1 for _ in output.glob("notes/*/*.html"))
    print(f"Prepared {len(PAPERS)} numbered notes, {html_count} HTML papers including companions, downloads and evidence at {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / ".build/site")
    prepare(parser.parse_args().output)
