# A maximum superincreasing core and its exact residual search

**First theoretical milestone for proposed Note V.** These are elementary
derivations, with independent finite checks in the accompanying tests. Literature
novelty remains unestablished.

## 1. Model and definitions

The input is an indexed list of $n$ positive integers $w_1,\ldots,w_n$ and an
integer target $t$, encoded in binary. Duplicate values remain separate items.
An empty subset is permitted.

A core is an indexed selection whose sorted values $g_1,\ldots,g_m$ satisfy

$$
g_j>\sum_{h<j}g_h.
$$

We regard the empty selection as a valid core. Its complement is $E$, the
exceptional list. Write

$$
k(w)=n-\max\{|C|:C\text{ is a superincreasing core}\},
\qquad
M(E)=|\mathcal A(E)|,
$$

where $\mathcal A(E)$ is the set of distinct subset sums of the indexed items
in $E$, including zero.

## 2. Greedy discovery improves the planned dynamic program

Sort the input by $(\text{weight},\text{original index})$. Start with total zero.
Accept a weight exactly when it is strictly larger than the total already
accepted. Otherwise put it among the exceptions.

**Theorem 1.** The accepted selection is a maximum-cardinality superincreasing
core. More strongly, whenever any superincreasing selection of length $j$ exists,
the first $j$ greedy selections exist and their total is minimum among all such
selections. Discovery uses $O(n\log(n+1))$ arithmetic/comparison operations and
$O(n)$ records, including sorting.

**Proof.** Consider any superincreasing selection with sorted positions
$p_1<\cdots<p_\ell$ and values $b_1,\ldots,b_\ell$. Let $q_j$ and $g_j$ be the
position and value of the $j$th greedy acceptance.

Inductively establish, for each $j\le\ell$,

$$
q_j\le p_j,
\qquad
g_j\le b_j,
\qquad
\sum_{h\le j}g_h\le\sum_{h\le j}b_h.
$$

For $j=1$, the greedy algorithm accepts the first positive input weight, so
these statements hold. Suppose they hold through $j-1$. If the greedy algorithm
has already accepted its $j$th item before position $p_j$, then $q_j\le p_j$.
Otherwise, at position $p_j$ it has accepted exactly $j-1$ items. The next
comparison satisfies

$$
b_j>\sum_{h<j}b_h\ge\sum_{h<j}g_h,
$$

so the greedy algorithm accepts this item. Again $q_j\le p_j$. Sorted order
gives $g_j\le b_j$; adding the prefix inequalities gives the total inequality.

Consequently, greedy accepts at least as many items as every feasible
selection. Its own selection is feasible by construction, so its cardinality is
optimal. The total inequality proves the stronger statement for each feasible
length. Sorting dominates the linear acceptance and partition scans. $\square$

The $O(n^2)$ minimum-total dynamic program in the prospectus is valid but
unnecessary for production. It remains a useful independent comparator. The
stronger greedy invariant explains why its minimum totals have a single chain
of representatives.

Verifying a supplied indexed partition and the core inequalities takes $O(n)$
operations in the usual word/RAM representation. This check establishes the
structure, not independently the core's maximum cardinality; optimality follows
from Theorem 1 and is checked by exhaustive selection on small inputs.

## 3. Exact queries to a verified core

**Lemma 2.** A residual target $r$ is reachable by a verified core exactly when
descending greedy subtraction ends at zero.

**Proof.** Negative targets and targets exceeding the core total are impossible.
At the largest remaining weight $g_j$, if $r<g_j$, inclusion is impossible because
weights are positive. If $r\ge g_j$, exclusion is impossible because the total of
all smaller remaining weights is strictly below $g_j$. Thus every successful
subset must follow the greedy choice. Applying this argument repeatedly proves
both directions. The accepted original indices form a witness when the remainder
is zero. $\square$

A query takes $O(m+1)$ arithmetic operations and $O(m)$ witness storage.

## 4. Searching the exceptions

For a fixed partition $(C,E)$, the original input is YES if and only if

$$
\exists s\in\mathcal A(E):
\quad t-s\in\mathcal A(C).
$$

This is an equivalence because the indexed parts are disjoint and exhaust the
input. One witness from each part combines into an original-input witness.

**Theorem 3.** Discovering the greedy core and enumerating all exceptional
selections gives an exact algorithm with arithmetic-operation bound

