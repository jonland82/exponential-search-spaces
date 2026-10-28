# Experiment 01: large-base structural geometry, October 28

Separate research-direction package; no earlier experiment, model or manuscript
is modified. All settings and source bytes were frozen before fresh generation.

- [Protocol](../../experiments/01_large_base/PROTOCOL.md).
- [Theory](../../THEORY.md) and [literature map](../../LITERATURE.md).
- [Measured report](REPORT.md) and [findings](../../FINDINGS.md).
- [Full summary](summary.json).
- [Validation record](VALIDATION.json).
- [Geometric plot](aggregate_geometry.png), [PDF](aggregate_geometry.pdf), [coordinate provenance](geometry_plot.json).
- [Frozen source/input manifest](protocol.json).
- [Post-hoc 32L-plus-live sensitivity](sensitivity_32L_live/REPORT.md): reused inputs, not an independent prospective test.

There are 108 new normalized-distinct lists, 324 targets and four policies:
shared portfolio, root detection without reuse, root geometric checking, and
selective checking inside DFS. Input sizes are 20,28,36; nine families include
large-base instances, outlier variants, near-equal/random controls and known
easy structures. Every target has independent exact reachability truth.

The detector receives only weights and target. It proposes at most 24 bases
from minimum/median distinct weights, powers of two and large consecutive gaps.
For each, w=M*p+r is an exact integer identity. Bounds on the signed residual
sum constrain integer aggregate q values. Empty q ranges certify NO; bounded
two-coordinate bitset DP gives exact decisions and indexed witnesses otherwise.
Caps or deadlines return unresolved, never a learned NO.

`lists.jsonl` preserves generator metadata for audit, which is not supplied to
solvers. `cases.jsonl` has raw inputs, target rules, oracle masks and declared
work caps. `diagnostics.jsonl` stores independent root descriptor acquisition.
`runs.jsonl` preserves 5,184 policy outcomes: 1,296 deterministic work runs and
3,888 live runs with a 50ms allowance each. All online discovery/checking,
fallback solving, logging and witness verification costs are charged.
`memory_profiles.jsonl` has 32 separate Python-allocation profiles. `sources/`
contains the complete pre-generation source snapshot, including reused solvers.
Per-stage manifests protect raw data, runs, profiles, analysis and plot artifacts.

The common portfolio uses Paper V's primitives and an equivalent memoized DFS
with shared-budget accounting in all policies. It includes gcd normalization.
It is an elementary practical baseline, not every best published algorithm.
Inherited bitset YES decisions can lack a witness; all returned indexed witnesses
and all completed decisions are independently checked. Logical DP/history bits
are representation bounds, and Python-traced peaks are not process RSS.

To run another experiment, use a **new** directory. A new freeze excludes prior
normalized lists present at that time, intentionally producing another sample.
These commands must run sequentially; avoid concurrent CPU-heavy jobs during
live timing. Frozen settings are not retuned on saved outcomes.

```powershell
python -m unittest discover -s Structural_Geometry_Subset_Sum/tests -p "test_*.py" -v
python Structural_Geometry_Subset_Sum/experiments/01_large_base/run.py freeze --output Structural_Geometry_Subset_Sum/results/new_large_base
python Structural_Geometry_Subset_Sum/experiments/01_large_base/run.py generate --output Structural_Geometry_Subset_Sum/results/new_large_base
python Structural_Geometry_Subset_Sum/experiments/01_large_base/run.py run --output Structural_Geometry_Subset_Sum/results/new_large_base
python Structural_Geometry_Subset_Sum/experiments/01_large_base/run.py memory --output Structural_Geometry_Subset_Sum/results/new_large_base
python Structural_Geometry_Subset_Sum/experiments/01_large_base/run.py analyze --output Structural_Geometry_Subset_Sum/results/new_large_base
python Structural_Geometry_Subset_Sum/experiments/01_large_base/run.py plot --output Structural_Geometry_Subset_Sum/results/new_large_base
python Structural_Geometry_Subset_Sum/experiments/01_large_base/validate.py Structural_Geometry_Subset_Sum/results/new_large_base
```

Replay/audit this saved experiment:

```powershell
python -m Structural_Geometry_Subset_Sum.verify_saved --output Structural_Geometry_Subset_Sum/results/01_large_base_20261028 --sensitivity
```

Timing and overshoot are machine-specific cooperative measurements. Target rules,
families and memory caps define this constructed study, not an arbitrary subset-
sum distribution or a proof of universal instance hardness.

The original audit entry point registers a new exclusive VALIDATION.json after
all checks pass. The repeat-audit wrapper runs every check and preserves an
existing final record, so repeated verification does not alter its timestamp/hash.
The sensitivity source and its pre-timing manifest are stored separately under
`sensitivity_32L_live/`; the primary source snapshot and results are unchanged.
