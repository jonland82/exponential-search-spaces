# Paid feature-pruned logistic prioritization

All online feature, prototype-distance, interaction, inference, sorting, exact-core reuse, solver and witness costs are charged. These whole-input pools are not the earlier branch-checking experiment. Totals sum independently budgeted cohorts per repeat, then take the median and range of three repeats.

| Mode | Budget fraction | Policy | Median completions [range] | Planning exhaustions / runs |
|---|---:|---|---:|---:|
| work | 0.2 | arrival | 540 [519, 544] | 0 / 24 |
| work | 0.2 | distance_rule | 376 [375, 380] | 24 / 24 |
| work | 0.2 | baseline | 370 [369, 371] | 24 / 24 |
| work | 0.2 | combined | 370 [369, 371] | 24 / 24 |
| work | 0.2 | top10 | 370 [369, 371] | 24 / 24 |
| work | 0.2 | top5 | 370 [369, 371] | 24 / 24 |
| work | 0.5 | arrival | 858 [853, 858] | 0 / 24 |
| work | 0.5 | distance_rule | 730 [730, 730] | 0 / 24 |
| work | 0.5 | baseline | 675 [673, 675] | 9 / 24 |
| work | 0.5 | combined | 653 [651, 653] | 9 / 24 |
| work | 0.5 | top10 | 655 [653, 655] | 9 / 24 |
| work | 0.5 | top5 | 659 [657, 659] | 9 / 24 |
| time | 0.2 | arrival | 657 [648, 657] | 0 / 24 |
| time | 0.2 | distance_rule | 810 [802, 815] | 0 / 24 |
| time | 0.2 | baseline | 838 [830, 838] | 0 / 24 |
| time | 0.2 | combined | 828 [824, 831] | 0 / 24 |
| time | 0.2 | top10 | 829 [825, 831] | 0 / 24 |
| time | 0.2 | top5 | 831 [829, 833] | 0 / 24 |
| time | 0.5 | arrival | 853 [849, 855] | 0 / 24 |
| time | 0.5 | distance_rule | 874 [874, 876] | 0 / 24 |
| time | 0.5 | baseline | 876 [868, 876] | 0 / 24 |
| time | 0.5 | combined | 874 [874, 877] | 0 / 24 |
| time | 0.5 | top10 | 874 [872, 876] | 0 / 24 |
| time | 0.5 | top5 | 877 [872, 877] | 0 / 24 |

Work units are heterogeneous declared counters, not CPU/bit operations. Time results include cooperative deadlines and exclude late answers. Timing ranges are descriptive; repeats and scaled encodings are dependent. Offline training/model loading is excluded. No prediction certifies NO. Per-cohort metrics and full phase/attempt traces are preserved; do not infer general speedups from an isolated timing difference.
