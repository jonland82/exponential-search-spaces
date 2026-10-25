# Learned solvability from distance to easy subset-sum structure

Paper VI. **Stage 9 complete as a first review draft: scoped prior-work audit,
manuscript and PDF built from preserved evidence.** The paper remains unpublished.
The original feasibility pilot and model-development results remain preserved.

**Stage 10 follow-up complete:** certified structural checks resolve search
subtrees, but the transferred combined model does not beat a simple distance
rule. At 50 ms, median completions were 152/216 for DFS, 159 for the combined
gate and 162 for the rule. See [branch findings and discussion point](BRANCH_FINDINGS.md),
[protocol](BRANCH_PROTOCOL.md), [soundness](BRANCH_THEORY.md) and
[saved report](results/branch_pruning_20261025/REPORT.md). This new exploratory
batch leaves the original frozen study and review manuscript unchanged.

- [Paper VI prospectus and remaining plan](../notes/06-learned-solvability/README.md).
- [Feature definitions, proofs, exact queries, and limits](THEORY.md).
- [Findings and decisions for discussion](FINDINGS.md).
- [Pilot report](results/pilot_20261025/REPORT.md).
- [Full summary](results/pilot_20261025/summary.json).
- [Stage 6 findings and recommendations](DEVELOPMENT_FINDINGS.md).
- [Progression and target-aware theory](ADVANCED_THEORY.md).
- [Development model comparison](results/development_20261025/ml/REPORT.md).
- [End-to-end completion prediction](results/development_20261025/end_to_end/REPORT.md).
- [Frozen-study findings and manuscript recommendation](PROSPECTIVE_FINDINGS.md).
- [Frozen study protocol](PROSPECTIVE_PROTOCOL.md).
- [Fresh prediction report](results/prospective_20261025/PREDICTION_REPORT.md).
- [Paid practical prioritization report](results/prospective_20261025/PRIORITY_REPORT.md).
- [Standalone study overview](results/prospective_20261025/figures/overview.pdf).
- [Paper VI PDF](../notes/06-learned-solvability/Predicting_Subset_Sum_Completion.pdf).
- [LaTeX manuscript](../notes/06-learned-solvability/Predicting_Subset_Sum_Completion.tex).
- [Scoped primary-source audit](LITERATURE.md).
- [Paper evidence manifest](../notes/06-learned-solvability/paper_evidence.json).

## Implemented

`features.py` returns exactly five integer distance features plus certificates,
indexed partitions, work counts, and timing diagnostics. Three distances are
exact minima; two are bounded-cost constructive upper bounds. Every core type
has an exact membership and original-index witness routine. Caps are explicit:
two distinct values, 128 reachable sums, and eight reachable intervals per prefix.
These are pilot choices, not optimized thresholds or final paper definitions.

`run_pilot.py` generates nine synthetic families at n=16,24,32, with three
replacement levels, two replicates and three targets per list. It reuses Paper V's
exact solvers and validates completed decisions against independent half enumeration.
All raw weights, targets, oracle witness masks, certificates, attempts, work counts,
timings, source snapshots, configuration and hashes are preserved under `results/`.

The portfolio first applies target-filtered range/gcd checks, then bitset DP,
superincreasing exception enumeration, memoized DFS and meet-in-the-middle. Work
is divided by a fixed schedule, with state and bitset caps. Labels mean completion
under that particular policy and its resource limits, not universal easiness.

The cost comparison adds feature extraction to that same policy without reusing
the new core certificates. It isolates a possible overhead, not the best feature-
enabled solver and not a test of learned guidance. Subsequent implementations
should reuse certificates and compare against direct exact-solving shortcuts.

## Run and validate

The original feasibility pilot and core feature tests use the standard library.
The development/frozen model comparisons and prospective tests additionally use
`requirements-ml.txt`. Install those dependencies to run the full current suite.

