# Stage 10: structural branch checks help; the learned gate adds no demonstrated gain

The first branch-pruning experiment is complete. It is an exploratory transfer
test of the frozen Paper VI model in Paper I's proposal--verification framework.
The original prospective study, fitted models and manuscript evidence are intact.

## Main result

Under a 50 ms budget per input, exact structural checks increased the observed
number of completed decisions. The combined model did not improve on a simple
distance rule with the same certificates available.

| Policy | Completed / 216 | Completion rate |
|---|---:|---:|
| Shared exact reductions + DFS | 152 | 70.4% |
| Always try a bounded structural check | 160 | 74.1% |
| Simple distance rule (distance <= 2) | 162 | 75.0% |
| Standard-feature learned gate | 156 | 72.2% |
| Combined-distance-and-standard learned gate | 159 | 73.6% |

These are medians of aggregate completions over three timing repeats. The
distance-only control computes all five distances and selects their minimum;
it uses no fitted parameters. All structural policies use the same exact core
queries, at most six exceptional items (64 assignments), and fallback DFS.
The DFS control shares the same checkpoint target reductions. Matched
acquisition controls that also compute the standard features completed 160
(always) and 162 (distance rule), so the learned gate loses this comparison
even when those feature acquisition costs are matched.

The combined model's observed gain over DFS is seven completions at the median,
or 4.6% more completed cases (3.2 percentage points of the test set). It finishes
three fewer cases than the distance rule. This is not evidence of a general
statistical improvement: the descriptive paired list-bootstrap interval for
the combined model's repeat-average completion difference versus DFS is
[-6, 17] cases, and versus the native distance rule is [-11.7, 1.7]. Both span
zero. The data contain 72 independent generated weight lists with dependent
targets; the conditional intervals resample whole lists, not individual nodes
or timing repeats. Multiple comparisons are not adjusted.

## Actual subtree pruning occurred

With the separate deterministic 10,000-visited-node limit, DFS completed 146
cases, the combined gate 162, always checking 163, and the distance rule 161.
This is a node allowance, not a common allowance for all computation.

The combined policy produced 3,571 certified NO subtree decisions in that pass.
Of these, 26 resolved a root and 3,545 occurred below the root. It constructed
40 YES witnesses at roots and 13 below roots. All are exact, rather than model
assertions. Of its 16 additional completed cases versus capped DFS, eight were
resolved by a root structural query and eight required further search. Thus
the implementation does resolve genuine internal subtrees, but some benefit
also comes from recognizing whole inputs cheaply.

Fewer visited nodes did not imply lower total cost. Across the node-capped
pass, combined gating visited 561,063 nodes versus DFS's 777,203, but used
3.474 seconds versus 0.792 seconds. Of the combined time, 2.315 seconds went to
feature acquisition and 0.443 to structural queries. This aggregate also mixes
different numbers of completed cases. On the 146 cases completed by both,
combined gating used 0.478 seconds and DFS 0.106 seconds. Cheap cases can become
slower when features are acquired repeatedly. These single-pass timings are
descriptive, not uncensored runtimes for the unresolved problems.

Benefits vary by family. In the live test the combined policy completed 18/18
few-value cases versus DFS's 12/18, and 16/18 progression cases versus 10/18.
It completed only 14/18 block-pair cases versus DFS's 18/18. At n=36, the
distance rule completed 53/72 cases, compared with 50 for combined gating and
48 for DFS. The current evidence concerns this constructed distribution.

## Whole-instance accuracy does not transfer unchanged

On 1,062 selected unresolved checkpoints from the unguided DFS, the combined
score had 69.9% accuracy, 67.1% precision and 99.2% recall for completion of the
bounded structural checker. That checker has no diagnostic time deadline;
completion means its fixed six-exception limit permits exhaustive checking.
This is a different label from the earlier portfolio's budgeted completion.
It is also a selected, dependent node sample, not 1,062 independent problems.

If the same high score were interpreted as predicting certified NO, precision
would be only 46.5%. That interpretation was never used by the solver. These
numbers explain why the earlier 95.5% whole-instance accuracy cannot justify
direct pruning: completion and infeasibility are different events, and the
residual-node and checker distributions differ from training.

## Verification and decision point

The experiment preserves 216 fresh cases (87 YES, 129 NO), independent oracle
witnesses/truths, 6,048 policy runs, 1,062 diagnostic records, the pre-generation
protocol, source snapshots and hashes. Every completed answer agrees with the
independent oracle; witnesses, resource limits, aggregate results and all hashes
pass the read-only validator. Scalar inference agrees with all saved frozen
model probabilities to 11 decimal places. Late answers are excluded; the
largest cooperative deadline overshoot was 1.565 ms. The original prospective
study also passes its full hash and result audit.

**Stage 10 is complete, and this is the discussion point.** We have a concrete
certified pruning mechanism and a useful simple-rule control. The old completion
model has not earned a role in choosing these checks. A next study should first
add a root-only structural control to isolate the value of repeated internal
checks, then evaluate a branch-specific predictor of net search time saved
after acquisition and verification costs. Training, threshold selection and
testing should use disjoint original weight lists/search trees, followed by
fresh held-out inputs. These results have not been used to retune this study.

## Evidence and reproduction

- [Saved comparison report](results/branch_pruning_20261025/REPORT.md).
- [Saved numerical results, family/size breakdowns and conditional intervals](results/branch_pruning_20261025/summary.json).
- [Protocol](BRANCH_PROTOCOL.md) and [soundness argument](BRANCH_THEORY.md).
- [Implementation](branch_pruning.py), [tests](test_branch_pruning.py) and [validator](validate_branch_pruning.py).

```powershell
python -m unittest discover -s Learned_Solvability_Subset_Sum -p "test_branch_pruning.py" -v
python Learned_Solvability_Subset_Sum/validate_branch_pruning.py Learned_Solvability_Subset_Sum/results/branch_pruning_20261025
python Learned_Solvability_Subset_Sum/branch_pruning.py --output Learned_Solvability_Subset_Sum/results/new_branch_experiment
```

The last command creates a new exploratory batch and excludes previously saved
lists, including the present batch. The saved inputs and deterministic solver
settings permit replay; live timings vary by machine. No asymptotic complexity
claim or publication change is made at this stage.
