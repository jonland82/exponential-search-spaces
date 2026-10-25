# Progression and target-aware extensions for Paper VI

October 25, 2026. Elementary correctness arguments for the development extension.
These are not novelty claims; a literature audit remains part of the manuscript work.

## A polynomial representation for an arithmetic-progression core

Let the core contain exactly one item of each weight

    a, a+h, ..., a+(m-1)h, with a,h positive integers.

For a subset of cardinality k, its weight is ka+hJ. The distinct index sums J
attain every integer between

    k(k-1)/2 and k(2m-k-1)/2.

To see attainability, begin with indices 0,...,k-1. Move the last index right
up to m-1, then the preceding one up to m-2, and so on until the desired surplus
is exhausted. Every surplus between zero and k(m-k) is possible; the index
order remains strict throughout. These endpoints also follow by choosing the k
smallest or k largest indices.

Consequently the reachable set is a union of m+1 arithmetic progressions, one
for each k, represented by these formulas. They may overlap; exact membership
tests each k and does not count overlapping sets as disjoint. A successful k
supports O(m)-step constructive witness recovery by the same index movement.
Membership and recovery use O(m) arithmetic operations and polynomial bit cost.
Every prefix is another progression with the same property.

`extract_advanced` searches a fixed number (16) of candidate positive steps.
Candidates are step 1 and the most frequent consecutive distinct-weight gaps,
with deterministic ties. For each step it scans maximal consecutive chains in
the distinct values, retaining one original index per value. The search has
polynomial discovery cost and never enumerates subset sums. It may miss a
larger core whose step is not among the candidates, or a better general union
of progressions. Its deletion count is a certified upper bound, not an optimum.

The fifth coordinate chooses the larger of this core and the earlier bounded-
prefix interval core, breaking equal-size ties in favor of the earlier core.
It is a distance to a union of two certified representation classes. It can
never have more deletions than the previous fifth coordinate. This extension
does not change the first four coordinates and keeps the vector five-dimensional.

## Safe target-dependent reduction

For original weights w and target t, the preprocessing routine applies:

1. Reject targets outside [0,sum(w)].
2. If t exceeds half the total, replace it once by sum(w)-t. Complementing the
   eventual indexed witness recovers an original witness.
3. Remove items exceeding the current target; they cannot occur in a positive-
   weight solution of the current problem.
4. Reject if remaining total is too small, or the remaining gcd cannot divide
   the target.
5. Force item i if the sum of all other remaining items is less than the target.
   Subtract all forced weights and repeat; a negative residual proves NO.
6. A zero residual proves YES, with the forced items supplying a witness.

Every forced iteration removes at least one item, so at most n such iterations
occur. Scans and gcd computations therefore have polynomial total bit cost.
These are exact equivalence or decision steps, not learned pruning.

The target-aware five-vector is the same extractor evaluated on the residual
kernel. Deleted overweight items are resolved choices, not exceptional variables
that must be searched again. Indices map back through a retained-index map, the
forced-index list and, when used, complementation. For a kernel witness U, the
original answer is F union U without complementation, or the complement of
F union U with it. Here F is the forced set in the transformed problem.

If preprocessing completes, its empty residual kernel has five zero distances.
Operational policies finish immediately without computing any features. These
known easy cases are not an ML discovery; model evaluations additionally report
the subgroup whose kernels remain unresolved. Two unresolved targets can still
share the same kernel vector: target awareness improves available information
but does not make the five numbers a sufficient description of runtime.

The first three distances are exact minimum deletions within that kernel and its
fixed gcd grid. The last two remain constructive upper bounds. They are not
minimum deletion counts relative to the unreduced original list.

## Two distinct prediction questions in the development experiment

The common-label comparison asks whether the vectors contain predictive
information about one fixed exact-solving task. All models use the same labels:
the shared reduction plus fixed portfolio completes within 8L, excluding feature
extraction. This prevents changing labels from masquerading as better prediction.

The end-to-end comparison uses a fixed feature-cost/reuse pipeline as each task:

    exact prechecks -> extract five distances -> query full certified cores
    -> fixed fallback portfolio, all within 8L.

Within each pipeline's task, models using that five-vector, ten conventional
features and their 15-input hybrid predict the same completion event. Scores
between different pipeline tasks are not directly comparable because their
labels and success rates differ. All feature work and reused-core query charges
are paid by the exact pipeline. Query charges are conservative declared work
scales, not equal-cost CPU operations or a uniform bit-operation budget.

These are predictions of a measured policy's finite-budget success. The learned
predictions have not yet been used to prioritize or dispatch solving; inference
cost and prediction-driven benefits belong to that later experiment. No empirical
score establishes polynomial asymptotic solvability.

## Certified-core reuse

An extractor has already constructed exact representations for its cores. If any
coordinate is zero, that core is the full problem being queried. Its YES or NO
membership answer is therefore an exact decision. The development cost policies
try these queries only when their predeclared complete-query work charge fits
the remaining budget. This avoids discarding the useful result of extraction.

Nonzero-deletion cores currently fall back to the existing exact portfolio.
The general residual-search sufficient condition in [THEORY.md](THEORY.md)
continues to apply to all five coordinates, including the new progression core.
