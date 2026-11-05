"""Render the static research home page from the complete paper catalog."""

from html import escape
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.paper_catalog import ALL_PAPERS, CONCEPTUAL_HIGHLIGHTS, KEY_EQUATIONS, artifact, paper_id

COMPASS_ICON = '''<span class="concept-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" focusable="false"><circle cx="12" cy="12" r="9"/><path class="compass-north" d="m16.5 7.5-2.8 6.2-6.2 2.8 2.8-6.2z"/><path class="compass-south" d="m7.5 16.5 2.8-6.2 3.4 3.4z"/><circle class="compass-center" cx="12" cy="12" r="1"/></svg></span>'''

MATHJAX = r'''  <script>
    window.MathJax = {
      tex: { inlineMath: [['\\(', '\\)']], displayMath: [['\\[', '\\]']], tags: 'none' },
      svg: { fontCache: 'global' },
      options: { enableMenu: false }
    };
  </script>
  <script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>'''

THEMES = (
    ("accounting", "Account for the shortcut", "Pay for discovering and using structure, as well as the search left over.",
     "What does a shortcut actually cost?", "The framework begins with an accounting rule. Lower-bound claims then require explicit computational assumptions.",
     ("note-i", "conservation")),
    ("experiments", "Test whether it pays", "Separate fewer candidates from a real reduction in total computation.",
     "Does grouping candidates earn its overhead?", "Controlled experiments keep negative results visible: a smaller represented search need not finish faster.",
     ("note-ii", "note-iv")),
    ("structure", "Find exact structure", "Use tractable cores, distinct sums, and reusable tables to resolve groups.",
     "Which representations give exact savings?", "Tractable cores and reusable summaries replace repeated individual work, with construction and query costs made explicit.",
     ("note-v", "block-overlap", "note-vii", "geometric-runtime", "connections")),
    ("prediction", "Predict before solving", "Distinguish target reachability from completion within a solver budget.",
     "What can we predict before solving?", "Reachability under a target distribution and completion under a solver budget are different probabilistic questions.",
     ("note-iii", "note-vi")),
    ("patterns", "Explain the landscape", "Relate unresolved clusters and runtime bands to available solving routes.",
     "Why do difficulty and runtime form patterns?", "The observed landscape reflects the inputs, available representations, and the policy that chooses among solving routes.",
     ("clusters", "runtime-bands")),
    ("shaping", "Make difficulty identifiable", "Choose a representation's shape, then check what its visible regions mean.",
     "Can we make expensive regions easier to identify?", "Use learned cost information to build a chosen geometry, then independently establish which regions have reliable meaning.",
     ("difficulty-buckets",)),
)

GUIDES = {
    "block-overlap": "notes/01-certified-coverage/block-overlap/README.md",
    "conservation": "notes/conservation-of-computational-work/README.md",
    "clusters": "notes/06-learned-solvability/README.md",
    "geometric-runtime": "notes/07-geometric-cores/README.md",
    "connections": "OpenAI_Subset_Sum_Connections/README.md",
    "runtime-bands": "OpenAI_Subset_Sum_Connections/README.md",
    "difficulty-buckets": "notes/01-certified-coverage/distribution-shaping/README.md",
}


def relative_asset(paper, extension):
    return artifact(paper, extension).relative_to(ROOT).as_posix()


def card(paper):
    key = paper_id(paper)
    formats = paper.get("formats", (".html", ".pdf", ".tex"))
    primary = ".html" if ".html" in formats else ".pdf"
    kicker = "Note " + paper["number"] if "number" in paper else paper["kind"]
    if paper.get("working_draft"):
        kicker += ' · <span class="draft-tag">Working draft</span>'
    elif formats == (".pdf",):
        kicker += " · PDF available"
    links = [f'<a href="{relative_asset(paper, ext)}">{label}</a>'
             for ext, label in ((".html", "HTML"), (".pdf", "PDF"), (".tex", "LaTeX")) if ext in formats]
    guide = paper.get("data") or GUIDES.get(key)
    if guide is None:
        guide = f"notes/{paper['folder']}/README.md"
    links.append(f'<a href="{escape(guide)}">Guide and evidence</a>')
    alias = ' id="connections"' if key == "connections" else ""
    featured = " paper-featured" if key == "difficulty-buckets" else ""
    conceptual = " paper-conceptual" if key in CONCEPTUAL_HIGHLIGHTS else ""
    badge = (
        f'\n          <p class="concept-badge" title="{escape(CONCEPTUAL_HIGHLIGHTS[key])}">'
        f'{COMPASS_ICON}<span>Conceptual highlight</span></p>'
        if conceptual else ""
    )
    highlights = "\n".join(
        f'''            <figure class="equation-highlight">
              <div class="equation-math">\\[{escape(latex)}\\]</div>
              <figcaption>{escape(caption)}</figcaption>
            </figure>'''
        for latex, caption in KEY_EQUATIONS[key]
    )
    return f'''        <article class="paper-entry{featured}{conceptual}" data-paper-id="{key}"{alias}>
          <p class="paper-kicker">{kicker}</p>{badge}
          <h4><a href="{relative_asset(paper, primary)}">{escape(paper['title'])}</a></h4>
          <p>{escape(paper['description'])}</p>
          <div class="paper-equations" aria-label="Key equations">
{highlights}
          </div>
          <div class="link-row">{' '.join(links)}</div>
        </article>'''


