# Feasibility checkpoint for proposed Paper VI

Historical stage 4 checkpoint. The subsequent accepted comparison and current
stage 6 status are in [DEVELOPMENT_FINDINGS.md](DEVELOPMENT_FINDINGS.md).

October 25, 2026. Stage 4 is complete: first feature implementation, elementary
theory and exploratory pilot. Model training has not begun. The next step is a
discussion of feature 5 and the prediction's target interpretation.

## What is implemented and checked

- Five certified distances; exact minima for superincreasing, fixed-grid coverage
  and at most two values; constructive upper bounds for support and interval cores.
- Exact membership with indexed witness recovery for every selected core type.
- Seven test methods, including independent exhaustive deletion checks, exact
  reachable-set checks and portfolio budget/answer checks, all passing.
- A pilot with 162 lists, 486 targets and 1,944 portfolio runs across nine families,
  sizes 16/24/32, two work budgets, and with/without feature extraction charges.
- All 1,640 completed decisions agree with independent half-enumeration answers.
  The remaining 304 runs are unresolved. All returned witnesses were validated.
  Bitset decisions need not return witnesses, consistent with Paper V.

The [report](results/pilot_20261025/REPORT.md), [summary](results/pilot_20261025/summary.json),
raw JSONL records, configuration, source snapshots and hashes preserve the evidence.
There are 110 distinct five-vectors and no duplicate sorted weight lists.

## Decisions suggested by the evidence

### 1. Keep five coordinates, but clarify coordinate 5 before freezing it

Coverage distance and the implemented interval-union distance have Pearson
correlation 0.989 on these 162 lists. This is sample-specific; it does not prove
redundancy in general. Other coordinates also overlap, notably few-values and
small-support distances (0.884).

The fifth extractor currently supports intervals on the whole-list gcd grid. It
does not support arbitrary arithmetic-progression steps. In the generated dense
coverage inputs it resembles coverage; in sparse large-weight inputs its small
interval cap can admit only a few items.

Recommendation: retain this implementation as a baseline, and evaluate a
progression-aware fifth representation on development data before the final
study. Compare feature ablations rather than assuming five means five independent
signals. A broader representation needs proved bounded construction and recovery.

### 2. Decide whether the prediction averages over targets or represents a target

All five coordinates depend on the weight list. At the tighter 8L budget with
feature cost charged, 45 of 162 lists have both completed and unresolved targets
among their three target queries. Without the feature charge, this occurs on
34 lists. At 32L it occurs on 12 lists for either policy.

The model can still give a valid conditional average over targets. It cannot
assign different probabilities to those targets from this vector. These
differences can include target-dependent budget length as well as search work.

Recommendation: make the primary five-feature experiment explicitly list-based
under a fixed target-sampling rule. Separately compare target-aware features as
a secondary baseline, or discuss redefining the five distances on a safely
reduced target-dependent instance before committing to the experiment.

### 3. Feature construction must repay its cost

| Work budget | Completed without extraction | Completed after extraction charge |
|---|---:|---:|
| 8L | 411 / 486 | 320 / 486 |
| 32L | 455 / 486 | 454 / 486 |

At 8L, extraction alone exceeds the budget on 60 cases, concentrated in small-
bit-length inputs. This reflects the declared operation counters and budget rule;
it is not evidence that those mathematical instances are hard. Median measured
extraction time was about 0.65 ms, with a maximum about 3.03 ms on this run.

This cost-only comparison does not reuse the new certificates for solving and
does not apply any learned policy. A direct certificate query can already solve
some of the easiest cases. Recommendation: reuse certificates, include cheap
exact prechecks, retain end-to-end and solver-only cost views, and use a clearly
defined primary budget plus separate wall-clock analysis in the final study.

### 4. Build a less saturated training problem

At 32L, all n=16 and n=24 targets finish with or without extraction. A constant
success prediction is therefore a strong baseline in those size strata. Before
training, use development data to choose sizes, target rules and resource limits
with meaningful completion variation, then freeze these before fresh evaluation.
No claim of five-feature predictive advantage can be made from this pilot.

## Suggested discussion outcome

Keep five dimensions and the probability-of-budgeted-completion target. Agree on
whether primary predictions average over targets, and whether to broaden feature
5 to progression representations. Then advance to stages 5-6: development data,
simple models, calibration and baselines. The final study, practical prioritization
and Paper VI manuscript remain future work.
