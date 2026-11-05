# Distribution-shaped representations of computational difficulty

[Standalone PDF](Distribution_Shaped_Difficulty_Buckets.pdf) | [Editable LaTeX source](Distribution_Shaped_Difficulty_Buckets.tex)

Research draft, November 4, 2026. This note formalizes a chosen distribution
whose identifiable regions contain large groups of computationally expensive
instances. It supplies proofs, a learning/calibration algorithm, and an exact
subset-sum router. The calibration guarantee is statistical and solver-specific.
No universal hardness test, general worst-case improvement, or empirical
subset-sum speedup is established. Literature novelty remains unestablished.

In the [research reading path](../../README.md), this follows the clustering
and runtime-bands accounts: it constructs identifiable difficulty regions
after those notes explain the observed landscape. [Block-overlap pruning](../block-overlap/README.md)
provides the exact structural route used in the solver application.

## 1. What is distributed, and what counts as hard

An observation X is a whole problem instance, such as (weights,target), drawn
from a declared population D. Fix a complete solver A, its implementation,
cost unit, and budget B before collecting labels. Write

$$
C_A(X)\ge0,\qquad H(X)=\mathbf1\{C_A(X)>B\}.
$$

H=1 means expensive for this solver and budget. It does not mean NO, and it
does not imply that every algorithm needs that much work. The target, input
length, and solver policy belong in this definition. A budget-exceedance label
can be observed by running A to B without needing its eventual full cost,
provided completion within that budget is observed exactly. A different
resource-stop event must be declared as a different label.

Extract inexpensive features phi(X), and fit a score S=s_theta(phi(X)) in
[0,1] using a training split. The implementation uses standardized logistic
regression. Optionally use clipped cost weights in training to emphasize
expensive examples. No predictive quality theorem is assumed for that learner.

Choose a score threshold tau and define the *predicted* group G=1{S>=tau}.
G is not the observed label H. Freeze the predictor, threshold, shape choices,
and bucket definitions before looking at calibration labels.

The algorithm has three distinct data roles:

| Split | Used for |
|---|---|
| Training | Learn score coefficients, standardization, optional cost weights |
| Reference | Estimate conditional score ranks; no cost labels used |
| Calibration | Test frozen bucket mass and true hard/easy purity |

These roles must be independent for the stated guarantees. An independent test
set is additionally needed for a performance comparison. Multiple targets or
scaled copies of the same generated list can be dependent observations; the
binomial theorem below does not automatically apply to treating them as
independent calibration rows. Unique IDs help detect split reuse but cannot
establish statistical independence.

## 2. Choose the shape, preserving the source population

Choose continuous target CDFs Q_0,Q_1, each strictly increasing on an interval
I_0,I_1 with disjoint ordered interiors. The reference implementation uses
truncated lognormals:

$$
Q_g(z)=\frac{\Phi((\log z-\mu_g)/\sigma_g)-a_g}{b_g-a_g},\qquad
a_g=\Phi((\log\ell_g-\mu_g)/\sigma_g),\quad
b_g=\Phi((\log u_g-\mu_g)/\sigma_g),
$$

for ell_g < z < u_g, with CDF 0 and 1 outside the interval. Thus

$$
Q_g^{-1}(u)=\exp\bigl(\mu_g+\sigma_g\Phi^{-1}(a_g+u(b_g-a_g))\bigr).
$$

The default lower-score component occupies (0.05,1). The higher-score
component occupies (2,12), with a narrower log scale. These are layout choices;
the reference population determines the mixture weights. Forcing a different
mixture weight would require changing the source distribution or importance
weights, rather than just changing coordinates.

Let F_g be the true CDF of S conditional on G=g. For a fresh independent
V uniform on [0,1), define the randomized rank and shaped coordinate

$$
U=F_g(S^-)+V\bigl(F_g(S)-F_g(S^-)\bigr),\qquad Z=Q_g^{-1}(U).
$$

Randomizing over a CDF jump handles tied or discrete scores. It adds no
information about H: V is independent of the instance and label.

