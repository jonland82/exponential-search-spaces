"""Root geometric checking with paid cost-sensitive decisions and exact fallback."""
from dataclasses import fields
from math import exp
from time import perf_counter

from Structural_Geometry_Subset_Sum.budget import Meter, ResourceLimit
from Structural_Geometry_Subset_Sum.classifier_features import (
    base_features, doubling_feature, geometry_features)
from Structural_Geometry_Subset_Sum.compat import (
    Limits, lift_witness, reduce_instance, solve_bitset, solve_dfs, solve_mitm)
from Structural_Geometry_Subset_Sum.structures.large_base import Geometry, check, eligible


POLICIES = ("lean_never", "never", "always", "simple", "learned", "direct_mitm")
DEFAULTS = dict(check_work_cap=12000, max_dp_bits=2_000_000,
    max_history_bits=64_000_000, max_q_count=4,
    max_states=32768, max_bitset_bits=1_000_000)
INFERENCE_WORK = 6*19+20


class PaidMeter(Meter):
    """Charge a final partial atomic phase before returning work exhaustion."""
    def tick(self, amount=1):
        if amount > self.remaining:
            super().tick(self.remaining)
            raise ResourceLimit("work_limit")
        super().tick(amount)


def gate_score(model, vector):
    """Offline-folded scaler/logit: same probabilities without library call overhead."""
    if "constant" in model:
        return model["constant"]
    if len(vector) != len(model["coefficients"]):
        raise ValueError("feature dimension mismatch")
    value = model["intercept"]+sum(a*b for a, b in zip(vector, model["coefficients"]))
    if value >= 0:
        return 1/(1+exp(-value))
    e = exp(value)
    return e/(1+e)


def capped_cost(result, budget):
    """Unresolved observations are censored at their full prescribed allowance."""
    return result["work"] if result["status"] != "unresolved" else budget


def solve_gate(weights, target, policy, *, max_work, seconds=None, model=None, config=None):
    if policy not in POLICIES or (policy == "learned" and model is None):
        raise ValueError("known policy and a fitted model for learned decisions required")
    config = dict(DEFAULTS if config is None else config)
    meter = PaidMeter(max_work, seconds)
    phases = {name:0 for name in ("preprocessing", "features", "cores", "geometry",
        "doubling", "decision", "checker", "bitset", "dfs", "mitm", "verification")}
    phase_seconds = {name:0. for name in phases}
    status, witness, reason = "unresolved", None, "not_started"
    vector, geometry_record, event = None, None, None
    decision_eligible, check_taken, score = False, False, None
    attempts = []

    def charge(phase, work, action):
        started, before = perf_counter(), meter.work
        try:
            value = action()
            meter.tick(work(value) if callable(work) else work)
            return value
        finally:
            phases[phase] += meter.work-before
            phase_seconds[phase] += perf_counter()-started

    def verify_answer():
        if witness is not None:
            if (len(witness) != len(set(witness)) or any(not 0 <= i < len(weights) for i in witness)
                    or sum(weights[i] for i in witness) != target):
                raise AssertionError("invalid lifted witness")

    try:
        kernel = charge("preprocessing", lambda k:k.work, lambda:reduce_instance(weights, target))
        status, witness, reason = kernel.status, kernel.witness, kernel.reason
        if status == "unresolved":
            base = charge("features", lambda b:b["work"], lambda:base_features(weights, target, kernel))
            reuse = charge("cores", base["reuse"]["work"], lambda:base["reuse"])
            status, witness, reason = reuse["status"], reuse["witness"], "five_core_reuse"
        if status == "unresolved" and policy not in ("lean_never", "direct_mitm"):
            discovered = charge("geometry", lambda d:d["work"],
                lambda:geometry_features(kernel.weights, kernel.target))
            geometry_record = discovered["geometry"]
            geometry = None if geometry_record is None else Geometry(**{
                f.name:geometry_record[f.name] for f in fields(Geometry)})
            if discovered["exact_no"]:
                status, witness, reason = "no", None, "aggregate_gap"
            elif eligible(geometry, max_dp_bits=config["max_dp_bits"],
                    max_history_bits=config["max_history_bits"], max_q_count=config["max_q_count"]):
                doubling = charge("doubling", lambda d:d["work"], lambda:doubling_feature(kernel.weights))
                vector = base["values"]+discovered["values"]+[doubling["value"]]
                decision_eligible = True

                def decide():
                    nonlocal score
                    if policy == "learned":
                        score = gate_score(model, vector)
                        return score >= model["threshold"]
                    return policy == "always" or (policy == "simple" and
                        geometry.q_count <= 2 and geometry.width-1 <= geometry.base)

                check_taken = charge("decision", INFERENCE_WORK if policy == "learned" else 1, decide)
                if check_taken:
                    started, before = perf_counter(), meter.work
                    event = dict(weights=kernel.weights, target=kernel.target, geometry=geometry_record,
                                 status="unresolved", reason="interrupted", witness=None)
                    try:
                        checked = check(geometry, meter, max_work=config["check_work_cap"],
                            max_dp_bits=config["max_dp_bits"], max_history_bits=config["max_history_bits"],
                            max_q_count=config["max_q_count"])
                        event.update(checked)
                    finally:
                        phases["checker"] += meter.work-before
                        phase_seconds["checker"] += perf_counter()-started
                    status, witness, reason = checked["status"], checked["witness"], checked["reason"]
                    if witness is not None:
                        witness = lift_witness(kernel, witness)
        if status == "unresolved":
            methods = [("mitm", solve_mitm)] if policy == "direct_mitm" else [
                ("bitset", solve_bitset), ("dfs", solve_dfs), ("mitm", solve_mitm)]
            for position, (name, method) in enumerate(methods):
                remaining_methods = len(methods)-position
                work_share = meter.remaining//remaining_methods
                if work_share < 1:
                    continue
                left = meter.seconds_left()
                limits = Limits(max_work=work_share, max_states=config["max_states"],
                    max_bitset_bits=config["max_bitset_bits"],
                    max_seconds=None if left is None else left/remaining_methods)
                result = charge(name, lambda r:r.stats["work"],
                                lambda:method(kernel.weights, kernel.target, limits=limits))
                attempts.append(dict(method=name, status=result.status, reason=result.reason,
                    work=result.stats["work"], peak_states=result.stats["peak_states"]))
                if result.status != "unresolved":
                    status, reason = result.status, result.reason
                    witness = None if result.witness is None else lift_witness(kernel, result.witness)
                    break
        if status != "unresolved":
            charge("verification", 1 if witness is None else 3*len(witness)+1, verify_answer)
        meter.check()
    except ResourceLimit as exc:
        status, witness, reason = "unresolved", None, str(exc)
    elapsed = perf_counter()-meter.started
    if seconds is not None and elapsed >= seconds:
        status, witness, reason = "unresolved", None, "deadline"
    return dict(status=status, witness=witness, reason=reason, work=meter.work, seconds=elapsed,
        phase_work=phases, phase_seconds=phase_seconds, gate_features=vector,
        decision_eligible=decision_eligible, check_taken=check_taken, gate_score=score,
        geometry=geometry_record, checker_event=event, attempts=attempts,
        peak_dp_bits=meter.peak_dp_bits, peak_history_bits=meter.peak_history_bits,
        overshoot_seconds=0 if seconds is None else max(0., elapsed-seconds))
