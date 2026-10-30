# Distribution search on saved runtimes

Rebuild: `python tools/fit_subset_sum_runtimes.py` from the repository root.
This is a retrospective descriptive analysis. Frozen evidence stays unchanged.

Candidates: zero-location exponential, gamma, Weibull, lognormal, log-logistic,
inverse Gaussian, and lognormal mixtures with 2 through 8 components: 13 models.
Fits maximize likelihood on individual observations, avoiding dependence on
histogram bin choices. Mixtures fit Gaussian components to natural log runtime;
their raw-time likelihood includes the logarithmic transformation's Jacobian.
Mixture EM uses 20 deterministic starts for the final fit and 4 for each
validation fit. Reported fits converged; mixture optimization remains local.

Selection uses mean held-out log likelihood per input, over two seeded repeats
of six folds, holding out entire base weight lists. Related targets cannot appear
on opposite sides of a fold. Selection is exploratory; these same folds compare
all candidates, so this is not an independent confirmatory validation.

On all 576 observations, six lognormals have the best validation score
(-1.753339 natural-log units per input). Four lognormals score -1.758024 and
have the lowest nominal BIC, 2044.433 versus 2060.672 for six. The predictive
difference is small; these criteria favor different complexities. The four-term
model is a reasonable compact alternative. BIC's independent-observation
assumption is imperfect because targets share lists; it is descriptive here.

With numeric runtime t in milliseconds, every mixture has density

    f(t) = sum_j w_j / (t sigma_j sqrt(2 pi))
                 * exp(-(ln(t) - mu_j)^2 / (2 sigma_j^2)), t > 0.

The six-term model parameters are:

| j | weight | mu | sigma |
|---|---:|---:|---:|
| 1 | 0.152357063 | -4.486898296 | 0.316054673 |
| 2 | 0.018458829 | -3.693411069 | 0.072425912 |
| 3 | 0.143912938 | -2.796665483 | 0.390914063 |
| 4 | 0.195705447 | 0.348734230 | 0.555660996 |
| 5 | 0.264361578 | 1.611407987 | 0.507431121 |
| 6 | 0.225204145 | 2.495860692 | 0.218740377 |

For a histogram bin [a,b], its expected count is
576 times sum_j w_j [Phi((ln(b)-mu_j)/sigma_j) - Phi((ln(a)-mu_j)/sigma_j)].
This integrated-bin formula, rather than a raw density curve, is used in the
PNG/PDF comparison. Phi is the standard normal cumulative distribution function.

A separate search on the 430 completed inputs selects four lognormals by
validation and three by nominal BIC. All parameters and candidate scores are
in `fit_results.json`; `model_comparison.csv` provides a compact comparison.

The main fit describes the actual displayed histogram, including 146 stopping
times for unresolved runs. It estimates the distribution of observed elapsed
times under this policy and sample. Eventual completion times for unresolved
inputs remain unknown. Stopping by work/state limits is informative and does
not justify ordinary independent-censoring survival assumptions. The completed
subset also represents a conditional distribution under these limits.
No general asymptotic runtime law, causal meaning of mixture components, or
correspondence between components and certified structural classes is claimed.
