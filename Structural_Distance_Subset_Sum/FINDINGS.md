# Structural distance: what the first frozen comparison establishes

**October 24, 2026.** Findings for the proposed new subset-sum note.

The constructive guarantee survives: a cheaply discovered superincreasing core
reduces exact search to its exceptions. The new experiment identifies a separate
limit: selecting a core with fewer residual sums can cost substantially more
than it saves.

## Theory and claim boundary

The [core proof](THEORY.md) gives a sorted greedy procedure finding a
maximum-cardinality superincreasing core. The exceptional-selection and
distinct-exceptional-sum procedures have core-discovery/search operation counts
of the forms

$$
O\!\left(n\log(n+1)+(n+1)2^{k(w)}\right)
$$

and

$$
O\!\left(n\log(n+1)+(n+1)M(E)\right).
$$

Here $k(w)$ is minimum deletion distance, and $M(E)$ is the number of distinct
subset sums of the chosen exceptional list. Arithmetic on encoded integers,
input validation, and root gcd checks must also be charged. In terms of full
binary input length $L$, conservative bounds remain

$$
\operatorname{poly}(L)\,2^{k(w)}
\qquad\text{and}\qquad
\operatorname{poly}(L)\,M(E).
$$

Thus logarithmic deletion distance is a sufficient polynomial regime. A
polynomially bounded exceptional support gives another sufficient regime for the
simple distinct-sum solver. Neither parameter is a lower bound on the complexity
of every other exact method.

The [literature audit](LITERATURE.md) places the ingredients among established
tractable-core, backdoor, and output-sensitive ideas. Novelty of the precise
specialization is not established.

## What was frozen and tested

The local protocol and 11 protected source snapshots were frozen before
generating fresh evaluation inputs. The full [report](results/prospective_20261024/REPORT.md)
links the protocol, hashes, inputs, independent labels, proposal logs, every
timing repetition, and the separate memory profiles.

The comparison used:

- 60 fresh lists at sizes 20, 28, and 36, with no sorted-list overlap with the
  earlier pilot and no duplicates within the new study.
- 54 structured lists spanning unrelated exceptions, repeated exceptions, and
  a deliberately constructed exchange gadget; plus six unstructured controls.
- 180 targets: 60 planted YES, 60 unconditioned uniform middle-range targets,
  and 60 middle-range targets conditioned on passing the modular screens and
  being NO. Both latter cohorts happened to be entirely NO in this sample.
- Seven methods, with three shuffled-order timing repetitions: 3,780 runs.
- Four predeclared cases for separate Python allocation tracing: 28 profiles.

The conditioned NO cohort passes range, gcd, and reachable-residue checks modulo
8, 10, 16, and 32. Every planned list yielded such a target, with no missing
slots. Conditioning defines the cohort; it does not give an unconditional
average-case statement.

All 3,117 completed timing answers agreed with independent full half-enumeration
labels. The remaining 663 runs reached declared limits. All 24 completed memory
answers also agreed; four memory runs were unresolved. Every returned indexed
witness was valid. No case changed completion status across timing repetitions.

The 16 independent test groups passed before the freeze. They check exact
answers, core optimality, indexed reconstruction, selection validity, modular
filters, resource handling, and censor-aware paired summaries.

## Smaller support did not repay these selectors

The two alternatives preserve maximum core cardinality:

1. Scan verified one-swap cores and choose a multiplicity-cap-ranked candidate.
2. Construct up to four candidate supports, choose the smallest actual support,
   and reuse its representatives.

All scanning, rejected checks, and losing probes are included in timing.

Both selectors reduced $M$ on 18 of the 54 structured lists. These were the
exchange-gadget lists, whose design was declared before evaluation. On those
lists, selecting the alternative core reduced the exceptional support from
$k+3$ to $k+1$ sums.

The selectors won **zero of 162 structured target cases** against the simple
greedy-core distinct-sum method. Across all completed paired cases:

| Selector | Paired cases | Faster than simple core solver | Median selected / simple total time |
|---|---:|---:|---:|
| Multiplicity cap | 168 | 5 | 9.034 |
| Exact support probes | 162 | 0 | 9.211 |

The cheap selector's five wins occurred on unstructured 20-item controls where
it chose the same core and the same $M=262144$ as the simple method. They do not
demonstrate a benefit from selecting a better decomposition.

Median selection time was about 1.91 ms for multiplicity ranking and 2.38 ms
for exact probes. Median query time among completed cases was about 0.10 ms.
These medians use each method's completion set and cannot be subtracted as a
paired decomposition of the median total; they nevertheless identify the
dominant measured work.

The [selection analysis](SELECTION_THEORY.md) explains the risk. Including
initial sorting and pool setup, core discovery, selection, and residual search
have a bound depending on every probed support:

$$
O\!\left(
n\log(n+1)
+mk\,n\log(n+1)
+k\sum_{j=1}^{b}M_j
+(m+1)\min_j M_j
\right),
\qquad b\le4.
$$

The winning $M$ alone does not describe its runtime.

## Comparison with ordinary exact methods

The simple distinct-sum core solver completed 168 of 180 cases, beat bounded DFS
on 36 of those matched cases, and beat the fastest feasible elementary baseline
on 31. Its median paired time ratio to that fastest baseline was 1.899.

On the 54 structured conditioned-NO cases, it beat the fastest baseline on 10;
the median ratio was 2.483. The two selectors beat that baseline on none.
These results do not establish a general speed advantage for explicit core
discovery over ordinary bounded search.

Meet-in-the-middle completed every case, including the large-distance controls
on which other methods reached limits. The deletion distances of the controls
were 18, 26, and 34. Their unresolved outcomes are part of the result, not NO
answers or evidence of an intrinsic hardness lower bound.

Bitset DP was feasible and completed on 25 cases under its declared width cap.
It is a decision-only baseline in this implementation. Matched comparisons keep
its feasibility limits visible.

## Memory confirms that representations have a cost

The separate memory pass measures new Python-traced allocations, excluding
already-existing inputs, process RSS, allocator retention, and tracing metadata.
It disables time limits while keeping work/state/bitset caps.

On the predeclared 20-item unstructured NO case:

| Method | Peak traced MiB | Profiling outcome |
|---|---:|---|
| Simple distinct sums | 34.288 | NO |
| Gray-code exceptional selections | 0.0058 | NO |
| Multiplicity selection | 34.295 | NO |
| Exact support selection | 67.494 | Unresolved: work limit |
| Bounded DFS | 24.767 | NO |
| Meet-in-the-middle | 0.243 | NO |

On the three structured profile cases, memory was much smaller. Those four cases
are a predeclared diagnostic subset, not a general memory ranking.

![Frozen comparison of selection cost, conditioned NO search, and memory](results/prospective_20261024/comparison.png)

## Implication for the new note

The note now has a concrete theoretical and experimental story:

> Structural distance gives an explicit route from exponential subset choices
> to a provably polynomial regime, including discovery of the tractable core.
> Residual support can sharpen exception count. However, improving the support
> is computationally useful only when the discovery and representation costs
> are smaller than the work avoided.

The immediate practical baseline should remain the simple greedy-core solver
alongside bounded DFS and MITM. The present one-swap selectors are not supported
as practical improvements on this sample.

Further work should target cheaper recognition or a stronger structure that
removes substantially more unresolved work. Any new selector should be assessed
on new frozen inputs; this cohort has now been inspected. Adaptive recognition
and a second kind of core remain untested directions.
