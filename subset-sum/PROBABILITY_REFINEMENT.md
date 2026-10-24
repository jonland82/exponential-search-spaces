# Probability refinement: theory, calibration, and cost

Publication update: October 23, 2026. These artifacts accompany the expanded [Note III](../notes/03-probability-valued-subset-sum/Probability_Valued_Subset_Sum.html) ([PDF](../notes/03-probability-valued-subset-sum/Probability_Valued_Subset_Sum.pdf), [source](../notes/03-probability-valued-subset-sum/Probability_Valued_Subset_Sum.tex)).

The revision adds a proved deterministic range/collision refinement, the reproduced list-level calibrated experiment including its size-transfer failure, and a frozen prospective cost study. The historical 50-list check and classifier experiment remain separately identified.

## Deterministic theory

For uniform targets on a finite nonempty set $D$, let $d=|D|$, $A,B$ be distinct half-sum sets, $r(t)$ their representation count, $M=\sum_{t\in D}r(t)$, and $J=\sum_{t\in D}\binom{r(t)}2$. With certified $J_-\le J\le J_+$ and $R\ge\max r(t)$, for $M>0$:

$$
\max\left\{\frac{M-J_+}{d},\frac{M^2}{d(M+2J_+)}\right\}
\le q\le\min\left\{1,\frac{M-2J_-/R}{d}\right\}.
$$

Intersect with the existing certified interval; round support counts with exact integer arithmetic before dividing by $d$. Handle $M=0$ separately by returning $q=0$. The $M\le K=\prod_j(c_j+1)$ comparison requires keeping all copies of each weight value in one block.

The implementation also uses the extremal collision upper bound $J_+=h\binom R2+\binom s2$ for $M=hR+s$, and a residue-matching cap $r(t)\le\sum_i\min(a_i,b_{(t-i)\bmod m})$. Both are proved in the paper and in the [preserved theory note](../Subset_Sum_Refinement_Experiment/deterministic_refinement/THEOREM.md).

## Statistical experiment

The frozen seed is 731029. Training/calibration/test sizes are 1,200/500/1,000 sixteen-item lists, plus 240 prespecified twenty-item diagnostic lists. Each list uses the original uniform middle-40% target rule restricted by reachable residues modulo 8, 10, 16, and 32. Original lower bounds use 512 subset witnesses. Exact reachable-target fractions label training, calibration, and evaluation; they are excluded from test features and interval construction.

A fixed gradient-boosted regressor predicts normalized position in the original interval. Calibration uses one-sided normalized errors with 2.5% allocated to each tail and score rank 489 of 500. Density and midpoint baselines receive the same calibration. Coverage is marginal across exchangeable new weight lists; it is not deterministic containment for each list.

| Center | Matched width removed | Matched coverage | Larger-list coverage |
|---|---:|---:|---:|
| Structural | 76.96% | 975/1000 (97.50%) | 213/240 (88.75%) |
| Density | 73.95% | 972/1000 (97.20%) | 237/240 (98.75%) |
| Midpoint | 56.79% | 961/1000 (96.10%) | 239/240 (99.58%) |

The structural model's size-transfer failure is retained. The earlier per-target classifier and its twenty-four-item diagnostic are a different experiment. A Windows rerun matched all labels and per-list predictions within 1e-10 after excluding timings; secondary density top-shrinkage selections varied because of floating-point ties. See the [rerun notes](../Subset_Sum_Refinement_Experiment/reruns/20261023-103931/README.md).

## Deterministic reproduction and fresh study

On the old 1,000-list cohort, range counting reproduced 13.098754% mean per-list narrowing, 778 strict improvements, and 1,000/1,000 containment. Mean width changed from 0.4044522237405377 to 0.372926981391316, a different statistic: 7.79% reduction in mean width.

The prospective protocol and protected-source hashes were frozen before fresh weights or labels were generated: 20 independent-weight and 20 repeated-pair lists at each of 12, 16, 20, and 22 weights (160 total). There is no sorted-list overlap with the original 2,940 lists. Exact positive-weight set DP supplies every evaluation label; GCD-compressed bitset DP independently agrees on 149 lists and exceeds its predeclared 100-million-bit cap on 11.

