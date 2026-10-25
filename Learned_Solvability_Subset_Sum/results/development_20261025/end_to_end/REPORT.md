# End-to-end completion prediction

exploratory end-to-end development prediction; not final evaluation.

Each task's labels include that feature pipeline's extraction and certificate reuse costs under 8L. Predictors are compared against the same labels within each row. Cross-row scores refer to different label distributions.

Calibrated forest Brier scores; lower is better.

| Cost/reuse task | Evaluation | Constant | Five | Conventional | Hybrid |
|---|---|---:|---:|---:|---:|
| original | test | 0.2181 | 0.1188 | 0.0665 | 0.0708 |
| original | larger_size | 0.2532 | 0.1582 | 0.0839 | 0.0863 |
| original | unseen_family | 0.3017 | 0.2682 | 0.2086 | 0.1642 |
| progression | test | 0.2242 | 0.1285 | 0.0774 | 0.0799 |
| progression | larger_size | 0.2688 | 0.1931 | 0.1261 | 0.1254 |
| progression | unseen_family | 0.3009 | 0.2786 | 0.2105 | 0.1665 |
| target_original | test | 0.2042 | 0.0720 | 0.0670 | 0.0399 |
| target_original | larger_size | 0.2543 | 0.1247 | 0.0905 | 0.0753 |
| target_original | unseen_family | 0.3150 | 0.2923 | 0.2081 | 0.1294 |
| target_progression | test | 0.2137 | 0.0671 | 0.0832 | 0.0492 |
| target_progression | larger_size | 0.2681 | 0.1417 | 0.1124 | 0.0988 |
| target_progression | unseen_family | 0.3127 | 0.3231 | 0.2196 | 0.1320 |

These predictions concern the predeclared exact-solving pipelines; no learned execution or prioritization policy has been deployed. Prediction inference cost is not part of the training labels. Preprocessing-only completions are included, and unresolved-kernel subgroups are reported separately.

Training, calibration, list splits and held-out domains match the common-label development comparison. No final prospective evidence or asymptotic claim is made.
