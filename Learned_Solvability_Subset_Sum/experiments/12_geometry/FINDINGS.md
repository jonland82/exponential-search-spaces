# Stage 12: prototype geometry and structural interactions

October 28, 2026. Separate calibrated logistic-regression follow-up. Earlier
frozen models, experiments, interactive plots and manuscript artifacts are
preserved. This study tests whole-input completion prediction and paid pool
prioritization, not the distance<=2 branch gate or branch-level time savings.

## What was added

The baseline retains five target-aware structural distances and ten numerical
summaries. Two new features measure distance to the nearest of three training
centroids per completion class. Ten more features are every pairwise product
between distinct standardized structural coordinates. The four arms have
15 baseline, 17 prototype, 25 interaction or 27 combined inputs. There is no
density or PCA feature in this experiment.

Geometry and classifier fitting use only the original 84 development training
lists / 336 targets. Each list has equal total weight within each prototype
class. Training rows exclude their entire own list when fitting their prototype
features; 42 separate calibration lists fit sigmoid calibration. All models use
the original fixed logistic settings, without new tuning or feature selection.
The refitted baseline reproduces the original frozen model's probabilities.

Models, protocol and sources were hashed before generating 144 fresh base lists
at n=24,32,38, with four targets and paired encodings: 1,152 cases. All 846 prior
normalized lists were excluded. The fixed reference completed 877 encoded cases
and left 275 unresolved. Original/scaled encodings share mathematical answers;
their completion labels can differ. There are only 144 independent base lists.

## Prediction: no overall improvement on the primary endpoint

Fresh unscaled cases: 576 targets, 426 reference completions and 150 unresolved.
Brier score measures squared probability error; lower is better.

| Model | Inputs | Accuracy | Hard precision | Hard recall | Brier |
|---|---:|---:|---:|---:|---:|
| Original baseline | 15 | 89.58% | 83.09% | 75.33% | 0.08220 |
| Add prototypes | 17 | 89.76% | 92.52% | 66.00% | 0.09046 |
| Add interactions | 25 | 88.89% | 80.28% | 76.00% | 0.08375 |
| Add both | 27 | 89.76% | 90.99% | 67.33% | 0.08576 |

The primary combined-minus-baseline Brier difference is +0.00356, conditional
base-list bootstrap 95% interval [-0.01399,+0.01914]. The point estimate worsens
and the interval spans zero; this does not establish improvement or equivalence.
Adding prototypes alone has difference +0.00827 [-0.00920,+0.02378]; interactions
alone have +0.00155 [-0.00295,+0.00585]. These are secondary comparisons.

At threshold 0.5, the combined model removes 13 false-hard flags (23 to 10) but
misses 12 additional unresolved cases (37 to 49). Its one additional correct
classification is not evidence of better calibrated probabilities or solving.
On 349 cases still unresolved after exact reduction and full-core reuse,
baseline Brier is 0.13164 and combined is 0.13831; the overall finding is not
explained solely by inputs already solved through exact shortcuts.

The secondary unscaled in-distribution cohort improves from 0.01703 to 0.01175;
prior-development holdouts worsen from 0.19068 to 0.26349. On new families the
combined score improves descriptively from 0.14688 to 0.11503, with a paired
interval spanning zero. On pooled scaled inputs it worsens from 0.12528 to
0.15039. No multiple-comparison adjustment was made; these subgroup results
do not establish a broadly better model.

Full metrics, probabilities, added features, calibration bins, shortcut subgroups
and conditional intervals are in the [prediction report](../../results/geometric_20261028/PREDICTION_REPORT.md)
and [raw prediction metrics](../../results/geometric_20261028/prediction_metrics.json).

## Paid solving: small descriptive time differences, unfavorable counters

All policies rerun shared exact preprocessing. Learned arms pay for the same
original features/cores, then their own online geometric transformations and
inference. These totals sum separately budgeted cohorts within each repetition
and report the median over three repetitions, across 1,152 encoded cases.

| Policy | Live 20% budget | Live 50% budget | Work 50% budget |
|---|---:|---:|---:|
| Arrival order | 657 | 838 | 848 |
| Pool distance rule | 790 | 860 | 750 |
| Original baseline | 813 | 860 | 687 |
| Add prototypes | 809 | 865 | 655 |
| Add interactions | 808 | 859 | 683 |
| Add both | 813 | 862 | 649 |

At the tighter live budget, combined ties baseline at 813; both ablations finish
fewer cases. At the half-budget endpoint, prototypes finish five more and
combined two more than baseline, but repeat ranges overlap: baseline 857-866,
prototypes 862-867, combined 859-865. These small differences are descriptive
machine-specific observations, not an established general improvement. Three
timing repeats are not three independent input datasets.

Counter accounting remains unfavorable. At half budget, combined completes 38
fewer cases than baseline and exhausts planning in 12/24 cohort-runs versus
6/24. Prototypes finish 32 fewer and interactions four fewer. At 20% work
budgets, every learned arm exhausts planning in all 24 cohort-runs and their
aggregate totals tie; this does not show that expanded features are free.
The declared heterogeneous counter model and live wall-clock endpoint are
different measurements; do not interpret a counter deficit as a CPU slowdown.

All 576 pool runs, phase costs, attempts, deadline flags and completed-case IDs
are retained in the [paid report](../../results/geometric_20261028/PRIORITY_REPORT.md)
and its linked JSON/JSONL artifacts. The pool distance rule ranks inputs by
2^(-minimum distance); it is not the earlier distance<=2 branch gate.

## Evidence and reproduction

All 43 experiment-package unit tests pass. The corrected independent audit
reconstructs training-only geometry and out-of-list prototype features, refits
each classifier and sigmoid calibrator, checks fresh probabilities/confusions,
replays independent half-enumeration truth for all 144 base lists, verifies
original-index witnesses and source/model/data hashes, and checks all 576 pool
runs including 288 deterministic counter replays. See [VALIDATION.json](../../results/geometric_20261028/VALIDATION.json).
The initial auditor's variable-shadowing error and its post-generation repair
are explicitly recorded; no experimental outputs were changed by the repair.

- [Fixed protocol](PROTOCOL.md).
- [Saved experiment guide](../../results/geometric_20261028/README.md).
- [Model and feature implementation](../../code/geometric_models.py).
- [Freeze/generate/evaluate runner](../../code/geometric_experiment.py).
- [Corrected independent audit](code/audit_geometric.py) and [audit-only repair note](../../results/geometric_20261028/AUDIT_NOTE.md).

These nonlinear transformations re-express existing measurements; they add no
correctness certificate. A different prototype design, interaction selection,
regularization, model family or branch-benefit label would require a separate
experiment with new held-out inputs. Preserve the default model on this evidence.