**Theorem 1 (chosen shape).** Conditional on a predicted group g of positive
probability, U is uniform and Z has CDF Q_g. The total distribution is the
mixture pi_0 Q_0 + pi_1 Q_1, with pi_g=P(G=g).

**Proof.** Let W be uniform on [0,1]. The generalized inverse F_g^(-1)(W)
has CDF F_g. Conditional on that inverse taking a score value s at an atom,
W is uniform on the jump interval [F_g(s^-),F_g(s)]. The independent V
construction realizes exactly this conditional distribution. At non-atomic
values it agrees almost surely with the ordinary continuous rank. Hence its
marginal U is uniform for arbitrary score distributions. For z in I_g,
P(Z<=z|G=g)=P(U<=Q_g(z)|G=g)=Q_g(z). Conditioning on the disjoint groups
gives the mixture. QED.

### Estimated ranks and a finite-reference error bound

Use the conditional empirical CDF Fhat_g from m_g independent reference scores
in group g. Define Uhat by the same randomized-jump formula with Fhat_g. Clip
Uhat to [c,1-c] before computing Zhat to avoid numerical endpoints. The code
uses c=10^(-9)/J, where J is the number of buckets per group.

**Theorem 2 (shape error).** If sup_s |Fhat_g(s)-F_g(s)| <= eta_g, then

$$
\sup_z|\Pr(\widehat Z\le z\mid G=g,\text{reference})-Q_g(z)|
\le \eta_g+c.
$$

For nonempty reference groups, with probability at least 1-delta_shape,
this holds simultaneously for the two groups with

$$
\eta_g=\min\left(1,\sqrt{\frac{\log(4/\delta_{\rm shape})}{2m_g}}\right).
$$

**Proof.** The same eta bound holds for left limits. Couple the true and
empirical ranks using the same (S,V). Their difference is a convex combination
of the two CDF errors, and so has absolute value at most eta_g. Clipping changes
the empirical rank by at most c. Coupling a variable within eta_g+c of a
uniform variable bounds its CDF discrepancy from uniform by eta_g+c.
The increasing inverse Q_g transfers that bound to Zhat.

Conditional on the group count m_g, the reference scores in that group are
i.i.d. from F_g. The Dvoretzky-Kiefer-Wolfowitz-Massart inequality bounds the
probability of CDF error exceeding eta by 2 exp(-2m_g eta^2). Apply it with
delta_shape/2 per group and take a union bound. If the displayed square root
exceeds one, the deterministic bound eta=1 suffices. QED.

When m_g=0, no rank-shaping accuracy is claimed. The algorithm returns an
unrepresented, unresolved region for that group. The CDF theorems describe
real arithmetic; the implementation uses floating-point score/quantile
evaluation and endpoint clipping. The exact statistical tests below instead
apply directly to the implemented, frozen bucket function.

## 3. Large, identifiable hard buckets: the calibration theorem

Choose J fixed rank intervals [j/J,(j+1)/J), closing the final endpoint, in
each of the two groups. After training and reference fitting, these define
M=2J fixed buckets B_1,...,B_M in the joint (X,V) space. Their images are
known intervals under Q_g, giving easily identifiable regions. Unrepresented
groups have no bucket assignment.

Fix a permitted impurity epsilon in (0,1/2), a minimum population mass gamma
in (0,1), and a total calibration failure probability delta in (0,1). Draw
N independent calibration observations from D, with independent tie uniforms.
For bucket b, record n_b assigned observations and k_b observed hard labels.
Use alpha=delta/(3M). Let T(n,k,p)=P(Bin(n,p)>=k), including endpoints.

Run three predeclared tests for every bucket:

| Claim | Accept when |
|---|---|
| Hard fraction at least 1-epsilon | n_b>0 and T(n_b,k_b,1-epsilon) <= alpha |
| Easy fraction at least 1-epsilon | n_b>0 and T(n_b,n_b-k_b,1-epsilon) <= alpha |
| Population mass at least gamma | T(N,n_b,gamma) <= alpha |

