"""Witness-preserving approximation to closest subset sum, using integer arithmetic.

Each summary (R, E) satisfies: for every true sum s there is an actual
subset sum r in R with r <= s <= r + E. No probability model is needed.
"""

from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass
from heapq import merge
from typing import Iterable


METHODS = ("paired_additive", "sequential_additive", "trimmed_multiplicative", "exact_mitm")
DEFAULT_MAX_STATES = 65_536
Representative = tuple[int, int]  # actual sum, bit mask in the ORIGINAL item order


@dataclass
class Certificate:
    lower: int
    upper: int
    subset_sum: int
    subset_mask: int
    tolerance: int
    status: str
    reason: str
    stats: dict

    @property
    def width(self) -> int:
        return self.upper - self.lower

    def as_dict(self) -> dict:
        return {
            "lower": self.lower,
            "upper": self.upper,
            "width": self.width,
            "subset_sum": self.subset_sum,
            "subset_indices": [i for i in range(self.subset_mask.bit_length()) if self.subset_mask >> i & 1],
            "tolerance": self.tolerance,
            "status": self.status,
            "reason": self.reason,
            **self.stats,
        }


class _Finished(Exception):
    pass


class _StateLimit(Exception):
    pass


class _Context:
    def __init__(self, weights: list[int], target: int, tolerance: int, max_states: int):
        self.target = target
        self.tolerance = tolerance
        self.total = sum(weights)
        self.full_mask = (1 << len(weights)) - 1
        self.max_states = max_states
        self.best: Representative = (0, 0)
        self.upper = abs(target)
        self.stats = {
            "generated_candidates": 0,
            "duplicate_merges": 0,
            "approximate_merges": 0,
            "peak_summary_states": 1,
            "summary_steps": 0,
            "pair_queries": 0,
            "left_states": 0,
            "right_states": 0,
            "coverage_error": 0,
            "coverage_complete": False,
        }
        self.consider((self.total, self.full_mask))

    def consider(self, rep: Representative, *, complement: bool = True) -> None:
        value, mask = rep
        distance = abs(value - self.target)
        if distance < self.upper:
            self.upper, self.best = distance, rep
        if complement:
            value, mask = self.total - value, self.full_mask ^ mask
            distance = abs(value - self.target)
            if distance < self.upper:
                self.upper, self.best = distance, (value, mask)

    def check_witness(self) -> None:
        if self.upper <= self.tolerance:
            raise _Finished

    def result(self, lower: int, status: str, reason: str) -> Certificate:
        assert 0 <= lower <= self.upper
        if status == "certified":
            assert self.upper - lower <= self.tolerance
        return Certificate(lower, self.upper, *self.best, self.tolerance, status, reason, self.stats.copy())


def trim_sorted(
    candidates: Iterable[Representative],
    *,
    additive_step: int,
    ratio_numerator: int,
    ratio_denominator: int,
    context: _Context,
) -> tuple[list[Representative], int]:
    """Greedy downward trimming; return the OBSERVED largest discarded gap.

    ratio_numerator > 0 selects multiplicative trimming. Otherwise use
    additive_step. Duplicate values are merged even when no error is allowed.
    """
    kept: list[Representative] = []
    largest_gap = 0
    previous_value = None
    for value, mask in candidates:
        context.stats["generated_candidates"] += 1
        if previous_value == value:
            context.stats["duplicate_merges"] += 1
            continue
        previous_value = value
        gap = value - kept[-1][0] if kept else 0
        discard = bool(kept) and (
            gap * ratio_denominator <= kept[-1][0] * ratio_numerator
            if ratio_numerator > 0 else gap <= additive_step
        )
        if discard:
            largest_gap = max(largest_gap, gap)
            context.stats["approximate_merges"] += 1
        else:
            if len(kept) >= context.max_states:
                raise _StateLimit
            kept.append((value, mask))
            context.stats["peak_summary_states"] = max(context.stats["peak_summary_states"], len(kept))
    return kept, largest_gap


def _build_summary(
    items: list[tuple[int, int]],
    context: _Context,
    *,
    additive_step: int = 0,
    multiplicative: bool = False,
    total_items: int,
) -> tuple[list[Representative], int]:
    reps: list[Representative] = [(0, 0)]
    error = 0
    for weight, bit in items:
        shifted = ((value + weight, mask | bit) for value, mask in reps)
        reps, dropped_gap = trim_sorted(
            merge(reps, shifted),
            additive_step=additive_step,
            ratio_numerator=context.tolerance if multiplicative else 0,
            ratio_denominator=max(1, total_items * context.total),
            context=context,
        )
        error += dropped_gap
        context.stats["summary_steps"] += 1
        # Every representative is a valid witness even before all items are used.
        # Complements are also valid witnesses in the FULL original item set.
        for goal in (context.target, context.total - context.target):
            index = bisect_left(reps, (goal, -1))
            for candidate in (index - 1, index):
                if 0 <= candidate < len(reps):
                    context.consider(reps[candidate])
        context.check_witness()
    return reps, error


