# Paper VI: stages 7-8 frozen-results checkpoint

Historical results checkpoint for the original frozen experiment. The updated
[paper](../notes/06-learned-solvability/Predicting_Subset_Sum_Completion.html)
includes these findings and the separate [branch follow-up](BRANCH_FINDINGS.md),
with a [scoped prior-work audit](LITERATURE.md). The findings below retain their
original claim boundary; the new study does not change this evidence.

October 25, 2026. The fresh prediction comparison and paid practical prioritization
test are complete and validated. Pause before the literature audit and full
manuscript to agree on the scope of the paper's claim.

## What was frozen and tested

Six fitted/calibrated models (three feature arms, logistic and forest) and all
execution sources were hashed before generating any new evaluation weights.
Only development training/calibration lists were fitted. Logistic regression was
the prespecified primary model; forests were secondary. The
[protocol](PROSPECTIVE_PROTOCOL.md) records the design and limits.

There are 144 new base weight lists at n=24,32,38, with four targets each. Each
base problem has an unscaled and jointly scaled weight/target encoding, giving
288 encodings and 1,152 cases. The paired encodings preserve mathematical answers
but change input length, budget and reference bitset applicability. They are not
independent problems. Three new families, prior development holdouts and larger
inputs are reported separately.

All 3,466 completed reference decisions among 4,608 work/time reference runs
agreed with independent half-enumeration labels; 1,142 runs remained unresolved.
The 672 pool experiments comprise 336 counter replays and 336 live timed runs,
with every completed solver decision checked. The audit reproduces all saved
features, predictions, probability metrics and counter-policy traces, checks
source/model/data hashes, and checks paid costs and late-answer exclusions.
All 24 current experiment tests pass.

Evidence: [prediction report](results/prospective_20261025/PREDICTION_REPORT.md),
[priority report](results/prospective_20261025/PRIORITY_REPORT.md),
[full prediction metrics](results/prospective_20261025/prediction_metrics.json),
[policy summaries](results/prospective_20261025/priority_summary.json), and
[standalone overview](results/prospective_20261025/figures/overview.png)
([PDF](results/prospective_20261025/figures/overview.pdf)).

## 1. The primary predictive comparison did not establish an improvement

On fresh unscaled in-distribution inputs, calibrated logistic Brier scores are
0.0715 for five distances, 0.0211 for conventional features, and 0.0266 combined.
The primary combined-minus-conventional difference is +0.0055, with conditional
base-list bootstrap 95% interval [-0.0018,+0.0138]. Lower is better, so this
does not support an added-value claim on the primary predictive endpoint.

Secondary results vary with the shift:

| Cohort | Five | Conventional | Combined |
|---|---:|---:|---:|
| Larger inputs | 0.0958 | 0.0512 | 0.0387 |
| Larger inputs, paired scaling | 0.0907 | 0.1926 | 0.1190 |
| Prior development holdouts | 0.1925 | 0.1786 | 0.0816 |
| Genuinely new families | 0.2071 | 0.1571 | 0.1231 |
| Genuinely new families, paired scaling | 0.2101 | 0.1496 | 0.1857 |

The combined improvement on scaled larger inputs and unscaled prior holdouts
has a conditional bootstrap interval below zero. The other displayed shifted
differences have intervals spanning zero. These are descriptive secondary
comparisons without multiplicity-adjusted significance claims. Forests give
different rankings on some shifts; their full results remain in the metrics.

The combined model therefore carries useful signal in some shifted settings,
but the five distances do not provide a uniform predictive advantage. All
probabilities concern this exact reference portfolio's finite-budget completion,
not an intrinsic probability of polynomial-time solvability.

## 2. The combined policy had a modest measured time-budget benefit

Every live run recomputes exact prechecks, applicable features, full-core queries,
batch inference, ordering and witness checks inside its pool deadline. No feature
work is charged on inputs already solved by exact prechecks. Seven policies use
the same pools and fallback solver; negative predictions never certify NO.

Below are median total completions across three repetitions, summing the eight
separately budgeted cohorts within each repetition before taking the median.
Thus these totals need not equal the sum of the per-cohort medians in the raw
report. Budgets are fixed fractions of total declared per-case allowances,
not fractions tuned from measured solver costs. There are 1,152 encoded cases.

| Live pool time budget | Arrival | Random | Short input | Distance rule | Five + ML | Conventional + ML | Combined + ML |
|---|---:|---:|---:|---:|---:|---:|---:|
| 20% | 664 | 680 | 763 | 794 | 796 | 823 | 836 |
| 50% | 854 | 850 | 856 | 874 | 871 | 865 | 878 |

At the tighter time budget, combined completes 13 more than conventional (+1.6%)
and 172 more than arrival (+25.9%). Repetition totals range 835-836 for combined,
822-825 for conventional and 662-670 for arrival. These are machine-specific
descriptive results on fixed pools, not confidence intervals over new inputs.

The benefit is not uniform: on the unscaled and scaled new-family cohorts,
conventional completes more than combined at the tighter time budget. In the
same-family and larger unscaled cohorts, the distance rule matches five-only ML
and combined. Cheap direct core reuse contributes some of the benefit.

The combined policy includes full-core queries that the conventional policy
does not construct. Consequently its measured gain cannot be attributed solely
to adding five learned inputs. A future matched-acquisition/core-reuse control
would isolate that marginal learning effect. The current distance-rule control
helps distinguish simple structural guidance from learned guidance but does not
provide that full factorial isolation.

All late answers are excluded. The largest observed pool-deadline overshoot was
about 0.44 ms. Cooperative operations can finish late; this is not a hard process
deadline or a guarantee about another machine's timings.

## 3. The work-counter endpoint gives an unfavorable result for structural planning

| Pool work budget | Arrival | Random | Short input | Distance rule | Five + ML | Conventional + ML | Combined + ML |
|---|---:|---:|---:|---:|---:|---:|---:|
| 20% | 541 | 560 | 705 | 379 | 379 | 769 | 374 |
| 50% | 855 | 857 | 873 | 722 | 711 | 887 | 677 |

Up-front structural construction often exhausts the declared counter allowance
before the ordering can be used: combined does so in 30 of its 48 work-pool runs;
five-only and the distance rule do so in 24 each. This is a failure of those
specified policies under those counters, not evidence that the corresponding
mathematical inputs are hard.

The counter units are deliberately explicit but heterogeneous. A bitset operation,
a dictionary entry and a scan are not equal CPU costs. Counter and live results
must therefore remain separate. The live benefit does not erase this unfavorable
endpoint, and the counter result is not a wall-clock speedup claim.

## Interpretation for Paper VI

The supported account is conditional: combining structural distances with
ordinary features can improve prediction under some distribution shifts and can
modestly increase measured time-budget completions in this implementation.
The primary predictive endpoint does not improve, the work-counter endpoint is
unfavorable, and neither the predictive nor practical advantage is uniform.

The [priority theory note](PRIORITIZATION_THEORY.md) separates correctness,
planning-cost accounting and heuristic ordering. The five certified core queries
and residual-search sufficient conditions remain valid independently of learning.
No learned score proves polynomial asymptotic solvability or a worst-case bound.

Recommendation: draft Paper VI as an empirical study of **predictive value and
computation cost of structural features**, preserving the primary and unfavorable
results. Perform the prior-work audit before making novelty claims. Selective
feature acquisition, amortization across targets and the matched core-reuse
control are possible follow-ups; they were not retrofitted onto these test inputs.

Stages 7-8 are complete. Stage 9 (prior-work audit and full manuscript) remains.
