"""Exact subset sum using small contiguous blocks and certified overlap bounds.

Reference implementation for the accompanying proof; no runtime superiority
claim. All sums, products, intervals, and witnesses use exact integers.
"""

from bisect import bisect_left, bisect_right
from dataclasses import dataclass


@dataclass(frozen=True)
class Block:
    start: int
    stop: int
    lower_total: int
    sums: tuple[int, ...]
    masks: tuple[int, ...]
    overlap: int


@dataclass(frozen=True)
class Representation:
    weights: tuple[int, ...]
    blocks: tuple[Block, ...]
    product: int
    block_limit: int
    intervals_checked: int
    support_candidates_constructed: int


@dataclass(frozen=True)
class Result:
    witness: tuple[int, ...] | None
    nodes: int
    children: int


def support(items):
    """Sorted distinct sums with one original-index mask per sum.

    Merge a sorted list with its translate. The counter includes both input
    lists at every merge, including duplicate sums that are then coalesced.
    """
    records = [(0, 0)]
    candidates = 0
    for original_index, weight in items:
        shifted = [(s + weight, mask | (1 << original_index))
                   for s, mask in records]
        candidates += len(records) + len(shifted)
        merged = []
        left = right = 0
        while left < len(records) or right < len(shifted):
            if right == len(shifted) or (
                    left < len(records) and records[left][0] <= shifted[right][0]):
                record = records[left]
                left += 1
            else:
                record = shifted[right]
                right += 1
            if not merged or merged[-1][0] != record[0]:
                merged.append(record)
        records = merged
    return records, candidates


def interval_overlap(sums, width):
    """Maximum distinct sums in a CLOSED interval of length width."""
    left = 0
    maximum = 0
    for right, value in enumerate(sums):
        while value - sums[left] > width:
            left += 1
        maximum = max(maximum, right - left + 1)
    return maximum


def prepare(weights, block_limit=3):
    """Minimize the overlap product over all contiguous sorted partitions.

    Every block contains at most block_limit items. This finds the exact
    optimum for that restricted partition family, not arbitrary partitions.
    """
    weights = tuple(weights)
    if type(block_limit) is not int or block_limit < 1:
        raise ValueError("block_limit must be a positive integer")
    if any(type(w) is not int or w <= 0 for w in weights):
        raise ValueError("weights must be positive integers")
    ordered = sorted(enumerate(weights), key=lambda pair: (pair[1], pair[0]))
    n = len(weights)
    prefix = [0]
    for _, w in ordered:
        prefix.append(prefix[-1] + w)
    best = [1] + [None] * n
    previous = [None] * (n + 1)
    scores = {}
    intervals_checked = candidates = 0
    for stop in range(1, n + 1):
        for start in range(max(0, stop - block_limit), stop):
            records, cost = support(ordered[start:stop])
            candidates += cost
            intervals_checked += 1
            score = interval_overlap([s for s, _ in records], prefix[start])
            scores[start, stop] = score
            value = best[start] * score
            if best[stop] is None or value < best[stop]:
                best[stop] = value
                previous[stop] = start
    spans = []
    stop = n
    while stop:
        start = previous[stop]
        spans.append((start, stop))
        stop = start
    blocks = []
    for start, stop in reversed(spans):
        records, cost = support(ordered[start:stop])
        candidates += cost
        blocks.append(Block(start, stop, prefix[start],
                            tuple(s for s, _ in records),
                            tuple(mask for _, mask in records),
                            scores[start, stop]))
    return Representation(weights, tuple(blocks), best[n], block_limit,
                          intervals_checked, candidates)


def solve(representation, target):
    """Exact DFS through compatible block sums, returning original indices."""
    if type(target) is not int:
        raise ValueError("target must be an integer")
    if target < 0 or target > sum(representation.weights):
        return Result(None, 1, 0)
    stack = [(len(representation.blocks) - 1, target, 0)]
    nodes = children = 0
    while stack:
        index, residual, mask = stack.pop()
        nodes += 1
        if index < 0:
            if residual == 0:
                witness = tuple(i for i in range(len(representation.weights))
                                if mask & (1 << i))
                return Result(witness, nodes, children)
            continue
        block = representation.blocks[index]
        low = bisect_left(block.sums, residual - block.lower_total)
        high = bisect_right(block.sums, residual)
        for position in range(high - 1, low - 1, -1):
            stack.append((index - 1, residual - block.sums[position],
                          mask | block.masks[position]))
            children += 1
    return Result(None, nodes, children)
