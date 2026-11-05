# Certified pruning from overlap between block sums

[Standalone paper: PDF](Certified_Block_Overlap_in_Subset_Sum.pdf) |
[LaTeX source](Certified_Block_Overlap_in_Subset_Sum.tex) |
[Paper evidence and plot data](paper_evidence.json)

The working draft, *Certified Block Overlap in Subset Sum*, develops
the argument below as a standalone graduate-level paper: interval geometry,
the search theorem, optimal contiguous discovery, separated and perturbed
families, and verification. Two reproducible plots explain the interval test
and contrast global support size with local dictionaries and paid counters.

Research draft, November 4, 2026. This note gives a constructive sufficient
condition for polynomial-time exact subset sum, including discovery costs.
The proofs are elementary; literature novelty is not established. It does not
assert a general subset-sum speedup or a lognormal law for actual runtimes.

The representation assigns each small block a list of its distinct sums. A
sum in a high block can only be completed inside an interval whose width is
the total of all lower blocks. The maximum number of overlapping intervals
bounds the number of branches that survive. The product of these bounds
provides a computable upper bound on the search, with an explicit cost for
constructing the representation.

## 1. Model and the exact exclusion rule

The input consists of indexed positive integers a_1,...,a_n and an integer
target t, encoded in binary. Let L be their total encoding length. Duplicate
weights are separate items. The empty subset is allowed. Sort by weight,
breaking ties by original index, and partition into consecutive nonempty
blocks B_1,...,B_m, ordered from smallest to largest weights. Every block
contains at most b items, with 1 <= b <= n for nonempty inputs.

For block j define

$$
S_j=\left\{\sum_{i\in U}a_i:U\subseteq B_j\right\},\qquad
P_j=\sum_{h<j}\sum_{i\in B_h}a_i.
$$

S_j contains distinct sums, with one indexed witness retained per sum. P_j is
the total weight below that block. Define its overlap bound

$$
\kappa_j=\max_{z\in\mathbb Z}
   |S_j\cap[z-P_j,z]|,\qquad
K=\prod_{j=1}^m\kappa_j.
$$

Intervals are closed: sums exactly P_j apart can both qualify. Each kappa is
an integer between 1 and |S_j|, and |S_j| <= 2^b. The empty input has K=1.

**Lemma 1 (sound exclusion).** Suppose choices in higher blocks have left
residual target r. Only block sums s in S_j intersected with [r-P_j,r] can
occur in a completion. Each excluded block sum rules out every completion
using that sum, without enumerating the lower choices.

**Proof.** The sum u of any lower selection satisfies 0 <= u <= P_j. The
equation s+u=r requires r-P_j <= s <= r. The contrapositive proves exclusion.
The interval test is necessary, not sufficient; lower blocks are still
searched for an exact completion. QED.

**Lemma 2 (merging).** One witness per distinct block sum is sufficient for
exact existence and recovery of one full witness.

**Proof.** Two selections inside the same block with equal sum leave the same
residual target and the same unprocessed items. Either representative can be
combined with any valid selection in lower blocks. Blocks are disjoint, so
substitution cannot reuse an item. QED.

Merging preserves existence; it need not preserve the number of solutions.
Only Lemma 1 certifies that all assignments in an excluded group are invalid.

## 2. Search theorem and proof

Construct each S_j as a sorted list. Search blocks from m down to 1. At each
node, use two binary searches to find S_j intersected with [r-P_j,r], then
recurse on each such s with residual r-s. At depth m accept precisely when
the residual is zero. Targets outside [0,sum(a)] are rejected immediately.

**Theorem 1 (certified search bound).** For a fixed represented partition,
this algorithm is exact. Its complete search tree has at most

$$
1+\kappa_m+\kappa_m\kappa_{m-1}+\cdots+
\prod_{j=1}^m\kappa_j\ \le\ (m+1)K
$$

nodes and at most K complete paths. Once the block lists exist, its bit time
is bounded by poly(L) K. An early YES may stop sooner.

**Proof.** Induct on the number of remaining blocks. The zero-block case
accepts exactly residual zero. Lemma 1 loses no possible solution, and Lemma
2 makes one witness per tested sum sufficient. Applying the induction
hypothesis to each eligible sum proves both YES and NO correctness.