def _greedy(items: list[tuple[int, int]], context: _Context) -> None:
    for goal in (context.target, context.total - context.target):
        value = mask = 0
        for weight, bit in items:
            context.consider((value + weight, mask | bit))
            if value + weight <= goal:
                value, mask = value + weight, mask | bit
                context.consider((value, mask))
    context.check_witness()


def _interval_distance(target: int, value: int, error: int) -> int:
    return max(value - target, target - value - error, 0)


def _query_pair(
    left: list[Representative], right: list[Representative], error: int, context: _Context
) -> int:
    """Linear staircase search for nearest pair and nearest covering interval.

    The largest pair sum <= target and smallest >= target suffice for both
    quantities. The usual two-pointer path visits such predecessor/successor
    sums, so it also minimizes distance to [pair_sum, pair_sum + error].
    """
    i, j = 0, len(right) - 1
    lower = context.total + abs(context.target) + error + 1
    while i < len(left) and j >= 0:
        value = left[i][0] + right[j][0]
        mask = left[i][1] | right[j][1]
        context.stats["pair_queries"] += 1
        lower = min(lower, _interval_distance(context.target, value, error))
        context.consider((value, mask))
        context.check_witness()
        if value < context.target:
            i += 1
        else:
            j -= 1
    return lower


def solve(
    weights: list[int],
    target: int,
    tolerance: int,
    method: str = "paired_additive",
    *,
    greedy: bool = True,
    max_states: int = DEFAULT_MAX_STATES,
) -> Certificate:
    """Return certified bounds, or honest partial bounds if the state cap is hit.

    Tolerance is an ABSOLUTE nonnegative integer distance. Both under- and
    overshooting sums are allowed. exact_mitm uses exact half summaries but
    may stop at a witnessed distance <= tolerance, as may all other methods.
    No truth labels or reference optima are used by any solver.
    """
    if method not in METHODS:
        raise ValueError(f"unknown method: {method}")
    if not isinstance(target, int) or not isinstance(tolerance, int) or tolerance < 0:
        raise ValueError("target must be an integer and tolerance a nonnegative integer")
    if any(not isinstance(weight, int) or weight <= 0 for weight in weights):
        raise ValueError("weights must be positive integers")
    if max_states < 1:
        raise ValueError("max_states must be positive")
    context = _Context(weights, target, tolerance, max_states)
    if target <= 0 or target >= context.total:
        return context.result(context.upper, "certified", "outside_range")
    items = [(weight, 1 << i) for i, weight in sorted(enumerate(weights), key=lambda item: (-item[1], item[0]))]
    reason = "endpoint_witness"
    try:
        context.check_witness()
        if greedy:
            reason = "greedy_witness"
            _greedy(items, context)
        reason = "summary_witness"
        step = tolerance // max(1, len(weights))
        if method in ("sequential_additive", "trimmed_multiplicative"):
            reps, error = _build_summary(
                items, context, additive_step=step,
                multiplicative=method == "trimmed_multiplicative", total_items=len(weights),
            )
            context.stats["coverage_error"] = error
            context.stats["coverage_complete"] = True
            context.stats["left_states"] = len(reps)
            lower = min(_interval_distance(target, value, error) for value, _ in reps)
        else:
            middle = len(items) // 2
            half_step = step if method == "paired_additive" else 0
            left, left_error = _build_summary(items[:middle], context, additive_step=half_step, total_items=len(weights))
            context.stats["left_states"] = len(left)
            right, right_error = _build_summary(items[middle:], context, additive_step=half_step, total_items=len(weights))
            context.stats["right_states"] = len(right)
            error = left_error + right_error
            context.stats["coverage_error"] = error
            context.stats["coverage_complete"] = True
            reason = "paired_witness"
            lower = _query_pair(left, right, error, context)
        return context.result(lower, "certified", "coverage_interval")
    except _Finished:
        return context.result(0, "certified", reason)
    except _StateLimit:
        return context.result(0, "state_limit", "summary_state_limit")


def brute_force_distance(weights: list[int], target: int) -> int:
    """Independent Gray-code oracle: enumerate every subset without summaries."""
    best, value, previous = abs(target), 0, 0
    for k in range(1, 1 << len(weights)):
        gray = k ^ (k >> 1)
        changed = gray ^ previous
        bit = changed.bit_length() - 1
        value += weights[bit] if gray & changed else -weights[bit]
        best = min(best, abs(value - target))
        previous = gray
    return best
