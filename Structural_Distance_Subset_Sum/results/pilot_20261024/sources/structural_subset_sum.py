"""Exact positive-integer subset sum using a maximum superincreasing core.

No third-party dependencies. Budgets yield "unresolved", never a false NO.
Work counts explicit scan, generation, and query steps; sorting is timed but
its internal comparisons are not included in that counter.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from math import gcd
from time import perf_counter
from typing import Callable, Iterable


@dataclass(frozen=True)
class Limits:
    max_work: int = 1_000_000
    max_states: int = 262_144
    max_seconds: float | None = None
    max_bitset_bits: int = 8_000_000

    def __post_init__(self) -> None:
        for value in (self.max_work, self.max_states, self.max_bitset_bits):
            if type(value) is not int or value < 1:
                raise ValueError("integer resource limits must be positive")
        if self.max_seconds is not None and not (
            isinstance(self.max_seconds, (int, float))
            and 0 < self.max_seconds < float("inf")
        ):
            raise ValueError("max_seconds must be finite and positive, or None")


@dataclass(frozen=True)
class Core:
    # Indices are in increasing (weight, original index) order.
    indices: tuple[int, ...]
    exceptions: tuple[int, ...]
    total: int


@dataclass
class Result:
    status: str
    witness: tuple[int, ...] | None
    reason: str
    core_indices: tuple[int, ...] | None
    exceptional_indices: tuple[int, ...] | None
    stats: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


class _Limit(Exception):
    pass


class _Budget:
    def __init__(self, limits: Limits):
        self.limits = limits
        self.started = perf_counter()
        self.work = 0
        self.peak_states = 0
        self.stats = {
            "discovery_seconds": 0.0,
            "verification_seconds": 0.0,
            "generation_seconds": 0.0,
            "query_seconds": 0.0,
            "exception_items_processed": 0,
            "distinct_exception_sums": None,
            "distinct_sums_complete": False,
            "generation_steps": 0,
            "duplicate_sums_merged": 0,
            "exception_selections": 0,
            "core_queries": 0,
            "range_rejections": 0,
            "core_steps": 0,
        }

    def tick(self, amount: int = 1) -> None:
        if self.work + amount > self.limits.max_work:
            raise _Limit("work_limit")
        self.work += amount
        self.check_time()

    def check_time(self) -> None:
        if (
            self.limits.max_seconds is not None
            and perf_counter() - self.started >= self.limits.max_seconds
        ):
            raise _Limit("time_limit")

    def states(self, count: int) -> None:
        if count > self.limits.max_states:
            raise _Limit("state_limit")
        self.peak_states = max(self.peak_states, count)
        self.check_time()

    def phase(self, name: str, action: Callable):
        start = perf_counter()
        try:
            return action()
        finally:
            self.stats[name + "_seconds"] += perf_counter() - start

    def finish(self, status, witness, reason, core=None) -> Result:
        self.stats.update(
            work=self.work,
            peak_states=self.peak_states,
            total_seconds=perf_counter() - self.started,
            k=None if core is None else len(core.exceptions),
        )
        return Result(
            status, witness, reason,
            None if core is None else core.indices,
            None if core is None else core.exceptions,
            self.stats,
        )


def _inputs(weights: Iterable[int], target: int) -> tuple[int, ...]:
    weights = tuple(weights)
    if type(target) is not int or any(type(w) is not int or w <= 0 for w in weights):
        raise ValueError("weights must be positive integers and target an integer")
    return weights


def _core(weights: tuple[int, ...], budget: _Budget) -> Core:
    ordered = sorted(range(len(weights)), key=lambda i: (weights[i], i))
    budget.check_time()
    selected, exceptions, total = [], [], 0
    for index in ordered:
        budget.tick()
        if weights[index] > total:
            selected.append(index)
            total += weights[index]
        else:
            exceptions.append(index)
    return Core(tuple(selected), tuple(exceptions), total)


def verify_core(weights: Iterable[int], core: Core) -> bool:
    """Verify a full indexed partition and the core's defining inequalities."""
    weights = _inputs(weights, 0)
    indices = core.indices + core.exceptions
    if (
        len(indices) != len(weights)
        or any(type(i) is not int or not 0 <= i < len(weights) for i in indices)
        or len(set(indices)) != len(weights)
    ):
        return False
    total = 0
    for index in core.indices:
        if weights[index] <= total:
            return False
        total += weights[index]
    return total == core.total


