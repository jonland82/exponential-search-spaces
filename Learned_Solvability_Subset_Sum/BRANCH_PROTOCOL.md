# Stage 10: learned selection of certified branch checks

This is a new exploratory transfer experiment, separate from the frozen Paper VI
study. The saved model is not fitted, calibrated or selected using these cases.
The protocol and source snapshots are saved before fresh inputs are generated.

## Question and guarantees

Does the combined completion predictor save time when deciding which residual
search problems to resolve with exact structural certificates? A prediction is
never a NO answer. Exhausting a resource limit returns unresolved.

At a checkpoint, apply the existing exact target reduction. Extract the five
certified distances on its unresolved kernel. Select the smallest-distance core
(first coordinate wins ties). If at most six items lie outside it, enumerate
all exceptional subsets and query that core exactly. A witness resolves YES;
exhaustion certifies NO for the whole branch. Check deadlines between queries.
No enumeration is hidden in feature extraction. The same checker is available
to every structural policy.

Search is descending-weight, include-first DFS with suffix range/gcd checks,
without memoization. Checkpoints occur every four levels while at least eight
items remain, up to 128 per solve. The reduction is shared by all policies at
these checkpoints, including the DFS control. Fallback branching is identical.

## Prespecified comparisons

- `dfs`: shared reductions and DFS, no structural extraction.
- `always_native`: acquire five distances and check whenever distance <= 6.
- `distance_native`: same acquisition; check when distance <= 2.
- `always_matched`: acquire five distances AND standard features; check at <= 6.
- `distance_matched`: same matched acquisition; check at <= 2.
- `conventional`: matched acquisition; check at <= 6 and standard model p >= .5.
- `hybrid`: matched acquisition; check at <= 6 and combined model p >= .5.

Matched policies pay for identical acquired features. Native policies measure
the practical alternative without unnecessary numerical feature acquisition.
As in training, distances describe the reduced kernel; standard features describe
the residual instance before that reduction.
Only the two learned policies pay inference. Frozen primary logistic models
are reused through algebraically equivalent scalar inference, checked against
scikit-learn predictions. Their output still refers to the OLD whole-instance
8L portfolio completion task: it is not a calibrated probability that this new
checker will succeed. Branch sizes and selection create distribution shifts.

## Inputs, budgets and accounting

Seed 720251026. Sizes 24, 32, 36; the twelve prospective-study families;
replacement fractions 0 and .125; one list per cell. Exclude every previously
used sorted weight list, including the frozen prospective study. Each of the
72 fresh lists supplies a planted target, a uniform middle target (30--70% of
total), and an odd target below its largest weight: 216 cases. Independent
binary-mask half enumeration supplies truths and is destroyed before timing.
Targets from one list are dependent. No scaled copies are added.

Two separate modes: deterministic search with a 10,000 visited-node cap (one
repeat), and a 50 ms live deadline with a 1,000,000-node safety cap (three
repeats). Both retain the 128-checkpoint and 64-exception-query limits. Seeded
shuffling interleaves policies and cases within each repeat. All sorting,
reductions, features, predictions, exact queries and witness checks occur inside
the solver clock. Model loading, input generation, independent oracles, output
serialization and post-hoc auditing are outside. Atomic feature operations can
overshoot a cooperative deadline; late answers are excluded and overshoot saved.

Report completions, YES/NO counts, time, nodes, certificate counts, exact core
queries, overhead components, and results by family and size. Compare node
reduction and elapsed time separately; the deterministic cap is not a uniform
computational-work budget. Timing of censored runs is a capped cost, not a
measurement of their full solution time. Median aggregate completions are
computed by repeat, not by adding per-case median outcomes.

NO-certified subtrees contribute 2^m assignment leaves, where m is the original
remaining suffix length. These are disjoint within one DFS traversal, not
measured visited nodes saved or claims of polynomial residual size.

Diagnostic only: use the first eight unresolved checkpoints encountered by the
unguided deterministic DFS per case. Re-evaluate the frozen scores and bounded
checker outside timing. Measure transfer to checker completion and certified NO
separately. This selected node sample is not an independent test distribution,
and the diagnostic does not change the operational policies or thresholds.

This stage tests a concrete instance of Paper I's proposal--verification
framework. Any positive result must exceed certificate discovery and checking
cost, and beat a simple rule with access to the same certificates. It does not
establish an asymptotic improvement. Results will be reported without tuning
the above choices on the resulting outcomes.
