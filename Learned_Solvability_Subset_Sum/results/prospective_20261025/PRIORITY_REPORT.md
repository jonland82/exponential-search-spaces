# Frozen practical prioritization experiment

Work results are deterministic-counter replays with charged planning phases. Time results are separate live runs, including feature extraction and model inference. Both use shared exact prechecks first; completed answers are independently validated.

Medians over three arrival/timing repetitions. The 0.2/0.5 budgets are fractions of total declared per-instance allowances, not fractions selected from observed runtimes.

| Mode | Cohort | Fraction | Arrival | Random | Short input | Distance rule | Five | Conventional | Combined |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| time | in_distribution | 0.2 | 197 | 197 | 197 | 203 | 203 | 197 | 203 |
| time | in_distribution | 0.5 | 197 | 197 | 197 | 203 | 203 | 197 | 203 |
| time | in_distribution_scaled | 0.2 | 161 | 163 | 186 | 200 | 200 | 196 | 201 |
| time | in_distribution_scaled | 0.5 | 197 | 198 | 197 | 201 | 200 | 198 | 201 |
| time | larger_size | 0.2 | 80 | 78 | 88 | 93 | 93 | 90 | 93 |
| time | larger_size | 0.5 | 90 | 90 | 90 | 93 | 93 | 90 | 93 |
| time | larger_size_scaled | 0.2 | 54 | 63 | 76 | 88 | 91 | 86 | 91 |
| time | larger_size_scaled | 0.5 | 89 | 89 | 89 | 92 | 92 | 89 | 92 |
| time | prior_holdout | 0.2 | 31 | 34 | 42 | 38 | 39 | 47 | 49 |
| time | prior_holdout | 0.5 | 52 | 52 | 52 | 52 | 52 | 52 | 52 |
| time | prior_holdout_scaled | 0.2 | 32 | 29 | 40 | 37 | 37 | 44 | 44 |
| time | prior_holdout_scaled | 0.5 | 46 | 46 | 54 | 53 | 52 | 56 | 55 |
| time | unseen_family | 0.2 | 60 | 63 | 70 | 69 | 70 | 87 | 82 |
| time | unseen_family | 0.5 | 91 | 91 | 91 | 91 | 91 | 91 | 91 |
| time | unseen_family_scaled | 0.2 | 49 | 57 | 63 | 67 | 63 | 78 | 73 |
| time | unseen_family_scaled | 0.5 | 91 | 88 | 85 | 89 | 90 | 93 | 93 |
| work | in_distribution | 0.2 | 122 | 125 | 169 | 84 | 84 | 180 | 81 |
| work | in_distribution | 0.5 | 197 | 197 | 197 | 162 | 158 | 197 | 125 |
| work | in_distribution_scaled | 0.2 | 149 | 144 | 176 | 116 | 116 | 187 | 113 |
| work | in_distribution_scaled | 0.5 | 203 | 203 | 203 | 206 | 206 | 203 | 206 |
| work | larger_size | 0.2 | 62 | 54 | 76 | 43 | 43 | 84 | 42 |
| work | larger_size | 0.5 | 90 | 90 | 90 | 65 | 64 | 90 | 59 |
| work | larger_size_scaled | 0.2 | 56 | 63 | 78 | 54 | 54 | 87 | 53 |
| work | larger_size_scaled | 0.5 | 94 | 94 | 94 | 97 | 97 | 94 | 97 |
| work | prior_holdout | 0.2 | 27 | 27 | 36 | 18 | 18 | 39 | 18 |
| work | prior_holdout | 0.5 | 44 | 45 | 50 | 30 | 29 | 52 | 26 |
| work | prior_holdout_scaled | 0.2 | 34 | 31 | 48 | 18 | 18 | 47 | 18 |
| work | prior_holdout_scaled | 0.5 | 55 | 53 | 63 | 52 | 51 | 62 | 55 |
| work | unseen_family | 0.2 | 46 | 46 | 58 | 24 | 24 | 67 | 24 |
| work | unseen_family | 0.5 | 82 | 80 | 85 | 33 | 33 | 91 | 26 |
| work | unseen_family_scaled | 0.2 | 52 | 60 | 64 | 25 | 25 | 78 | 25 |
| work | unseen_family_scaled | 0.5 | 94 | 93 | 91 | 77 | 73 | 98 | 83 |

Counter replay is not a wall-clock speedup claim. The live deadlines are cooperative: the last feature/query/solver operation may finish after the deadline; late answers are not counted. All overshoots and phase costs are recorded. The timing comparison is machine-specific. Inference uses frozen logistic models; forest predictions belong to the secondary predictive evaluation only.

Arrival order is seed-shuffled; random order uses a separate seed. Repetitions are not independent input samples. No negative prediction removes a case as NO. Only paid exact prechecks, core queries or solvers can complete an instance.
