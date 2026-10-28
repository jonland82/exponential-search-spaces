# Frozen bounds-first study

This is Experiment 05: five fixed exact portfolios, 384 fresh weight lists /
1,152 targets, sizes 24/30/36 and sixteen families. The source/configuration
freeze precedes generation, and 2,244 earlier normalized lists are excluded.

- [Protocol](protocol.json) and [source snapshots](sources/Structural_Geometry_Subset_Sum/bounds_study.py).
- [Experimental protocol](../../experiments/05_bounds_first/PROTOCOL.md) and
  [mathematics](../../experiments/05_bounds_first/THEORY.md).
- [Report](REPORT.md), [summary](summary.json) and [independent audit](VALIDATION.json).
- [Findings and limits](../../BOUNDS_FINDINGS.md).

`root` and `reuse` call the unchanged Experiment 04 solver. `bounds_only` and
`bounds_first` use fast capped discovery; `fast_eager` shares that discovery to
isolate the effect of delayed construction. All online work is charged. No ML
is fitted and no generator metadata enters solving. Exact truths are computed
offline by an independent meet-in-the-middle oracle.

The primary comparison is bounds-first minus previous reuse completions with
individual 32L work caps. Report secondary capped-work savings, actual work,
family results, table builds and three randomized live 20ms repeats separately.
The three old regressions are retrospective and excluded from fresh endpoints.

## Verify these saved results

From the repository root, using the existing Python/NumPy/scikit-learn/joblib/
threadpoolctl environment:

```powershell
python -m Structural_Geometry_Subset_Sum.bounds_audit --output Structural_Geometry_Subset_Sum/results/05_bounds_first_20261028
python -m unittest discover -s Structural_Geometry_Subset_Sum/tests -p "test_*.py" -v
```

The auditor checks source/input/artifact hashes, independent exact truths,
partitions, witnesses, complete bounds certificates, resource accounting,
all deterministic replays, live deadlines and report reconstruction. It preserves
an existing successful validation record on repeat runs.

## Generate a new experiment

```powershell
python -m Structural_Geometry_Subset_Sum.bounds_study all --output Structural_Geometry_Subset_Sum/results/05_bounds_first_new_run
python -m Structural_Geometry_Subset_Sum.bounds_audit --output Structural_Geometry_Subset_Sum/results/05_bounds_first_new_run
```

Choose a previously nonexistent directory. A new freeze excludes every current
list, including this run, so this command produces a new sample. Replay of the
saved sample is done by the auditor. Wall-clock results depend on the machine.
Do not overwrite or renormalize these frozen files and their source snapshots.
