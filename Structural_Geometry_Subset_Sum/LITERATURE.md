# Literature map: tractable routes, solver obstructions and guarantees

Initial scoped audit: October 28, 2026. This is a research direction and exact
experiment package, not an exhaustive taxonomy or novelty claim.

| Structure / regime | Guarantee type | Relationship to this package |
|---|---|---|
| Superincreasing, complete coverage, few values, bounded support, compact interval/progression cores | Exact tractable representations under explicit bounds | Existing Paper V/VI implementations; reused as background and easy controls |
| Small target or maximum item size | Pseudopolynomial; polynomial when the relevant numeric parameter is polynomially bounded in input length | Existing bitset fallback partially covers this route |
| Small additive doubling | Polynomial for each fixed doubling constant under the cited formulation | Candidate future structural detector, not implemented here |
| Dense subset-sum parameter regimes | Near-linear algorithms under explicit parameter conditions, with conditional lower bounds outside them | Candidate future route; density alone is not an easy/hard certificate |
| Random low-density instances | Distributional lattice-recovery results with explicit assumptions | A possible solver route; failure to recover a solution is not a NO certificate |
| Large-base decompositions w=M*p+r | Tuned families hard for particular branching rules, easy under aggregate branching/reformulation | First experiment tests bounded blind discovery and exact aggregate checks |
| SAT-encoded families | Conditional worst-case lower bounds under SETH | Complexity context; no per-instance time certificate |

## Primary sources and limits

1. Krishnamoorthy and Pataki, *Column basis reduction, and decomposable knapsack
   problems*, Discrete Optimization 6(3), 242-270 (2009),
   [author manuscript](https://arxiv.org/abs/0807.1317). The constraint vector has
   the form pM+r. For suitably chosen instances the authors prove difficulty
   for ordinary individual-variable branch-and-bound, and easiness under
   aggregate branching or lattice-based reformulation. Our generated families
   are inspired by this decomposition; they are not asserted to satisfy every
   hypothesis of those hardness constructions. Our coordinate DP is an
   elementary exact shortcut, not a new general reformulation theorem.

2. Randolph and Wegrzycki, *Parameterized Algorithms on Integer Sets with Small
   Doubling: Integer Programming, Subset Sum and k-SUM*, ESA 2024,
   [primary paper](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ESA.2024.96).
   The doubling constant |A+A|/|A| is a distinct additive-structure parameter.
   Their polynomial exponent depends on that constant; this is not a universal
   fixed-exponent FPT claim or a ready-made inexpensive practical oracle.

3. Bringmann and Wellnitz, *On Near-Linear-Time Algorithms for Dense Subset Sum*,
   SODA 2021, [full paper](https://arxiv.org/abs/2010.09096). Their dense-regime
   dichotomy depends on n, target, maximum item and total, not just a generic
   density score. The multiset extension has separate conditions. Their term
   "dense" must not be confused with the cryptographic n/log(maximum) convention.

4. Polak, Rohwedder and Wegrzycki, *Knapsack and Subset Sum with Small Items*,
   [primary manuscript](https://arxiv.org/abs/2105.04035). Algorithms exploit
   maximum item size, including succinct multiplicities. These numeric bounds
   do not establish strongly polynomial solving of general binary inputs.

5. Lagarias and Odlyzko, *Solving Low-Density Subset Sum Problems*, JACM 1985,
   [publisher article](https://doi.org/10.1145/2455.2461). Distributional recovery
   and lattice conditions differ from guaranteed exact decision on every input.

6. Abboud, Bringmann, Hermelin and Shabtay, *SETH-Based Lower Bounds for Subset
   Sum and Bicriteria Path*, [primary manuscript](https://arxiv.org/abs/1704.04546).
   Tight reductions yield conditional family-level lower bounds, not labels
   proving that an individual instance must consume a given amount of time.

7. The repository's [Paper V audit](../Structural_Distance_Subset_Sum/LITERATURE.md)
   and [Paper VI audit](../Learned_Solvability_Subset_Sum/LITERATURE.md) document
   tractable-core/backdoor, output-sensitive, performance-prediction and feature-
   cost precedents. This package retains those accounting and claim boundaries.

New measured efficiency, if any, must exceed discovery and verification costs
and be compared with meaningful exact baselines. New features or a visually
separated input cloud alone do not establish faster solving.
