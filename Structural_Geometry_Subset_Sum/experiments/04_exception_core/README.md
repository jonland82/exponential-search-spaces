# A geometric core with a few exceptional weights

The failure diagnosis found narrow geometric structure hidden behind a few
weights with very large residuals. This experiment adds an exact route for
those inputs: **build the retained core once, then query shifted targets**.

For a blind decomposition $u_i=Mp_i+r_i$, split indices into core $K$ and
exceptions $E$. Build the reachable $(q,s)$ table for $K$. For each exceptional
assignment, ask whether that same table reaches

$$
Mq+s=v-\sum_{i\in E}u_ix_i.
$$

Four or five exceptions require 16-32 shifted-target queries. The table and
witness history are reused. The intended accounting is

$$
T\le F+C_{\rm core}+2^{|E|}Q_{\rm query}+V,
$$

including discovery, one core construction, queries and witness verification.
The implementation permits at most nine exceptions, bounded logical table/
history size and a conservative work gate. Exhaustion returns unresolved.

This extends Paper V's exception-to-tractable-core idea to the literature-
inspired geometry. No classifier is required: exact structures provide every
answer. It is a specialized solver route, not a new general complexity bound.

Compare root geometry, new discovery without solving, full core reuse, a lean
portfolio and direct MITM. Fresh lists supply the primary evidence; the old
115 failures are replayed only as an explicitly retrospective diagnostic.

Use the experimental exact solver from the repository root:

```python
from Structural_Geometry_Subset_Sum.compat import input_length
from Structural_Geometry_Subset_Sum.exception_solver import solve_exceptions

result = solve_exceptions(
    weights, target, "reuse",
    max_work=32 * input_length(weights, target), seconds=0.020,
)
```

Its status is `yes`, `no`, or `unresolved`; indexed witnesses accompany
constructed YES answers, while the existing bitset fallback is decision-only.

[Protocol](PROTOCOL.md) · [Exactness and cost](THEORY.md) ·
[Measured findings](../../EXCEPTION_FINDINGS.md) ·
[Motivating failure diagnosis](../../FAILURE_FINDINGS.md).
