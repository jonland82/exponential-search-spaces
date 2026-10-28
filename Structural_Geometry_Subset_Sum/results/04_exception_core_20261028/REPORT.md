# Reusable geometric cores with exceptional weights

Fresh inputs after a source/config freeze; no ML. All online discovery, prefix-history copies, core construction, exceptional queries, exact fallback and witness checking are paid. No planted decomposition or family metadata enters solving.

| Policy | Full 32L completions | Actual work | Live 20ms median [range] | Core calls / completions |
|---|---:|---:|---:|---|
| lean | 434 | 16157748 | 356 [353,356] | 0/0 |
| root | 453 | 13990563 | 407 [402,408] | 0/0 |
| discover_only | 450 | 14272360 | 407 [404,408] | 0/0 |
| reuse | 469 | 12708976 | 440 [434,440] | 98/98 |
| direct_mitm | 412 | 11704849 | 358 [357,362] | 0/0 |

Primary reuse-minus-root completion difference: +16; conditional whole-list-bootstrap 95% interval [4.0, 30.024999999999864]. Reuse-only completions: 19; root-only: 3.

The primary is full individual work-capped completion on all fresh cases, not a pool endpoint. Bootstrap keeps targets from each weight list together and conditions on the fixed solver. Capped-cost, family, timing and other-control comparisons are secondary; timing repeats share the same cases.

## Fresh family completions

| Family | Lean | Root DP | Discovery only | Reuse | Direct MITM |
|---|---:|---:|---:|---:|---:|
| superincreasing | 36 | 36 | 36 | 36 | 36 |
| coverage | 36 | 36 | 36 | 36 | 26 |
| few_values | 36 | 36 | 36 | 36 | 36 |
| small_support | 36 | 36 | 36 | 36 | 36 |
| interval_union | 36 | 36 | 36 | 36 | 36 |
| progression | 33 | 33 | 33 | 33 | 29 |
| random_wide | 12 | 12 | 12 | 12 | 12 |
| near_equal | 21 | 20 | 20 | 25 | 25 |
| filtered_modular | 22 | 22 | 22 | 22 | 20 |
| block_pairs | 36 | 36 | 36 | 36 | 16 |
| two_scale | 15 | 13 | 11 | 11 | 12 |
| two_progressions | 15 | 14 | 13 | 13 | 17 |
| large_base | 34 | 36 | 36 | 36 | 36 |
| large_base_one_outlier | 28 | 34 | 34 | 36 | 36 |
| large_base_many_outliers | 19 | 22 | 22 | 34 | 24 |
| wide_aggregate | 19 | 31 | 31 | 31 | 15 |

## Paid work pools

| Cohort | Budget fraction | Lean | Root | Discovery only | Reuse | Direct MITM |
|---|---:|---:|---:|---:|---:|---:|
| large_base | 0.2 | 33 | 58 | 58 | 97 | 49 |
| large_base | 0.5 | 70 | 123 | 123 | 137 | 111 |
| legacy_families | 0.2 | 150 | 136 | 127 | 136 | 165 |
| legacy_families | 0.5 | 334 | 324 | 314 | 332 | 301 |

## Retrospective repair diagnostic

The following previously inspected failures motivated the algorithm. This is explicitly exploratory reuse, not fresh evidence or an additional primary endpoint. Root here omits the old classifier's unnecessary doubling/inference costs.

| Policy | Completed / 115 old misses | Many-outlier cases completed / 14 |
|---|---:|---:|
| root | 0 | 0 |
| reuse | 25 | 11 |
| direct_mitm | 15 | 5 |

The route uses the single existing blind projection, removes largest absolute residuals until fixed size/work gates fit, builds one signed two-coordinate bitset table with prefix witnesses, then queries every necessary Gray-code exceptional assignment. Nonnegative quotients and positive exceptional weights justify truncating q using the original target. NO requires a complete core and exhaustion of all assignments. Work/time caps always yield unresolved. Up to nine exceptions and logical DP/history caps bound the route; these are not exact Python/RSS allocation bounds. Heterogeneous work counters are not uniform bit operations. All returned witnesses/answers are independently checked; live late answers are excluded.

The primary root control shares all existing five-core reuse, original root geometry, caps and bitset/DFS/MITM fallback. Discovery-only measures new partition-search cost without solving; lean/direct MITM are additional controls. Results concern this constructed small-size mixture, not arbitrary subset sum or a new worst-case complexity theorem. Earlier models, experiments and manuscripts are preserved.
