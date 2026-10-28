# Literature-derived features in logistic regression

New disjoint expanded training/calibration/test lists; every model uses identical training labels and C=1. The label remains original exact-portfolio completion within 8L, not reachability or geometric-check benefit. Models were frozen before test generation.

## Primary: cases remaining after identical exact shortcuts

Reduction, all five existing zero-deletion cores and aggregate-gap NO checks define this subgroup. Exact geometric certificates receive no ML credit. Lower Brier is better.

| Model | Cases | Brier | Accuracy | Hard recall | Brier difference vs 15 | Adjusted 97.5% interval |
|---|---:|---:|---:|---:|---:|---|
| baseline15 | 250 | 0.12222 | 84.0% | 97.3% | -- | -- |
| geometry18 | 250 | 0.10621 | 84.4% | 94.6% | -0.01601 | [-0.03825, +0.00451] |
| doubling19 | 250 | 0.10111 | 85.6% | 95.2% | -0.02111 | [-0.04341, +0.00065] |

## Secondary predictive cohorts

| Cohort | Cases | Baseline15 Brier | Geometry18 | Doubling19 |
|---|---:|---:|---:|---:|
| all | 405 | 0.09016 | 0.07990 | 0.07595 |
| legacy_families | 324 | 0.08192 | 0.08147 | 0.07747 |
| large_base | 81 | 0.12311 | 0.07364 | 0.06987 |

## Paid prioritization

Median completions over three paired arrival orders, including acquisition, inference, exact reuse, sorting, solving and witness checking. Live pools use actual recomputation and cooperative deadlines; late answers are excluded. Work counters are heterogeneous operations, not CPU/bit complexity.

cheap15 skips geometric discovery. matched15 pays discovery and uses its exact gap certificate, but predicts from the original 15 inputs. geometry18 has the same exact shortcuts plus three geometric inputs. doubling19 additionally pays distinct-weight additive doubling. Comparing geometry18 with matched15 isolates the learned features; comparison with cheap15 measures their complete package.

| Mode | Cohort | Budget fraction | cheap15 | matched15 | geometry18 | doubling19 |
|---|---|---:|---:|---:|---:|---:|
| time | large_base | 0.2 | 6.0 | 50.0 | 55.0 | 55.0 |
| time | large_base | 0.5 | 9.0 | 56.0 | 56.0 | 56.0 |
| time | legacy_families | 0.2 | 191.0 | 193.0 | 197.0 | 199.0 |
| time | legacy_families | 0.5 | 199.0 | 202.0 | 202.0 | 202.0 |
| work | large_base | 0.2 | 0.0 | 8.0 | 8.0 | 8.0 |
| work | large_base | 0.5 | 0.0 | 28.0 | 28.0 | 26.0 |
| work | legacy_families | 0.2 | 54.0 | 55.0 | 55.0 | 51.0 |
| work | legacy_families | 0.5 | 89.0 | 81.0 | 81.0 | 78.0 |

Test cases: 405 from 135 independent lists; 250 remain after all shared checks; 56 additional exact aggregate-gap answers after the five cores.

## Limits

These are proposed operational descriptors motivated by decomposable-knapsack and small-doubling results, not published proven difficulty predictors. Candidate discovery is bounded and heuristic. Models use the same expanded mixture, so this is a feature comparison rather than a direct retest of the earlier fitted model. There is no paired scaled-encoding or unseen-family generalization claim. Bootstrap intervals keep targets from each list together, condition on fitted models, and omit retraining uncertainty; subgroup endpoints and timing comparisons are descriptive. The two primary comparisons use conservative Bonferroni-level intervals. Three repeat orders are not independent datasets. No learned prediction certifies NO or prunes a branch. No large-base DP is run in this classifier experiment. No default model or paper is changed.
