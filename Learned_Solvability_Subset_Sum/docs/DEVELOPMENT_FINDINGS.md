# Paper VI: stage 6 development checkpoint

Historical development checkpoint. Later evidence is in
[the original frozen findings](PROSPECTIVE_FINDINGS.md) and the independent
[branch-pruning follow-up](BRANCH_FINDINGS.md). Both are now included in
[Paper VI](../../notes/06-learned-solvability/Predicting_Subset_Sum_Completion.html).

October 25, 2026. The accepted target-aware and progression-aware comparison is
implemented and fitted. Pause for discussion before freezing the final study.

## Completed

- Kept the original extractor and its first pilot unchanged for replay.
- Added a progression-aware fifth coordinate with a polynomial membership and
  indexed witness routine; the first four coordinates remain unchanged.
- Added exact target reductions and compared four five-input vectors: original,
  progression-aware, target-aware original, and target-aware progression.
- Generated 324 new weight lists, 1,296 targets and 6,480 exact-policy runs.
  All 4,142 completed decisions match independent half-enumeration labels; 2,338
  policy runs are unresolved. All returned indexed witnesses were validated.
- Fit logistic and forest models, with separate calibration and test lists,
  plus constant, conventional-feature, hybrid and coordinate-ablation comparisons.
- Separately fit end-to-end completion probabilities including feature cost and
  certified-core reuse, comparing predictors within each fixed pipeline's task.

Data, code snapshots, hashes and timings are in
[the development results](../results/development_20261025/summary.json).
The [common-label report](../results/development_20261025/ml/REPORT.md) and
[end-to-end report](../results/development_20261025/end_to_end/REPORT.md)
retain all fitted comparisons and probabilities. The
[theory extension](ADVANCED_THEORY.md) gives the definitions and elementary proofs.

## What changed in the features

On this dataset, the list-based coverage/fifth correlation fell from 0.988 to
0.886 after adding progression cores. The stronger fifth coordinate reduced
deletions on 67 of 324 lists (268 of their target observations). The target-aware
progression vector differed from the original vector on 908 of 1,296 targets.
This confirms that the extensions create different information; it does not
establish predictive advantage.

## Predictive information under a common label

Every model in this comparison predicts the same event: the shared exact
portfolio completes within 8L, excluding feature extraction. Calibrated forest
Brier scores (lower is better) are:

| Predictor | Disjoint-list test | Larger size | Unseen families |
|---|---:|---:|---:|
| Original five | 0.0540 | 0.0898 | 0.2605 |
| Progression five | 0.0540 | 0.0911 | 0.2515 |
| Target-aware original five | 0.0403 | 0.0763 | 0.2872 |
| Target-aware progression five | 0.0353 | 0.0814 | 0.2915 |
| Ten conventional features | 0.0231 | 0.0452 | 0.2392 |
| Fifteen-input hybrid | 0.0199 | 0.0453 | 0.1961 |

Target-aware progression improves on the original vector on the disjoint-list
test. Its paired Brier difference is -0.0188, with a conditional list-bootstrap
95% interval [-0.0352,-0.0064]. Its larger-size interval includes zero. On unseen
families it is worse descriptively; the difference from original is +0.0310,
with interval [-0.0115,+0.0784]. These intervals hold the fitted models fixed.

Conventional features beat the five-only forests in each of these three
evaluations. The hybrid's advantage over conventional features is concentrated
in unseen families: difference -0.0431, conditional interval [-0.0794,-0.0096].
Logistic models give a different ranking on shifted data: the target-aware
progression model scores 0.1849 on unseen families, and the hybrid scores 0.1114.
Thus performance is sensitive to model choice; these forest numbers are a
matched-model comparison, not a claim to have selected the best model family.

Five-coordinate ablations show no uniformly indispensable coordinate in this
development sample. For example, dropping few-values improves the target-aware
forest on larger inputs and unseen families. Keep ablations in the final study.

## End-to-end labels: the actual feature-cost question

For the target-aware progression cost/reuse pipeline, all models below predict
that same pipeline's completion, including feature extraction:

| Predictor | Disjoint-list test | Larger size | Unseen families |
|---|---:|---:|---:|
| Constant prior | 0.2137 | 0.2681 | 0.3127 |
| Target-aware progression five, forest | 0.0671 | 0.1417 | 0.3231 |
| Conventional features, forest | 0.0832 | 0.1124 | 0.2196 |
| Hybrid, forest | 0.0492 | 0.0988 | 0.1320 |

The five-only forest beats conventional features on the disjoint-list test
for this task, but does worse on larger sizes and unseen families. On unseen
families its Brier score is even worse than the constant training prior.
This is a concrete generalization failure of that model, not a proof that
all five-feature predictors fail.

## Extraction and solving remain different objectives

The common exact pipeline completes 1,035 of 1,296 cases. With all feature costs
and full-core reuse charged, the original policy completes 778, progression 752,
target-original 802, and target-progression 775. These are exact policies with no
learned scheduling. The progression policies each gain 15 completions the common
pipeline misses, but lose substantially more under this tight counter budget.

Some simple small-bit-length inputs spend their entire 8L allowance extracting
features. These counts depend on the declared nonuniform operation counters;
they are not measurements of mathematical instance hardness. Single-run elapsed
times are retained but cannot substantiate a robust wall-clock speedup claim.
Feature inference and a learned budget-prioritization policy remain untested.

## Evidence boundaries and next decision

Training uses 84 lists (336 targets), calibration 42 (168), and the ordinary test
42 (168). Larger-size evaluation has 84 n=36 lists (336 targets). Unseen-family
evaluation has 72 lists (288 targets), and includes n=36 as well; the common-label
metrics retain a smaller-size subgroup to isolate family shift. The two withheld
families are near-equal and filtered-modular. These are selected synthetic
development distributions, not a representative distribution of all subset sum.

Recommendation: keep the five-distance model as the primary structural hypothesis,
but freeze conventional and hybrid models as serious comparison arms. The next
study should test whether distances add value beyond ordinary features, not assume
that five distances suffice. Before that freeze, make the primary work/memory
budget and a separately measured wall-clock budget explicit, add independent
bit-length and family shifts, and decide how to avoid paying for expensive
features on instances already solved by cheap exact methods.

Stages 5-6 are complete as development work. Stage 7 (fresh frozen evaluation),
stage 8 (learned practical prioritization) and stage 9 (literature audit and full
Paper VI manuscript) remain. The existing note is still a prospectus.
