# Exact aggregate geometry and its cost

Positive weights w and target t are first subjected to the shared exact
target reductions and gcd normalization. Those steps preserve witnesses through
the existing Paper VI index maps. Below, w and t denote the current residual
problem. Discovery is a bounded heuristic, not a minimum-distance algorithm.

## An exact coordinate change

For any integer M >= 2, choose nonnegative nearest-integer quotients
p_i=floor((w_i+floor(M/2))/M), and signed r_i=w_i-M*p_i. Then for x in {0,1}^n,

    sum(w_i*x_i)=t iff M*q+s=t,
    where q=sum(p_i*x_i), s=sum(r_i*x_i).

Let R_minus=sum(min(0,r_i)), R_plus=sum(max(0,r_i)), and P=sum(p_i).
Every selection has R_minus <= s <= R_plus and 0 <= q <= P, so necessarily

    q_low=max(0,ceil((t-R_plus)/M))
    q_high=min(P,floor((t-R_minus)/M)).

If q_low>q_high, the residual problem is impossible. This is an exact integer
certificate, including for a subtree. It does not rely on the decomposition
being planted, an approximate statistical model, or a hard-family label.
Necessary range constraints alone do not prove YES.

## Exact two-coordinate dynamic programming

For each prefix j store the reachable pairs (q,s), with q from 0 through q_high
and s in the global interval [R_minus,R_plus]. The recurrence is

    S_0={(0,0)}
    S_j=S_(j-1) union {(q+p_j,s+r_j):(q,s) in S_(j-1)}.

Discard pairs with q>q_high. Because all p_i>=0, a discarded pair cannot return
to an admissible q. Global residual bounds contain every prefix selection, so
clipping to them loses nothing. Each q-row is a bitset over residual sums;
shift left/right by signed r_j, and update q in descending order. If p_j=0,
update each row once from its pre-update value, still using the item at most once.

If a reachable pair satisfies M*q+s=t, saved prefix rows reconstruct original
item indices. Checking prefixes permits valid early YES answers. After all
items, failure for every admissible q certifies NO. An interrupted DP, failed
allocation gate or deadline proves neither answer.

Let H=q_high+1 and W=R_plus-R_minus+1. DP arithmetic uses O(nH) bounded-width
integer bitset updates, not O(nH) uniform bit operations. A conservative bit-cost
bound is polynomial in input encoding times nHW. Saved witness prefixes require
at most (n+1)HW logical bit positions, plus Python object overhead. If H and W
are polynomial in full input length, this supplies a sufficient polynomial
regime even if M is numerically huge. Large H/W are not hardness certificates.

The implementation caps HW at 2,000,000 and prefix history at 64,000,000 logical
bits; actual allocations are measured separately. No exponential search is
hidden in feature extraction. Up to 24 candidate bases are proposed by a fixed
rule using minimum/median weight, powers of two and consecutive-weight gaps; all proposals
and representations are paid. Candidate choice first favors a certified empty
q interval, then minimum estimated history bits, width and base.

## Geometry, certificates and solver-specific difficulty

The binary hypercube projects to integer points in the (q,s) plane. Feasible
solutions lie on M*q+s=t. A narrow residual strip can leave that line between
integer q columns, or reduce exact search to a small represented region.
Relative residual width (R_plus-R_minus)/M, feasible q count and representation
size are geometric descriptors; no claim is made that they are true metrics,
optimal distances, complete hardness tests or calibrated probabilities.

For a successful NO at a DFS node with m undecided items, all 2^m assignment
leaves below that prefix are impossible. Removed prefixes have no descendants
visited later. This coverage count is not the number of DFS nodes actually
saved, particularly with memoization and ordinary range checks.

The large-base idea is established in decomposable-knapsack literature. This
bounded detector and elementary bitset implementation do not reproduce a
general lattice reformulation, nor establish a new subset-sum complexity bound.
Hardness results for individual-variable branch-and-bound do not automatically
apply to our generator or portfolio. See LITERATURE.md.
