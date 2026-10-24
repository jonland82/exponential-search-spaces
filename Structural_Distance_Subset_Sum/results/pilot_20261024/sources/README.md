# Structural distance in exact subset sum

First implementation milestone for [the proposed new note](../Distance_From_Easy_Subset_Sum_Next_Note.md).

The [theory note](THEORY.md) proves that a sorted greedy scan finds a maximum-size
superincreasing core. This improves the prospectus's initial $O(n^2)$ discovery
bound to $O(n\log(n+1))$, including sorting.

The exact solvers search only exceptions, either as indexed selections or as
distinct exceptional sums. The resulting bounds are

$$
O\!\left(n\log(n+1)+(n+1)2^{k(w)}\right)
$$

and

$$
O\!\left(n\log(n+1)+(n+1)M(E)\right),
$$

in arithmetic operations. Full bit costs are polynomial in the binary input
length times the indicated exponential or support-size factor. These are
sufficient tractability guarantees, not lower bounds for inputs outside them.

## Validate

From the repository root:

```powershell
python -m unittest discover -s Structural_Distance_Subset_Sum -p test_structural_subset_sum.py -v
```

The tests independently enumerate small cores and subset sums, check all-target
answers, indexed witnesses, shuffled and large-integer inputs, repeated
exceptions, and honest resource exhaustion. The code uses the standard library.

## Use

From this directory:

```python
from structural_subset_sum import Limits, find_core, solve

weights = [2, 5, 6, 11, 23]
core = find_core(weights)
answer = solve(weights, 17, limits=Limits(max_work=1_000_000))
assert answer.status == "yes"
assert sum(weights[i] for i in answer.witness) == 17
```

`status` is `yes`, `no`, or `unresolved`. A stopped run never turns into NO.
`method="distinct"` constructs and merges exceptional sums before querying the
core. `method="enumerate"` visits indexed selections in Gray-code order and can
stop early on a witness. `M` is unavailable until full distinct construction has
completed; an early result is not an estimate of that quantity.

The baseline functions provide independent meet-in-the-middle, memoized bounded
DFS, and decision-only integer-bitset methods. The bitset baseline intentionally
does not store witnesses. Every method includes its own preprocessing in elapsed
time. Explicit work units differ by operation; use them for mechanism accounting,
not as a uniform CPU-cost model.

## Exploratory pilot

```powershell
python Structural_Distance_Subset_Sum/run_pilot.py
```

The default output is `results/pilot_20261024/`. Existing output is protected;
use `--output` with a new directory for a rerun. The optional chart requires
`matplotlib`; raw data and the Markdown report do not.

The pilot saves inputs, independently computed labels, raw per-run results,
source hashes, configuration, a summary, and a chart when plotting is available.
It varies total size and injected disruption, records actual discovered
distance, compares repeated and unrelated exceptions, and labels both planted
and uniformly drawn middle-range targets by a separate exact oracle.

This is exploratory evidence. Timings use one shuffled-order run per case and
method, and include instrumented Python overhead. Residual-record counts are
reported; exact byte memory profiling and a fresh frozen prospective comparison
remain subsequent work. Resource limits and bitset infeasibility are recorded
as unresolved outcomes.

## Next research decisions

1. Evaluate whether observed cost is better explained by $k$ or $M$.
2. Compare core choices: minimum deletion count need not minimize residual support.
3. Freeze a prospective comparison after choosing useful sizes and budgets.
4. Add adaptive recognition or a second type of core only with separate cost
   accounting and independent correctness checks.

No files in the earlier frozen refinement experiments are modified by this package.
