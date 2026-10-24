# Frozen comparison: cost of selecting a tractable core

The machine-readable configuration and protected-source hashes are written by
the freeze command before any fresh evaluation weights or labels are generated.
This is a local protocol freeze, not externally registered preregistration.

## Questions

1. Do verified one-swap cores reduce residual support relative to the maximum
   greedy core?
2. Does the reduction repay the full selection and probing cost?
3. How do the exact methods behave on a stronger NO cohort at nonzero distance?
4. What Python-traced memory do the methods use on a predeclared small subset?

## Inputs

Use sizes $n\in\{20,28,36\}$, injected counts $r\in\{4,8,12\}$, three families,
and two independent seed replicates per cell: 54 structured lists.

- **Unrelated:** a gappy superincreasing generator plus unrelated positive
  integers at most its total. The first core weight is drawn in
  $[2^{24},2^{25})$; later weights exceed the previous total by roughly one
  quarter to one half of that total. This keeps target support sparse enough
  to obtain NO labels.
- **Repeated:** the same gappy generator, with all injected weights duplicating
  a middle core value.
- **Exchange gadget:** $r$ copies of $a$, one $2a$, and one $3a$, where
  $a\in\{1,2,3,4\}$, followed by $n-r-2$ superincreasing extensions larger than
  the total of all preceding items. The low gadget is motivated by the earlier
  finite counterexample, not a discovery on the new test labels.

Add six unstructured controls: two random 41-bit lists at each size. Total:
60 lists. Shuffle indexed items. Require gcd one, with at most 32 seeded weight
draws per planned list; record failures instead of silently replacing strata.

Measure actual $k$, bit lengths, and sorted-list overlap with earlier pilots.
Do not assume injected $r$ equals minimum deletion distance.

## Targets and independent labels

For each retained list:

1. A target from an independent fair-bit subset of all indexed items.
2. An integer uniform on the inclusive interval
   $[\operatorname{round}(.30S),\operatorname{round}(.70S)]$, where $S$ is the total.
3. A second draw rule uniform on that interval, accepted only if all reachable
   residue screens modulo $8,10,16,32$ pass and an independent exact oracle
   labels it NO. Use at most 256 proposals. Record each proposal and acceptance
   outcome; if none is accepted, retain the other targets and report a missing
   NO slot.

The third cohort is deliberately conditional. It does not estimate a uniform
target success rate or unconditional average solver cost. It passes root
range/gcd and the stated modular checks. The unconditioned uniform cohort is
reported separately.

Use independent full binary-mask half enumeration for labels. Save oracle
witnesses, preprocessing time, proposal/filter/query counts, and label-generation
time separately. Oracle tables and labels are never supplied to measured solvers.
Destroy oracle tables before solver timing.

## Methods and accounting

- Greedy-core distinct exceptional sums.
- Greedy-core exceptional selections in Gray-code order.
- Multiplicity-cap one-swap core selection.
- At most four exact-support one-swap probes, with winning support reused.
- Memoized bounded DFS.
- Meet-in-the-middle, merging duplicate half sums.
- Integer-bitset DP with a declared width limit; decision-only.

The selection policies are exactly those in
[SELECTION_THEORY.md](SELECTION_THEORY.md). All scans, rejected checks,
construction, selection, and queries are included in elapsed time. Every method
performs its own range/gcd checks. The modular screens condition the NO targets;
they are not an extra root accelerator given only to one solver.

Limits per timing run: 2,000,000 explicit work units, 1,048,576 live residual
records, 1.5 seconds checked between operations, and 16,000,000 bitset width bits.
The time limit is cooperative, not a hard process kill. Input/core records,
candidate records, Python object overhead, and integer byte sizes are not covered
by the residual-record cap; the separate memory pass measures tracked bytes.

Use three timing repetitions per case and method, with independently shuffled
method order for each repetition. Preserve every run. Report per-case medians,
completion consistency, and paired comparisons only when both methods complete
all three repetitions. A faster method is strictly smaller in median elapsed time.
No threshold is fitted to evaluation results.

Never count resource exhaustion as NO. Check every completed answer against
the independent label and every returned witness against original indices.
Any discrepancy invalidates the corresponding experiment and must be reported.

## Separate memory pass

Profile the conditioned-NO case at $n=20,r=8$, seed replicate zero, for each
structured family, plus the $n=20$ unstructured control at replicate zero:
four predeclared cases, seven methods each.

Run garbage collection, start a fresh tracemalloc session with one-frame traces,
invoke the complete method, capture peak Python-traced bytes, and stop tracing.
Use the same work/state/bitset limits but no time limit, because tracing changes
execution time. Record profiling completion separately from timing completion.
Inputs already exist when tracing starts. This measures new Python allocations,
not total process RSS or allocator retention; tracemalloc metadata itself is
outside the reported application-allocation peak.

## Prespecified reporting

- Input, target, YES/NO, actual distance, and NO-slot completion counts by stratum.
- All unresolved reasons and repeat inconsistencies.
- Exact-answer and witness agreement.
- Selected support size versus greedy support on lists with completed supports;
  one target-independent observation per list and policy.
- Paired total-time wins and median time ratios against greedy distinct search,
  bounded DFS, and the fastest feasible elementary baseline on the same case.
- YES/NO and target-rule stratification; ordinary controls separately from
  structured lists.
- Selection/probing versus generation and query time.
- The 28 separate memory profiles, with completion status.
- Source hashes, immutable configuration, input/proposal/run data, and charts.

No significance claim or general speedup follows from this small synthetic
sample. If selection is slower despite smaller support, preserve that result.

## Execution integrity

The freeze writes source snapshots, a protocol digest, and UTC time. Generation,
timing, and memory commands verify those protected hashes and reject existing
stage outputs. Record stage input/output digests. Source or generator changes
after labels are inspected require a new, explicitly identified study rather
than relabeling the same inputs as fresh prospective evidence.
