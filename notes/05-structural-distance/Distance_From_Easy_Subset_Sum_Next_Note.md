# How Far from Easy? Certified Structural Distance in Subset Sum

**Working prospectus for a new companion note; proposed Note V.**

**Status:** Research prospectus with a first proved and implemented milestone, October 24, 2026. See the [theory and proofs](../../Structural_Distance_Subset_Sum/THEORY.md), [solver and validation instructions](../../Structural_Distance_Subset_Sum/README.md), and progress update below. Literature novelty and a practical advantage over strong baselines remain open.

## 1. The question

> How far can a list depart from an easily solved structure before the unresolved search becomes large?

The earlier notes introduced certified coverage, tested exact pairing and pruning, bounded random-target reachability probabilities, and studied certified approximation. This note returns to the exact subset-sum decision problem and makes the structural part of the coverage framing concrete.

For positive integer weights $w=(w_1,\ldots,w_n)$ and an integer target $t$, ask whether

$$
\sum_{i=1}^n x_iw_i=t,
\qquad x_i\in\{0,1\}.
$$

The direct search has $2^n$ binary choices. Our proposed solver searches for an easily solved core, verifies its structure, and explicitly resolves only the remaining uncertainty.

We want both a theorem and a costed experiment:

- A theorem identifying families on which structure discovery and exact solution take polynomial time.
- An experiment measuring when discovering and exploiting that structure beats existing exact methods.

A single fast run does not establish a polynomial family. Conversely, a polynomial guarantee need not produce a practical timing advantage.

## 2. First structure: a superincreasing core

A sorted list $a_1,\ldots,a_m$ is superincreasing when

$$
a_i>\sum_{j<i}a_j
\qquad\text{for every }i.
$$

For positive weights, this condition also allows the empty list and one-element lists as trivial cases.

Membership in its reachable-sum set is decided greedily, from largest to smallest. If the current target remainder $r$ is below $a_i$, including $a_i$ is impossible. If $r\ge a_i$, excluding $a_i$ is impossible because all smaller weights together total less than $a_i$. Choose the forced branch and continue. A final remainder of zero gives a witness; otherwise there is no solution.

After sorting, a membership query uses $O(m)$ arithmetic operations. This is a standard tractable case, including when the weights are numerically large.

For example, consider

$$
w=[2,5,6,11,23].
$$

Removing $6$ leaves the superincreasing core $[2,5,11,23]$. For target $17$, the solver tests the core against $17$ and $17-6=11$. The second query succeeds, giving the original witness $6+11=17$.

## 3. A precise distance and a polynomial discovery procedure

Define the deletion distance

$$
k(w)=
\min\left\{
|E|:
\text{removing the indexed items in }E
\text{ leaves a superincreasing list}
\right\}.
$$

Items are indexed: two equal weights are separate selectable copies. Sorting changes their order, not their identities.

Finding a good core must be part of the algorithm. We should not assume that the decomposition is supplied for free.

### Greedy discovery

The first implementation improves the originally planned discovery procedure. Sort the weights, start with total zero, and keep each weight exactly when it exceeds the total already kept.

The scan finds a maximum-size superincreasing core. For every feasible length, its accepted prefix also has minimum total: compared with any superincreasing selection, its next item is accepted no later and is no larger. Induction gives both claims. The complete proof is [Theorem 1 in the theory note](../../Structural_Distance_Subset_Sum/THEORY.md).

Discovery therefore uses $O(n\log(n+1))$ arithmetic/comparison operations, including sorting, and $O(n)$ records. The dynamic program below remains a valid reference construction, with a weaker runtime bound.

### Reference construction: minimum-total dynamic programming

Sort the input as $a_1\le\cdots\le a_n$. Let $D_{i,\ell}$ be the minimum total of any superincreasing selection of $\ell$ items from the first $i$ items. Set it to $+\infty$ when no such selection exists.

The initial conditions are

$$
D_{0,0}=0,
\qquad
D_{0,\ell}=+\infty\quad(\ell>0).
$$

For $\ell\ge1$, the recurrence is

$$
D_{i,\ell}=
\begin{cases}
\min\{D_{i-1,\ell},\,D_{i-1,\ell-1}+a_i\},
& D_{i-1,\ell-1}<a_i,\\
D_{i-1,\ell},
& D_{i-1,\ell-1}\ge a_i.
\end{cases}
$$

Also set $D_{i,0}=0$.

The reason one minimum total per length suffices is a dominance argument. If a selection of length $\ell-1$ can be extended by $a_i$, then a selection of the same length with a smaller total can also be extended. Its resulting total is no larger, so it is at least as useful for every later extension.

