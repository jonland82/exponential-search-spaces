# Certified Coverage of Exponential Search Spaces

Jonathan R. Landers | September-October 2026

[Six-note research sequence](https://jonland82.github.io/exponential-search-spaces/) | [All six note folders](notes/README.md)

The sequence follows one question: when can useful structure account for enough of an exponential search that only manageable work remains? All six notes have HTML/PDF versions. Note V remains clearly labeled as a working draft.

## Notes

| Note | Question | Files |
|---|---|---|
| **I. Certified Coverage of Exponential Search Spaces** (published) | When does certified coverage leave a polynomial residual? | [HTML](notes/01-certified-coverage/Certified_Coverage_of_Exponential_Search_Spaces.html) / [PDF](notes/01-certified-coverage/Certified_Coverage_of_Exponential_Search_Spaces.pdf) / [LaTeX](notes/01-certified-coverage/Certified_Coverage_of_Exponential_Search_Spaces.tex) |
| **II. Subset Sum as a Stress Test for Certified Coverage** (published) | Do exact pairing, pruning, and learned proposals save work? | [HTML](notes/02-subset-sum-stress-test/Subset_Sum_as_a_Stress_Test.html) / [PDF](notes/02-subset-sum-stress-test/Subset_Sum_as_a_Stress_Test.pdf) / [LaTeX](notes/02-subset-sum-stress-test/Subset_Sum_as_a_Stress_Test.tex) |
| **III. Probability-Valued Subset Sum: Certified Bounds and Learned Guidance** (published) | How tightly can we bound random-target reachability? | [HTML](notes/03-probability-valued-subset-sum/Probability_Valued_Subset_Sum.html) / [PDF](notes/03-probability-valued-subset-sum/Probability_Valued_Subset_Sum.pdf) / [LaTeX](notes/03-probability-valued-subset-sum/Probability_Valued_Subset_Sum.tex) |
| **IV. Does Pairing Add Value to Certified Approximation? A Subset-Sum Experiment** (published) | Does pairing add value beyond the same approximation rule? | [HTML](notes/04-certified-approximation/Certified_Approximation_of_Subset_Sum.html) / [PDF](notes/04-certified-approximation/Certified_Approximation_of_Subset_Sum.pdf) / [LaTeX](notes/04-certified-approximation/Certified_Approximation_of_Subset_Sum.tex) |
| **V. How Far from Easy? Structural Distance in Subset Sum** (working draft) | How far can a list depart from an easy structure before residual search grows? | [HTML](notes/05-structural-distance/Structural_Distance_in_Subset_Sum.html) / [PDF](notes/05-structural-distance/Structural_Distance_in_Subset_Sum.pdf) / [LaTeX](notes/05-structural-distance/Structural_Distance_in_Subset_Sum.tex) |
| **VI. Predicting Subset-Sum Completion: The Value and Cost of Structural Features** (published) | Do structural distances improve prediction and certified pruning after their costs are paid? | [HTML](notes/06-learned-solvability/Predicting_Subset_Sum_Completion.html) / [PDF](notes/06-learned-solvability/Predicting_Subset_Sum_Completion.pdf) / [LaTeX](notes/06-learned-solvability/Predicting_Subset_Sum_Completion.tex) |

Read I, then II. Notes III and IV branch into random-target probability and fixed-target approximation. Note V returns to exact search: it proves a concrete tractable regime and measures the cost of trying to improve the discovered structure.

[Note VI](notes/06-learned-solvability/README.md) combines five certified structural features with numerical summaries. Its [experiment package](Learned_Solvability_Subset_Sum/README.md) includes theory, a [prior-work audit](Learned_Solvability_Subset_Sum/LITERATURE.md), calibrated models and [mixed frozen-study findings](Learned_Solvability_Subset_Sum/PROSPECTIVE_FINDINGS.md). The primary probability comparison does not improve; a modest live-time policy gain coexists with an unfavorable work-counter endpoint.

A separate [branch-pruning follow-up](Learned_Solvability_Subset_Sum/BRANCH_FINDINGS.md)
implements Note I's proposal--verification framework using exact easy-core queries.
On 216 fresh cases, a simple distance rule completed 162 within 50 ms each,
compared with 159 for the combined learned gate and 152 for DFS (median totals).
The transferred model has not demonstrated an advantage over the rule.

## Repository layout

- `notes/01-...` through `notes/06-...` contain each note's source, PDF, and local guide. Available HTML papers and Note V's draft downloads are linked from the six-note index.
- `subset-sum/` contains the original experiments and publication artifacts for Notes II-IV.
- `Subset_Sum_Refinement_Experiment/` preserves Note III's statistical and deterministic follow-ups, including frozen evidence and reruns.
- `Structural_Distance_Subset_Sum/` contains Note V's proofs, exact solvers, tests, literature audit, frozen study, and raw measurements.
- `Learned_Solvability_Subset_Sum/` contains Note VI's certified features, theory, scoped literature audit, frozen models, exact evidence and prioritization traces.
- `tools/` contains the note catalog, evidence-to-paper helpers, link checking, and website staging.
- `index.html`, `paper.css`, and `fonts/` are the six-note website. Small root HTML redirects preserve earlier entrypoints.
- `.build/` holds ignored LaTeX byproducts and optional staged website files.

The experiment packages retain their existing locations and frozen source bytes. Their protocols and measured data were not regenerated for the reorganization.

## Build and check

Requires `pdflatex` and `pandoc`. Numerical tests use Python's standard library; plots use Matplotlib.

```powershell
python build_papers.py
python build_papers.py --paper 5
python build_papers.py --paper 6
python build_papers.py --paper Probability_Valued_Subset_Sum
python tools/check_links.py
python -m unittest discover -s Structural_Distance_Subset_Sum -p "test_*.py" -v
```

The builder accepts a note number or filename stem. It builds all six PDFs by default and updates generated HTML for Notes II-VI; Note I's maintained HTML is preserved. Note V retains its visible working-draft label. Use `--html-only` to refresh generated HTML without rebuilding PDFs, or `--pdf-only` for PDFs alone. Generated Note III, V and VI artifacts come from preserved measurements with integrity checks. Paper VI includes both the original frozen study and the separate branch-pruning follow-up. No experiments or model fitting are rerun by a paper build.

See [Note V's findings](Structural_Distance_Subset_Sum/FINDINGS.md), [its full study report](Structural_Distance_Subset_Sum/results/prospective_20261024/REPORT.md), and [Note III's methods ledger](subset-sum/PROBABILITY_REFINEMENT.md) for the guarantees, results, and their limits.

## Website compatibility

GitHub Pages serves the repository root on `main`; research development lives on `master`. Deploy a validated staged site as a new commit on `main`, preserving the existing Pages setting and branch history. The live index includes all six notes and clearly identifies Note V's draft status.

To prepare a deployable copy of the six-note website:

```powershell
python tools/prepare_site.py --output .build/site
python tools/check_links.py --site .build/site
```

The staged payload contains all six canonical note folders, supporting evidence packages, Markdown guides, figures and TeX inputs. It retains the root HTML, PDF and LaTeX URLs for all six papers. Compatibility downloads are generated there instead of cluttering the research repository root. Note V's HTML/PDF versions remain labeled as working drafts. Use a new output directory for another staged copy.

These notes establish model criteria and results on specified synthetic families. They do not claim a new general worst-case subset-sum bound.
