# Subset-sum probability bounds: conversation transcript and research handoff

Prepared October 23, 2026.

Scope: the transcript starts with the requested assistant response beginning “Note III gives a valid way to bound the chance a random target is reachable.” It continues through the request for this export. User messages, substantive assistant replies, and assistant progress updates are retained in chronological order. Tool calls, tool output, and private reasoning are omitted. The research handoff after the transcript is newly written material.

## Conversation transcript

### Assistant

**Note III gives a valid way to bound the chance a random target is reachable.**

But the math is simple, the bounds are loose, and it hasn’t shown a speed advantage.

**Useful starting point; modest research result so far.**

### User

In my repo on semantic Boolean analysis I introduce a technique for tightening the bounds. Is it applicable to this case? If so so me the theory in chat

### Assistant — progress update

I’ll read the bound-tightening technique in your semantic Boolean repo and check how it applies to Note III.

### Assistant

**Yes. Your calibrated-envelope technique applies directly to Note III.** It can give narrower statistical bounds; deterministic bounds require proved error control.

Your [Boolean paper](https://github.com/jonland82/semantic-boolean-complexity/blob/master/papers/learned-semantic-envelopes/learned-semantic-envelopes.tex) supplies the general theorem. Here is its subset-sum version.

**1. Start with Note III’s certified interval.**

For fixed weights $w$ and a specified target distribution $\mu$, define

$$
q(w)=\Pr_{T\sim\mu}[T\text{ is reachable}].
$$

Witnessed targets $L$ and a sound outer target set $U$ give

$$
\ell(w)=\mu(L)\le q(w)\le\mu(U)=u(w).
$$

Write the unresolved width as $W(w)=u(w)-\ell(w)$. If $W=0$, the answer is already exact.

**2. Learn where the answer sits inside that interval.**

On training lists whose exact $q(w)$ is known, learn the normalized position

$$
\rho(w)=\frac{q(w)-\ell(w)}{W(w)}\in[0,1].
$$

A model predicts $\widehat\rho(w)\in[0,1]$, giving

$$
\widehat q(w)=\ell(w)+\widehat\rho(w)W(w).
$$

This requires a predictor of **reachability fraction per weight list**. Note II’s classifier predicts individual target answers, so it would need adaptation.

**3. Calibrate the error and intersect.**

On separate calibration lists, measure the normalized errors

$$
s^-=\frac{(\widehat q-q)_+}{W},
\qquad
s^+=\frac{(q-\widehat q)_+}{W}.
$$

Choose split-conformal upper quantiles $c^-,c^+$, allocating error probability $\alpha/2$ to each tail. Then use

$$
\boxed{
I_*(w)=
\left[
\max\{\ell,\widehat q-c^-W\},
\min\{u,\widehat q+c^+W\}
\right].
}
$$

Under exchangeability of calibration and new lists,

$$
\Pr\{q(w)\in I_*(w)\}\ge1-\alpha.
$$

That probability concerns coverage **across new weight lists**; $q(w)$ itself concerns random targets within one list.

**4. Your tightening theorem transfers unchanged.**

Writing $p=\widehat\rho(w)$, the refined width satisfies

$$
\frac{|I_*(w)|}{W(w)}
=
\min\{p,c^-\}+\min\{1-p,c^+\}
\le\min\{1,c^-+c^+\}.
$$

Therefore,

$$
\boxed{
\text{fraction of original width removed}
\ge \max\{0,1-c^--c^+\}.
}
$$

For example, **if calibration achieves** $c^-=c^+=0.1$, every nonzero interval shrinks by at least **80%**. Whether subset-sum data permits allowances that small remains an experimental question.

**The crucial distinction:** interval shrinkage is guaranteed algebraically; containing the truth is statistical unless the error allowances are universally proved. Your [selection paper](https://github.com/jonland82/semantic-boolean-complexity/blob/master/papers/selection-breaks-calibration/selection-breaks-calibration.tex) also applies: selecting only the largest predicted improvements requires calibration that accounts for that selection.

So yes: **the theoretical transfer is direct. The research question is whether subset-sum structure predicts the remaining gap accurately enough to make the refinement useful.**

### User

Test it

### Assistant — progress update

I’ll test the refinement on subset-sum lists with exact reachability fractions, using separate training, calibration, and test sets. I’ll measure coverage, interval shrinkage, and runtime.

### Assistant — progress update

The method transfers cleanly, but it needs a new predictor: Note II’s model predicts YES/NO for individual targets; this test must predict the reachable-target fraction for a whole list. I’m keeping Note III’s target rule and comparing against calibrated midpoint and density baselines.

### Assistant — progress update

The experiment has generated exact fractions for all 1,000 test lists, and every original analytic interval contains its answer. A separate test on larger lists is still running to check how the calibrated refinement behaves when the problem size changes.

### Assistant — progress update

On the matched test, the learned intervals shrank by about 77% and contained the truth on 975 of 1,000 lists. The simple density model came close: 74% shrinkage and 972 covered.

The larger-list test exposed a limit: the main model’s coverage dropped to 88.8%. I’ll include that failure alongside the successful result.

### Assistant — progress update

The checks passed. The results support calibrated statistical tightening on the tested distribution; they also show that the main model’s calibration did not carry over to larger lists. I’m saving the report, raw results, and reproduction code using the Library skill.

### Assistant

**Yes—it worked on matched data.**

Using separate training and calibration sets, I tested 1,000 fresh 16-weight lists:

| Method | Average width removed | Contained the truth |
|---|---:|---:|
| Your method + structural model | **77.0%** | **97.5%** |
| Simple density model | 74.0% | 97.2% |
| Calibrated midpoint | 56.8% | 96.1% |

The target coverage was 95%.

**The limitation:** on 240 larger, 20-weight lists, the structural model’s coverage dropped to **88.8%** without recalibration.

This supports useful **statistical tightening**, with a modest advantage over the density baseline. It does not establish universally valid tighter bounds.

[Subset_Sum_Refinement_Report.html](sandbox:/workspace/scratch/37b355549cd7/subset_sum_refinement/Subset_Sum_Refinement_Report.html) · [Subset_Sum_Refinement_Experiment.zip](sandbox:/workspace/scratch/37b355549cd7/subset_sum_refinement/Subset_Sum_Refinement_Experiment.zip)

### User

Use the analytical form of the statistical tightening along with the specific form of the subset sums formalism to derive a better bound. Seems like in this case given the specifics it should be possible algebraically

### Assistant — progress update

I’ll look for an algebraic improvement using the subset-sum structure—especially repeated sums, complementary subsets, and the restricted target range—and check any proposed inequality on small exact cases.

### Assistant — progress update

I found a deterministic correction: count half-sum pairs that actually land in the target range, then discount pairs that produce the same target. The first step alone reduced interval width by 13.1% on average on the earlier 1,000-list cohort, with every bound still containing the truth. The collision correction gives a further algebraic refinement.

### Assistant

**Yes. The subset-sum structure lets us turn part of the predicted tightening into a proved correction.**

The key is that Note III’s upper bound counts selection patterns. Some fall outside the target range; others produce the same sum.

**1. Count only relevant half-sum pairs.**

Let $D$ be the target set, $d=|D|$, and

$$
K=\prod_j(c_j+1),
$$

where $c_j$ is each distinct weight’s multiplicity. The original upper bound is $q\le\min(1,K/d)$.

Partition the weight-value groups into two blocks, keeping repeated copies together. Let $A,B$ be their distinct attainable sums. Define

$$
r(t)=|\{(a,b)\in A\times B:a+b=t\}|,
\qquad
M=\sum_{t\in D}r(t).
$$

Every reachable target has at least one representation, so

$$
\boxed{q\le \min\left(1,\frac{M}{d}\right),\qquad M\le K.}
$$

For Note III’s target rule, $M$ can be counted using sorted half-sum lists and interval searches. Every attainable pair sum already passes the modular screens.

**2. Subtract collisions algebraically.**

Define the number of colliding representation pairs,

$$
J=\sum_{t\in D}\binom{r(t)}2,
$$

and take any certified cap $R\ge\max_{t\in D}r(t)$. Always,

$$
R=\min(|A|,|B|)
$$

is safe.

Writing $N=|A(w)\cap D|$, we have

$$
M-N=\sum_{t:r(t)>0}(r(t)-1).
$$

Because $r(t)\le R$,

$$
2J=\sum_t r(t)(r(t)-1)\le R(M-N).
$$

Therefore,

$$
\boxed{q\le \min\left(1,\frac{M-2J/R}{d}\right).}
$$

This removes both irrelevant selection patterns and a **provable amount of collision overcounting**.

**3. This is exactly an analytical version of your slack refinement.**

Before capping the original upper endpoint at $1$, its removable slack satisfies

$$
\boxed{
\frac Kd-q
\ge
\frac{K-M+2J/R}{d}.
}
$$

Your statistical method predicts how much slack can be removed. Here, the subset-sum algebra certifies a particular removal directly.

**4. Collisions also give a lower bound.**

Cauchy–Schwarz gives

$$
M^2\le N\sum_t r(t)^2=N(M+2J).
$$

Also, $r-1\le\binom r2$ implies $N\ge M-J$. Consequently, for $M>0$,

$$
\boxed{
\frac1d\max\left\{M-J,\frac{M^2}{M+2J}\right\}
\le q
\le
\min\left\{1,\frac{M-2J/R}{d}\right\}.
}
$$

Intersect this with the existing certified interval. It can only tighten it. If $M=0$, then $q=0$.

For example, with weights $(10,20,30,100)$ and targets $20,\ldots,120$,

$$
d=101,\quad K=16,\quad M=9,\quad J=1,\quad R=2.
$$

The bounds collapse to the exact answer:

$$
\frac{M-J}{d}
=\frac{M-2J/R}{d}
=\boxed{\frac8{101}},
$$

improving the original upper bound $16/101$.

I checked these inequalities on **1,200 small exact cases**. On the earlier 1,000-list cohort, using **only the inexpensive $M/d$ correction** removed **13.1% of interval width on average**, with all bounds valid.

Computing the collision information can be expensive. But even a certified lower bound on $J$ strengthens the upper bound—so a full collision calculation is unnecessary to obtain further improvement.

### User — request for this export

give a transcript of our convo as markdown since your response that started with -- "Note III gives a valid way to bound the chance a random target is reachable." --- then describe at the bottom of the transcript the next extension steps given these substantial results that we just went thru. i will use this in codex to continue my research

---

## Research handoff for Codex

The remainder is a continuation brief, not part of the historical transcript. It records what is established, how to reproduce the work, and the next extensions to pursue.

### 1. Research objective and current status

The objective is to tighten the probability-valued subset-sum bounds in Note III, then determine whether useful certified accuracy can be obtained at less cost than direct computation. The conversation produced two related developments:

1. A direct application of gap-normalized, prediction-calibrated interval refinement, with a completed frozen experiment showing substantial matched-distribution shrinkage and a failure under a size shift.
2. An algebraic decomposition of the original upper-bound slack into count-pattern compression, target-range exclusion, and repeated representations of the same target. This yields deterministic upper and lower bounds using representation counts and collision moments.

The experiments support a useful research direction. They do not yet establish a new complexity bound, a robust cross-size statistical guarantee, a practical advantage over optimized alternatives, or literature novelty. The moment inequalities use elementary counting, Cauchy–Schwarz, and a Bonferroni-type support bound; investigate their relationship to existing sumset and additive-energy methods before making novelty claims.

### 2. Source repositories and papers

- [Exponential Search Spaces repository](https://github.com/jonland82/exponential-search-spaces), default branch main.
- [Note III: Probability-Valued Subset Sum](https://github.com/jonland82/exponential-search-spaces/blob/master/notes/03-probability-valued-subset-sum/Probability_Valued_Subset_Sum.tex).
- [Existing probability experiment](https://github.com/jonland82/exponential-search-spaces/blob/main/subset-sum/probability_extension.py).
- [Existing weight generator and features](https://github.com/jonland82/exponential-search-spaces/blob/main/subset-sum/ml_experiment.py).
- [Semantic Boolean Complexity repository](https://github.com/jonland82/semantic-boolean-complexity), default branch master.
- [Prediction-Calibrated Refinement of Analytic Bounds](https://github.com/jonland82/semantic-boolean-complexity/blob/master/papers/learned-semantic-envelopes/learned-semantic-envelopes.tex).
- [When Selection Breaks Calibration](https://github.com/jonland82/semantic-boolean-complexity/blob/master/papers/selection-breaks-calibration/selection-breaks-calibration.tex).

No remote repository was modified during this conversation. The experiment code and outputs were created separately. Read current repository instructions and check for later upstream changes before preparing a patch.

### 3. Artifacts and reproduction

The completed experiment is packaged in:

- Subset_Sum_Refinement_Experiment.zip — full source snapshot, frozen protocol, weights, labels, per-list interval predictions, checks, provenance, and HTML report.
- Subset_Sum_Refinement_Report.html — standalone report.

Their original paths in this conversation are:

    /workspace/scratch/37b355549cd7/subset_sum_refinement/Subset_Sum_Refinement_Experiment.zip
    /workspace/scratch/37b355549cd7/subset_sum_refinement/Subset_Sum_Refinement_Report.html

The persistent file identifiers, if the continuing environment supports the same file connector, are:

    Subset_Sum_Refinement_Experiment.zip:
    libfile_77e52bb6da188191b0e3591858d0c0ff

    Subset_Sum_Refinement_Report.html:
    libfile_f3aa1c0e0fdc8191ba5092fe83e3d801

These identifiers are retrieval references, not credentials. The scratch paths are conversation-specific and may be unavailable in a new Codex environment. In that case, provide the ZIP alongside this Markdown file and extract it. This transcript alone does not embed the ZIP or its raw data.

Within the extracted experiment directory:

    python -m pip install -r requirements.txt
    OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 python run_refinement.py
    python make_report.py

Important files:

    protocol.json
    run_refinement.py
    make_report.py
    upstream/subset-sum/ml_experiment.py
    upstream/subset-sum/experiment.py
    upstream/subset-sum/probability_extension.py
    results/train.jsonl
    results/calibration.jsonl
    results/test.jsonl
    results/unseen_n20.jsonl
    results/predictions.csv
    results/summary.json
    results/independent_checks.json
    results/provenance.json

The JSONL rows retain full weights, support denominator, target interval, multiplicity count, exact reachable-target count, original bounds, features, split identity, and timings. Provenance records exact source hashes and package versions.

### 4. Completed statistical experiment: exact specification

- Seed: 731029.
- Training: 1,200 independent 16-item lists.
- Calibration: 500 additional independent 16-item lists.
- Primary test: 1,000 additional independent 16-item lists.
- Prespecified size-transfer diagnostic: 240 independent 20-item lists.
- Family selection: independently equiprobable independent-weight or repeated-pair family.
- Weight generator: the upstream make_weights implementation, including its density/scale variation.
- No duplicated sorted weight lists across any cohorts.
- Target set: integer targets from round(0.30 times total weight) through round(0.70 times total weight), inclusive, restricted to targets passing the reachable-residue checks modulo 8, 10, 16, and 32.
- Target distribution: uniform on that eligible set. Its size is counted exactly using the period-160 residue structure.
- Original lower endpoint: distinct eligible sums witnessed by 512 sampled subsets, divided by eligible target count.
- Original upper endpoint: min(1, product of multiplicity counts plus one, divided by eligible target count).
- Exact q labels: full attainable-sum enumeration, used for training, calibration, and evaluation; excluded from test features and construction of test intervals.
- Primary model: HistGradientBoostingRegressor with max_iter=200, max_leaf_nodes=15, learning_rate=0.05, min_samples_leaf=20, l2_regularization=1.0, fixed seed.
- Density baseline: degree-two polynomial ridge regression using only density proxy, unique-weight fraction, and original upper endpoint.
- Midpoint baseline: normalized prediction 1/2.
- Prediction target: normalized position inside the original interval.
- Calibration: separate one-sided normalized error scores, 2.5% nominal error in each tail, using ordered score number ceil(501 times 0.975)=489.
- No fitting, hyperparameter changes, model selection, or recalibration after inspecting test results.

Primary test results:

| Center | Covered / lists | Coverage | Exact 95% binomial CI for coverage | Mean per-list width removed | Mean remaining width |
|---|---:|---:|---:|---:|---:|
| Structural model | 975 / 1,000 | 97.5% | 96.33%–98.38% | 76.96% | 0.0926085 |
| Density baseline | 972 / 1,000 | 97.2% | 95.98%–98.13% | 73.95% | 0.1045138 |
| Calibrated midpoint | 961 / 1,000 | 96.1% | 94.71%–97.21% | 56.79% | 0.1747668 |

The mean original width was 0.4044522. Mean fractional reduction and reduction in the mean width are different statistics; do not interchange them.

Structural-model corrections were:

$$
c^-=0.1321238130483019,\qquad
c^+=0.09935828651288747.
$$

Thus the algebraic width identity guarantees at least 76.85179% shrinkage for each noncollapsed interval formed with these corrections. This is a guarantee about interval width, not deterministic containment of the answer.

On the primary test, all 25 structural-model misses occurred among the repeated-pair lists: coverage was 499/499 for independent weights and 476/501 for repeated pairs.

On the 20-item diagnostic:

| Center | Covered / lists | Coverage | Mean per-list width removed |
|---|---:|---:|---:|
| Structural model | 213 / 240 | 88.75% | 76.86% |
| Density baseline | 237 / 240 | 98.75% | 73.83% |
| Calibrated midpoint | 239 / 240 | 99.58% | 56.79% |

The structural-model coverage CI on the larger lists was 84.06%–92.45%, below the nominal 95% target. There is no exchangeability guarantee across that size shift. The simpler baseline’s successful transfer is an empirical observation, not a universal robustness result.

Checks completed:

- All 2,940 original certified intervals contained the exact q.
- Thirty small cases checked set-enumeration labels against direct brute force.
- Twelve primary-test labels independently checked using integer-bitset dynamic programming.
- Width identity and minimum-shrinkage inequality checked on all 3,720 model/cohort predictions.
- A prespecified top-20%-fractional-shrinkage diagnostic produced structural-model coverage 197/200 on matched lists and 43/48 on larger lists. This does not establish arbitrary selection-conditional coverage.

The main run took approximately 69.4 seconds. Exact training and calibration labels took approximately 9.41 seconds; structural fitting took approximately 0.19 seconds. Primary-test outer-bound construction, feature extraction, and batched inference averaged approximately 0.99 ms per list, while exact set enumeration averaged approximately 5.82 ms per list. These compare a statistical interval against an exact answer, use small Python implementations, and include no optimized bitset or matched-accuracy sampling benchmark.

### 5. Completed algebraic work: theorem and evidence

Use the following notation consistently in the continuation:

- $\mathcal A(w)$: the full attainable-sum set.
- $D$: finite, nonempty target set; $d=|D|$.
- $A,B$: distinct attainable-sum sets for the two blocks.
- $K=\prod_j(c_j+1)$: count-pattern upper bound.
- $r(t)$: number of distinct half-sum pairs producing target t.
- $M=\sum_{t\in D}r(t)$: relevant pair count.
- $J=\sum_{t\in D}\binom{r(t)}2$: unordered colliding-pair count.
- $R$: a proved upper bound on r(t) for all t in D.
- $N=|\mathcal A(w)\cap D|$, so $q=N/d$.

Keeping all copies of each repeated value in the same block is essential for the specific comparison $M\le |A||B|\le K$. Arbitrary index partitions still give valid representation formulas, but their pair count need not be bounded by the globally compressed K. For example, splitting two copies of weight 1 across blocks gives four pairs but only three global count patterns.

The core identities are:

$$
M-N=\sum_{t\in D:r(t)>0}(r(t)-1),
\qquad
\sum_{t\in D}r(t)^2=M+2J.
$$

For $M>0$, the deterministic interval is:

$$
L_{\mathrm{alg}}
=\frac1d\max\left\{M-J,\frac{M^2}{M+2J}\right\},
\qquad
U_{\mathrm{alg}}
=\min\left\{1,\frac{M-2J/R}{d}\right\}.
$$

Intersect with any pre-existing certified interval. If M=0, return q=0. Do not divide by zero. R must be a certified cap; an estimated representation maximum cannot be substituted into a deterministic theorem.

The inequalities and the difference-based collision identity below were checked on 1,200 random small cases, with 2–10 weights, repeated values allowed, and irregular target sets allowed. This was randomized exact checking, not exhaustive verification over all inputs.

The worked example used weights (10,20,30,100), blocks (10,20) and (30,100), and D={20,...,120}. It gives d=101, K=16, M=9, J=1, and exact R=2. Both algebraic endpoints are 8/101.

An additional post-hoc test on the existing 1,000-list primary-test cohort evaluated only the relevant-pair upper bound M/d:

| Quantity | Result |
|---|---:|
| Mean original interval width | 0.4044522237405377 |
| Mean width after intersecting with M/d | 0.372926981391316 |
| Mean per-list fractional width reduction | 13.098753580857592% |
| Lists with a strictly smaller upper endpoint | 778 / 1,000 |
| Intervals containing the exact q | 1,000 / 1,000 |

The mean-width reduction is approximately 7.79%; the 13.10% number is the average of each list’s fractional reduction. Retain that distinction.

This post-hoc computation took approximately 0.10 seconds for the 1,000 lists in the observed run, including reconstruction of the half-sum sets. It was a single exploratory timing, not a controlled performance study.

This algebraic follow-up was executed as an inline calculation after the original ZIP was created. Its code and output are not included in that earlier ZIP. Reproduce and save it as the first continuation task. The full collision-refined interval has not been benchmarked on the 1,000-list cohort.

The grouping rule in the follow-up was: sort the distinct weight values; assign each complete value-multiplicity group to the block currently having smaller accumulated load $\sum\log_2(c_j+1)$. Generate each block’s distinct sums. For every a in A, count B values in [lo-a, hi-a] by binary searches. Divide by the stored eligible-target count, then intersect with the stored original interval. The modular filter need not be reapplied to attainable pair sums because they already satisfy it.

### 6. Next extension steps

#### Step A — reproduce and preserve the algebraic result

Implement a standalone, deterministic follow-up script using the saved primary-test lists. Reproduce the 778/1,000 strict improvements, the mean widths above, and the 13.10% average per-list shrinkage. Save per-list M, half-set sizes, partition, endpoints, exact q used for evaluation, and timings.

Add independent small-instance tests covering zero relevant pairs, singleton support, repeated weights, collision-free pairs, irregular D, asymmetric intervals, integer endpoints, and the example above. Verify the group-preserving partition condition. Preserve the original frozen statistical experiment unchanged.

Acceptance: exact agreement with the recorded aggregate results up to floating-point rounding, and no algebraic interval misses.

#### Step B — state and audit the theorem precisely

Write a short proposition and proof with explicit assumptions: positive integer weights, finite nonempty D, uniform targets for the cardinality formulas, distinct half sums, complete multiplicity groups within blocks when claiming M≤K, and a certified R.

Separate three claims:

1. Universal validity of the combinatorial inequalities.
2. Observed width improvement on the tested generator.
3. Computational cost of obtaining M, J, and R.

Use exact rational or integer arithmetic for certification. An integer-strengthened version can round the support-count lower endpoint upward and the upper endpoint downward before dividing by d.

Acceptance: independent exact verification of every theorem implementation; no statistical model output used as an unverified deterministic certificate.

#### Step C — bound collisions without enumerating all pair sums

For positive differences $\delta$, define

$$
A_\delta=\{a\in A:a+\delta\in A\},
\qquad
B_\delta=\{b\in B:b-\delta\in B\}.
$$

The exact identity checked during the conversation is

$$
J=
\sum_{\delta>0}
\left|\{(a,b)\in A_\delta\times B_\delta:a+b\in D\}\right|.
$$

Each unordered collision is counted once by its positive difference in the A coordinate. For a selected set of differences $\Delta$, summing only those terms gives a certified lower bound $J_-\le J$. Use sorted lists and interval counts within each selected difference rather than materializing the full Cartesian product.

If $J_-\le J\le J_+$, valid endpoints are

$$
L_{\mathrm{cert}}
=\max\left\{
\ell,\,
\frac{M-J_+}{d},\,
\frac{M^2}{d(M+2J_+)}
\right\},
$$

$$
U_{\mathrm{cert}}
=\min\left\{
u,\,
1,\,
\frac{M-2J_-/R}{d}
\right\}.
$$

These formulas apply for M>0. Handle M=0 separately. Lower and upper collision certificates have different roles: a lower collision bound tightens the upper support endpoint; an upper collision bound supplies lower support information.

A universally available but potentially loose choice is $J_+\le (R-1)M/2$. Stronger certificates should exploit shared differences, local additive relations, block structure, or residue information. Charge all certificate-construction costs.

Acceptance: the certificate procedure must avoid computing the complete r(t) histogram merely to rediscover N, unless that full computation is explicitly labeled as an evaluation oracle.

#### Step D — improve the representation cap R

The baseline cap min(|A|,|B|) may make the collision correction weak. Explore certified arithmetic caps.

One concrete route: for a modulus m, count half sums in each residue,

$$
a_i=|\{a\in A:a\bmod m=i\}|,\qquad
b_i=|\{b\in B:b\bmod m=i\}|.
$$

Then every target obeys

$$
r(t)\le C_m(t\bmod m),
\qquad
C_m(s)=\sum_{i=0}^{m-1}a_i b_{(s-i)\bmod m}.
$$

Thus the minimum of the basic cap and the appropriate maxima of C_m over residues occurring in D is another certified R. Multiple moduli can be combined safely. Use exact convolution or verified error control; floating-point FFT rounding alone is not a certificate.

This residue-cap extension follows from counting a superset of exact-sum pairs. It has not yet been implemented or benchmarked in the conversation.

#### Step E — use learning to find certificates

The stronger connection to the Boolean work is to predict where certified slack can be found, then verify the proposed correction exactly. A model can choose:

- Which multiplicity-preserving partition to build.
- Which differences to examine first.
- Which modulus or local additive relation is promising.
- Where to spend an additional witness budget.

Every accepted deterministic update must be justified by exact M, a proved collision certificate, or a proved R cap. Adaptive selection of valid certificates does not invalidate deterministic containment. Any additional prediction-calibrated band remains statistical and retains its calibration assumptions.

Do not reuse the original calibration constants after changing the analytic envelope and normalized target without a new justification. If the new deterministic envelope is built first and a new normalized residual is learned inside it, refit and recalibrate on disjoint data. Intersecting a previously valid statistical interval with an always-valid deterministic interval preserves its original marginal coverage on the original exchangeable population, but does not repair the observed size-transfer failure.

#### Step F — run a frozen, multi-size prospective study

Freeze the new method before generating untouched test lists. Include multiple sizes and both weight families in training and calibration, or calibrate within prespecified size/family strata with adequate sample counts. State the intended population before calibration.

Report:

- Deterministic containment, which must be 100% absent numerical or implementation error.
- Statistical coverage separately, both marginal and by prespecified strata.
- Mean and median per-list shrinkage, and reduction in mean width as distinct statistics.
- Width versus total work and memory.
- Failure cases and size-transfer diagnostics.
- Any selection procedure used to choose instances or certificate actions.

The old 1,000-list cohort can remain a regression benchmark but is no longer untouched evidence for a method developed after inspecting it.

#### Step G — benchmark useful accuracy against meaningful alternatives

Compare original Note III bounds; relevant-pair counting alone; partial-collision refinement; improved R; the combined deterministic interval; and any learned extension.

Use direct attainable-sum enumeration, optimized integer-bitset dynamic programming where feasible, and sampling targets with exact decision labels as baselines. Include preprocessing, half-set construction, certificate work, model inference, and memory. Report model training and exact calibration-label costs separately.

The operational question is: for a prespecified error tolerance, what total work is needed to reach the required interval width or produce a valid answer? A narrow interval that costs as much as exact enumeration is mathematically valid but does not establish an algorithmic advantage.

#### Step H — assess novelty and integrate the research

Search primary literature on subset-sum support bounds, additive energy, second-moment support inequalities, Bonferroni bounds, meet-in-the-middle counting, and certified approximation. The elementary inequalities may be established tools; a potential contribution could lie in the target-restricted formulation, a cheap certificate scheme, a useful composition with learned guidance, or a convincing cost-versus-accuracy result.

After verification, prepare a local revision to Note III or a companion note. A clean narrative is:

1. Broad analytic envelopes leave measurable slack.
2. Calibrated learning locates that slack empirically but fails under some shifts.
3. Subset-sum representation identities expose part of the slack algebraically.
4. Certified range and collision corrections turn that structure into valid bounds.
5. Experiments determine when obtaining the corrections is worth the cost.

Preserve the negative size-transfer result. Do not present the 77% statistical shrinkage as a universal analytic guarantee, or the 13.1% deterministic follow-up as a new prospective test.

### 7. Optional mathematical extension: nonuniform targets

The conversation’s algebraic bounds used uniform targets. A natural extension to verify is to retain a finite probability mass function $\mu$ and define

$$
M_\mu=\sum_t\mu(t)r(t),
\qquad
J_\mu=\sum_t\mu(t)\binom{r(t)}2.
$$

The same pointwise inequalities and weighted Cauchy–Schwarz suggest, for $M_\mu>0$,

$$
\max\left\{M_\mu-J_\mu,\frac{M_\mu^2}{M_\mu+2J_\mu}\right\}
\le q_\mu
\le
\min\left\{1,M_\mu-\frac{2J_\mu}{R}\right\}.
$$

Check and prove this as a separate extension, including zero-mass and zero-M cases. These weighted formulas were not empirically tested in the completed experiment. Their computational usefulness depends on how $\mu$ is represented and how weighted pair counts can be obtained.

### 8. Suggested opening instruction for the continuing Codex session

Continue the research described in this transcript using the attached experiment ZIP and the two linked repositories. First reproduce the existing results without changing the original frozen experiment. Then implement and verify the deterministic relevant-pair and partial-collision bounds, paying particular attention to complete multiplicity groups, certified representation caps, and computation cost. Freeze a new prospective multi-size evaluation before inspecting its exact test labels. Keep deterministic containment, statistical coverage, empirical speed, and novelty claims separate. Prepare reproducible code, proofs, raw measurements, and a concise proposed note revision; preserve the observed statistical size-transfer failure.

### 9. Continuation completed and integrated — October 23, 2026

This section updates the handoff after the recorded conversation; it is not part of that historical transcript. The reproduction, theorem implementation, and prospective benchmark described above have now been completed, and the user authorized integration into Paper III.

- The statistical rerun reproduced the main results: 76.96% matched mean per-list narrowing, 97.5% coverage, and 88.75% coverage under the size shift. A secondary density-model selection diagnostic varied because of floating-point ties; the limitation is recorded in the [rerun notes](reruns/20261023-103931/README.md).
- The missing deterministic calculation reproduced 13.0988% mean per-list narrowing, 778/1,000 strict improvements, and 1,000/1,000 containment. The [theory note](deterministic_refinement/THEOREM.md) proves integer-strengthened range/collision endpoints, an extremal collision upper certificate, and a stronger residue matching cap. Seven independent test groups passed.
- A protocol and protected-source hashes were frozen before generating 160 fresh lists, with 20 lists per family at each size 12, 16, 20, and 22. All deterministic intervals contained exact truth. Range counting removed 14.15% of width on average; partial collisions plus residue caps increased this to 14.19% at higher cost. Exact bitset DP agreed on 149 feasible lists; 11 exceeded its predeclared bit cap. Sampling, accuracy attainment, timing, and separately profiled memory are recorded in the [full report](deterministic_refinement/REPORT.md).
- [Paper III](../notes/03-probability-valued-subset-sum/Probability_Valued_Subset_Sum.html) ([PDF](../notes/03-probability-valued-subset-sum/Probability_Valued_Subset_Sum.pdf), [LaTeX](../notes/03-probability-valued-subset-sum/Probability_Valued_Subset_Sum.tex)) now includes the proofs, calibrated results and transfer failure, deterministic reproduction, and prospective cost study. Its tables, chart, methods notes, and machine-readable summary are generated from preserved measurements. The [publication methods ledger](../subset-sum/PROBABILITY_REFINEMENT.md) gives the source hashes and rebuild commands. The series remains four notes.

The current research bottleneck is finding substantially stronger verified collision information cheaply. The proven refinement remains valid, but the tested partial certificates yield little additional narrowing and establish no broad computational advantage. Literature novelty, stronger certificate selection, learned certificate guidance, and nonuniform-target extensions remain open. The frozen algorithms, protocols, original statistical data, and historical transcript are preserved; their pre-integration publication status is archival.
