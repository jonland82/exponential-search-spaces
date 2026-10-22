# Subset sum as a test case

This folder contains the reproducible work behind [Note II: Subset Sum as a Stress Test](../Subset_Sum_as_a_Stress_Test.html) and [Note III: Probability-Valued Subset Sum](../Probability_Valued_Subset_Sum.html). The [series landing page](../index.html) gives the short narrative; the notes give the paper-length argument.

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

## Reading the raw data

In the JSON and CSV files, `n` is the number of weights, `target` is the integer being tested, and `group_id` identifies one weight list shared by its sampled targets. In `ml_predictions.csv`, `exact_yes` is the exact 0/1 answer, `probability_yes` is the calibrated forest's predicted YES probability, and `density_baseline_probability` is the comparison model's prediction. Timing fields named `seconds` use seconds; `peak_traced_mib` is Python-traced peak memory in mebibytes (MiB), where one MiB is $2^{20}$ bytes. Counts of sums refer to distinct sums unless a field says `attempts`; `visited_states` counts explored search branches.
