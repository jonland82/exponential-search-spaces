# Exact branch resolution using distance certificates

This Stage 10 extension implements the proposal--verification part of
[Paper I](../../notes/01-certified-coverage/Certified_Coverage_of_Exponential_Search_Spaces.tex).
The previous whole-instance prioritization study and its model remain frozen.
The experiment is specified in [BRANCH_PROTOCOL.md](BRANCH_PROTOCOL.md).

## A certificate for a whole residual subtree

At a DFS node, the selected prefix contributes s and the remaining positive
weights form W. The residual question is whether a subset of W sums to t-s.
Exact target reduction produces an equivalent kernel (K,u), with witness maps.
Suppose a feature extractor partitions K into a certified easy core C and d
exceptional items E. Then

    u is reachable in K
    iff there is A subset E with u-sum(A) reachable in C.

Enumerate the 2^d exceptional subsets and query the exact core representation.
A successful query constructs a kernel witness, which the reduction maps back
to W and the prefix maps back to the original instance. If every query fails,
no completion of the prefix is feasible and the whole branch can be removed.
An interrupted enumeration gives no NO certificate.

If core extraction costs F and one core query costs at most Q on the current
encoding, a complete check costs F + O(2^d Q), in addition to reductions and
prediction. Q differs among the five core types. Choosing the smallest d is a
fixed heuristic for cost, not a proof that this core is the cheapest to query.
The experiment caps d at six, so at most 64 core queries are attempted.

The argument is valid for every core returned by either extractor, including
coordinates whose deletion distance is a constructive upper bound. Optimality
of the core is unnecessary for soundness. The input-index partitions, gcd
normalization and reduction witness map are part of the certificate.

## Connection to certified coverage

If a node has m undecided original items, a certified NO resolves all 2^m
assignment leaves beneath it. Such removed subtrees are disjoint in this DFS
because their descendants are never visited. This is certified assignment
coverage; it is not the number of visited DFS nodes actually avoided. Ordinary
range/gcd checks may have rejected many descendants cheaply anyway.

In Paper I's notation, successful NO verifications can enlarge a(n) delta(n),
while feature discovery, scoring and checking increase P(n). Their net effect
on total cost must be measured in consistent units. Here wall-clock time pays
for all of these phases, and separate counters explain what happened. The
node cap experiment deliberately does not treat its nodes as total work units.

For this existential decision problem, a verified YES witness stops the entire
search. It is a distinct benefit from certifying an infeasible subtree. Both
types of completed decision are recorded separately.

## What the frozen model does

The model estimates finite-budget completion of an earlier exact portfolio on
whole inputs. Stage 10 transfers that score to residual problems and uses its
fixed .5 threshold to choose whether to try the bounded structural checker.
It predicts neither infeasibility nor the new checker's calibrated completion
probability. In particular, a low score means continue ordinary search, not
discard the branch. Feature acquisition itself is paid even for skipped checks.

Always checking and distance-only policies use exactly the same verifier and
fallback traversal. Matched acquisition controls also compute the numerical
features, isolating the learned gate more closely; native controls avoid that
extra acquisition cost. A failed transfer result would justify a future model
trained on branch-level checker benefit, on independent training trees. It
would not justify tuning the present thresholds on these outcomes and calling
the same cases a new prospective test.

## Limits of any empirical result

Whole-instance classification accuracy does not bound certified coverage or
runtime savings. Prediction errors can cost time but cannot change exactness.
No asymptotic improvement follows unless one can additionally bound discovery,
verification and remaining search over an explicitly specified input family.
Even if every individual core check is polynomial, exponentially many nodes
can remain. The existing 95.5% whole-instance accuracy does not address that
remaining-tree requirement.
