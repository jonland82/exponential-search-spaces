# Paper VI: stage 11 empirical easy/hard proximity

October 25, 2026. This separate follow-up tests the hypothesis suggested by the
3D plot: proximity to observed failures might help identify hard inputs. The
original study, figure data and current paper remain preserved.

**Stage 11 complete and validated.** All 35 tests pass. The independent audit
reproduces training-bank isolation, all empirical distances, the added-feature
model fits and calibration, scaled pairing, confusion counts, fresh reachability
truth, saved predictions and all 336 counter-pool traces. All 672 pool runs and
artifact/source hashes are checked. This is the discussion checkpoint.

## Design

Five fitted models were hashed before generating 144 additional base weight
lists and 1,152 cases across original/scaled encodings. Each base list has four
targets. The 576 original-encoding cases are 436 reference completions and 140
unresolved cases; always predicting easy achieves 75.7% accuracy. These are
synthetic, deliberately structured families, not an estimate for arbitrary
subset-sum inputs.

The reference bank contains only the 84 development training lists / 336 targets,
including 40 observed hard targets. Geometry is Euclidean distance in the
training-standardized original 15 features. Each class-distance feature averages
the nearest distances from five distinct reference lists with that label.
Training rows exclude their entire own weight list. The separate 42 calibration
lists enter neither the bank nor classifier fitting. Models use the same fixed
logistic settings and separate sigmoid calibration; k=5 is not tuned.

The baseline is the original frozen combined logistic model. Added features are
distance to hard training examples, or distance to both classes. The two-distance
model replaces the original inputs with these two empirical summaries; list-aware
nearest-neighbor classification is a separate control. All still compute the
original 15 features to perform their neighbor search.

## Fresh prediction results

| Model | Accuracy | Hard precision | Hard recall | Brier score |
|---|---:|---:|---:|---:|
| Original combined baseline | 90.6% | 83.1% | 77.1% | 0.0704 |
| Add distance to hard | 91.0% | 86.7% | 74.3% | 0.0712 |
| Add both distances | 89.1% | 74.5% | 83.6% | 0.0792 |
| Two distances alone | 90.6% | 85.2% | 74.3% | 0.0620 |
| Five nearest lists | 89.9% | 88.0% | 67.9% | 0.0836 |

The primary both-added-minus-baseline Brier difference is +0.0088, conditional
base-list bootstrap 95% interval [-0.0015,+0.0190]. Lower is better. This does
not establish an overall improvement. At the fixed 0.5 threshold, adding both
distances finds 117/140 hard cases versus 108/140 for the baseline, but mislabels
40/436 easy cases as hard versus 22/436. Thus nine additional detected hard cases
cost eighteen additional false alarms.

Hard-distance alone removes six false alarms but misses four additional hard
cases. The two-distance-only model has the best fresh unscaled Brier score and
hard-class average precision (0.9139 versus 0.8645 for baseline), but its paired
Brier interval also spans zero: difference -0.0084, interval [-0.0209,+0.0029].
Secondary rankings are descriptive, without multiplicity adjustment.

Encoding shifts matter: hard-distance added improves the scaled Brier score
from 0.1089 to 0.0633, while adding both distances worsens it to 0.2519. The
two-distance-only score is 0.0656. Euclidean proximity to a training bank does
not have guaranteed stability outside the training distribution. These paired
encodings preserve mathematical answers but alter the solver's budget and
representation behavior; they are not independent problems.

The same comparisons restricted to cases left unresolved by exact preprocessing
and by core reuse are saved in the report. The old plot's sample is separately
marked exploratory reuse; no model was selected using its labels.

The [interactive diagnostic viewer](visualizations/input_space_20261025/input_space.html)
now overlays observed outcomes, saved predictions and mistakes, with fixed
coordinates/axes across model comparisons. Focus on missed hard inputs while
keeping faint context to inspect where the boundary fails. This viewer uses the
**original** sample: baseline misses 28 hard cases and has 23 false hard flags;
both-added misses 16 and has 37 false flags. Those counts differ from the fresh
sample above because the inputs differ. Point inspection compares all five saved
probabilities and the empirical hard/easy distances.

## Solver benefit and validation

The 672 pool runs cover seven policies, eight cohorts, two budget fractions,
three repetitions and separate work/time endpoints. Every learned model acquires
the same features and exact cores. All online neighbor search, inference and
witness verification costs are paid. The following totals sum separately
budgeted cohort completions within each repetition, then take the median.

| Policy | Live 20% budget | Live 50% budget | Work 50% budget |
|---|---:|---:|---:|
| Arrival order | 690 | 869 | 875 |
| Simple structural rule | 819 | 885 | 763 |
| Original combined baseline | 854 | 887 | 729 |
| Add distance to hard | 849 | 888 | 468 |
| Add both distances | 837 | 887 | 468 |
| Two distances alone | 853 | 888 | 468 |
| Five nearest lists | 843 | 885 | 474 |

There is no clear incremental live benefit from neighbor features. At the tighter
budget all neighbor variants complete fewer cases than baseline. At 50%, the
one-case median gains for hard-only and distances-only lie within overlapping
repetition ranges: baseline 887-887, hard-only 886-889 and distances-only 886-890.
These timing ranges are descriptive, not confidence intervals over fresh inputs.

The declared-work endpoint is unfavorable: brute-force neighbor acquisition
exhausts planning in all 24 half-budget cohort-runs for the three distance-feature
models, versus 3/24 for baseline. At 20% work budgets, every learned model already
exhausts its planning allowance; equal totals there do not show free lookup.
Heterogeneous work counters and wall-clock time are separate cost models, so
the work deficit must not be described as a measured CPU slowdown.

The [paid priority report](results/neighbors_20261025/PRIORITY_REPORT.md)
preserves ranges and per-cohort results. Its finite-budget scheduling experiment
is separate from classification quality and from the earlier certified
branch-pruning experiment. Late answers are excluded and all returned solver
decisions are checked against independent reachability truth.

## Interpretation and discussion point

The visual cluster carries usable predictive signal, but visual separation does
not guarantee a better calibrated classifier. The original model already learns
from both labels. Adding label-dependent proximity changes how existing features
are represented; it does not create independent information, a new structural
hardness definition, or a correctness certificate.

Do not replace the default classifier solely on these results. The two-distance
summary and hard-distance feature are candidates for a later study with cheaper
reference prototypes and geometry designed to tolerate encoding changes. Those
would be new, separately evaluated choices. Stop here for discussion before
changing the model, running another tuned sample or updating the manuscript.

Evidence: [protocol](NEIGHBOR_PROTOCOL.md),
[prediction report](results/neighbors_20261025/PREDICTION_REPORT.md),
[all metrics](results/neighbors_20261025/prediction_metrics.json),
[priority report](results/neighbors_20261025/PRIORITY_REPORT.md),
[priority summaries](results/neighbors_20261025/priority_summary.json),
[independent validation](results/neighbors_20261025/INDEPENDENT_VALIDATION.json).

To reproduce, use a fresh output directory with `neighbor_experiment.py` stages
`freeze`, `generate`, `analyze`, `priorities`, then run `validate_neighbors.py`.
The original frozen records are never overwritten. Timing repetitions are
machine-specific observations, not independent input samples; bootstrap intervals
condition on fitted models and resample entire base lists.
