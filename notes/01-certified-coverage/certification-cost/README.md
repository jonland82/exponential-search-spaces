# The Cost of Avoiding Search: A Conditional Coverage Law

**Research draft, November 1, 2026.** Unnumbered follow-up to Note I. The proposed lower bound for general subset sum remains unproved; Section 4 proves a restricted oracle case.

The question throughout this series is whether finding and verifying a shortcut costs less than the search it avoids. The conservation framing starts with an exact accounting identity: every candidate is either handled collectively or left for explicit search. The proposed cost law asks whether, on hard inputs, the work of obtaining that coverage plus the remaining search must retain a positive exponential floor, even when individual shortcuts are cheap.

## 1. Coverage, total work, and net saving

Following [Note I](../Certified_Coverage_of_Exponential_Search_Spaces.pdf), let $n$ be the number of binary choices, giving $2^n$ candidate assignments. Count each candidate once:

| Quantity | Meaning |
|---|---|
| $k(n)$ | Structurally represented candidates |
| $\delta(n)$ | Distinct candidates proposed for exclusion |
| $a(n)\in[0,1]$ | Fraction of proposals certified; set $a(n)=0$ when $\delta(n)=0$ |
| $p(n)$ | Candidates represented by exact paired summaries |
| $r(n)$ | Candidates left for explicit search |

Thus $a(n)\delta(n)$ counts certified exclusions. The covered categories do not overlap. Normalize explicit search to one unit per candidate, with all other costs in the same units:

$$
\underbrace{r(n)}_{\text{remaining search}}
=
2^n-
\underbrace{\bigl[k(n)+a(n)\delta(n)+p(n)\bigr]}_{\text{states handled collectively or safely excluded}}.
$$

Let $T(n)$ be total work. Let $P(n)$ pay for discovery, proposals, and verification outside pairing, and $Q_{\mathrm{pair}}(n)$ for finding, constructing, checking, and using paired summaries. These costs do not overlap:

$$
\underbrace{T(n)}_{\text{total work}}
=
\underbrace{P(n)+Q_{\mathrm{pair}}(n)+\log_2 k(n)}_{\text{discovery, verification, construction, and use}}
+r(n).
$$

Here $\log_2$ is the base-two logarithm. Its charge is Note I's representation-cost assumption, with $k(n)\ge1$, rather than a universal encoding theorem.

Define $S(n)$ as the net saving relative to direct enumeration:

$$
\boxed{
\underbrace{S(n)}_{\text{net saving}}
=2^n-T(n)
=
\underbrace{k(n)+a(n)\delta(n)+p(n)}_{\text{search avoided}}
-
\underbrace{\left[P(n)+Q_{\mathrm{pair}}(n)+\log_2 k(n)\right]}_{\text{cost paid}}.
}
$$

Positive $S$ means a saving; zero means break-even; negative $S$ means extra cost. Against a faster baseline, substitute its actual avoided work for the direct-enumeration comparison.

For compactness, suppress the argument $n$ and define total collective coverage $C$ and its overhead cost $H$:

$$
C=k+a\delta+p,\qquad H=P+Q_{\mathrm{pair}}+\log_2 k.
$$

### Conservation principle

[Explore the conservation curves interactively](conservation-explorer.html): move coverage from explicit search into certification and adjust its cost in the restricted oracle model.

**Exact accounting:** every candidate is either handled collectively or left for explicit search:

$$
\boxed{k+a\delta+p+r=C+r=2^n.}
$$

At fixed $n$, let $\Delta$ denote the change between two methods or configurations. Increasing coverage reduces the residual by the same amount:

$$
\boxed{\Delta C+\Delta r=0.}
$$

Since $T=H+r$ and $S=C-H$, the resulting change in paid work is

$$
\boxed{\Delta T=\Delta H-\Delta C.}
$$

**Proposed computational principle:** on hard inputs, redistributing work among search, discovery, certification, and representation cannot remove some positive exponential cost floor, even though local shortcuts and smaller exponential rates remain possible. This is the hypothesis developed in Section 3. The accounting identity alone does not conserve computational effort or prove that floor; Section 2 examines the stronger equal-cost version and why it fails for general subset sum.

## 2. The equal-cost hypothesis and its failure

