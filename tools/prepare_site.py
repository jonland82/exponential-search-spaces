"""Stage the four published notes, preserving legacy URLs and excluding Note V."""

import argparse
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.paper_catalog import PAPERS, artifact


def prepare(output):
    output = output.resolve()
    if output.exists():
        raise FileExistsError("Choose a new output folder; existing staged sites are preserved.")
    output.mkdir(parents=True)
    for name in ("index.html", "paper.css", ".nojekyll"):
        shutil.copy2(ROOT / name, output / name)
    for name in ("fonts", "subset-sum", "Subset_Sum_Refinement_Experiment"):
        shutil.copytree(
            ROOT / name, output / name,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.aux", "*.log", "*.out"),
        )
    for paper in PAPERS:
        if not paper["published"]:
            continue
        destination = output / "notes" / paper["folder"]
        destination.mkdir(parents=True)
        for extension in (".html", ".pdf", ".tex"):
            shutil.copy2(artifact(paper, extension), destination / (paper["stem"] + extension))
        # Compatibility downloads exist only in the deployment artifact.
        shutil.copy2(ROOT / (paper["stem"] + ".html"), output / (paper["stem"] + ".html"))
        shutil.copy2(artifact(paper, ".pdf"), output / (paper["stem"] + ".pdf"))
        text = artifact(paper, ".tex").read_text(encoding="utf-8")
        text = text.replace("{../../subset-sum/", "{subset-sum/")
        (output / (paper["stem"] + ".tex")).write_text(text, encoding="utf-8")
    assert not (output / "notes" / PAPERS[-1]["folder"]).exists()
    assert not any(output.rglob(PAPERS[-1]["stem"] + ".*"))
    print(f"Prepared four published notes and legacy download aliases at {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / ".build/site")
    prepare(parser.parse_args().output)
