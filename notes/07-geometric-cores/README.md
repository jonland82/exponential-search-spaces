# Note VII: Geometric Cores and Exceptions in Subset Sum

Working draft, October 28, 2026. An exact geometric core-and-exceptions route
turns the series' structural coverage principle into a measured improvement
under declared paid budgets.

- [Read HTML](Geometric_Cores_and_Exceptions_in_Subset_Sum.html).
- [Read PDF](Geometric_Cores_and_Exceptions_in_Subset_Sum.pdf).
- [LaTeX manuscript](Geometric_Cores_and_Exceptions_in_Subset_Sum.tex).
- Two-page runtime companion: [PDF](Runtime_of_Geometric_Core_Subset_Sum.pdf),
  [HTML](Runtime_of_Geometric_Core_Subset_Sum.html),
  [LaTeX source](Runtime_of_Geometric_Core_Subset_Sum.tex).
- [Evidence manifest](paper_evidence.json) and [figure](geometric_gain.png).
- [Exception-core findings](../../Structural_Geometry_Subset_Sum/EXCEPTION_FINDINGS.md).
- [Bounds-first findings](../../Structural_Geometry_Subset_Sum/BOUNDS_FINDINGS.md).
- [Study 04 protocol](../../Structural_Geometry_Subset_Sum/experiments/04_exception_core/PROTOCOL.md)
  and [saved evidence](../../Structural_Geometry_Subset_Sum/results/04_exception_core_20261028/README.md).
- [Study 05 protocol](../../Structural_Geometry_Subset_Sum/experiments/05_bounds_first/PROTOCOL.md)
  and [saved evidence](../../Structural_Geometry_Subset_Sum/results/05_bounds_first_20261028/README.md).

## Central mechanism

After exact reductions, write $u_i=Mp_i+r_i$. Build an exact table for a core
$C$ and enumerate the small exceptional set $E$. For exceptional subset $A$,
test the shifted target $z_A=T-\sum_{i\in A}u_i$ using necessary geometric bounds.
Construct the table only if some assignment survives; reuse it for all queries.

$$
C\le F+2^{|E|}B+I D+N_QQ_{\mathrm{pt}}+V.
$$

$F$ pays discovery, $B$ pays bounds per assignment, $D$ constructs one table,
$I$ records whether construction is needed, and the remaining terms pay exact
queries and verification. The manuscript proves safe truncation, exact reuse
and a complete bounds-only NO certificate.

## What the experiments support

- Study 04: 453 → 469 completions / 576 targets; primary net +16,
  conditional whole-list-bootstrap 95% interval approximately [4,30].
- Study 05: root 916 versus bounds-first 954 / 1,152 targets; this is a secondary
  fresh comparison, net +38 with exploratory interval approximately [20,57].
- Study 05 primary incremental comparison: previous reuse 953 versus 954;
  interval [0,3], so no reliable additional completion advantage is established.
- The refinement reduces capped work by 1.74% and avoids 90/182 tables.
  Incremental wall-clock results are nearly tied. No new general worst-case
  bound or state-of-the-art superiority is claimed.

The two studies have different fresh samples and primaries. They are reported
separately. Inspected old failures and repaired regressions remain retrospective.
No new experiment was run to write the note.

## Build and audit

```powershell
python build_papers.py --paper 7
python tools/check_links.py
```

The builder verifies frozen source/input/artifact hashes, checks completion and
table-build counts against raw saved traces, and regenerates values, tables,
figure, PDF, HTML and the evidence manifest. It performs no training, solver
reruns, new timings or new bootstrap. Full replay commands are in the study
guides above. Build artifacts stay in `.build/latex/07-geometric-cores/`.

The same command builds the two-page runtime companion. It derives explicit
table/query costs, states sufficient structural regimes, and compares the
general classical benchmarks (including the separately labeled October 2026
preprint). It introduces no new experiment and is a supplement to Note VII,
not an eighth numbered note.