Let $\mathcal S_n$ be the full candidate set. Partition it as $\mathcal S_n=U\mathbin{\dot\cup}R$, where $U$ is handled collectively and $R$ is searched explicitly. The symbol $\dot\cup$ means disjoint union, and $|X|$ counts the elements of a set $X$. Thus $|U|=C$, $|R|=r$, and $|U|+|R|=2^n$.

Assume that, on hard executions, collective resolution costs at least a constant per covered candidate:

$$
\boxed{H\ge c|U|,}
$$

for a fixed cost constant $c>0$, **after accounting for all reuse and shared computation**. Explicit search costs at least $d|R|$, for another fixed cost constant $d>0$. Neither constant depends on $n$. Therefore,

$$
\begin{aligned}
T(n)
&\ge H+d|R|\\
&\ge c|U|+d|R|\\
&\ge \min(c,d)(|U|+|R|)\\
&=\min(c,d)\,2^n.
\end{aligned}
$$

For nonnegative functions $f$ and $g$, write $f(n)=\Omega(g(n))$ when $f$ is at least a positive constant times $g$ for all sufficiently large $n$. The conclusion is

$$
\boxed{T(n)=\Omega(2^n).}
$$

**This is false as a universal lower bound for general subset sum.** On polynomial-bit inputs, classical meet-in-the-middle already solves the problem in $O^*(2^{n/2})$ time, asymptotically less than $2^n$. Here $O^*$ denotes an upper bound with polynomial factors in the input length suppressed. See the [runtime comparison](../../07-geometric-cores/Runtime_of_Geometric_Core_Subset_Sum.pdf).

The derivation is valid under its assumptions, so the contradiction rejects the universal equal-cost hypothesis, not the algebra. Collective representations can resolve candidates more cheaply than a constant per original assignment. The linear law could still describe a restricted search model.

**Rejecting this law does not prove a better lower bound.** It neither establishes an optimal exponent nor implies $\Omega(2^{n/2})$. A faster algorithm supplies an upper bound; a lower bound requires a separate argument. Section 3 introduces a weaker hypothesis rather than deriving one from this failure.

## 3. The main hypothesis: an unknown exponential floor

The broader proposal leaves the exponential-rate parameter $\beta$ unspecified:

> There exists a fixed $\beta>0$ such that every algorithm in the chosen class has worst-case runtime $\Omega(2^{\beta n})$.

The hard input may depend on the algorithm and size. The exponent is common to the class; multiplicative constants may depend on the algorithm but cannot shrink with $n$.

A sufficient coverage-cost mechanism is, for some fixed $0<\beta\le1$,

$$
\boxed{H\ge c|U|^\beta,\qquad T\ge H+d|R|.}
$$

To derive the floor, let $N=2^n$ be the total candidate count. Either $|R|\ge N/2$, giving $T\ge dN/2$, or $|U|>N/2$, giving $T\ge c(N/2)^\beta$. Hence

$$
\boxed{
T(n)\ge\min(d/2,c\,2^{-\beta})N^\beta
=\Omega(2^{\beta n}).
}
$$

The linear law is the special case $\beta=1$. For $\beta<1$, substantial local and global savings remain possible while hard inputs retain an exponential cost. This conditional argument gives a lower bound only if the new coverage-cost hypothesis is established; it does not determine $\beta$.

Known faster algorithms constrain this unknown floor. Meet-in-the-middle already excludes a universal $\Omega(2^n)$ bound for subset sum. Servedio and coauthors' polynomial-factor speedup, and the cited OpenAI preprint's claimed smaller exponent, can coexist with a floor at a smaller positive exponent. An algorithmic upper bound does not establish the optimal lower bound. See the [runtime comparison](../../07-geometric-cores/Runtime_of_Geometric_Core_Subset_Sum.pdf).

The coverage argument concerns complete exact resolution, naturally NO executions; a YES search may stop at one witness. A class-wide conclusion requires the cost hypothesis on hard inputs for every algorithm in that class. The restricted model below also supports a separate randomized argument.

## 4. A restricted model where the law can be proved

**Model.** A hidden function $f:\{0,1\}^n\to\{0,1\}$ specifies one independent outcome for each of the $N=2^n$ candidates. An algorithm must decide whether any outcome is $1$. It may adapt, compute, and reuse earlier results freely, but learns about $f$ only by probing an individual candidate; each probe costs one unit. Certificates and summaries must be computed from those probes. Take the hard input $f_0$, which is zero everywhere.

