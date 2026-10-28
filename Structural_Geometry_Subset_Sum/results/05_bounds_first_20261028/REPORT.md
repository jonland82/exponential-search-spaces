# Bounds before geometric core construction

Fresh source/config freeze; every acquisition, bound, construction, fallback and verification cost is paid. Root/reuse call the frozen Experiment 04 implementation. No ML or family labels enter solving.

| Policy | Exact completions | Capped work | Actual work | Discovery work | Core builds | Live 20ms median [range] |
|---|---:|---:|---:|---:|---:|---:|
| root | 916/1152 | 28582458 | 27779526 | 0 | 0 | 836 [823,836] |
| reuse | 953/1152 | 26463413 | 25735033 | 875473 | 182 | 896 [884,898] |
| bounds_only | 933/1152 | 27494127 | 26710068 | 249587 | 0 | 862 [846,862] |
| bounds_first | 954/1152 | 26002456 | 25218397 | 249587 | 92 | 897 [889,897] |
| fast_eager | 954/1152 | 26122175 | 25338116 | 249587 | 182 | 894 [884,898] |

Primary bounds-first minus previous reuse completions: {'difference': 1, 'list_bootstrap_95': [0.0, 3.0], 'first_only': 1, 'second_only': 0, 'lists': 384}.

Intervals resample whole weight lists (three dependent targets per list). They condition on these fixed solvers and this generated mixture. Secondary intervals are exploratory and unadjusted. Timing repeats share the same inputs; counters are heterogeneous units, not CPU/bit operations.

## Attribution comparisons

| Comparator | Bounds-first completion difference [95% interval] | Capped work saved [95% interval] |
|---|---:|---:|
| root | +38 [20.0, 57.02500000000009] | +2580002 [1539439.475, 3698673.95] |
| reuse | +1 [0.0, 3.0] | +460957 [371704.425, 566670.55] |
| bounds_only | +21 [12.0, 31.0] | +1491671 [982738.95, 2038007.325] |
| fast_eager | +0 [0.0, 0.0] | +119719 [47780.625, 219336.67500000002] |

fast_eager shares the fast discovery, selected plan and gates with bounds_first; only table timing differs. bounds_only uses those same DP-affordability gates and returns unresolved at the first interval-feasible assignment. It is an attribution control, not an unrestricted bounds-only solver.

## Fresh family completions

| Family | root | reuse | bounds_only | bounds_first | fast_eager |
|---|---:|---:|---:|---:|---:|
| superincreasing | 72 | 72 | 72 | 72 | 72 |
| coverage | 72 | 72 | 72 | 72 | 72 |
| few_values | 72 | 72 | 72 | 72 | 72 |
| small_support | 72 | 72 | 72 | 72 | 72 |
| interval_union | 72 | 72 | 72 | 72 | 72 |
| progression | 57 | 60 | 59 | 60 | 60 |
| random_wide | 24 | 24 | 24 | 24 | 24 |
| near_equal | 56 | 67 | 64 | 68 | 68 |
| filtered_modular | 38 | 38 | 38 | 38 | 38 |
| block_pairs | 71 | 71 | 71 | 71 | 71 |
| two_scale | 30 | 30 | 30 | 30 | 30 |
| two_progressions | 26 | 26 | 26 | 26 | 26 |
| large_base | 72 | 72 | 72 | 72 | 72 |
| large_base_one_outlier | 70 | 72 | 69 | 72 | 72 |
| large_base_many_outliers | 45 | 66 | 53 | 66 | 66 |
| wide_aggregate | 67 | 67 | 67 | 67 | 67 |

## Previously observed regressions (retrospective only)

The three Experiment 04 cases completed by root but missed by reuse are replayed as a diagnostic. They are excluded from all fresh counts and intervals.

- root: 3/3
- reuse: 0/3
- bounds_only: 3/3
- bounds_first: 3/3
- fast_eager: 3/3

NO requires all exceptional assignments to be rejected by necessary bounds, or complete exact core queries. An interrupted check returns unresolved. Logical DP/history limits do not measure exact Python allocation or RSS. Earlier frozen studies and manuscripts are preserved. No general worst-case or state-of-the-art claim is made.
