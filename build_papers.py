"""Build companion PDFs and matching HTML pages from their LaTeX sources."""

from __future__ import annotations

import html
import subprocess
from pathlib import Path


ROOT = Path(__file__).parent
PAPERS = (
    {
        "stem": "Subset_Sum_as_a_Stress_Test",
        "title": "Subset Sum as a Stress Test for Certified Coverage",
        "description": "A short experimental note testing exact pairing and learned proposals on subset sum.",
        "number": "II",
        "other": "Probability_Valued_Subset_Sum.html",
        "other_label": "Continue to Note III",
        "data": "subset-sum/README.md",
    },
    {
        "stem": "Probability_Valued_Subset_Sum",
        "title": "Probability-Valued Subset Sum: Certified Bounds and Learned Guidance",
        "description": "A short note defining reachable-target probability and evaluating certified bounds.",
        "number": "III",
        "other": "Subset_Sum_as_a_Stress_Test.html",
        "other_label": "Read Note II",
        "data": "subset-sum/PROBABILITY_EXTENSION.md",
    },
)


def build_one(paper: dict[str, str]) -> None:
    stem = paper["stem"]
    for _ in range(2):
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", f"{stem}.tex"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.DEVNULL,
        )
    result = subprocess.run(
        ["pandoc", f"{stem}.tex", "-f", "latex", "-t", "html", "--mathjax"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    body = result.stdout.decode("utf-8").replace("\r\n", "\n")
    body = body[body.index('<div class="tcolorbox">') :]
    body = body.replace('<div class="tcolorbox">', '<div class="abstract">', 1)
    body = body.replace('<div class="tcolorbox">', '<div class="keyeq">')
    body = body.replace("<h1 ", "<h2 ").replace("</h1>", "</h2>")
    body = body.replace("<table>", '<table class="paper-table">')
    title = html.escape(paper["title"])
    description = html.escape(paper["description"])
    content = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="{description}">
<title>{title} — Jonathan R. Landers</title>
<script>
window.MathJax = {{
  tex: {{ inlineMath: [['\\\\(','\\\\)']], displayMath: [['\\\\[','\\\\]']], tags: 'none' }},
  svg: {{ fontCache: 'global', scale: 0.98 }},
  options: {{ enableMenu: false }}
}};
</script>
<script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
<link rel="stylesheet" href="paper.css">
</head>
<body>
<main>
<nav class="top-links" aria-label="Paper links">
  <a href="index.html">← Series home</a>
  <a href="https://github.com/jonland82/exponential-search-spaces">GitHub repository</a>
  <a href="{stem}.pdf">Download PDF</a>
  <a href="{stem}.tex">LaTeX source</a>
</nav>
<header>
  <span class="series-label">Companion note {paper["number"]} of III</span>
  <h1>{title}</h1>
  <div class="byline">Jonathan R. Landers<br>October 2026</div>
</header>
{body}
<footer>
  <p>Part of the <a href="index.html">Certified Coverage research sequence</a>.</p>
  <div class="link-row">
    <a href="Certified_Coverage_of_Exponential_Search_Spaces.html">Note I: Framework</a>
    <a href="{paper["other"]}">{paper["other_label"]}</a>
    <a href="{paper["data"]}">Methods and data</a>
  </div>
</footer>
</main>
</body>
</html>
"""
    (ROOT / f"{stem}.html").write_text(content, encoding="utf-8")


def main() -> None:
    for paper in PAPERS:
        build_one(paper)
        print(f"Built {paper['stem']}.pdf and .html")


if __name__ == "__main__":
    main()