**Exact result.** Every deterministic algorithm correct for all such functions must probe all $N$ candidates on $f_0$. If it leaves a candidate $z$ unprobed, change only $f(z)$ to $1$. Every answer the algorithm saw remains the same, so it would still answer NO and be wrong. More specifically, any sound certificate that a region $U$ contains no $1$ must probe every member of $U$ on $f_0$. Charging those probes to certificate work gives $H\ge |U|$; probing the remaining region $R$ costs at least $|R|$. Thus this model realizes the Section 2 law with $c=d=1$:

$$
\boxed{T(f_0)\ge H+|R|\ge |U|+|R|=2^n.}
$$

**Randomized extension.** Suppose an algorithm is correct with probability at least $2/3$ on every input. For each candidate $z$, let $f_z$ equal $f_0$ except that $f_z(z)=1$. Run the algorithm on $f_0$ and $f_z$ with the same random choices. Their answers can differ only if it probes $z$; yet the YES probability differs by at least $1/3$. Therefore it probes each $z$ on $f_0$ with probability at least $1/3$. Summing these probabilities shows that its expected number of distinct probes on $f_0$ is at least $N/3=\Omega(2^n)$.

**Scope.** The oracle hides $N$ independent bits, so this is linear in the oracle's input size. It gives a precise example of the conservation principle, not a new lower bound for subset sum. Subset-sum candidate outcomes are linked by their weights and target: if all weights are even and the target is odd, one short parity check excludes all $2^n$ assignments. Proving a cost floor for hard inputs in that richer model remains the open step.

## 5. Local gains, reuse, and learning

Index collective-resolution events by $j$. Let $u_j$ count candidates newly covered at event $j$, and $h_j$ be the actual cost allocated to it. All sums below run over those events. Include failed attempts with $u_j=0$ and charge shared construction once:

$$
\sum_j u_j=|U|,\qquad \sum_j h_j=H.
$$

The proposed global law is

$$
\boxed{\sum_j h_j\ge c\left(\sum_j u_j\right)^\beta.}
$$

It need not hold separately at each event. For $\beta<1$, cheap checks need not be exactly offset elsewhere: total work may fall substantially while remaining above the exponential floor.

Reuse illustrates why the accounting boundary matters. A table built for $B$ and queried $m$ times at cost $q$ beats $m$ separate solves costing $s$ each when

$$
\boxed{B+mq<ms\quad\Longleftrightarrow\quad m(s-q)>B.}
$$

For a learned pruning gate, let $x$ be the information available at the current search node, and $\mathbb E[\cdot\mid x]$ the expected value conditional on that information. Let $C_{\mathrm{features}}$, $C_{\mathrm{decision}}$, and $C_{\mathrm{verification}}$ be the additional work of acquiring features, making the gating decision, and checking the certificate. These subscripted costs are distinct from the coverage count $C$. Attempt the check when

$$
\mathbb E[\text{search work avoided}\mid x]
>
C_{\mathrm{features}}+C_{\mathrm{decision}}+C_{\mathrm{verification}}.
$$

Expectation determines whether to try the check; an exact certificate authorizes pruning. Discovery, training, and preprocessing costs must have an explicit place in the chosen model.

## 6. Context and next question

[Notes II](../../02-subset-sum-stress-test/Subset_Sum_as_a_Stress_Test.pdf), [V](../../05-structural-distance/Structural_Distance_in_Subset_Sum.pdf), and [VI](../../06-learned-solvability/Predicting_Subset_Sum_Completion.pdf) show why fewer possibilities or visited nodes can still mean more paid work. [Note VII](../../07-geometric-cores/Geometric_Cores_and_Exceptions_in_Subset_Sum.pdf) shows when reusable structure pays. [Chen, Jin, Randolph, and Servedio](https://arxiv.org/abs/2301.07134) prove a net speedup by balancing construction, screening, and verification. [From Choices to Sums](../../../OpenAI_Subset_Sum_Connections/From_Choices_to_Sums.pdf) connects the series to the OpenAI preprints.

The oracle argument proves the law for independent hidden outcomes. The next research question is whether a model that retains meaningful subset-sum structure has a hard family with a positive coverage-cost floor. The experiments motivate that question; they do not prove such a law.

[Parent note](../README.md) | [All notes](../../README.md) | [Repository guide](../../../README.md)
