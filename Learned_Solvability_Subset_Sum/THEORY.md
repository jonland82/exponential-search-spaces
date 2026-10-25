# Five certified distances: first implementation and sufficient conditions

Status: elementary arguments for the feasibility implementation, not a novelty
claim. This is the theory checkpoint for proposed Paper VI, not a completed paper.
The subsequent progression and target-aware extension is in
[ADVANCED_THEORY.md](ADVANCED_THEORY.md); the original definitions below remain
the baseline for the preserved feasibility pilot.

## Instance, normalization, and features

An instance is x=(w,t), where w has n positive integer weights and t is an
integer. Let L denote full binary input length. The pilot uses the explicit
self-delimiting length proxy in `features.input_length`, polynomially equivalent
to the usual encoding. Normalize weights by the gcd g of the entire weight list
(g=1 for an empty list). All selected cores use this same grid. Core queries
reject t not divisible by g before operating on t/g.

The five features depend on w, not t. They are integer deletion counts, not
normalized proportions. With fixed caps r=2, s=128, q=8, the implementation is:

| Coordinate | Certified remaining core | Distance status |
|---|---|---|
| 1 | Sorted weights strictly exceed their preceding total | Exact minimum deletion |
| 2 | Sorted normalized weights satisfy a_i <= 1 + preceding total | Exact minimum deletion |
| 3 | At most r distinct values | Exact minimum deletion |
| 4 | At most s distinct subset sums, including zero | Constructive upper bound |
| 5 | Every accepted sorted prefix has at most q disjoint reachable intervals on the fixed g-grid | Constructive upper bound |

Empty cores are allowed. Coordinate 5 implements a specific common-grid interval
representation. It does not implement arbitrary unions of arithmetic progressions
with independent steps. An arithmetic progression of *input weights* is also
different from an arithmetic progression representation of *reachable sums*.

## Discovery and minimum-distance claims

1. **Superincreasing:** sort and accept an item exactly when it exceeds the
   accepted total. The maximum-cardinality proof is already in
   [Paper V's theory](../Structural_Distance_Subset_Sum/THEORY.md). Scaling by
   the common gcd preserves its inequalities.

2. **Coverage:** sort and accept a <= S+1, where S is the accepted total. The
   invariant is exact coverage of [0,S]: adding a translates that interval to
   [a,a+S], whose union is [0,S+a] precisely when a <= S+1. At the first rejected
   item b>S+1, every remaining item is at least b. No selection of later items
   can supply the missing integer S+1, and deleting previously accepted items
   only reduces their total. Consequently no valid coverage core can include
   a later item; the accepted prefix has maximum cardinality. This minimum is
   relative to the fixed whole-list normalization, not a freely chosen core gcd.

3. **Few values:** retain the r most frequent values, breaking ties by value.
   Any core with at most r values has at most the sum of those r frequencies.
   Retaining all their indexed occurrences attains this bound.

4. **Small support:** start with S={0}; scan sorted items and construct
   S'=S union (S+a). Accept iff |S'| <= s. Store an indexed representative
   witness for every retained sum. Each trial creates at most 2s entries, so
   rejection never requires enumeration of all subsets of the original input.
   The returned core has the promised support; its deletion count need not be
   minimal. Any prefix of that core also has support at most s, since subset-sum
   support only grows when items are added.

5. **Interval union:** represent the current reachable set by sorted, disjoint,
   nonadjacent integer intervals. Merge it with its translation by a, coalescing
   adjacent intervals. This constructs the exact new set using at most 2q input
   intervals and O(q) interval operations. Accept iff the result has at most q
   intervals. Save every accepted prefix for witness recovery. The certificate
   proves the bounded-prefix condition; it is an upper bound on the minimum
   deletion to this condition, not necessarily a maximum-size core.

For coordinate 5, a final representation can be small while earlier prefixes
are large: [3,4,5,6] has reachable intervals [0,0],[3,15],[18,18], but its [3,4,5]
prefix has four intervals: [0,0],[3,5],[7,9],[12,12]. A final-size-only definition would therefore
not justify our construction bound. The implemented class includes prefix bounds.

## Exact core queries and witnesses

- Superincreasing membership uses descending greedy, as in Paper V.
- Coverage answers YES exactly on [0,total]. Descending greedy recovers a witness:
  when omitting a, the remaining target is at most a-1 <= previous total;
  when taking a, subtracting it leaves at most the previous total.
- Few-values membership enumerates counts for each value. With at most r groups,
  there are at most (n+1)^r count vectors. The counts map back to original indices.
- Small support membership finds a stored sum and its indexed witness.
- Interval membership checks the saved final intervals. Backtrack through saved
  prefixes: omit an item if the target belongs to the preceding set, otherwise
  subtract it. The exact-union invariant guarantees membership after subtraction.

These procedures are polynomial for fixed r and polynomially bounded s,q. The
saved certificates use polynomial space, including original-index witness masks
and interval endpoints. All sums and endpoints have O(L) bits. Python hash-table
overhead does not change polynomiality even with conservative worst-case lookup
accounting. Instrumented work counts are not a substitute for bit-complexity bounds.

The included tests independently enumerate small deletions, reachable sets,
prefix representations, and targets. They verify the mathematical invariants
and original-index witness recovery; they are not empirical proofs for all inputs.

## Residual-search sufficient condition

Suppose extractor i returns a certified core and k_i exceptional items, at cost
F_i(L). If its exact membership query including witness recovery costs Q_i(L),
enumerate the exceptional selections and query target minus their sum. Each
original subset is a unique pair of an exceptional and core selection. Thus

    T_i(x) <= F_i(L) + 2^k_i poly(L) + 2^k_i Q_i(L).

If F_i and Q_i are polynomial and k_i=O(log L) throughout an input family,
this is a polynomial-time sufficient condition. It applies to the constructed
upper bounds as well as exact minimum distances. A large coordinate gives no
hardness certificate. Enumerating only distinct exceptional sums is another
possible extension, following Paper V, but is not needed for this bound.

## Prediction and asymptotic limits

Fix a solver portfolio A, its schedule, its resource caps and an input distribution
D. For a budget B(L), train toward

    P_{X~D}(A finishes exactly within budget, including features | phi(X)=phi(x)).

This is the probability of budgeted completion, not the probability of a YES
subset-sum answer and not a certificate of polynomial-time solvability. In the
pilot, B(L)=8L or 32L counts instrumentation units, with additional memory caps.
Bitset operations can touch many bits per recorded unit, so the pilot budget
is explicitly not a uniform bit-operation model. Finite-size success cannot
establish polynomial asymptotic scaling.

Because phi depends only on w, targets on the same list have the same prediction.
Different actual outcomes do not contradict a probability estimate: the model
averages over the declared conditional target distribution. They do limit the
information available for ranking individual targets. Likewise, omission of n,
L and the budget from the five inputs creates possible information loss; a
separate model per fixed budget rule and conventional-feature baselines are
required in a later study.
