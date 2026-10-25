# Paid neighbor-guided prioritization

Same features, core queries, fallback solvers and deadlines in every learned arm. Neighbor lookup is executed inside live inference and fully charged in the declared counter model. No predicted label prunes a case.

Totals below sum separately budgeted cohort completions within each repetition, then report the median and range over three repetitions. Scaled copies and timing repetitions are not independent problems.

| Mode | Budget fraction | Policy | Total median [range] | Planning exhaustions / 24 cohort-runs |
|---|---:|---|---:|---:|
| work | 0.2 | arrival | 566 [562, 585] | 0 / 24 |
| work | 0.2 | distance_rule | 409 [406, 415] | 24 / 24 |
| work | 0.2 | baseline | 399 [398, 405] | 24 / 24 |
| work | 0.2 | hard | 399 [398, 405] | 24 / 24 |
| work | 0.2 | both | 399 [398, 405] | 24 / 24 |
| work | 0.2 | distances | 399 [398, 405] | 24 / 24 |
| work | 0.2 | knn | 399 [398, 405] | 24 / 24 |
| work | 0.5 | arrival | 875 [873, 878] | 0 / 24 |
| work | 0.5 | distance_rule | 763 [763, 763] | 0 / 24 |
| work | 0.5 | baseline | 729 [729, 729] | 3 / 24 |
| work | 0.5 | hard | 468 [468, 468] | 24 / 24 |
| work | 0.5 | both | 468 [468, 468] | 24 / 24 |
| work | 0.5 | distances | 468 [468, 468] | 24 / 24 |
| work | 0.5 | knn | 474 [474, 474] | 21 / 24 |
| time | 0.2 | arrival | 690 [689, 697] | 0 / 24 |
| time | 0.2 | distance_rule | 819 [818, 821] | 0 / 24 |
| time | 0.2 | baseline | 854 [852, 854] | 0 / 24 |
| time | 0.2 | hard | 849 [849, 850] | 0 / 24 |
| time | 0.2 | both | 837 [837, 838] | 0 / 24 |
| time | 0.2 | distances | 853 [851, 853] | 0 / 24 |
| time | 0.2 | knn | 843 [839, 844] | 0 / 24 |
| time | 0.5 | arrival | 869 [868, 871] | 0 / 24 |
| time | 0.5 | distance_rule | 885 [884, 885] | 0 / 24 |
| time | 0.5 | baseline | 887 [887, 887] | 0 / 24 |
| time | 0.5 | hard | 888 [886, 889] | 0 / 24 |
| time | 0.5 | both | 887 [885, 888] | 0 / 24 |
| time | 0.5 | distances | 888 [886, 890] | 0 / 24 |
| time | 0.5 | knn | 885 [883, 888] | 0 / 24 |

Complete per-cohort summaries are in priority_summary.json; per-run phase costs, attempts, deadline flags and completion IDs are in priority_runs.jsonl. Work units are declared heterogeneous counters, not uniform CPU/bit operations. Live times are machine-specific cooperative deadlines and exclude late answers. Training and model loading are offline; every online lookup is included. All learned arms share exact core reuse, so their differences isolate changed prediction/lookup behavior for this pool task. This is prioritization, not branch pruning or a proof of faster asymptotic solving.