def find_core(weights: Iterable[int]) -> Core:
    weights = _inputs(weights, 0)
    # This standalone polynomial procedure is unrestricted.
    budget = _Budget(Limits(max_work=max(1, len(weights))))
    return _core(weights, budget)


def _root_answer(weights, target, budget):
    total, divisor = 0, 0
    for weight in weights:
        budget.tick()
        total += weight
        divisor = gcd(divisor, weight)
    if target == 0:
        return "yes", (), "zero_target"
    if target < 0 or target > total:
        return "no", None, "root_range"
    if divisor and target % divisor:
        return "no", None, "root_gcd"
    return None


def _greedy(weights, core, target, budget):
    budget.tick()
    budget.stats["core_queries"] += 1
    if target < 0 or target > core.total:
        budget.stats["range_rejections"] += 1
        return None
    chosen = []
    remainder = target
    for index in reversed(core.indices):
        budget.tick()
        budget.stats["core_steps"] += 1
        if weights[index] <= remainder:
            remainder -= weights[index]
            chosen.append(index)
    return tuple(chosen) if remainder == 0 else None


def _exception_sums(weights, indices, budget):
    # Every representative retains one original-index mask. The two lists
    # coexist during merging, so the cap counts both, not just output size.
    sums = [(0, 0)]
    budget.states(1)
    for index in indices:
        weight = weights[index]
        output = []
        left = right = 0
        while left < len(sums) or right < len(sums):
            budget.tick()
            budget.stats["generation_steps"] += 1
            a = sums[left][0] if left < len(sums) else None
            b = sums[right][0] + weight if right < len(sums) else None
            if b is None or (a is not None and a < b):
                candidate = sums[left]
                left += 1
            elif a is None or b < a:
                candidate = (b, sums[right][1] | (1 << index))
                right += 1
            else:
                candidate = sums[left]
                left += 1
                right += 1
                budget.stats["duplicate_sums_merged"] += 1
            budget.states(len(sums) + len(output) + 1)
            output.append(candidate)
        sums = output
        budget.stats["exception_items_processed"] += 1
    budget.stats["distinct_exception_sums"] = len(sums)
    budget.stats["distinct_sums_complete"] = True
    return sums


def _mask_indices(mask):
    indices = []
    while mask:
        bit = mask & -mask
        indices.append(bit.bit_length() - 1)
        mask ^= bit
    return tuple(indices)


def solve(
    weights: Iterable[int], target: int, *,
    method: str = "distinct", limits: Limits | None = None,
) -> Result:
    """Solve exactly, or report unresolved when a declared budget is spent.

    "distinct" builds all distinct exceptional sums before querying the core.
    "enumerate" queries selections in Gray-code order, stopping on a witness.
    M is reported only when the full distinct-sum construction has finished.
    Peak states counts live residual records, excluding input/core storage.
    """
    budget = _Budget(limits or Limits())
    weights = _inputs(weights, target)
    if method not in ("distinct", "enumerate"):
        raise ValueError("method must be 'distinct' or 'enumerate'")
    core = None
    try:
        answer = _root_answer(weights, target, budget)
        if answer is not None:
            return budget.finish(*answer)
        core = budget.phase("discovery", lambda: _core(weights, budget))

        def verification():
            budget.tick(len(weights))
            if not verify_core(weights, core):
                raise AssertionError("core verification failed")
            budget.check_time()

        budget.phase("verification", verification)
        if method == "distinct":
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
        else:
            def enumerate_query():
                budget.states(1)
                value = previous_gray = 0
                for step in range(1 << len(core.exceptions)):
                    budget.tick()
                    gray = step ^ (step >> 1)
                    if step:
                        changed = gray ^ previous_gray
                        offset = changed.bit_length() - 1
                        delta = weights[core.exceptions[offset]]
                        value += delta if gray & changed else -delta
                    previous_gray = gray
                    budget.stats["exception_selections"] += 1
                    witness = _greedy(weights, core, target - value, budget)
                    if witness is not None:
                        extras = tuple(
                            index for offset, index in enumerate(core.exceptions)
                            if gray >> offset & 1
                        )
                        return tuple(sorted(witness + extras))
                return None

            witness = budget.phase("query", enumerate_query)
        return budget.finish(
            "yes" if witness is not None else "no", witness,
            "witness" if witness is not None else "exhausted", core,
        )
    except _Limit as exc:
        return budget.finish("unresolved", None, str(exc), core)


