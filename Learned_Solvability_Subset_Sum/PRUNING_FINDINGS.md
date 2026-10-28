# Stage 13: training-only top-five / top-ten feature pruning

October 28, 2026. Separate follow-up after the 27-feature geometric experiment.
All earlier sources, datasets, models, interactive plots and manuscripts are
preserved. This experiment tests calibrated whole-input completion prediction
and paid prioritization, not the earlier branch gate or a time-savings label.

## Selection, isolation and fixed models

Recursive feature elimination (RFE) repeatedly refits StandardScaler + logistic
regression (C=1, max_iter=2000, original seed) and drops the smallest absolute
standardized coefficient. Starting from 27 candidates, it saves nested subsets
at 10 and 5 inputs. Exact ties use the original feature index. Selection uses
only the 84 development training lists / 336 targets, with validated
entire-own-list-excluded prototype training features. Forty-two separate
calibration lists fit sigmoid calibration only. Neither calibration nor any
evaluation labels select subsets or settings. Rankings are model-dependent,
especially when inputs are correlated; they are not universal importance claims.

The frozen top five, in final RFE rank order, are:

1. Distance to unresolved prototypes.
2. min(target,total-target)/total.
3. Standardized superincreasing-distance x coverage-distance.
4. Standardized coverage-distance x few-values-distance.
5. target/total.

Top ten also includes distance to completed prototypes, weight coefficient of
variation, few-values distance, coverage distance, and log2(minimum weight+1).
The complete 23-step coefficient trace and ordered schemas are preserved.

The 15-input baseline and full-27 controls are the exact original frozen models.
All four arms were frozen before generating 144 new base lists / 1,152 cases
with original/scaled paired encodings, excluding all 990 prior normalized lists.
Independent half enumeration supplies exact reachability truth. Prediction
labels concern the unchanged exact reference's completion within its 8L budget.

## Prediction: top five is promising on unscaled inputs, not an established gain

| Model | Inputs | Fresh unscaled accuracy | Brier, unscaled | Brier, scaled |
|---|---:|---:|---:|---:|
| Original baseline | 15 | 90.45% | 0.07414 | 0.11324 |
| Full geometric model | 27 | 90.28% | 0.08594 | 0.14611 |
| RFE top ten | 10 | 89.76% | 0.08802 | 0.16285 |
| RFE top five | 5 | 90.97% | 0.06808 | 0.13388 |

Lower Brier is better. Top five lowers the unscaled point estimate by 0.00606
(about 8.2%) versus baseline, with conditional list-bootstrap 95% interval
[-0.01822,+0.00372]. The two-co-primary Bonferroni-level 97.5% interval is
[-0.01981,+0.00487]. Both span zero. Its scaled and pooled-encoding scores
remain worse than baseline: pooled baseline 0.09369 versus top-five 0.10098.
This is a promising unscaled point estimate, not established overall superiority.

Top ten worsens the unscaled point estimate by 0.01388; its conditional 95%
interval is [-0.00013,+0.02745], and adjusted-level interval is
[-0.00215,+0.02897]. The larger selected set does not improve this sample.
Intervals condition on fixed selection/fits; they do not include retraining or
selection uncertainty. All other cohort/full27 comparisons are secondary.

Top five descriptively improves the unscaled larger-size score from 0.04399 to
0.03010 and unseen-family score from 0.11492 to 0.09923; its in-distribution
score worsens from 0.02448 to 0.02615. Subgroup findings are not
multiplicity-adjusted. Full calibration, confusion matrices, shortcut-unresolved
subgroups, scaled cohorts and paired comparisons are saved in the
[prediction report](results/pruning_20261028/PREDICTION_REPORT.md) and
[raw metrics](results/pruning_20261028/prediction_metrics.json).

## Feature count and real acquisition cost

Both selected models retain prototype distances and therefore still depend on
all 15 original measurements. Every learned arm pays the same original feature
acquisition and exact-core reuse. The online adapters compute only retained
transformations: top five needs one class's three prototype queries and two
products; top ten needs both classes and two products. Total declared inference
charges, including transformations, are 110 baseline, 519 full27, 409 top10,
and 238 top5. These heterogeneous counters are not CPU/bit-operation costs.
Fewer classifier inputs do not mean fewer underlying measurements here.

## Paid solving: no clear advantage over the original model

| Policy | Live 20% budget | Live 50% budget | Work 50% budget |
|---|---:|---:|---:|
| Arrival order | 657 | 853 | 858 |
| Pool distance rule | 810 | 874 | 730 |
| Original baseline, 15 | 838 | 876 | 675 |
| Full geometric, 27 | 828 | 874 | 653 |
| RFE top ten | 829 | 874 | 655 |
| RFE top five | 831 | 877 | 659 |

Counts are medians of totals summed over separately budgeted cohorts within
each of three repetitions, across all 1,152 encoded cases. Top five finishes
seven fewer cases than baseline at the tighter live budget, and one more at the
larger budget. The larger-budget ranges overlap: baseline 868-876 versus top
five 872-877. This does not establish improved practical solving. Time ranges
are descriptive machine-specific repetitions, not fresh independent samples.

Under half-budget work accounting, top five finishes six more cases than full27
but 16 fewer than baseline; top ten improves on full27 by two. All learned arms
exhaust planning in 9/24 half-budget cohort-runs. At 20% work budget, all learned
arms exhaust planning in 24/24 and tie in aggregate; classifier pruning cannot
recover costs already consumed acquiring original features and cores.

These are separate cost models. Heterogeneous work deficits are not measured
CPU slowdowns. Predictions only rank inputs; every returned decision is exact
and late answers are excluded. The pool distance rule ranks by 2^(-minimum
distance), rather than using the earlier distance<=2 branch gate. Full traces,
deadline flags and per-cohort costs are in the
[paid report](results/pruning_20261028/PRIORITY_REPORT.md) and its JSON/JSONL artifacts.

## Evidence

All 50 experiment-package unit tests pass. The independent audit reproduces
every RFE elimination and nested subset, independently refits the selected
classifiers/calibrators, verifies unchanged controls, reconstructs fresh derived
features and probabilities, replays exact half-enumeration truth on all 144 base
lists, checks indexed witnesses and all 576 pool traces, and reproduces 288
deterministic counter runs. Source/input/model/data hashes pass. The
[validation record](results/pruning_20261028/VALIDATION.json) preserves counts and
the auditor hash. No earlier experiment or default model was changed.

- [Fixed protocol](PRUNING_PROTOCOL.md).
- [Saved guide](results/pruning_20261028/README.md).
- [Selection trace](results/pruning_20261028/selection.json).
- [Pruning and selected-transform implementation](pruning_models.py).
- [Experiment runner](pruning_experiment.py).
- [Independent audit](audit_pruning.py).

The old default remains unchanged. Any alternative selection method, C tuning,
geometry change or branch-specific target needs a separately evaluated study.
