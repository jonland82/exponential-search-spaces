# Research library: fourteen PDF papers

The library contains **seven numbered notes and seven companions or standalone papers**. Note numbers record development order. The reading path below follows the argument: account for a shortcut, test it, find exact structure, predict completion, explain the landscape, and make expensive regions identifiable. The [home page](../index.html) follows the same arc.

All fourteen papers have PDFs. Links below distinguish available HTML/LaTeX sources from the PDF-only conservation manuscript. Notes V and VII, the geometric runtime companion, the block-overlap paper, and the difficulty-buckets note are working drafts. Repository availability does not imply external peer review.

## Account for the shortcut

Start by charging the cost of discovering and using structure, alongside residual search. Lower-bound statements require their own computational assumptions.

- **[Certified Coverage of Exponential Search Spaces — PDF](01-certified-coverage/Certified_Coverage_of_Exponential_Search_Spaces.pdf)** (Note I): a costed framework for collective representation and certified exclusion. [HTML](01-certified-coverage/Certified_Coverage_of_Exponential_Search_Spaces.html), [LaTeX](01-certified-coverage/Certified_Coverage_of_Exponential_Search_Spaces.tex), [guide](01-certified-coverage/README.md).
- **[A Conservation Law for Search Work — PDF](conservation-of-computational-work/conservation_of_search_work.pdf)**: discovery/search tradeoffs, model-specific and SETH-conditional lower bounds, and pruning break-even costs. [Guide](conservation-of-computational-work/README.md). Four pages; LaTeX source is not included in this checkout.

## Test whether grouping pays

The experiments separate fewer represented candidates from lower total computation, retaining their negative results.

- **[Subset Sum as a Stress Test for Certified Coverage — PDF](02-subset-sum-stress-test/Subset_Sum_as_a_Stress_Test.pdf)** (Note II): pairing, sound pruning, and learned proposals in exact search. [HTML](02-subset-sum-stress-test/Subset_Sum_as_a_Stress_Test.html), [LaTeX](02-subset-sum-stress-test/Subset_Sum_as_a_Stress_Test.tex), [guide](02-subset-sum-stress-test/README.md).
- **[Does Pairing Add Value to Certified Approximation? A Subset-Sum Experiment — PDF](04-certified-approximation/Certified_Approximation_of_Subset_Sum.pdf)** (Note IV): controlled comparisons under a common accuracy rule find no consistent extra timing benefit from pairing. [HTML](04-certified-approximation/Certified_Approximation_of_Subset_Sum.html), [LaTeX](04-certified-approximation/Certified_Approximation_of_Subset_Sum.tex), [guide](04-certified-approximation/README.md).

## Find exact structure

Easy cores, distinct sums, and reusable tables can replace repeated individual work. Their construction and query costs determine when this is worthwhile.

