# Structural geometry of subset sum

A literature-guided research direction extending the certified-coverage framework of Papers
I-VI. Use established tractable structures and solver-specific obstructions to
discover exact solving routes whose benefits exceed acquisition/checking costs.
Earlier packages, frozen studies, models, plots and manuscripts are preserved.

The [Note VII working draft](../notes/07-geometric-cores/README.md) gives the exact
core-and-exceptions algorithm, correctness proofs and both fresh studies.
Its [three-page runtime companion](../notes/07-geometric-cores/Runtime_of_Geometric_Core_Subset_Sum.html)
derives bit-cost and memory bounds and compares general algorithms.

## Current result

Core reuse improves work-capped completions from 453 to 469 of 576 fresh targets
over matched root geometry (Study 04 primary net +16, whole-list-bootstrap 95%
interval approximately [4,30]). Study 05 finds 954 bounds-first versus 916 root
completions on 1,152 fresh targets, a secondary comparison. Its primary refinement
comparison is only 954 versus 953 previous-reuse completions, interval [0,3].
The refinement avoids 90 of 182 table builds and lowers capped work by 1.74%;
incremental completion and wall-clock gains remain unestablished. Earlier ML
feature and gating studies are separate comparisons, not the source of this
exact-route gain. There is no new general worst-case bound.

## Studies and evidence

- [Literature map](LITERATURE.md): guarantees and limits, with primary sources.
- [Theory](THEORY.md): exact aggregate geometry, signed DP, witnesses and costs.
- [First protocol](experiments/01_large_base/PROTOCOL.md): fixed methods and fresh inputs.
- [First experiment findings](FINDINGS.md).
- [Saved first experiment](results/01_large_base_20261028/README.md).
- [Classifier experiment protocol](experiments/02_literature_classifier/PROTOCOL.md):
  compare the original 15 inputs with decomposition geometry and additive doubling.
- [Classifier mathematical overview](experiments/02_literature_classifier/OVERVIEW.md):
  literature comparisons, all feature definitions and the research-program connection.
- [Classifier findings](CLASSIFIER_FINDINGS.md) and
  [saved classifier experiment](results/02_literature_classifier_20261028/README.md).
- [Cost-aware gate experiment](experiments/03_cost_aware_gate/README.md):
  learn whether an eligible geometric DP repays its cost, with matched controls.
- [Cost-aware gate findings](COST_GATE_FINDINGS.md) and
  [saved gate experiment](results/03_cost_aware_gate_20261028/README.md).
- [Failure diagnosis](FAILURE_FINDINGS.md): which inputs remain unresolved,
  resource limits, and a proposed geometric core with a few exceptions.
- [Reusable geometric-core experiment](experiments/04_exception_core/README.md):
  build one exact core and query every bounded exceptional assignment.
- [Exception-core findings](EXCEPTION_FINDINGS.md) and
  [saved exception-core experiment](results/04_exception_core_20261028/README.md).
- [Bounds-first experiment](experiments/05_bounds_first/README.md):
  test cheaper discovery and necessary bounds before building exact tables.
- [Bounds-first findings](BOUNDS_FINDINGS.md) and
  [saved bounds-first experiment](results/05_bounds_first_20261028/README.md).

The original large-base study is complete and validated. Root checks increase completions
against the declared shared portfolio. A separately labeled post-hoc live/work
sensitivity gives 284/324 root completions versus 219 for portfolio; repeated
checks finish 270. This reused sample does not establish superiority over a
tuned portfolio or matched reuse of all five existing core types. See findings
for the original schedule limitation, full counts and uncertainty.

## First experiment

Discover w=M*p+r without receiving a planted base. Project binary selections
into q=sum(p_i*x_i), s=sum(r_i*x_i); exact solutions satisfy M*q+s=t. Bounds on
s can rule out every integer q, or permit bounded exact two-coordinate DP.
Compare the shared exact portfolio, root detection without reuse, root exact
checks, and selective internal checks. Discovery, verification, fallback solving
and witness checking are charged. No ML is fitted in this first experiment.

This is an implementation of an established structural idea, not a claim of a
new worst-case bound or proof that every generated large-base instance is hard.
The literature's ordinary-branching lower bounds are not universal hardness
certificates. Our geometric descriptors are neither complete difficulty labels
nor minimum structural distances.

## Layout

```text
structures/large_base.py          bounded detector and exact checks
budget.py                        shared/local resource limits
solver.py                        common portfolio and DFS checkpoints
study.py                         freeze, generation, measurement and reporting
audit.py                         independent truth/event checks and replay
visualize.py                     diagnostic aggregate-coordinate plot
experiments/01_large_base/        protocol and command entry points
classifier_features.py           literature-derived inputs to the classifier
classifier_study.py              matched 15/18/19-input experiment
cost_gate.py                     root decisions with paid exact fallback
cost_gate_study.py               paired cost labels, fitting and paid pools
experiments/03_cost_aware_gate/   cost-aware gate protocol and overview
structures/exception_core.py     exact reusable table and exceptional queries
structures/bounds_core.py        incremental discovery and lazy exact construction
exception_solver.py             matched root/exception portfolios
exception_study.py              fresh evidence and retrospective repair checks
experiments/04_exception_core/   protocol, overview and exactness argument
bounds_solver.py                bounded discovery and bounds-first portfolios
bounds_study.py                 fresh five-policy mechanism comparison
experiments/05_bounds_first/     bounds-first protocol and mathematics
tests/                           exactness, reconstruction and accounting
results/01_... through 05_.../    separate frozen studies and measured outcomes
```

Requires Python; plotting additionally uses Matplotlib already used elsewhere
in this repository. Solving and numerical tests use the standard library.
The classifier follow-up and its tests also require NumPy, scikit-learn, joblib
and threadpoolctl, as used by the existing learned-classifier package.

```powershell
python -m unittest discover -s Structural_Geometry_Subset_Sum/tests -p "test_*.py" -v
```

New runs require a new output directory. See each saved study's guide for its staged
commands. A new freeze excludes all existing normalized lists and intentionally
creates a new sample; source snapshots and deterministic traces permit replay
of this sample, while wall-clock measurements vary by machine.
