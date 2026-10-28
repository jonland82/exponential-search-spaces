# Experiment 01: large-base structural geometry

108 fresh lists, 324 cases, 5184 policy runs. Source/config freeze preceded generation. No fitted model or oracle parameter enters solving.

| Policy | Work completions | Live median [range] | Median capped live seconds | Root YES/NO, live | Internal YES/NO, live |
|---|---:|---:|---:|---|---|
| portfolio | 240 | 121 [120, 121] | 10.4967 | 0/0 | 0/0 |
| detect_only | 236 | 121 [121, 121] | 10.5288 | 0/0 | 0/0 |
| root_geometry | 287 | 244 [244, 245] | 4.2824 | 144/309 | 0/0 |
| selective_geometry | 270 | 245 [245, 245] | 4.2755 | 144/309 | 0/0 |

Root/internal counts above sum three dependent timing repeats; completion medians are totals per repeat. Capped seconds include unresolved runs and are not uncensored solution times.

## Paired completion comparisons

| Comparison | Repeat-average difference | Conditional list-bootstrap 95% interval | Joint completions | Median comparator/policy time |
|---|---:|---|---:|---:|
| root_geometry_vs_portfolio | +123.67 | [+101.65, +145.34] | 119 | 0.919 |
| selective_geometry_vs_root_geometry | +0.67 | [+0.00, +1.67] | 243 | 1.001 |
| detect_only_vs_portfolio | +0.33 | [+0.00, +1.00] | 120 | 0.914 |

Only root_geometry versus portfolio is primary. Bootstrap resamples whole base lists, not targets or timing repeats. Joint timing ratios require both policies to finish the case in all three repeats. Secondary comparisons are unadjusted; machine timings do not establish general asymptotic speedups.

## Live family completions

| Family | Portfolio | Detection only | Root geometry | Selective geometry |
|---|---:|---:|---:|---:|
| coverage | 36 | 36 | 36 | 36 |
| few_values | 16 | 16 | 19 | 19 |
| large_base | 7 | 7 | 36 | 36 |
| large_base_many_outliers | 6 | 6 | 16 | 17 |
| large_base_one_outlier | 5 | 5 | 29 | 29 |
| near_equal | 4 | 4 | 36 | 36 |
| progression | 11 | 11 | 36 | 36 |
| random_wide | 0 | 0 | 0 | 0 |
| superincreasing | 36 | 36 | 36 | 36 |

## Separate peak allocation profiles

| Policy | Maximum traced MiB |
|---|---:|
| portfolio | 3.116 |
| detect_only | 3.118 |
| root_geometry | 3.118 |
| selective_geometry | 0.289 |

Memory is Python-traced allocation from 32 separate fixed-case/work-budget profiles, not process RSS or same-success uncensored memory. Logical DP/history bounds are representation estimates. All discovery, checking and native solver work is charged; counters are heterogeneous, not CPU/bit operations. Returned witnesses and completed decisions are checked against independent truth. Bounds and discovery are elementary implementations motivated by decomposable-knapsack literature; the generator is not asserted to inherit that literature's branching lower bounds.

Raw events, phase costs, attempts, overshoots and family/size metrics are retained. The companion geometric plot illustrates aggregate coordinates without fitting PCA or using labels to choose a detector. No paper or earlier model is changed.
