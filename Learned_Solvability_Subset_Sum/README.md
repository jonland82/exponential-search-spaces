# Learned solvability from distance to easy subset-sum structure

Paper VI. **Updated HTML/PDF paper: prediction, paid prioritization, and
Stage 10 certified branch-pruning results.** The six-note website links the paper
and its supporting evidence.
The original feasibility pilot and model-development results remain preserved.

The recent classifier follow-ups are grouped under [experiments/](experiments/README.md):
[Stage 12 geometry](experiments/12_geometry/README.md) and
[Stage 13 feature pruning](experiments/13_feature_pruning/README.md), each with
code, tests, protocol and findings together. Shared modules now live in `code/`; the compatibility entry points resolve
original frozen names for downstream studies.

**Stage 13 complete: training-only feature pruning.** A separate October 28 experiment
selects nested top-five/top-ten subsets from the 27 candidates using recursive
elimination on development training lists only. It freezes calibrated logistic
models before another 144 fresh base lists / 1,152 paired-encoding cases.
See the [protocol](experiments/13_feature_pruning/PROTOCOL.md), [saved guide](results/pruning_20261028/README.md),
[prediction report](results/pruning_20261028/PREDICTION_REPORT.md),
[paid solver report](results/pruning_20261028/PRIORITY_REPORT.md) and
[findings](experiments/13_feature_pruning/FINDINGS.md). Original models and all earlier evidence are preserved.
Top five improves the unscaled Brier point estimate (0.06808 versus baseline
0.07414), with uncertainty spanning zero; top ten worsens it. Neither model
establishes better paid solving. All 50 tests and the independent 576-pool audit pass.

**Stage 12 complete: prototype geometry and structural interactions.** A separate
October 28 experiment reruns calibrated logistic regression with 15 baseline,
17 prototype, 25 interaction and 27 combined features. It uses training-only
geometry, out-of-list training prototypes, and 144 fresh base lists / 1,152
paired-encoding cases. See the [protocol](experiments/12_geometry/PROTOCOL.md),
[experiment guide](results/geometric_20261028/README.md),
[prediction report](results/geometric_20261028/PREDICTION_REPORT.md),
[paid solver report](results/geometric_20261028/PRIORITY_REPORT.md) and
[findings](experiments/12_geometry/FINDINGS.md). This tests whole-input completion prediction
and paid prioritization; it does not rerun the branch-checking experiment or
replace the default model. Earlier frozen evidence and the manuscript are preserved.
The combined features do not improve the primary Brier endpoint (0.08576 versus
0.08220); small live-time differences coexist with worse work-counter outcomes.
All 43 tests and the independent 1,152-case / 576-pool audit pass.

**Stage 11 complete: proximity to observed easy/hard inputs.** A separate model freeze
tests empirical neighbor distances in the original 15-feature space on another
144 base lists / 1,152 paired-encoding cases. Related targets never serve as
their own training neighbors. See the [protocol](docs/NEIGHBOR_PROTOCOL.md),
[prediction report](results/neighbors_20261025/PREDICTION_REPORT.md),
[paid solver report](results/neighbors_20261025/PRIORITY_REPORT.md) and
[findings](docs/NEIGHBOR_FINDINGS.md). These follow-up results are separate from the
current manuscript and preserve all earlier frozen evidence. Adding both
distances catches more hard inputs but does not improve overall prediction or
paid solver completions; the original model remains the default.

**Stage 10 follow-up complete:** certified structural checks resolve search
subtrees, but the transferred combined model does not beat a simple distance
rule. At 50 ms, median completions were 152/216 for DFS, 159 for the combined
gate and 162 for the rule. See [branch findings and discussion point](docs/BRANCH_FINDINGS.md),
[protocol](docs/BRANCH_PROTOCOL.md), [soundness](docs/BRANCH_THEORY.md) and
[saved report](results/branch_pruning_20261025/REPORT.md). This new exploratory
batch leaves the original frozen study intact; its results are now included as
a separate exploratory section in the paper.

