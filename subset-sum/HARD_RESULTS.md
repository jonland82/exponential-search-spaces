# Follow-up: hard no-solution subset-sum cases

These measurements support [companion Note II](../Subset_Sum_as_a_Stress_Test.html).

This experiment tests whether paired summaries add a benefit after cheap root certificates have failed.
The solvers agreed with exhaustive search on 9 small cases. Both meet-in-the-middle and the paired solver returned NO on every benchmark case.
Each weight is a random 41-bit odd integer, appearing once, twice, or three times; the table calls these families `unique`, `pairs`, and `triples`, respectively. Targets lie near half the total weight. Every target passes the whole-instance bounds and the reachable-residue checks modulo 8, 10, 16, and 32; all inputs have greatest common divisor (gcd) 1.
The sorted half split keeps repeated weights together. The same whole-instance bounds and residue checks are charged to all algorithms. Bitset dynamic programming (DP) is infeasible because targets are trillions.
Certified depth-first search (DFS) is stopped after 2 seconds; a stopped run has no answer. Times are one uninstrumented Python run per seed, with medians below. In the table, $n$ is the number of weights, MITM means meet-in-the-middle, ms means milliseconds, Pair / MITM is the paired time divided by MITM time, and Pair tail sums counts distinct stored half sums. All data is in [hard_results.json](hard_results.json).

| Family | $n$ | MITM (ms) | Certified pair (ms) | Pair / MITM | Certified DFS (ms) | Pair tail sums |
|---|---:|---:|---:|---:|---:|---:|
| unique | 24 | 2.0 | 10.1 | 5.16× | 1729.5 | 4,096 |
| unique | 30 | 16.9 | 83.7 | 4.96× | >2000 (some stopped) | 32,768 |
| unique | 36 | 148.0 | 707.1 | 4.78× | >2000 (some stopped) | 262,144 |
| pairs | 24 | 0.8 | 3.4 | 4.33× | 73.2 | 729 |
| pairs | 30 | 3.2 | 13.5 | 4.26× | >2000 (some stopped) | 4,374 |
| pairs | 36 | 14.6 | 77.1 | 5.27× | >2000 (some stopped) | 19,683 |
| triples | 24 | 0.2 | 1.5 | 6.29× | 19.8 | 256 |
| triples | 30 | 1.0 | 5.7 | 5.48× | 228.0 | 1,024 |
| triples | 36 | 3.6 | 21.1 | 5.89× | >2000 (some stopped) | 4,096 |

The paired solver was faster on 0 of 18 individual cases. This implementation therefore shows no incremental subset-sum gain on the tested collision levels.

Across all 18 benchmark cases, the paired solver made 0 residue-based branch rejections. Bounds rejected 1,424 of 1,382,730 visited branch states. These checks supplied little additional pruning on this family; meet-in-the-middle already compresses equal sums in both halves.

A ratio below 1 means the paired solver was faster than meet-in-the-middle. That ratio alone does not establish a new algorithm: both are exact variants of half-sum search, and the dataset is small and constructed.

Reproduce with `python subset-sum/hard_experiment.py` from the repository root.
