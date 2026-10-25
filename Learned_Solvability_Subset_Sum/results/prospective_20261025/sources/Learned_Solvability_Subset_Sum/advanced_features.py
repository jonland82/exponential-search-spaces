"""Progression-aware fifth distance and exact target-dependent reductions.

The original five-feature extractor remains unchanged for historical replay.
No labels, oracle data, or fitted parameters are used by these extractors.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from math import gcd
from time import perf_counter

from features import FeatureConfig, Features, extract, query


@dataclass(frozen=True)
class Progression:
    indices: tuple[int, ...]
    start: int
    step: int


@dataclass(frozen=True)
class AdvancedFeatures:
    base: Features
    progression: Progression | None
    candidate_steps: tuple[int, ...]
    work: int
    seconds: float

    @property
    def values(self):
        fifth = (self.base.values[4] if self.progression is None else
                 len(self.base.weights) - len(self.progression.indices))
        return self.base.values[:4] + (fifth,)


def extract_advanced(weights, config=FeatureConfig(), *, max_steps=16, base=None):
    """Choose the larger of an interval core and a certified AP weight core.

    Trial steps are the most frequent consecutive distinct-value gaps, ties
    increasing by step, plus step 1. This bounded candidate search need not find
    the minimum deletion distance to the union of these representations.
    Passing a matching base permits reuse; its work/time is still charged.
    """
    if type(max_steps) is not int or max_steps < 1:
        raise ValueError("max_steps must be a positive integer")
    raw = tuple(weights)
    reused = base is not None
    started = perf_counter()
    if base is None:
        base = extract(raw, config)
    elif tuple(w * base.divisor for w in base.weights) != raw:
        raise ValueError("base features do not match weights")
    value_index = {}
    for i, weight in enumerate(base.weights):
        value_index.setdefault(weight, i)
    values = sorted(value_index)
    gaps = Counter(b - a for a, b in zip(values, values[1:]))
    steps = tuple(dict.fromkeys([1] + sorted(gaps, key=lambda d: (-gaps[d], d))[:max_steps - 1]))
    work = base.work + 3 * len(raw) + 2 * len(raw) * max(1, len(raw).bit_length())
    best = None
    best_size = len(raw) - base.values[4]
    for step in steps:
        for start in values:
            work += 1
            if start - step in value_index:
                continue
            chain, value = [], start
            while value in value_index:
                work += 1
                chain.append(value_index[value])
                value += step
            if len(chain) > best_size:
                best_size = len(chain)
                best = Progression(tuple(chain), start, step)
    elapsed = perf_counter() - started + (base.seconds if reused else 0)
    return AdvancedFeatures(base, best, steps, work, elapsed)


def progression_query(weights, progression, target):
    """Exact AP-core query in the units of weights, with indexed witness.

    For k choices, reachable index totals are precisely every integer from
    k(k-1)/2 through k(2m-k-1)/2. The corresponding sums form one progression.
    """
    if target < 0:
        return None
    m = len(progression.indices)
    for count in range(m + 1):
        remainder = target - count * progression.start
        if remainder < 0 or remainder % progression.step:
            continue
        index_sum = remainder // progression.step
        low = count * (count - 1) // 2
        high = count * (2 * m - count - 1) // 2
        if not low <= index_sum <= high:
            continue
        selected = list(range(count))
        surplus = index_sum - low
        for position in range(count - 1, -1, -1):
            delta = min(surplus, m - count + position - selected[position])
            selected[position] += delta
            surplus -= delta
        witness = tuple(progression.indices[i] for i in selected)
        if surplus or sum(weights[i] for i in witness) != target:
            raise AssertionError("invalid progression witness")
        return witness
    return None


def query_advanced(features, dimension, target):
    if type(target) is not int:
        raise ValueError("integer target required")
    if dimension != 4 or features.progression is None:
        return query(features.base, dimension, target)
    if target % features.base.divisor:
        return None
    return progression_query(features.base.weights, features.progression,
                             target // features.base.divisor)


@dataclass(frozen=True)
class Kernel:
    original_weights: tuple[int, ...]
    original_target: int
    weights: tuple[int, ...]
    target: int
    indices: tuple[int, ...]
    forced: tuple[int, ...]
    complemented: bool
    status: str
    reason: str
    witness: tuple[int, ...] | None
    work: int
    seconds: float


def lift_witness(kernel, witness):
    chosen = set(kernel.forced)
    chosen.update(kernel.indices[i] for i in witness)
    if kernel.complemented:
        chosen = set(range(len(kernel.original_weights))) - chosen
    return tuple(sorted(chosen))


def reduce_instance(weights, target):
    """Exact equivalence reductions; no subset enumeration or learned choices.

    Complement once, discard overweight items, and force an item when all other
    retained items together cannot reach the target. Repeat to a fixed point.
    Gcd and range contradictions, and a zero remainder, solve some cases exactly.
    A solved kernel uses the empty residual list. Its five distances are zero;
    report these shortcut cases separately from unresolved-kernel ML evaluation.
    """
    started = perf_counter()
    original = tuple(weights)
    if type(target) is not int or any(type(w) is not int or w <= 0 for w in original):
        raise ValueError("positive integer weights and integer target required")
    remaining_target = target
    total = sum(original)
    work = 2 * len(original) + 1
    complemented = False
    forced = []
    active = list(range(len(original)))

    def finish(status, reason):
        kernel = Kernel(original, target,
                        tuple(original[i] for i in active) if status == "unresolved" else (),
                        remaining_target if status == "unresolved" else 0,
                        tuple(active) if status == "unresolved" else (),
                        tuple(forced), complemented, status, reason, None,
                        work, perf_counter() - started)
        if status == "yes":
            witness = lift_witness(kernel, ())
            if sum(original[i] for i in witness) != target:
                raise AssertionError("invalid forced/complement witness")
            return Kernel(**{**kernel.__dict__, "witness": witness})
        return kernel

    if target < 0 or target > total:
        return finish("no", "range")
    if target > total // 2:
        complemented = True
        remaining_target = total - target
    while True:
        work += 1
        if remaining_target == 0:
            return finish("yes", "forced_or_boundary")
        retained = []
        for i in active:
            work += 1
            if original[i] <= remaining_target:
                retained.append(i)
        active = retained
        remaining_total, divisor = 0, 0
        for i in active:
            work += 1
            remaining_total += original[i]
            divisor = gcd(divisor, original[i])
        if remaining_target > remaining_total:
            return finish("no", "filtered_range")
        if divisor and remaining_target % divisor:
            return finish("no", "filtered_gcd")
        forced_now = []
        for i in active:
            work += 1
            if remaining_total - original[i] < remaining_target:
                forced_now.append(i)
        if not forced_now:
            return finish("unresolved", "fixed_point")
        forced_set = set(forced_now)
        active = [i for i in active if i not in forced_set]
        forced.extend(forced_now)
        remaining_target -= sum(original[i] for i in forced_now)
        work += len(active) + 2 * len(forced_now)
        if remaining_target < 0:
            return finish("no", "incompatible_forced_choices")
