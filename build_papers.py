"""Build the catalog's PDFs and published HTML pages from organized note sources."""

from __future__ import annotations

import argparse
import html
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

from tools.paper_catalog import PAPERS, ROOT, artifact, directory


RUNTIME_COMPANION = dict(
    next(paper for paper in PAPERS if paper["number"] == "VII"),
    number="VII-runtime", stem="Runtime_of_Geometric_Core_Subset_Sum",
    title="The Runtime of Geometric Core Subset Sum",
    description="A three-page runtime companion to Note VII: subset-sum context, the Note I equation mapping, bit costs and general-algorithm comparisons.",
    series_label="Runtime companion to Note VII &middot; Working draft",
    create_legacy_redirect=False, max_pages=3,
)
CLUSTER_COMPANION = dict(
    next(paper for paper in PAPERS if paper["number"] == "VI"),
    number="VI-cluster", stem="Why_Unresolved_Inputs_Cluster",
    title="Why Unresolved Inputs Cluster: A Structural and Statistical Account",
    description="A three-page companion explaining structural solving routes and descriptive clustering of budgeted portfolio failures.",
    series_label="Companion to Note VI &middot; Structural and statistical geometry",
    body_start="<p>The subset-sum plot", number_equations=True,
    create_legacy_redirect=False,
)
CONNECTION_NOTE = dict(
    number="connections", folder="openai-connections",
    source_dir="OpenAI_Subset_Sum_Connections", stem="From_Choices_to_Sums",
    title="From Choices to Sums: Connections to OpenAI's Subset-Sum Algorithms",
    description="A four-page note connecting distinct sums, compatible representations and geometric core reuse to OpenAI's subset-sum manuscripts.",
    nav_label="OpenAI connections", data="OpenAI_Subset_Sum_Connections/README.md",
    published=True, maintained_html=False, working_draft=False,
    series_label="",
    create_legacy_redirect=False, max_pages=4,
)


def relative(target, base):
    return Path(os.path.relpath(target, base)).as_posix()