Let

$$
m^*=\max\{\ell:D_{n,\ell}<+\infty\}.
$$

Then

$$
k(w)=n-m^*.
$$

The table takes $O(n^2)$ arithmetic operations. Predecessor records recover an actual maximum-size core and its exceptional items. The implementation must preserve valid predecessor histories; copying whole selections at every update would introduce extra work.

The first milestone establishes optimality through the stronger greedy invariant. Independent exhaustive checks compare every greedy prefix total with the minimum over all feasible selections on small inputs.

## 4. The initial exact solver and its guarantee

Partition the indexed input into a verified core $C$ and exceptional items $E$, with $|E|=k(w)$.

Enumerate exceptional selections. For each selection with total $s$, ask whether the core reaches $t-s$. A successful query combines the two selections into a witness for the original input.

This gives the arithmetic-operation bound

$$
T(w,t)=O\!\left(n\log(n+1)+(n+1)2^{k(w)}\right).
$$

The algorithm is exact for both YES and NO answers. A NO answer follows only after every exceptional possibility has been covered by an exact core query or a sound exclusion.

In particular, if a family satisfies

$$
k(w)\le c\log_2 n
$$

for a fixed constant $c$, then

$$
T(w,t)=O\!\left(n\log(n+1)+n^{c+1}\right).
$$

This is a sufficient polynomial regime for this algorithm. A larger distance does not prove that an input is hard, nor that another algorithm needs exponential time.

These are arithmetic-operation bounds. A full theorem must account for the binary input length $L$, including the weights and target. All intermediate sums have polynomially bounded bit lengths in $L$, giving a bound of the form

$$
\operatorname{poly}(L)\,2^{k(w)}.
$$

The important guarantee includes finding and verifying the core.

## 5. A sharper measure: distinct exceptional sums

Exception count is only an initial measure of uncertainty. Different exceptional selections may have the same sum and therefore pose the same query to the core.

Define

$$
\mathcal A(E)=
\left\{
\sum_{i\in B}w_i:B\subseteq E
\right\},
\qquad
M(E)=|\mathcal A(E)|.
$$

Always,

$$
1\le M(E)\le2^{|E|}.
$$

If all $k$ exceptional weights equal the same positive value $v$, their distinct sums are

$$
\{0,v,2v,\ldots,kv\},
\qquad M(E)=k+1.
$$

Thus many exceptional items can still leave only polynomially many residual queries.

Construct the sorted distinct-sum list incrementally:

$$
S_0=\{0\},
\qquad
S_{j+1}=S_j\cup(S_j+e_{j+1}).
$$

Merge sorted lists and remove duplicates, retaining one witness per sum. Every prefix sum remains attainable after adding more items by omitting those new items, so $|S_j|\le M(E)$. Construction therefore takes $O(kM(E))$ arithmetic operations.

Querying the core once per distinct exceptional sum gives

$$
T(w,t)=
O\!\left(n\log(n+1)+kM(E)+(n+1)M(E)\right)
=O\!\left(n\log(n+1)+(n+1)M(E)\right).
$$

Here $E$ is the remainder of the selected core, not a target-independent optimal remainder under every possible decomposition.

The stronger sufficient condition is

$$
M(E)=\operatorname{poly}(n),
$$

even when $|E|$ is much larger than $\log n$.

This changes the next optimization problem:

> Which cheaply discoverable core leaves the least expensive unresolved problem?

A maximum-size core minimizes deletion count. It need not minimize the number of distinct exceptional sums or total solution cost. We should compare these objectives without assuming that optimizing the stronger objective is easy.

## 6. What the prototype should do

The initial implementation should:

1. Find a maximum-size superincreasing core using the dynamic program.
2. Verify its defining inequalities independently.
3. Generate distinct exceptional sums with recoverable indexed witnesses.
4. Query the core exactly for each relevant residual target.
5. Return YES with a checked original-input witness, or NO after complete coverage.
6. Record the costs of discovery, verification, sum construction, and queries separately.

Record $n$, $k$, $M$, input bit lengths, peak stored states, attempted updates, core queries, time, and memory. Distinguish item selections from distinct sum states when reporting coverage.

Simple bounds such as $t-s<0$ or $t-s>\sum_{i\in C}w_i$ can reject queries immediately. Any additional residue certificates must also be costed.

Use a declared resource budget. A run that exhausts it returns **unresolved**, together with its work measurements. It must not return NO or classify the instance as inherently hard.

