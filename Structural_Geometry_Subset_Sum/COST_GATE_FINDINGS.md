# Cost-aware checking: fewer DP calls, no demonstrated completion gain

October 28, 2026. [Overview](experiments/03_cost_aware_gate/README.md) ·
[Frozen protocol](experiments/03_cost_aware_gate/PROTOCOL.md) ·
[Saved report](results/03_cost_aware_gate_20261028/REPORT.md) ·
[Reproduction](results/03_cost_aware_gate_20261028/README.md).

The cost-aware gate avoided nine of 34 eligible DP calls on fresh inputs.
It preserved the completion count but did not beat the simple rule on the
primary shared-budget endpoint. Its small counter saving did not transfer to
a consistent live-time improvement. The experiment does not justify replacing
the simple gate.

## What was tested

A new weighted logistic model learns the sign of paired **net censored-work
savings**, rather than the earlier portfolio-completion label. Development
inputs are solved both with and without the geometric DP. Exact completed runs
contribute their actual work; unresolved runs contribute their full 32L allowance
to the training objective. Weight each non-tied example by the absolute saving
or waste. Separate calibration lists select the actual policy's threshold,
including paid scalar inference. The selected threshold is 0.25.

The same 19 features are acquired at eligible decision points. This is a
root-only gate **after discovery**; it cannot avoid acquiring geometry. All
geometry-acquiring controls share exact aggregate-gap answers. All policies
first reuse the original five exact cores. Fallback splits remaining work and
time between bitset, DFS and MITM; an additional direct-MITM control uses its
whole fallback allowance on MITM.

There are 192 training, 96 calibration and 192 test lists, with three targets
each: 576/288/576 cases, 1,440 total. Sixteen families include the earlier
twelve, three large-base families and a new wider-aggregate family. Sizes are
24,30,36; all 1,572 prior normalized lists and cross-split duplicates were
excluded. Sources/configuration were frozen before development generation;
the fitted model and threshold were frozen before test generation.

**Effective decision sample is small:** only 28 eligible training cases survive
the shared exact shortcuts, with 14 beneficial and 14 harmful checks. Calibration
has 11 eligible decisions. Fresh test data have 34 eligible decisions from
29 independent lists. Total corpus size overstates the information available
to train this particular gate.

## Individual work results

All costs include online acquisition, inference, exact checks, fallback and
verification. Counts below use the same 32L per-input work allowance.

| Policy | Exact completions / 576 | DP calls | Capped cost | Actual work |
|---|---:|---:|---:|---:|
| Lean never: no discovery | 431 | 0 | 16,274,475 | 15,719,129 |
| Matched never: discovery/gap only | 461 | 0 | 13,417,540 | 13,072,957 |
| Always eligible DP | 461 | 34 | 13,364,119 | 13,025,492 |
| Simple geometric rule | 461 | 34 | 13,364,119 | 13,025,492 |
| Learned cost-aware gate | 461 | 25 | 13,361,360 | 13,016,844 |
| Direct MITM control | 434 | 0 | 15,129,245 | 11,385,152 |

The simple rule admitted every eligible test decision, so its deterministic
trace matches always checking in this sample. The learned gate saves 2,759
capped-cost units (0.0206%) and 8,648 actual-work units (0.0664%) relative to
simple. Its paired whole-list-bootstrap 95% interval for capped-cost difference
is [-45,933,+34,050], spanning zero. These are heterogeneous counter units,
not CPU/bit operations or uncensored runtimes.

Secondary decision diagnostics: the gate checks 18 of 21 beneficial cases and
seven of 12 harmful ones; it skips three beneficial, five harmful and one tied
case. Thus fewer calls alone do not show consistently better decisions.

## Paid shared-budget results

Work and live pools include every online phase. Each row reports the median
over three paired arrival orders on the same fresh sample.

| Endpoint | Cohort | Budget fraction | Matched never | Always | Simple | Learned |
|---|---|---:|---:|---:|---:|---:|
| Work | Large base | 20% | 68 | 68 | 68 | 68 |
| Work | Earlier families | 20% | 145 | 146 | 146 | 146 |
| Work | Large base | 50% | 128 | 128 | 128 | 128 |
| Work | Earlier families | 50% | 333 | 333 | 333 | 333 |
| Live | Large base | 20% | 72 | 79 | 80 | 75 |
| Live | Earlier families | 20% | 176 | 175 | 179 | 179 |
| Live | Large base | 50% | 118 | 121 | 121 | 120 |
| Live | Earlier families | 50% | 314 | 315 | 314 | 314 |

**Primary result:** at 50% work pools, learned and simple both finish 461 cases
in each repeat: difference zero. All inputs were attempted under both policies
at this budget; the endpoint had little queue-throughput headroom. The tighter
20% work pools also give no learned completion advantage. Live results do not
rescue the gate: it finishes fewer large-base cases than simple at both budgets.
These timings and repeated orders are descriptive, not independent new samples.

The saved report also includes lean and direct-MITM controls. Direct MITM is
stronger on some tighter earlier-family work pools, while geometry is stronger
on large-base pools. This reinforces the need for meaningful fallback/portfolio
controls rather than treating a single schedule as universally best.

## Interpretation and next useful evidence

The implementation successfully trains on the decision's own cost and avoids
some wasteful calls. Its marginal benefit is tiny after existing exact shortcuts,
with too few eligible examples to support a strong learned policy. Exact
geometry remains useful, but this experiment supplies no reliable additional
ML efficiency gain.

A further gate study should obtain more eligible training decisions through
input-structure-based sampling, retain broad fresh evaluation, and use budgets
with actual throughput headroom. A separate earlier gate could try to avoid
discovery/feature acquisition itself; that is a different decision with new
cost labels, not a conclusion established here. There is no new general
complexity bound, default-model change or manuscript revision.

## Validation

All 89 relevant tests pass: 23 structural-geometry, 50 learned-classifier and
16 original structural-distance tests. The successful
[audit](results/03_cost_aware_gate_20261028/VALIDATION.json) checks all 480 lists /
1,440 exact truths, 864 paired development action labels, weighted refitting,
calibration threshold replay, scalar/sklearn parity, source/input/model/result
hashes, all 3,456 fresh counter-run replays, exact certificates/witnesses and
144 paid pools including 72 deterministic pool replays. Live late answers are
excluded. The reused certificate auditor also matches Experiment 01's frozen
source. Earlier frozen evidence is preserved.
