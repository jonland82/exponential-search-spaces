# Subset-sum runtime histogram and class locations

Retrospective visualization of saved evidence, generated October 30, 2026.
No solver runs, model fits, or changes to frozen evidence.

Rebuild from the repository root:

```powershell
python tools/plot_subset_sum_runtimes.py
python tools/plot_subset_sum_completion_times.py
python tools/plot_analytical_completion_sketch.py
```

The PNG is intended for inline viewing; the PDF provides an exportable version.
The [completion-time histogram](subset_sum_completion_time_histogram.png)
stacks the 430 completed inputs by first finishing route while using each
input's total elapsed time, including preprocessing and earlier attempts.
Its red rug shows the 146 unresolved stopping times separately; their
eventual completion times are not observed. The completed-input median is
1.002 ms. A [vector PDF](subset_sum_completion_time_histogram.pdf) is also
available.
The [smooth structural sketch](subset_sum_analytical_completion_sketch.png)
overlays a five-route lognormal mixture on the same completed-input histogram.
It uses the saved route counts and medians as anchors, but sets route log-spreads
by hand; no likelihood, error criterion, or density fit is used. It is an
illustration of the route-mixture hypothesis, not an analytical prediction of
the distribution. A [vector PDF](subset_sum_analytical_completion_sketch.pdf)
is also available.
`plotted_inputs.csv` contains the 576 main-panel input records, and
`manifest.json` records source hashes, histogram bins and checked counts.

Panels A and B join the original prospective study's `scale=1` inputs to
`references.jsonl`, using `mode=work`, `repeat=0`. The x coordinate is saved
wall-clock runtime, not work counts. Each input is counted once in panel A.
The 8L allowance and state/bitset limits can stop a run without an answer:
the 146 unresolved observations are elapsed stopping times, and their eventual
completion times are unknown. Do not read them as completed runtimes.
The measurements include exact target preprocessing and exclude ML feature and
inference acquisition costs. Timings are the original single work-mode measurements,
not medians across the separate live-time runs.

Certified full-list classes come from the saved input-space presentation's
full-list distance certificates. They overlap in panel B; their union contains
144 inputs, including 9 unresolved interval/progression inputs. Of 430 completed
inputs, 135 belong to this union and 295 do not. Absence from these classes does
not imply lack of other useful structure.

ML flags use the frozen original combined logistic model and threshold
`p(completion) < 0.5`. It flags 118 unresolved and 23 completed cases, and misses
28 unresolved cases. These are predictions about finite-budget portfolio
completion, not newly proved hard classes or evidence of intrinsic hardness.
Panel B uses deterministic vertical jitter solely to separate markers.

Panel C separately shows all 18 historical constructed hard NO benchmarks from
`subset-sum/hard_results.json`. Each has a saved completed meet-in-the-middle
runtime and a certified DFS runtime; 9 DFS runs stop at 2 seconds. The families
repeat random 41-bit odd weights once, twice or three times, with n=24/30/36,
two seeds, and targets passing cheap whole-instance bounds/residue checks.
These use different solvers and a separate experiment; their runtimes have a
separate x-axis scale and are not pooled into panel A. "Hard" is the historical
benchmark description, not a solver-independent complexity classification.

The inputs are synthetic and targets from the same weight list are dependent.
The histogram describes this sampled corpus, not a uniform distribution over
all subset-sum inputs. Its equal-width bins in log runtime show counts, not
density per millisecond.
