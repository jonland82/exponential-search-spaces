"""Exact certificates for uniform, finite-target subset-sum probabilities.

All certificate endpoints are integer support counts. Floating point is used
only for partition balancing, presentation, and the statistical baseline.
"""
from __future__ import annotations

from bisect import bisect_left, bisect_right
from collections import Counter
from dataclasses import dataclass
from functools import cached_property
import math
import random


MODULI = (8, 10, 16, 32)


def check_weights(weights):
    if not weights or any(type(w) is not int or w <= 0 for w in weights):
        raise ValueError('weights must be a nonempty list of positive integers')


def all_sums(weights, limit=None):
    sums = {0}
    for weight in weights:
        sums |= {s + weight for s in sums if limit is None or s + weight <= limit}
    return sums


def residue_mask(weights, modulus):
    full, mask = (1 << modulus) - 1, 1
    for w in weights:
        shift = w % modulus
        mask |= ((mask << shift) | (mask >> (modulus - shift))) & full
    return mask


@dataclass(frozen=True)
class Targets:
    lo: int
    hi: int
    period: int = 1
    residues: tuple = (0,)

    def __post_init__(self):
        if (self.lo > self.hi or self.period <= 0 or
                any(type(r) is not int or not 0 <= r < self.period for r in self.residues)
                or len(set(self.residues)) != len(self.residues) or self.size <= 0):
            raise ValueError('target set must be nonempty with unique valid residues')

    @cached_property
    def size(self):
        return sum((self.hi-r)//self.period - (self.lo-1-r)//self.period
                   for r in self.residues)

    def contains(self, value):
        return self.lo <= value <= self.hi and value % self.period in self.residue_set

    @cached_property
    def residue_set(self):
        return frozenset(self.residues)

    def sample(self, rng):
        # Rank sampling is exactly uniform, including short boundary periods.
        rank = rng.randrange(self.size)
        firsts, cumulative = self.rank_segments
        index = bisect_right(cumulative, rank)
        preceding = cumulative[index-1] if index else 0
        return firsts[index] + self.period*(rank-preceding)

    @cached_property
    def rank_segments(self):
        firsts, cumulative, total = [], [], 0
        for residue in self.residues:
            first = self.lo + (residue-self.lo) % self.period
            count = max(0, (self.hi-first)//self.period + 1)
            if count:
                total += count
                firsts.append(first)
                cumulative.append(total)
        return firsts, cumulative


def study_targets(weights):
    check_weights(weights)
    # Deliberately retain the original round(.30 total), round(.70 total) rule.
    total = sum(weights)
    period = math.lcm(*MODULI)
    masks = {m: residue_mask(weights, m) for m in MODULI}
    residues = tuple(r for r in range(period)
                     if all((mask >> (r % m)) & 1 for m, mask in masks.items()))
    return Targets(round(.30*total), round(.70*total), period, residues)


def original_interval(weights, targets, rng, witness_budget=512):
    witnessed = set()
    for _ in range(witness_budget):
        bits = rng.getrandbits(len(weights))
        value = sum(w for i, w in enumerate(weights) if (bits >> i) & 1)
        if targets.contains(value):
            witnessed.add(value)
    k = math.prod(c+1 for c in Counter(weights).values())
    return len(witnessed), min(targets.size, k), k


def partition(weights):
    check_weights(weights)
    blocks, loads = [[], []], [0., 0.]
    for value, count in sorted(Counter(weights).items()):
        index = 0 if loads[0] <= loads[1] else 1
        blocks[index].extend([value]*count)
        loads[index] += math.log2(count+1)
    assert not set(blocks[0]).intersection(blocks[1])
    return blocks


def half_sums(weights):
    blocks = partition(weights)
    return blocks, sorted(all_sums(blocks[0])), sorted(all_sums(blocks[1]))


def count_pairs(a, b, targets, all_pairs_pass_residues=False):
    """Count pairs in D; interval shortcut needs a proved residue implication."""
    if all_pairs_pass_residues or targets.period == 1:
        return sum(bisect_right(b, targets.hi-x)-bisect_left(b, targets.lo-x) for x in a)
    # Generic periodic target sets need explicit residue accounting.
    grouped = {}
    for value in b:
        grouped.setdefault(value % targets.period, []).append(value)
    result = 0
    for x in a:
        for residue in targets.residues:
            values = grouped.get((residue-x) % targets.period, ())
            result += bisect_right(values, targets.hi-x)-bisect_left(values, targets.lo-x)
    return result


def selected_differences(a, b, budget):
    """Select before examining collision contributions or any exact label."""
    ca = Counter(y-x for x, y in zip(a, a[1:]))
    cb = Counter(y-x for x, y in zip(b, b[1:]))
    return sorted(ca.keys() & cb.keys(), key=lambda d: (-ca[d]*cb[d], d))[:budget]


def collision_terms(a, b, targets, differences, all_pairs_pass_residues=False):
    sa, sb = set(a), set(b)
    for delta in differences:
        if type(delta) is not int or delta <= 0:
            raise ValueError('differences must be positive integers')
    if len(set(differences)) != len(differences):
        raise ValueError('collision differences must be distinct')
    for delta in differences:
        ad = [x for x in a if x+delta in sa]
        bd = [y for y in b if y-delta in sb]
        yield delta, count_pairs(ad, bd, targets, all_pairs_pass_residues)


def residue_cap(a, b, moduli=(16, 64)):
    """Certified cap by residue-wise injective matching, stronger than products."""
    best = min(len(a), len(b))
    details = []
    for modulus in moduli:
        ca, cb = [0]*modulus, [0]*modulus
        for x in a:
            ca[x % modulus] += 1
        for y in b:
            cb[y % modulus] += 1
        cap = max(sum(min(ca[i], cb[(s-i) % modulus]) for i in range(modulus))
                  for s in range(modulus))
        best = min(best, cap)
        details.append({'modulus': modulus, 'cap': cap})
    return best, details


def ceil_div(numerator, denominator):
    return -(-numerator//denominator)


def support_interval(m, j_lower, j_upper, cap, denominator, lower=0, upper=None):
    if upper is None:
        upper = denominator
    if not (0 <= lower <= upper <= denominator and 0 <= j_lower <= j_upper):
        raise ValueError('invalid support bounds')
    if m == 0:
        if lower != 0 or j_lower != 0:
            raise ValueError('inconsistent zero-pair certificate')
        return 0, 0
    if m < 0 or cap < 1:
        raise ValueError('positive pair count requires a positive cap')
    lo = max(lower, m-j_upper, ceil_div(m*m, m+2*j_upper), ceil_div(m, cap))
    hi = min(upper, denominator, m-ceil_div(2*j_lower, cap))
    if lo > hi:
        raise ValueError('inconsistent certificates')
    return lo, hi


def collision_upper(m, cap):
    """Maximal collision energy with M representations and cell cap R."""
    full, remainder = divmod(m, cap)
    return full*cap*(cap-1)//2 + remainder*(remainder-1)//2


def exact_histogram(a, b, targets):
    """Evaluation oracle, never called by a partial-certificate method."""
    histogram = Counter(x+y for x in a for y in b if targets.contains(x+y))
    m = sum(histogram.values())
    j = sum(r*(r-1)//2 for r in histogram.values())
    return histogram, m, j


def exact_set_count(weights, targets):
    return sum(targets.contains(s) for s in all_sums(weights, targets.hi))


def exact_bitset_count(weights, targets, max_bits=100_000_000):
    # GCD compression and truncation at hi are valid for positive weights.
    divisor = math.gcd(*weights)
    hi, lo = targets.hi//divisor, max(0, ceil_div(targets.lo, divisor))
    if hi+1 > max_bits:
        return None
    if hi < lo:
        return 0
    cap, bits = (1 << (hi+1))-1, 1
    for w in weights:
        bits = (bits | (bits << (w//divisor))) & cap
    reachable = (bits >> lo) & ((1 << (hi-lo+1))-1)
    if all((divisor*s) % targets.period in targets.residues
           for s in range(math.lcm(divisor, targets.period)//divisor)):
        # The study's D includes all attainable residues; this shortcut also
        # requires every multiple of gcd to pass its residue rule.
        return reachable.bit_count()
    # Generic D: count allowed positions with a periodic integer mask.
    period = targets.period//math.gcd(targets.period, divisor)
    pattern = sum(1 << i for i in range(period)
                  if ((lo+i)*divisor) % targets.period in targets.residues)
    length = hi-lo+1
    repeats = ceil_div(length, period)
    mask = pattern * (((1 << (period*repeats))-1)//((1 << period)-1))
    return (reachable & mask).bit_count()


def decision(target, a, b_set):
    return any(target-x in b_set for x in a)


def sampling_checkpoint(successes, trials, denominator, lower, upper, alpha):
    """Hoeffding band, intersected with a deterministic interval."""
    radius = math.sqrt(math.log(2/alpha)/(2*trials))
    # Never silently replace an empty statistical/certified intersection.
    lo, hi = max(lower/denominator, successes/trials-radius), min(
        upper/denominator, successes/trials+radius)
    return {'lower': lo, 'upper': hi, 'width': max(0., hi-lo),
            'empty': lo > hi, 'successes': successes, 'trials': trials,
            'radius': radius}
