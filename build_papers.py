"""Build all five PDFs and the published HTML pages from organized note sources."""

from __future__ import annotations

import argparse
import html
import os
from pathlib import Path
import shutil
import subprocess
import sys

from tools.paper_catalog import PAPERS, ROOT, artifact, directory


def relative(target, base):
    return Path(os.path.relpath(target, base)).as_posix()


def build_one(paper, pdf_only=False):
    folder = directory(paper)
    stem = paper["stem"]
    if paper["number"] == "III":
        subprocess.run(
            [sys.executable, str(ROOT / "subset-sum/probability_refinement_artifacts.py")],
            cwd=ROOT, check=True,
        )
    if paper["number"] == "V":
        subprocess.run(
            [sys.executable, str(ROOT / "tools/note_v_artifacts.py")], cwd=ROOT, check=True,
        )
    output = ROOT / ".build" / "latex" / paper["folder"]
    output.mkdir(parents=True, exist_ok=True)
    for _ in range(2):
        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-halt-on-error",
             f"-output-directory={output}", str(artifact(paper, ".tex"))],
            cwd=folder, capture_output=True,
        )
        if result.returncode:
            print(result.stdout.decode("utf-8", errors="replace")[-7000:])
            result.check_returncode()
    shutil.copyfile(output / (stem + ".pdf"), artifact(paper, ".pdf"))
    if pdf_only or not paper["published"] or paper["maintained_html"]:
        print(f"Built {artifact(paper, '.pdf').relative_to(ROOT)}")
        return
    result = subprocess.run(
        ["pandoc", str(artifact(paper, ".tex")), "-f", "latex", "-t", "html", "--mathjax"],
        cwd=folder, check=True, capture_output=True,
    )
    body = result.stdout.decode("utf-8").replace("\r\n", "\n")
    body = body[body.index('<div class="tcolorbox">'):]
    body = body.replace('<div class="tcolorbox">', '<div class="abstract">', 1)
    body = body.replace('<div class="tcolorbox">', '<div class="keyeq">')
    body = body.replace("<h1 ", "<h2 ").replace("</h1>", "</h2>")
    body = body.replace("<table>", '<table class="paper-table">')
    title, description = html.escape(paper["title"]), html.escape(paper["description"])
    related = "\n    ".join(
        f'<a href="{relative(artifact(other, ".html"), folder)}">{html.escape(other["nav_label"])}</a>'
        for other in PAPERS if other["published"] and other is not paper
    )
    home = relative(ROOT / "index.html", folder)
    css = relative(ROOT / "paper.css", folder)
    data = relative(ROOT / paper["data"], folder)
    content = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="{description}">
<title>{title} | Jonathan R. Landers</title>
<script>
window.MathJax = {{
  tex: {{ inlineMath: [['\\\\(','\\\\)']], displayMath: [['\\\\[','\\\\]']], tags: 'none' }},
  svg: {{ fontCache: 'global', scale: 0.98 }},
  options: {{ enableMenu: false }}
}};
</script>
<script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
<link rel="stylesheet" href="{css}">
</head>
<body>
<main>
<nav class="top-links" aria-label="Paper links">
  <a href="{home}">&larr; Series home</a>
  <a href="https://github.com/jonland82/exponential-search-spaces">GitHub repository</a>
  <a href="{stem}.pdf">Download PDF</a>
  <a href="{stem}.tex">LaTeX source</a>
</nav>
<header>
  <span class="series-label">Companion note {paper["number"]} of IV</span>
  <h1>{title}</h1>
  <div class="byline">Jonathan R. Landers<br>October 2026</div>
</header>
{body}
<footer>
  <p>Part of the <a href="{home}">Certified Coverage research sequence</a>.</p>
  <div class="link-row">
    {related}
    <a href="{data}">Methods and data</a>
  </div>
</footer>
</main>
</body>
</html>
"""
    artifact(paper, ".html").write_text(content, encoding="utf-8")
    print(f"Built {artifact(paper, '.pdf').relative_to(ROOT)} and published HTML")


def main():
    choices = [paper["stem"] for paper in PAPERS] + [str(i) for i in range(1, 6)]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper", choices=choices, help="Note number or existing filename stem; default: all five.")
    parser.add_argument("--pdf-only", action="store_true", help="Build PDFs without updating published HTML.")
    args = parser.parse_args()
    for number, paper in enumerate(PAPERS, 1):
        if args.paper and args.paper not in (str(number), paper["stem"]):
            continue
        build_one(paper, args.pdf_only)


if __name__ == "__main__":
    main()
