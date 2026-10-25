# Experiment rerun ? October 23, 2026

Completed the unchanged frozen experiment in this directory, preserving the original package in `../../subset_sum_refinement`.

Runtime: 55.95 seconds (excluding environment setup and report generation).

| Model | 16-item coverage | Average per-list width removed | 20-item coverage |
|---|---:|---:|---:|
| Structural | 975/1000 (97.50%) | 76.96% | 213/240 (88.75%) |
| Density | 972/1000 (97.20%) | 73.95% | 237/240 (98.75%) |
| Midpoint | 961/1000 (96.10%) | 56.79% | 239/240 (99.58%) |

All built-in checks passed: 30 small brute-force comparisons, 12 independent bitset labels, certified containment for all 2,940 original intervals, no duplicate lists, and width identities for all 3,720 predictions.

All regenerated cohort records, exact labels, and per-list predictions agree with the saved outputs within absolute/relative tolerance 1e-10 after excluding timings. The main summary also agrees within that tolerance.

The density-model top-20% diagnostic differs: floating-point changes of at most 4.22e-15 in fractional shrinkage change selection among effectively tied instances. This changes diagnostic coverage but leaves the main findings unchanged. The experiment and selection code were preserved.

Python is 3.13.5 on Windows; the recorded original used 3.12.14. NumPy 2.3.5, SciPy 1.17.0, and scikit-learn 1.8.0 match the pinned versions. See `environment.txt` for the full rerun dependency list.

Artifacts: `comparison.json`, `compare_results.py`, `subset_sum_refinement/run.log`, and `subset_sum_refinement/Subset_Sum_Refinement_Report.html`. The report generator also produced a ZIP containing the rerun package.

This reruns the statistical experiment. The algebraic follow-up remains a separate continuation task.