| Method | Lists | Mean width | Mean per-list narrowing | Median total ms |
|---|---:|---:|---:|---:|
| Original | 160 | 0.346567 | 0.00% | 1.610 |
| Range | 160 | 0.314830 | 14.15% | 1.901 |
| Cap only | 160 | 0.314734 | 14.18% | 1.910 |
| Partial 8 | 160 | 0.314723 | 14.18% | 1.983 |
| Partial 32 | 160 | 0.314723 | 14.18% | 2.012 |
| Residue cap | 160 | 0.314720 | 14.18% | 2.556 |
| Combined | 160 | 0.314702 | 14.19% | 2.693 |
| Sampling 128 | 160 | 0.156162 | — | 4.174 |
| Sampling 512 | 160 | 0.094139 | — | 10.971 |
| Sampling 2048 | 160 | 0.054284 | — | 37.076 |
| exact_set | 160 feasible | 0 | 100% | 22.707 |
| bitset | 149 feasible | 0 | 100% | 0.670 |

Every deterministic interval contained the exact answer. The combined method improves 75/160 intervals further than range counting, but removes only 0.00012839 additional absolute width on average. The tested collision selection is cheap and weak; a full target histogram gives much stronger information but already reveals the exact support. The old-cohort histogram row is explicitly an evaluation oracle, not a deployable approximation shortcut.

![Certified width versus total work](probability_refinement_tradeoff.png)

Times include target-support construction, witnesses, half-set construction, sorting, and all certificates, independently for each method. Sampling uses exact meet-in-the-middle labels and fixed budgets 128/512/2048. Each Hoeffding band uses alpha 0.05/3, giving at least 95% simultaneous coverage across the checkpoints; all 160 lists were covered simultaneously in this run. Empty intersections count as misses. No learned model is refit in the deterministic study.

Exact set DP covers all 160 cases. Bitset medians use only its feasible subset and should not be read as a matched all-cohort speed ratio. Timing uses one run per method/list in a reproducibly shuffled order. Python-traced memory is measured separately on the first case of each stratum (eight cases), excluding the interpreter baseline and allocator retention.

At full interval width 0.10, original bounds attain the tolerance on 64/160 lists, range and combined bounds on 67/160, and statistical sampling on 160/160 by the last checkpoint. The report compares costs against the fastest feasible exact method on the same lists. These results establish mathematical validity and modest range tightening; they do not establish a broad computational advantage.

## Sources and reproduction

- [Frozen statistical package](../Subset_Sum_Refinement_Experiment/subset_sum_refinement/README.md), [protocol](../Subset_Sum_Refinement_Experiment/subset_sum_refinement/protocol.json), and [stored summary](../Subset_Sum_Refinement_Experiment/subset_sum_refinement/results/summary.json).
- [Deterministic report](../Subset_Sum_Refinement_Experiment/deterministic_refinement/REPORT.md), [protocol and source hashes](../Subset_Sum_Refinement_Experiment/deterministic_refinement/protocol.json), [tests](../Subset_Sum_Refinement_Experiment/deterministic_refinement/test_bounds.py), and [raw measurements](../Subset_Sum_Refinement_Experiment/deterministic_refinement/results/prospective.jsonl).
- [Publication summary and input hashes](probability_refinement_summary.json), [calibration table](probability_calibration_table.tex), [deterministic table](probability_refinement_table.tex), and [standalone chart PDF](probability_refinement_tradeoff.pdf).

From the repository root, rebuild publication artifacts without regenerating labels or timings:

```text
python subset-sum/probability_refinement_artifacts.py
python build_papers.py --paper Probability_Valued_Subset_Sum
```

To rerun the deterministic experiments, follow the preserved package README in a new sibling copy without its existing results. The runner refuses to overwrite prospective evidence or accept modified protected sources. Algorithms and tests need only Python's standard library; plotting requires Matplotlib. The statistical package lists its separate pinned numerical dependencies. The publication builder only reads saved evidence and copies its archived chart.

The bounds use elementary counting and Cauchy–Schwarz. Literature novelty and a new worst-case complexity bound are not claimed. The raw experiments and frozen proof note retain their historical pre-publication wording.
