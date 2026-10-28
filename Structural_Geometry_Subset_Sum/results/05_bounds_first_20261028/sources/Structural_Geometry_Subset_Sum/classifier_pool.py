"""Paid prioritization: same exact solver, paired orders, work and live endpoints."""
from dataclasses import asdict
import random
from time import perf_counter

from Structural_Geometry_Subset_Sum.classifier_features import (MODEL_FOR,
    base_features, doubling_feature, geometry_features, inference_work, infer,
    limited_portfolio)
from Structural_Geometry_Subset_Sum.compat import lift_witness, reduce_instance


PHASES = ("preprocessing", "features", "core_queries", "geometry", "doubling",
          "inference", "sorting", "solving", "verification")


def witness_cost(weights, target, status, witness):
    if status != "yes" or witness is None:
        return 0
    assert len(set(witness)) == len(witness)
    assert all(0 <= i < len(weights) for i in witness)
    assert sum(weights[i] for i in witness) == target
    return 3*len(witness)+1


def run_pool(cases, bundles, predictions, policy, mode, fraction, repeat, seed,
             per_case_seconds=.020):
    """All feature use follows payment; work replay never substitutes cached time."""
    cohort = cases[0]["cohort"]
    budget = (int(fraction*sum(c["budget"] for c in cases)) if mode == "work" else
              fraction*len(cases)*per_case_seconds)
    started = perf_counter()
    costs = {phase:0 for phase in PHASES}
    spent, exhausted = 0, None
    solved, attempts, events, pending, kernels, scores = [], [], [], [], {}, {}
    ordered = list(cases)
    random.Random(f"{seed}:arrival:{cohort}:{repeat}").shuffle(ordered)
    arm = MODEL_FOR[policy]

    def pay(amount, phase):
        nonlocal spent, exhausted
        if mode == "work":
            used = min(amount, budget-spent)
            spent += used
            costs[phase] += used
            okay = used == amount
        else:
            costs[phase] += amount
            okay = perf_counter()-started <= budget
        if not okay:
            exhausted = phase
        return okay

    def finish():
        elapsed = perf_counter()-started
        return dict(cohort=cohort, policy=policy, mode=mode, fraction=fraction,
            repeat=repeat, budget=budget, spent=spent if mode == "work" else elapsed,
            costs=costs, solved=len(solved), solved_ids=solved, attempts=attempts,
            events=events, exhausted_phase=exhausted,
            overshoot_seconds=0 if mode == "work" else max(0, elapsed-budget))

    def accept(case, status, witness, source):
        tick = perf_counter()
        work = witness_cost(case["weights"], case["target"], status, witness)
        if not pay(work if mode == "work" else perf_counter()-tick, "verification"):
            return False
        accepted_at = perf_counter()-started if mode == "time" else None
        if mode == "time" and accepted_at > budget:
            pay(0, "verification")
            return False
        events.append(dict(case_id=case["case_id"], source=source, status=status, witness=witness,
                          accepted_at_seconds=accepted_at))
        if status != "unresolved":
            solved.append(case["case_id"])
        return True

    # Identical reduction and original five-core reuse for every policy.
    for case in ordered:
        tick = perf_counter()
        kernel = case["kernel"] if mode == "work" else asdict(reduce_instance(case["weights"], case["target"]))
        if not pay(kernel["work"] if mode == "work" else perf_counter()-tick, "preprocessing"):
            return finish()
        kernels[case["case_id"]] = kernel
        if kernel["status"] != "unresolved":
            if not accept(case, kernel["status"], kernel["witness"], "reduction"):
                return finish()
        else:
            pending.append(case)

    residual, vectors = [], []
    for case in pending:
        kernel = kernels[case["case_id"]]
        tick = perf_counter()
        if mode == "work":
            base = case["base"]
        else:
            from advanced_features import Kernel
            base = base_features(case["weights"], case["target"], Kernel(**kernel))
        # Live acquisition includes the core query inside the measured operation.
        if not pay(base["work"] if mode == "work" else perf_counter()-tick, "features"):
            return finish()
        reuse = base["reuse"]
        if not pay(reuse["work"] if mode == "work" else 0, "core_queries"):
            return finish()
        if reuse["status"] != "unresolved":
            if not accept(case, reuse["status"], reuse["witness"], "five_core_reuse"):
                return finish()
            continue
        vector = list(base["values"])
        if policy != "cheap15":
            tick = perf_counter()
            geometry = case["geometry"] if mode == "work" else geometry_features(kernel["weights"], kernel["target"])
            if not pay(geometry["work"] if mode == "work" else perf_counter()-tick, "geometry"):
                return finish()
            if geometry["exact_no"]:
                if not accept(case, "no", None, "aggregate_gap"):
                    return finish()
                continue
            if arm != "baseline15":
                vector += geometry["values"]
        if policy == "doubling19":
            tick = perf_counter()
            doubling = case["doubling"] if mode == "work" else doubling_feature(kernel["weights"])
            if not pay(doubling["work"] if mode == "work" else perf_counter()-tick, "doubling"):
                return finish()
            vector.append(doubling["value"])
        residual.append(case)
        vectors.append(vector)
    pending = residual
    tick = perf_counter()
    if mode == "work":
        if not pay(inference_work(arm)*len(pending), "inference"):
            return finish()
        scores = {c["case_id"]:predictions[c["case_id"]][arm] for c in pending}
    else:
        predicted, _, _ = infer(bundles[arm], vectors, count_work=False)
        if not pay(perf_counter()-tick, "inference"):
            return finish()
        scores = {c["case_id"]:p for c, p in zip(pending, predicted)}
    tick = perf_counter()
    pending.sort(key=lambda c: -scores[c["case_id"]]/(c["budget"] if mode == "work" else 1))
    if not pay(len(pending)*max(1, len(pending).bit_length()) if mode == "work" else
               perf_counter()-tick, "sorting"):
        return finish()
    for case in pending:
        kernel = kernels[case["case_id"]]
        cap = case["budget"]-kernel["work"]
        remaining = budget-(spent if mode == "work" else perf_counter()-started)
        if remaining <= 0:
            break
        clipped = mode == "work" and remaining < cap
        allowance = None if mode == "work" else min(per_case_seconds-kernel["seconds"], remaining)
        if cap < 1 or (allowance is not None and allowance <= 0):
            continue
        tick = perf_counter()
        if mode == "work" and not clipped:
            ref = case["reference"]
            status, witness, used = ref["status"], ref["witness"], ref["work"]-kernel["work"]
        else:
            result = limited_portfolio(kernel["weights"], kernel["target"],
                                      min(cap, remaining) if mode == "work" else cap, allowance)
            status, witness, used = result["status"], result["witness"], result["work"]
            if witness is not None:
                from advanced_features import Kernel
                witness = lift_witness(Kernel(**kernel), witness)
        elapsed = perf_counter()-tick
        returned = status
        within = allowance is None or elapsed <= allowance
        if not within:
            status = "unresolved"
        attempts.append(dict(case_id=case["case_id"], status=status, returned_status=returned,
            witness=witness, work=used, clipped=clipped,
            **({} if mode == "work" else dict(seconds=elapsed, allowance_seconds=allowance,
                                              within_case_deadline=within))))
        if not pay(used if mode == "work" else elapsed, "solving"):
            return finish()
        if not accept(case, status, witness, "portfolio"):
            return finish()
    return finish()
