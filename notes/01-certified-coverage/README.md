# Note I: Certified Coverage of Exponential Search Spaces

Published note.

[HTML](Certified_Coverage_of_Exponential_Search_Spaces.html) | [PDF](Certified_Coverage_of_Exponential_Search_Spaces.pdf) | [LaTeX source](Certified_Coverage_of_Exponential_Search_Spaces.tex)

From the repository root, rebuild with `python build_papers.py --paper 1`. LaTeX byproducts go under `.build/latex/`.

Exploratory follow-up: [The Cost of Avoiding Search: A Conditional Coverage Law](certification-cost/README.md), a Markdown research draft on global certification costs and conditional exponential lower bounds.

Two additional standalone working drafts develop [exact block-overlap pruning](block-overlap/README.md) and [distribution-shaped difficulty buckets](distribution-shaping/README.md). The latter proves chosen-shape transport and simultaneous statistical bucket guarantees, and includes a learned representation plus an exact subset-sum router.

The six-page block-overlap paper has a standalone [PDF](block-overlap/Certified_Block_Overlap_in_Subset_Sum.pdf) and [LaTeX source](block-overlap/Certified_Block_Overlap_in_Subset_Sum.tex), with full proofs, verification, and two reproducible plots. Its bound includes both discovering the optimal permitted partition and exact search; the original Markdown derivation and code remain available.

The distribution-shaped construction also has a standalone [PDF](distribution-shaping/Distribution_Shaped_Difficulty_Buckets.pdf) and [LaTeX source](distribution-shaping/Distribution_Shaped_Difficulty_Buckets.tex), including full proofs and saved synthetic verification results. The PDF uses natural pagination.

The separate [A Conservation Law for Search Work](../conservation-of-computational-work/README.md) PDF develops discovery/search tradeoffs under explicit model-specific or conditional lower bounds. In the [thematic reading path](../README.md), it accompanies this framework before the empirical tests and exact structural routes.

[All notes](../README.md) | [Repository guide](../../README.md)
