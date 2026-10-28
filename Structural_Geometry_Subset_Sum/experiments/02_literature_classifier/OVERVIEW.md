# Literature geometry in the subset-sum classifier

**Question:** Can known mathematical structure help us predict which inputs an
exact solver can finish, cheaply enough to improve the solver's useful work?

This extends the research program from **certified coverage**, through
**distance to tractable cores**, to **learned allocation of exact computation**.
The literature supplies candidate structures; our experiment tests their value
as measured features. [Protocol](PROTOCOL.md) ·
[Findings](../../CLASSIFIER_FINDINGS.md) ·
[Code](../../classifier_features.py).

## 1. What the literature adds

| Direction | Mathematical structure | Established result and our use |
|---|---|---|
| [Krishnamoorthy–Pataki, 2009](https://arxiv.org/abs/0807.1317) | $w=Mp+r$; branch on the aggregate $p^\top x$ | Suitably constructed knapsacks obstruct individual-variable branching but admit effective aggregate branching/reformulation. We extract projection descriptors and exact gap certificates; we do not implement their general lattice reformulation. |
| [Randolph–Węgrzycki, 2024](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ESA.2024.96) | $\mathcal C(A)=\lvert A+A\rvert/\lvert A\rvert$ | Their set formulation admits subset-sum algorithms in $n^{O_{\mathcal C}(1)}$: polynomial for fixed doubling, with exponent depending on it. We measure doubling as a descriptor, without implementing their algorithm or transferring that guarantee to arbitrary multiplicities. |
| [Bringmann–Wellnitz, 2021](https://arxiv.org/abs/2010.09096) | Dense-set threshold $t\gg a_{\max}\sum_i a_i/n^2$ | In their dense, polynomially bounded set regime, with $a_{\max}\le t\le\sum_i a_i/2$, this permits near-linear solving, with logarithmic qualifications. This is context for future features; this experiment adds no dense-regime detector. Multisets have separate conditions. |

The shared lesson is that **difficulty depends on the representation and the
algorithm**. A large-base example is not universally hard, and a structure score
alone is not an exact answer.

## 2. From large weights to a small geometric picture

Write the original input as $(a,t)$. Exact reductions produce a residual problem
$(w,\tau)$. Divide by $g=\gcd(w)$ to obtain $(u,v)=(w/g,\tau/g)$; a
nondivisible target is already an exact NO. For a discovered integer $M\ge2$,
our implementation chooses

$$
p_i=\left\lfloor\frac{u_i+\lfloor M/2\rfloor}{M}\right\rfloor,
\qquad r_i=u_i-Mp_i.
$$

Each binary selection $x$ becomes a point in two integer coordinates:

$$
q=p^\top x,\qquad s=r^\top x,\qquad
u^\top x=v\iff Mq+s=v.
$$

Instead of viewing only a huge one-dimensional sum, view attainable points
inside a residual strip. Solutions must lie on a line crossing that strip.
Define

$$
R_-=\sum_i\min(0,r_i),\qquad R_+=\sum_i\max(0,r_i),\qquad P=\sum_i p_i.
$$

Every solution must have an integer $q$ between

$$
q_\ell=\max\left(0,\left\lceil\frac{v-R_+}{M}\right\rceil\right),\qquad
q_h=\min\left(P,\left\lfloor\frac{v-R_-}{M}\right\rfloor\right).
$$

If $q_\ell>q_h$, no integer column can meet the line: **exact NO**. Otherwise,
the bounds are only necessary. Experiment 01 also tests exact DP on reachable
$(q,s)$ pairs; this classifier experiment uses the gap certificate and descriptors.
Discovery tries at most 24 data-derived bases, without receiving the planted $M$.

## 3. The features, mathematically

### Original five structural features

For each tractable class $\mathcal E_j$, the ideal deletion distance and the
implemented certified-core feature are

$$
d_j(u)=\min_{K:\,u_K\in\mathcal E_j}(m-\lvert K\rvert),\qquad
\widehat d_j(u)=m-\lvert K_j\rvert\ge d_j(u),\qquad m=\lvert u\rvert.
$$

| Core class | Membership condition / representation |
|---|---|
| Superincreasing | Sorted retained weights satisfy $b_j>\sum_{i<j}b_i$. |
| Complete coverage | On the fixed gcd grid, $b_j\le1+\sum_{i<j}b_i$; all sums from $0$ through $\sum b_i$ are covered. |
| Few values | At most two distinct retained weights. |
| Small support | $\lvert\{\sum_{i\in K}u_ix_i:x_i\in\{0,1\}\}\rvert\le128$. |
| Compact representation | Every retained prefix has at most eight reachable intervals, or retained weights form an arithmetic progression; keep the larger discovered core. |

The first three distances are exact for their implemented classes. The last
two are constructive upper bounds; bounded discovery need not find the largest
possible core. These features connect directly to Paper V: with $d$ exceptions,
at most $2^d$ exact core queries suffice, giving the accounting form
$T\le F+2^dQ$ for extraction cost $F$ and a per-query bound $Q$.

### Original ten numerical features

These use the **original input**, while structural features use its reduced
kernel. Let $n=\lvert a\rvert$, $S=\sum a_i$, $D=\lvert\{a_i\}\rvert$,
$\mu=S/n$, and $\sigma^2=n^{-1}\sum_i(a_i-\mu)^2$. With $L$ the existing
[binary encoding-length proxy](../../../Learned_Solvability_Subset_Sum/features.py),
the numerical vector is

$$
\left(
n,\ L,\ \log_2(S+1),\ \log_2(a_{\max}+1),\ \log_2(a_{\min}+1),
\frac Dn,\ \frac\sigma\mu,\ \frac tS,\ \frac{\min(t,S-t)}S,
\frac{n}{\max(1,\log_2(a_{\max}+1))}
\right).
$$

They describe scale, repetition, spread and target position. The last coordinate
is the existing density score; it is not the dense-set theorem's full criterion.

### Four new literature-inspired features

Set $W=R_+-R_-+1$, $H=\max(0,q_h+1)$, and
$N_q=\max(0,q_h-q_\ell+1)$. Append:

| Feature | Implemented formula | Simple interpretation |
|---|---|---|
| Relative residual width | $\phi_{16}=\log(1+(W-1)/M)$ | How wide is the residual strip relative to the main spacing? |
| Feasible aggregate count | $\phi_{17}=\log(1+N_q)$ | How many integer columns can contain a solution? |
| Projected representation size | $\phi_{18}=\log(1+HW)$ | How large would the bounded DP rectangle be? |
| Additive doubling | $\phi_{19}=\lvert A+A\rvert/\lvert A\rvert$, $A=\{u_i\}$ | How many different pair sums arise per distinct weight? |

Here $A+A=\{a+b:a,b\in A\}$ includes $a+a$. Multiplicities do not increase
$\lvert A\rvert$; doubling is different from reachable-subset-sum support.
For $A=\{1,2,3\}$, the pair sums are $\{2,3,4,5,6\}$, so doubling is $5/3$.
The first three transforms use natural logarithms. Missing decompositions give
three zeros; empty $A$ gives zero. These formulas are **our proposed predictive
descriptors**, motivated by the literature, not proven runtime predictors.

## 4. Where ML enters—and what counts as success

All three vectors, $\boldsymbol\phi^{(15)}$, $\boldsymbol\phi^{(18)}$ and
$\boldsymbol\phi^{(19)}$, use the same
expanded training lists. Standardize with training statistics, then fit and
calibrate logistic regression on disjoint training/calibration lists:

$$
z_j=\frac{\phi_j-\mu_j^{\rm train}}{s_j^{\rm train}},\qquad
p_0=\operatorname{sigmoid}(b+\beta^\top z),\qquad
\widehat p=\operatorname{sigmoid}(c+\alpha\operatorname{logit}(\bar p_0)),
$$

where $\operatorname{sigmoid}(h)=1/(1+e^{-h})$ and $\bar p_0$ clips $p_0$ to
$[10^{-6},1-10^{-6}]$; constant columns use scale one. The label is

$$
Y=\mathbf{1}\{\text{original exact portfolio finishes within }8L\text{ work units}\}.
$$

It concerns budgeted completion, not truth.
Rank remaining inputs by $\widehat p/(8L)$ in work pools and by $\widehat p$
in live-time pools. Exact algorithms supply every answer.

The program's practical objective is more exact completions $N(B)$ under a
fixed total budget $B$, paying for

$$
T_{\rm total}=T_{\rm reductions}+T_{\rm features}+T_{\rm inference/scheduling}
+T_{\rm exact\ checks/search}+T_{\rm witness\ verification}.
$$

The matched 15-input control receives the **same paid geometric NO checks** as
the 18/19-input models. Thus learned ranking gains can be separated from exact
certificate gains and discovery cost. Unlike the earlier prototype distances,
these features inspect additional structure in the actual weights.

## 5. What this experiment found

From 405 fresh test cases, 250 remained after common exact shortcuts. Their
Brier error $\mathbb E[(\widehat p-Y)^2]$ was **0.1222 / 0.1062 / 0.1011**
for 15/18/19 inputs. Tight live budgets showed extra completions over the matched
control, but both adjusted primary intervals include zero and several work
pools worsened after acquisition costs. The strongest package gain came from
exact certificates. This supports further investigation of geometry-aware
allocation; it establishes neither a general speedup nor a new complexity bound.