- [Paper VI guide and current status](../notes/06-learned-solvability/README.md).
- [Read Paper VI in HTML](../notes/06-learned-solvability/Predicting_Subset_Sum_Completion.html).
- [Feature definitions, proofs, exact queries, and limits](docs/THEORY.md).
- [Findings and decisions for discussion](docs/FINDINGS.md).
- [Pilot report](results/pilot_20261025/REPORT.md).
- [Full summary](results/pilot_20261025/summary.json).
- [Stage 6 findings and recommendations](docs/DEVELOPMENT_FINDINGS.md).
- [Progression and target-aware theory](docs/ADVANCED_THEORY.md).
- [Development model comparison](results/development_20261025/ml/REPORT.md).
- [End-to-end completion prediction](results/development_20261025/end_to_end/REPORT.md).
- [Frozen-study findings and manuscript recommendation](docs/PROSPECTIVE_FINDINGS.md).
- [Frozen study protocol](docs/PROSPECTIVE_PROTOCOL.md).
- [Fresh prediction report](results/prospective_20261025/PREDICTION_REPORT.md).
- [Paid practical prioritization report](results/prospective_20261025/PRIORITY_REPORT.md).
- [Standalone study overview](results/prospective_20261025/figures/overview.pdf).
- [Interactive 3D input space with prediction and mistake overlays](visualizations/input_space_20261025/input_space.html), [static plot](visualizations/input_space_20261025/input_space.png) and [label/projection notes](visualizations/input_space_20261025/README.md).
- [Paper VI PDF](../notes/06-learned-solvability/Predicting_Subset_Sum_Completion.pdf).
- [LaTeX manuscript](../notes/06-learned-solvability/Predicting_Subset_Sum_Completion.tex).
- [Scoped primary-source audit](docs/LITERATURE.md).
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
python Learned_Solvability_Subset_Sum/experiments/run.py all tests
python Learned_Solvability_Subset_Sum/run.py run_pilot --output Learned_Solvability_Subset_Sum/results/new_pilot
python Learned_Solvability_Subset_Sum/run.py validate_results Learned_Solvability_Subset_Sum/results/pilot_20261025
python Learned_Solvability_Subset_Sum/run.py run_development --output Learned_Solvability_Subset_Sum/results/new_development
python Learned_Solvability_Subset_Sum/run.py fit_development --data Learned_Solvability_Subset_Sum/results/new_development --output Learned_Solvability_Subset_Sum/results/new_development/ml
python Learned_Solvability_Subset_Sum/run.py fit_end_to_end --data Learned_Solvability_Subset_Sum/results/new_development --output Learned_Solvability_Subset_Sum/results/new_development/end_to_end
python Learned_Solvability_Subset_Sum/run.py validate_development Learned_Solvability_Subset_Sum/results/development_20261025
python Learned_Solvability_Subset_Sum/run.py prospective_study freeze --output Learned_Solvability_Subset_Sum/results/new_frozen_study
python Learned_Solvability_Subset_Sum/run.py prospective_study generate --output Learned_Solvability_Subset_Sum/results/new_frozen_study
python Learned_Solvability_Subset_Sum/run.py prospective_study analyze --output Learned_Solvability_Subset_Sum/results/new_frozen_study
python Learned_Solvability_Subset_Sum/run.py priority_experiment --output Learned_Solvability_Subset_Sum/results/new_frozen_study
python Learned_Solvability_Subset_Sum/run.py validate_prospective Learned_Solvability_Subset_Sum/results/prospective_20261025
python Learned_Solvability_Subset_Sum/run.py neighbor_experiment freeze --output Learned_Solvability_Subset_Sum/results/new_neighbor_study
python Learned_Solvability_Subset_Sum/run.py neighbor_experiment generate --output Learned_Solvability_Subset_Sum/results/new_neighbor_study
python Learned_Solvability_Subset_Sum/run.py neighbor_experiment analyze --output Learned_Solvability_Subset_Sum/results/new_neighbor_study
python Learned_Solvability_Subset_Sum/run.py neighbor_experiment priorities --output Learned_Solvability_Subset_Sum/results/new_neighbor_study
python Learned_Solvability_Subset_Sum/run.py validate_neighbors Learned_Solvability_Subset_Sum/results/new_neighbor_study
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
list-bootstrap intervals and subgroup metrics. These historical development
reports precede the paid-priority and branch-guidance experiments described below.

## Frozen evaluation and priorities

`prospective_study.py` freezes fitted models, protected sources and a protocol
before fresh generation. It tests 144 base lists, 288 paired encodings and 1,152
targets, with genuinely new families and n=38 inputs. `priority_experiment.py`
compares seven policies under shared pool budgets, using both fully charged
counter replay and separately measured live deadlines. `validate_prospective.py`
audits all model/data hashes, features, answers, probabilities and policy traces.
`plot_prospective.py` renders the saved results without any new model fitting.

## Paper and publication status

A separate [literature-geometry classifier follow-up](../Structural_Geometry_Subset_Sum/CLASSIFIER_FINDINGS.md)
tests the original 15 inputs plus blind large-base decomposition descriptors
and additive doubling on matched expanded training data. Its protocol, models,
fresh tests and paid comparisons live in the structural-geometry package;
earlier frozen models and the manuscript remain preserved.
The [mathematical overview](../Structural_Geometry_Subset_Sum/experiments/02_literature_classifier/OVERVIEW.md)
connects the literature, all 19 feature definitions and the broader research program.
The subsequent [cost-aware gate study](../Structural_Geometry_Subset_Sum/COST_GATE_FINDINGS.md)
trains on paired check-versus-skip savings and compares paid exact policies.
The [exact geometric-core follow-up](../Structural_Geometry_Subset_Sum/EXCEPTION_FINDINGS.md)
adds a reusable core with exceptional weights and reports fresh costed gains.

The updated manuscript presents definitions, elementary guarantees, matched
prediction comparisons, paid practical policies, certified branch checks and
limits. It cites established
empirical performance modeling, structural knapsack features, calibration,
backdoors and feature-cost accounting. No broad novelty or complexity claim is
made. The costed policy benefit cannot be isolated to the learned five inputs
without an additional matched core-reuse control for that original pool task.
The independent branch experiment supplies matched acquisition/common-checker
controls for its own task and finds no learned advantage over the distance rule.

`python build_papers.py --paper 6` verifies saved evidence and generates tables,
values, a paper-sized plot, the PDF and HTML without rerunning experiments.
The six-note site includes this paper, its methods and its preserved evidence.

## Folder guide

- `code/`: shared features, solvers, training, validation and plotting scripts.
- `tests/`: original shared test suites.
- `docs/`: theory, literature, protocols and earlier findings.
- `experiments/`: grouped geometry/pruning follow-ups and the full test/audit launcher.
- `results/` and `visualizations/`: preserved measured evidence and figures.

Run an older script through the package entry point, for example:

```powershell
python Learned_Solvability_Subset_Sum/run.py run_pilot --help
python Learned_Solvability_Subset_Sum/experiments/run.py all tests
```

The small root `advanced_features.py` and `__init__.py` files preserve existing
imports. Original source bytes are loaded from the locations in
[the layout map](experiments/LAYOUT.json).
