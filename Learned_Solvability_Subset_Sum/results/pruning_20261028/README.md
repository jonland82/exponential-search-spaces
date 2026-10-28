# October 28 top-five / top-ten feature-pruning experiment

Separate follow-up to the 27-feature geometric study. All prior experiments,
models, source snapshots, plots and manuscript artifacts remain preserved.

- [Fixed protocol](../../PRUNING_PROTOCOL.md): selection, isolation and paid accounting.
- [Findings](../../PRUNING_FINDINGS.md): interpretation and evidence limits.
- [Selection trace](selection.json): all elimination coefficients, rankings, names and dependencies.
- [Feature schema](feature_schema.json): ordered inputs to each model.
- [Prediction report](PREDICTION_REPORT.md): fresh probability/accuracy comparisons.
- [Paid priority report](PRIORITY_REPORT.md): counter and live solver outcomes.
- [Validation](VALIDATION.json): ranking/refits, exact truths and trace replays.
- [Frozen manifest](protocol.json): source/input/model hashes and split/exclusion IDs.

RFE repeatedly fits standardized logistic regression and removes its smallest
absolute coefficient, saving nested subsets at 10 and 5 remaining inputs.
Only the original 84 development training lists / 336 targets participate in
selection. The 42 disjoint calibration lists fit sigmoid calibration only.
No calibration, old-test or fresh-test labels choose features or settings.

The top-five model keeps target fraction, complement-minimum target fraction,
distance to unresolved prototypes, superincreasing-times-coverage and
coverage-times-few-values products of standardized structural distances.
Top ten additionally keeps distance to completed prototypes, weight coefficient
of variation, few-values distance, coverage distance and log2(minimum weight+1).
Both models depend on all 15 original measurements because of their prototype
distances. All learned policies pay the same original acquisition/core-reuse
costs; only retained online transformations and smaller classifier costs differ.

`models.joblib` contains both selected models and the exact unmodified prior
15-input and full-27 controls. `training_features.jsonl` preserves selected
out-of-list training designs. Raw fresh lists/cases/oracle truths/reference labels,
probabilities, bootstrap comparisons, phase costs, attempts and deadlines are in
the JSON/JSONL artifacts. `sources/` contains the pre-generation source snapshots.

To repeat, use a **new** output directory. A new freeze excludes all prior lists
present then and intentionally generates another sample. Time measurements vary
by machine; saved deterministic counter traces can be replayed.

```powershell
python -m unittest discover -s Learned_Solvability_Subset_Sum -p "test_*.py" -v
python Learned_Solvability_Subset_Sum/pruning_experiment.py freeze --output Learned_Solvability_Subset_Sum/results/new_pruning
python Learned_Solvability_Subset_Sum/pruning_experiment.py generate --output Learned_Solvability_Subset_Sum/results/new_pruning
python Learned_Solvability_Subset_Sum/pruning_experiment.py analyze --output Learned_Solvability_Subset_Sum/results/new_pruning
python Learned_Solvability_Subset_Sum/pruning_experiment.py priorities --output Learned_Solvability_Subset_Sum/results/new_pruning
python Learned_Solvability_Subset_Sum/audit_pruning.py Learned_Solvability_Subset_Sum/results/new_pruning
```

Validate this saved experiment:

```powershell
python Learned_Solvability_Subset_Sum/audit_pruning.py Learned_Solvability_Subset_Sum/results/pruning_20261028
```

The new batch is separate from both the earlier geometric sample and the
distance<=2 branch-checking experiment. Outcomes concern this fixed portfolio's
finite-budget completion, not reachability or intrinsic mathematical hardness.
