# Stage 13: feature pruning

Select nested top-five/top-ten subsets from the 27 geometry candidates using
training-only recursive elimination, then fit calibrated logistic models and
evaluate prediction and fully paid prioritization on fresh lists.

- [Protocol](PROTOCOL.md) and [findings](FINDINGS.md).
- [Selection/model implementation](code/pruning_models.py),
  [study implementation](code/pruning_experiment.py) and [auditor](code/audit_pruning.py).
- [Tests](tests/test_pruning.py).
- [Saved selection, models, results and reproduction](../../results/pruning_20261028/README.md).
- [Preceding geometric-feature experiment](../12_geometry/README.md).

```powershell
python Learned_Solvability_Subset_Sum/experiments/run.py pruning check
python Learned_Solvability_Subset_Sum/experiments/run.py pruning audit
```

See the [experiment index](../README.md) for tests, new runs and the layout map.
