# Post-hoc sensitivity: 32L work plus 50ms live deadline

These are the previously inspected inputs, reused for a schedule/resource diagnostic. This was not prespecified as a primary endpoint or a new independent evaluation. The detector, exact checking, native algorithms and thresholds are unchanged. Only the live safety work cap is replaced by the original prespecified deterministic per-case 32L allowance.

| Policy | Median completions [range] | Internal YES/NO | DFS attempts | MITM attempts |
|---|---:|---|---:|---:|
| portfolio | 219 [219, 219] | 0/0 | 648 | 145 |
| detect_only | 219 [219, 220] | 0/0 | 651 | 166 |
| root_geometry | 284 [284, 284] | 0/0 | 252 | 61 |
| selective_geometry | 270 [270, 270] | 36/1089 | 252 | 42 |

Event and attempt counts sum three dependent repeats. All completion counts exclude late answers and pay online work/time. Bootstrap values in summary.json are descriptive conditional reuse, not a new prospective significance claim. This control tests sensitivity to the common portfolio schedule; it is not an optimized modern solver comparison.
