"""Shared exact portfolio with root or selective internal aggregate checks."""
from collections import Counter
from math import gcd
from time import perf_counter

from Structural_Geometry_Subset_Sum.budget import Meter, ResourceLimit
from Structural_Geometry_Subset_Sum.compat import (Limits, _Budget, _Limit, _inputs,
    _mask_indices, _root_answer, lift_witness, reduce_instance,
    solve, solve_bitset, solve_mitm)
from Structural_Geometry_Subset_Sum.structures.large_base import check, detect, eligible


POLICIES = ("portfolio", "detect_only", "root_geometry", "selective_geometry")
DEFAULTS = dict(candidate_cap=24, check_work_cap=12000, max_dp_bits=2_000_000,
    max_history_bits=64_000_000, max_q_count=4, stride=4, minimum_remaining=8,
    checkpoint_cap=16, max_states=32768, max_bitset_bits=1_000_000)


class SharedBudget(_Budget):
    def __init__(self, limits, parent):
        super().__init__(limits)
        self.parent = parent

    def tick(self, amount=1):
        if self.work+amount > self.limits.max_work:
            raise _Limit("work_limit")
        self.parent.tick(amount)
        super().tick(amount)


def shared_dfs(weights, target, limits, parent, callback=None, config=DEFAULTS):
    """Paper V's memoized include-first DFS, with optional bounded checkpoints.

    The same accounting adapter/traversal is used by all four policies. Native
    work/status/order match the original DFS when no callbacks run.
    """
    budget = SharedBudget(limits, parent)
    weights = _inputs(weights, target)
    checkpoints = 0
    try:
        answer = _root_answer(weights, target, budget)
        if answer is not None:
            return budget.finish(*answer)
        ordered = sorted(range(len(weights)), key=lambda i:(-weights[i], i))
        totals = [0]*(len(weights)+1)
        for offset in range(len(weights)-1, -1, -1):
            budget.tick()
            totals[offset] = totals[offset+1]+weights[ordered[offset]]
        seen, stack = set(), [(0, target, 0)]
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
                key = offset, remainder
                if key in seen:
                    continue
                budget.states(len(seen)+len(stack)+1)
                seen.add(key)
                remaining = len(weights)-offset
                if (callback is not None and offset > 0 and offset % config["stride"] == 0
                        and remaining >= config["minimum_remaining"] and checkpoints < config["checkpoint_cap"]):
                    checkpoints += 1
                    result = callback(tuple(weights[i] for i in ordered[offset:]), remainder, offset)
                    if result["status"] == "no":
                        continue
                    if result["status"] == "yes":
                        for local in result["witness"]:
                            mask |= 1 << ordered[offset+local]
                        witness = _mask_indices(mask)
                        break
                index = ordered[offset]
                budget.states(len(seen)+len(stack)+2)
                stack.append((offset+1, remainder, mask))
                stack.append((offset+1, remainder-weights[index], mask | (1 << index)))
        finally:
            budget.stats["query_seconds"] += perf_counter()-start
        return budget.finish("yes" if witness is not None else "no", witness,
            "witness" if witness is not None else "exhausted")
    except (_Limit, ResourceLimit) as exc:
        return budget.finish("unresolved", None, str(exc))