At the first level there are at most kappa_m children, at the second at most
kappa_m*kappa_(m-1), and so forth. Summing these level bounds proves the first
inequality. Every kappa is at least one, so every partial product is at most
K. This proves the second inequality. Two binary searches per node take
O(b+1) comparisons. Creating child records is charged once per edge. All
sums and masks have O(L) bits, so the stated conservative bit bound follows.
QED.

This is an upper bound for this algorithm, not a lower bound on instance
hardness. All costs for rejected or failed branches are included.

## 3. Discovery theorem: optimize the bound without searching all partitions

Let w_1 <= ... <= w_n be the sorted weights and let H_v=sum_{i<=v} w_i,
with H_0=0. For every possible block [u,v] of length at most b, compute its
distinct support S_[u,v] and

$$
\kappa(u,v)=\max_z|S_{[u,v]}\cap[z-H_{u-1},z]|.
$$

Crucially, H_(u-1) depends only on where the block starts; it does not depend
on how earlier weights were partitioned.

Set D(0)=1 and use the integer recurrence

$$
D(v)=\min_{\max(1,v-b+1)\le u\le v}
       D(u-1)\,\kappa(u,v).
$$

Retain a minimizing predecessor to reconstruct the blocks. Define K_b=D(n).
The implementation multiplies exact integers, avoiding floating-point logs.

**Theorem 2 (paid discovery and solving).** The recurrence finds the minimum
K over every contiguous sorted partition with block size at most b. Including
sorting, discovery, reconstruction, and exact solving, a conservative bit-time
bound is

$$
\boxed{T(w,t;b)\le\operatorname{poly}(L)\bigl(2^b+K_b\bigr).}
$$

The polynomial factor is uniform; it hides n and b factors as well as integer
arithmetic, not additional exponential parameters. The workspace can be
bounded by poly(L) 2^b with depth-first search.

**Proof.** Every partition of the first v items has a final block [u,v]. Its
product equals the preceding partition product times kappa(u,v). Since that
factor is independent of the preceding cuts, replacing the preceding
partition by an optimum cannot worsen the product. Induction on v proves
the recurrence and reconstructability.

There are at most nb candidate blocks. Their support lists can be built by
starting at {0}, adjoining each new item's translated list, and merging
duplicates. For a length-l block this takes O(2^l) arithmetic operations:
the intermediate list sizes are bounded by 1,2,...,2^l, whose sum is O(2^l).
Sorted list merging preserves one witness per distinct sum.

A sliding window computes kappa in O(|S|) comparisons. Move its left endpoint
until the difference between the rightmost and leftmost sums is at most the
allowed width. A maximum window exists with right endpoint at a support
value, so this evaluates the exact maximum over all integer z.

Thus discovery uses O(n log(n+1)+nb 2^b) arithmetic/comparison operations.
Discard candidate lists after scoring and rebuild only the chosen lists;
this adds O(n 2^b) work. Store the O(nb) scores and the DP predecessors.
All DP products are at most 2^n, since kappa(u,v) <= 2^(v-u+1), so their bit
length is at most n+1. Original indices and intermediate sums also have
polynomial bit length. Theorem 1 completes the time bound.

For space, chosen lists have at most m 2^b records. Depth-first search keeps
one path and its pending siblings, with at most 1+m(2^b-1) pending nodes;
each record has polynomial bit length. The score table and one temporary
candidate list obey the same conservative space bound. QED.

**Corollary 1 (efficiently recognizable tractable class).** Fix integers c>=1,d>=0.
Use b=min(n,max(1,floor(c log_2(L+1)))). Inputs for which K_b <= (L+1)^d can
be recognized and solved in polynomial bit time, for every target. Recognition
includes computing K_b and the partition. No partition or modulus is supplied
by an oracle.

**Proof.** Both 2^b and K_b are polynomial in L. Theorem 2 supplies discovery
and solving, and the bound on K_b is checked by integer comparison. QED.

