# Training-only pruning: fresh logistic comparison

RFE selected features using only the 84 development training lists. Models were frozen before fresh generation; calibration uses separate lists. Lower Brier is better. Completion labels concern the exact reference's 8L work budget, not reachability or branch-checker benefit.

| Model | Inputs | Accuracy | Hard precision | Hard recall | Brier |
|---|---:|---:|---:|---:|---:|
| baseline | 15 | 90.451% | 84.559% | 77.181% | 0.07414 |
| combined | 27 | 90.278% | 89.744% | 70.470% | 0.08594 |
| top10 | 10 | 89.757% | 88.793% | 69.128% | 0.08802 |
| top5 | 5 | 90.972% | 90.083% | 73.154% | 0.06808 |

## Two co-primary comparisons against original baseline

| Model | Brier difference | Conditional 95% interval | Bonferroni-level 97.5% interval |
|---|---:|---|---|
| top5 | -0.00606 | [-0.01822, +0.00372] | [-0.01981, +0.00487] |
| top10 | +0.01388 | [-0.00013, +0.02745] | [-0.00215, +0.02897] |

## Frozen selected features

**top5:** target_fraction, complement_min_target_fraction, prototype_distance_unresolved, standardized_d0_times_d1, standardized_d1_times_d2.

**top10:** d_coverage, d_values, log2_min_plus_one, coefficient_of_variation, target_fraction, complement_min_target_fraction, prototype_distance_unresolved, prototype_distance_completed, standardized_d0_times_d1, standardized_d1_times_d2.

The top5 set is nested within top10. Rankings describe this fixed RFE procedure on correlated candidate features, not universal feature importance. All learned policies still pay original feature acquisition and identical core reuse. Selected prototype distances depend on all 15 base inputs; selected products depend on both original coordinates.

## Secondary cohort comparisons

| Cohort | Cases | Baseline Brier | Full27 | Top10 | Top5 |
|---|---:|---:|---:|---:|---:|
| unscaled | 576 | 0.07414 | 0.08594 | 0.08802 | 0.06808 |
| scaled | 576 | 0.11324 | 0.14611 | 0.16285 | 0.13388 |
| all_encodings | 1152 | 0.09369 | 0.11603 | 0.12544 | 0.10098 |
| in_distribution | 224 | 0.02448 | 0.02097 | 0.02134 | 0.02615 |
| in_distribution_scaled | 224 | 0.07222 | 0.07252 | 0.07974 | 0.07658 |
| larger_size | 112 | 0.04399 | 0.04964 | 0.05519 | 0.03010 |
| larger_size_scaled | 112 | 0.08576 | 0.08324 | 0.10162 | 0.06734 |
| prior_holdout | 96 | 0.16403 | 0.21735 | 0.22772 | 0.16349 |
| prior_holdout_scaled | 96 | 0.19282 | 0.30446 | 0.32334 | 0.27258 |
| unseen_family | 144 | 0.11492 | 0.12764 | 0.12416 | 0.09923 |
| unseen_family_scaled | 144 | 0.14538 | 0.20392 | 0.23274 | 0.18231 |

Bootstrap intervals resample base lists with targets/encodings together and condition on fixed models/selection. They exclude retraining/selection uncertainty. The two co-primary comparisons have conservative 97.5% per-comparison levels; all remaining subgroup/full27 comparisons are secondary. Full calibration, confusion, unresolved-shortcut subgroup and full27-paired metrics are saved. Paid solver timing is a separate endpoint; no default model is changed.
