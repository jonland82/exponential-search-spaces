# Literature-inspired geometry in the classifier

October 28, 2026. [Frozen protocol](experiments/02_literature_classifier/PROTOCOL.md),
[saved report](results/02_literature_classifier_20261028/REPORT.md),
[reproduction guide](results/02_literature_classifier_20261028/README.md).

The new features improve probability estimates on this sample and produce some
extra completions under tight live budgets. They do not yet establish a reliable
general efficiency gain. The largest operational improvement comes from an
exact geometric NO certificate, which the matched control also receives.

## What changed

Refit three calibrated logistic models on identical new expanded training data:
the original 15 inputs; 15 plus relative residual width, feasible aggregate count
and projected DP size; and those 18 plus distinct-weight additive doubling.
The three decomposition inputs use log1p transforms. Geometry is discovered
blindly on the reduced kernel with the existing capped candidate search.

There are 90 training, 45 calibration and 135 test lists, each with three
targets: 270/135/405 cases. The mixture includes the twelve earlier families
and three large-base families, at n=24,32,36. All new lists are disjoint after
gcd normalization and sorting; 1,302 prior normalized lists were excluded.
Fitted models were frozen before test generation. This compares features under
matched expanded training, rather than the earlier frozen model's probabilities.

The label is unchanged: completion of the original exact portfolio within 8L
work, excluding acquisition. It is not subset-sum truth, intrinsic hardness,
or whether running a geometric checker will pay off.

## Primary prediction result

250 test cases from 108 lists remain after exact reduction, reuse of all five
existing zero-deletion cores and the aggregate-gap NO check. These known answers
receive no ML credit. Lower Brier is better.

| Model | Brier | Accuracy | Unresolved recall | Brier difference vs 15 | Adjusted 97.5% interval |
|---|---:|---:|---:|---:|---|
| Original 15 inputs | 0.12222 | 84.0% | 97.3% | -- | -- |
| + Three decomposition inputs | 0.10621 | 84.4% | 94.6% | -0.01601 | [-0.03825, +0.00451] |
| + Additive doubling | 0.10111 | 85.6% | 95.2% | -0.02111 | [-0.04341, +0.00065] |

Observed Brier reductions are 13.1% and 17.3%. Both conservative two-comparison
intervals include zero. The ordinary 95% interval for doubling19 excludes zero
[-0.04097,-0.00181], but that does not satisfy the stated adjusted primary test.
Intervals resample lists with targets together, condition on fitted models and
exclude refitting uncertainty. The fixed 0.5 threshold also trades fewer false
unresolved predictions for more missed unresolved cases.

Across all 405 cases, Brier is 0.09016/0.07990/0.07595. The large-base cohort
shows the larger predictive improvement: 0.12311/0.07364/0.06987, compared with
0.08192/0.08147/0.07747 for the earlier families. These subgroup results are
secondary and do not establish transfer to unseen families.

## Paid operational result

All four policies pay the same original feature acquisition and exact five-core
reuse. cheap15 skips geometry. matched15 acquires geometry and its exact empty
aggregate-range certificate, while predicting with the same 15-input model.
geometry18 and doubling19 receive identical geometric certificates; their
additional completions must therefore come from different ranking under paid
acquisition/inference, not extra correctness shortcuts.

Median completions over three paired orders, including all online computation:

| Endpoint | Cohort | Budget fraction | cheap15 | matched15 | geometry18 | doubling19 |
|---|---|---:|---:|---:|---:|---:|
| Live | Large base | 20% | 6 | 50 | 55 | 55 |
| Live | Earlier families | 20% | 191 | 193 | 197 | 199 |
| Live | Large base | 50% | 9 | 56 | 56 | 56 |
| Live | Earlier families | 50% | 199 | 202 | 202 | 202 |
| Work | Large base | 20% | 0 | 8 | 8 | 8 |
| Work | Earlier families | 20% | 54 | 55 | 55 | 51 |
| Work | Large base | 50% | 0 | 28 | 28 | 26 |
| Work | Earlier families | 50% | 89 | 81 | 81 | 78 |

At 20% live budgets, geometry18 adds five large-base completions and four
earlier-family completions over the matched control; doubling19 adds five and
six. Large-base geometry18 varies 54-55, while matched15 is 50 in all repeats;
earlier-family geometry18 varies 194-197, matched15 192-194, doubling19 199.
At 50%, all three geometry-acquiring policies reach the same completion counts.
The repeats share a dataset; these are descriptive machine-specific results.

There are 56 new exact aggregate-gap answers after the original five cores in
the full test sample. They explain much of the gain over cheap15. Work results
show the costs can outweigh additional predictive information: doubling reduces
completions in several pools, and discovery hurts the larger earlier-family
work pool. Counter units are heterogeneous; this is not a contradiction with
the independently measured live endpoint, nor an asymptotic speedup claim.

## Interpretation and checks

The descriptors appear useful enough for a fresh confirmation study. Retain
the matched geometric-precheck control, test a larger independent sample and
measure generalization and acquisition cost before changing the default model.
This experiment does not train an action-specific geometric-check benefit
predictor; doing that needs new labels and a separately frozen study.

Six new mathematical/accounting tests passed; the structural package now has
18 passing tests. All 50 earlier learned-classifier tests and 16 original
structural-distance tests also pass: 84 total. The saved audit checked all
270 lists / 810 cases, exact truths, descriptor arithmetic, reference labels,
model refits/calibration, hashes, predictions, summaries and paid answers across
96 pools, including all 48 deterministic pool replays. Live late answers were
excluded. [Validation](results/02_literature_classifier_20261028/VALIDATION.json)
passed. Earlier frozen experiments, defaults and manuscripts are preserved.