```powershell
python -m unittest discover -s Learned_Solvability_Subset_Sum -p "test_*.py" -v
python Learned_Solvability_Subset_Sum/run_pilot.py --output Learned_Solvability_Subset_Sum/results/new_pilot
python Learned_Solvability_Subset_Sum/validate_results.py Learned_Solvability_Subset_Sum/results/pilot_20261025
python Learned_Solvability_Subset_Sum/run_development.py --output Learned_Solvability_Subset_Sum/results/new_development
python Learned_Solvability_Subset_Sum/fit_development.py --data Learned_Solvability_Subset_Sum/results/new_development --output Learned_Solvability_Subset_Sum/results/new_development/ml
python Learned_Solvability_Subset_Sum/fit_end_to_end.py --data Learned_Solvability_Subset_Sum/results/new_development --output Learned_Solvability_Subset_Sum/results/new_development/end_to_end
python Learned_Solvability_Subset_Sum/validate_development.py Learned_Solvability_Subset_Sum/results/development_20261025
python Learned_Solvability_Subset_Sum/prospective_study.py freeze --output Learned_Solvability_Subset_Sum/results/new_frozen_study
python Learned_Solvability_Subset_Sum/prospective_study.py generate --output Learned_Solvability_Subset_Sum/results/new_frozen_study
python Learned_Solvability_Subset_Sum/prospective_study.py analyze --output Learned_Solvability_Subset_Sum/results/new_frozen_study
python Learned_Solvability_Subset_Sum/priority_experiment.py --output Learned_Solvability_Subset_Sum/results/new_frozen_study
python Learned_Solvability_Subset_Sum/validate_prospective.py Learned_Solvability_Subset_Sum/results/prospective_20261025
```

A pilot requires a new output directory. The manifest and source snapshots are
written before generation, then source hashes checked again after execution.
This is exploratory evidence, not external preregistration. Replays reproduce
inputs and instrumented completion labels; wall-clock timings vary by machine.

## Development extension

`advanced_features.py` broadens coordinate 5 to choose between the original
interval representation and certified arithmetic-progression cores. It also
implements exact target reductions with witness lifting. Both vector variants
still have five coordinates. `run_development.py` compares original/progression
and list/target-aware choices using 324 new lists and 1,296 targets. It pays for
preprocessing, skips features when exact prechecks finish, and reuses zero-deletion
cores. Its code and inputs are snapshotted independently of the first pilot.

`fit_development.py` compares predictive information using one common solver-only
label. `fit_end_to_end.py` predicts each pipeline's actual completion including
extraction and reuse cost, with matched labels for all predictors within a task.
Both use logistic/forest models and disjoint calibration lists. Model outputs
include raw/calibrated probabilities, conventional and hybrid comparisons,
list-bootstrap intervals and subgroup metrics. Predictions have not yet been
used to guide solving, and inference cost has not yet been measured.

## Frozen evaluation and priorities

`prospective_study.py` freezes fitted models, protected sources and a protocol
before fresh generation. It tests 144 base lists, 288 paired encodings and 1,152
targets, with genuinely new families and n=38 inputs. `priority_experiment.py`
compares seven policies under shared pool budgets, using both fully charged
counter replay and separately measured live deadlines. `validate_prospective.py`
audits all model/data hashes, features, answers, probabilities and policy traces.
`plot_prospective.py` renders the saved results without any new model fitting.

## Paper and review status

The first manuscript presents definitions, elementary guarantees, matched
prediction comparisons, paid practical policies and limits. It cites established
empirical performance modeling, structural knapsack features, calibration,
backdoors and feature-cost accounting. No broad novelty or complexity claim is
made. The costed policy benefit cannot be isolated to the learned five inputs
without an additional matched core-reuse control.

`python build_papers.py --paper 6` verifies saved evidence and generates tables,
values, a paper-sized plot and the review PDF without rerunning experiments.
Notes V-VI remain excluded from the published four-note site and site staging.
