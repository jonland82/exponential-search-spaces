# Note VI: Predicting Subset-Sum Completion

**The Value and Cost of Structural Features.** Updated HTML/PDF note, October 25,
2026. The manuscript includes the original frozen study and Stage 10's independent
certified branch-pruning experiment. Both are preserved and reported separately.

- [Read HTML](Predicting_Subset_Sum_Completion.html).
- [Read the PDF](Predicting_Subset_Sum_Completion.pdf).
- [LaTeX source](Predicting_Subset_Sum_Completion.tex).
- [Generated evidence manifest](paper_evidence.json).
- [Scoped literature audit](../../Learned_Solvability_Subset_Sum/docs/LITERATURE.md).
- [Frozen findings](../../Learned_Solvability_Subset_Sum/docs/PROSPECTIVE_FINDINGS.md).
- [Branch-pruning findings](../../Learned_Solvability_Subset_Sum/docs/BRANCH_FINDINGS.md).

Build the main paper with `python build_papers.py --paper 6`. The builder verifies
frozen source/model/data hashes and generates measured values, tables and the
plot. It regenerates PDF/HTML and performs no training or experiment reruns.

## Companion note: why unresolved inputs cluster

[Three-page PDF](Why_Unresolved_Inputs_Cluster.pdf) | [LaTeX source](Why_Unresolved_Inputs_Cluster.tex) |
[3D figure](cluster_geometry.png) | [Descriptive evidence](cluster_evidence.json).

October 26, 2026. A focused account of the structural residual-search bound,
the union of affordable core-solving routes, and the probability identity behind
hard-neighbor enrichment. It distinguishes unresolved portfolio runs from
intrinsic hardness and separates an ideal local-pair explanation from the exact
finite-neighbor graph calculation. The figure reuses the frozen PCA coordinates;
the full-space neighborhood rate is 586/730, or 80.27%, against 25.35% unresolved
overall. This is descriptive reuse of the original sample, not a new experiment.

Rebuild with `python tools/note_vi_cluster_artifacts.py --pdf`. The script checks
saved evidence hashes and identities, regenerates the figure and numerical
macros, and compiles the PDF. It does not rerun solvers, fit models or refit PCA.

## Latest result

At 50 ms per case on 216 fresh inputs, median completions are 152 for DFS,
159 for combined ML guidance and 162 for a simple distance rule. Exact checks
certify internal subtrees as impossible, but the transferred completion model
adds no demonstrated benefit over the rule. Matched acquisition controls,
component costs and uncertainty are included in the new manuscript section.

The original primary probability comparison remains unfavorable: combined
Brier score 0.0266 versus ordinary features' 0.0211. The original live-pool
gain and work-counter failure are retained, with their attribution limits.

## Research question

Can five certified distances to easy subset-sum structures predict exact completion
under a declared computational budget, including on other input families? Can
the predictions improve how a fixed total solving budget is spent?

For x=(w,t), define phi(x)=(d_SI,d_cover,d_values,d_support,d_repr). The first
implementation uses three minimum deletion distances and two certified constructive
upper bounds on a target-dependent exact residual kernel. It estimates

    P_{X~D}(the fixed exact pipeline finishes within B(L_X) | phi(X)=phi(x)),

with fixed input distribution D, exact portfolio A, execution schedule, resource
caps and budget rule B. Common labels exclude acquisition for a matched
predictive-information comparison; the separate practical pool experiment pays
all feature, inference and witness costs. This probability concerns exact
completion, not whether the target is reachable. Finite-size completion does not
prove polynomial asymptotic solvability.

## Connection to the sequence

Note V proves a sufficient regime using one structural distance. Note VI tests
a learned combination of several such distances, retaining exact solvers for all
answers. Unlike the earlier learned reachability classifier in Notes II-III, the
labels concern solver completion. Feature and inference costs must be paid, and
simple conventional predictors must be competitive baselines. The branch
follow-up directly implements Note I: predictions suggest checks, exact
certificates resolve subtrees, and ordinary search handles the remainder.

## Execution and manuscript plan

1. Define the budgeted outcome and distinguish it from asymptotic tractability.
2. Implement all five distances with certified cores and bounded discovery cost.
3. Prove exact core-query costs and sufficient polynomial residual-search regimes.
4. Pilot feature feasibility, costs, label variation and redundancy. Complete.
5. Implement target-aware and progression-aware variants; build development data. Complete.
6. Fit and calibrate simple models; compare conventional features and ablations. Complete as development work.
7. Freeze new test inputs; hold out lists, families, sizes and bit lengths. Complete.
8. Compare budgeted prioritization with simpler policies using total costs. Complete.
9. Audit prior literature and write the paper around results that survive these checks. Complete.
10. Transfer frozen scores to certified branch checks with native and matched-acquisition controls. Complete.
11. Incorporate those results, refresh the six-note index/docs and publish HTML/PDF. Current publication update.

The manuscript covers problem definition, certified feature construction,
elementary guarantees, experimental protocol, calibrated prediction, shifts,
paid practical utility, certified branch checks and limitations. Its primary prediction comparison is
unfavorable. Some live-time benefit coexists with a work-counter failure.

## Current evidence and discussion

The [experiment package](../../Learned_Solvability_Subset_Sum/README.md) contains
code, tests, [theory](../../Learned_Solvability_Subset_Sum/docs/THEORY.md),
[findings](../../Learned_Solvability_Subset_Sum/docs/FINDINGS.md), and
[the pilot report](../../Learned_Solvability_Subset_Sum/results/pilot_20261025/REPORT.md).

The first pilot has 162 lists, 486 targets and 1,944 portfolio runs. The accepted
development extension adds 324 lists, 1,296 targets and 6,480 exact-policy runs,
target-aware kernels and an arithmetic-progression representation for feature 5.
Every completed decision in both datasets agrees with an independent oracle.

[Stage 6 findings](../../Learned_Solvability_Subset_Sum/docs/DEVELOPMENT_FINDINGS.md)
show improvement from target awareness on the ordinary disjoint-list test, but
no general five-feature advantage over conventional features. Hybrids show useful
development results, while feature costs still reduce many tight-budget completions.
The
[extended theory](../../Learned_Solvability_Subset_Sum/docs/ADVANCED_THEORY.md) and
[model reports](../../Learned_Solvability_Subset_Sum/results/development_20261025/ml/REPORT.md)
retain definitions, guarantees, calibrated scores and evidence limits.

The [fresh frozen study](../../Learned_Solvability_Subset_Sum/docs/PROSPECTIVE_FINDINGS.md)
adds 144 base lists / 288 paired encodings / 1,152 cases and 672 practical pool
runs. Combined logistic guidance gives a modest live-time completion benefit on
these pools, but the primary probability comparison does not improve and the
work-counter endpoint is unfavorable. The manuscript should preserve these mixed
results and distinguish prediction, structural certificates and resource accounting.
The [protocol](../../Learned_Solvability_Subset_Sum/docs/PROSPECTIVE_PROTOCOL.md) and
[overview figure](../../Learned_Solvability_Subset_Sum/results/prospective_20261025/figures/overview.pdf)
make the experiment reviewable alongside the manuscript.

The manuscript and experiment package are included in the six-note website.
Next research controls are root-only structural checks and branch-specific
prediction of net time saved, with independent training and test trees.

[All notes](../README.md) | [Repository guide](../../README.md)