def solve_mitm(weights, target, *, limits: Limits | None = None) -> Result:
    """Independent baseline: indexed half sums, with duplicate sums merged."""
    budget = _Budget(limits or Limits())
    weights = _inputs(weights, target)
    try:
        answer = _root_answer(weights, target, budget)
        if answer is not None:
            return budget.finish(*answer)
        middle = len(weights) // 2

        def build(indices, other_size=0):
            sums = {0: 0}
            budget.states(other_size + 1)
            for index in indices:
                # Snapshot shares entries; the state cap also counts the
                # snapshot's live references during this update.
                old = list(sums.items())
                budget.states(other_size + len(sums) + len(old))
                for value, mask in old:
                    budget.tick()
                    candidate = value + weights[index]
                    if candidate <= target and candidate not in sums:
                        budget.states(other_size + len(sums) + len(old) + 1)
                        sums[candidate] = mask | (1 << index)
            return sums

        def generate():
            left = build(range(middle))
            right = build(range(middle, len(weights)), len(left))
            return left, right

        left, right = budget.phase("generation", generate)

        def query():
            for value, mask in left.items():
                budget.tick()
                other = right.get(target - value)
                if other is not None:
                    return _mask_indices(mask | other)
            return None

        witness = budget.phase("query", query)
        return budget.finish(
            "yes" if witness is not None else "no", witness,
            "witness" if witness is not None else "exhausted",
        )
    except _Limit as exc:
        return budget.finish("unresolved", None, str(exc))


def solve_dfs(weights, target, *, limits: Limits | None = None) -> Result:
    """Memoized bounded DFS, implemented with a stack to avoid recursion caps."""
    budget = _Budget(limits or Limits())
    weights = _inputs(weights, target)
    try:
        answer = _root_answer(weights, target, budget)
        if answer is not None:
            return budget.finish(*answer)
        ordered = sorted(range(len(weights)), key=lambda i: (-weights[i], i))
        totals = [0] * (len(weights) + 1)
        for offset in range(len(weights) - 1, -1, -1):
            budget.tick()
            totals[offset] = totals[offset + 1] + weights[ordered[offset]]
        seen = set()
        stack = [(0, target, 0)]
        budget.states(1)
        witness = None
        start = perf_counter()
        try:
            while stack:
                budget.tick()
                offset, remainder, mask = stack.pop()
                if remainder == 0:
                    witness = _mask_indices(mask)
                    break
                if remainder < 0 or remainder > totals[offset]:
                    continue
                key = (offset, remainder)
                if key in seen:
                    continue
                budget.states(len(seen) + len(stack) + 1)
                seen.add(key)
                index = ordered[offset]
                budget.states(len(seen) + len(stack) + 2)
                stack.append((offset + 1, remainder, mask))
                stack.append((
                    offset + 1, remainder - weights[index], mask | (1 << index)
                ))
        finally:
            budget.stats["query_seconds"] += perf_counter() - start
        return budget.finish(
            "yes" if witness is not None else "no", witness,
            "witness" if witness is not None else "exhausted",
        )
    except _Limit as exc:
        return budget.finish("unresolved", None, str(exc))


def solve_bitset(weights, target, *, limits: Limits | None = None) -> Result:
    """Decision-only integer-bitset baseline; no witness storage is charged."""
    budget = _Budget(limits or Limits())
    weights = _inputs(weights, target)
    try:
        answer = _root_answer(weights, target, budget)
        if answer is not None:
            return budget.finish(*answer)
        if target + 1 > budget.limits.max_bitset_bits:
            raise _Limit("bitset_limit")
        # Three target-width integers can coexist. This is a width limit,
        # not a claim that Python allocation has an exact byte cap.
        budget.stats["bitset_width_bits"] = target + 1
        start = perf_counter()
        try:
            bits = 1
            cap = (1 << (target + 1)) - 1
            for weight in weights:
                budget.tick()
                # Slice the source first so a huge weight cannot allocate
                # a correspondingly huge temporary shifted integer.
                if weight <= target:
                    source = bits & (cap >> weight)
                    bits |= source << weight
            reachable = bool(bits >> target & 1)
        finally:
            budget.stats["query_seconds"] += perf_counter() - start
        budget.check_time()
        return budget.finish(
            "yes" if reachable else "no", None, "decision_only"
        )
    except _Limit as exc:
        return budget.finish("unresolved", None, str(exc))
