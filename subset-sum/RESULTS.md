# First subset-sum experiments

These measurements support [companion Note II](../Subset_Sum_as_a_Stress_Test.html), which interprets the exact-search results alongside the later hard-case and classifier experiments.

All runs used Python 3.13.5 on Windows-11-10.0.26200-SP0.
All applicable exact implementations agreed with exhaustive search on 120 small cases.
Each time is the median of three uninstrumented runs, then the table takes the median of two fixed seeds.
Peak memory is measured separately using Python `tracemalloc`; it is not total process memory.
Targets above 100,000,000 skip bitset dynamic programming (DP) to avoid a large target-sized allocation.
Unpaired bounded depth-first search (DFS) is omitted on wide inputs because it may explore exponentially many distinct states.

In the table, $n$ is the number of weights, MITM means meet-in-the-middle, and ms means milliseconds. Pair / MITM and Pair / DFS divide the paired solver's time by each baseline's time; a ratio below 1 favors pairing. `n/a` means the solver was not run or the ratio is unavailable.

**Input families.** `narrow`: weights 1–25, planted target; `wide`: 45-bit weights, planted target; `mixed`: one quarter million-scale weights and three quarters weights 1–25, planted target; `mixed_no`: one quarter million-multiple weights and three quarters weights 1–25, with a target 50,000 above a large-weight subset sum; `modular_no`: all weights multiples of ten except one 1, with a target ending in 2. The last two families have no solution; `modular_no` has global greatest common divisor (gcd) 1.

| Input family | $n$ | Answer | Bitset DP (ms) | MITM (ms) | Bounded DFS (ms) | Certified pair (ms) | Pair / MITM | Pair / DFS |
|---|---:|:---:|---:|---:|---:|---:|---:|---:|
| narrow | 24 | yes | 0.007 | 0.140 | 0.019 | 0.111 | 0.790× | 5.786× |
| narrow | 36 | yes | 0.006 | 0.231 | 0.026 | 0.148 | 0.639× | 5.688× |
| narrow | 48 | yes | 0.009 | 0.664 | 0.034 | 0.244 | 0.368× | 7.167× |
| wide | 24 | yes | n/a | 1.833 | n/a | 4.081 | 2.227× | n/a |
| wide | 30 | yes | n/a | 17.405 | n/a | 72.324 | 4.155× | n/a |
| wide | 36 | yes | n/a | 164.083 | n/a | 354.408 | 2.160× | n/a |
| mixed | 24 | yes | 26.645 | 0.399 | 0.017 | 0.084 | 0.212× | 5.075× |
| mixed | 36 | yes | 89.166 | 15.291 | 0.032 | 0.169 | 0.011× | 5.303× |
| mixed | 48 | yes | 164.379 | 388.777 | 0.091 | 0.527 | 0.001× | 5.800× |
| mixed_no | 24 | no | 67.836 | 0.453 | 0.021 | 0.170 | 0.376× | 8.148× |
| mixed_no | 36 | no | 95.488 | 0.951 | 0.035 | 0.255 | 0.268× | 7.322× |
| mixed_no | 48 | no | 186.243 | 3.354 | 0.079 | 0.509 | 0.152× | 6.454× |
| modular_no | 24 | no | 0.086 | 1.156 | 17.004 | 0.031 | 0.027× | 0.002× |
| modular_no | 36 | no | 0.324 | 12.204 | 117.682 | 0.081 | 0.007× | 0.001× |
| modular_no | 48 | no | 0.401 | 38.144 | 248.429 | 0.069 | 0.002× | 0.000× |

The certified pair search first checks whole-instance bounds and residues. If they pass, it stores all distinct sums of one half, then explores the other half. It merges equal partial sums, rejects sums outside exact lower/upper bounds, and rejects unreachable target residues modulo 8, 10, 16, or 32. Each rejection is sound. The simple meet-in-middle baseline also merges duplicate sums and discards sums above the target.
Bounded DFS uses the same item order and exact interval bounds as the pair search, but no paired tail or residue checks. This separates early discovery of a planted solution from gains due to the added mechanisms.

**Why the rejections are exact.** A positive-weight branch with partial sum above the target, or with partial sum plus all remaining weights below it, cannot succeed. If the needed remainder has no attainable suffix residue modulo any tested modulus, it cannot succeed either. A paired lookup succeeds exactly when the complement is among the stored tail sums.

## Interpretation

- Narrow weights favor bitset DP. Wide weights favor meet-in-the-middle. The paired solver does not beat either on those families.
- On mixed inputs, pairing beats meet-in-the-middle, but plain bounded DFS is faster still. Early discovery or interval pruning explains the apparent gain; pairing has not earned its cost.
- On `modular_no`, the residue-10 check rejects at the root before any tail summary is built. This is an exact polynomial-cost certificate, but it is a simple known arithmetic test that a stronger baseline could also use.
- No learned proposal model was used. These results isolate exact representation and certification first.

The next useful test is a family where bounded DFS and meet-in-the-middle both do substantial work, while a compact paired summary plus a nontrivial verifier saves time over both.

Raw per-run times, traced memory, and operation counts are in [results.json](results.json). These small constructed families show behavior, not a new worst-case bound or a claim against optimized solvers.

Reproduce with `python subset-sum/experiment.py` from the repository root.
