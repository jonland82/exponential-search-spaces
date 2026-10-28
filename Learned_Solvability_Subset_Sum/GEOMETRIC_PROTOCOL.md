# Prototype geometry and interaction features: a new logistic experiment

October 28, 2026. A new, separately frozen follow-up in the Paper VI experiment
package. Previous models, sources, results and manuscript artifacts are preserved.
This is a local pre-generation freeze, not external preregistration.

## Fixed question and models

Can cheap nonlinear transformations of the original 15 inputs improve calibrated
prediction and paid whole-input prioritization? The label remains completion of
the fixed exact portfolio under its 8L counter allowance. This is not a new
branch-checking experiment, a reachability classifier, or a net-time-savings label.

Four arms use logistic regression with C=1, max_iter=2000 and the original seed
630251026, followed by separate sigmoid calibration with those same settings:

| Arm | Inputs | Count |
|---|---|---:|
| baseline | Original five target-aware structural distances + ten numerical summaries | 15 |
| prototypes | Original inputs + nearest hard/easy centroid distances | 17 |
| interactions | Original inputs + all ten products between distinct standardized structural coordinates | 25 |
| combined (primary) | Original inputs + both prototype distances + ten products | 27 |

No products, thresholds or hyperparameters are selected using evaluation results.
No gradient boosting, random forest, density feature or PCA coordinate is added.
Density was an optional suggestion and is outside this fixed experiment.

Let z be the original 15 inputs standardized using development-training rows
only. For each completion class y in {0,1}, fit three KMeans centroids c[y,k]
in that 15D space. Use seed 740281026, n_init=10, max_iter=300, Lloyd's algorithm,
and one offline numerical thread. Each distinct training list has total sample
weight one within each class it contributes to. If a class has fewer than three
distinct feature vectors, use that many centroids; do not invent duplicates.

    D_y(x) = min_k ||z(x) - c[y,k]||_2
    interaction_ij(x) = z_i(x) z_j(x), 0 <= i < j < 5

Centroids summarize observed solver completion/unresolved outcomes; they do not
certify easy/hard mathematics. Calibration/evaluation labels never fit centroids
or scalers. The same 84 development training lists / 336 targets fit classifiers;
42 disjoint calibration lists fit sigmoid calibration only. Training rows use
leave-one-list-out prototypes: remove all targets of that row's list before
fitting class centroids. The unsupervised initial standardization stays fixed on
training rows. Store these out-of-list features. Final calibration/evaluation
uses prototypes fitted on all training lists. No online insertion or refitting.
Every expanded design gets its own training-only StandardScaler before logistic
regression. Refit the original baseline and reproduce its frozen probabilities.

## New inputs and outcomes

Freeze models/config/source hashes before generating inputs with new seed
740281026. Use n=24,32,38, twelve existing generating families, replacement
fractions 0 and 0.25, two replicates, four existing target rules, and original /
(2^24+1) paired encodings: 144 base lists, 288 encoded lists, 1,152 cases.
Exclude normalized sorted-weight overlap with every prior results/*/lists.jsonl
present at freeze. Preserve their paths/hashes and the full exclusion set.
Existing generating families are not newly discovered external distributions.
No rejection by solver outcome or reachability. Independently enumerate halves
for exact truths; use the unchanged reference portfolio for completion labels.

Primary endpoint: combined minus baseline Brier score, pooled fresh unscaled
inputs. Report all four arms, constant-prior and always-completed controls;
accuracy, balanced accuracy, hard precision/recall/AP, ROC AUC, log loss,
calibration bins and confusion matrices. Report scaled inputs and each existing
cohort separately, plus unresolved-after-reduction and unresolved-after-core-reuse
subgroups. Bootstrap 1,000 times by base list, keeping related targets together;
intervals condition on fixed fits and do not include retraining uncertainty.
Other arms/cohorts are secondary with no multiplicity-adjusted claims.

## Paid practical comparison

Use the unchanged precheck/core-reuse/fallback pool pipeline and the original
20ms cooperative per-case limit. Compare arrival order, the existing pool
distance rule, and all four logistic arms at 20% / 50% shared budgets, three
rotated-order repetitions. The pool distance rule ranks by 2^(-min distance);
it is distinct from the distance<=2 branch gate in the earlier branch study.
All learned arms acquire the same original features and exact cores.

Run both counter replay and live wall-clock endpoints. Online prototype
distances, interaction construction, expanded standardization, inference,
sorting, core queries, fallback solving and witness checks are paid. Inherited
base inference charge is 6*dimension+20; geometric_models.py adds 45 initial
standardization operations, 47 per prototype, and ten products as applicable.
This declared heterogeneous counter is not CPU or bit complexity. Offline
KMeans, classifier fitting and frozen-model loading are excluded as before.
Record phase costs, planning exhaustion, all attempts, and late-answer exclusions.
Predictions never certify NO. Fresh cases and timing repetitions are dependent;
timing ranges are descriptive, not confidence intervals over fresh inputs.

Preserve source snapshots, feature names, models, train/calibration IDs,
out-of-list training features, raw added features, predictions, hashes and traces.
Validate feature construction, calibration, source/data isolation, original-index
witnesses, independent truth and deterministic counter replay. Report findings
without changing the default model or paper based on this one experiment.
