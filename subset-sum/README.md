# Subset sum as a test case

This folder contains the reproducible work behind Notes II, III, and IV. The [series landing page](../index.html) gives the narrative and reading order: start with [the framework](../notes/01-certified-coverage/Certified_Coverage_of_Exponential_Search_Spaces.html), then [the exact-search test](../notes/02-subset-sum-stress-test/Subset_Sum_as_a_Stress_Test.html). [Random-target probability](../notes/03-probability-valued-subset-sum/Probability_Valued_Subset_Sum.html) and [pairing in fixed-target approximation](../notes/04-certified-approximation/Certified_Approximation_of_Subset_Sum.html) are sibling extensions of that test.

The expanded Note III adds proved range/collision certificates, matched-data calibrated tightening with a size-transfer failure, and a frozen 160-list cost study. [PROBABILITY_REFINEMENT.md](PROBABILITY_REFINEMENT.md) explains the guarantees and measurements; [the experiment package](../Subset_Sum_Refinement_Experiment/README.md) links the frozen code and raw evidence. Rebuild the publication tables, chart, and summary with `python subset-sum/probability_refinement_artifacts.py`, or rebuild these plus the PDF/HTML with `python build_papers.py --paper Probability_Valued_Subset_Sum`. Neither command regenerates labels or timings.

[Note IV: Does Pairing Add Value to Certified Approximation?](../notes/04-certified-approximation/Certified_Approximation_of_Subset_Sum.html) reports a controlled negative timing result for fixed-target approximation. The key comparison finds no consistent additional timing gain over the same additive rule used sequentially, alongside one additional input finished within the state cap. Its [specification](APPROXIMATION_SPEC.md) establishes a common accuracy contract; its [results](APPROXIMATION_RESULTS.md) separate approximation, summary organization, and early witness discovery.

Given a list of $n$ positive integers $w_1,\ldots,w_n$ and a target $t$, **subset sum** asks whether there is a choice $x_i\in\{0,1\}$ for each number, with $x_i=1$ meaning that $w_i$ is included, such that

$$
\sum_{i=1}^{n}x_iw_i=t.
$$

Each choice vector describes one subset, so direct search has $2^n$ candidates. For example, the numbers $3,5,8$ reach target $11$ by choosing $3$ and $8$.

## Why it fits the framework

- **Exact representation:** Partial choices with the same sum have the same possible continuations. A group of items can be summarized by its set of reachable sums; summaries for two disjoint item groups combine by adding one sum from each. This gives a concrete, checkable pairing rule.
- **Certified elimination:** Because weights are positive, a partial sum above $t$ cannot succeed. Nor can a partial sum that remains below $t$ even after adding every remaining item. These are simple exact certificates for discarded branches.
- **Measurable tradeoff:** Inputs with repeated or small weights may have far fewer distinct reachable sums than subsets. Recording summary sizes, certified eliminations, uncovered candidates, and the cost of obtaining them tests whether coverage actually saves work.

The first experiments should compare against exhaustive search, conventional reachable-sum dynamic programming, and meet-in-the-middle search. A large gain over exhaustive search alone would illustrate compression, but would not establish an improvement over existing subset-sum algorithms.

## First experiment

Run `python subset-sum/experiment.py` from the repository root. The script checks small cases against exhaustive search, compares four exact solvers on fixed-seed inputs, and writes [the results](RESULTS.md) and [raw measurements](results.json). The first run found no general advantage for pairing: a cheap residue certificate helped one constructed no-solution family, while standard methods won elsewhere.

The [hard no-solution follow-up](HARD_RESULTS.md), reproduced with `python subset-sum/hard_experiment.py`, tests large targets with controlled repeated weights after all cheap root checks pass. On all 18 tested cases, the paired solver was slower than meet-in-the-middle and made no residue-based branch rejections. This narrows the useful next question: pairing needs a family where its exact summary and verifier jointly save work beyond what meet-in-the-middle already does.

## Probability-classifier experiment

The [machine-learning follow-up](ML_RESULTS.md) trains a classifier to estimate whether a target is reachable from a list. It includes [three PNG charts](classifier_overview.png), grouped held-out evaluation, a simple density-model comparison, and counts of mistaken proposed NO answers. Run `python subset-sum/ml_experiment.py` after installing [the ML dependencies](requirements-ml.txt). The classifier ranks cases reasonably well, but even its most confident NO proposals include real YES instances, so it cannot certify elimination on its own.

The [probability-valued extension](PROBABILITY_EXTENSION.md) defines the chance that a randomly drawn target is reachable, gives exact upper and lower bounds from witnesses and residue certificates, and reinterprets the classifier results with list-level uncertainty intervals. Its charts separate [target probability from classifier error](probability_bounds.png) and compare [certified per-list bounds with exact values](instance_probability_bounds.png). Reproduce it with `python subset-sum/probability_extension.py` after the ML experiment.

## Fixed-target approximation and the negative result

For fixed-target approximation, run `python -m unittest discover -s subset-sum -p test_certified_approximation.py -v`, then `python subset-sum/approximation_experiment.py`. The full run uses 48 list-target instances, four tolerances, and four methods; the largest inputs also run without the common greedy witness search. `--quick` writes a separate smoke dataset, and `--report-only` regenerates reports from saved measurements. The numerical benchmark requires only Python's standard library; plotting additionally uses `matplotlib`.

In [approximation_results.json](approximation_results.json), `cases` records weights, targets, seeds, and separately computed exact distances. Each comparison in `rows` records its absolute tolerance, greedy setting, and method results. `lower` and `upper` bound the optimal distance, `subset_indices` reconstructs the returned witness, and `status` distinguishes a certified answer from a summary-state limit. `peak_traced_mib` measures Python allocation in a separate run. [approximation_summary.json](approximation_summary.json) supplies aggregate counts and matched timing ratios.

## Reading the earlier raw data

In the JSON and CSV files, `n` is the number of weights, `target` is the integer being tested, and `group_id` identifies one weight list shared by its sampled targets. In `ml_predictions.csv`, `exact_yes` is the exact 0/1 answer, `probability_yes` is the calibrated forest's predicted YES probability, and `density_baseline_probability` is the comparison model's prediction. Timing fields named `seconds` use seconds; `peak_traced_mib` is Python-traced peak memory in mebibytes (MiB), where one MiB is $2^{20}$ bytes. Counts of sums refer to distinct sums unless a field says `attempts`; `visited_states` counts explored search branches.