$$
O\!\left(n\log(n+1)+(n+1)2^{k(w)}\right).
$$

**Proof.** Apply Theorem 1. There are $2^{k(w)}$ exceptional selections. A Gray-code
enumeration updates the exceptional sum in a constant number of arithmetic
operations per selection, and Lemma 2 answers each query in $O(n+1)$ operations.
All selections are visited unless a witness is found earlier. Exhaustion proves
NO. $\square$

In particular, on any family with $k(w)\le c\log_2(n+1)$ for a fixed constant
$c$, the arithmetic-operation bound is polynomial in $n$.

## 5. Merging equal residual sums

Start with $S_0=\{0\}$ and process the exceptional items $e_1,\ldots,e_k$:

$$
S_{j+1}=S_j\cup(S_j+e_{j+1}).
$$

Retain one indexed witness for each distinct sum. Merging the two sorted lists
constructs the next list in $O(|S_j|+|S_{j+1}|)$ operations. Every element of a
prefix support remains attainable in the final support by omitting all later
items. Hence

$$
|S_j|\le M(E)
\quad\text{for all }j.
$$

**Theorem 4.** The distinct-sum solver is exact and has arithmetic-operation bound

$$
O\!\left(n\log(n+1)+(k+m+1)M(E)\right)
=O\!\left(n\log(n+1)+(n+1)M(E)\right).
$$

**Proof.** Construction uses $O(kM(E))$ operations. It covers every exceptional
selection because the recurrence exactly handles exclusion and inclusion at each
step. Equal sums give the same residual target, so one representative is enough
for existence and witness recovery. The final list needs $M(E)$ core queries,
each costing $O(m+1)$. Lemma 2 and the partition equivalence establish YES and NO
correctness. $\square$

Only the two consecutive lists need coexist, so the residual summary needs
$O(M(E))$ records; indexed witnesses can be represented by $n$-bit masks. A mask
operation is not a constant-cost operation in a bit model.

Let $L$ be the total binary input length. Intermediate sums need only
polynomially many bits in $L$, and masks use at most $n\le L$ bits. Sorting,
integer arithmetic, root gcd checks, and witness handling therefore give
conservative bit bounds of the forms

$$
\operatorname{poly}(L)\,2^{k(w)}
\qquad\text{and}\qquad
\operatorname{poly}(L)\,M(E).
$$

These are upper bounds, not hardness lower bounds. Large $k$ or $M$ does not
exclude another cheap representation or a fast target-specific witness.

## 6. A small counterexample to choosing a core by size alone

Consider

$$
w=[1,1,1,2,3].
$$

The greedy core has values $[1,2]$ and exceptions $[1,1,3]$, giving

$$
\mathcal A(E)=\{0,1,2,3,4,5\},
\qquad M(E)=6.
$$

The alternative core $[1,3]$ has the same maximum cardinality, but its exceptions
are $[1,1,2]$, giving

$$
\mathcal A(E')=\{0,1,2,3,4\},
\qquad M(E')=5.
$$

No three-item core exists: its first two items total at least $3$, and no remaining
weight exceeds $3$. Thus even among maximum-size cores, minimum total and minimum
residual support are different objectives.

The greedy core is an inexpensive, proved starting point. Efficiently choosing a
decomposition that better controls $M$ is a separate research problem.

## 7. Certificates, limits, and empirical claims

The implementation verifies its discovered partition and checks every YES witness
against original indices. The solver's exact enumeration and core-query proofs
justify NO answers; it does not claim to emit a separate succinct NO certificate
for every instance.

Finite work, residual-record, bitset-width, and optional time limits protect
experiments. Exhausting one returns `unresolved`. Completed support size $M$ is
reported only after full distinct-sum construction. Input and core storage are
separate from the residual-record cap; the cap is not an exact Python byte limit.

An exploratory pilot can check mechanisms and identify suitable benchmark sizes.
It does not establish novelty, a universal practical speedup, or a prospective
test of a method developed after inspecting those results.

Standard superincreasing membership is documented in the
[SageMath reference](https://doc.sagemath.org/html/en/reference/numerical/sage/numerical/knapsack.html).
The broader structural approach has relatives in
[backdoors to tractable classes](https://www.cs.cornell.edu/selman/papers/pdf/03.ijcai.backdoors.pdf).
Prior work on greedy core discovery and this precise deletion parameter still
needs a systematic literature audit.
