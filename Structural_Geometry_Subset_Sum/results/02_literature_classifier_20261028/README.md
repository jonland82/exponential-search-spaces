# Saved Experiment 02: literature geometry in logistic regression

Completed October 28, 2026.
[Mathematical overview](../../experiments/02_literature_classifier/OVERVIEW.md),
[Findings](../../CLASSIFIER_FINDINGS.md),
[protocol](../../experiments/02_literature_classifier/PROTOCOL.md),
[report](REPORT.md), [validation](VALIDATION.json).

Three calibrated logistic designs (15/18/19 inputs), identical expanded training
and calibration lists, fresh test generation after model freeze. Four paid
policies distinguish geometric acquisition/exact certificates from the learned
features. No earlier fitted model, frozen evidence or manuscript was changed.

Key artifacts:

- `protocol.json`, `protocol.sha256`, `sources/`: pre-generation source/config freeze.
- `development_lists.jsonl`, `development_cases.jsonl`: train/calibration inputs and labels.
- `model_freeze.json`, `models.joblib`, `coefficients.json`: frozen models and fits.
- `test_lists.jsonl`, `test_cases.jsonl`, `lists.jsonl`: new test inputs and all exclusion IDs.
- `predictions.jsonl`, `prediction_metrics.json`: primary/subgroup prediction evidence.
- `pool_runs.jsonl`, `pool_summary.json`: 96 paid work/live traces and summaries.
- `*_hashes.json`: artifact manifests; `VALIDATION.json`: successful audit.

From the repository root, verify the saved evidence without overwriting it:

```powershell
python -m Structural_Geometry_Subset_Sum.classifier_audit --output Structural_Geometry_Subset_Sum/results/02_literature_classifier_20261028
```

The audit repeats exact reference/feature calculations, fitting and deterministic
pool runs. It validates saved timing traces; it does not regenerate wall-clock
measurements. It preserves an existing successful validation record.

Run a new frozen experiment in a new directory (never reuse this one):

```powershell
python -m Structural_Geometry_Subset_Sum.classifier_study all --output Structural_Geometry_Subset_Sum/results/02_literature_classifier_new_run
python -m Structural_Geometry_Subset_Sum.classifier_audit --output Structural_Geometry_Subset_Sum/results/02_literature_classifier_new_run
```

Stages can also be called separately: `freeze`, `development`, `fit`, `test`,
`evaluate`, in that order. Future runs exclude this saved sample and use new
inputs. Live timings are machine-dependent and input mixtures are exploratory.
Requires NumPy, scikit-learn, joblib and threadpoolctl, already used by the
existing learned-classifier framework.
