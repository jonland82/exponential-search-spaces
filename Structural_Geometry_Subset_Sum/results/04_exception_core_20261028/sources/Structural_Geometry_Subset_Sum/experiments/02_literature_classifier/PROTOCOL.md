# Experiment 02: literature-inspired inputs to logistic regression

October 28, 2026. New experiment; preserve all earlier frozen sources, models,
data and papers. Locally freeze this protocol, source hashes, generators,
features, model settings and endpoints before generating development inputs.
Freeze fitted models before generating test inputs. No tuning on test outcomes.

## Question and features

Does actual instance geometry add useful information beyond the existing five
structural and ten numerical inputs? The earlier prototype features describe
geometry in that original feature space. Here use blind decomposition of the
exact reduced target kernel, w_i = divisor*(M*p_i+r_i), following the existing
24-candidate detector without supplying the generator's planted M.

Append these three features: log1p((Rplus-Rminus)/M), log1p(Nq), and
log1p((qhigh+1)*(Rplus-Rminus+1)). Rminus is the sum of negative residuals,
Rplus the sum of positive residuals; qlow=max(0,ceil((t-Rplus)/M)),
qhigh=min(sum(p),floor((t-Rminus)/M)), and Nq=max(0,qhigh-qlow+1).
The projected area is precisely the existing detector's dp_bits, clamped at zero.
No descriptor is available when discovery returns none; encode its three values
as zero and record availability separately. Discovery includes gcd normalization.

The third model appends exact additive doubling |A+A|/|A| on DISTINCT kernel
weight values, including a+a. Duplicates do not enter the denominator repeatedly.
It is not the size of the set of reachable subset sums. Empty A has value zero.
Compute this separately, with its own measured time and declared O(|A|^2) charge.

These are our proposed operational descriptors motivated by decomposable
knapsack geometry (Krishnamoorthy and Pataki, arXiv:0807.1317) and small-doubling
subset sum (Randolph and Wegrzycki, ESA 2024, doi:10.4230/LIPIcs.ESA.2024.96).
The papers do not prove these features predict this portfolio's runtime.
See the package literature map. No full lattice reduction or geometric DP here.

## Data, fitting and label

Seed 770281028. Sizes 24,32,36; the twelve existing prospective-study families
plus large_base, large_base_one_outlier and large_base_many_outliers.
For each family/size generate two training, one calibration and three test
lists: 90/45/135 lists, three targets each, 270/135/405 cases.
Old families randomly choose zero or round(n/4) replacements; structural
families use the existing generator with a randomly chosen variant 0..3,
covering power-of-two/arbitrary 24/32-bit bases. Selection is independent of
split. Targets are planted, unconditioned uniform middle, and fractional-band
for planted decompositions (otherwise total//2+1). Never reject by truth or
completion. Exclude all normalized sorted prior lists and duplicates across
every new split. Keep each list's targets together. Independent half enumeration
provides exact truth; generation metadata never enters feature extraction.

Refit baseline15, geometry18 and doubling19 on the SAME expanded training
lists. This is a controlled feature comparison, not comparison against an
unchanged earlier fitted model. StandardScaler + LogisticRegression(C=1,
max_iter=2000,random_state=630251026). Sigmoid calibration on clipped raw logits
uses separate calibration lists with the same fixed logistic settings. Train
on all training cases, matching the previous whole-instance classification task.
No feature selection, search over C, or learned policy thresholds.

The label remains completion of the original exact portfolio within 8L
heterogeneous work units, under its unchanged memory caps. Features and reuse
are excluded from label construction and paid separately in operational tests.
This label is neither reachability nor benefit of running the geometric DP.

## Endpoints and correctness

Two co-primary differences: geometry18 minus baseline15 Brier, and doubling19
minus baseline15 Brier, on test cases STILL UNRESOLVED after exact reduction,
the original five zero-deletion core queries, and aggregate-gap NO checks.
Thus already-proven answers receive no ML credit. Save all-case and family
metrics, calibration, log loss, accuracy, unresolved-class precision/recall/AP.
Use 2,000 paired list-bootstrap draws with fixed seed, keeping all targets
together; report 95% and Bonferroni two-comparison 97.5% intervals conditional
on fixed fits. No retraining or generalization to unseen families is claimed.
These small mixtures are exploratory, and subgroups are secondary.

Counter and separately measured live prioritization pools: two cohorts
(legacy families / large-base families), 20% and 50% total nominal budgets,
three paired arrival orders, four policies, seeded randomized measurement order.
All policies pay the identical reduction, original feature acquisition and five
core reuse. cheap15 uses baseline15 without geometric discovery. matched15
pays discovery and uses any exact empty-q-range NO certificate, then uses
baseline15 for ranking. geometry18 has the same exact shortcuts and uses the
three appended features. doubling19 also computes and pays additive doubling.
Geometry18 versus matched15 isolates learned descriptor utility; versus cheap15
includes the cost/benefit of the whole geometric package. Doubling19 versus
geometry18 includes the extra descriptor's acquisition. Nq=0 is always exact
NO for all THREE policies that acquire geometry; do not credit this to learning.

No learned probability discards an instance or certifies NO. The exact fallback
is unchanged. Counter ranking is calibrated completion probability divided by
the fixed 8L allowance; live ranking uses probability, as in previous studies.
Counter pools use stored deterministic reference traces only at the full
allowance; execute any last clipped solve with its actual smaller cap.
Live pools recompute every precheck, feature, inference and solve under an
actual shared deadline, with a 20ms per-instance fallback cap and original work
cap. The final atomic operation may overrun; record overshoot and exclude late
answers. Feature acquisition currently contains the original core query, so
its live phase includes core time; counter phases separate their work charges.
Model fitting/loading and independent truth auditing are offline.

Inference work is 6*k+20 per pending case; discovery pays the unchanged detector
counter plus three transformations; doubling pays sorting scale plus two units
per unordered value pair plus one. These heterogeneous counters are not uniform
bit operations; use the live endpoint for machine-specific practical costs.

Validate source/input/model/data hashes, disjoint groups and excluded prior
inputs, independent exact truths, descriptor arithmetic, reference labels,
refitting/calibration, predictions, subgroup and bootstrap summaries, every
accepted answer/witness, and all deterministic pool replays. Preserve raw live
traces and overshoots. Publish checked findings without changing defaults/papers.
