# Scoped prior-work audit for Paper VI

Audit date: October 25, 2026. Primary papers, author-hosted manuscripts and the
ASlib specification were inspected. This is a scoped audit, not an exhaustive
novelty certification. Publication dates below follow the papers, not search
engine crawl/upload dates.

## Scope and sources

Queries combined subset sum / knapsack with structural features, empirical
hardness, machine learning, runtime prediction, distance to easy structure,
feature computation cost, algorithm selection, calibration and backdoors.

1. **Empirical algorithm performance prediction is established.** Hutter, Xu,
   Hoos and Leyton-Brown, *Algorithm Runtime Prediction: Methods & Evaluation*,
   Artificial Intelligence 206 (2014), 79-111. The paper studies instance-feature
   models and explicitly discusses success-probability prediction and censored
   observations. Our fixed-budget binary label is a specific observed outcome,
   not a new general performance-modeling principle.
   [Author preprint](https://arxiv.org/abs/1211.0906),
   [published DOI](https://doi.org/10.1016/j.artint.2013.10.003).

2. **Feature cost and cheap exact presolving already matter in learned portfolios.**
   Xu, Hutter, Hoos and Leyton-Brown, *SATzilla: Portfolio-based Algorithm Selection
   for SAT*, JAIR 32 (2008), 565-606. Section 4.2 records feature timeouts and a
   fallback solver; Section 4.3 includes presolving and feature computation in
   total runtime. Our use of exact prechecks and paid prediction must not be
   presented as a new general portfolio technique. We prioritize instances for
   a fixed portfolio rather than learn a per-instance solver choice.
   [Primary paper](https://arxiv.org/abs/1111.2249),
   [DOI](https://doi.org/10.1613/jair.2490).

3. **Accounting for answers obtained during feature computation is established.**
   Bischl et al., *ASlib: A Benchmark Library for Algorithm Selection*, Artificial
   Intelligence 237 (2016), 41-58. Sections 3 and 6.2 describe feature costs and
   presolved instances; their evaluation includes costs and credits instances
   solved during feature generation. This closely precedes our certificate-reuse
   accounting. The model/inference/trace freeze is our reproducibility procedure,
   not a claim that feature-cost accounting originated here.
   [Primary paper](https://arxiv.org/abs/1506.02465),
   [DOI](https://doi.org/10.1016/j.artint.2016.04.003),
   [official scenario format](https://github.com/coseal/aslib-spec/blob/master/format.md).

4. **Closest problem-domain precedent: structural knapsack features predicting
   difficulty.** Jooken, Leyman and De Causmaecker, *Features for the 0-1 knapsack
   problem based on inclusionwise maximal solutions*, European Journal of
   Operational Research 311(1) (2023), 36-55. They derive 14 features from
   structural results and evaluate added empirical-hardness information for the
   Combo solver, noting expensive computation. This rules out a broad novelty
   claim about combining structural theory with learned knapsack hardness.
   Their optimization problem, features and solver differ from our subset-sum
   decision task and five deletion coordinates. The arXiv version predates the
   journal publication; the published/accepted version also discusses cheaper
   approximations.
   [Primary preprint](https://arxiv.org/abs/2211.09665),
   [accepted manuscript](https://backoffice.biblio.ugent.be/download/01GYY78DHGZDPR9EHAQV2ZQADQ/01GYY7BPDQZGQBG5H88FWXC2H6),
   [DOI](https://doi.org/10.1016/j.ejor.2023.04.023).

5. **Probability calibration is established.** Niculescu-Mizil and Caruana,
   *Predicting Good Probabilities With Supervised Learning*, ICML 2005, 625-632.
   Section 2 discusses sigmoid/isotonic calibration and an independent calibration
   set. Our second logistic fit on clipped-logit scores is a specified regularized
   sigmoid calibration; we do not claim to implement every detail of original
   Platt target smoothing or introduce a calibration method.
   [Author paper](https://www.cs.cornell.edu/~alexn/papers/calibration.icml05.crc.rev3.pdf),
   [DOI](https://doi.org/10.1145/1102351.1102430).

6. **Distance to a tractable remainder has established relatives.** Williams,
   Gomes and Selman, *Backdoors To Typical Case Complexity*, IJCAI 2003,
   1173-1178, studies small variable sets exposing tractable reasoning structure.
   The elementary branching-on-exceptions condition here is an analogous concrete
   decomposition, not a new general parameterized-complexity framework.
   [Author paper](https://www.cs.cornell.edu/selman/papers/pdf/03.ijcai.backdoors.pdf).

7. **The exact subset-sum primitives have substantial prior literature.**
   Superincreasing membership is documented in the
   [SageMath manual](https://doc.sagemath.org/html/en/reference/numerical/sage/numerical/knapsack.html).
   Bringmann and Nakos, *Top-k-Convolution and the Quest for Near-Linear
   Output-Sensitive Subset Sum*, STOC 2020, full version arXiv:2107.13206, studies
   support-sensitive solving. Our capped exact support is a feature extractor,
   not an improved output-sensitive algorithm. See also Paper V's
   [broader subset-sum audit](../Structural_Distance_Subset_Sum/LITERATURE.md).
   [Primary full version](https://arxiv.org/abs/2107.13206).

## Claim boundary after the audit

The narrow deliverable is an auditable experiment with a specific five-coordinate
certified feature map, ordinary-feature and combined comparisons, frozen fresh
inputs, paired representation shifts, and separately costed counter/live
prioritization. Its unfavorable primary probability comparison and counter
endpoint are results alongside the modest live-time benefit.

The search did not establish that the exact five-coordinate combination or the
elementary progression recovery argument is novel. No new model, calibration
method, general selection principle, complexity classification or state-of-the-art
subset-sum solver is claimed. The missing matched-acquisition/core-reuse control
also prevents assigning the whole policy gain to the learned structural inputs.

Future novelty assessment should trace citations and seek exact matches to each
distance definition, broaden subsets/knapsack structural-parameter searches, and
compare mature solvers. A failure to find an exact matching title is not evidence
of novelty. This audit supports the empirical-study framing, not a priority claim.
