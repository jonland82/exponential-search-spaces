# Paper VI feasibility pilot

exploratory feasibility pilot; no fitted model or prospective performance claim.

162 weight lists, 486 targets, 1944 portfolio runs. 1640 completed decisions independently checked; zero disagreements. Every returned witness checked against original indices.

## Five features

| Feature | Min | Median | Max | Zero-distance lists |
|---|---:|---:|---:|---:|
| superincreasing | 0 | 20.0 | 30 | 6 |
| coverage | 0 | 16.0 | 32 | 12 |
| few_values | 0 | 14.0 | 30 | 12 |
| small_support | 0 | 9.0 | 25 | 12 |
| interval_union | 0 | 13.0 | 29 | 26 |

Unique feature vectors: 110. Duplicate sorted lists: 0.

## Budget feasibility

L is the documented self-delimiting input-length proxy. Work counters include a conservative feature-extraction charge and the existing solvers' counters; they are not equal-cost bit operations. A separate state cap and bitset width cap apply.

| Budget / policy | Completed | Unresolved | Lists with target-dependent outcomes |
|---|---:|---:|---:|
| 8L:without_features | 411 | 75 | 34 |
| 8L:with_features | 320 | 166 | 45 |
| 32L:without_features | 455 | 31 | 12 |
| 32L:with_features | 454 | 32 | 12 |

## Interpretation boundary

No model has been trained. The feature majority ceiling is an in-sample descriptive statistic, not a held-out accuracy result. Target-blind features can estimate an average over targets but cannot distinguish targets on the same list. All families are synthetic, the seed count is small, and timings are single-run measurements.

The with-features policy prepays extraction separately for every target. The without-features policy uses the identical schedule with no extraction charge. There is no learned policy in this comparison. Extraction is completed offline even when its work charge exceeds the per-case budget, in which case no solver runs.

Full inputs, oracle witnesses, certificates, attempts, work counts, timings, source snapshots and hashes are retained beside this report.
