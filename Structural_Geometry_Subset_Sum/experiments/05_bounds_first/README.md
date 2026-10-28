# Bounds-first geometric core experiment

Experiment 04 found that most core NO calls never queried a table, while
unsuccessful discovery caused three regressions. This follow-up tests cheaper
partition discovery and delayed table construction separately.

- [Frozen protocol](PROTOCOL.md): controls, costs and fresh-sample endpoints.
- [Mathematics](THEORY.md): exact necessary bounds and the saved construction cost.
- [Findings](../../BOUNDS_FINDINGS.md).
- [Saved evidence and reproduction](../../results/05_bounds_first_20261028/README.md).

Four substantive versions are compared: root, previous reuse, bounds-only,
and bounds-first with reuse. A fifth matched eager-construction control isolates
the effect of delaying construction from the effect of faster discovery.

No ML is fitted. This develops the research program's exact structural routes:
make the cost of discovering and certifying a tractable core smaller than the
search it replaces, while retaining exact fallback and honest unresolved results.

```powershell
python -m Structural_Geometry_Subset_Sum.bounds_study all --output Structural_Geometry_Subset_Sum/results/05_bounds_first_20261028
python -m Structural_Geometry_Subset_Sum.bounds_audit --output Structural_Geometry_Subset_Sum/results/05_bounds_first_20261028
```

Each new run needs a fresh directory. Source/configuration are frozen before
generation. Results from old failure cases are labeled retrospective.
