"""Five certified distance-to-easy features; no training labels are consulted.

The last two distances are constructive upper bounds, not optimal deletions.
Operation counts are instrumentation units, not CPU instructions or bit costs.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from itertools import product
from math import gcd
from time import perf_counter


FEATURE_NAMES = ("superincreasing", "coverage", "few_values", "small_support", "interval_union")


@dataclass(frozen=True)
class FeatureConfig:
    distinct_values: int = 2
    support_cap: int = 128
    interval_cap: int = 8

    def __post_init__(self):
        if any(type(v) is not int or v < 1 for v in (
            self.distinct_values, self.support_cap, self.interval_cap)):
            raise ValueError("feature caps must be positive integers")


@dataclass(frozen=True)
class Certificate:
    name: str
    indices: tuple[int, ...]
    exceptions: tuple[int, ...]
    exact_distance: bool
    # For support: ((sum, original-index mask), ...).
    support: tuple[tuple[int, int], ...] = ()
    # Exact reachable intervals after each accepted item, including empty prefix.
    prefixes: tuple[tuple[tuple[int, int], ...], ...] = ()


@dataclass(frozen=True)
class Features:
    weights: tuple[int, ...]
    divisor: int
    certificates: tuple[Certificate, ...]
    work: int
    seconds: float

    @property
    def values(self):
        return tuple(len(c.exceptions) for c in self.certificates)


def input_length(weights, target):
    """Explicit length proxy: self-delimiting positive weights and signed target.

    Each integer uses 2*bit_length+1 bits; a sign bit is added for the target.
    This is polynomially equivalent to ordinary binary instance encodings.
    """
    return (2 * len(weights).bit_length() + 1
            + sum(2 * w.bit_length() + 1 for w in weights)
            + 2 * abs(target).bit_length() + 2)


def _contains(intervals, target):
    return any(lo <= target <= hi for lo, hi in intervals)


def _extend_intervals(intervals, weight):
    """Linear merge of S and S+weight, without expanding covered integers."""
    left = right = work = 0
    out = []
    while left < len(intervals) or right < len(intervals):
        work += 1
        a = intervals[left] if left < len(intervals) else None
        b = ((intervals[right][0] + weight, intervals[right][1] + weight)
             if right < len(intervals) else None)
        if b is None or (a is not None and a <= b):
            lo, hi = a
            left += 1
        else:
            lo, hi = b
            right += 1
        if out and lo <= out[-1][1] + 1:
            out[-1] = (out[-1][0], max(out[-1][1], hi))
        else:
            out.append((lo, hi))
    return tuple(out), work


def extract(weights, config=FeatureConfig()):
    started = perf_counter()
    raw = tuple(weights)
    if any(type(w) is not int or w <= 0 for w in raw):
        raise ValueError("positive integer weights required")
    divisor = 0
    for w in raw:
        divisor = gcd(divisor, w)
    divisor = divisor or 1
    normalized = tuple(w // divisor for w in raw)
    ordered = sorted(range(len(raw)), key=lambda i: (normalized[i], i))
    # Charge input validation, gcd, normalization and a conservative sort scale.
    work = 3 * len(raw) + len(raw) * max(1, len(raw).bit_length())
    records = []

    def certificate(name, selected, exact, **kwargs):
        nonlocal work
        selected_set = set(selected)
        work += len(raw)
        return Certificate(name, tuple(selected), tuple(
            i for i in range(len(raw)) if i not in selected_set), exact, **kwargs)

    selected, total = [], 0
    for i in ordered:
        work += 1
        if normalized[i] > total:
            selected.append(i)
            total += normalized[i]
    records.append(certificate(FEATURE_NAMES[0], selected, True))

    selected, total = [], 0
    for i in ordered:
        work += 1
        if normalized[i] <= total + 1:
            selected.append(i)
            total += normalized[i]
    records.append(certificate(FEATURE_NAMES[1], selected, True))

    counts = Counter(normalized)
    chosen_values = set(sorted(counts, key=lambda v: (-counts[v], v))[:config.distinct_values])
    work += len(raw) * (2 + max(1, len(raw).bit_length()))
    selected = [i for i in ordered if normalized[i] in chosen_values]
    records.append(certificate(FEATURE_NAMES[2], selected, True))

    selected, support = [], {0: 0}
    for i in ordered:
        candidate = dict(support)
        work += len(support)
        for value, mask in support.items():
            work += 1
            candidate.setdefault(value + normalized[i], mask | (1 << i))
        if len(candidate) <= config.support_cap:
            selected.append(i)
            support = candidate
    records.append(certificate(FEATURE_NAMES[3], selected, False,
                               support=tuple(sorted(support.items()))))
    work += len(support) * max(1, len(support).bit_length())

    selected, intervals, prefixes = [], ((0, 0),), [((0, 0),)]
    for i in ordered:
        candidate, steps = _extend_intervals(intervals, normalized[i])
        work += steps
        if len(candidate) <= config.interval_cap:
            selected.append(i)
            intervals = candidate
            prefixes.append(intervals)
    records.append(certificate(FEATURE_NAMES[4], selected, False, prefixes=tuple(prefixes)))
    return Features(normalized, divisor, tuple(records), work, perf_counter() - started)


def query(features, dimension, target):
    """Exact core membership with an original-index witness, or None.

    The target is in the original input's units. This function queries only the
    selected core; it does not search exceptional items.
    """
    if type(target) is not int:
        raise ValueError("integer target required")
    if target < 0 or target % features.divisor:
        return None
    remaining = target // features.divisor
    cert = features.certificates[dimension]
    weights = features.weights
    if dimension in (0, 1):
        chosen = []
        for i in reversed(cert.indices):
            if weights[i] <= remaining:
                chosen.append(i)
                remaining -= weights[i]
        return tuple(chosen) if remaining == 0 else None
    if dimension == 2:
        groups = {}
        for i in cert.indices:
            groups.setdefault(weights[i], []).append(i)
        values = sorted(groups)
        for counts in product(*(range(len(groups[v]) + 1) for v in values)):
            if sum(v * count for v, count in zip(values, counts)) == remaining:
                return tuple(i for v, count in zip(values, counts) for i in groups[v][:count])
        return None
    if dimension == 3:
        mask = dict(cert.support).get(remaining)
        return (None if mask is None else
                tuple(i for i in cert.indices if mask & (1 << i)))
    if dimension == 4:
        if not _contains(cert.prefixes[-1], remaining):
            return None
        chosen = []
        for position in range(len(cert.indices) - 1, -1, -1):
            i = cert.indices[position]
            if not _contains(cert.prefixes[position], remaining):
                remaining -= weights[i]
                if not _contains(cert.prefixes[position], remaining):
                    raise AssertionError("invalid interval certificate")
                chosen.append(i)
        if remaining != 0:
            raise AssertionError("invalid backtracking result")
        return tuple(chosen)
    raise ValueError("dimension must be in 0..4")
