# Training-only proximity to easy and hard inputs

October 25, 2026. This follow-up was motivated by inspecting the earlier 3D
plot. The old prospective sample is therefore exploratory reuse. New weights
are generated only after hashing this protocol, source snapshots and fitted
models. This is a local freeze, not external preregistration.

## Models and isolation

Use the same 84 development training lists and 42 separate calibration lists.
Retain the original frozen calibrated 15-feature logistic model as baseline.
Compare logistic models with (a) one hard-proximity feature, (b) both hard and
easy proximity features, (c) those two proximity features alone, and (d) a
five-nearest-list classifier. Fix k=5 and all logistic/calibration settings in
advance; do not tune against either evaluation sample.

Fit Euclidean geometry on training-only standardized 15-feature vectors.
For each label, find each training list's closest target with that label, then
average distances from the five closest distinct lists. Hard means the fixed
reference failed to finish under its 8L allowance; easy means it completed.
A training row excludes its entire own weight list when constructing these
features. Evaluation and calibration use the unchanged training bank. No
evaluation/calibration label enters a reference bank. The separate list-neighbor
classifier chooses each list's closest target and votes among the five closest
lists, then receives the same separate sigmoid calibration. Distance-feature
logistic models use C=1 and max_iter=2000, matching the baseline. The hard-only
ablation still computes both distances and pays the same search overhead.

## New evaluation

Generate 144 new base lists: n=24,32,38; the same twelve families; replacement
fractions 0 and 0.25; two seed replicates, with new seed 730251026. Use the same
four target rules and unscaled / (2^24+1) paired encodings, giving 1,152 cases.
Exclude normalized sorted-weight overlap with all prior pilot, development,
prospective and branch samples. Preserve prior-holdout, new-family, larger-size
and in-distribution cohorts separately. Family novelty is relative to training;
these generating families were already inspected in earlier experiments.
No rejection by solver outcome or reachability. Independent binary-half
enumeration checks reachability; the fixed reference supplies completion labels.

Primary comparison: Brier(both distances added) minus Brier(baseline), pooled
fresh unscaled inputs. Also report each cohort and scaled inputs separately,
log loss, ROC AUC, hard-class average precision, hard precision/recall,
balanced accuracy, accuracy at 0.5 and confusion counts. Include constant-prior
and always-easy controls. Show subgroups unresolved after exact preprocessing
and after core reuse; easy preprocessing cases must not hide residual failures.
Resample base lists within the reported evaluation subgroup, using 1,000 draws
and retaining related targets/scaled pairs together. Intervals condition
on fitted models, do not include refitting uncertainty, and secondary comparisons
are descriptive without multiplicity adjustment. No significance claim follows
from inspecting the old plot or sample.

## Paid solver benefit

On fresh inputs rerun identical-pool prioritization at fractions 0.2 and 0.5 of
declared allowances, three repetitions. Compare all five learned models with
arrival order and the simple structural-distance rule. All learned arms and
the structural rule acquire identical features and reuse the same exact cores.
Retain the earlier fixed preprocessing, fallback portfolio and 20ms cooperative
case limit. Test both declared-work replay and separately measured live time.
Charge every online feature, neighbor lookup, inference, sorting, certificate
query and witness check. Neighbor work includes scanning all 336 reference
vectors and list minima/sorting; its formula is saved in neighbor_models.py.
No neighbors are inserted online; loading frozen models is outside the budget,
as in the earlier experiment. No predicted failure certifies NO or removes a
branch. Record planning exhaustion, phase costs and late-answer exclusions.

Report full traces, fitted models, raw distances, predictions, hashes and a
validation audit. Preserve all earlier artifacts. This experiment tests finite
solver completion and practical prioritization, not intrinsic or asymptotic
hardness. Stop after checked findings for discussion before revising the paper.
