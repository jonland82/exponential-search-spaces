# Deterministic refinement continuation

This folder contains the implementation, proof, regression evidence, and
frozen prospective study for steps 1–3 of the research handoff. The findings
are now integrated into [Paper III](../../notes/03-probability-valued-subset-sum/Probability_Valued_Subset_Sum.html);
the original statistical package, its rerun, and all frozen sources and raw
measurements are preserved. The protected proof note's original publication
status describes the experiment stage, before this integration.

Start with [REPORT.md](REPORT.md) for the findings, [THEOREM.md](THEOREM.md)
for the proof, and [protocol.json](protocol.json) for the predeclared study.
The [publication methods ledger](../../subset-sum/PROBABILITY_REFINEMENT.md)
links the generated tables, chart, and summary used in the revised paper.

Algorithms and verification use Python's standard library. The reporting
script additionally requires Matplotlib. Run commands from this directory:

```powershell
python -m unittest -v test_bounds
python run_study.py regression
python run_study.py freeze
python run_study.py prospective
python report_study.py
```

Prospective evidence is write-once: the runner refuses to overwrite it or
run with modified protected sources. Preserve the original dataset at
`../subset_sum_refinement/results`. Copy this directory without its results
to a new sibling directory to repeat the frozen study.

Certificate algorithms cannot access exact evaluation labels. Histogram
enumeration appears only as an explicitly labeled oracle on the old cohort.
The prospective exact labels are computed after all intervals for each list.
