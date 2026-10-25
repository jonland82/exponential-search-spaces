"""Costed, deterministic one-swap alternatives to the maximum greedy core."""

from collections import Counter
from math import prod
from time import perf_counter

from structural_subset_sum import (
    Core, Limits, _Budget, _Limit, _core, _exception_sums, _greedy,
    _inputs, _mask_indices, _root_answer, verify_core,
)


def _rank(weights, core, budget):
    budget.tick(len(weights))
    counts = Counter(weights[i] for i in core.exceptions)
    cap = prod(count + 1 for count in counts.values())
    return cap, core.total, tuple(weights[i] for i in core.indices)


def candidate_pool(weights, base, budget, pool_size=4):
    """Return base plus at most pool_size-1 best distinct-valued one-swaps.

    All retained cores have the same maximum cardinality. Ranking minimizes the
    multiplicity selection cap, then core total, then core weight sequence.
    Discovery and rejection of candidates are part of the budget.
    """
    base_rank = _rank(weights, base, budget)
    alternatives = []
    seen = {base_rank[2]}
    for remove in base.indices:
        for add in base.exceptions:
            budget.tick()
            budget.stats["swap_pairs_considered"] += 1
            if weights[remove] == weights[add]:
                continue
            indices = tuple(sorted(
                (i for i in base.indices if i != remove),
                key=lambda i: (weights[i], i),
            ))
            indices = tuple(sorted(indices + (add,), key=lambda i: (weights[i], i)))
            signature = tuple(weights[i] for i in indices)
            if signature in seen:
                continue
            seen.add(signature)
            chosen = set(indices)
            exceptions = tuple(
                i for i in sorted(range(len(weights)), key=lambda i: (weights[i], i))
                if i not in chosen
            )
            candidate = Core(indices, exceptions, sum(weights[i] for i in indices))
            budget.tick(len(weights))
            budget.stats["candidate_verifications"] += 1
            if not verify_core(weights, candidate):
                continue
            budget.stats["valid_alternatives"] += 1
            rank = _rank(weights, candidate, budget)
            alternatives.append((rank, candidate))
            alternatives.sort(key=lambda entry: entry[0])
            del alternatives[max(0, pool_size - 1):]
    pool = [(base_rank, base), *alternatives]
    pool.sort(key=lambda entry: entry[0])
    budget.stats["candidate_pool_size"] = len(pool)
    return pool


class _RetainedSupportBudget:
    """Count the best retained support while a second support is built."""
    def __init__(self, budget, retained):
        self.budget = budget
        self.retained = retained
        self.stats = budget.stats

    def tick(self, amount=1):
        self.budget.tick(amount)

    def states(self, count):
        self.budget.states(self.retained + count)


def solve_selected(weights, target, *, policy="multiplicity", limits=None):
    """Exact distinct-sum solver with all core-selection costs included.

    multiplicity: select the best multiplicity-cap-ranked core from the pool.
    support: construct up to four supports, select minimum M, and reuse it.
    No target labels or oracle information are used in either policy.
    """
    if policy not in ("multiplicity", "support"):
        raise ValueError("policy must be 'multiplicity' or 'support'")
    budget = _Budget(limits or Limits())
    weights = _inputs(weights, target)
    budget.stats.update(
        selection_seconds=0.0, swap_pairs_considered=0,
        candidate_verifications=0, valid_alternatives=0,
        candidate_pool_size=0, support_probes=0, support_probe_sizes=[],
        probe_generation_seconds=0.0, selection_complete=False,
        initial_core_indices=None, selected_core_changed=False,
    )
    core = None
    try:
        answer = _root_answer(weights, target, budget)
        if answer is not None:
            return budget.finish(*answer)
        core = budget.phase("discovery", lambda: _core(weights, budget))
        initial = core
        budget.stats["initial_core_indices"] = initial.indices

        def verification():
            budget.tick(len(weights))
            if not verify_core(weights, core):
                raise AssertionError("initial core verification failed")

        budget.phase("verification", verification)

        def selection():
            pool = candidate_pool(weights, initial, budget)
            if policy == "multiplicity":
                return pool[0][1], None
            best_core, best_sums, best_key = None, None, None
            for rank, candidate in pool:
                budget.stats["distinct_exception_sums"] = None
                budget.stats["distinct_sums_complete"] = False
                retained = 0 if best_sums is None else len(best_sums)
                start = perf_counter()
                try:
                    sums = _exception_sums(
                        weights, candidate.exceptions,
                        _RetainedSupportBudget(budget, retained),
                    )
                finally:
                    budget.stats["probe_generation_seconds"] += perf_counter() - start
                budget.stats["support_probes"] += 1
                budget.stats["support_probe_sizes"].append(len(sums))
                key = (len(sums), rank)
                if best_key is None or key < best_key:
                    best_core, best_sums, best_key = candidate, sums, key
                # Drop a losing support before the next allocation. When it won,
                # best_sums retains it and this only removes the temporary name.
                del sums
            budget.stats["distinct_exception_sums"] = len(best_sums)
            budget.stats["distinct_sums_complete"] = True
            return best_core, best_sums

        core, sums = budget.phase("selection", selection)
        budget.stats["selection_complete"] = True
        budget.stats["selected_core_changed"] = core.indices != initial.indices
        if sums is None:
            sums = budget.phase(
                "generation", lambda: _exception_sums(weights, core.exceptions, budget)
            )

        def query():
            for value, mask in sums:
                witness = _greedy(weights, core, target - value, budget)
                if witness is not None:
                    return tuple(sorted(witness + _mask_indices(mask)))
            return None

        witness = budget.phase("query", query)
        return budget.finish(
            "yes" if witness is not None else "no", witness,
            "witness" if witness is not None else "exhausted", core,
        )
    except _Limit as exc:
        # An unfinished selector has not established its final selected M.
        if not budget.stats["selection_complete"]:
            budget.stats["distinct_exception_sums"] = None
            budget.stats["distinct_sums_complete"] = False
        return budget.finish("unresolved", None, str(exc), core)
