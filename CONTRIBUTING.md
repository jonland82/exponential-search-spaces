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
and experiment guides consistent. There are seven numbered notes and two short
companions: clustering beside Note VI (PDF/source), and runtime beside Note VII
(HTML/PDF/source, working draft). Supplements keep their parent folder and do
not increase the numbered-note count. Retain visible draft labels and distinguish
fresh comparisons, retrospective diagnostics and conditional runtime claims.

`python build_papers.py --paper 7` builds Note VII and its runtime companion;
`python tools/note_vi_cluster_artifacts.py --pdf` builds the clustering companion.
For navigation-only changes, link checking and a staged-site check are sufficient;
there is no need to rerun experiments or rewrite manuscript PDFs. Dated protocols,
reports, transcripts and source snapshots document their historical state, so
correct current navigation rather than rewriting old experimental claims.

Stage into a fresh ignored directory, then check the candidate release:

```powershell
python tools/prepare_site.py --output .build/site-review-20261028
python tools/check_links.py --site .build/site-review-20261028
```

Staging does not publish the site.

## Branches and commits

Research development lives on `master`. `main` hosts the published website;
deploying it is a separate action. Prefer a topic branch for independent work,
and follow an explicit requested branch when collaborating on an existing task.

Inspect `git status` and the staged diff before committing. Stage explicit paths,
check that no local environments/caches were included, and use descriptive
commit messages. Fetch before publishing, incorporate remote work without
discarding others' commits, and use a normal fast-forward push. Avoid force
pushes or unrelated history rewrites.
