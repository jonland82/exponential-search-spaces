# Experiment 01: root aggregate checks help; repeated acquisition does not pay

October 28, 2026. The first structural-geometry experiment and its post-hoc
budget-sensitivity diagnostic are complete. Earlier studies, model defaults,
papers and interactive plots are preserved. No ML is fitted in this experiment.

## What was frozen and tested

The detector discovers an exact w=M*p+r representation from at most 24 data-only
candidate bases. It receives weights/target only, never a planted base or family
label. Signed residual bounds constrain the integer aggregate q=sum(p_i*x_i).
An empty q interval proves NO. Otherwise a bounded exact two-coordinate bitset
DP supplies YES witnesses or an exhaustive NO. Caps/deadlines return unresolved.

The pre-generation freeze protects 21 source/protocol files, including reused
Paper V/VI primitives, and excludes 1,194 prior normalized weight lists.
Fresh generation supplies 108 lists and 324 targets at n=20,28,36 across nine
families. Raw generator metadata is saved for audit only. Independent full-half
enumeration supplies exact truth for every target.

All four policies share exact reduction, gcd normalization, native bitset /
superincreasing enumeration / memoized DFS / MITM fallbacks, resource caps and
index lifting. The DFS accounting adapter is used by every policy and matches
the original native traversal when callbacks are disabled. All online detection,
checking, logging, fallback and returned-witness costs are paid.

## Prespecified results and the schedule limitation

| Policy | Deterministic 32L completions | Original live median, 50ms | Live range |
|---|---:|---:|---|
| Shared portfolio | 240 | 121 | 120-121 |
| Root detection without reuse | 236 | 121 | 121-121 |
| Root exact geometry | 287 | 244 | 244-245 |
| Selective root/internal geometry | 270 | 245 | 245-245 |

Root checking improves the prespecified live completion endpoint by a
repeat-average 123.67 cases, conditional base-list bootstrap 95% interval
[101.65,145.34]. This is a strong result for this constructed sample and fixed
schedule, not a general algorithmic speedup. Median capped total live time is
10.497 seconds for portfolio and 4.282 for root geometry, but capped totals mix
different completion sets and censored runs. On 119 cases both finish in every
repeat, the median portfolio/root time ratio is 0.919: the root policy adds
overhead to many already-easy cases rather than winning universally.

The important limitation is visible in the native attempt traces. With the
original live safety work cap of 2,000,000, early superincreasing enumeration
can consume the entire 50ms deadline. Neither DFS nor MITM is reached in any
original live run, even for inputs where a later method would work well.
Consequently the large live completion difference is partly schedule-sensitive
and does not show an advantage over a well-tuned modern portfolio.

Original live geometry produces 144 root YES and 309 root NO events across
three dependent repeats, with no internal certificates. Under the separate
deterministic 32L pass, repeated checking produces 12 internal YES and 363
internal NO events but finishes 17 fewer cases than root-only checking.
Genuine subtree resolution therefore does not establish net efficiency.

## Post-hoc diagnostic: keep the original 32L cap alongside the live deadline

After observing starvation of later methods, one separately recorded diagnostic
uses the already specified deterministic 32L allowance plus the same 50ms
deadline. Detector candidates, check gates, thresholds, native algorithms and
the original frozen evidence remain unchanged. Inputs have already been
inspected, so this is descriptive sensitivity analysis, not a new prospective
test or a replacement primary endpoint. Its source/config were hashed before
these additional timings.

| Policy | 32L + 50ms median completions | Range |
|---|---:|---|
| Shared portfolio | 219 | 219-219 |
| Root detection without reuse | 219 | 219-220 |
| Root exact geometry | 284 | 284-284 |
| Selective root/internal geometry | 270 | 270-270 |

The root route retains a 65-case descriptive median advantage over portfolio
when later methods can run. Portfolio reaches DFS in 648 and MITM in 145 of
the 972 case/repeat runs. Selective checking now produces 36 internal YES and
1,089 internal NO events across repeats, but still finishes 14 fewer cases than
root-only. This supports the root shortcut while arguing against the present
repeated-acquisition policy. It does not settle the best portfolio schedule or
whether a different internal-check policy would help.

See the [sensitivity report](results/01_large_base_20261028/sensitivity_32L_live/REPORT.md)
for all counts and provenance. Its bootstrap values are conditional reuse, not
independent confirmatory evidence.

## Where the original live gain occurs

| Family, 36 targets each | Portfolio | Root geometry |
|---|---:|---:|
| Large base | 7 | 36 |
| One outlier | 5 | 29 |
| Multiple outliers | 6 | 16 |
| Near equal | 4 | 36 |
| Progression | 11 | 36 |
| Few values | 16 | 19 |
| Coverage | 36 | 36 |
| Superincreasing | 36 | 36 |
| Random wide | 0 | 0 |

These are median totals over repeats. Random-wide failure is a statement about
this capped schedule, not intrinsic hardness, and illustrates the schedule
limitation above. The constructed large-base and near-equal families deliberately
expose the new route. Their success is not a distribution-free coverage claim.

## Memory, geometry and validation

The first unperturbed n=20 list is plotted in exact aggregate/residual coordinates:
[PNG](results/01_large_base_20261028/aggregate_geometry.png),
[PDF](results/01_large_base_20261028/aggregate_geometry.pdf),
[coordinates/provenance](results/01_large_base_20261028/geometry_plot.json).
The planted target has one admissible integer q; the fractional-band target has
none. This is a direct arithmetic projection, with no PCA, trained embedding
or outcome-based detector selection. Both plotted coordinate sets are complete.

Thirty-two separate fixed-case/work-budget allocation profiles have maximum
Python-traced peaks of 3.116 MiB portfolio, 3.118 detection-only, 3.118 root,
and 0.289 selective. These profiles include different completion outcomes;
they are not a matched-success memory ranking and are not process RSS. Logical
history bounds and actual traced allocations are saved separately.

All 12 new unit tests and all 66 relevant existing tests pass. The primary audit
checks every completed answer against independent exact truth, every returned
witness, 4,355 saved geometric events, 1,296 deterministic work replays, all
32 allocation profiles and source/input/artifact hashes. The additional 3,888
live sensitivity runs pass answer/event/provenance checks. Original live plus
work runs total 5,184; these are repeated measurements of 324 targets on 108
base lists, not thousands of independent inputs.

## Next evidence needed

The useful result is a paid exact root-solving route for these structured
families. Its incremental value over all five existing certified-core queries
is not established: the shared portfolio did not acquire/reuse those five
certificates, and some controls (notably progressions) already have such routes.
The next independent comparison should
freeze a schedule that gives later fallback methods time, include direct MITM
and existing five-core reuse controls, and evaluate on fresh lists. Root-only
geometry is the candidate to carry forward. Repeated discovery and any learned
gate must separately earn their cost; neither is justified by this study alone.

This bounded detector/DP is an elementary specialization of established
large-base/decomposable-knapsack ideas. No new universal complexity bound,
hardness certificate, state-of-the-art claim or paper revision is made.

Evidence: [protocol](experiments/01_large_base/PROTOCOL.md),
[theory](THEORY.md), [literature](LITERATURE.md),
[saved experiment guide](results/01_large_base_20261028/README.md),
[primary measured report](results/01_large_base_20261028/REPORT.md),
[primary validation](results/01_large_base_20261028/VALIDATION.json),
[sensitivity validation](results/01_large_base_20261028/sensitivity_32L_live/VALIDATION.json).
