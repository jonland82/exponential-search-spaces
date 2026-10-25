# Note VI: Predicting Subset-Sum Completion

**The Value and Cost of Structural Features.** First review draft, October 25,
2026. Stage 9 is complete as a scoped prior-work audit, manuscript and built PDF.
This is an unpublished PDF/LaTeX draft; the published website remains four notes.

- [Read the PDF](Predicting_Subset_Sum_Completion.pdf).
- [LaTeX source](Predicting_Subset_Sum_Completion.tex).
- [Generated evidence manifest](paper_evidence.json).
- [Scoped literature audit](../../Learned_Solvability_Subset_Sum/LITERATURE.md).
- [Frozen findings](../../Learned_Solvability_Subset_Sum/PROSPECTIVE_FINDINGS.md).

Build with `python build_papers.py --paper 6`. The builder verifies frozen
source/model/data hashes and generates measured values, tables and the plot.
It performs no training, experiment reruns, HTML generation or publication.

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

Note V proves a sufficient regime using one structural distance. Note VI proposes
a learned combination of several such distances, retaining exact solvers for all
answers. Unlike the earlier learned reachability classifier in Notes II-III, the
labels concern solver completion. Feature and inference costs must be paid, and
simple conventional predictors must be competitive baselines.

## Execution and manuscript plan

1. Define the budgeted outcome and distinguish it from asymptotic tractability.
2. Implement all five distances with certified cores and bounded discovery cost.
3. Prove exact core-query costs and sufficient polynomial residual-search regimes.
4. Pilot feature feasibility, costs, label variation and redundancy. Complete.
5. Implement target-aware and progression-aware variants; build development data. Complete.
6. Fit and calibrate simple models; compare conventional features and ablations. Complete as development work.
7. Freeze new test inputs; hold out lists, families, sizes and bit lengths. Complete.
8. Compare budgeted prioritization with simpler policies using total costs. Complete.
9. Audit prior literature and write the paper around results that survive these checks. **Current checkpoint: first review draft complete.**

The manuscript covers problem definition, certified feature construction,
elementary guarantees, experimental protocol, calibrated prediction, shifts,
paid practical utility and limitations. Its primary prediction comparison is
unfavorable. Some live-time benefit coexists with a work-counter failure.

## Current evidence and discussion

The [experiment package](../../Learned_Solvability_Subset_Sum/README.md) contains
code, tests, [theory](../../Learned_Solvability_Subset_Sum/THEORY.md),
[findings](../../Learned_Solvability_Subset_Sum/FINDINGS.md), and
[the pilot report](../../Learned_Solvability_Subset_Sum/results/pilot_20261025/REPORT.md).

The first pilot has 162 lists, 486 targets and 1,944 portfolio runs. The accepted
development extension adds 324 lists, 1,296 targets and 6,480 exact-policy runs,
target-aware kernels and an arithmetic-progression representation for feature 5.
Every completed decision in both datasets agrees with an independent oracle.

[Stage 6 findings](../../Learned_Solvability_Subset_Sum/DEVELOPMENT_FINDINGS.md)
show improvement from target awareness on the ordinary disjoint-list test, but
no general five-feature advantage over conventional features. Hybrids show useful
development results, while feature costs still reduce many tight-budget completions.
The
[extended theory](../../Learned_Solvability_Subset_Sum/ADVANCED_THEORY.md) and
[model reports](../../Learned_Solvability_Subset_Sum/results/development_20261025/ml/REPORT.md)
retain definitions, guarantees, calibrated scores and evidence limits.

The [fresh frozen study](../../Learned_Solvability_Subset_Sum/PROSPECTIVE_FINDINGS.md)
adds 144 base lists / 288 paired encodings / 1,152 cases and 672 practical pool
runs. Combined logistic guidance gives a modest live-time completion benefit on
these pools, but the primary probability comparison does not improve and the
work-counter endpoint is unfavorable. The manuscript should preserve these mixed
results and distinguish prediction, structural certificates and resource accounting.
The [protocol](../../Learned_Solvability_Subset_Sum/PROSPECTIVE_PROTOCOL.md) and
[overview figure](../../Learned_Solvability_Subset_Sum/results/prospective_20261025/figures/overview.pdf)
make the experiment reviewable alongside the manuscript.

The manuscript is in the six-paper build catalog. Its draft and experiment
package remain outside the published four-note website and staged site payload.
