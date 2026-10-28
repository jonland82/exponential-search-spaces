# What a learned priority can and cannot guarantee

Elementary consequences of the stage 7-8 protocol; no novelty claim.

## Correctness is independent of the prediction

A prediction changes order only. Exact positive-weight reductions, certified
full-core membership, or the exact fallback portfolio must produce every counted
decision. A low predicted completion probability never certifies NO. A budget,
state or time limit yields unresolved. Returning fewer answers therefore cannot
create a mathematical false negative if this distinction is maintained.

For a fixed pool, induction through the policy trace gives this invariant:
every counted completion is an exact decision obtained before its applicable
deadline; every uncounted or unattempted input remains unresolved. Indexed YES
witnesses are checked against original weights, including complement/forced-item
lifting. Independent experimental labels cross-check the decisions; those labels
are not available to ordering or inference.

## The planning-cost constraint

Write the paid cost of a batch plan as

    C_plan = C_prechecks + C_features + C_core_queries + C_inference + C_ordering.

If the global budget is B, at most max(0,B-C_plan) remains for fallback solving
and returned-witness checking. This is an accounting identity, not a lower bound
on every possible algorithm. Exact prechecks/core queries can already complete
some cases during planning. If planning exhausts B, the learned ordering never
gets to act on the remaining pool, regardless of its predictive accuracy.

The experiment uses this full-batch protocol deliberately and reports planning
exhaustion. More selective or incremental feature acquisition is a possible new
policy, but its advantage is not established by these results. Shared feature
caching across related targets would likewise require explicit accounting and
its own measured policy; it is not silently credited here.

## A good probability estimate need not yield a good schedule

The models estimate a particular exact portfolio's finite-budget completion event,
conditional on observed features under a training distribution. Brier score
measures probability error. The practical outcome is the count of exact decisions
completed under a shared budget. The two objectives differ: computation of the
predictor consumes resources, realized solver costs vary, and errors on an early
expensive case can matter more to the schedule than errors on cheap cases.

Ranking by predicted probability divided by a declared per-case work allowance
is a heuristic. Even with correct probabilities, a ratio rule is not generally
an optimal indivisible budget allocation, and refunding unused solving work
changes the operational problem further. The time experiment also transfers a
work-completion predictor to a wall-clock deadline. No optimality or expected
speedup theorem is claimed for either ranking.

## Relation to the structural guarantees

The sufficient polynomial regime for a certified core plus few exceptions remains
valid independently of learning. A model may suggest where such structure will
be useful, or combine its distance with numerical summaries, but its score is
not a certificate of membership in an asymptotic complexity class. The stage 7-8
experiment can support scoped predictive and practical comparisons on its frozen
input distributions. It cannot establish a new worst-case subset-sum bound.