Independent checks should include exhaustive enumeration on small inputs, duplicate weights with distinct indices, target zero, impossible targets, reconstruction correctness, and the optimality of the detected core. Larger validation should state which independent exact method was feasible.

## 7. Controlled experiments

### Generators and targets

Begin with verified superincreasing cores and add several kinds of disruption:

- Unrelated exceptional weights.
- Repeated exceptional values.
- Exceptional values with many additive collisions.
- Numerical perturbations of core weights.

Also include unstructured lists, easy interval-covering lists, and the earlier independent and repeated-pair families. These reveal where the chosen structural parameter is informative and where another representation is better.

Measure the actual detected $k$ and $M$. The number of injected items is not necessarily the minimum deletion distance: an alternative core may retain some of them.

Vary total list size and disruption separately. Report bit lengths and numerical ranges so that the cost of arithmetic and feasibility of target-indexed methods are visible.

Use a stated target-generation rule. Include independently labeled YES and NO targets where feasible, and report them separately. Preserve trivial root rejections as a separate stratum. Do not interpret planted-YES speed alone as evidence of efficient exhaustive coverage.

### Baselines and accounting

Compare:

- Ordinary meet-in-the-middle with duplicate sums merged.
- Integer-bitset dynamic programming where its declared memory limit permits it.
- The existing memoized bounded search.
- Core search enumerating exceptional selections.
- Core search merging distinct exceptional sums.

The last two separate the benefit of the structural decomposition from the benefit of merging residual states.

Charge all preprocessing and certificate work. For repeated targets on the same list, report a separate workload showing preprocessing cost and amortized query cost; do not mix it with single-target timings.

Freeze the solver variants, generators, seeds, resource caps, and reported metrics before the prospective comparison. Use exploratory data for development and fresh data for the final comparison.

### Main figures

The main result should map where the methods succeed and where their costs grow:

- Total work versus $n$ at controlled structural distances.
- Total work versus $k$, with $M$ shown separately.
- Residual query counts versus $M$.
- Time and memory relative to the strongest feasible baseline on the same inputs.
- Completion and budget-exhaustion rates, with YES and NO results separated.

The $2^k$ and $M$ expressions are upper bounds for the proposed implementations. Empirical curves do not establish matching lower bounds for subset sum.

## 8. Adaptive recognition during search

After establishing the initial decomposition baseline, test recognizing structure again inside the search.

A partial assignment changes the remaining list and target. New bounds may force choices, eliminate unusable weights, or expose an easier remainder. A recursive solver could:

1. Apply cheap exact exclusions and forced choices.
2. Check for a cheaply recognizable tractable remainder.
3. Solve that remainder directly when recognized.
4. Otherwise branch and merge equivalent residual states.

Compare recognition only at the root with recognition at selected nodes. Count the recognition work even when it finds nothing.

The question is whether repeated recognition saves more branching than it costs. A proposed theorem here must bound both the number of expanded states and all recognition and terminal-solver work. The deletion-distance theorem does not automatically establish such a guarantee.

## 9. Extend the library of tractable cores

Once the first mechanism is understood, consider:

- **Certified interval coverage:** a sorted core beginning with $1$ and satisfying $a_i\le1+\sum_{j<i}a_j$ reaches every integer from zero to its total.
- **Few distinct values:** count how many copies of each value are chosen.
- **Small reachable-sum sets:** merge exact partial sums when only polynomially many survive.
- **Arithmetic progressions or unions of intervals:** use them only with proved construction, update, membership, and witness-recovery costs.

For any proposed representation, ask:

1. How do we discover and verify it?
2. How expensive is an exact residual query?
3. How much unresolved information remains outside it?
4. Can intermediate representations become large even when the final one is small?

The long-term objective is a solver that selects a useful certified representation and bounds the remaining work.

## 10. Relationship to the earlier notes and existing work

In Note I's language, the core supplies a cheap exact procedure covering many original choices. The exceptional problem measures what still needs explicit resolution. Merging equal exceptional sums gives another exact representation, reducing the residual queries further.

Notes II and IV show why every discovery, representation, and verification cost must be included. The new experiment should retain that discipline.

The first version of this note concerns a fixed target and exact correctness. A later connection to Note III could reuse the decomposition across random targets. Computing reachability probability requires counting distinct reachable targets or their probability mass; adding counts from overlapping translated core sets would be invalid.

The general idea has established relatives in structural parameterization and backdoors to tractable classes. Relevant starting points include:

