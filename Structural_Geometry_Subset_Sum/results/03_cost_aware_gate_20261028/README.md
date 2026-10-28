# Saved cost-aware gate experiment

October 28, 2026. [Findings](../../COST_GATE_FINDINGS.md),
[Overview](../../experiments/03_cost_aware_gate/README.md),
[protocol](../../experiments/03_cost_aware_gate/PROTOCOL.md),
[report](REPORT.md), [validation](VALIDATION.json).

A separate [post-hoc failure diagnosis](../../FAILURE_FINDINGS.md) analyzes
the unresolved inputs and runs explicitly labeled resource-cap probes.

The new gate predicts whether a bounded root geometric DP repays its cost.
Training uses paired action costs, with sample weights proportional to savings
or waste. Separate calibration lists choose the threshold; the fitted gate is
frozen before fresh test generation. Whole-input completion prediction from
Experiment 02 is not reused as the decision label.

Six policies distinguish matched always/never/simple/learned checking from
lean acquisition and a direct MITM control. Every policy reuses the original
five exact cores. Feature extraction, inference, exact checking and fallback
costs are paid, and only exact algorithms supply answers.

Artifacts include the source/config freeze (`protocol.json`, `sources/`),
development action pairs (`development_pairs.jsonl`), fitted coefficients and
threshold (`gate.json`, `fitted.joblib`, `fit_diagnostics.json`), model freeze,
fresh cases, all deterministic per-case runs (`counter_runs.jsonl`), all paid
pool traces (`pool_runs.jsonl`), summary/report and artifact hash manifests.
`lists.jsonl` contains all new lists for future duplicate exclusion.

From the repository root, recheck the saved study without replacing its files:

```powershell
python -m Structural_Geometry_Subset_Sum.cost_gate_audit --output Structural_Geometry_Subset_Sum/results/03_cost_aware_gate_20261028
```

The auditor repeats independent truths, paired labels, fitting, threshold
selection and deterministic policies/pools. It checks saved live traces rather
than regenerating machine timings, and preserves an existing successful audit.

To run a new frozen sample, use a new output directory:

```powershell
python -m Structural_Geometry_Subset_Sum.cost_gate_study all --output Structural_Geometry_Subset_Sum/results/03_cost_aware_gate_new_run
python -m Structural_Geometry_Subset_Sum.cost_gate_audit --output Structural_Geometry_Subset_Sum/results/03_cost_aware_gate_new_run
```

Individual stages are `freeze`, `development`, `fit`, `test`, `evaluate`.
New runs exclude this sample and generate new inputs. Requires the same NumPy,
scikit-learn, joblib and threadpoolctl dependencies as the preceding classifier
experiment. Live time and heterogeneous work counters are separate endpoints.
