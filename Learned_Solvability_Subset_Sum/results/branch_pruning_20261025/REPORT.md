# Stage 10: certified branch checks guided by frozen completion scores

Exploratory transfer experiment; no refitting or threshold selection. The original frozen Paper VI study remains unchanged.

72 fresh lists, 216 targets; truths: {'yes': 87, 'no': 129}.

## Live 50 ms budget

Medians of aggregate totals across three repeats. Lower time and node totals alone are not improvements when fewer cases finish. Timing is descriptive.

| Policy | Completed | YES | NO | Total seconds | Nodes | Structural NO checks |
|---|---:|---:|---:|---:|---:|---:|
| dfs | 152 | 53 | 99 | 3.487 | 3.58125e+06 | 0 |
| always_native | 160 | 56 | 104 | 3.275 | 589672 | 3037 |
| distance_native | 162 | 57 | 105 | 3.415 | 1.47518e+06 | 2531 |
| always_matched | 160 | 56 | 104 | 3.280 | 544700 | 2999 |
| distance_matched | 162 | 57 | 105 | 3.462 | 1.38677e+06 | 2527 |
| conventional | 156 | 54 | 102 | 3.554 | 608426 | 3705 |
| hybrid | 159 | 56 | 103 | 3.348 | 549851 | 3033 |

## Deterministic 10,000-node cap

This cap is on visited DFS nodes, not on total computational work. Feature, inference and certificate costs are included in elapsed seconds.

| Policy | Completed | Total seconds | Nodes | Structural NO checks | Feature seconds | Checker seconds |
|---|---:|---:|---:|---:|---:|---:|
| dfs | 146 | 0.792 | 777203 | 0 | 0.000 | 0.000 |
| always_native | 163 | 3.337 | 550988 | 3439 | 2.214 | 0.452 |
| distance_native | 161 | 2.511 | 580067 | 2535 | 1.728 | 0.094 |
| always_matched | 163 | 3.415 | 550988 | 3439 | 2.281 | 0.450 |
| distance_matched | 161 | 2.619 | 580067 | 2535 | 1.807 | 0.097 |
| conventional | 159 | 3.650 | 591329 | 4111 | 2.454 | 0.434 |
| hybrid | 162 | 3.474 | 561063 | 3571 | 2.315 | 0.443 |

## Transfer diagnostic

First eight unresolved checkpoints per unguided deterministic DFS case; these are selected, dependent nodes. The completion model was not trained for this checker or for NO prediction. A high score never permits removal.

| Model | Diagnostic event | Nodes | Accuracy | Precision | Recall |
|---|---|---:|---:|---:|---:|
| hybrid | completion | 1062 | 69.9% | 67.1% | 99.2% |
| hybrid | no | 1062 | 51.7% | 46.5% | 99.8% |
| conventional | completion | 1062 | 66.9% | 65.3% | 97.4% |
| conventional | no | 1062 | 49.4% | 45.3% | 98.0% |

Per-family/size results, all repeat totals, paired common-completion timings, component costs, certificate counts and deadline overshoots are in summary.json. Raw inputs, truths, runs, diagnostics and source hashes are preserved. Certified NO leaf coverage counts assignments, not measured work saved. No asymptotic runtime claim follows.
