# What the latest solver misses

Post-hoc diagnosis of the already-inspected Experiment 03 test set, using full individual work-capped runs rather than cases left unattempted by a shared pool. These are solver failures, not classifier misclassifications or proofs of intrinsic hardness.

| Family | Unresolved | Total |
|---|---:|---:|
| random_wide | 24 | 36 |
| two_scale | 23 | 36 |
| two_progressions | 23 | 36 |
| large_base_many_outliers | 14 | 36 |
| filtered_modular | 13 | 36 |
| near_equal | 12 | 36 |
| progression | 4 | 36 |
| large_base_one_outlier | 1 | 36 |
| wide_aggregate | 1 | 36 |
| superincreasing | 0 | 36 |
| coverage | 0 | 36 |
| few_values | 0 | 36 |
| small_support | 0 | 36 |
| interval_union | 0 | 36 |
| block_pairs | 0 | 36 |
| large_base | 0 | 36 |

115/576 unresolved under learned; 100 remain unresolved under every original policy. Direct MITM already rescues 15 learned failures at the original allowance. All unresolved inputs have 30 or 36 items; every 24-item case completes.

Only 1 unresolved case reaches an eligible DP decision. The others exceed both DP-area and history caps. All 115 bitset attempts hit width limits; all 115 DFS attempts hit work limits; MITM hits 58 state limits and 57 work limits. The minimum old-core deletion feature among failed cases ranges from 15 to 29, median 27.

The named easy families can contain replacements: all failed near_equal and progression cases have 25% random replacements. Two progressions/two scales combine distinct structures that a single existing core or projection may represent poorly. Many-outlier large-base cases have a few dominant residuals; trimming those suggests an exception-to-geometric-core route, but this analysis does not implement or time such a solver.

## Resource sensitivity on the same failed inputs

Direct MITM retains original reduction/feature/five-core costs. Only the declared resource caps change. No live deadline is imposed. These probes diagnose caps; they are not speedups or fresh confirmatory results.

| Probe | Work allowance | State cap | Completed / selected failures |
|---|---|---:|---:|
| memory_only | original 32L | 1048576 | 17/115 |
| work_only | 16 times original | 32768 | 20/115 |
| memory_and_work | 16 times original | 1048576 | 115/115 |

Full per-case descriptors, input-only trimmed-core size hypotheses, exact probe answers/witnesses, parent/source hashes and all subgroup counts are saved. Geometry eligibility, repeated-family targets and post-hoc selection limit interpretation. Generated family metadata is used only for diagnosis; it never enters the measured original algorithms. Earlier models and experiments are unchanged.
