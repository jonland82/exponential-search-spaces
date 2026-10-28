# Paper VI experimental follow-ups

The recent learned-classifier work is grouped by experiment:

| Folder | Question | Evidence |
|---|---|---|
| [12_geometry](12_geometry/README.md) | Add prototype distances and structural interactions to the original 15 features? | [Geometric study](../results/geometric_20261028/README.md) |
| [13_feature_pruning](13_feature_pruning/README.md) | Keep the best five or ten of the 27 candidate features? | [Pruning study](../results/pruning_20261028/README.md) |

Each experiment has its protocol, findings, standalone code and tests together.
Shared models and runners live in `../code/`; original logical imports and
frozen source paths resolve through the package compatibility layer. The existing
`results/` directories retain immutable inputs, serialized models, runs and source
snapshots. The package root contains only the guide, dependencies and small entry
points; earlier theory/findings are in `../docs/` and shared tests in `../tests/`.

## Commands

From the repository root:

```powershell
python Learned_Solvability_Subset_Sum/experiments/run.py all check
python Learned_Solvability_Subset_Sum/experiments/run.py all tests
python Learned_Solvability_Subset_Sum/experiments/run.py geometric audit
python Learned_Solvability_Subset_Sum/experiments/run.py pruning audit
```

`check` verifies saved source/input/artifact hashes. `audit` also refits models,
recomputes independent exact truths, reproduces predictions and replays the paid
work traces. Existing successful validation records are preserved on repeat runs.
`tests` includes the original 50 tests and two additional layout checks.

For a new run, choose an individual experiment and a fresh output directory:

```powershell
python Learned_Solvability_Subset_Sum/experiments/run.py pruning freeze --output Learned_Solvability_Subset_Sum/results/new_pruning
python Learned_Solvability_Subset_Sum/experiments/run.py pruning generate --output Learned_Solvability_Subset_Sum/results/new_pruning
python Learned_Solvability_Subset_Sum/experiments/run.py pruning analyze --output Learned_Solvability_Subset_Sum/results/new_pruning
python Learned_Solvability_Subset_Sum/experiments/run.py pruning priorities --output Learned_Solvability_Subset_Sum/results/new_pruning
python Learned_Solvability_Subset_Sum/experiments/run.py pruning audit --output Learned_Solvability_Subset_Sum/results/new_pruning
```

Substitute `geometric` to run the geometry experiment. New freezes exclude the
list datasets present at that time and intentionally produce another sample.

## Preserved evidence

[LAYOUT.json](LAYOUT.json) maps the old logical filenames to their new locations.
The launcher resolves those names for imports, serialized models and source
verification. Moved Python sources and protocols retain their original bytes;
only navigation documents have updated links. Original datasets, models,
protocol manifests, result hashes and source snapshots remain in place.
New freezes also capture the launcher and layout resolver in their source hashes.
Earlier scripts are available through `python Learned_Solvability_Subset_Sum/run.py SCRIPT [arguments]`.
Use this launcher for the geometry/pruning follow-ups and all shared tests.
