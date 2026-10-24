# Validation ledger: October 24, 2026

## Independent tests before the freeze

Command:

```powershell
python -m unittest discover -s Structural_Distance_Subset_Sum -p "test_*.py" -v
```

All 16 test groups passed before evaluation generation. They include exhaustive
core optimality and all-target checks, indexed witnesses, large integers,
one-swap selection, exact support coverage, retained-support resource accounting,
modular filtering, the declared cohort grid, and exclusion of incomplete timing
repetitions from paired summaries.

## Freeze and source integrity

The protocol was frozen at `2026-10-24T13:55:09.922679+00:00`, before the
generation stage completed at `2026-10-24T13:55:17.444757+00:00`. Generation
was invoked only after the freeze command returned successfully.

Protocol SHA-256:

```text
4ee68d07809c297e6fa70738040803493230d07bbe8b2d4b0d7b5ebf0145aebc
```

All 11 protected working sources and frozen snapshots still match their
declared hashes. The reporting stage also checked the saved input, timing-run,
and memory-profile digests.

The two earlier pilot source versions are preserved in their own source
snapshots, so subsequent overview edits do not obscure the versions that
produced those measurements.

## Saved data checks

- 60 unique new lists and 180 unique case IDs; no sorted-list overlap with the
  earlier pilot and no duplicate lists in the new cohort.
- Every conditioned NO target independently passes the declared residue
  screens and has a NO oracle label.
- 3,780 timing records: 3,117 completed and correct, 663 unresolved.
- 28 memory records: 24 completed and correct, four unresolved.
- Every saved witness uses distinct valid original indices and sums exactly
  to its target.
- Every timing case-method group has exactly three distinct repetition IDs.
  There are no inconsistent completion statuses across those repetitions.
- Every published support improvement belongs to an exchange-gadget list and
  reduces support by two sums.
- Neither selector wins a paired timing comparison on any of the 162
  structured target cases.

These checks confirm agreement on the tested inputs and integrity of the
recorded experiment. They are not a novelty certification or a worst-case
performance theorem.

## Documents and figures

Markdown inline/display math delimiters and local links were checked across
the prospectus, package documents, and generated report. The comparison chart
was visually inspected; standalone PNG and SVG artifacts are preserved.

The [findings](FINDINGS.md) distinguish core-discovery/search operation counts
from full binary-input costs, and distinguish support reduction, elapsed cost,
completion, and Python-traced memory.
