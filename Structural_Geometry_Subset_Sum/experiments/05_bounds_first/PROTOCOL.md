# Experiment 05: bounds-first execution

Freeze source, configuration and prior-list hashes before generation. Preserve
Experiments 01–04. This tests a refinement motivated by the inspected Experiment
04 results; its new evaluation inputs are independently generated after freezing.

## Fixed methods

1. `root`: unchanged Experiment 04 root geometry and shared exact portfolio.
2. `reuse`: unchanged Experiment 04 exception-core route, including discovery.
3. `bounds_only`: fast capped discovery, then necessary interval checks only;
   stop unresolved at the first feasible exceptional assignment, with no DP.
4. `bounds_first`: same discovery, build one exact core table only when an
   exceptional assignment survives necessary bounds, then reuse it.
5. `fast_eager`: attribution control; identical discovery/plans to bounds-first,
   but construct the same table immediately, before exceptional bounds.

All retain the same preprocessing, original 15 base features, five-core reuse,
blind projection, root checking, exact fallback and certificate verification.
No generator metadata or family labels enter solving. Bounds-only deliberately
uses the same DP-affordability gates; this isolates the certificate mechanism,
and is not an unrestricted bounds-only solver.

Fast discovery ranks the same residuals and considers the same zero-to-nine
exception partitions. Maintain residual/quotient totals incrementally and defer
the detailed work estimate until memory gates pass. Discovery has a local cap
`min(1024, remaining_work // 16)`. Sort/initial totals cost `n*bit_length(n)+4n`,
each partition costs 8 and each memory-eligible work estimate costs `3n` units.
The work-estimate gate, 3/4 execution reserve, 60,000 core cap, 2,000,000 DP bits,
64,000,000 history bits and original fallback caps remain unchanged. Cap
exhaustion returns unresolved and preserves the unused fallback allowance.

Core construction and every bound, assignment, point query, history copy,
reconstruction and verification are charged with the preceding counter model.
Construction is delayed, never duplicated. There is no tuning on fresh results.

## Inputs and endpoints

Seed 800281028; 16 existing families; sizes 24, 30, 36; eight fresh lists per
family/size; three target rules per list: 384 lists / 1,152 targets. Exclude all
previous normalized sorted-list signatures and new duplicates. Preserve the
preceding generation recipe and label all inputs by their original families.
An independent meet-in-the-middle oracle establishes exact truths offline.

Primary: bounds-first minus previous reuse exact completions under the same
individual `32 * input_length` allowance. Report gains and losses separately,
and a 4,000-draw paired whole-list-bootstrap 95% interval (all three targets
stay together). This is conditional evidence for the fixed generated mixture.

Secondary: capped-work savings (unresolved charged their full allowance), actual
work, family counts, discovery cost/caps, DP builds and bounds-only NO counts.
The fast-eager comparison isolates delayed construction from discovery changes.
Secondary intervals are exploratory and unadjusted; no universal or asymptotic
claim follows. Record work-capped live 20ms deadlines in three randomized case
and policy orders; reject outer-deadline answers. These repeats share inputs.

Replay only the three previously observed root-success/reuse-failure cases as
an explicitly retrospective regression diagnostic, excluded from fresh endpoints.
No shared-pool endpoint or expanded-size claim is part of this experiment.

## Audit

Hash source snapshots, inputs and artifacts; recompute all independent truths;
check witnesses, partitions, decomposition, caps and phase sums. Independently
enumerate exceptional binary masks to validate complete bounds certificates.
Replay every deterministic counter and retrospective call, check live deadlines,
and reconstruct reports. Exhausted or partial checks must remain unresolved.
