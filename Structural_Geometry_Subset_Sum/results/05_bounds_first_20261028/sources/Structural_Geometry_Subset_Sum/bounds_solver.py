"""Experiment 05 portfolios; frozen Experiment 04 remains unchanged."""
from dataclasses import fields
from time import perf_counter

from Structural_Geometry_Subset_Sum.budget import ResourceLimit
from Structural_Geometry_Subset_Sum.classifier_features import base_features, geometry_features
from Structural_Geometry_Subset_Sum.compat import (Limits, lift_witness, reduce_instance,
    solve_bitset, solve_dfs, solve_mitm)
from Structural_Geometry_Subset_Sum.cost_gate import PaidMeter
from Structural_Geometry_Subset_Sum.structures.large_base import Geometry, check, eligible
from Structural_Geometry_Subset_Sum.structures.bounds_core import choose_fast, solve_bounds
from Structural_Geometry_Subset_Sum.exception_solver import solve_exceptions, DEFAULTS as ORIGINAL_DEFAULTS


POLICIES = ("root", "reuse", "bounds_only", "bounds_first", "fast_eager")
DEFAULTS = dict(ORIGINAL_DEFAULTS, discovery_work_cap=1024, discovery_fraction=16)
def solve_bounds_portfolio(weights, target, policy, *, max_work, seconds=None, config=None):
    if policy not in POLICIES:
        raise ValueError("known bounds-first policy required")
    config = dict(DEFAULTS if config is None else config)
    if policy in ("root", "reuse"):
        return solve_exceptions(weights, target, policy, max_work=max_work, seconds=seconds,
            config={k:config[k] for k in ORIGINAL_DEFAULTS})
    meter = PaidMeter(max_work, seconds)
    phases = {p:0 for p in ("preprocessing", "features", "cores", "geometry", "root_check",
        "core_discovery", "core_solving", "bitset", "dfs", "mitm", "verification")}
    times = {p:0. for p in phases}
    status, witness, reason = "unresolved", None, "not_started"
    geometry_record, plan_record, core_event, root_event = None, None, None, None
    attempts = []
    discovery_event = None

    def phase(name, action, work=None):
        start, before = perf_counter(), meter.work
        try:
            result = action()
            if work is not None:
                meter.tick(work(result) if callable(work) else work)
            return result
        finally:
            phases[name] += meter.work-before
            times[name] += perf_counter()-start

    def verify_witness():
        if witness is not None and (len(set(witness)) != len(witness)
                or any(not 0 <= i < len(weights) for i in witness)
                or sum(weights[i] for i in witness) != target):
            raise AssertionError("invalid original-index witness")

    try:
        kernel = phase("preprocessing", lambda:reduce_instance(weights, target), lambda k:k.work)
        status, witness, reason = kernel.status, kernel.witness, kernel.reason
        if status == "unresolved":
            base = phase("features", lambda:base_features(weights, target, kernel), lambda b:b["work"])
            reused = phase("cores", lambda:base["reuse"], base["reuse"]["work"])
            status, witness, reason = reused["status"], reused["witness"], "five_core_reuse"
        if status == "unresolved":
            discovered = phase("geometry", lambda:geometry_features(kernel.weights, kernel.target), lambda d:d["work"])
            geometry_record = discovered["geometry"]
            geometry = None if geometry_record is None else Geometry(**{
                f.name:geometry_record[f.name] for f in fields(Geometry)})
            if discovered["exact_no"]:
                status, witness, reason = "no", None, "aggregate_gap"
            elif eligible(geometry, max_dp_bits=config["max_dp_bits"],
                    max_history_bits=config["max_history_bits"], max_q_count=config["max_q_count"]):
                checked = phase("root_check", lambda:check(geometry, meter,
                    max_work=config["root_check_work"], max_dp_bits=config["max_dp_bits"],
                    max_history_bits=config["max_history_bits"], max_q_count=config["max_q_count"]))
                root_event = dict(weights=kernel.weights, target=kernel.target, geometry=geometry_record, **checked)
                status, witness, reason = checked["status"], checked["witness"], checked["reason"]
                if witness is not None:
                    witness = lift_witness(kernel, witness)
            if status == "unresolved":
                remaining_allowance = lambda:min(config["core_work_cap"],
                    meter.remaining*config["reserve_numerator"]//config["reserve_denominator"])
                discovery_cap = min(config["discovery_work_cap"], meter.remaining//config["discovery_fraction"])
                plan, discovery_event = phase("core_discovery", lambda:choose_fast(geometry, meter,
                    max_work=discovery_cap, available_work=remaining_allowance,
                    maximum_exceptions=config["maximum_exceptions"], max_dp_bits=config["max_dp_bits"],
                    max_history_bits=config["max_history_bits"]))
                plan_record = None if plan is None else plan.record()
                allowance = remaining_allowance()
                if plan is not None and plan.estimated_work <= allowance:
                    checked = phase("core_solving", lambda:solve_bounds(geometry, plan, meter,
                        max_work=allowance, mode=policy))
                    core_event = dict(weights=kernel.weights, target=kernel.target,
                        geometry=geometry_record, plan=plan_record, allowance=allowance, **checked)
                    status, witness, reason = checked["status"], checked["witness"], checked["reason"]
                    if witness is not None:
                        witness = lift_witness(kernel, witness)
        if status == "unresolved":
            methods = [
                ("bitset", solve_bitset), ("dfs", solve_dfs), ("mitm", solve_mitm)]
            for position, (name, method) in enumerate(methods):
                left = len(methods)-position
                cap = meter.remaining//left
                if cap < 1:
                    continue
                remaining_seconds = meter.seconds_left()
                limits = Limits(max_work=cap, max_states=config["max_states"],
                    max_bitset_bits=config["max_bitset_bits"],
                    max_seconds=None if remaining_seconds is None else remaining_seconds/left)
                native = phase(name, lambda:method(kernel.weights, kernel.target, limits=limits), lambda r:r.stats["work"])
                attempts.append(dict(method=name, status=native.status, reason=native.reason,
                                     work=native.stats["work"], peak_states=native.stats["peak_states"]))
                if native.status != "unresolved":
                    status, reason = native.status, native.reason
                    witness = None if native.witness is None else lift_witness(kernel, native.witness)
                    break
        if status != "unresolved":
            phase("verification", verify_witness, 1 if witness is None else 3*len(witness)+1)
        meter.check()
    except ResourceLimit as exc:
        status, witness, reason = "unresolved", None, str(exc)
    elapsed = perf_counter()-meter.started
    if seconds is not None and elapsed >= seconds:
        status, witness, reason = "unresolved", None, "deadline"
    return dict(status=status, witness=witness, reason=reason, work=meter.work, seconds=elapsed,
        phase_work=phases, phase_seconds=times, geometry=geometry_record, plan=plan_record,
        root_event=root_event, core_event=core_event, discovery_event=discovery_event, attempts=attempts,
        peak_dp_bits=meter.peak_dp_bits, peak_history_bits=meter.peak_history_bits,
        overshoot_seconds=0 if seconds is None else max(0., elapsed-seconds))