- [Williams, Gomes, and Selman, *Backdoors To Typical Case Complexity*](https://www.cs.cornell.edu/selman/papers/pdf/03.ijcai.backdoors.pdf).
- [Guo, Hüffner, and Niedermeier, *A Structural View on Parameterizing Problems: Distance from Triviality* — author presentation](https://hueffner.de/falk/slides/iwpec04.pdf).
- [SageMath documentation for superincreasing subset sum](https://doc.sagemath.org/html/en/reference/numerical/sage/numerical/knapsack.html).
- [Randolph and Węgrzycki, *Parameterized Algorithms on Integer Sets with Small Doubling: Integer Programming, Subset Sum and k-SUM*](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ESA.2024.96), which studies a different measure of additive structure.

Before claiming novelty, investigate prior work on superincreasing-core discovery, deletion distance, structural subset-sum parameters, and algorithms sensitive to the number of attainable sums. The elementary decomposition bound is a starting point. A contribution would need to be established through a stronger parameter, a better discovery procedure, a useful adaptive guarantee, or a demonstrated computational advantage.

## 11. First deliverable and proposed narrative

The first deliverable is:

1. A proof of the core-discovery recurrence and exact solver.
2. The $k$-dependent and distinct-sum-dependent runtime bounds, including bit costs.
3. A verified implementation with indexed witnesses and explicit resource limits.
4. A frozen prospective experiment comparing total work against meaningful exact baselines.
5. A chart locating the regimes where structural discovery pays for itself.

The proposed note's narrative is:

> Some subset-sum lists admit cheap exact solution because their choices have exploitable structure. We measure departure from one such structure, discover a largest tractable core in polynomial time, and confine the explicit search to its exceptions. The number of distinct exceptional sums can matter more than the number of exceptional items. Proofs identify sufficient polynomial regimes; experiments determine when obtaining and using the decomposition is computationally worthwhile.

The broader research question is:

> How much independent uncertainty remains after all cheaply verifiable structure has been used?

## 12. First milestone completed: October 24, 2026

The [implementation package](../../Structural_Distance_Subset_Sum/README.md) now contains:

- A proof that sorted greedy discovery finds a maximum-cardinality superincreasing core, improving discovery from the planned $O(n^2)$ to $O(n\log(n+1))$.
- Exact exceptional-selection and distinct-exceptional-sum solvers, with indexed witnesses and honest unresolved outcomes under resource limits.
- Independent meet-in-the-middle, bounded-search, and decision-only bitset baselines.
- Eight test groups covering exhaustive core optimality, all-target exact answers, witnesses, large integers, repeated items, and resource limits.
- An exploratory pilot with preserved inputs, labels, source versions, measurements, and a chart.

The [milestone findings and immediate next steps](../../Structural_Distance_Subset_Sum/MILESTONE.md) link the checked pilot report. All 444 completed pilot answers agreed with independent exact labels, but ordinary bounded search remained competitive. The pilot is development evidence. A larger frozen prospective comparison, separate byte-memory profiling, adaptive recognition, and the literature audit remain future work.

There is already a concrete reason to compare decompositions. On $[1,1,1,2,3]$, both $[1,2]$ and $[1,3]$ are maximum-size cores. The first leaves six exceptional sums; the second leaves five. Minimizing deletion distance does not necessarily minimize the remaining search.

## 13. Frozen comparison completed: October 24, 2026

The [study findings](../../Structural_Distance_Subset_Sum/FINDINGS.md) and
[full report](../../Structural_Distance_Subset_Sum/results/prospective_20261024/REPORT.md)
now supply the next stage. A local protocol freeze and protected source
snapshots preceded generation of 60 fresh lists and 180 targets. The cohort
contains 60 YES and 120 NO targets, including 60 NO targets that pass the
declared range, gcd, and residue checks.

Seven methods ran three timing repetitions each, producing 3,780 measurements.
All 3,117 completed timing answers agreed with independent exact labels; 663
runs reached declared limits. A separate predeclared memory pass produced 28
profiles, with 24 completed and correct answers. The expanded independent test
suite has 16 passing groups.

Two verified one-swap selectors reduced exceptional support on 18 of 54
structured lists. Neither was faster than the simple greedy-core distinct-sum
solver on any of the 162 structured target cases. Their overall paired median
time ratios to that solver were 9.034 and 9.211. The cheap selector had five
control-case wins, all with the same selected core and support as the simple
method; the exact-probe selector had none.

The new note can therefore combine a constructive polynomial-regime theorem
with a controlled limitation: reducing residual support is insufficient when
discovering the improved decomposition costs more than it saves. The literature
audit identifies established ingredients and does not establish novelty.
