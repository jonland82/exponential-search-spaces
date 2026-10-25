# The six notes

The website indexes all six notes. Notes I-IV and VI have HTML and PDF versions;
Note V remains a clearly labeled PDF/source working draft.

- **I. [Certified Coverage of Exponential Search Spaces](01-certified-coverage/README.md)** - published note.
- **II. [Subset Sum as a Stress Test for Certified Coverage](02-subset-sum-stress-test/README.md)** - published note.
- **III. [Probability-Valued Subset Sum: Certified Bounds and Learned Guidance](03-probability-valued-subset-sum/README.md)** - published note.
- **IV. [Does Pairing Add Value to Certified Approximation? A Subset-Sum Experiment](04-certified-approximation/README.md)** - published note.
- **V. [How Far from Easy? Structural Distance in Subset Sum](05-structural-distance/README.md)** - working draft; PDF/LaTeX only.
- **VI. [Predicting Subset-Sum Completion: The Value and Cost of Structural Features](06-learned-solvability/README.md)** - HTML/PDF paper, including the certified branch-pruning follow-up.

Each folder owns its source and PDF. Shared methods and frozen raw evidence stay in the experiment packages, rather than being duplicated into the note folders.

The Note VI build verifies both experiments' model/source/data hashes before generating tables, values and the figure. The paper retains the primary unfavorable result, modest live-pool gain, work-counter failure and scoped prior-work audit. Its new pruning section finds 159/216 live completions for combined ML guidance, 152 for DFS and 162 for a simple distance rule; the transferred model adds no demonstrated advantage over that rule.
