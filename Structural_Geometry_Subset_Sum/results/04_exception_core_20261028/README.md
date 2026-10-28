# Saved reusable geometric-core experiment

October 28, 2026. [Findings](../../EXCEPTION_FINDINGS.md) ·
[Overview](../../experiments/04_exception_core/README.md) ·
[Protocol](../../experiments/04_exception_core/PROTOCOL.md) ·
[Theory](../../experiments/04_exception_core/THEORY.md) ·
[Report](REPORT.md) · [Validation](VALIDATION.json).

This exact solver builds one signed aggregate/residual table for a retained
core, saves prefix witnesses and reuses it across exceptional assignments.
Discovery receives weights and target only. Fresh data and an explicitly
separate retrospective replay are both saved; no ML is fitted.

Main artifacts: source/config freeze (`protocol.json`, `sources/`), fresh
lists/cases and independent truth, deterministic `counter_runs.jsonl`, three
paired `live_runs.jsonl` repeats, charged FIFO `pool_runs.jsonl`, separate
`retrospective_runs.jsonl`, numerical summary, report and hash manifests.

Recheck the saved experiment from the repository root:

```powershell
python -m Structural_Geometry_Subset_Sum.exception_audit --output Structural_Geometry_Subset_Sum/results/04_exception_core_20261028
```

The auditor repeats independent fresh truths, partition/bounds arithmetic,
all deterministic policies and pools, old-case replays and result summaries.
It checks saved live deadlines rather than rerunning machine timings, and
preserves an existing successful validation record.

For new evidence, use a new directory:

```powershell
python -m Structural_Geometry_Subset_Sum.exception_study all --output Structural_Geometry_Subset_Sum/results/04_exception_core_new_run
python -m Structural_Geometry_Subset_Sum.exception_audit --output Structural_Geometry_Subset_Sum/results/04_exception_core_new_run
```

Stages can be called individually as `freeze`, `generate`, `evaluate`.
A new freeze excludes all prior normalized lists, including this sample, so
future generation differs. Work and separately measured live endpoints have
different accounting; neither establishes a universal speedup. Requires the
same Python, NumPy, scikit-learn, joblib and threadpoolctl environment as the
preceding studies (the exact route fits no ML model).
