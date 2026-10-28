# Cost-aware geometric checking

The preceding experiment predicts whether a portfolio finishes. This experiment
asks the decision-specific question: **will trying the geometric DP save more
work than it consumes?**

For each development input, run the same exact pipeline twice, once with and
once without the check. Charge all phases, and assign unresolved runs their
full work allowance in the censored training objective:

$$
\Delta_i=C_i(\text{skip})-C_i(\text{try}),\qquad
y_i=\mathbf{1}\{\Delta_i>0\}.
$$

Train a logistic gate with the same 19 features, weighting each example by
$|\Delta_i|$. Consequently an expensive mistake matters more than a cheap one:

$$
\mathcal L=\sum_{i:\Delta_i\ne0}|\Delta_i|
\big[-y_i\log p_i-(1-y_i)\log(1-p_i)\big].
$$

Fit on training lists; choose a threshold on separate calibration lists using
the actual complete policy cost, including prediction. Freeze both before
generating fresh test lists. The score is a cost-sensitive decision score, not
a calibrated probability of YES, NO, or portfolio completion.

Compare always, never, a simple geometric rule, and the learned gate with
matched acquisition. Also include a lean baseline that avoids discovery and a
direct MITM control. Every policy first reuses all five existing exact cores.
Only exact checks/solvers produce answers; every online cost is charged.

This first gate operates **once at the root, after discovering geometry**.
It tests whether to run an eligible DP, not whether to acquire geometry or
recompute features inside search. Work-trained decisions are evaluated under
both work and separately measured live-time budgets.

[Frozen protocol](PROTOCOL.md) ·
[Results and limitations](../../COST_GATE_FINDINGS.md) ·
[Previous feature overview](../02_literature_classifier/OVERVIEW.md).
