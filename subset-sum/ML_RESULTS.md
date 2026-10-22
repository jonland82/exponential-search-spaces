# Subset-sum probability classifier

This experiment is discussed in [companion Note II](../Subset_Sum_as_a_Stress_Test.html) and reinterpreted for the random-target question in [Note III](../Probability_Valued_Subset_Sum.html).

A random forest predicts the probability that a target can be formed from a list of positive integers. Every label is computed exactly by meet-in-the-middle. Targets are sampled independently of labels from the middle 40% of each list's total sum, then required to pass simple modular certificates. The model sees only summary features of the list and target, not the exact subset sums.

- Training: 3,360 targets; calibration: 720; held-out test: 720. Splits use disjoint input lists.
- Held-out YES rate: 31.8%. Forest AUC 0.866, Brier 0.133, accuracy 80.8%.
- Simple density-model AUC 0.864, Brier 0.136. On unseen n=24 lists, forest AUC 0.879, Brier 0.115.
- Even at P(YES) ≤ 1%, 2 of 43 proposed NO answers are actually YES.

## Charts

![Predicted probabilities, calibration, ROC, and confusion matrix](classifier_overview.png)

![Proposed NO coverage and errors by probability threshold](classifier_thresholds.png)

![Performance across input families and feature importance](classifier_generalization.png)

## Interpretation

The classifier can rank cases by likelihood, but a predicted NO is not a proof. False NO predictions are exactly the dangerous errors for certified elimination. The threshold chart counts them explicitly; the framework still needs an exact verifier.

The forest performs about as well as the simple density-based classifier. This suggests most of its signal comes from density, rather than a new property of the pairing framework. The comparison is not against an optimized learned solver. The input families are synthetic, the probability calibration is specific to their sampling distribution, and the model has not been shown to reduce exact solution time.

Reproduce with `python subset-sum/ml_experiment.py` after installing [requirements-ml.txt](requirements-ml.txt). Raw scores and thresholds are in [ml_results.json](ml_results.json); each held-out prediction is in [ml_predictions.csv](ml_predictions.csv).
