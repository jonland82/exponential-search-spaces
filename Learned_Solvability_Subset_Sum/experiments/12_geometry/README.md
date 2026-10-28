# Stage 12: geometric features

Test the original 15-feature logistic classifier against 17 inputs with
prototype distances, 25 with pairwise structural interactions, and all 27.
Training prototypes exclude the query's entire weight list; all online feature
costs enter the separate paid-prioritization comparison.

- [Protocol](PROTOCOL.md) and [findings](FINDINGS.md).
- [Saved results and reproduction](../../results/geometric_20261028/README.md).
- [Corrected independent auditor](code/audit_geometric.py).
- [Originally frozen validator](code/validate_geometric.py): retained for provenance;
  use the corrected auditor through the launcher, as the [audit note](../../results/geometric_20261028/AUDIT_NOTE.md) explains.
- [Tests](tests/test_geometric.py).
- Shared [model/feature implementation](../../code/geometric_models.py) and
  [study implementation](../../code/geometric_experiment.py).

```powershell
python Learned_Solvability_Subset_Sum/experiments/run.py geometric check
python Learned_Solvability_Subset_Sum/experiments/run.py geometric audit
```

See the [experiment index](../README.md) for tests, new runs and the layout map.