Label the bucket **hard** only if both its hard and mass tests pass. Label it
**easy** only if both its easy and mass tests pass. Otherwise return
**unresolved**. Since epsilon<1/2, the two purity tests cannot both pass at
this alpha. Empty or insufficiently supported buckets remain unresolved.

**Theorem 3 (simultaneously reliable large buckets).** Conditional on any
training/reference result, with probability at least 1-delta over the
independent calibration sample and its ties, every labeled bucket satisfies
simultaneously:

$$
\boxed{\begin{aligned}
\text{hard bucket }b:&\quad
 \Pr(H=1\mid B_b)\ge1-\epsilon,\quad\Pr(B_b)\ge\gamma,\\
\text{easy bucket }b:&\quad
 \Pr(H=0\mid B_b)\ge1-\epsilon,\quad\Pr(B_b)\ge\gamma.
\end{aligned}}
$$

The probabilities inside the box concern a fresh draw (X,V), not a promise
about an individual instance. Selecting any union of labeled hard buckets
after seeing these calibration results preserves hard purity at least
1-epsilon. If q distinct hard buckets are selected, their union has mass
at least q gamma on the same event.

**Proof.** For fixed frozen bucket b, let p_b=P(H=1|B_b) and rho_b=P(B_b).
Conditional on n_b, its k_b labels have Bin(n_b,p_b) law. If p_b <= p_0,
the upper tail at p_0 evaluated at the observed count is superuniform:

$$
\Pr\{T(n_b,k_b,p_0)\le\alpha\mid n_b\}\le\alpha.
$$

Indeed the rejecting counts form an upper tail. Under p_0 the probability
of that tail is at most alpha by its definition, and a coupling of Bernoulli
trials makes it no larger for p_b <= p_0. This proves the hard-purity test
with p_0=1-epsilon. Apply the same argument to easy-label counts for the
easy-purity test. Averaging over the random n_b preserves each bound.

Also n_b has Bin(N,rho_b) law, so the same argument proves the mass test's
type-I bound when rho_b <= gamma. There are 3M tests, each with false
certification probability at most alpha. A union bound gives at most delta
probability of any erroneous claim. No independence between these tests is
needed. Simultaneous validity permits post-calibration selection among the
predeclared buckets. Disjoint bucket masses add, and union purity is their
mass-weighted average. QED.

This proof is exact-binomial inversion with simultaneous error accounting,
not a new general concentration inequality. The implementation evaluates
the binomial tails and alpha comparisons as exact rational numbers. It stores
calibration counts and decisions; it never rounds a confidence threshold to
decide whether to certify a bucket.

**Corollary (availability with feature signal and margins).** Fix one frozen
bucket whose true mass rho and hard fraction p satisfy

$$
\rho\ge\gamma+\Delta_\rho,\qquad
p\ge1-\epsilon+\Delta_p,
$$

for positive margins Delta_rho,Delta_p. For any beta in (0,1), let

$$
L_0=\max\{\log(1/\alpha),\log(2/\beta)\}.
$$

If the fixed calibration size satisfies

$$
N\ge2L_0\max\left\{\frac1{\Delta_\rho^2},
                         \frac1{\gamma\Delta_p^2}\right\},
$$

the algorithm labels that bucket hard with probability at least 1-beta.

**Proof.** Hoeffding's binomial tail bound gives
P(n_b/N < gamma+Delta_rho/2) <= exp(-N Delta_rho^2/2).
On its complement, n_b>=N gamma and the mass-test p-value is at most
exp(-N Delta_rho^2/2), which is at most alpha by the chosen N.

Conditional on any such n_b, the probability that k_b/n_b is below
1-epsilon+Delta_p/2 is at most exp(-n_b Delta_p^2/2), hence at most
exp(-N gamma Delta_p^2/2). On its complement the hard-test p-value is at most
that latter bound, also at most alpha. Each adverse event has probability
at most beta/2, so both tests pass with probability at least 1-beta. QED.

