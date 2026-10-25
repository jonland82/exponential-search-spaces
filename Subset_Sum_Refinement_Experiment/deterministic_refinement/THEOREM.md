# Certified range and collision refinement for subset sum

This is a proof and implementation note for the continuation study. Paper III
is unchanged. No novelty or asymptotic speed claim is made here.

## Assumptions and notation

Let $w$ be a nonempty list of positive integer weights, $D$ a finite nonempty
set of integer targets, and $d=|D|$. Targets are uniform on $D$.
Partition the indices into two blocks and let $A,B$ be their **distinct**
attainable sums, including zero. Let $\mathcal A(w)=A+B$ and

$$
r(t)=|\{(a,b)\in A\times B:a+b=t\}|,\quad
N=|\mathcal A(w)\cap D|,\quad q=N/d,
$$

$$
M=\sum_{t\in D}r(t),\qquad
J=\sum_{t\in D}\binom{r(t)}2.
$$

Suppose $L\le N\le U$ are existing integer support-count bounds,
$J_-\le J\le J_+$ are certified collision bounds, and
$R\ge\max_{t\in D}r(t)$ is a positive integer. An estimated maximum is
insufficient. The basic certified cap is $\min(|A|,|B|)$.

## Proposition: integer-strengthened interval

For $M>0$,

$$
\boxed{
\max\left\{L,\ M-J_+,\
\left\lceil\frac{M^2}{M+2J_+}\right\rceil,\
\left\lceil\frac M R\right\rceil\right\}
\ \le N\le\
\min\left\{U,d,\ M-\left\lceil\frac{2J_-}{R}\right\rceil\right\}.
}
$$

Divide the integer endpoints by $d$ only when displaying probabilities.
When $M=0$, $N=q=0$; no division by $M$ or $R$ is required.

**Proof.** Every reachable target contributes at least one representation, and

$$
M-N=\sum_{r(t)>0}(r(t)-1),\qquad \sum_t r(t)^2=M+2J.
$$

For positive integer $r$, $r-1\le\binom r2$. Thus $N\ge M-J\ge M-J_+$.
Cauchy–Schwarz gives $M^2\le N(M+2J)\le N(M+2J_+)$.
Also $M\le RN$, giving $N\ge M/R$.
Finally,

$$
2J=\sum_t r(t)(r(t)-1)\le R\sum_{r(t)>0}(r(t)-1)=R(M-N).
$$

Hence $N\le M-2J/R\le M-2J_-/R$. Integer rounding and intersection
with $[L,U]$ prove the statement. $\square$

The $M/R$ bound is already implied by the second-moment bound when
$J_+\le (R-1)M/2$; it is retained as an explicit elementary certificate.

## Why the range correction improves the original count bound

Write $c_j$ for each distinct weight value's multiplicity and
$K=\prod_j(c_j+1)$. Keep **all copies of each value together** in one
block. Then

$$
N\le M\le |A||B|\le K.
$$

Each block's distinct sums are no more numerous than its count patterns;
the product of the two block pattern counts is $K$. Arbitrary index
partitions preserve the representation identities but may violate the last
inequality: splitting two copies of 1 gives four pairs and $K=3$.

For an integer interval $D=[\mathrm{lo},\mathrm{hi}]$, sorted $B$ permits
counting $M$ by two binary searches per $a\in A$.
For the study's residue-filtered interval, every attainable pair sum already
passes every filter, so the same shortcut is sound. For an arbitrary
residue-restricted $D$, filter membership must be accounted for explicitly.

Partitioning uses ascending distinct values, assigning each complete group
to the block of smaller accumulated $\sum_j\log_2(c_j+1)$, with ties going
to the first block. Floating-point balancing affects speed and partition
choice, never the validity of the integer certificates.

## Partial collision certificates

For a positive integer difference $\delta$, set

$$
A_\delta=\{a\in A:a+\delta\in A\},\qquad
B_\delta=\{b\in B:b-\delta\in B\}.
$$

Then

$$
J=\sum_{\delta>0}|\{(a,b)\in A_\delta\times B_\delta:a+b\in D\}|.
$$

