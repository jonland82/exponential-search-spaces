# October 28 geometric-feature logistic experiment

Separate Paper VI follow-up; original studies and models remain preserved.

- [Protocol](../../GEOMETRIC_PROTOCOL.md): fixed features, fitting, isolation and cost accounting.
- [Findings](../../GEOMETRIC_FINDINGS.md): results and interpretation.
- [Prediction report](PREDICTION_REPORT.md): fresh probability/accuracy comparison.
- [Paid priority report](PRIORITY_REPORT.md): counter and live-time solver outcomes.
- [Validation audit](VALIDATION.json): geometry/refits, independent truths, predictions and counter replays.
- [Audit correction note](AUDIT_NOTE.md): a repaired audit-only variable name; frozen sources/results are preserved.
- [Feature schema](feature_schema.json): ordered feature names for every arm.
- [Frozen protocol manifest](protocol.json): source/input/model hashes, split IDs and exclusion set.

Models have 15 original inputs, 17 inputs with two prototype distances, 25 inputs
with ten structural products, or all 27 inputs. Three weighted KMeans centroids
per completion class are fitted offline in training-standardized 15D space.
Distances are to the nearest centroid of each class. Training prototypes exclude
the query's entire weight list. Ten products cover every distinct pair of the
first five standardized structural coordinates. No density/PCA feature is added.

`training_features.jsonl` stores out-of-list fitting designs; `models.joblib`
stores frozen geometry, models and sigmoid calibration. `cases.jsonl`,
`lists.jsonl`, `references.jsonl` and `proposals.jsonl` retain fresh inputs,
independent reachability truth, reference labels and duplicate-rejection logs.
`predictions.jsonl` stores raw added features and all probabilities.
`prediction_metrics.json` retains subgroup metrics, bootstrap intervals and
confusion matrices. `priority_runs.jsonl` stores all paid pool traces and
`priority_summary.json` aggregates by cohort. `sources/` preserves source bytes.

To reproduce, use a **new** output directory. The saved experiment must not be
overwritten. Running a new freeze excludes all prior list datasets present at
that time, so it intentionally creates a different fresh sample. Live timing
will vary by machine; the existing deterministic counter traces are replayable.

```powershell
python -m unittest discover -s Learned_Solvability_Subset_Sum -p "test_*.py" -v
python Learned_Solvability_Subset_Sum/geometric_experiment.py freeze --output Learned_Solvability_Subset_Sum/results/new_geometric
python Learned_Solvability_Subset_Sum/geometric_experiment.py generate --output Learned_Solvability_Subset_Sum/results/new_geometric
python Learned_Solvability_Subset_Sum/geometric_experiment.py analyze --output Learned_Solvability_Subset_Sum/results/new_geometric
python Learned_Solvability_Subset_Sum/geometric_experiment.py priorities --output Learned_Solvability_Subset_Sum/results/new_geometric
python Learned_Solvability_Subset_Sum/audit_geometric.py Learned_Solvability_Subset_Sum/results/new_geometric
```

Read-only validation of this saved experiment:

```powershell
python Learned_Solvability_Subset_Sum/audit_geometric.py Learned_Solvability_Subset_Sum/results/geometric_20261028
```

This is a whole-input prioritization experiment. Its distance-rule control ranks
by 2^(-minimum structural distance), whereas the earlier branch experiment used
a distance<=2 gate. These results cannot replace that separate branch comparison.
