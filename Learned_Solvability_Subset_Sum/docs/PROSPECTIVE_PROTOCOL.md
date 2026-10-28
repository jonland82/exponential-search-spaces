# Frozen evaluation and practical prioritization: Paper VI

Protocol date: October 25, 2026. Local prospective freeze, not external
preregistration. The freeze is executed before any evaluation weights or labels
are generated. Source/config/model hashes reject changes between stages.

## Questions and comparisons

1. Do the five target-aware structural distances add predictive information to
   ordinary features on fresh inputs?
2. Does the combined model improve exact completions under a shared total budget
   after paying for its features, inference, ordering and witness checks?

Three arms: target-aware progression five-vector; the existing ten conventional
features; their 15-input combination. Logistic regression is primary for all
three. The existing forest settings are a prespecified secondary comparison.
No selection is made using new inputs, new labels or new calibration results.

Models train only on the 84 development training lists; sigmoid calibration uses
only the 42 development calibration lists. The models, dependencies and protected
sources are saved and hashed by the freeze. Earlier development test/OOD labels
are not fitted. The constant training success prior is retained as a baseline.

The primary predictive endpoint is paired Brier(combined logistic) minus
Brier(conventional logistic), on fresh unscaled in-distribution inputs. Negative
is better for the combination. Report log loss, calibration, ranking and
unresolved-kernel subgroups as well. Confidence intervals resample base lists
1,000 times, with models fixed; they do not quantify uncertainty from retraining.
Multiple secondary comparisons are descriptive; no multiple-testing significance
claim or universal generalization claim follows.

## Inputs and independence

144 base lists are planned: n=24,32,38; 12 families; replacement fractions 0 and
0.25; two independent seed replicates. Seven families occur in model training.
Near-equal and filtered-modular were development holdouts and remain separate.
Three new families are defined before fresh evaluation:

- **Block pairs:** widely separated pairs (a,a+small_delta), each next base
  larger than the preceding total.
- **Two scale:** half small bounded weights and half random large weights.
- **Two progressions:** two distinct arithmetic-progression blocks at separate
  scales, with independently chosen steps.

Each list receives four target rules fixed in the code: independent fair-bit
planted subset, uniform middle-range integer, odd target below the largest weight,
and uniform low-range integer. There is no rejection by answer or solver outcome.

Encode every base list and its same four targets at scale 1 and scale 2^24+1,
yielding 288 encodings and 1,152 cases. Multiplying weights and targets together
preserves mathematical answers and controls the encoding-size change. It changes
input-length budgets and can disable the reference bitset width allowance. This
is a paired representation test, not arbitrary independent bit-length variation.
Scaled copies are clustered with the base list in uncertainty calculations.

New-family status takes cohort precedence; prior development holdouts next;
otherwise n=38 is larger-size and n=24/32 is in-distribution. Unscaled/scaled
cohorts are distinct. This separates genuinely new families from those the
investigator already inspected in development.

Exclude sorted-list overlap with the earlier pilots/development data and within
fresh encodings. Record every duplicate proposal. Allow at most 32 deterministic
seeded draws per planned base slot; record a missing slot instead of silently
replacing a failed stratum.

## Exact labels and reference cost

Independently enumerate both indexed halves of each base list and preserve YES
witness masks. NO is the result of exhausting independent exact half matching.
Use scaling equivalence for paired encodings and check original-index witnesses.
Destroy half tables before measured solving. No oracle objects or labels are
available to model inference or the exact reference portfolio.

The common work label uses the same positive-weight reduction and exact portfolio
as development, with an 8L work allowance, 32,768 live-state cap and 1,000,000-bit
bitset width cap. L is the documented self-delimiting encoding proxy. Resource
exhaustion means unresolved, never NO. Feature extraction is excluded only from
this common predictive-information label. It is fully paid in the practical test.

Also run the reference three times with a 20 ms per-case cooperative deadline.
These repetitions describe time variability and do not create extra independent
input observations. An operation can complete after a cooperative deadline;
strict late-answer exclusions are applied in the live pool experiment.

## Practical test: identical pools and total budgets

Each cohort is one pool. Run seven policies: seed-shuffled arrival, independently
random order, shortest encoded input first, a simple structural-distance rule,
and the three frozen logistic arms. Repeat three times with matched arrival seeds;
shuffle policy execution order within each cohort/budget/repeat.

Every policy first pays for exact preprocessing of the pool, recording any exact
completions. Learned policies extract features only for unresolved kernels.
The five/combined/distance policies reuse exact zero-deletion core queries and pay
their charges. A cheap exact completion is not credited to ML. Known shortcut
cases are not subjected to feature computation. All policies verify returned
indexed witnesses before counting the answer. Independent oracle cross-checks
are experimental validation outside the measured interval.

Planning scans the full remaining pool, so its entire cost is paid up front.
If planning exhausts the budget, retain only exact completions already obtained.
Predicted failure never discards a case as NO. Each residual instance is attempted
at most once by the same fallback portfolio; unresolved attempts remain unresolved.

### Work endpoint

Pool budgets are 0.2 and 0.5 times the sum of the declared 8L case allowances,
chosen before new data are generated. Instrumented counters have heterogeneous
costs: they are not CPU instructions or uniform bit operations. Conventional
feature cost is a declared 12n+80 scan/statistics scale. Logistic inference costs
6d+20 units for d inputs. Ordering costs a linear shuffle or an m*bit_length(m)
sorting scale. Structural construction and core queries use existing counters.

Learned order is descending probability/declared-case-allowance. The distance
rule uses 2^(-minimum_distance)/allowance. Trace replay charges each phase before
its outputs can be used. Reuse an already measured full-cap reference trace only
when the global remaining work permits that full cap. Otherwise execute the
portfolio with the actual remaining allowance. Pay witness verification too.

### Live time endpoint

Pool deadlines are 0.2 and 0.5 times (case count * 20 ms). Recompute preprocessing,
features, core queries, batch inference and ordering inside each measured run.
Work label predictions rank by probability because per-case time caps are equal.
This transfer from work-completion learning to wall-clock guidance is explicit.
Each solve has the smaller of its 20 ms residual allowance and remaining pool time.

Time includes all online overhead; input loading, frozen model loading, experimental
oracle validation and logging are outside the interval. Return-witness checks
are inside. Features and queries are bounded but not preempted mid-operation;
the solvers check cooperative time limits. Record overshoots, exclude late answers,
and never describe this as a hard process deadline. Machine/load variation is
captured by the three repetitions and phase/overshoot logs.

## Reporting and interpretation

Preserve all inputs, targets, oracle witnesses, probabilities, exact reference
attempts, source/model/config hashes, policy traces, phase costs and late runs.
Report completion medians and ranges for all policies, cohorts and budgets,
including unfavorable results. Repetitions are descriptive, not independent
samples for a significance claim. Prediction quality, practical completion and
the sufficient-condition theory are distinct claims. No new worst-case bound,
learned correctness certificate or proof of polynomial scaling follows.

The immediate deliverable is checked stage 7-8 evidence. The literature audit
and full Paper VI manuscript follow a discussion of these frozen results.
