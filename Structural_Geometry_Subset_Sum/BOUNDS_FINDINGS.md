# Bounds-first execution: cheaper work, similar completion

October 28, 2026. [Overview](experiments/05_bounds_first/README.md) ·
[Protocol](experiments/05_bounds_first/PROTOCOL.md) ·
[Mathematics](experiments/05_bounds_first/THEORY.md) ·
[Saved report](results/05_bounds_first_20261028/REPORT.md) ·
[Reproduction](results/05_bounds_first_20261028/README.md).

The follow-up preserves the exception-core route's advantage over root geometry,
and reduces its measured work. It does **not** establish an additional completion
or wall-clock improvement over previous reuse. Fast discovery recovers the three
previously observed regressions, in an explicitly retrospective check.

## Fresh result

384 new weight lists / 1,152 targets, sixteen families, n=24,30,36. Sources,
configuration and endpoints were frozen before generation; 2,244 prior normalized
lists and new duplicates were excluded. Every method shares the original five
core reuse and fallback, with all acquisition/checking costs charged. No ML is
fitted and no planted decomposition or family labels enter solving.

| Policy | Exact decisions under 32L | Capped work | Core tables built | Live 20ms median [range] |
|---|---:|---:|---:|---:|
| Original root geometry | 916 | 28,582,458 | 0 | 836 [823,836] |
| Previous core reuse | 953 | 26,463,413 | 182 | 896 [884,898] |
| Fast discovery, bounds only | 933 | 27,494,127 | 0 | 862 [846,862] |
| Fast discovery, bounds first + reuse | **954** | **26,002,456** | **92** | **897 [889,897]** |
| Fast discovery, immediate table | 954 | 26,122,175 | 182 | 894 [884,898] |

The primary bounds-first minus previous-reuse completion difference is **+1**,
with paired whole-list-bootstrap 95% interval **[0,3]**: one gain, no losses in
this sample. The gain is one n=30 near-equal NO target. This is not evidence of
a reliable incremental completion advantage.

The secondary capped-work saving is **460,957 units (1.74%)**, with exploratory
95% interval approximately **[371,704,566,671]**. Unresolved calls are charged
their full allowance here. Actual work is 25,218,397 versus 25,735,033, a 2.01%
reduction; actual totals mix different completion sets and censored runs.
Neither measure is a uniform CPU/bit-operation count or a runtime speedup.

Compared with root geometry, bounds-first completes **38 more targets**,
with conditional interval approximately **[20,57]**. This is fresh support for
the wider exception-core direction, rather than a large new gain from bounds.
All intervals keep the three targets per weight list together and condition
on the fixed solvers and generated mixture. Secondary intervals are unadjusted.

## Which change helped?

**Delaying construction avoids 90 of 182 tables (49.5%).** All 90 are exact NO
certificates obtained by exhausting exceptional assignments using necessary
range/quotient bounds. Against the matched fast-eager control, bounds-first
saves **119,719 capped-work units**, with exploratory interval approximately
**[47,781,219,337]**, while tying on completions. Thus those tables were unnecessary
for these decisions. When an assignment survives bounds, exact table membership
and witness reconstruction remain available.

**Bounds alone are insufficient.** The bounds-only portfolio completes 933,
versus 954 with the table available: a net difference of 21, conditional interval
[12,31]. This control uses the same DP-affordability gates; it is not a separately
optimized, unrestricted bounds-only algorithm. It returns unresolved at its first
interval-feasible assignment because feasibility does not establish reachability.

**Discovery is cheaper and can preserve fallback answers.** Discovery work falls
from 875,473 to 249,587 units. The new search maintains quotient/residual totals
incrementally, defers detailed estimates until memory gates pass, and has a
local work cap preserving fallback allowance. Fast-eager also completes 954,
so the one new completion is attributable to discovery changes rather than
delaying construction. Plans/gates are identical between fast-eager and
bounds-first on every fresh counter call.

The three old root-success/reuse-failure cases are all recovered by the fast
discovery versions (3/3 versus previous reuse 0/3). These selected, inspected
cases are **retrospective**, excluded from the fresh statistics. They do not
prove discovery can never cause a regression on another input.

## Runtime and remaining limits

The live medians of 897 versus 896 are effectively tied in these three repeated
orders. Their ranges overlap and the repeats share the same inputs. No clear
additional wall-clock benefit over previous reuse is established at 20ms. Late
outer calls are excluded, including any whose inner solver finished in time.
The largest observed outer overshoot was 52.1ms for previous reuse and 1.81ms
for bounds-first (61.4ms for root). These are observed maxima, not hard timing
guarantees; Python calls and operating-system scheduling are not preempted.

This is a small implementation improvement to an existing structural route.
The clear mechanism is avoiding unnecessary table construction while keeping
exact queries for the cases that need them. The root-to-exception gain persists;
the new bounds-first refinement mainly reduces work rather than expanding
coverage. No general worst-case bound, state-of-the-art superiority, default
model replacement or manuscript revision follows.

There are 198 unresolved fresh targets. Of these, 88 belong to two-scale or
two-progression families, 48 to random-wide and 34 to filtered-modular. Those
170 misses suggest a different route is needed to substantially expand coverage;
further table-construction savings alone will not address most remaining cases.
This family breakdown is descriptive post-evaluation analysis, not a hardness
certificate. Larger sizes, stronger portfolios and independent machines remain
untested. Logical DP/history caps do not measure exact Python allocation or RSS.

## Validation

All 100 relevant tests pass (34 structural geometry, 50 learned-model and 16
original structural-distance tests). The successful [saved audit](results/05_bounds_first_20261028/VALIDATION.json)
checks source/input/artifact hashes, all 384 lists / 1,152 independent exact
truths, 5,760 deterministic fresh replays, 17,280 live records and 15 retrospective
replays. It independently enumerates the bounds certificates, checks partitions,
witnesses, caps and phase sums, verifies matched discovery plans, and reconstructs
the report. The four previous structural studies retain their frozen hashes.