More generally, define D_b=log_2 K_b for description only. Then the cost
envelope is poly(L)(2^b+2^D_b). This makes (b,D_b) a representation of two
sources of cost: constructing small blocks and exploring overlapping choices.
Increasing b cannot increase K_b because the permitted partitions only expand.
But b=n always permits K_b=1 by representing the whole input in one block;
the potentially exponential construction cost remains explicit.

If at most q blocks have kappa>1, and every kappa<=k for a fixed constant k,
then K<=k^q. Therefore q=O(log L) suffices when discovery is polynomial.
This allows a logarithmic number of imperfectly separated blocks.

## 4. Exponentially many distinct sums, a single search path

For j=0,...,m-1, take the block

$$
B_{j+1}=\{2\cdot10^j,3\cdot10^j,4\cdot10^j\}.
$$

There are n=3m items. Each block has eight distinct sums:

$$
S_{j+1}=10^j\{0,2,3,4,5,6,7,9\}.
$$

The total of all lower blocks is P_(j+1)=10^j-1. Adjacent block sums differ
by at least 10^j, strictly more than P_(j+1). Hence kappa_(j+1)=1.
The size-three partition has K=1, so discovery with b=3 also returns K_b=1.
The algorithm visits at most m+1 search nodes for every target, including NO
targets. It constructs only constant-size local support lists.

**All 2^(3m) global subset sums are distinct.** Every block produces a different
decimal digit in {0,2,3,4,5,6,7,9}, with no carries between blocks. Distinct
selections have distinct digit sequences. Thus a table of all distinct global
sums would still have exponential size. The proof uses local separation to
avoid constructing it.

For m=100 this gives 300 items and 2^300 distinct candidate sums. The known
YES target consisting of 100 decimal 7s takes 101 search nodes in the
reference implementation. A target with leading digit 8 is rejected at the
first block. Discovery cost is charged separately in validation.json.

This family is also not an itemwise superincreasing sequence: 4*10^j is less
than 2*10^j+3*10^j. The greedy maximum core described in Note V keeps two
items per triple and leaves m exceptions. Its exception-count bound is
exponential here. That comparison concerns the bounds for those two routes;
it is not a lower bound against other existing solvers or a novelty claim.

## 5. Separation survives perturbations and irregular scales

The mechanism does not require powers of ten or a shared modulus. Take
blocks {2M_j+e_(j,2),3M_j+e_(j,3),4M_j+e_(j,4)}, with integer errors of
absolute value at most E_j. Let P_j be the actual sum of all earlier blocks.
Assume

$$
M_j-3E_j>P_j.
$$

**Corollary 2.** These blocks are positive, sorted in scale order, have eight
distinct local sums, satisfy kappa_j=1, and have 2^n distinct global sums.
Theorem 2 with b=3 solves the family in polynomial bit time.

**Proof.** Unperturbed distinct block sums differ by at least M_j. In the
difference between any two perturbed sums, each of the three errors has
coefficient -1,0,or 1, changing the difference by at most 3E_j. Thus every
distinct pair remains separated by more than P_j. The assumption also
implies positivity, strict within-block weight order, and that every weight
in the new block exceeds every earlier weight. Therefore the sorted triples
are a permitted partition and each kappa is one.

For two different full selections, take their highest differing block.
Its sum difference exceeds P_j, while all lower blocks can change the total
by at most P_j. Cancellation is impossible, proving global distinctness.
QED.

This is a robust structured class. Arbitrary weights need not meet its
conditions. The general overlap-product theorem still applies when some
block intervals overlap, with its stated larger bound.

## 6. Relationship to the distribution proposal

This establishes a concrete pruning mechanism and a paid complexity bound.
Its assumptions are exact, efficiently checked properties of the input.
No independence assumption about successive pruning fractions is needed.

The product K has an additive logarithm, sum_j log(kappa_j). A statistical
model might therefore give an approximately lognormal K across some random
instance ensemble. Neither a random ensemble nor the necessary independence
or limit-theorem conditions have been established here. Exponentiating an
axis leaves all overlap tests and their cost unchanged. The provable saving
comes from bounded overlap and small block construction.

