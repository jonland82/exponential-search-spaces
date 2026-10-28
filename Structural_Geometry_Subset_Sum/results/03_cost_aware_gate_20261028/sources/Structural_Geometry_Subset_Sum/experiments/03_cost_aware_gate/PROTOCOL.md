# Experiment 03: does geometric checking repay its cost?

October 28, 2026. New local freeze; preserve earlier sources, evidence and
manuscripts. Freeze code, configuration, generators and endpoints before
development generation. Freeze fitted gate and threshold before test generation.

## Decision and training target

After exact target reductions and reuse of all five existing zero-deletion
cores, discover aggregate geometry once at the root. Every policy that acquires
geometry uses an empty aggregate interval as exact NO. The learned decision is
only whether to run the bounded exact two-coordinate DP on an eligible,
nonempty representation. It cannot skip discovery, and it is not a branch gate.

For each development input, run matched policies $a=0$ (never DP) and $a=1$
(always DP when eligible) with the same full $B_i=32L_i$ work allowance. Define

$$
C_i(a)=\begin{cases}W_i(a),&\text{if an exact answer finishes},\\
B_i,&\text{if unresolved},\end{cases}\qquad
\Delta_i=C_i(0)-C_i(1).
$$

This is censored budgeted cost, not an uncensored runtime or certified amount
of work saved. Train on eligible training decisions with $\Delta_i\ne0$,
label $y_i=\mathbf1\{\Delta_i>0\}$ and weight $|\Delta_i|$, normalized to mean
one over retained training rows. Ties contain no observed preference and are
excluded. All 19 feature definitions remain those of Experiment 02; acquire
doubling lazily only at an eligible nonempty DP decision. Features and core
reuse are computed online and paid in all matched controls.

Fit training-only StandardScaler + LogisticRegression(C=1,max_iter=2000,
random_state=630251026) using sample weights in the logistic loss. Its score is
cost-sensitive, NOT an ordinary calibrated probability of solving or NO.
If only one nonzero-savings class occurs, explicitly record a constant gate;
if none occur, use constant zero. Do not invent a learned improvement.

On disjoint calibration lists, choose threshold from
$\{0,.1,.25,.5,.75,.9,1.1\}$ minimizing the actual complete learned-policy
sum of capped costs, including inference. Ties prefer the higher threshold.
Threshold zero always checks when eligible; 1.1 never checks. No test tuning.
Fold the fitted scaler and logistic affine transformation offline into 19
coefficients/intercept; scalar online inference must match sklearn to $10^{-12}$.
Charge $6\cdot19+20$ heterogeneous units per learned decision; simple controls
pay one decision unit. Threshold calibration accounts for this extra cost.

## Policies and common fallback

- `lean_never`: original feature/core acquisition, no geometric discovery.
- `never`: acquire geometry, use exact gap certificates, never run DP.
- `always`: run DP for every eligible nonempty representation.
- `simple`: run DP only if $N_q\le2$ and $R_+-R_-\le M$.
- `learned`: run DP iff weighted logistic score exceeds the calibrated threshold.
- `direct_mitm`: original feature/core acquisition, then direct MITM, no geometry.

The four matched geometry policies share original features, discovery, gap
certificates, and all 19 inputs at eligible decision points. Learned inference
is additionally paid. Only the decision to run DP differs. Hard representation
caps remain $HW\le2{,}000{,}000$, history at most $64{,}000{,}000$ logical bits,
$N_q\le4$, and at most 12,000 check work units. Exhaustion returns unresolved.
DP witnesses are lifted to original indices and verified.

The shared fallback is bitset, memoized DFS, then MITM, dividing remaining work
AND remaining live time among remaining methods, carrying unused resources
forward. No superincreasing enumeration stage can consume the whole deadline.
The direct-MITM control receives its whole remaining fallback allowance.
Existing 32,768 search-state and 1,000,000 bitset-width caps remain. All policies
share these exact implementations and prechecks. Native bitset YES may be a
decision without a witness; every completed answer is independently audited.

## Data and costs

Seed 780281028; sizes 24,30,36. Sixteen families: the twelve earlier families,
three prior large-base families, plus wide_aggregate. The latter uses 28-bit
power-of-two/arbitrary bases, quotients 1..32 or 1..128, residual radii 8/64,
with variants sampled independently of split. Earlier generators and random
0/25% replacements are unchanged. Existing large-base variants cover 24/32-bit
bases. Three targets: planted, uniform middle, fractional band for decomposable
families (otherwise total//2+1). No outcome-conditioned acceptance.

Per family/size: four training lists, two calibration, four test; 192/96/192
lists and 576/288/576 cases. Exclude normalized sorted prior lists and all
cross-split duplicate lists. Entire lists, with all targets, stay in one split.
Independent half enumeration gives exact truths. No family/planted metadata
enters the solver or predictor. Only development cases get paired action labels
before fitting. Test inputs are generated after the model freeze.

All online work/time, including feature extraction, discovery, DP, inference,
fallback, witness checking and solver logging, is included. Atomic acquisition
may overrun a cooperative live deadline; late answers do not count. Final
partial counter phases consume remaining allowance before reporting exhaustion.
Offline fitting, loading and independent truth auditing are excluded.
Counters are heterogeneous operations, not uniform bit costs or CPU time.

## Endpoints and audit

Run six policies on every fresh test case under its 32L work cap; save full
phase costs, features, decisions, checker certificates, fallback attempts and
answers. Also compare paired FIFO pools by earlier/large-base cohort, at 20/50%
total nominal allowance, three paired arrival orders, seeded randomized policy
measurement order. All cases are attempted at most once. Work pools reuse
complete deterministic traces only if their full allowance remains; rerun a
last clipped case with its actual smaller cap. Live pools recompute everything
under actual shared time with at most 20ms per case plus the original 32L cap.

Primary endpoint: repeat-average learned minus simple exact completions at
50% work pools, summed across cohorts. Report actual totals and all controls;
three orders on one fixed dataset do not support an independent-repetition
significance claim. Secondary: other pools, individual capped costs/completions,
cost-sensitive predictions, DP successes and separately measured live utility.
Provide 2,000 whole-list bootstrap draws for paired per-case completion and
capped-cost endpoints, conditional on the fitted gate. These intervals do not
apply to the discontinuous shared-pool primary endpoint or include retraining.
No multiplicity-adjusted or general superiority claim from secondary comparisons.

Audit source/input/model/data/result hashes; disjoint groups and exact truths;
every development action pair and cost label; weighted fitting and scalar
parity; calibration threshold replay; every test counter run; all DP certificates
and witnesses; pooled accounting/accepted deadlines and deterministic pool
replay; and reconstructed reports. Keep earlier frozen sources untouched.
