# New geometric features: calibrated logistic regression

Fresh inputs generated after freezing all four models. Completion means the fixed exact portfolio finishes within 8L, not reachability or intrinsic hardness. Training-list-only geometry; entire-own-list exclusions for training prototypes; disjoint sigmoid calibration. See GEOMETRIC_PROTOCOL.md and feature_schema.json.

| Model | Features | Accuracy | Hard precision | Hard recall | Brier (lower better) |
|---|---:|---:|---:|---:|---:|
| baseline | 15 | 89.583% | 83.088% | 75.333% | 0.08220 |
| prototypes | 17 | 89.757% | 92.523% | 66.000% | 0.09046 |
| interactions | 25 | 88.889% | 80.282% | 76.000% | 0.08375 |
| combined | 27 | 89.757% | 90.991% | 67.333% | 0.08576 |

## Combined versus baseline by cohort

| Cohort | Cases | Baseline Brier | Combined Brier | Difference [conditional 95% interval] |
|---|---:|---:|---:|---|
| unscaled | 576 | 0.08220 | 0.08576 | +0.00356 [-0.01399, +0.01914] |
| scaled | 576 | 0.12528 | 0.15039 | +0.02511 [-0.02234, +0.07302] |
| all_encodings | 1152 | 0.10374 | 0.11808 | +0.01434 [-0.01446, +0.04401] |
| in_distribution | 224 | 0.01703 | 0.01175 | -0.00528 [-0.01402, -0.00034] |
| in_distribution_scaled | 224 | 0.06520 | 0.06358 | -0.00162 [-0.05337, +0.04570] |
| larger_size | 112 | 0.03639 | 0.04379 | +0.00740 [-0.01433, +0.02862] |
| larger_size_scaled | 112 | 0.10994 | 0.06572 | -0.04422 [-0.12409, +0.04076] |
| prior_holdout | 96 | 0.19068 | 0.26349 | +0.07281 [+0.03774, +0.10878] |
| prior_holdout_scaled | 96 | 0.22155 | 0.36537 | +0.14381 [-0.07034, +0.34655] |
| unseen_family | 144 | 0.14688 | 0.11503 | -0.03185 [-0.08255, +0.01357] |
| unseen_family_scaled | 144 | 0.16651 | 0.20798 | +0.04147 [-0.06098, +0.14843] |

Primary endpoint is combined-minus-baseline Brier on fresh unscaled cases; negative favors the new features. All 1,000 bootstrap draws resample base lists. Intervals condition on these fixed fitted models, not retraining. Other arms and cohorts are secondary; no multiplicity-adjusted claims. Full subgroup/shortcut metrics, confusion matrices, probabilities and raw added features are saved. Paid prioritization is separate from prediction quality and from branch-level checking.
