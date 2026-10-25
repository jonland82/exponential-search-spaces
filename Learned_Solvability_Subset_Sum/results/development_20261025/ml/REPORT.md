# Five-feature development comparison

exploratory development-model comparison; no prospective performance claim.

The prediction label is completion by the same exact solver portfolio under the 8L budget for every feature set. Feature extraction is excluded from this common label to compare predictive information. Separate operational runs charge extraction, reuse certificates and apply the same fallback portfolio.

## Calibrated probability quality

Brier score: lower is better. Evaluation includes every target. Additional unresolved-kernel-only metrics and raw/calibrated scores are in metrics.json.

| Model | Same-distribution test | Larger size | Unseen families |
|---|---:|---:|---:|
| constant | 0.0777 | 0.1344 | 0.3740 |
| original:forest | 0.0540 | 0.0898 | 0.2605 |
| progression:forest | 0.0540 | 0.0911 | 0.2515 |
| target_original:forest | 0.0403 | 0.0763 | 0.2872 |
| target_progression:forest | 0.0353 | 0.0814 | 0.2915 |
| conventional:forest | 0.0231 | 0.0452 | 0.2392 |
| hybrid:forest | 0.0199 | 0.0453 | 0.1961 |

## Interpretation

All targets from a weight list share a split. Calibration uses separate lists. Near-equal and filtered-modular families, and size n=36, never enter training or calibration. Unseen-family evaluation also includes n=36; its smaller-size subgroup is recorded separately to distinguish family and size shifts.

Confidence intervals resample lists with model predictions held fixed; they do not include uncertainty from retraining. Model and feature choices are development choices informed by the earlier feasibility pilot. No final prospective test or claim of polynomial asymptotic performance is made.

The raw predictions, calibration comparisons, four-input ablations, paired Brier differences, dependency versions and source/data hashes are retained. No learned budget-prioritization policy has been tested yet.