The same result holds for easy buckets by exchanging hard and easy labels.
For simultaneous availability of up to M qualifying buckets, replace
log(2/beta) by log(2M/beta) and apply a union bound. This is a sufficient,
conservative sample-size bound; exact-binomial certification can pass with
fewer samples. Its essential assumption is that the learned features actually
provide a region with positive mass and purity margins. The algorithm cannot
create that signal by changing the target density.

**Corollary (work concentration).** Let U be a union of q certified hard
buckets. On the same event,

$$
\mathbb E[C_A(X)\mathbf1_U]\ge
B(1-\epsilon)\Pr(U)\ge B(1-\epsilon)q\gamma.
$$

**Proof.** On U intersected with {H=1}, C_A>B. Integrate this pointwise lower
bound and apply Theorem 3. QED.

This gives a lower bound on the aggregate work in an identified region under
the fixed source population. It does not guarantee that every run within the
region exceeds B, nor that the region accounts for most total work. The latter
requires additional information about costs outside the region.

## 4. Why shaping alone cannot guarantee identifiable hardness

**Proposition 1 (features limit separation).** If H is independent of phi(X),
with P(H=1)=p, then every positive-mass region produced from phi(X) and
independent randomization has hard fraction p, regardless of its target shape.

**Proof.** Z=f(phi(X),V) is a measurable function of variables jointly
independent of H. Hence H and Z are independent, so P(H=1|Z in B)=p. QED.

For example, if p=1/2, no region can actually have purity 0.9. Theorem 3
then ensures that issuing such a label happens with probability at most
delta. It does not force any bucket to receive a label. No theorem of large
certified coverage is possible without an informative feature/distribution
assumption.

**Proposition 2 (layout invariance).** With predictor, reference ranks, rank
buckets, and ties fixed, replacing Q_g by any increasing target quantile
function leaves bucket membership and its conditional hardness unchanged.

**Proof.** Membership is determined by the predicted group and the rank
interval. The target function changes only the coordinate assigned to that
same interval. Its inverse recovers the interval almost surely. QED.

Thus the supervised score supplies the difficulty information. The chosen
distribution supplies recognizable locations, scale, and concentration.
Calibration establishes which of those locations have reliable meaning.

## 5. Updated algorithm

Offline, with a declared population, solver and cost budget:

1. Extract phi and learn s_theta on training observations. Optionally weight
   the training loss by clipped costs. Fit standardization on training only.
2. Choose tau, J, Q_0,Q_1, epsilon,gamma,delta before inspecting calibration
   labels. Estimate Fhat_g using only the reference split. Freeze this map.
3. Assign independent calibration cases to the frozen rank buckets. Compute
   all 3M exact binomial tests. Keep hard/easy/unresolved labels and source
   fingerprints. Reusing calibration to refit the score, tune new cutpoints,
   choose new models, or repeatedly stop sampling invalidates this accounting
   unless the additional choices are included in a new guarantee.

Online:

1. Extract phi(X), compute score, predicted group, randomized reference rank,
   and shaped coordinate. Read the fixed bucket's calibration label.
2. Use the label to choose a solving route, allocate resources, or abstain
   from a difficulty prediction. A hard label does not authorize a NO answer
   or exclusion of candidate solutions.
3. Return an exact answer only after an exact solver completes. Check every
   reconstructed YES witness against original indices and weights.

### Concrete exact subset-sum router

[algorithm.py](algorithm.py) includes both the difficulty algorithm and a
complete reference router. It uses a fixed 12-feature extractor with input
length, target position/range, gcd information, duplicate rate, ordinary
superincreasing-core exceptions, and weight gaps. Extraction uses a sort
and linear scans, with polynomial bit cost; it does not enumerate subsets.
These features are a concrete starting point, not a proved sufficient
description of solver cost. The new learner does not modify or retrain the
repository's earlier frozen models.

- A certified easy bucket proposes the existing [block-overlap route](../block-overlap/README.md)
  with b=3. Build its representation and use it only if its exact overlap
  product K is at most 2^ceil(n/2); otherwise use meet in the middle.
