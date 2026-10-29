# Certified Coverage of Exponential Search Spaces

Jonathan R. Landers | September-October 2026

[Live research site](https://jonland82.github.io/exponential-search-spaces/) | [Latest papers](https://jonland82.github.io/exponential-search-spaces/#latest) | [All seven notes and two companions](notes/README.md)

The sequence follows one question: when can useful structure account for enough of an exponential search that only manageable work remains? This checkout contains HTML/PDF versions of all seven notes and both short companions. Notes V, VII and the runtime companion are labeled as working drafts. **`master` is the single branch for the research, GitHub's default view and the live Pages site.**

## Notes

| Note | Question | Files |
|---|---|---|
| **I. Certified Coverage of Exponential Search Spaces** (published) | When does certified coverage leave a polynomial residual? | [HTML](notes/01-certified-coverage/Certified_Coverage_of_Exponential_Search_Spaces.html) / [PDF](notes/01-certified-coverage/Certified_Coverage_of_Exponential_Search_Spaces.pdf) / [LaTeX](notes/01-certified-coverage/Certified_Coverage_of_Exponential_Search_Spaces.tex) |
| **II. Subset Sum as a Stress Test for Certified Coverage** (published) | Do exact pairing, pruning, and learned proposals save work? | [HTML](notes/02-subset-sum-stress-test/Subset_Sum_as_a_Stress_Test.html) / [PDF](notes/02-subset-sum-stress-test/Subset_Sum_as_a_Stress_Test.pdf) / [LaTeX](notes/02-subset-sum-stress-test/Subset_Sum_as_a_Stress_Test.tex) |
| **III. Probability-Valued Subset Sum: Certified Bounds and Learned Guidance** (published) | How tightly can we bound random-target reachability? | [HTML](notes/03-probability-valued-subset-sum/Probability_Valued_Subset_Sum.html) / [PDF](notes/03-probability-valued-subset-sum/Probability_Valued_Subset_Sum.pdf) / [LaTeX](notes/03-probability-valued-subset-sum/Probability_Valued_Subset_Sum.tex) |
| **IV. Does Pairing Add Value to Certified Approximation? A Subset-Sum Experiment** (published) | Does pairing add value beyond the same approximation rule? | [HTML](notes/04-certified-approximation/Certified_Approximation_of_Subset_Sum.html) / [PDF](notes/04-certified-approximation/Certified_Approximation_of_Subset_Sum.pdf) / [LaTeX](notes/04-certified-approximation/Certified_Approximation_of_Subset_Sum.tex) |
| **V. How Far from Easy? Structural Distance in Subset Sum** (working draft) | How far can a list depart from an easy structure before residual search grows? | [HTML](notes/05-structural-distance/Structural_Distance_in_Subset_Sum.html) / [PDF](notes/05-structural-distance/Structural_Distance_in_Subset_Sum.pdf) / [LaTeX](notes/05-structural-distance/Structural_Distance_in_Subset_Sum.tex) |
| **VI. Predicting Subset-Sum Completion: The Value and Cost of Structural Features** (published) | Do structural distances improve prediction and certified pruning after their costs are paid? | [HTML](notes/06-learned-solvability/Predicting_Subset_Sum_Completion.html) / [PDF](notes/06-learned-solvability/Predicting_Subset_Sum_Completion.pdf) / [LaTeX](notes/06-learned-solvability/Predicting_Subset_Sum_Completion.tex) |
| **VII. Geometric Cores and Exceptions in Subset Sum** (working draft) | Can one exact geometric core and cheap exceptional bounds improve paid completion? | [HTML](notes/07-geometric-cores/Geometric_Cores_and_Exceptions_in_Subset_Sum.html) / [PDF](notes/07-geometric-cores/Geometric_Cores_and_Exceptions_in_Subset_Sum.pdf) / [LaTeX](notes/07-geometric-cores/Geometric_Cores_and_Exceptions_in_Subset_Sum.tex) |

Read I, then II. Notes III and IV branch into random-target probability and fixed-target approximation. Note V returns to exact search: it proves a concrete tractable regime and measures the cost of trying to improve the discovered structure.

## Short companions and latest results

[**From Choices to Sums: Connections to OpenAI's Subset-Sum Algorithms**](OpenAI_Subset_Sum_Connections/From_Choices_to_Sums.html)
is a four-page expository note on distinct sums, compatible
representations and reusable geometric tables, including a derived combined
runtime bound. [PDF](OpenAI_Subset_Sum_Connections/From_Choices_to_Sums.pdf),
[source and rebuild](OpenAI_Subset_Sum_Connections/README.md).

| Companion | Focus | Files |
|---|---|---|
| **Why Unresolved Inputs Cluster: A Structural and Statistical Account** (Note VI; three pages) | Several affordable solving routes and descriptive neighborhood enrichment; unresolved does not mean intrinsically hard. | [HTML](notes/06-learned-solvability/Why_Unresolved_Inputs_Cluster.html) / [PDF](notes/06-learned-solvability/Why_Unresolved_Inputs_Cluster.pdf) / [LaTeX](notes/06-learned-solvability/Why_Unresolved_Inputs_Cluster.tex) / [Evidence and rebuild](notes/06-learned-solvability/README.md#companion-note-why-unresolved-inputs-cluster) |
| **The Runtime of Geometric Core Subset Sum** (Note VII; three-page working draft) | One construction plus exceptional queries, memory costs, sufficient tractable regimes and general-algorithm comparisons. | [HTML](notes/07-geometric-cores/Runtime_of_Geometric_Core_Subset_Sum.html) / [PDF](notes/07-geometric-cores/Runtime_of_Geometric_Core_Subset_Sum.pdf) / [LaTeX](notes/07-geometric-cores/Runtime_of_Geometric_Core_Subset_Sum.tex) |

[Note VII](notes/07-geometric-cores/README.md) supplies an exact geometric solving route: reuse one core table across exceptional assignments. Its first fresh study improves work-capped completions from 453 to 469 of 576 targets over matched root geometry. A second fresh study finds 954 versus root's 916 of 1,152 targets. The final bounds-first refinement mainly saves construction: 90 avoided tables and 1.74% lower capped work; its primary incremental completion comparison is only 953 versus 954, with interval [0,3]. Neither study establishes a new general worst-case bound. The companions explain existing evidence and run no new experiments.

[Note VI](notes/06-learned-solvability/README.md) combines five certified structural features with numerical summaries. Its [experiment package](Learned_Solvability_Subset_Sum/README.md) includes theory, a [prior-work audit](Learned_Solvability_Subset_Sum/docs/LITERATURE.md), calibrated models and [mixed frozen-study findings](Learned_Solvability_Subset_Sum/docs/PROSPECTIVE_FINDINGS.md). The primary probability comparison does not improve; a modest live-time policy gain coexists with an unfavorable work-counter endpoint.

A separate [branch-pruning follow-up](Learned_Solvability_Subset_Sum/docs/BRANCH_FINDINGS.md)
implements Note I's proposal--verification framework using exact easy-core queries.
On 216 fresh cases, a simple distance rule completed 162 within 50 ms each,
compared with 159 for the combined learned gate and 152 for DFS (median totals).
The transferred model has not demonstrated an advantage over the rule.

## Repository layout

- `notes/01-...` through `notes/07-...` contain each note's source, PDF, and local guide. The two companions live alongside Notes VI and VII. The home index links all seven notes and both supplements.
- `subset-sum/` contains the original experiments and publication artifacts for Notes II-IV.
- `Subset_Sum_Refinement_Experiment/` preserves Note III's statistical and deterministic follow-ups, including frozen evidence and reruns.
- `Structural_Distance_Subset_Sum/` contains Note V's proofs, exact solvers, tests, literature audit, frozen study, and raw measurements.
- `Learned_Solvability_Subset_Sum/` contains Note VI's certified features, theory, scoped literature audit, frozen models, exact evidence and prioritization traces. Shared sources are in `code/`, guides in `docs/`, tests in `tests/`, and geometry/pruning follow-ups in `experiments/`; use the documented launchers to preserve frozen imports and paths.
- `Structural_Geometry_Subset_Sum/` contains a separate literature-guided direction: exact geometric solving routes, classifier features and cost-aware gates. The [reusable exception-core experiment](Structural_Geometry_Subset_Sum/EXCEPTION_FINDINGS.md) improves fresh work-capped completions from 453 to 469 over matched root geometry, with full cost accounting and scoped claims.
- Its [bounds-first follow-up](Structural_Geometry_Subset_Sum/BOUNDS_FINDINGS.md) tests 1,152 fresh targets: 954 versus 953 previous-reuse completions, with 1.74% lower capped work and 90 avoided tables; incremental completion and wall-clock gains remain unestablished.
- `tools/` contains the note catalog, evidence-to-paper helpers, link checking, and website staging.
- `index.html`, `paper.css`, and `fonts/` are the home site and shared presentation. Root HTML redirects and generated PDF/TeX compatibility copies preserve earlier numbered-note URLs; edit the canonical sources under `notes/`.
- `.build/` holds ignored LaTeX byproducts and optional staged website files.

The experiment packages retain their existing locations and frozen source bytes. Their protocols and measured data were not regenerated for the reorganization.

## Build and check

See [CONTRIBUTING.md](CONTRIBUTING.md) for Git workflow, verification and preservation
of frozen research evidence.

Paper builds require `pdflatex` and `pandoc`; plots use Matplotlib. Core exact-solver tests use Python's standard library. Learned-model suites also require the packages in [requirements-ml.txt](Learned_Solvability_Subset_Sum/requirements-ml.txt).

```powershell
python build_papers.py
python build_papers.py --paper 5
python build_papers.py --paper 6
python build_papers.py --paper 7
python build_papers.py --paper connections
python tools/note_vi_cluster_artifacts.py --pdf
python build_papers.py --paper Probability_Valued_Subset_Sum
python tools/check_links.py
python -m unittest discover -s Structural_Distance_Subset_Sum -p "test_*.py" -v
```

The builder accepts a note number or filename stem. By default it builds the seven numbered PDFs, both companions and the OpenAI connections note, and updates their generated HTML; Note I's maintained HTML is preserved. Use `--paper connections` to build the four-page connections note alone. Building Note VI includes its clustering companion, and building Note VII includes its runtime companion. Notes V and VII and the runtime companion retain visible working-draft labels. Use `--html-only` to refresh generated HTML without rebuilding PDFs, or `--pdf-only` for PDFs alone. Builds also synchronize the historical root PDF/TeX downloads from canonical sources. Generated Note III, V, VI and VII evidence artifacts come from preserved measurements with integrity checks. Note VI includes the original frozen study and the separate branch-pruning follow-up. No experiments or model fitting are rerun by these paper builds.

See [Note V's findings](Structural_Distance_Subset_Sum/FINDINGS.md), [its full study report](Structural_Distance_Subset_Sum/results/prospective_20261024/REPORT.md), and [Note III's methods ledger](subset-sum/PROBABILITY_REFINEMENT.md) for the guarantees, results, and their limits.

## Website compatibility

GitHub's default branch and GitHub Pages both use **`master`**. Pages serves its repository root, so a push to `master` publishes the committed site after GitHub's build completes. There is no separate publication branch. The former `main` release commits are retained in `master`'s merged history; all current research and site files live together.

To review a copy of the committed site before pushing, choose a new output directory:

```powershell
python tools/prepare_site.py --output .build/site-review-20261028
python tools/check_links.py --site .build/site-review-20261028
```

The review copy contains all seven canonical note folders, both companions, supporting evidence packages, Markdown guides, figures and TeX inputs. Historical root HTML, PDF and LaTeX URLs remain available; companions use canonical URLs inside their note folders. Working-draft labels are preserved. This optional staging step checks the site; publishing uses a normal push to `master`.

These notes establish model criteria and results on specified synthetic families. They do not claim a new general worst-case subset-sum bound.