The separate [distribution-shaped difficulty follow-up](../distribution-shaping/README.md)
formalizes the other object: distributions of whole instances grouped by
solver-specific computational cost. It proves chosen-shape transport and
simultaneous bucket mass/purity guarantees, with a learned representation and
an exact solver router.

The theorem guarantees existence and recovery of one witness. It is not a
solution-counting algorithm, a general hardness classifier, or a proof of
polynomial time on every subset-sum input.

## 7. Prior work and scope

- [Note V theory](../../../Structural_Distance_Subset_Sum/THEORY.md) proves
  maximum superincreasing core discovery and bounds residual search by
  exception count or distinct exceptional sums. The block representation
  differs by keeping local sum dictionaries and using intervals of possible
  lower completions.
- [Note VII theory](../../../Structural_Geometry_Subset_Sum/THEORY.md) uses
  quotient/remainder geometry and exact coordinate tables. Both mechanisms
  charge construction and use sound necessary bounds before exact queries.
- Atkinson, Negro, and Santoro, *Sums of Lexicographically Ordered Sets*,
  [Carleton technical report TR-100 (1987)](https://carleton.ca/scs/research/scs-technical-reports/technical-reports-1987/tr-100-sums-of-lexicographically-ordered-sets/),
  gives earlier ordered-sum constructions with distinct subset sums and linear
  knapsack decision. The source abstract establishes relevant precedent, not
  an identification of this overlap bound with a theorem in that report.
- [Sage's superincreasing knapsack documentation](https://doc.sagemath.org/html/en/reference/numerical/sage/numerical/knapsack.html)
  describes the classical itemwise separated case. Singleton blocks with
  a_j greater than the sum of all preceding weights have kappa_j=1 here.

The combination above is a self-contained elementary derivation. A complete
novelty audit and comparative performance study remain outside this proof.

The standalone paper integrates **ten references** into the narrative,
covering foundational meet-in-the-middle and time-space results, ordered
distinct sums, pseudopolynomial and output-sensitive algorithms, dense
instances, small additive doubling, and recent worst-case methods. The
selection includes SODA 2025 work and Li and Ye's partial-match preprint
revised November 2, 2026. [references.json](references.json) records primary
sources, reviewed versions, and the specific relationship to this paper;
preprints and repository drafts remain explicitly identified. This is a
selected related-work discussion, not an exhaustive novelty audit.

## 8. Reproduce the finite correctness checks

From the repository root:

```powershell
python notes/01-certified-coverage/block-overlap/verify.py
```

To write a fresh verification record, pass `--output` with a new file path.
The included [validation.json](validation.json) records the initial run and
SHA-256 hashes of [solver.py](solver.py) and [verify.py](verify.py).

The independent checks enumerate all subsets on small inputs and all
contiguous partitions to verify decision, original-index witnesses, optimal
partition products, and the search-tree bound. They include closed interval
endpoints, duplicate weights, empty inputs, shuffled inputs, and large binary
weights. The large constructed example is validated using its proved digit
structure; its 2^300 subsets are not enumerated. These are finite correctness
checks accompanying the proof, not timing evidence or a replacement for it.

## 9. Build the standalone paper and plots

From the repository root:

```powershell
python notes/01-certified-coverage/block-overlap/build_note.py
```

Requires Matplotlib, `pdflatex`, and `pdfinfo`. The builder checks the original
source hashes in `validation.json`, regenerates the two vector plots and
`paper_values.tex`, checks that all ten bibliography entries are cited and
match `references.json`, compiles the LaTeX twice, rejects overfull boxes and
unresolved references, and lets pagination flow naturally without a page limit.
LaTeX scratch stays under `.build/latex/block-overlap/`.

[paper_evidence.json](paper_evidence.json) records source/artifact SHA-256
hashes, exact plot inputs, and structural counts for 1, 2, 4, 8, 16, 32, 64,
and 100 decimal triples. The 100-triple row is checked against the preserved
verification record. Plot counts distinguish candidate blocks, processed
support records including reconstruction, retained dictionaries, and visited
search nodes; these are separate counters, not uniform bit operations or
timing measurements. Global support sizes use the proved digit construction.
The original solver, checker, and verification record are never rewritten
by the paper builder.
