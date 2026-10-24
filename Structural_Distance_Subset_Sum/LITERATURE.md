# Literature audit for the structural-distance note

**Audit date:** October 24, 2026. This is a scoped primary-source audit, not an
exhaustive novelty certification.

## Search scope

Searched combinations of subset sum with superincreasing core, maximum
superincreasing subsequence, deletion distance, structural parameterization,
backdoors, and output-sensitive attainable sums. Inspected the primary sources
below. Search results alone were not used as evidence that an algorithm is new.

## Established ingredients

1. **Superincreasing membership is classical.** Descending greedy recovery is
   documented in the [SageMath reference](https://doc.sagemath.org/html/en/reference/numerical/sage/numerical/knapsack.html)
   and in [Galbraith's cryptography text, chapter 19](https://www.math.auckland.ac.nz/~sgal018/crypto-book/ch19a.pdf).
   The core oracle is an existing tractable case.

2. **Branching on a small exceptional set is an established structural idea.**
   [Williams, Gomes, and Selman, *Backdoors To Typical Case Complexity*, IJCAI 2003](https://www.cs.cornell.edu/selman/papers/pdf/03.ijcai.backdoors.pdf)
   formalizes small sets of variables whose assignment exposes tractable
   structure in reasoning problems. Our decomposition has the same broad
   architecture. The general exponential-in-exceptions argument should not be
   presented as a new complexity principle.

3. **Reachable-support-sensitive subset sum is an active existing subject.**
   [Bringmann and Nakos, *Top-k-Convolution and the Quest for Near-Linear Output-Sensitive Subset Sum*](https://arxiv.org/abs/2107.13206)
   explicitly discusses the standard dynamic-programming dependence
   $O(n|\mathcal S(X,t)|)$ and develops faster output-sensitive methods. Our
   elementary sorted union for exceptional sums is not a new output-sensitive
   algorithmic primitive.

4. **Stronger support-sensitive bounds already exist.**
   [Bringmann, Fischer, and Nakos, *Beating Bellman's Algorithm for Subset Sum*](https://arxiv.org/abs/2410.21942)
   gives a bound of $\widetilde O(|\mathcal S(X,t)|\sqrt n)$ for the whole
   reachable support. This prevents comparing only against naive full subset
   enumeration when making broad algorithmic claims. The current experiment
   implements practical elementary baselines, not every asymptotically best
   theoretical algorithm.

5. **Other structural parameters already yield tractable families.**
   [Randolph and Węgrzycki, *Parameterized Algorithms on Integer Sets with Small Doubling*, ESA 2024](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ESA.2024.96)
   studies the doubling constant $|A+A|/|A|$ and derives structural subset-sum
   algorithms. This is related motivation, with a different parameter and
   algorithm from our deletion-to-superincreasing experiment.

6. **Pseudopolynomial algorithm comparisons also have a substantial literature.**
   [Chan, *Derandomizing Pseudopolynomial Algorithms for Subset Sum*, 2026](https://arxiv.org/abs/2601.01390)
   develops deterministic algorithms with nearly linear target dependence.
   Python integer-bitset DP is a practical baseline here, not a representation
   of the full state of the art.

## What this audit establishes

The framing, the tractable core oracle, branching on exceptions, and merging
reachable sums all have established relatives. The note should present its
elementary proofs as a concrete specialization and make its controlled
decomposition-cost experiment the immediate deliverable.

The scoped search did not identify a primary reference explicitly analyzing our
precise minimum deletion parameter together with this sorted greedy discovery
procedure. That absence is not evidence of novelty. No claim that the greedy
maximum-core lemma, the deletion bound, or one-swap selection is new is warranted
from this audit.

Before a publication novelty claim, follow the cited structural-parameter and
output-sensitive literature further, seek exact matches to the core-discovery
lemma, and compare against stronger algorithms in any regime for which a broad
advantage is proposed.

## Claim boundary for the frozen study

The study can establish correctness on its checked inputs and descriptive
cost differences between the implemented, predeclared methods on its synthetic
families. It can also show that a smaller residual support does or does not pay
for these particular selectors.

It cannot establish a new worst-case subset-sum bound, a globally optimal
decomposition, a universal speedup, or novelty merely because a matching title
was not found.
