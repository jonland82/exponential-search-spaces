# Seven notes and two companions

All seven notes have repository HTML and PDF versions.
Notes V and VII are clearly labeled as working drafts.
Two unnumbered companions live in the corresponding note folders.

- **I. [Certified Coverage of Exponential Search Spaces](01-certified-coverage/README.md)** - published note.
- **II. [Subset Sum as a Stress Test for Certified Coverage](02-subset-sum-stress-test/README.md)** - published note.
- **III. [Probability-Valued Subset Sum: Certified Bounds and Learned Guidance](03-probability-valued-subset-sum/README.md)** - published note.
- **IV. [Does Pairing Add Value to Certified Approximation? A Subset-Sum Experiment](04-certified-approximation/README.md)** - published note.
- **V. [How Far from Easy? Structural Distance in Subset Sum](05-structural-distance/README.md)** - working draft; HTML/PDF with LaTeX source.
- **VI. [Predicting Subset-Sum Completion: The Value and Cost of Structural Features](06-learned-solvability/README.md)** - HTML/PDF paper, including the certified branch-pruning follow-up.
- **VII. [Geometric Cores and Exceptions in Subset Sum](07-geometric-cores/README.md)** - working draft; exact reuse, fresh paid completion gains and bounds-first ablation.

## Short companions

- **[Why Unresolved Inputs Cluster: A Structural and Statistical Account](06-learned-solvability/Why_Unresolved_Inputs_Cluster.html)** (Note VI, three pages): sufficient structural routes and descriptive neighborhood enrichment. [PDF](06-learned-solvability/Why_Unresolved_Inputs_Cluster.pdf), [source](06-learned-solvability/Why_Unresolved_Inputs_Cluster.tex) and [reproduction guide](06-learned-solvability/README.md#companion-note-why-unresolved-inputs-cluster). Built with `python build_papers.py --paper 6`.
- **[The Runtime of Geometric Core Subset Sum](07-geometric-cores/Runtime_of_Geometric_Core_Subset_Sum.html)** (Note VII, three-page working draft): table/query costs, polynomial structured regimes and comparisons with general algorithms. [PDF](07-geometric-cores/Runtime_of_Geometric_Core_Subset_Sum.pdf) and [source](07-geometric-cores/Runtime_of_Geometric_Core_Subset_Sum.tex). Built with `python build_papers.py --paper 7`.

## Evidence and builds

Each folder owns its source and PDF. Shared methods and frozen raw evidence stay in the experiment packages, rather than being duplicated into the note folders.

The Note VI build verifies both experiments' model/source/data hashes before generating tables, values and the figure. The paper retains the primary unfavorable result, modest live-pool gain, work-counter failure and scoped prior-work audit. Its new pruning section finds 159/216 live completions for combined ML guidance, 152 for DFS and 162 for a simple distance rule; the transferred model adds no demonstrated advantage over that rule.

Note VII verifies two separate fresh studies. Its original core-reuse comparison gains 16 completions over root geometry on 576 targets. The later bounds-first refinement avoids 90 table builds but establishes no reliable incremental completion or wall-clock advantage. The runtime companion states conditional structural bounds, without a new general worst-case claim. See the [repository guide](../README.md) for dependencies, build commands and the single `master` branch used for research and the site.
