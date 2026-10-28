# Paid geometric-feature prioritization

All online feature, prototype-distance, interaction, inference, sorting, exact-core reuse, solver and witness costs are charged. These whole-input pools are not the earlier branch-checking experiment. Totals sum independently budgeted cohorts per repeat, then take the median and range of three repeats.

| Mode | Budget fraction | Policy | Median completions [range] | Planning exhaustions / runs |
|---|---:|---|---:|---:|
| work | 0.2 | arrival | 551 [545, 560] | 0 / 24 |
| work | 0.2 | distance_rule | 396 [392, 396] | 24 / 24 |
| work | 0.2 | baseline | 384 [384, 386] | 24 / 24 |
| work | 0.2 | prototypes | 384 [384, 386] | 24 / 24 |
| work | 0.2 | interactions | 384 [384, 386] | 24 / 24 |
| work | 0.2 | combined | 384 [384, 386] | 24 / 24 |
| work | 0.5 | arrival | 848 [845, 851] | 0 / 24 |
| work | 0.5 | distance_rule | 750 [750, 751] | 0 / 24 |
| work | 0.5 | baseline | 687 [685, 687] | 6 / 24 |
| work | 0.5 | prototypes | 655 [653, 655] | 9 / 24 |
| work | 0.5 | interactions | 683 [681, 683] | 6 / 24 |
| work | 0.5 | combined | 649 [647, 649] | 12 / 24 |
| time | 0.2 | arrival | 657 [654, 662] | 0 / 24 |
| time | 0.2 | distance_rule | 790 [785, 792] | 0 / 24 |
| time | 0.2 | baseline | 813 [810, 819] | 0 / 24 |
| time | 0.2 | prototypes | 809 [804, 810] | 0 / 24 |
| time | 0.2 | interactions | 808 [807, 812] | 0 / 24 |
| time | 0.2 | combined | 813 [811, 818] | 0 / 24 |
| time | 0.5 | arrival | 838 [826, 843] | 0 / 24 |
| time | 0.5 | distance_rule | 860 [857, 866] | 0 / 24 |
| time | 0.5 | baseline | 860 [857, 866] | 0 / 24 |
| time | 0.5 | prototypes | 865 [862, 867] | 0 / 24 |
| time | 0.5 | interactions | 859 [852, 863] | 0 / 24 |
| time | 0.5 | combined | 862 [859, 865] | 0 / 24 |

Work units are heterogeneous declared counters, not CPU/bit operations. Time results include cooperative deadlines and exclude late answers. Timing ranges are descriptive; repeats and scaled encodings are dependent. Offline training/model loading is excluded. No prediction certifies NO. Per-cohort metrics and full phase/attempt traces are preserved; do not infer general speedups from an isolated timing difference.