def build_one(paper, pdf_only=False, html_only=False):
    folder = directory(paper)
    stem = paper["stem"]
    if html_only:
        if paper["published"] and not paper["maintained_html"]:
            build_html(paper)
        return
    if paper["number"] == "III":
        subprocess.run(
            [sys.executable, str(ROOT / "subset-sum/probability_refinement_artifacts.py")],
            cwd=ROOT, check=True,
        )
    if paper["number"] == "V":
        subprocess.run(
            [sys.executable, str(ROOT / "tools/note_v_artifacts.py")], cwd=ROOT, check=True,
        )
    if paper["number"] == "VI":
        subprocess.run(
            [sys.executable, str(ROOT / "tools/note_vi_artifacts.py")], cwd=ROOT, check=True,
        )
    if paper["number"] == "VII":
        subprocess.run(
            [sys.executable, str(ROOT / "tools/note_vii_artifacts.py")], cwd=ROOT, check=True,
        )
    if paper["number"] == "VI-cluster":
        subprocess.run(
            [sys.executable, str(ROOT / "tools/note_vi_cluster_artifacts.py")],
            cwd=ROOT, check=True,
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
    if paper.get("max_pages"):
        log = (output / (stem + ".log")).read_text(encoding="utf-8", errors="replace")
        pages = re.search(r"\((\d+) pages?,\s*\d+ bytes\)", log)
        if pages is None or int(pages[1]) > paper["max_pages"]:
            raise ValueError(f"{stem} must fit within {paper['max_pages']} pages")
    shutil.copyfile(output / (stem + ".pdf"), artifact(paper, ".pdf"))
    if pdf_only or not paper["published"] or paper["maintained_html"]:
        print(f"Built {artifact(paper, '.pdf').relative_to(ROOT)}")
        return
    build_html(paper)


def build_html(paper):
    folder, stem = directory(paper), paper["stem"]
    source = artifact(paper, ".tex").read_text(encoding="utf-8")
    if paper.get("number_equations"):
        equations = {}
        def numbered_equation(match):
            label = re.search(r"\\label\{([^}]+)\}", match[1])
            if label is None:
                return match[0]
            key, number = label[1], len(equations) + 1
            equations[key] = number
            equation = match[1].replace(label[0], rf"\tag{{{number}}}")
            return rf"\hypertarget{{{key}}}{{}}\begin{{equation}}{equation}\end{{equation}}"
        source = re.sub(r"\\begin\{equation\}(.*?)\\end\{equation\}",
                        numbered_equation, source, flags=re.S)
        source = re.sub(r"\\eqref\{([^}]+)\}",
                        lambda match: rf"\hyperlink{{{match[1]}}}{{({equations[match[1]]})}}", source)
    bibliography = re.search(r"\\begin\{thebibliography\}\{[^}]*\}(.*?)\\end\{thebibliography\}", source, re.S)
    if bibliography:
        keys = re.findall(r"\\bibitem\{([^}]+)\}", bibliography.group(1))
        numbers = {key: i + 1 for i, key in enumerate(keys)}
        entries = re.sub(r"\\bibitem\{([^}]+)\}",
                         lambda m: r"\item \hypertarget{ref-" + m[1] + "}{} ", bibliography.group(1))
        source = source[:bibliography.start()] + r"\section{References}\begin{enumerate}" + entries + r"\end{enumerate}" + source[bibliography.end():]
        source = re.sub(r"\\cite\{([^}]+)\}", lambda m: ", ".join(
            r"\hyperlink{ref-" + key.strip() + "}{[" + str(numbers[key.strip()]) + "]}"
            for key in m[1].split(",")), source)
    result = subprocess.run(
        ["pandoc", "-f", "latex", "-t", "html", "--mathjax"],
        input=source.encode("utf-8"), cwd=folder, check=True, capture_output=True,
    )
    body = result.stdout.decode("utf-8").replace("\r\n", "\n")
    body = body[body.index(paper.get("body_start", '<div class="tcolorbox">')):]
    if paper.get("body_start"):
        end = body.index("</p>") + len("</p>")
        body = '<div class="abstract">' + body[:end] + '</div>' + body[end:]
    body = body.replace('<div class="tcolorbox">', '<div class="abstract">', 1)
    body = body.replace('<div class="tcolorbox">', '<div class="keyeq">')
    body = body.replace("<h3 ", "<h4 ").replace("</h3>", "</h4>")
    body = body.replace("<h2 ", "<h3 ").replace("</h2>", "</h3>")
    body = body.replace("<h1 ", "<h2 ").replace("</h1>", "</h2>")
    body = body.replace("<table>", '<table class="paper-table">')
    body = re.sub(r'(<table\b.*?</table>)', r'<div class="table-wrap">\1</div>', body, flags=re.S)
    body = body.replace('src="prediction_plot.pdf"', 'src="prediction_plot.png"')
    body = body.replace('src="geometric_gain.pdf"', 'src="geometric_gain.png"')
    body = re.sub(r'<embed src="geometric_gain.png"([^>]*?)/?>',
                  r'<img src="geometric_gain.png"\1 alt="Paired exact-completion gains and avoided core-table constructions">', body)
    body = body.replace('<embed src="prediction_plot.png" />', '<img src="prediction_plot.png" width="1188" height="684" alt="Brier scores for five distances, ordinary features and their combination">')
    body = body.replace('<figcaption aria-hidden="true">', '<figcaption>')
    body = body.replace('<img src="cluster_geometry.png" alt="image" />',
                        '<img src="cluster_geometry.png" style="width:100%;height:auto" '
                        'alt="Frozen input-space projection showing structural certificates and unresolved portfolio outcomes" />')
    body = body.replace('alt=""', 'alt="Comparison of Brier scores for five distances, ordinary features and their combination"')
    title, description = html.escape(paper["title"]), html.escape(paper["description"])
    related = "\n    ".join(
        f'<a href="{relative(artifact(other, ".html" if other["published"] else ".pdf"), folder)}">'
        f'{html.escape(other["nav_label"])}{" (working draft)" if other.get("working_draft") else ""}</a>'
        for other in PAPERS if other is not paper
    )
    home = relative(ROOT / "index.html", folder)
    css = relative(ROOT / "paper.css", folder)
    data = relative(ROOT / paper["data"], folder)
    series_label = paper.get("series_label", (
        f'Companion note {paper["number"]} of {PAPERS[-1]["number"]}'
        + (" &middot; Working draft" if paper.get("working_draft") else "")
    ))
    series_heading = f'  <span class="series-label">{series_label}</span>' if series_label else ""
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
{series_heading}
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
    legacy = ROOT / (stem + ".html")
    if paper.get("create_legacy_redirect", True) and not legacy.exists():
        target = artifact(paper, ".html").relative_to(ROOT).as_posix()
        legacy.write_text(f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="0; url={target}">
<link rel="canonical" href="{target}"><title>Note moved</title>
<script>location.replace('{target}' + location.search + location.hash);</script>
</head><body><p><a href="{target}">Continue to the note</a>.</p></body></html>
''', encoding="utf-8")
    print(f"Built {artifact(paper, '.html').relative_to(ROOT)}")


def main():
    choices = [paper["stem"] for paper in PAPERS] + [str(i) for i in range(1, len(PAPERS) + 1)]
    choices += [CONNECTION_NOTE["stem"], "connections"]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper", choices=choices, help="Note number or filename stem; default: all catalog entries.")
    parser.add_argument("--pdf-only", action="store_true", help="Build PDFs without updating published HTML.")
    parser.add_argument("--html-only", action="store_true", help="Update generated HTML using existing evidence assets, without rebuilding PDFs.")
    args = parser.parse_args()
    if args.pdf_only and args.html_only:
        parser.error("choose either --pdf-only or --html-only")
    selected = []
    for number, paper in enumerate(PAPERS, 1):
        if args.paper and args.paper not in (str(number), paper["stem"]):
            continue
        build_one(paper, args.pdf_only, args.html_only)
        selected.append(paper)
        if paper["number"] == "VI":
            build_one(CLUSTER_COMPANION, args.pdf_only, args.html_only)
        if paper["number"] == "VII":
            build_one(RUNTIME_COMPANION, args.pdf_only, args.html_only)
    if args.paper in (None, "connections", CONNECTION_NOTE["stem"]):
        build_one(CONNECTION_NOTE, args.pdf_only, args.html_only)
    from tools.prepare_site import sync_downloads
    sync_downloads(ROOT, selected)


if __name__ == "__main__":
    main()