def render():
    papers = {paper_id(p): p for p in ALL_PAPERS}
    if set(KEY_EQUATIONS) != set(papers) or any(
        not 1 <= len(equations) <= 2 for equations in KEY_EQUATIONS.values()
    ):
        raise ValueError("every paper must have one or two key equations")
    ordered = [key for theme in THEMES for key in theme[5]]
    if len(ordered) != len(set(ordered)) or set(ordered) != set(papers):
        raise ValueError("reading themes must include every paper exactly once")
    if not set(CONCEPTUAL_HIGHLIGHTS) <= set(papers):
        raise ValueError("conceptual highlights must identify catalog papers")
    steps, groups = [], []
    for number, (key, label, summary, question, context, keys) in enumerate(THEMES, 1):
        steps.append(f'''      <li><a href="#{key}"><span class="arc-step">{number:02}</span><h3>{escape(label)}</h3><p>{escape(summary)}</p></a></li>''')
        groups.append(f'''    <section class="theme-group" aria-labelledby="{key}">
      <div class="theme-heading"><span class="theme-number">{number:02}</span><div><h3 id="{key}">{escape(question)}</h3><p>{escape(context)}</p></div></div>
      <div class="paper-grid">
{chr(10).join(card(papers[k]) for k in keys)}
      </div>
    </section>''')
    count = len(papers)
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <meta name="description" content="{count} research papers by Jonathan R. Landers on the cost of representing exponential search: exact structure, subset-sum experiments, solver prediction, runtime distributions, and certified difficulty buckets.">
  <meta name="theme-color" content="#f3f7fc">
  <title>Certified Coverage of Exponential Search Spaces — Jonathan R. Landers</title>
  <link rel="stylesheet" href="paper.css">
{MATHJAX}
</head>
<body class="research-home">
<a class="skip-link" href="#content">Skip to content</a>
<main id="content">
  <nav class="home-nav" aria-label="Main navigation">
    <a class="home-brand" href="index.html">J. R. Landers <span>/ Research</span></a>
    <div class="home-nav-links"><a href="#arc">Reading guide</a><a href="#papers">Papers</a><a href="#reproduce">Reproducibility</a><a href="https://github.com/jonland82/exponential-search-spaces">GitHub <span aria-hidden="true">↗</span></a></div>
  </nav>
  <header class="home-hero">
    <div>
      <p class="eyebrow">Algorithms · Structure · Computational cost</p>
      <h1>Certified Coverage of Exponential Search Spaces</h1>
      <p class="hero-question">When does finding structure make search cheaper?</p>
      <p class="deck">A research program on representations that handle many candidates together—and on identifying the expensive work that remains. Subset sum provides the common test case.</p>
      <div class="hero-actions"><a class="primary-link" href="#arc">Follow the research story <span aria-hidden="true">↓</span></a><a href="#papers">Browse all {count} papers</a></div>
      <p class="hero-meta">Jonathan R. Landers <span aria-hidden="true">·</span> September–November 2026</p>
    </div>
    <aside class="latest-panel" aria-labelledby="latest">
      <p class="eyebrow" id="latest">Recent additions</p>
      <a href="{relative_asset(papers['block-overlap'], '.pdf')}"><span class="latest-label">Exact structure · Working draft</span><strong>Certified Block Overlap in Subset Sum</strong><span>Small local dictionaries, a bounded exact search, and a paid algorithm for finding the partition.</span></a>
      <a href="{relative_asset(papers['difficulty-buckets'], '.pdf')}"><span class="latest-label">Chosen geometry · Working draft</span><strong>Distribution-Shaped Difficulty Buckets</strong><span>Shapes a feature representation and independently checks which regions are large and expensive.</span></a>
      <a href="{relative_asset(papers['conservation'], '.pdf')}"><span class="latest-label">Cost accounting · PDF note</span><strong>A Conservation Law for Search Work</strong><span>Connects structural work, residual search, and explicitly assumed lower bounds.</span></a>
    </aside>
  </header>
  <section class="reading-guide" aria-labelledby="arc">
    <div class="section-heading"><p class="eyebrow">A reading path</p><h2 id="arc">From saving work to mapping difficulty</h2><p>The note numbers record the sequence of development. This route follows the questions that connect the results.</p></div>
    <ol class="arc-grid">
{chr(10).join(steps)}
    </ol>
  </section>
  <section class="paper-library" aria-labelledby="papers">
    <div class="section-heading library-heading"><div><p class="eyebrow">Research library</p><h2 id="papers">{count} papers, organized by question</h2></div><a href="notes/README.md">Full inventory and build guides <span aria-hidden="true">↗</span></a></div>
    <p class="library-intro" id="companions">{sum('number' in p for p in ALL_PAPERS)} numbered notes and {sum('number' not in p for p in ALL_PAPERS)} companions or standalone papers. Working drafts are marked; links show the formats available in this repository.</p>
    <p class="concept-legend">{COMPASS_ICON}<span><strong>Conceptual highlights</strong> mark the foundational framework, conservation, clustering, and difficulty buckets—the ideas connecting the research story.</span></p>
{chr(10).join(groups)}
  </section>
  <section class="research-drafts" aria-labelledby="drafts">
    <div class="section-heading"><p class="eyebrow">Alongside the papers</p><h2 id="drafts">Supporting theory and algorithms</h2></div>
    <div class="draft-grid">
      <article><h3><a href="notes/01-certified-coverage/block-overlap/README.md">Block-overlap proofs and reference solver</a></h3><p>The full Markdown derivation and reproducible code behind the standalone paper, including exhaustive verification and figure-building instructions.</p></article>
      <article id="certification-cost"><h3><a href="notes/01-certified-coverage/certification-cost/README.md">The Cost of Avoiding Search: A Conditional Coverage Law</a></h3><p>An exploratory cost-law draft under an assumed positive exponential floor. Its general lower-bound premise remains unproved.</p></article>
    </div>
  </section>
  <section class="evidence-section" aria-labelledby="language">
    <span id="formalism"></span>
    <div class="section-heading"><p class="eyebrow">How to assess the results</p><h2 id="language">Proofs, measurements, and scope</h2></div>
    <div class="evidence-grid">
      <div><h3>Exact savings need exact structure</h3><p>Core and block theorems give sufficient tractable regimes. They do not establish that every subset-sum input has a cheap representation.</p></div>
      <div><h3>Measured gains include acquisition costs</h3><p>Geometric reuse improves work-capped completions from 453 to 469 on 576 fresh constructed targets. Later refinements mainly save construction; the reported comparisons remain separate.</p></div>
      <div><h3>Prediction carries a different guarantee</h3><p>Bucket mass and purity are population statements for a fixed solver and budget. The new demonstration uses synthetic costs; a fresh paid subset-sum evaluation remains open.</p></div>
    </div>
  </section>
  <section class="reproduce-panel" aria-labelledby="reproduce">
    <div><p class="eyebrow">Reproducibility</p><h2 id="reproduce">Follow the evidence behind each claim</h2><p>Sources, saved inputs, protocols, measurements, and build instructions are linked from the individual guides. Historical experiments retain their original source and result hashes.</p></div>
    <div class="reproduce-links"><a href="README.md">Repository guide <span aria-hidden="true">↗</span></a><a href="CONTRIBUTING.md">Build and preservation rules <span aria-hidden="true">↗</span></a><a href="notes/README.md">Complete paper inventory <span aria-hidden="true">↗</span></a></div>
  </section>
  <footer class="home-footer"><p>Jonathan R. Landers <span aria-hidden="true">·</span> Research archive, 2026</p><p><a href="https://github.com/jonland82/exponential-search-spaces">Repository</a> <span aria-hidden="true">·</span> Updated November 4, 2026</p></footer>
</main>
</body>
</html>
'''


if __name__ == "__main__":
    (ROOT / "index.html").write_text(render(), encoding="utf-8", newline="\n")
    print(f"Rendered {len(ALL_PAPERS)} paper entries in six thematic groups.")
