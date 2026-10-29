# Connections Between Exponential Search Spaces and OpenAI's Subset-Sum Work

Research handoff based on the repository sources reviewed on October 28, 2026.

Repository: [jonland82/exponential-search-spaces](https://github.com/jonland82/exponential-search-spaces), branch `master`.

## 1. Main connection

The shared algorithmic question is:

> How much of an exponential subset search can be handled through cheaper representations, after charging for discovering, constructing, checking, and using those representations?

The strongest connections are in Notes V and VII. Note V exploits an easy core and the distinct sums of its exceptions. Note VII constructs one geometric core table and reuses it across exceptional assignments. OpenAI's papers also exploit distinct-sum structure and filtered representations, but use different constructions to claim general worst-case improvements.

| Repository work | Connection | Important distinction |
| --- | --- | --- |
| Notes I–II: certified coverage, exact summaries, and pruning | Account for groups of subsets collectively and charge the cost of doing so. | The abstract coverage criterion alone does not construct a faster general algorithm. |
| Note III: probability-valued subset sum | Representation counts and collisions distinguish the number of choices from the number of distinct outcomes. | Its probability is over target selection, whereas OpenAI's success probability is over algorithmic randomness for a fixed input. |
| Note V: superincreasing core plus exceptions | Distinct exceptional sums can compress the remaining search. | The guarantee depends on the discovered structure. |
| Note VII and its runtime companion: geometric core reuse | One exact representation answers many residual queries. | The geometric table is a different mechanism from OpenAI's randomized representation and checksum constructions. |

## 2. The clearest mathematical bridge: distinct-sum deficiency

For an indexed collection of weights $V$, define its distinct subset-sum set by

$$
\mathcal A(V)=\left\{\sum_{i\in S}w_i:S\subseteq V\right\}.
$$

OpenAI's low-space paper defines the deficiency of a block as

$$
d(V)=|V|-\log_2|\mathcal A(V)|.
$$

Large deficiency means that many subset choices collapse to relatively few distinct sums. Small deficiency means that the block supplies many distinct sums. The paper analyzes complementary trials that exploit these two situations: compression in the first case and filtered solution representations in the second.

In Note V, let $E$ be the exceptions to a discovered superincreasing core, and write

$$
e=|E|,\qquad M(E)=|\mathcal A(E)|.
$$

Once equal exceptional sums are merged, Note V gives a conservative bound of the form

$$
T_V\le p(L)M(E),
$$

for a polynomial $p$ in binary input length $L$, including core discovery and the required arithmetic. Using the deficiency definition gives

$$
M(E)=2^{e-d(E)},
$$

and therefore

$$
\boxed{T_V\le p(L)2^{e-d(E)}.}
$$

This is an algebraic restatement of the existing Note V bound, not a new complexity theorem. It exposes the shared structural quantity directly: the effective exponent can shrink through fewer exceptions, greater deficiency among their sums, or both.

For example, if all $e$ exceptional weights equal the same positive integer, then

$$
M(E)=e+1,\qquad d(E)=e-\log_2(e+1).
$$

The distinct-sum route then makes only $e+1$ core queries rather than $2^e$ queries. Note V's tractable regimes include $e=O(\log(n+1))$, or more generally $M(E)=\operatorname{poly}(L)$.

The exception set and an OpenAI block play different roles in their respective algorithms. Sharing the deficiency statistic does not make the algorithms identical or establish a transfer of their proofs.

## 3. Note VII: a representation that is built once and reused

Note VII discovers a base $M\ge2$ and decomposes normalized weights as

$$
u_i=Mp_i+r_i.
$$

After selecting a core $C$ and exceptions $E$, the core table stores reachable coordinate pairs

$$
q=\sum_{i\in C}p_ix_i,\qquad s=\sum_{i\in C}r_ix_i.
$$

For each exceptional subset $A\subseteq E$, it answers the shifted query

$$
Mq+s=T-\sum_{i\in A}u_i.
$$

The same table serves all exceptional assignments. Let $H$ and $W$ be its height and width, $e=|E|$, $G\le H$ the maximum number of point tests per assignment, and $F$ the discovery and preprocessing cost. The runtime companion gives the conservative bit-time envelope

$$
T_{\mathrm{geom}}\le F+O^*(HW+2^eGW)
\le F+O^*(2^eHW),
$$

where $O^*$ suppresses factors polynomial in $L$. The numeric dimensions $H$ and $W$ remain explicit: short binary encodings do not guarantee small tables.

A sufficient polynomial regime is

$$
F=\operatorname{poly}(L),\qquad HW=\operatorname{poly}(L),\qquad e=O(\log L).
$$

The companion already compares this bound with general subset-sum algorithms, including OpenAI's October preprint. For polynomial-bit inputs, a sufficient condition for the coarse bound to lie strictly below the exponential scale $2^{cn}$ is that, for some fixed $\varepsilon>0$,

$$
F=O^*(2^{(c-\varepsilon)n}),\qquad
e+\log_2(HW)\le(c-\varepsilon)n.
$$

Use $c=1/2$ for the classical meet-in-the-middle scale, or $c=0.49$ for OpenAI's claimed time scale. This compares asymptotic bounds on qualifying structured families. It does not establish a wall-clock speedup, and the sharper shared-table bound may permit better sufficient conditions.

## 4. What OpenAI's papers add

The two preprints examined in this discussion are:

- **September 26, 2026 — A Low-Space Algorithm for Worst-Case Subset Sum.** Claims polynomial-times-$2^{n/2}$ time with ordinary $O(2^{n/5})$ writable-word space under fixed polynomial bounds on input bit length. Its strategy combines distinct-sum compression, multilevel representations, modular filtering, streamed generation, and disjointness checks. It has one-sided error: it never accepts an unsolvable instance and accepts each solvable instance with probability at least $2/3$.
- **October 4, 2026 — Subset Sum in Time $O(2^{0.49n})$.** Claims a randomized worst-case time improvement for polynomial-bit inputs in its stated word-RAM model. Its proof overview combines a small-support preliminary test, isolation, estimation of a modular checksum, and recovery and subtraction of modular false positives called aliases. It states correctness probability at least $2/3$ for each fixed input and a runtime cap on every execution.

These are the manuscripts' stated results; this handoff compares their formulations and proof overviews rather than independently validating the full proofs.

The substantive difference in scope is that OpenAI's claims cover arbitrary inputs within their encoding assumptions. The repository's concrete guarantees describe inputs with useful discovered cores or compact representations. Obtaining cheap, useful structure on every input would require an additional theorem.

The OpenAI methods described here are randomized algorithms, rather than learned pruning policies. Their use of randomness should be kept separate from Notes II, III, and VI's statistical learning components.

## 5. Coverage, collisions, and probability: distinctions to preserve

### Coverage counts and representation costs

Note I models explicit residual search as

$$
T(n)=P(n)+Q_{\mathrm{pair}}(n)+r(n)+\rho(n,k(n)),
\qquad r(n)=2^n-C(n).
$$

With polynomial overhead and representation cost, polynomial runtime in that model is equivalent to a polynomial explicit residual. This criterion concerns the stated processing model. A new representation can replace explicit residual enumeration with collective queries, as Note VII does.

In particular, $HW$ counts table positions and $2^e$ counts exceptional assignments. Neither is a count of original uncovered subsets, and neither can simply be substituted for $C(n)$.

### Collisions can help different objectives

Note III defines a representation count $r(t)$ and collision count

$$
M=\sum_{t\in D}r(t),\qquad
J=\sum_{t\in D}\binom{r(t)}2.
$$

It uses identities such as

$$
\sum_{t\in D}r(t)^2=M+2J
$$

to bound the number of distinct reachable targets. This connects conceptually to the distinction between representation multiplicity and distinct support in OpenAI's work. The quantities and uses differ: collisions in Note III tighten reachability bounds; OpenAI's representation methods also need enough compatible decompositions to survive filtering. A direct transfer of the collision bounds remains a research question.

### Two different probabilities

For fixed weights $w$ and a stated target distribution $\mu$, Note III studies

$$
q_\mu(w)=\Pr_{T\sim\mu}[T\in\mathcal A(w)].
$$

OpenAI's guarantees instead concern

$$
\Pr_{\omega}[\mathcal B(w,t;\omega)\text{ returns the correct answer}],
$$

where $(w,t)$ is fixed and $\omega$ is internal algorithmic randomness. A reachability probability, a learned score, and a randomized algorithm's correctness probability are distinct objects.

## 6. Suggested exploration with Codex

1. **Make the deficiency bridge explicit.** Re-derive $T_V\le p(L)2^{e-d(E)}$ from the implementation and proof, including support-construction, memory, and witness costs. Determine when measuring or bounding deficiency earns its acquisition cost.
2. **Compare compressed summaries precisely.** Map the repository's distinct-sum lists and geometric tables to the records, masks, and compatibility conditions in OpenAI's methods. Identify exactly which information each summary must retain.
3. **Explore a hybrid portfolio.** Ask whether cheap core recognition or geometric reduction can precede a general solver. Charge failed discovery attempts and preserve the fallback guarantee. Establish whether a decomposition reduces item count, numeric range, or query count; these are different savings.
4. **Investigate collision certificates.** Test whether affordable Note III certificates can predict or certify a useful compression regime without first paying for the full support. Separate deterministic certificates from empirical predictors.
5. **Sharpen the geometric comparison.** Start with $F+O^*(HW+2^eGW)$ rather than only its coarse product bound. Characterize input families satisfying an exponent advantage, with all discovery and bit costs included.
6. **Test paid performance on fresh inputs.** Compare against appropriate MITM, DFS, and bitset baselines; include discovery, construction, unsuccessful attempts, memory, and witness recovery. Treat capped unresolved cases separately from completed exact decisions.

Suggested opening prompt:

> Read this handoff, the current canonical notes, and the relevant solver code. Verify the deficiency connection first. Then identify one concrete extension supported by a precise theorem or a small reproducible experiment. Distinguish existing results, algebraic restatements, proposed extensions, and empirical findings. Charge discovery and verification costs, preserve frozen evidence, and do not infer a general worst-case improvement from success on structured families.

## Sources and entry points

- [Repository README and current note catalog](https://github.com/jonland82/exponential-search-spaces/blob/master/README.md)
- [Note I: Certified Coverage of Exponential Search Spaces](https://github.com/jonland82/exponential-search-spaces/blob/master/notes/01-certified-coverage/Certified_Coverage_of_Exponential_Search_Spaces.tex)
- [Note II: Subset Sum as a Stress Test](https://github.com/jonland82/exponential-search-spaces/blob/master/notes/02-subset-sum-stress-test/Subset_Sum_as_a_Stress_Test.tex)
- [Note III: Probability-Valued Subset Sum](https://github.com/jonland82/exponential-search-spaces/blob/master/notes/03-probability-valued-subset-sum/Probability_Valued_Subset_Sum.tex)
- [Note V: Structural Distance in Subset Sum](https://github.com/jonland82/exponential-search-spaces/blob/master/notes/05-structural-distance/Structural_Distance_in_Subset_Sum.tex)
- [Note VII: Geometric Cores and Exceptions](https://github.com/jonland82/exponential-search-spaces/blob/master/notes/07-geometric-cores/Geometric_Cores_and_Exceptions_in_Subset_Sum.tex)
- [Runtime companion to Note VII](https://github.com/jonland82/exponential-search-spaces/blob/master/notes/07-geometric-cores/Runtime_of_Geometric_Core_Subset_Sum.tex)
- [OpenAI low-space paper: introduction and proof strategy](https://github.com/openai/math/blob/main/preprints/A-Low-Space-Algorithm-for-Worst-Case-Subset-Sum-September-26-2026/build/introduction.tex)
- [OpenAI time-improvement paper: introduction and proof strategy](https://github.com/openai/math/blob/main/preprints/Subset-Sum-in-Time-2-power-0-49n-October-4-2026/build/sections/introduction.tex)

These links track moving branches. A formal follow-up should record the specific source commits it analyzes and check the papers' cited predecessors before making a novelty claim.
