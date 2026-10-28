# Cost-aware root geometric gate

A new weighted logistic gate learns the sign of net paired censored-work savings, not ordinary solver completion. Training and threshold selection use disjoint original lists; the model is frozen before fresh test generation. Scores are cost-sensitive decision scores, not calibrated reachability probabilities.

Train decisions with nonzero savings: 28, positive 14, negative 14; selected threshold 0.25.

## Fixed 32L per-case work endpoint

| Policy | Completed | Capped cost | Actual work | Eligible decisions | DP checks | DP completions |
|---|---:|---:|---:|---:|---:|---:|
| lean_never | 431 | 16274475 | 15719129 | 0 | 0 | 0 |
| never | 461 | 13417540 | 13072957 | 34 | 0 | 0 |
| always | 461 | 13364119 | 13025492 | 34 | 34 | 32 |
| simple | 461 | 13364119 | 13025492 | 34 | 34 | 32 |
| learned | 461 | 13361360 | 13016844 | 34 | 25 | 25 |
| direct_mitm | 434 | 15129245 | 11385152 | 0 | 0 | 0 |

Unresolved cases contribute their full prescribed budget to capped cost; actual work is reported separately. All policies share exact target reductions, original five-core reuse, and a bitset/DFS/MITM fallback with remaining work/time split among remaining methods. direct_mitm instead spends its fallback allowance on MITM. lean_never and direct_mitm omit geometric discovery. Matched never/always/simple/learned pay the same 19-feature acquisition at eligible decisions and share exact aggregate-gap answers. The learned policy also pays inference; caps always return unresolved, never an unsupported NO.

## Paid pools

Median exact completions over three paired arrival orders. Both work and live pools include all online phases. Live feature extraction and exact solving are recomputed under real deadlines; late answers are excluded. Work reuses complete deterministic traces only when the complete per-case allowance remains, and reruns any clipped solve.

| Mode | Cohort | Fraction | Lean never | Matched never | Always | Simple | Learned | Direct MITM |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| time | large_base | 0.2 | 15.0 | 72.0 | 79.0 | 80.0 | 75.0 | 22.0 |
| time | large_base | 0.5 | 34.0 | 118.0 | 121.0 | 121.0 | 120.0 | 56.0 |
| time | legacy_families | 0.2 | 176.0 | 176.0 | 175.0 | 179.0 | 179.0 | 160.0 |
| time | legacy_families | 0.5 | 313.0 | 314.0 | 315.0 | 314.0 | 314.0 | 304.0 |
| work | large_base | 0.2 | 27.0 | 68.0 | 68.0 | 68.0 | 68.0 | 49.0 |
| work | large_base | 0.5 | 67.0 | 128.0 | 128.0 | 128.0 | 128.0 | 114.0 |
| work | legacy_families | 0.2 | 162.0 | 145.0 | 146.0 | 146.0 | 146.0 | 195.0 |
| work | legacy_families | 0.5 | 334.0 | 333.0 | 333.0 | 333.0 | 333.0 | 320.0 |

Primary learned-minus-simple repeat-average completion difference at 50% work pools: +0.00.

This is a root-only gate for an already discovered eligible geometric DP, not a repeated internal branch gate or a gate avoiding discovery itself. It transfers a work-trained policy to live time only as a secondary test. Capped work is a censored training objective, not an uncensored runtime claim; heterogeneous counters do not measure uniform bit operations. Pooled completion repeats use the same sample, so no independent-repetition significance claim is made. Per-case paired whole-list bootstrap intervals are saved for separate completion/capped-cost endpoints. Constructed families, fixed small sizes and schedule limit generalization. No default model or manuscript is changed.
