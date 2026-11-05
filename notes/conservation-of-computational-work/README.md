# A Conservation Law for Search Work

J. R. Landers. [Standalone PDF](conservation_of_search_work.pdf), four pages.

This note separates work spent discovering and constructing structure from work spent using it and finishing a search. A lower bound on their total constrains possible allocations; stronger tradeoffs require explicit bounds on how much progress each phase can make.

It covers:

- Accounting at a proven computational lower bound, including a maximum-finding example.
- A conditional candidate-coverage model for subset sum, with structural charges and individual-survivor search charges stated as hypotheses.
- A classical quadratic lower bound for real-valued subset sum in a linear decision-tree model.
- A SETH-conditional obstruction to a uniform integer subset-sum bound of the specified target-dependent form.
- The practical pruning criterion: saved checking cost must exceed all pruning overhead.

The note does not establish an unconditional exponential lower bound for general integer subset sum. Model-specific and conditional bounds remain distinct from general runtime upper bounds.

The PDF is preserved as supplied. This checkout currently contains no corresponding LaTeX source or HTML edition, so the paper is included in site staging and link checks without a rebuild target.

In the [research reading path](../README.md), read it alongside [Certified Coverage](../01-certified-coverage/README.md), before the experiments testing whether shortcuts repay their cost. The separate [conditional coverage-law Markdown draft](../01-certified-coverage/certification-cost/README.md) develops a related hypothesis; it is not an alternate source for this PDF.