- A certified hard or unresolved bucket uses complete meet in the middle.
- An exact range failure returns NO directly. Every returned YES witness is
  verified. Both solving routes exhaust their required possibilities before
  returning NO. The learned label itself supplies neither answer.

**Theorem 4 (exactness and fallback cost).** This router is exact for every
valid subset-sum input, regardless of statistical prediction errors. Once
the model has been fitted, its time is at most

$$
\operatorname{poly}(L,R)\bigl(1+2^{\lceil n/2\rceil}\bigr),
$$

where R is serialized model size. Fitting and collecting labeled costs are
additional offline expenses. No expected or measured speedup follows from
the purity theorem.

**Proof.** Learned output only selects one of complete exact algorithms.
The range check is sound. The block route's earlier theorem bounds its time
by poly(L)(2^3+K), and its guard bounds K by 2^ceil(n/2). Otherwise, build
the two indexed half-support lists and scan them for a pair summing to the
target; construction and matching take poly(L)2^ceil(n/2) bit time. Merging
equal half sums retains one sufficient witness. All feature/model work is
polynomial in L and R. Thus every route is exact and obeys the bound. QED.

The proof concerns completed executions with the required resources. The
reference implementation has exponential memory in the general MITM case;
it makes no promise that a large hard instance fits in available memory.

### Cost accounting for learning and certification

For fixed I gradient iterations, d features and N_train training rows,
score fitting uses O(I N_train d) arithmetic operations. Reference scoring
and sorting use O(N_ref d + N_ref log(N_ref+1)). Online rank lookup is
logarithmic in reference size, plus feature/scoring/quantile costs. This
implementation also rechecks the representation fingerprint on every public
prediction, costing O(R), which is included in Theorem 4.

Calibration computes O(M) rational binomial tails, each in O(N) big-integer
steps. If the rational thresholds have bit length ell, the intermediate
integers have O(N ell + N) bits. This is polynomial in the calibration data
size and threshold encoding, including confidence computations. None of
these costs includes the cost of obtaining actual solver labels; that must
be charged to a real experiment or deployment separately.

## 6. Run the implementation

The module uses Python's standard library. Each JSONL observation contains
either a `features` vector, or `weights` and `target` for the built-in
extractor. Optional unique `id` fields identify observations. Training and
calibration also need `cost`, or an explicit boolean `hard` meaning that the
declared budget was exceeded. Reference labels are not used.

```json
{"id":"train-1","weights":[2,3,4,20,30,40],"target":57,"cost":12}
```

The cost above is an illustrative schema value, not a measured runtime.
Use consistent solver identities, units and cost definitions across splits.
An unlabeled censored cost is rejected. Explicit labels that contradict a
complete observed cost are also rejected.

Fit a new artifact from independent split files:

```powershell
python notes/01-certified-coverage/distribution-shaping/algorithm.py fit --train train.jsonl --reference reference.jsonl --calibration calibration.jsonl --solver-id my-fixed-solver-v1 --budget 10000 --output model.json
```

An optional `--config config.json` sets `bins`, `epsilon`, `minimum_mass`,
`delta`, `threshold`, training controls, optional `cost_weight_cap`, and two
`shapes` dictionaries containing `mu`, `sigma`, `lower`, `upper`. For example:

```json
{
  "bins": 2,
  "epsilon": "0.1",
  "minimum_mass": "0.05",
  "delta": "0.05",
  "shapes": [
    {"mu": -1.0, "sigma": 0.35, "lower": 0.05, "upper": 1.0},
    {"mu": 1.6, "sigma": 0.2, "lower": 2.0, "upper": 12.0}
  ]
}
```

Risk/mass/failure thresholds are parsed as exact rational numbers. The
returned artifact fingerprints both the frozen representation and its
calibration record; changing either requires fitting/calibration again.
Hashes detect accidental changes, not maliciously forged evidence.

Identify new cases, or add `--run-exact` to invoke the exact subset-sum router:

```powershell
python notes/01-certified-coverage/distribution-shaping/algorithm.py predict --model model.json --input new_cases.jsonl --output predictions.jsonl
```