**Proof.** In each unordered pair of distinct representations of the same
target, order the $A$ coordinates increasingly as $a<a+\delta$. Equality
of the sums forces the $B$ coordinates to be $b>b-\delta$. This is a
bijection with one term of the sum, and $\delta>0$ makes the count unique.
$\square$

Summing any set of **distinct** positive differences yields a certified
$J_-$. Choosing those differences adaptively preserves deterministic
validity because each accepted contribution is verified exactly.
This implementation chooses at most 8 or 32 shared adjacent half-sum gaps,
ordered by decreasing product of adjacent-gap frequencies, breaking ties
by increasing integer difference. Membership checks build $A_\delta$ and
$B_\delta$; interval counts avoid their full Cartesian products.

## A universal collision upper bound

Write $M=hR+s$, $0\le s<R$. Then

$$
J\le J_+ := h\binom R2+\binom s2\le\frac{(R-1)M}{2}.
$$

**Proof.** For integer cell occupancies bounded by $R$ and totaling $M$,
moving one unit from a smaller positive cell to a larger nonfull cell
cannot decrease $\sum\binom r2$. Repetition leaves $h$ full cells and
one remainder. Ignoring the number and arrangement of target cells only
enlarges the feasible class, so this maximum remains an upper bound.
$\square$

## Stronger residue matching cap

For a positive modulus $m$, let $a_i,b_i$ count the elements of $A,B$
in residue $i$. A target with residue $s$ has

$$
r(t)\le H_m(s):=\sum_{i=0}^{m-1}\min(a_i,b_{(s-i)\bmod m}).
$$

**Proof.** Within one $A$ residue class, $b=t-a$ is uniquely determined
by $a$ and vice versa. Exact-sum pairs therefore form an injective matching,
of size at most the smaller residue-class population. Sum over disjoint
$A$ residue classes. $\square$

Consequently $R=\min\{\min(|A|,|B|),\max_s H_{16}(s),\max_s H_{64}(s)\}$
is certified. Taking maxima over all residues is safe for every $D$.
This improves on the transcript's product cap
$C_m(s)=\sum_i a_i b_{s-i}$, since $\min(x,y)\le xy$ for nonnegative
integers. No floating-point convolution is used.

## Cost and verification

Half-sum construction can still be exponential. Once sorted halves exist,
range counting costs $O(|A|\log|B|)$; checking $k$ differences costs at most
$O(k(|A|+|B|+|A|\log|B|))$ with linear auxiliary space per difference.
The residue cap here costs $O(|A|+|B|+m^2)$ per modulus. Sorting and selecting
adjacent gaps are charged. These are costs in numbers of Python operations;
integer bit complexity is not constant in general.

The test suite independently enumerates subsets on all weight multisets
of lengths 1 through 6 over $\{1,2,3,4\}$, plus 1,200 attempted random
cases with irregular periodic target sets, zero-support and singleton cases,
and the documented $(10,20,30,100)$ example. It checks the full positive-
difference identity, lower and upper collision certificates, representation
caps, integer endpoints, exact bitset labels, and uniform target-rank mapping.
An independent integer optimization checks the extremal collision upper
bound. Random tests supplement the proof; they are not its justification.

The full histogram is used only as an evaluation oracle on the old cohort.
No tested certificate method or sampling decision can read exact support
counts or that histogram.

## Sampling baseline and stopping

Uniform targets are sampled independently with replacement by exact rank
mapping in $D$. Each receives an exact meet-in-the-middle YES/NO label.
At $m\in\{128,512,2048\}$, Hoeffding's radius is

$$
e_m=\sqrt{\frac{\log(2/\alpha_m)}{2m}},\qquad \alpha_m=0.05/3.
$$

Intersect $[\widehat q-e_m,\widehat q+e_m]$ with the original deterministic
interval. A union bound gives at least 95% simultaneous coverage for all
three checkpoints on each fixed list. Stopping at a reported checkpoint
therefore preserves this guarantee. Empty intersections count as misses
and never as successful accuracy attainment. The deterministic algorithms
have no sampling coverage parameter: their containment is pointwise.
