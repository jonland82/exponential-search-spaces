# Certified Coverage of Exponential Search Spaces

Jonathan R. Landers | September-October 2026

[Published four-note sequence](https://jonland82.github.io/exponential-search-spaces/) | [All five note folders](notes/README.md)

The sequence follows one question: when can useful structure account for enough of an exponential search that only manageable work remains? Notes I-IV are published. Note V is a four-page PDF/LaTeX working draft kept out of the website and its navigation.

## Notes

| Note | Question | Files |
|---|---|---|
| **I. Certified Coverage of Exponential Search Spaces** (published) | When does certified coverage leave a polynomial residual? | [HTML](notes/01-certified-coverage/Certified_Coverage_of_Exponential_Search_Spaces.html) / [PDF](notes/01-certified-coverage/Certified_Coverage_of_Exponential_Search_Spaces.pdf) / [LaTeX](notes/01-certified-coverage/Certified_Coverage_of_Exponential_Search_Spaces.tex) |
| **II. Subset Sum as a Stress Test for Certified Coverage** (published) | Do exact pairing, pruning, and learned proposals save work? | [HTML](notes/02-subset-sum-stress-test/Subset_Sum_as_a_Stress_Test.html) / [PDF](notes/02-subset-sum-stress-test/Subset_Sum_as_a_Stress_Test.pdf) / [LaTeX](notes/02-subset-sum-stress-test/Subset_Sum_as_a_Stress_Test.tex) |
| **III. Probability-Valued Subset Sum: Certified Bounds and Learned Guidance** (published) | How tightly can we bound random-target reachability? | [HTML](notes/03-probability-valued-subset-sum/Probability_Valued_Subset_Sum.html) / [PDF](notes/03-probability-valued-subset-sum/Probability_Valued_Subset_Sum.pdf) / [LaTeX](notes/03-probability-valued-subset-sum/Probability_Valued_Subset_Sum.tex) |
| **IV. Does Pairing Add Value to Certified Approximation? A Subset-Sum Experiment** (published) | Does pairing add value beyond the same approximation rule? | [HTML](notes/04-certified-approximation/Certified_Approximation_of_Subset_Sum.html) / [PDF](notes/04-certified-approximation/Certified_Approximation_of_Subset_Sum.pdf) / [LaTeX](notes/04-certified-approximation/Certified_Approximation_of_Subset_Sum.tex) |
| **V. How Far from Easy? Structural Distance in Subset Sum** (draft; PDF/LaTeX only) | How far can a list depart from an easy structure before residual search grows? | [PDF](notes/05-structural-distance/Structural_Distance_in_Subset_Sum.pdf) / [LaTeX](notes/05-structural-distance/Structural_Distance_in_Subset_Sum.tex) |

Read I, then II. Notes III and IV branch into random-target probability and fixed-target approximation. Note V returns to exact search: it proves a concrete tractable regime and measures the cost of trying to improve the discovered structure.

## Repository layout

- `notes/01-...` through `notes/05-...` contain each note's source, PDF, and local guide. Published notes also have HTML. The Note V planning document lives with that draft.
- `subset-sum/` contains the original experiments and publication artifacts for Notes II-IV.
- `Subset_Sum_Refinement_Experiment/` preserves Note III's statistical and deterministic follow-ups, including frozen evidence and reruns.
- `Structural_Distance_Subset_Sum/` contains Note V's proofs, exact solvers, tests, literature audit, frozen study, and raw measurements.
- `tools/` contains the note catalog, evidence-to-paper helpers, link checking, and website staging.
- `index.html`, `paper.css`, and `fonts/` are the four-note website. Four small legacy HTML redirects preserve its earlier entrypoints.
- `.build/` holds ignored LaTeX byproducts and optional staged website files.

The experiment packages retain their existing locations and frozen source bytes. Their protocols and measured data were not regenerated for the reorganization.

## Build and check

Requires `pdflatex` and `pandoc`. Numerical tests use Python's standard library; plots use Matplotlib.

```powershell
python build_papers.py
python build_papers.py --paper 5
python build_papers.py --paper Probability_Valued_Subset_Sum
python tools/check_links.py
python -m unittest discover -s Structural_Distance_Subset_Sum -p "test_*.py" -v
```

The builder accepts a note number or the existing filename stem. It builds all five PDFs by default, maintains the four published HTML pages, and never generates Note V HTML. Generated Note III and V tables are read from preserved measurements, with source and data integrity checks. No experiments are rerun by a paper build.

See [Note V's findings](Structural_Distance_Subset_Sum/FINDINGS.md), [its full study report](Structural_Distance_Subset_Sum/results/prospective_20261024/REPORT.md), and [Note III's methods ledger](subset-sum/PROBABILITY_REFINEMENT.md) for the guarantees, results, and their limits.

## Website compatibility

The currently published website uses `main`; development is pushed to `master`. This organization does not change the Pages setting or deploy the draft.

To prepare a deployable copy of the four-note website:

```powershell
python tools/prepare_site.py --output .build/site
python tools/check_links.py --site .build/site
```

The staged payload contains canonical note folders plus the old root HTML, PDF, and LaTeX URLs. Compatibility downloads are generated there instead of cluttering the repository root. Note V and its experiment package are excluded from that payload. Use a new output directory for another staged copy.

These notes establish model criteria and results on specified synthetic families. They do not claim a new general worst-case subset-sum bound.