An optional `--seed` makes randomized ties reproducible for review. The
statistical theorems model independent uniform ties; the implementation uses
ordinary pseudorandom draws when a seed is supplied and system randomness
otherwise. A changed deployment population or solver/budget requires renewed
validation. Feature dimensions and semantics must match the fitted model;
the exact router requires a model trained on the built-in 12-feature schema.

## 7. Verification and example

Rebuild the standalone note with:

```powershell
python notes/01-certified-coverage/distribution-shaping/build_note.py
```

This checks the saved verification-source hashes and every reported table
value, compiles the self-contained LaTeX source twice, and checks references
and overflow warnings without a page limit. Sections flow naturally;
there are no forced section page breaks. It requires `pdflatex` and `pdfinfo`.
Build scratch stays under `.build/latex/distribution-shaped-difficulty/`.
The build neither runs experiments nor overwrites the verification record.

Run the finite proof checks:

```powershell
python notes/01-certified-coverage/distribution-shaping/verify.py
```

Pass `--output` with a fresh path to save a new report. Optional
`--demo-model` writes a model for the synthetic one-feature population;
that model is for shaping/identification only, not the 12-feature exact
router. [validation.json](validation.json) records the initial verification
and SHA-256 hashes of algorithm.py and verify.py.

Checks include exact binomial tails against independent direct summation,
enumerated type-I rejection probabilities, quantile/CDF inversion, tied
scores, empty buckets/groups, label censoring, representation fingerprints,
serialization, and exact subset-sum answers under all three routing labels.
Small subset-sum results are compared with independent exhaustive subsets.

The synthetic demonstration samples training, reference, and calibration
independently from a known finite population of 101 feature values. Its
cost rule is constructed, not measured solver runtime. Exact integration
over randomized ties verifies the true mass and purity of each identified
bucket. The saved run identifies two hard buckets of about 20.5% and 21.1%
population mass, with actual hard fractions about 95.2% and 100%; the requested
certificate is at least 5% mass and 90% hard purity, at simultaneous confidence
95%. This illustrates availability on that population. The proof does not
guarantee that real subset-sum features will achieve similar coverage.

The calibration theorem itself is proved above for arbitrary frozen models
and i.i.d. populations. Finite tests supplement the proof; a successful
demonstration is not a distribution-independent separation theorem.

## 8. Sources and relationship to earlier work

- Hutter, Xu, Hoos, and Leyton-Brown, [Algorithm Runtime Prediction: Methods
  & Evaluation](https://arxiv.org/abs/1211.0906): the established use of
  instance features to predict solver runtime.
- Clopper and Pearson, [The Use of Confidence or Fiducial Limits Illustrated
  in the Case of the Binomial](https://doi.org/10.1093/biomet/26.4.404), 1934:
  exact binomial inversion. The threshold tests here use this classical
  one-sided logic with a union bound across predeclared claims.
- Massart, [The Tight Constant in the Dvoretzky-Kiefer-Wolfowitz Inequality](https://doi.org/10.1214/aop/1176990746),
  1990: the finite-reference CDF inequality used in Theorem 2.
- Hoeffding, [Probability Inequalities for Sums of Bounded Random Variables](https://doi.org/10.1080/01621459.1963.10500830),
  1963: the binomial tail bound used in the availability corollary.
- Gangrade, Kag, and Saligrama, [Selective Classification via One-Sided
  Prediction](https://proceedings.mlr.press/v130/gangrade21a.html), 2021:
  relevant precedent for predicting on selected regions with abstention.
- The repository's [feature theory](../../../Learned_Solvability_Subset_Sum/docs/THEORY.md)
  already distinguishes budgeted solver completion from universal hardness.
  This follow-up adds a selected target distribution and finite-sample
  simultaneous bucket mass/purity tests. Earlier frozen experiments and
  models are preserved.

The contribution here is a concrete combined formulation and reference
implementation of these ingredients. A comprehensive novelty assessment
and a fresh paid subset-sum evaluation remain separate tasks.
