# Note III refinement evidence

The October 23, 2026 revision integrates the theoretical and experimental
follow-up into [Paper III](../notes/03-probability-valued-subset-sum/Probability_Valued_Subset_Sum.html)
([PDF](../notes/03-probability-valued-subset-sum/Probability_Valued_Subset_Sum.pdf), [LaTeX](../notes/03-probability-valued-subset-sum/Probability_Valued_Subset_Sum.tex)).
The series remains four notes.

- [Publication methods ledger](../subset-sum/PROBABILITY_REFINEMENT.md):
  the theory, statistics, cost findings, source hashes, and rebuild commands.
- [Original statistical experiment](subset_sum_refinement/README.md):
  frozen protocol, separate training/calibration/test data, exact labels,
  interval predictions, provenance, and the original report.
- [Statistical rerun](reruns/20261023-103931/README.md): reproduced main
  results, environment details, and floating-point tie sensitivity in a
  secondary selection diagnostic.
- [Deterministic continuation](deterministic_refinement/REPORT.md):
  reproduced 13.10% old-cohort range tightening, proof and verification,
  160 fresh multi-size lists, exact and sampling baselines, timing and memory.
- [Conversation and research handoff](Subset_Sum_Research_Transcript_and_Next_Steps.md):
  historical discussion followed by the continuation and integration status.

Publication tables, chart, and summary are generated from these saved
measurements by `python subset-sum/probability_refinement_artifacts.py`.
Run `python build_papers.py --paper Probability_Valued_Subset_Sum` to
regenerate those artifacts and the paper's PDF/HTML.

The protected deterministic sources, frozen protocol, original statistical
data, and rerun measurements retain their historical state. In particular,
the frozen proof note's statement that Paper III was unchanged describes
the experiment stage before this publication integration. No calibration
constants or methods were changed after prospective test inspection.
