# Costed alternatives to a maximum-size core

## Candidate neighborhood

Start with the maximum-cardinality greedy core $C$ and complement $E$. Consider
every single-index exchange

$$
C'=(C\setminus\{i\})\cup\{j\},
\qquad i\in C,\quad j\in E.
$$

Sort $C'$ and retain it only after verifying its superincreasing inequalities and
indexed partition. Its cardinality equals the original maximum, so the exchange
preserves minimum deletion distance. Equal-value exchanges and repeated core
weight sequences are redundant for support size and are omitted.

For each complement, compute the multiplicity cap

$$
H(E')=\prod_v(c_v(E')+1),
\qquad M(E')\le H(E')\le2^{|E'|}.
$$

The cap counts how many copies of each value can be chosen. Different such
choices may still collide additively. Ranking by $H$ does not guarantee ranking
by actual $M$.

Rank candidates by $H$, then core total, then sorted core weights. Retain the
original core plus the three best alternative weight sequences. All scanning,
sorting, rejected checks, and ranking are charged.

## Two policies

**Multiplicity policy:** select the minimum-ranked core, construct its residual
support, and query it exactly.

**Support policy:** construct supports for all retained candidates, choose
minimum $M$ with the same rank for ties, retain one indexed representative per
sum, and reuse the winning support for exact queries. Count the best retained
support while building another support; a losing support is released before the
next construction.

The support policy can use strictly more memory and time than the simple solver.
If a budget expires before selection or querying is complete, return unresolved.
An interrupted selector does not publish an intermediate probe's $M$ as its final
selected support size.

## Correctness and complexity

Every selected core is verified. The exact partition equivalence and query lemma
in [THEORY.md](THEORY.md) apply unchanged. Thus selecting any retained candidate
preserves YES and NO correctness.

Let $m=|C|$, $k=|E|$, and $b\le4$ be the retained pool size. A conservative
arithmetic/comparison bound for the implemented one-swap scan is

$$
O\!\left(mk\,n\log(n+1)\right).
$$

This includes sorting and checking candidates, polynomial ranking work, and
deduplication in the ordinary RAM model. In a bit model, hashing, comparisons,
and products require their usual additional polynomial costs.

For the support policy, let the probed complements have sizes $M_1,\ldots,M_b$.
Its further work is bounded by

$$
O\!\left(k\sum_{j=1}^b M_j+(m+1)\min_j M_j\right).
$$

The winning support is not rebuilt. However, a candidate with a large support
can make selection expensive even if the winning support is small. It would be
incorrect to state a bound depending only on the winner's $M$ for this policy.

Since $b\le4$ and every complement has $k$ items,

$$
\sum_j M_j\le4\cdot2^k.
$$

The policy therefore preserves a bound of the form

$$
\operatorname{poly}(L)\,2^{k(w)},
$$

including discovery. It preserves the logarithmic-deletion sufficient polynomial
regime. It is not guaranteed to preserve a favorable bound in terms of the
original greedy complement's $M$ alone.

## Interpretation of the experiment

Support reduction and total time reduction are separate outcomes. Compare both,
and charge the probes that were rejected. Candidate selection is independent of
the target and uses no labels, but its entire cost is included for every
single-target run.

The neighborhood is local. Neither policy claims a globally minimum-support
core. The comparison asks whether these inexpensive-to-describe, verified choices
pay for their actual discovery and probing cost.