def solve_instance(weights, target, policy, *, max_work, seconds=None, config=None):
    config = dict(DEFAULTS if config is None else config)
    meter = Meter(max_work, seconds)
    original = tuple(weights)
    if policy not in POLICIES or type(target) is not int or any(type(w) is not int or w <= 0 for w in original):
        raise ValueError("known policy, positive integer weights and integer target required")
    counts = Counter(detections=0, candidates=0, geometry_checks=0, geometry_yes=0,
        geometry_no=0, root_yes=0, root_no=0, internal_yes=0, internal_no=0,
        internal_no_leaves=0, dp_updates=0, skipped_checks=0)
    times = {name:0. for name in ("preprocessing", "detection", "checker", "bitset", "core", "dfs", "mitm", "verification")}
    attempts, events = [], []
    status, witness, reason = "unresolved", None, "not_started"

    def geometric(weights, residual, depth=0, use=True):
        stamp = perf_counter()
        counts["detections"] += 1
        try:
            geometry, proposals = detect(weights, residual, meter, config["candidate_cap"])
        finally:
            times["detection"] += perf_counter()-stamp
        counts["candidates"] += proposals
        allowed = use and eligible(geometry, max_dp_bits=config["max_dp_bits"],
            max_history_bits=config["max_history_bits"], max_q_count=config["max_q_count"], selective=depth > 0)
        event = dict(depth=depth, weights=weights, target=residual, proposals=proposals,
            geometry=None if geometry is None else geometry.record(), allowed=allowed,
            status="unresolved", reason="detection_only" if not use else "representation_cap", witness=None)
        events.append(event)
        if not allowed:
            counts["skipped_checks"] += 1
            return dict(status="unresolved", witness=None)
        counts["geometry_checks"] += 1
        stamp = perf_counter()
        try:
            result = check(geometry, meter, max_work=config["check_work_cap"],
                max_dp_bits=config["max_dp_bits"], max_history_bits=config["max_history_bits"],
                max_q_count=config["max_q_count"])
        except ResourceLimit as exc:
            event["reason"] = str(exc)
            raise
        finally:
            times["checker"] += perf_counter()-stamp
        event.update(result)
        counts["dp_updates"] += result["updates"]
        if result["status"] in ("yes", "no"):
            counts["geometry_"+result["status"]] += 1
            counts[("root_" if depth == 0 else "internal_")+result["status"]] += 1
            if depth and result["status"] == "no":
                counts["internal_no_leaves"] += 1 << len(weights)
        return result

    try:
        stamp = perf_counter()
        try:
            kernel = reduce_instance(original, target)
            meter.tick(kernel.work)
            normalized, residual = kernel.weights, kernel.target
            if kernel.status == "unresolved":
                divisor = 0
                for value in normalized:
                    meter.tick()
                    divisor = gcd(divisor, value)
                normalized = tuple(w//divisor for w in normalized)
                residual //= divisor
                meter.tick(len(normalized)+1)
        finally:
            times["preprocessing"] += perf_counter()-stamp
        status, witness, reason = kernel.status, kernel.witness, kernel.reason
        if status == "unresolved" and policy != "portfolio":
            result = geometric(normalized, residual, use=policy != "detect_only")
            status, witness = result["status"], result["witness"]
            if status != "unresolved":
                reason = result["reason"]
                if witness is not None:
                    witness = lift_witness(kernel, witness)
        if status == "unresolved":
            methods = (("bitset", solve_bitset), ("core", None), ("dfs", None), ("mitm", solve_mitm))
            for position, (name, method) in enumerate(methods):
                meter.check()
                share = meter.remaining//(len(methods)-position)
                if share < 1:
                    continue
                limits = Limits(max_work=share, max_states=config["max_states"],
                    max_seconds=meter.seconds_left(), max_bitset_bits=config["max_bitset_bits"])
                stamp = perf_counter()
                nested_before = times["detection"]+times["checker"]
                try:
                    if name == "dfs":
                        result = shared_dfs(normalized, residual, limits, meter,
                            geometric if policy == "selective_geometry" else None, config)
                    elif name == "core":
                        result = solve(normalized, residual, method="enumerate", limits=limits)
                        meter.tick(result.stats["work"])
                    else:
                        result = method(normalized, residual, limits=limits)
                        meter.tick(result.stats["work"])
                    meter.peak_search_states = max(meter.peak_search_states, result.stats["peak_states"])
                finally:
                    nested = times["detection"]+times["checker"]-nested_before
                    times[name] += max(0., perf_counter()-stamp-nested)
                attempts.append(dict(method=name, status=result.status, reason=result.reason,
                    native_work=result.stats["work"], peak_states=result.stats["peak_states"]))
                if result.status != "unresolved":
                    status, reason = result.status, result.reason
                    witness = None if result.witness is None else lift_witness(kernel, result.witness)
                    break
            if status == "unresolved":
                reason = "portfolio_limits"
        if status != "unresolved":
            stamp = perf_counter()
            meter.tick(1 if witness is None else 3*len(witness)+1)
            if witness is not None and (len(set(witness)) != len(witness) or
                    any(not 0 <= i < len(original) for i in witness) or sum(original[i] for i in witness) != target):
                raise AssertionError("invalid original-index witness")
            times["verification"] += perf_counter()-stamp
        meter.check()
    except ResourceLimit as exc:
        status, witness, reason = "unresolved", None, str(exc)
    elapsed = perf_counter()-meter.started
    if seconds is not None and elapsed >= seconds:
        status, witness, reason = "unresolved", None, "deadline"
    return dict(status=status, reason=reason, witness=witness, seconds=elapsed, work=meter.work,
        overshoot_seconds=0 if seconds is None else max(0., elapsed-seconds), counts=dict(counts),
        component_seconds=times, peak_dp_bits=meter.peak_dp_bits,
        peak_history_bits=meter.peak_history_bits, peak_search_states=meter.peak_search_states,
        attempts=attempts, events=events)
