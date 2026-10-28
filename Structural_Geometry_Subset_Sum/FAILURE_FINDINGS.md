# Which cases are still unresolved?

October 28, 2026. Post-hoc diagnosis of the latest 576-case test set. These
are failures of the actual exact solver under its individual 32L work cap,
not classifier errors or inputs left unattempted by a pool.
[Saved analysis](results/03_cost_aware_gate_20261028/failure_analysis_20261028/REPORT.md).

## Concentration of failures

The learned policy leaves 115/576 unresolved. Every 24-item case completes;
48/192 cases fail at n=30 and 67/192 at n=36. Failures include 52 true YES and
63 true NO cases, including 42 planted-solution targets. This is not exclusively
a problem of certifying impossible targets.

| Main family | Unresolved / 36 | What these inputs contain |
|---|---:|---|
| Random wide weights | 24 | Large irregular weights without a recognized compact core. |
| Two scales | 23 | Small weights mixed with large weights, sometimes with replacements. |
| Two progressions | 23 | Two different arithmetic structures, often further perturbed. |
| Large base with several outliers | 14 | A narrow geometric core spoiled by four or five weights. |
| Filtered modular | 13 | Targets for which the initial range/parity/gcd shortcut is insufficient. |
| Near equal | 12 | Every failure has roughly a quarter of the weights randomly replaced. |

The remaining six failures are four perturbed progression cases, one
single-outlier large-base case and one wide-aggregate case. Clean large-base,
superincreasing, coverage, few-value, small-support, interval-union and block-pair
families have no failures in this sample. Family labels describe generators,
not guarantees of tractability for every perturbed input or target.

## What stops the algorithms

Every one of the 115 failures hits the ordinary bitset's width cap and DFS's
work cap. MITM then hits a state cap in 58 cases and a work cap in 57.
For irregular halves, 15/18 items can produce up to 32,768/262,144 different
sums; the implementation permits only 32,768 simultaneous states, including
update snapshots and the other half. The n=30/36 failure concentration is
therefore strongly tied to the experimental resource limits.

114 failures exceed the geometric DP area and history caps. Only one reaches
an eligible DP decision; its always-checking control is also unresolved.
Consequently improving this gate's predictions cannot fix most of these inputs.
The existing structural feature values also miss useful alternative cores:
their minimum among failures is 15-29 deletions, median 27. These are computed
features, not proof of optimal deletion distances for the heuristic coordinates.

There is some routing headroom: direct MITM already solves 15 of the learned
policy's misses under the original allowance. Nevertheless, 100 inputs remain
unresolved under every original policy.

## Diagnostic: increase resources, keeping the exact method

On those same 115 inspected failures, direct MITM, including existing reduction,
feature and five-core costs, gives:

| Allowance | State cap | Completed / 115 |
|---|---:|---:|
| Original work allowance | 32,768 | 15 |
| Original work allowance | 1,048,576 | 17 |
| 16 times original work | 32,768 | 20 |
| 16 times original work | 1,048,576 | 115 |

These runs have no live deadline and deliberately spend more resources. They
diagnose the limits; they are neither an algorithmic speedup nor independent
confirmatory evidence. All returned answers/witnesses agree with the parent's
independently audited exact truths. No intrinsic hardness claim follows.

## A concrete structural opening

For all 14 missed many-outlier cases, an **input-only** diagnostic removes the
four or five largest absolute residuals from the already discovered projection.
Those weights account for more than 99.9% of residual width. The remaining span
falls from roughly 639,000-12.5 billion to 130-794; its full geometric DP needs
only 43,194-257,665 logical bits, below the original two-million-bit area cap.

This suggests extending the framework's exception-to-core idea to geometric
cores. If $E$ contains the exceptional weights and $K$ the retained core, test

$$
\sum_{i\in K}w_ix_i=t-\sum_{i\in E}w_ix_i,
\qquad |E|\in\{4,5\}.
$$

Build the core's reachable $(q,s)$ representation once, then query the 16-32
shifted targets from exceptional assignments. The accounting target is

$$
T\le F+C_{\rm core}+2^{|E|}Q,
$$

where $F$ includes blind decomposition and exception discovery, $C_{\rm core}$
is exact core construction, and $Q$ includes membership/witness work per query.
Repeatedly rebuilding DP for every assignment could erase the advantage.

The current diagnosis establishes compact-core candidates, not an implemented
efficient solver: witness history, construction, exception enumeration and
verification still need to earn their cost in a fresh matched experiment.
Allowing up to nine removals finds compact full-core candidates for 29/115
failures; random-wide, two-scale and two-progression misses need other ideas
under this particular single-base detector. This is a more specific research
target than further tuning a gate for checks that cannot currently run.

## Evidence

The [post-hoc protocol](results/03_cost_aware_gate_20261028/failure_analysis_20261028/protocol.json)
pins the parent inputs and analysis source before probes. Saved artifacts include
all 576 per-case descriptors, 345 exact cap-probe runs, subgroup summaries,
source copy, hashes and a successful answer/witness consistency record.
The original experiment, trained models and manuscript are unchanged.
