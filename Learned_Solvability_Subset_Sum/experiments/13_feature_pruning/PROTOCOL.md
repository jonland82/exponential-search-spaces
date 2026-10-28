# Training-only feature pruning: top five and ten logistic inputs

October 28, 2026. A separate experiment after the geometric-feature results.
Preserve all previous models, datasets, sources and manuscript artifacts.
Freeze feature selection, models, configuration and sources before new generation.
This is a local freeze, not external preregistration.

## Selection and fitting

Start with the same 27 candidates: 15 original inputs, two nearest class-centroid
distances, and ten pairwise products of standardized structural distances.
Use the original development training split only: 84 lists / 336 targets.
Reuse the validated out-of-list prototype training designs from the geometric
experiment. Entire-own-list exclusion for prototype construction remains intact.
No calibration, old evaluation or new evaluation outcomes rank/select features.

Use recursive feature elimination (RFE), not cross-validated model selection.
At each step fit StandardScaler + LogisticRegression(C=1,max_iter=2000,
random_state=630251026) on the surviving columns and remove the smallest absolute
standardized coefficient. Exact ties remove the smallest original column index.
Continue one column at a time from 27 down to 5; save survivors at 10 and 5.
Rank the final five by their final coefficient magnitudes, then reverse the
elimination order for ranks 6-27. This is a conditional model-based ranking,
not proof that these are the universally most informative features.

Refit logistic regression separately on the selected 10 and 5 columns; calibrate
each with sigmoid/logit calibration on the same 42 separate development
calibration lists. The calibration split changes neither selection nor C.
Keep original settings and fixed 0.5 classification threshold. Compare four arms:
original frozen 15-input baseline, frozen full 27-input combined model, top10,
and top5. The two unpruned controls are the exact prior fitted/calibrated models.
Record selected names/indices, all RFE coefficients and elimination steps,
training designs, dependency lists, frozen models and split IDs.

The label remains completion of the fixed exact portfolio within 8L work units.
It is not reachability or branch-checker benefit. No classifier prediction
certifies NO or discards a search branch.

## Fresh evaluation

Use new generation seed 750281026, n=24,32,38, twelve existing families,
replacement fractions 0/.25, two replicates, four targets, and original/scaled
encodings: 144 base lists, 288 encoded lists, 1,152 cases. Exclude normalized
sorted-list overlap with every prior results/*/lists.jsonl present at freeze,
including the geometric study. Hash and preserve the exclusion files/set.
Independent half enumeration supplies reachability truths; unchanged exact
reference solving supplies completion labels. Never reject by either outcome.

Two co-primary endpoints: unscaled pooled Brier(top5)-Brier(baseline15), and
Brier(top10)-Brier(baseline15). Report conditional base-list bootstrap 95%
intervals and conservative 97.5% per-comparison intervals for these two endpoints
(Bonferroni family coverage at least 95%, subject to bootstrap approximation).
Use 1,000 base-list bootstrap draws with seed 740281026, matching the reused
analysis helper. Keep related targets/encodings together. Intervals condition
on fixed selected models and do not include selection/refitting uncertainty.
Report secondary comparisons against full27, all cohorts, paired encodings,
accuracy, log loss, AUC, hard precision/recall/AP, confusion/calibration, and
unresolved-after-reduction/core-reuse subgroups. No tuning after outcomes.

## Paid utility and dependencies

Run unchanged whole-input prioritization pools with arrival order, pool distance
rule, baseline15, full27, top10 and top5: 20%/50% budgets, three rotated-order
repeats, counter and separately measured live endpoints, 20ms per-case cap.
All learned arms pay for the original 15-input acquisition and the same exact
core reuse before ranking. This deliberately measures selection/prediction gains
with matched acquisition; it does not claim to optimize underlying extraction.

Selected online adapters construct only retained transformations. A selected
prototype distance still depends on all 15 base inputs. A selected product
depends on both original coordinates. Geometry standardizes 15 inputs once
(45 declared units) when any derived feature is selected, then pays 47 per
queried prototype plus one per selected product. Inference is 6*k+20 for k model
inputs. Fully retained 27-input and baseline costs stay identical to the earlier
study. Disclose dependencies: a five-input classifier is not automatically a
five-measurement solver. These are heterogeneous work counters, not uniform
CPU/bit costs. Charge all online computation, sorting and witness verification;
exclude offline fitting/loading. Preserve deadline flags and exclude late answers.

Validate ranking/nested subsets, refits/calibration, selected-transform parity,
old-control probabilities, source/input/model hashes, independent exact truth,
all pool traces and deterministic counter replays. Stop with checked findings;
do not replace the default model or revise the paper from this one study.