- **[How Far from Easy? Structural Distance in Subset Sum — PDF](05-structural-distance/Structural_Distance_in_Subset_Sum.pdf)** (Note V; working draft): maximum superincreasing cores, exceptional items, distinct residual sums, and the cost of selecting a core. [HTML](05-structural-distance/Structural_Distance_in_Subset_Sum.html), [LaTeX](05-structural-distance/Structural_Distance_in_Subset_Sum.tex), [guide](05-structural-distance/README.md).
- **[Certified Block Overlap in Subset Sum — PDF](01-certified-coverage/block-overlap/Certified_Block_Overlap_in_Subset_Sum.pdf)** (standalone working draft): exact interval pruning, an optimal contiguous-partition dynamic program, paid bit-cost and space bounds, robust separated families, finite verification, and two reproducible plots. [LaTeX](01-certified-coverage/block-overlap/Certified_Block_Overlap_in_Subset_Sum.tex), [proofs, code and build guide](01-certified-coverage/block-overlap/README.md).
- **[Geometric Cores and Exceptions in Subset Sum — PDF](07-geometric-cores/Geometric_Cores_and_Exceptions_in_Subset_Sum.pdf)** (Note VII; working draft): one quotient–remainder core table reused across exceptional assignments, with fresh paid-completion studies. [HTML](07-geometric-cores/Geometric_Cores_and_Exceptions_in_Subset_Sum.html), [LaTeX](07-geometric-cores/Geometric_Cores_and_Exceptions_in_Subset_Sum.tex), [guide](07-geometric-cores/README.md).
- **[The Runtime of Geometric Core Subset Sum — PDF](07-geometric-cores/Runtime_of_Geometric_Core_Subset_Sum.pdf)** (companion to VII; working draft): construction, query and memory bounds; sufficient structured regimes; comparisons with general algorithms. [HTML](07-geometric-cores/Runtime_of_Geometric_Core_Subset_Sum.html), [LaTeX](07-geometric-cores/Runtime_of_Geometric_Core_Subset_Sum.tex). Three pages.
- **[From Choices to Sums: Connections to OpenAI's Subset-Sum Algorithms — PDF](../OpenAI_Subset_Sum_Connections/From_Choices_to_Sums.pdf)**: distinct-sum compression, compatible records, modular checksums, and shared geometric tables. [HTML](../OpenAI_Subset_Sum_Connections/From_Choices_to_Sums.html), [LaTeX](../OpenAI_Subset_Sum_Connections/From_Choices_to_Sums.tex), [sources and guide](../OpenAI_Subset_Sum_Connections/README.md). Four pages.

## Predict before solving

Whether a random target is reachable and whether an exact solver finishes within a budget are different probabilistic questions.

- **[Probability-Valued Subset Sum: Certified Bounds and Learned Guidance — PDF](03-probability-valued-subset-sum/Probability_Valued_Subset_Sum.pdf)** (Note III): certified range/collision bounds, learned tightening, and transfer limits under specified target distributions. [HTML](03-probability-valued-subset-sum/Probability_Valued_Subset_Sum.html), [LaTeX](03-probability-valued-subset-sum/Probability_Valued_Subset_Sum.tex), [guide](03-probability-valued-subset-sum/README.md).
- **[Predicting Subset-Sum Completion: The Value and Cost of Structural Features — PDF](06-learned-solvability/Predicting_Subset_Sum_Completion.pdf)** (Note VI): completion prediction, paid prioritization, and certified branch pruning, including feature costs and mixed results. [HTML](06-learned-solvability/Predicting_Subset_Sum_Completion.html), [LaTeX](06-learned-solvability/Predicting_Subset_Sum_Completion.tex), [guide](06-learned-solvability/README.md).

## Explain the landscape

Clustering and runtime bands reflect the input population, the representations available, and the solver policy choosing between them.

- **[Why Unresolved Inputs Cluster: A Structural and Statistical Account — PDF](06-learned-solvability/Why_Unresolved_Inputs_Cluster.pdf)** (companion to VI): structural solving routes and descriptive neighborhood enrichment; unresolved does not establish intrinsic hardness. [HTML](06-learned-solvability/Why_Unresolved_Inputs_Cluster.html), [LaTeX](06-learned-solvability/Why_Unresolved_Inputs_Cluster.tex), [evidence guide](06-learned-solvability/README.md#companion-note-why-unresolved-inputs-cluster). Three pages.
- **[Why Subset-Sum Runtimes Form Several Bands — PDF](../OpenAI_Subset_Sum_Connections/Runtime_Distribution_from_Structural_Routes.pdf)**: route-mixture identities, structural cost scales, and assumptions behind lognormal sketches. [LaTeX](../OpenAI_Subset_Sum_Connections/Runtime_Distribution_from_Structural_Routes.tex), [guide](../OpenAI_Subset_Sum_Connections/README.md). Four pages; no HTML edition is currently supplied.

## Make difficulty identifiable

A chosen distribution supplies a layout. Feature information and independent calibration establish which visible regions reliably contain expensive cases for a fixed solver and budget.

- **[Distribution-Shaped Difficulty Buckets — PDF](01-certified-coverage/distribution-shaping/Distribution_Shaped_Difficulty_Buckets.pdf)** (standalone working draft): chosen-shape transport, simultaneous bucket mass/purity guarantees, sample-size conditions for availability, and an exact solver router. [LaTeX](01-certified-coverage/distribution-shaping/Distribution_Shaped_Difficulty_Buckets.tex), [full theory, algorithm and guide](01-certified-coverage/distribution-shaping/README.md). The verification example uses synthetic known costs; practical subset-sum coverage and speedups remain to be measured.

## Related Markdown draft

- [The Cost of Avoiding Search: A Conditional Coverage Law](01-certified-coverage/certification-cost/README.md): an exploratory draft assuming an unknown positive exponential floor. Its general premise remains unproved. It is distinct from the conservation PDF above.

The conditional-cost draft has no separate PDF. The block-overlap derivation now has its own standalone paper, listed above.

## Evidence and builds

The numbered papers' canonical sources live in their note folders. Shared methods, dated protocols, model files, source snapshots, and measurements remain in the original experiment packages. Existing experiments are preserved; paper builds use their saved evidence.

- `python build_papers.py` builds the seven numbered notes, two companions, and *From Choices to Sums*. Individual targets accept a number or filename stem; `--paper 6` and `--paper 7` include their companions.
- `python notes/01-certified-coverage/block-overlap/build_note.py` checks the preserved source hashes, regenerates exact structural plots and numerical macros, and builds the block-overlap paper with natural pagination and no page limit. It preserves the original solver, checker, and validation record.
- `python notes/01-certified-coverage/distribution-shaping/build_note.py` checks source hashes and reported values, then builds the buckets paper with natural pagination and no forced section page breaks.
- The [connections guide](../OpenAI_Subset_Sum_Connections/README.md) documents the separate runtime-bands LaTeX build. The conservation PDF is preserved as supplied; its source is absent.
- `python tools/render_home.py` regenerates the thematic home page from the complete catalog. `python tools/check_links.py` checks links, all fourteen catalog PDFs, available formats, inventory coverage, and draft status.
- `python tools/prepare_site.py --output .build/site-review-new` stages every note folder, all paper PDFs, source formats, and supporting evidence into a fresh directory. Check it with `python tools/check_links.py --site .build/site-review-new`.

See the [repository guide](../README.md) for current findings and the [contribution rules](../CONTRIBUTING.md) for builds, evidence preservation, and publishing.
