# Contributing

Keep changes focused: describe the concrete problem, the resulting behavior,
and the checks that support it. Include source, documentation and the evidence
needed to review a research result together. Separate repository housekeeping
from experimental changes when practical.

## Research evidence

Frozen protocols hash raw source, input, model and result bytes. Preserve those
files and their source snapshots. Add a separate module/protocol/output directory
for follow-up experiments instead of overwriting frozen evidence or silently
retuning on inspected evaluation cases. Label retrospective analyses explicitly.

Commit relevant raw results, source snapshots, manifests, successful validations
and reproduction guides alongside findings. Keep exact certificates distinct
from learned scores, and report total acquisition/checking costs, comparison
baselines, uncertainty and material regressions. Manuscript/publication changes
are separate from new experimental evidence.

The research-package rules in `.gitattributes` disable line-ending conversion.
Do not bulk-format, renormalize or run text cleanup over frozen sources/results.
Compare staged bytes with working files when adding a new frozen package.
Local environments, caches, credentials and generated build scratch belong in
ignored paths; frozen research evidence belongs in Git.

## Verification

Run checks appropriate to the changed code, and the saved experiment's audit
when changing evidence-handling or verification code. A check-only workflow is:

```powershell
git diff --check
python tools/check_links.py
python -m unittest discover -s Structural_Distance_Subset_Sum -p "test_*.py" -v
python Learned_Solvability_Subset_Sum/experiments/run.py all tests
python -m unittest discover -s Structural_Geometry_Subset_Sum/tests -p "test_*.py" -v
```

For the reorganized Paper VI geometry/pruning follow-ups, use their launcher
to include local tests and resolve the original frozen source names:

```powershell
python Learned_Solvability_Subset_Sum/experiments/run.py all tests
python Learned_Solvability_Subset_Sum/experiments/run.py all check
```

See the [Paper VI experiment guide](Learned_Solvability_Subset_Sum/experiments/README.md)
for complete saved audits and commands for new runs.

The learned/geometry checks use the existing NumPy, scikit-learn, joblib,
threadpoolctl and plotting environment. Experiment READMEs document audit
commands. Tests and audits should not regenerate or overwrite saved experiments.
Paper builds can update generated artifacts; run them when those outputs are
part of the intended change.

## Documentation and paper releases

Keep the home `index.html`, root `README.md`, `notes/README.md` and affected note
and experiment guides consistent. The library currently has fourteen distinct
PDF papers: seven numbered notes and seven companions or standalone papers. The
clustering and geometric runtime companions live beside Notes VI and VII;
the two connections/runtime-band expositions live in `OpenAI_Subset_Sum_Connections/`;
the conservation PDF has its own unnumbered note folder; and difficulty buckets
and block overlap live under Note I. Supplements do not change the numbered-note
count. Retain draft labels and distinguish fresh comparisons, retrospective diagnostics,
synthetic verification, and conditional runtime claims.

`tools/paper_catalog.py` owns numbered and supplemental paper metadata.
Its `KEY_EQUATIONS` entries give each paper one or two manuscript-based
equations with concise captions that preserve the relevant assumptions.
`tools/render_home.py` owns the thematic home-page layout and reading path;
run it to regenerate `index.html` after editing its template or catalog.
The link checker requires every catalog PDF in both the home page and the
Markdown inventory, and checks each format declared available. Home-only CSS
is scoped under `.research-home` so paper pages retain their typography.
The homepage renders its equation highlights with MathJax; review them at
desktop and mobile widths after changing the mathematics or card styles.

The separate four-page connections note lives in `OpenAI_Subset_Sum_Connections/`
and builds with `python build_papers.py --paper connections`. Its HTML and PDF
share one LaTeX source, and its source ledger records fixed upstream revisions.

`python build_papers.py --paper 6` builds Note VI and its clustering companion;
`python build_papers.py --paper 7` builds Note VII and its runtime companion.
Both companions have HTML/PDF/source. Builds synchronize root PDF/TeX compatibility
downloads; edit the canonical manuscripts in `notes/`, not those generated copies.
The difficulty-buckets note has a separate evidence-checking builder at
`notes/01-certified-coverage/distribution-shaping/build_note.py`; its pagination
flows naturally, with an upper page-count check rather than forced section
breaks. The block-overlap paper likewise has an evidence-checking builder at
`notes/01-certified-coverage/block-overlap/build_note.py`; it regenerates
structural illustrations, preserves the original checks, and enforces at
most six pages. The connections guide documents the separate runtime-bands build.
The conservation manuscript currently has PDF only: preserve it as supplied
and do not advertise unavailable source or HTML formats.
For navigation-only changes, link checking and a staged-site check are sufficient;
there is no need to rerun experiments or rewrite manuscript PDFs. Dated protocols,
reports, transcripts and source snapshots document their historical state, so
correct current navigation rather than rewriting old experimental claims.

Stage into a fresh ignored directory, then check the candidate release:

```powershell
python tools/prepare_site.py --output .build/site-review-20261028
python tools/check_links.py --site .build/site-review-20261028
```

Staging includes every note directory, including unnumbered manuscripts, and
all fourteen catalog PDFs. Use a fresh output directory for every review.
Staging is an optional local check; the committed root on `master` is the live site.

## Branches and commits

Use **`master`** for this repository. It is the only maintained branch, GitHub's
default branch and the GitHub Pages source (repository root). Keep research,
documentation and generated site files together. A push to `master` triggers
publication; do not recreate a separate site branch. Former `main` release
history has been merged into `master` without rewriting either history.

Inspect `git status` and the staged diff before committing. Stage explicit paths,
check that no local environments/caches were included, and use descriptive
commit messages. Fetch before publishing, incorporate remote work without
discarding others' commits, and use a normal fast-forward push. Avoid force
pushes or unrelated history rewrites.
