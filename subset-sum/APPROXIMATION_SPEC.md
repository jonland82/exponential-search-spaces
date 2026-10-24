# Certified approximation to a fixed target

Series navigation: [reading order](../index.html#arc) · [Note IV: pairing in certified approximation](../notes/04-certified-approximation/Certified_Approximation_of_Subset_Sum.html).

**Central question:** "If we only need to get close to the target, and know how close, can our framework avoid much of the exponential search?"

This extends the series with a fixed-target optimization problem. Note III's random-target probability remains a separate objective. Start with deterministic bounds; statistical confidence and learned guidance are outside this first experiment.

The empirical question for Note IV is whether pairing adds a computational benefit beyond the same approximation rule used sequentially. The main contribution is a controlled negative timing finding, with the state-cap exception retained. The mathematics below establishes a common accuracy contract for that comparison; it does not claim a new approximation-complexity result.

## Contract

Let positive integer weights be $w_1,\ldots,w_n$, their total be $S$, and the integer target be $t$. Both undershooting and overshooting are permitted. Define

$$d^*=\min_{x\in\{0,1\}^n}\left|\sum_i x_iw_i-t\right|.$$

Given an absolute integer tolerance $\eta\ge0$, return a subset witness with sum $z$, bounds $\ell,u$, and a status. A successful result must satisfy

$$0\le\ell\le d^*\le u=|z-t|,\qquad u-\ell\le\eta.$$

Thus the witnessed subset is at most $\eta$ worse than the best possible distance, with a deterministic certificate. A state-limit result retains valid bounds but does not claim to meet the requested tolerance. No solver is given the exact optimum. The benchmark chooses $\eta=\lfloor\varepsilon S\rfloor$ and records both quantities. This scale must be stated: one percent of total weight can be a substantial absolute miss.

## Summary invariant and composition

For an item group $B$, store $(R_B,E_B)$. Every representative $r\in R_B$ is an actual subset sum of that group, with its original-item bit mask. Require

$$\forall s\in A(B),\quad\exists r\in R_B:\quad r\le s\le r+E_B.$$

The initial empty group has $R=\{0\}$ and $E=0$. Adding a weight takes the sorted merge of $R$ and $R+w$. This preserves the old error. In that merged list, keep its smallest element, then discard each subsequent value $y$ if it is within $h$ above the most recently retained value $r$. Each retained value remains witnessed. If the largest gap actually discarded at that step is $g\le h$, the new covering error is $E+g$.

**Proof.** Any true sum $s$ previously had a candidate $y$ with $y\le s\le y+E$, including when the new weight is selected. Its retained representative satisfies $r\le y\le r+g$. Therefore $r\le s\le r+g+E$. Duplicate-value merges introduce zero error. Induction proves the invariant over any number of updates.

For disjoint groups $B,C$, combining their representatives gives covering intervals

$$[r_B+r_C,\ r_B+r_C+E_B+E_C].$$

**Proof.** Choose representatives for each true component sum and add the two inequalities. Their masks select disjoint items, so bitwise OR recovers a valid combined witness. If the combined list is trimmed again, add that trim's observed maximum gap as well. This is the approximation counterpart of the exact paired-summary condition in Note I.

## Obtaining bounds without enumerating all paired sums

For a complete summary, or a combination of two disjoint summaries covering all items, let $\mathcal I$ be the corresponding collection of intervals. Define

$$\ell=\min_{I\in\mathcal I}\operatorname{dist}(t,I),\qquad u=\min_{r\in R}|r-t|,$$

where in the paired case $R=R_B+R_C$. A better independently witnessed subset may further lower $u$.

**Proposition.** If every interval has width at most $E$, these bounds satisfy $\ell\le d^*\le u$ and $u-\ell\le E$.

**Proof.** Every attainable sum lies in the union of intervals, so distance to that union is a lower bound. Representatives are attainable, so their nearest distance is an upper bound. Choose an interval attaining the minimum lower bound. Its witnessed left endpoint lies at distance at most $\ell+E$ from the target. Taking the best witnessed distance proves the gap bound. An additional valid witness can only improve it.

For sorted half summaries, the conventional two-pointer nearest-pair search finds the largest pair sum below the target and the smallest above it in $O(|R_B|+|R_C|)$ steps. Those two values also minimize distance to the intervals $[r_B+r_C,r_B+r_C+E]$: either the predecessor's interval reaches the target, or its right endpoint and the successor's left endpoint are the closest interval boundaries. No Cartesian-product list is constructed.

## Error budget and cost

Use $h=\lfloor\eta/n\rfloor$ for each of the $n$ item updates, whether arranged sequentially or as two half summaries. Then the sum of observed discarded gaps is at most $nh\le\eta$. Each completed summary therefore provides the required certificate.

Representatives in a sum range $[0,S_B]$ are separated by at least $h+1$ because sums are integers. Consequently

$$|R_B|\le 1+\left\lfloor\frac{S_B}{h+1}\right\rfloor.$$

For $\eta>0$, $h+1>\eta/n$, giving $O(1+nS/\eta)$ representatives. Sorted merging and trimming take linear time in the incoming list size. Sequential and paired constructions both take at most $O(n+n^2S/\eta)$ arithmetic operations; the paired query is linear in its two summary sizes. With actual normalized tolerance $\eta/S>0$ fixed, this is polynomial in $n$ and inverse tolerance. Weight sums use $O(\log(S+1))$ bits and witness masks use $O(n)$ bits, so bit costs are also polynomial in encoded input length and inverse tolerance. This is a coarse upper bound, not a claimed improvement over established approximation schemes.

At $\eta=0$, no unequal sums may merge and no such approximation bound follows. On integer inputs any certified interval narrower than one identifies the exact integer optimum. A multiplicative approximation to $d^*$ would also require exact success when $d^*=0$, which is why this experiment uses an additive guarantee.

The benchmark imposes a 65,536-state cap per individual summary. The theoretical guarantee above describes the unrestricted algorithm; the executable reports a state-limit status if it cannot finish within that cap. Two-half methods can hold two such lists, plus a list under construction, so the cap is not a common total-memory limit. Separate peak-memory measurements expose that cost.

## Comparators and attribution

- **Paired additive:** two downward-trimmed half summaries, with errors added, followed by a linear nearest-pair query.
- **Sequential additive:** the same additive rule on one full list. This isolates the effect of organizing the computation into halves.
- **Multiplicative trimming:** a conventional trimmed-list baseline adapted to preserve both sides of the target. Discard $y$ above retained $r$ when $y-r\le\delta r$, using $\delta=\eta/(nS)$ and integer cross multiplication. Since $r\le S$, each dropped gap is at most $\eta/n$; the same observed-error invariant supplies the certificate. This is a transparent baseline, not the fastest known approximation implementation.
- **Exact-half MITM:** exact half summaries and a nearest-pair query. It solves the same two-sided distance objective. It can stop early at the requested tolerance, just like the approximate methods.

All methods share item ordering, endpoint witnesses, optional greedy witnesses, original-item mask reconstruction, and witness-based stopping. A witness with distance $u\le\eta$ already supplies the certificate $[0,u]$, even before summaries are complete. Such an outcome demonstrates early discovery, not compression. An ablation disables the common greedy search; it still permits valid witness-based stopping during construction. There is no branch-exclusion mechanism in this first implementation beyond stopping on a sufficient witness.

## Established context

The conventional list-trimming approximation idea is described in the [University of Illinois CS 473 notes](https://courses.grainger.illinois.edu/cs473/fa2015/w/lec/slides/10_notes.pdf). Those notes optimize the largest sum at most the target; this experiment explicitly adapts the baseline to two-sided distance and an additive certificate. [Bringmann and Nakos, *A Fine-Grained Perspective on Approximating Subset Sum and Partition*](https://arxiv.org/abs/1912.12529) situate approximation within a much stronger algorithmic literature. The contribution being tested here is the cost and behavior of a concrete coverage implementation, not the invention of approximate subset sum.
