# Empirical distance-to-hard / distance-to-easy follow-up

Frozen before new generation; motivated by the previously inspected plot. Hard means reference completion failure under 8L, not proven intrinsic hardness. All geometry uses the 15 original standardized features and development-training reference lists only. k=5 distinct lists; training rows exclude their entire own list. Separate calibration lists fit sigmoid calibration.

## Fresh unscaled inputs

| Model | Accuracy | Balanced accuracy | Hard precision | Hard recall | Hard AP | Brier |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 90.625% | 86.048% | 83.077% | 77.143% | 0.8645 | 0.0704 |
| hard | 90.972% | 85.308% | 86.667% | 74.286% | 0.8943 | 0.0712 |
| both | 89.062% | 87.199% | 74.522% | 83.571% | 0.8452 | 0.0792 |
| distances | 90.625% | 85.079% | 85.246% | 74.286% | 0.9139 | 0.0620 |
| knn | 89.931% | 82.438% | 87.963% | 67.857% | 0.8053 | 0.0836 |
| constant_prior | 75.694% | 50.000% | 0.000% | 0.000% | 0.2431 | 0.1994 |
| always_easy | 75.694% | 50.000% | 0.000% | 0.000% | 0.2431 | 0.2431 |

576 cases: 436 completed and 140 unresolved. Hard AP is average precision for the hard class; Brier is lower-is-better. Threshold is fixed at p(easy)=0.5. Confusion matrices, log loss, ROC AUC and calibration bins are in prediction_metrics.json.

## Paired fresh comparisons against baseline

| Cohort | Cases | Baseline Brier | Hard-added Brier | Both-added Brier | Both minus baseline [conditional list-bootstrap 95% interval] |
|---|---:|---:|---:|---:|---|
| unscaled | 576 | 0.0704 | 0.0712 | 0.0792 | +0.0088 [-0.0015, +0.0190] |
| scaled | 576 | 0.1089 | 0.0633 | 0.2519 | +0.1430 [+0.1197, +0.1686] |
| all_encodings | 1152 | 0.0896 | 0.0673 | 0.1655 | +0.0759 [+0.0628, +0.0902] |
| in_distribution | 224 | 0.0203 | 0.0187 | 0.0169 | -0.0034 [-0.0098, +0.0018] |
| in_distribution_scaled | 224 | 0.0649 | 0.0225 | 0.1724 | +0.1075 [+0.0713, +0.1469] |
| larger_size | 112 | 0.0708 | 0.0613 | 0.0868 | +0.0160 [-0.0117, +0.0453] |
| larger_size_scaled | 112 | 0.0863 | 0.0367 | 0.2308 | +0.1444 [+0.0910, +0.2082] |
| prior_holdout | 96 | 0.1053 | 0.1346 | 0.1298 | +0.0246 [-0.0073, +0.0524] |
| prior_holdout_scaled | 96 | 0.1775 | 0.1627 | 0.3736 | +0.1961 [+0.1357, +0.2573] |
| unseen_family | 144 | 0.1247 | 0.1182 | 0.1364 | +0.0117 [-0.0129, +0.0361] |
| unseen_family_scaled | 144 | 0.1492 | 0.0814 | 0.3109 | +0.1617 [+0.1212, +0.2013] |

## Remaining cases after exact shortcuts

| Subgroup, fresh unscaled | Cases | Model | Hard recall | Brier |
|---|---:|---|---:|---:|
| unresolved_kernel | 435 | baseline | 77.143% | 0.0932 |
| unresolved_kernel | 435 | hard | 74.286% | 0.0943 |
| unresolved_kernel | 435 | both | 83.571% | 0.1049 |
| unresolved_kernel | 435 | distances | 74.286% | 0.0820 |
| unresolved_kernel | 435 | knn | 67.857% | 0.1107 |
| unresolved_after_reuse | 342 | baseline | 75.940% | 0.1164 |
| unresolved_after_reuse | 342 | hard | 72.932% | 0.1180 |
| unresolved_after_reuse | 342 | both | 82.707% | 0.1300 |
| unresolved_after_reuse | 342 | distances | 72.932% | 0.1021 |
| unresolved_after_reuse | 342 | knn | 68.421% | 0.1299 |

## Previously inspected sample: exploratory reuse

| Model | Accuracy | Hard recall | Brier |
|---|---:|---:|---:|
| baseline | 91.146% | 80.822% | 0.0622 |
| hard | 91.319% | 75.342% | 0.0611 |
| both | 90.799% | 89.041% | 0.0690 |
| distances | 91.493% | 75.342% | 0.0573 |
| knn | 91.146% | 71.233% | 0.0720 |

No hyperparameters or thresholds were selected on either evaluation sample. Intervals resample base lists with all related targets and paired encodings kept together; they condition on fixed models. Secondary comparisons have no multiplicity-adjusted significance interpretation. These features re-express existing inputs; they do not add independent information or correctness certificates. See the separately paid priority experiment for actual solver benefit.
