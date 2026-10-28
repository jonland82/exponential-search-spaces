# Experiment 01: blind large-base discovery and exact aggregate geometry

October 28, 2026. Freeze this protocol, sources and configuration before fresh
generation. Preserve Papers I-VI and every earlier experiment. This is a local
freeze and exploratory efficiency comparison, not external preregistration.

## Question

Does bounded discovery of w=M*p+r pay for itself through exact aggregate checks?
Does repeating checks inside DFS improve on root-only recognition? Literature
motivates this family; our generated instances are not claimed to satisfy
every hypothesis of known branch-and-bound lower bounds. No ML is fitted here.

## Exact methods and controls

All policies apply the same target reduction, gcd normalization and portfolio:
bitset DP, superincreasing exception enumeration, memoized include-first DFS,
then meet-in-the-middle. Native solvers are reused from Paper V. DFS is copied
with a common shared-budget adapter and optional checkpoints; without callbacks
its native work, decisions and traversal match the original and are tested.
Every policy uses the adapter. All sort, detection, checking, solver, logging
and returned-witness costs occur within the total clock. Inherited bitset YES
decisions need not have witnesses; all returned indexed witnesses are verified.

Four policies:

- portfolio: shared exact pipeline, no geometric discovery.
- detect_only: discover root geometry and pay for it, but do not use it to answer.
- root_geometry: discover and try an eligible exact root check, then fallback.
- selective_geometry: same root action, then selectively try checks during DFS.

The detector sees weights and target only, never planted parameters, family,
oracle answer or generator metadata. After gcd normalization it proposes the
minimum and median distinct weight, eight nearby powers of two from the maximum
weight's bit length, and the four largest
consecutive distinct-weight gaps divided by 1..4; round divisions to nearest
integer and remove duplicates. Keep at most 24 candidates >=2. Nearest-integer
quotients define exact signed residuals for every candidate. Pick an empty q
range first, otherwise minimum estimated prefix-history bits, residual width,
then base. The score is target-dependent and need not find the optimal base.

Checks use the exact q bounds and two-coordinate bitset DP in THEORY.md. Caps:
2,000,000 DP logical bits; 64,000,000 prefix-history logical bits; at most four
feasible q values; at most 12,000 charged update/query steps per check. Local
check interruption leaves remaining fallback budget available and cannot prove
NO. Shared deadline/work exhaustion returns unresolved. At internal checkpoints
also require at most two feasible q values and residual span <= base; checkpoints
occur every four DFS levels below the root with >=8 items remaining, at most
16 per solve. Root checks are not repeated at DFS depth zero.

## Fresh data

Seed 760281028. Sizes 20,28,36; four replicates; nine families: large_base,
large_base_one_outlier, large_base_many_outliers, near_equal, random_wide,
superincreasing, coverage, few_values and progression. Thus 108 base lists,
three targets each, 324 cases. Exclude gcd-normalized sorted-list overlap with
all prior list files found under the existing experiment packages and this
package at freeze. Preserve hashes and the complete exclusion set. No outcome-
conditioned rejection; proposals are rejected only for duplicate lists.

Large-base families have p_i uniformly from 1..6 and r_i from -8..8, with
M bit scale 24 or 32 and power-of-two/arbitrary bases crossed by replicate.
Outlier families replace one or ceil(n/8) items by distinct, larger weights
above the original maximum plus (j+1)*M, with independent offsets drawn uniformly
from [floor(M/4),floor(2M/5)]. They deliberately stress root
representations while allowing remaining branches to recover structure; no
operational solver receives these details. Near-equal controls use their own
large random base and residuals -1024..1024. Other controls use the existing
Paper VI generators, unchanged, with no replacement items.

Targets are a planted random subset, an unconditioned uniform 30%-70% target,
and a fractional-band target: M*floor(sum(p)/2)+floor(M/2) for large-base and
near-equal lists, otherwise total//2+1. This target rule uses generator metadata
for data construction only and does not assert NO; independent exact truth is
computed for every case and never supplied to a timed solver.

## Budgets and endpoints

One deterministic work pass: max_work=32*encoded_input_length, no time deadline.
The same shared counter pays preprocessing, discovery, exact checking and native
fallback work. Counters are heterogeneous instrumentation, not uniform CPU/bit
operations; integer widths and sorting costs are bounded and separately tracked.
Three live timing repetitions use 50ms per case, max_work=2,000,000 safety cap,
32,768 search states and a 1,000,000-bit ordinary bitset cap. Policy order is
seed-shuffled within each case/repeat; cases are also shuffled. All policies
receive identical per-case caps. Cooperative overshoot is saved; late answers
are excluded. Training/loading, generation, oracle calculation, serialization,
plots and independent audit are outside the solver clock.

Primary endpoint: root_geometry minus portfolio live completions, averaged over
the three repeats, with a conditional 95% percentile interval from 1,000
base-list bootstrap draws. Secondary: selective versus root, detection overhead,
work completions, family/size results, capped total time, and per-input timing
ratios restricted to jointly completed cases. Do not count fast unresolved runs
as successful speedups. Timing repeats are not independent data; targets share
lists. Intervals do not include generator-selection uncertainty and secondary
comparisons are not multiplicity-adjusted.

Retain all original inputs, oracle masks, target rules, source/input hashes,
per-policy outcomes, geometry descriptors and exact-check events, native attempts,
discovery/check/solver phase times, logical DP/search-state peaks and overshoot.
Node/assignment coverage is not total work saved. Report root and internal YES
and NO resolutions separately so whole-instance recognition cannot masquerade
as an internal-pruning advantage.

Separately profile Python-traced peak allocation for the first n=36 list of
large_base, large_base_one_outlier, random_wide and coverage, using planted and
fractional-band targets under each policy: 32 profiles, deterministic work caps,
no live deadline. These timings are not CPU comparisons and memory is not RSS.

Audit decomposition identities, signed DP and witness logic, source/data hashes,
all completed decisions against independent half enumeration, returned witnesses,
every saved exact event and deterministic work replay. Produce an illustrative
(q,s) plot from the first n=20 unperturbed list's planted/fractional targets,
with exact reachable coordinates capped at 250,000 states and clear disclosure
if a diagnostic plot is partial. Plot construction is outside online costs.
Stop with checked findings; do not retune on this sample or change the papers.
