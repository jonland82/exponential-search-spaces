# Certified Coverage of Exponential Search Spaces

Jonathan R. Landers | September-November 2026

[Live research site](https://jonland82.github.io/exponential-search-spaces/) | [Reading guide](https://jonland82.github.io/exponential-search-spaces/#arc) | [All 14 papers](notes/README.md) | [Build and preservation rules](CONTRIBUTING.md)

The research follows one question: when does finding structure make search cheaper? It develops representations that handle many candidates together, then asks how to identify expensive work before solving. The library contains **14 distinct PDF papers: seven numbered notes and seven companions or standalone papers**. Note numbers record development order; the reading path below follows the argument. Notes V, VII, the geometric runtime companion, the block-overlap paper, and the difficulty-buckets note retain their working-draft labels.

## Reading the research

1. **Account for the shortcut.** *Certified Coverage* pays for collective representation and residual search. *A Conservation Law for Search Work* makes the assumptions behind discovery/search tradeoffs and lower bounds explicit.
2. **Test whether grouping pays.** The exact-search stress test and approximation experiment separate fewer represented candidates from lower total computation, retaining their negative results.
3. **Find exact structure.** Structural distance separates easy cores from exceptions; block overlap bounds local branching and optimizes the partition; geometric reuse shares a table across queries. The runtime companion charges construction, queries, and memory. *From Choices to Sums* connects these mechanisms to distinct-sum compression and modular representations.
4. **Predict before solving.** Random-target reachability and budgeted solver completion are different questions. The probability-valued and learned-completion notes study their certificates, predictions, and acquisition costs.
5. **Explain the landscape.** The clustering and runtime-bands notes relate observed patterns to available solving routes, rather than treating unresolved cases as intrinsically hard.
6. **Make difficulty identifiable.** *Distribution-Shaped Difficulty Buckets* learns a feature score, chooses its representation's shape, and independently certifies which visible regions are large and expensive for a fixed solver and budget.

The [paper inventory](notes/README.md) links every PDF in this thematic order. The [block-overlap paper](notes/01-certified-coverage/block-overlap/Certified_Block_Overlap_in_Subset_Sum.pdf) develops an exact search bound with paid discovery. A separate [conditional coverage-cost law](notes/01-certified-coverage/certification-cost/README.md) remains a Markdown draft.

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

These numbered notes remain the original sequence. The reading path above connects them with the six additional papers by question, rather than requiring a numerical reading order.

## Short companions

| Companion | Focus | Files |
|---|---|---|
| **Why Unresolved Inputs Cluster: A Structural and Statistical Account** (Note VI; three pages) | Several affordable solving routes and descriptive neighborhood enrichment; unresolved does not mean intrinsically hard. | [HTML](notes/06-learned-solvability/Why_Unresolved_Inputs_Cluster.html) / [PDF](notes/06-learned-solvability/Why_Unresolved_Inputs_Cluster.pdf) / [LaTeX](notes/06-learned-solvability/Why_Unresolved_Inputs_Cluster.tex) / [Evidence and rebuild](notes/06-learned-solvability/README.md#companion-note-why-unresolved-inputs-cluster) |
| **The Runtime of Geometric Core Subset Sum** (Note VII; three-page working draft) | One construction plus exceptional queries, memory costs, sufficient tractable regimes and general-algorithm comparisons. | [HTML](notes/07-geometric-cores/Runtime_of_Geometric_Core_Subset_Sum.html) / [PDF](notes/07-geometric-cores/Runtime_of_Geometric_Core_Subset_Sum.pdf) / [LaTeX](notes/07-geometric-cores/Runtime_of_Geometric_Core_Subset_Sum.tex) |

## Standalone papers

| Paper | Focus | Files |
|---|---|---|
| **Certified Block Overlap in Subset Sum** (working draft) | Local overlap products bound exact search; a dynamic program optimizes contiguous blocks with discovery costs included. Full proofs, verification, and two plots. | [PDF](notes/01-certified-coverage/block-overlap/Certified_Block_Overlap_in_Subset_Sum.pdf) / [LaTeX](notes/01-certified-coverage/block-overlap/Certified_Block_Overlap_in_Subset_Sum.tex) / [Proofs, code and rebuild](notes/01-certified-coverage/block-overlap/README.md) |
| **From Choices to Sums: Connections to OpenAI's Subset-Sum Algorithms** (four pages) | Distinct exceptional sums, compatible representations, modular checksums and reusable geometric tables; derives a combined runtime bound from existing constructions. | [HTML](OpenAI_Subset_Sum_Connections/From_Choices_to_Sums.html) / [PDF](OpenAI_Subset_Sum_Connections/From_Choices_to_Sums.pdf) / [LaTeX](OpenAI_Subset_Sum_Connections/From_Choices_to_Sums.tex) / [Sources and rebuild](OpenAI_Subset_Sum_Connections/README.md) |
| **Why Subset-Sum Runtimes Form Several Bands** (four pages) | Solver-route mixtures, structural cost scales, and the extra assumptions behind lognormal sketches. | [PDF](OpenAI_Subset_Sum_Connections/Runtime_Distribution_from_Structural_Routes.pdf) / [LaTeX](OpenAI_Subset_Sum_Connections/Runtime_Distribution_from_Structural_Routes.tex) / [Guide](OpenAI_Subset_Sum_Connections/README.md) |
| **A Conservation Law for Search Work** (four pages) | Structural/search accounting, model-specific and SETH-conditional lower bounds, and pruning break-even costs. | [PDF](notes/conservation-of-computational-work/conservation_of_search_work.pdf) / [Guide](notes/conservation-of-computational-work/README.md); source not included in this checkout |
| **Distribution-Shaped Difficulty Buckets** (working draft) | Chosen-shape transport, independently certified bucket mass and difficulty, an availability bound, and an exact solver router. | [PDF](notes/01-certified-coverage/distribution-shaping/Distribution_Shaped_Difficulty_Buckets.pdf) / [LaTeX](notes/01-certified-coverage/distribution-shaping/Distribution_Shaped_Difficulty_Buckets.tex) / [Theory, code and rebuild](notes/01-certified-coverage/distribution-shaping/README.md) |

## Latest results

An exploratory Markdown draft, [The Cost of Avoiding Search: A Conditional Coverage Law](notes/01-certified-coverage/certification-cost/README.md), assumes a positive exponential cost floor with an unknown exponent and develops a sufficient coverage-cost mechanism. Local gains and faster exponential algorithms can coexist with that hypothetical floor.

The separate [conservation PDF](notes/conservation-of-computational-work/conservation_of_search_work.pdf) distinguishes accounting identities from proven model-specific and conditional lower bounds. The new [difficulty-buckets note](notes/01-certified-coverage/distribution-shaping/README.md) proves selected-shape transport and simultaneous population mass/purity guarantees for fixed buckets. Its demonstrated coverage uses synthetic known costs; a paid subset-sum performance evaluation remains open. The [block-overlap paper](notes/01-certified-coverage/block-overlap/Certified_Block_Overlap_in_Subset_Sum.pdf) proves an exact search bound with optimal contiguous-partition discovery included; its two reproducible plots distinguish local interval geometry, global support size, and paid structural counters. Its 37,055 finite decision/witness comparisons are correctness evidence, not timing benchmarks.

[Note VII](notes/07-geometric-cores/README.md) supplies an exact geometric solving route: reuse one core table across exceptional assignments. Its first fresh study improves work-capped completions from 453 to 469 of 576 targets over matched root geometry. A second fresh study finds 954 versus root's 916 of 1,152 targets. The final bounds-first refinement mainly saves construction: 90 avoided tables and 1.74% lower capped work; its primary incremental completion comparison is only 953 versus 954, with interval [0,3]. Neither study establishes a new general worst-case bound. The companions explain existing evidence and run no new experiments.

[Note VI](notes/06-learned-solvability/README.md) combines five certified structural features with numerical summaries. Its [experiment package](Learned_Solvability_Subset_Sum/README.md) includes theory, a [prior-work audit](Learned_Solvability_Subset_Sum/docs/LITERATURE.md), calibrated models and [mixed frozen-study findings](Learned_Solvability_Subset_Sum/docs/PROSPECTIVE_FINDINGS.md). The primary probability comparison does not improve; a modest live-time policy gain coexists with an unfavorable work-counter endpoint.

A separate [branch-pruning follow-up](Learned_Solvability_Subset_Sum/docs/BRANCH_FINDINGS.md)
implements Note I's proposal--verification framework using exact easy-core queries.
On 216 fresh cases, a simple distance rule completed 162 within 50 ms each,
compared with 159 for the combined learned gate and 152 for DFS (median totals).
The transferred model has not demonstrated an advantage over the rule.

## Repository layout

- `notes/01-...` through `notes/07-...` contain the numbered notes and their guides. The clustering and geometric runtime companions live beside Notes VI and VII. Note I also contains the block-overlap and distribution-shaping follow-ups.
- `notes/conservation-of-computational-work/` contains the PDF-only conservation manuscript and its guide.
- `OpenAI_Subset_Sum_Connections/` contains *From Choices to Sums* and the separate runtime-bands note, with sources, saved figures, and a rebuild guide.
- `subset-sum/` contains the original experiments and publication artifacts for Notes II-IV.
- `Subset_Sum_Refinement_Experiment/` preserves Note III's statistical and deterministic follow-ups, including frozen evidence and reruns.
- `Structural_Distance_Subset_Sum/` contains Note V's proofs, exact solvers, tests, literature audit, frozen study, and raw measurements.
- `Learned_Solvability_Subset_Sum/` contains Note VI's certified features, theory, scoped literature audit, frozen models, exact evidence and prioritization traces. Shared sources are in `code/`, guides in `docs/`, tests in `tests/`, and geometry/pruning follow-ups in `experiments/`; use the documented launchers to preserve frozen imports and paths.
- `Structural_Geometry_Subset_Sum/` contains a separate literature-guided direction: exact geometric solving routes, classifier features and cost-aware gates. The [reusable exception-core experiment](Structural_Geometry_Subset_Sum/EXCEPTION_FINDINGS.md) improves fresh work-capped completions from 453 to 469 over matched root geometry, with full cost accounting and scoped claims.
- Its [bounds-first follow-up](Structural_Geometry_Subset_Sum/BOUNDS_FINDINGS.md) tests 1,152 fresh targets: 954 versus 953 previous-reuse completions, with 1.74% lower capped work and 90 avoided tables; incremental completion and wall-clock gains remain unestablished.
- `tools/` contains the complete paper catalog, thematic home-page renderer, evidence-to-paper helpers, link checking, and website staging.
- `index.html`, `paper.css`, and `fonts/` are the home site and shared presentation. Each paper entry includes one or two key equations with concise explanations, rendered by MathJax. Regenerate the home page with `python tools/render_home.py` after changing its renderer or catalog. Root HTML redirects and generated PDF/TeX compatibility copies preserve earlier numbered-note URLs; edit canonical sources under `notes/`.
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
python notes/01-certified-coverage/distribution-shaping/build_note.py
python notes/01-certified-coverage/block-overlap/build_note.py
python tools/render_home.py
python tools/note_vi_cluster_artifacts.py --pdf
python build_papers.py --paper Probability_Valued_Subset_Sum
python tools/check_links.py
python -m unittest discover -s Structural_Distance_Subset_Sum -p "test_*.py" -v
```

The builder accepts a note number or filename stem. By default it builds the seven numbered PDFs, both companions and the OpenAI connections note, and updates their generated HTML; Note I's maintained HTML is preserved. Use `--paper connections` to build the four-page connections note alone. Building Note VI includes its clustering companion, and building Note VII includes its runtime companion. Notes V and VII and the runtime companion retain visible working-draft labels. Use `--html-only` to refresh generated HTML without rebuilding PDFs, or `--pdf-only` for PDFs alone. Builds also synchronize the historical root PDF/TeX downloads from canonical sources. Generated Note III, V, VI and VII evidence artifacts come from preserved measurements with integrity checks. Note VI includes the original frozen study and the separate branch-pruning follow-up. No experiments or model fitting are rerun by these paper builds.

The main builder covers ten of the fourteen PDFs. The buckets and block-overlap papers have their own evidence-checking builders shown above, with natural pagination. The buckets paper retains a six-page upper limit; the block-overlap paper has no page limit. The runtime-bands note uses the [separate two-pass LaTeX workflow](OpenAI_Subset_Sum_Connections/README.md). The conservation PDF is preserved as supplied because its LaTeX source is absent. These four standalone papers are nevertheless included in the catalog, home page, and staged site.

See [Note V's findings](Structural_Distance_Subset_Sum/FINDINGS.md), [its full study report](Structural_Distance_Subset_Sum/results/prospective_20261024/REPORT.md), and [Note III's methods ledger](subset-sum/PROBABILITY_REFINEMENT.md) for the guarantees, results, and their limits.

## Site review

To review a copy of the committed site before pushing, choose a new output directory:

```powershell
python tools/prepare_site.py --output .build/site-review-20261029
python tools/check_links.py --site .build/site-review-20261029
```

The review copy contains all fourteen paper PDFs, every note folder including the unnumbered conservation folder, supporting evidence packages, guides, and available sources. Historical root HTML, PDF and LaTeX URLs remain available. Link checks require every catalog paper in both the home page and the Markdown inventory, and verify all declared formats. Working-draft labels are preserved.

These notes establish model criteria and results on specified synthetic families. They do not claim a new general worst-case subset-sum bound.
