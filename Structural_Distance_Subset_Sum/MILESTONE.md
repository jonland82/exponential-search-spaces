# First milestone: October 24, 2026

The first stage of the proposed note is implemented and checked. The immediate
next stage is a controlled comparison of decompositions and their residual work.

## What is established

- Sorted greedy discovery finds a maximum-size superincreasing core in
  $O(n\log(n+1))$ arithmetic/comparison operations, including sorting. The
  [proof](THEORY.md) improves the originally planned quadratic discovery bound.
- The two exact solvers have bounds

$$
O\!\left(n\log(n+1)+(n+1)2^{k(w)}\right)
$$

and

$$
O\!\left(n\log(n+1)+(n+1)M(E)\right).
$$

- Eight independent test groups pass, including exhaustive core optimality,
  all-target small cases, indexed witnesses, large integers, and resource limits.
- Maximum core cardinality does not minimize residual support. The explicit
  example $[1,1,1,2,3]$ has equally large cores leaving six or five exceptional
  sums, respectively.

The decomposition argument establishes correctness and sufficient polynomial
regimes. Literature novelty has not yet been established.

## What the exploratory pilot says

The [checked pilot report](results/pilot_20261024_checked/REPORT.md) covers 48 lists,
96 targets, and five methods. There are 79 YES and 17 NO targets. All 444 completed
answers agree with independently enumerated half-sum labels; all returned
witnesses are valid. The other 36 runs are bitset-width exclusions.

At actual distance $k=12$, repeated exceptions have $M=13$, whereas some unrelated
exceptions have $M=4096$. This illustrates the difference between exception count
and residual support.

Elapsed cost still depends on the target. In the checked run, distinct-sum core
search beats bounded DFS on 45 of 96 cases; exceptional-selection core search
beats it on 56. These are single instrumented timings, not stable speedup
estimates. The full support construction can cost more than an early YES search.

The NO cohort is small and uneven: 11 targets have $k=0$, three have $k=8$, two
have $k=12$, and one has $k=4$. It does not support a broad conclusion about
exhaustive search as disruption grows.

The original pilot is also preserved, with source snapshots, under
`results/pilot_20261024/`. The checked rerun tightens the MITM baseline's snapshot
budget check to occur before allocating that snapshot. It uses the same inputs
and is a regression rerun, not an independent prospective sample.

## Next steps

1. **Finish the literature audit.** Establish what is already known about
   superincreasing-core discovery, deletion parameters, and support-sensitive
   subset-sum algorithms before choosing a novelty claim.
2. **Choose a small, explicit set of alternative core-selection rules.** Compare
   residual supports among cores of the same maximum size. Any support estimate
   or exact support calculation used to select a core must be charged.
3. **Design a stronger target cohort.** Obtain more independently labeled NO
   cases at nonzero distances. Report the conditioning or rejection sampling
   used to obtain them, including label-generation effort, separately from
   uniform-target and planted-YES workloads.
4. **Freeze the comparison before generating fresh evaluation inputs.** Fix
   sizes, disruption families, target rules, solver variants, seeds, state/time
   limits, and reporting metrics. Include matched comparisons with bounded DFS
   and every feasible exact baseline.
5. **Profile memory separately and scale the useful regimes.** Distinguish
   record counts from measured Python bytes; show discovery, generation, and
   query work separately. Keep interrupted outcomes visible.

Adaptive recognition and other types of cores come after this comparison. The
next decision is whether selecting a better decomposition reduces enough actual
search to pay for discovering it.

## Follow-up completed

The [frozen-study findings](FINDINGS.md) now answer that next-stage question for
the two tested one-swap selectors. They reduced support on 18 structured lists
but did not repay their cost on any of the 162 structured target cases. The
report preserves all timing repetitions, resource limits, controls, and
separate memory measurements.
