# Geometric core reuse: a fresh measured gain

October 28, 2026. [Overview](experiments/04_exception_core/README.md) ·
[Frozen protocol](experiments/04_exception_core/PROTOCOL.md) ·
[Exactness and cost](experiments/04_exception_core/THEORY.md) ·
[Saved report](results/04_exception_core_20261028/REPORT.md) ·
[Reproduction](results/04_exception_core_20261028/README.md).

The new exact route improves fresh completion counts over the matched original
root-geometry portfolio. It builds one geometric core table, then reuses it for
all required exceptional assignments. Discovery, construction, prefix-history
copies, exceptional queries, fallback and verification are all paid. No ML or
generator-supplied decomposition/outlier labels enter solving.

## Fresh primary result

192 fresh lists / 576 targets, n=24,30,36, sixteen families. Sources, gates,
generators and endpoints were frozen before generation; all 2,052 prior
normalized sorted lists and new duplicates were excluded. The primary is
completed exact decisions under the same full individual 32L work allowance.

| Policy | Work completions / 576 | Live 20ms median [range] |
|---|---:|---:|
| Lean portfolio, no geometry | 434 | 356 [353,356] |
| Original root geometry | 453 | 407 [402,408] |
| Root plus new discovery only | 450 | 407 [404,408] |
| Root plus reusable exception core | **469** | **440 [434,440]** |
| Direct MITM control | 412 | 358 [357,362] |

**Primary difference: +16 completions**, with paired whole-list-bootstrap 95%
interval approximately [+4,+30]. Reuse finishes 19 inputs that root geometry
does not, while losing three root completions: net +2.78 percentage points,
or 3.5% more completed decisions relative to root. The interval conditions on
the fixed solvers and generated mixture; it is not a distribution-free result.

The separate live endpoint uses both the original work cap and a real 20ms
per-input deadline, excluding late outer calls. Its three repeated-order totals
are descriptive measurements on the same inputs, not independent new samples.
The largest reuse overshoot is about 0.84ms; late answers are not counted.

Aggregate actual work is 12,708,976 for reuse versus 13,990,563 for root,
9.16% lower in this counter model. These heterogeneous units are not CPU/bit
operations, and aggregate work mixes different completion sets and unresolved
runs; this is not a 9.16% wall-clock or asymptotic speedup claim.

## Where it helps and where it costs

| Family, 36 targets each | Root geometry | Core reuse | Difference |
|---|---:|---:|---:|
| Large base, many outliers | 22 | 34 | +12 |
| Near equal, possibly perturbed | 20 | 25 | +5 |
| Large base, one outlier | 34 | 36 | +2 |
| Two scales | 13 | 11 | -2 |
| Two progressions | 14 | 13 | -1 |

All other family work-completion counts tie. The three lost cases have no
acceptable new core plan: unproductive discovery consumes enough work to lose
a later fallback answer. The discovery-only control loses the same three cases.
This identifies a concrete overhead to reduce rather than hiding regressions.

All 98 executed new core calls finish exactly: 46 YES witnesses and 52 NO
certificates. Each constructs one table. Across them, 13,074 exceptional
assignments use just 53 point-membership queries, with cheap shifted-target
range/aggregate checks rejecting the other assignments. The work/memory gates
select between one and nine exceptions; this generalizes the motivating
four/five-outlier examples rather than using a planted exception count.

49 of the 52 core NO events need zero point-membership queries. Thus an
interval/bounds-only exceptional-assignment ablation could isolate how much
benefit requires constructing the table. This experiment establishes the value
of the complete exception-core route, not the incremental necessity of table
reuse versus every cheaper possible certificate. Testing bounds before table
construction is a concrete future optimization.

## Shared work pools

Medians over three paired FIFO arrival orders, with all online work charged:

| Cohort | Nominal budget fraction | Root geometry | Core reuse |
|---|---:|---:|---:|
| Large base | 20% | 58 | 97 |
| Large base | 50% | 123 | 137 |
| Earlier families | 20% | 136 | 136 |
| Earlier families | 50% | 324 | 332 |

These are secondary endpoints on the same sample. Lean/direct-MITM controls
remain stronger on some earlier-family pools; the saved report retains them.
No universal portfolio or state-of-the-art superiority is established.

## Old-failure repair: retrospective only

Replaying the 115 inspected failures that motivated the route at their original
work allowances, root geometry resolves zero, core reuse resolves 25, and direct
MITM resolves 15. Reuse fixes 11/14 many-outlier cases, versus 5/14 for direct
MITM. The remaining three many-outlier targets share one n=36 list for which
the size/work gates select no affordable plan.

This selected old sample is explicitly retrospective. Its repairs are not
fresh confirmation, not added to the primary statistic, and not a net gain
over every input in the old dataset, which was not all rerun.

## Research-program implication and limits

The failure analysis exposed instances far from the original five recognized
cores but close to a geometric core after removing a few large residuals. This
implements the program's exception-to-tractable-core principle with the cost
form $F+C_{\rm core}+2^{|E|}Q+V$, instead of repeatedly rebuilding a checker or
asking ML to select an unavailable route.

The next refinement is cheaper discovery/bounds-first execution to preserve the
gain while removing the three acquisition regressions. Larger independent
samples, other sizes and stronger portfolios are needed for wider claims.
There is no new general worst-case bound, default-model replacement or paper
revision. Logical DP/history caps bound represented positions, not exact Python
allocation or RSS; the largest recorded history bound is 40,408,128 bits.

## Validation

95 relevant tests pass: 29 structural-geometry tests, 50 earlier learned-model
tests and 16 original structural-distance tests. The successful
[audit](results/04_exception_core_20261028/VALIDATION.json) independently checks
all 192 fresh lists / 576 exact truths, source/input/artifact hashes, partition
and projection arithmetic, one-build and full-enumeration invariants, witnesses,
all 2,880 fresh counter replays, 8,640 saved live runs/deadlines, 60 deterministic
pool replays, 345 retrospective replays and reconstructed summaries/reports.
Earlier frozen evidence is preserved.
