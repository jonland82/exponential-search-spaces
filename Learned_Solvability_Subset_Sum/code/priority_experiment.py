"""Frozen pool-prioritization experiment with counter and live-time endpoints.

Counter replay charges every phase before its result can influence scheduling.
Only the common exact solver's full-cap trace is reused; a clipped final solve
is executed with that actual smaller allowance. The separate live endpoint
recomputes all prechecks/features/predictions and uses real cooperative deadlines.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import asdict
import json
from pathlib import Path
import random
from statistics import median
from time import perf_counter

import joblib

from advanced_features import extract_advanced, lift_witness, reduce_instance
from features import FeatureConfig
from prospective_study import (ARMS, CONFIG, conventional, conventional_cost, infer,
                                limited_portfolio, read_jsonl, verify)
from run_development import full_core_query
from run_pilot import check, save_json, save_jsonl, sha


PHASES = ("preprocessing", "features", "inference", "sorting", "core_queries", "solving", "verification")


def validate_witness(weights, target, status, witness):
    if status != "yes" or witness is None:
        return 0
    if (len(set(witness)) != len(witness) or any(not 0 <= i < len(weights) for i in witness)
            or sum(weights[i] for i in witness) != target):
        raise AssertionError("invalid indexed witness during paid verification")
    return 3 * len(witness) + 1


def arrivals(cases, cohort, repeat):
    ordered = list(cases)
    random.Random(f"{CONFIG['seed']}:arrival:{cohort}:{repeat}").shuffle(ordered)
    return ordered


def rank_cases(pending, policy, scores, *, time_mode=False, cohort="", repeat=0):
    ordered = list(pending)
    if policy == "random":
        random.Random(f"{CONFIG['seed']}:random:{cohort}:{repeat}").shuffle(ordered)
    elif policy == "short_input":
        ordered.sort(key=lambda c: c["budget"])
    elif policy in ARMS or policy == "distance_rule":
        ordered.sort(key=lambda c: -(scores[c["case_id"]] /
                                    (1 if time_mode else c["budget"])))
    return ordered


def replay_pool(cases, reference_map, policy, fraction, repeat):
    cohort = cases[0]["cohort"]
    budget = int(fraction * sum(c["budget"] for c in cases))
    costs = {name: 0 for name in PHASES}
    spent, exhausted = 0, None
    solved, attempts, pending, scores = [], [], [], {}
    ordered = arrivals(cases, cohort, repeat)

    def consume(amount, phase):
        nonlocal spent, exhausted
        used = min(amount, budget - spent)
        costs[phase] += used
        spent += used
        if used < amount:
            exhausted = phase
            return False
        return True

    def finish():
        return {"cohort": cohort, "mode": "work", "policy": policy,
                "fraction": fraction, "repeat": repeat, "budget": budget,
                "spent": spent, "costs": costs, "solved": len(solved),
                "solved_ids": solved, "attempts": attempts, "exhausted_phase": exhausted}

    def accept(case, status, witness):
        verification = validate_witness(case["weights"], case["target"], status, witness)
        if not consume(verification, "verification"):
            return False
        if status != "unresolved":
            solved.append(case["case_id"])
        return True

    # Every policy pays the same shared exact-precheck sweep first.
    for case in ordered:
        kernel = case["kernel"]
        if not consume(kernel["work"], "preprocessing"):
            return finish()
        if kernel["status"] != "unresolved":
            if not accept(case, kernel["status"], kernel["witness"]):
                return finish()
        else:
            pending.append(case)
    if policy in ARMS or policy == "distance_rule":
        residual = []
        feature_arm = "five" if policy == "distance_rule" else policy
        for case in pending:
            if not consume(case["feature_work"][feature_arm], "features"):
                return finish()
            if feature_arm != "conventional":
                reuse = case["reuse"]
                if not consume(reuse["work"], "core_queries"):
                    return finish()
                if reuse["status"] != "unresolved":
                    if not accept(case, reuse["status"], reuse["witness"]):
                        return finish()
                    continue
            residual.append(case)
        pending = residual
        for case in pending:
            if policy == "distance_rule":
                if not consume(1, "inference"):
                    return finish()
                scores[case["case_id"]] = 2.0 ** (-min(case["vectors"]["five"]))
            else:
                model_name = f"{policy}:logistic"
                if not consume(case["inference_work"][model_name], "inference"):
                    return finish()
                scores[case["case_id"]] = case["predictions"][model_name]
    if policy != "arrival":
        sort_work = (len(pending) if policy == "random" else
                     len(pending) * max(1, len(pending).bit_length()))
        if not consume(sort_work, "sorting"):
            return finish()
    pending = rank_cases(pending, policy, scores, cohort=cohort, repeat=repeat)
    for case in pending:
        if spent >= budget:
            break
        allowance = case["budget"] - case["kernel"]["work"]
        remaining = budget - spent
        if remaining >= allowance:
            reference = reference_map[case["case_id"]]
            status, witness = reference["status"], reference["witness"]
            used = reference["work"] - case["kernel"]["work"]
            clipped = False
        else:
            result = limited_portfolio(case["kernel"]["weights"], case["kernel"]["target"], remaining)
            status, witness, used = result["status"], result["witness"], result["work"]
            if witness is not None:
                from advanced_features import Kernel
                witness = lift_witness(Kernel(**case["kernel"]), witness)
            check(case["weights"], case["target"], case["truth"] == "yes", {**result, "witness": witness})
            clipped = True
        if not consume(used, "solving"):
            raise AssertionError("a capped solve overran its work budget")
        attempts.append({"case_id": case["case_id"], "status": status, "work": used, "clipped": clipped})
        if not accept(case, status, witness):
            return finish()
    return finish()


def live_pool(cases, bundles, policy, fraction, repeat):
    """Complete live run; no precomputed features, runtimes or probabilities."""
    cohort = cases[0]["cohort"]
    budget = fraction * len(cases) * CONFIG["per_case_seconds"]
    started = perf_counter()
    phases = {name: 0.0 for name in PHASES}
    solved, attempts, pending, scores, kernels = [], [], [], {}, {}
    exhausted = None
    ordered = arrivals(cases, cohort, repeat)

    def expired(phase):
        nonlocal exhausted
        if perf_counter() - started > budget:
            exhausted = phase
            return True
        return False

    def finish():
        elapsed = perf_counter() - started
        return {"cohort": cohort, "mode": "time", "policy": policy,
                "fraction": fraction, "repeat": repeat, "budget": budget,
                "spent": elapsed, "costs": phases, "solved": len(solved),
                "solved_ids": solved, "attempts": attempts, "exhausted_phase": exhausted,
                "overshoot_seconds": max(0, elapsed - budget)}

    def accept(case, status, witness):
        tick = perf_counter()
        validate_witness(case["weights"], case["target"], status, witness)
        phases["verification"] += perf_counter() - tick
        if expired("verification"):
            return False
        if status != "unresolved":
            solved.append(case["case_id"])
        return True

    for case in ordered:
        tick = perf_counter()
        kernel = reduce_instance(case["weights"], case["target"])
        phases["preprocessing"] += perf_counter() - tick
        kernels[case["case_id"]] = kernel
        if expired("preprocessing"):
            return finish()
        if kernel.status != "unresolved":
            if not accept(case, kernel.status, kernel.witness):
                return finish()
        else:
            pending.append(case)
    if policy in ARMS or policy == "distance_rule":
        vectors, residual = [], []
        for case in pending:
            kernel = kernels[case["case_id"]]
            tick = perf_counter()
            structural, ordinary, advanced = [], [], None
            if policy != "conventional":
                advanced = extract_advanced(kernel.weights, FeatureConfig(**CONFIG["features"]),
                                            max_steps=CONFIG["max_steps"])
                structural = list(advanced.values)
            if policy in ("conventional", "hybrid"):
                ordinary = conventional(case["weights"], case["target"])
            vector = ordinary if policy == "conventional" else structural + ordinary
            phases["features"] += perf_counter() - tick
            if expired("features"):
                return finish()
            if advanced is not None:
                tick = perf_counter()
                reuse = full_core_query(advanced, True, kernel.target, case["budget"])
                witness = reuse["witness"]
                if witness is not None:
                    witness = lift_witness(kernel, witness)
                phases["core_queries"] += perf_counter() - tick
                if expired("core_queries"):
                    return finish()
                if reuse["status"] != "unresolved":
                    if not accept(case, reuse["status"], witness):
                        return finish()
                    continue
            residual.append(case)
            vectors.append(vector)
        pending = residual
        tick = perf_counter()
        if policy == "distance_rule":
            for case, vector in zip(pending, vectors):
                scores[case["case_id"]] = 2.0 ** (-min(vector))
        else:
            probabilities, _, _ = infer(bundles[f"{policy}:logistic"], vectors, count_work=False)
            scores = {c["case_id"]: p for c, p in zip(pending, probabilities)}
        phases["inference"] += perf_counter() - tick
        if expired("inference"):
            return finish()
    tick = perf_counter()
    pending = rank_cases(pending, policy, scores, time_mode=True, cohort=cohort, repeat=repeat)
    phases["sorting"] += perf_counter() - tick
    if expired("sorting"):
        return finish()
    for case in pending:
        remaining = budget - (perf_counter() - started)
        if remaining <= 0:
            exhausted = "solving"
            break
        kernel = kernels[case["case_id"]]
        allowance = min(CONFIG["per_case_seconds"] - kernel.seconds, remaining)
        if allowance <= 0:
            continue
        tick = perf_counter()
        result = limited_portfolio(kernel.weights, kernel.target,
                                   case["budget"] - kernel.work, allowance)
        witness = result["witness"]
        if witness is not None:
            witness = lift_witness(kernel, witness)
        elapsed_solve = perf_counter() - tick
        phases["solving"] += elapsed_solve
        within_case = elapsed_solve <= allowance
        status = result["status"] if within_case else "unresolved"
        attempts.append({"case_id": case["case_id"], "status": status,
                         "returned_status": result["status"], "seconds": elapsed_solve,
                         "allowance_seconds": allowance, "within_case_deadline": within_case,
                         "witness": witness, "work": result["work"]})
        if expired("solving"):
            return finish()
        if not accept(case, status, witness):
            return finish()
    return finish()


def aggregate(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[(row["mode"], row["cohort"], row["fraction"], row["policy"])].append(row)
    summary = []
    for (mode, cohort, fraction, policy), group in sorted(groups.items()):
        summary.append({"mode": mode, "cohort": cohort, "fraction": fraction, "policy": policy,
                        "median_solved": median(r["solved"] for r in group),
                        "min_solved": min(r["solved"] for r in group),
                        "max_solved": max(r["solved"] for r in group),
                        "runs": len(group), "planning_exhaustions": sum(r["exhausted_phase"] in (
                            "features", "inference", "sorting", "core_queries") for r in group),
                        "max_overshoot_seconds": max(r.get("overshoot_seconds", 0) for r in group)})
    return summary


def report(summary):
    lines = ["# Frozen practical prioritization experiment", "",
             "Work results are deterministic-counter replays with charged planning phases. "
             "Time results are separate live runs, including feature extraction and model inference. "
             "Both use shared exact prechecks first; completed answers are independently validated.", "",
             "Medians over three arrival/timing repetitions. The 0.2/0.5 budgets are fractions "
             "of total declared per-instance allowances, not fractions selected from observed runtimes.", "",
             "| Mode | Cohort | Fraction | Arrival | Random | Short input | Distance rule | Five | Conventional | Combined |",
             "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    indexed = {(r["mode"], r["cohort"], r["fraction"], r["policy"]): r for r in summary}
    for mode, cohort, fraction in sorted({key[:3] for key in indexed}):
        values = [indexed[(mode, cohort, fraction, policy)]["median_solved"] for policy in CONFIG["pool_policies"]]
        lines.append(f"| {mode} | {cohort} | {fraction} | " + " | ".join(str(v) for v in values) + " |")
    lines += ["", "Counter replay is not a wall-clock speedup claim. The live deadlines are "
              "cooperative: the last feature/query/solver operation may finish after the deadline; "
              "late answers are not counted. All overshoots and phase costs are recorded. "
              "The timing comparison is machine-specific. Inference uses frozen logistic models; "
              "forest predictions belong to the secondary predictive evaluation only.", "",
              "Arrival order is seed-shuffled; random order uses a separate seed. Repetitions "
              "are not independent input samples. No negative prediction removes a case as NO. "
              "Only paid exact prechecks, core queries or solvers can complete an instance."]
    return "\n".join(lines) + "\n"


def run(output):
    verify(output)
    if (output / "priority.started.json").exists():
        raise FileExistsError("priority stage cannot overwrite a started run")
    for name, digest in json.loads((output / "data_hashes.json").read_text()).items():
        if sha(output / name) != digest:
            raise AssertionError("fresh evaluation data changed")
    from datetime import datetime, timezone
    save_json(output / "priority.started.json", {"utc": datetime.now(timezone.utc).isoformat()})
    cases, references = read_jsonl(output / "cases.jsonl"), read_jsonl(output / "references.jsonl")
    reference_map = {r["case_id"]: r for r in references if r["mode"] == "work"}
    bundles = joblib.load(output / "models.joblib")
    cohorts = defaultdict(list)
    for case in cases:
        cohorts[case["cohort"]].append(case)
    rows = []
    # Persist each row immediately; an interrupted live run remains inspectable.
    with (output / "priority_runs.jsonl").open("x", encoding="utf-8") as handle:
        for mode in ("work", "time"):
            fractions = CONFIG["pool_work_fractions"] if mode == "work" else CONFIG["pool_time_fractions"]
            for cohort, pool in sorted(cohorts.items()):
                for fraction in fractions:
                    for repeat in range(CONFIG["pool_repeats"]):
                        policies = list(CONFIG["pool_policies"])
                        random.Random(f"{CONFIG['seed']}:{mode}:{cohort}:{fraction}:{repeat}").shuffle(policies)
                        for policy in policies:
                            row = (replay_pool(pool, reference_map, policy, fraction, repeat) if mode == "work" else
                                   live_pool(pool, bundles, policy, fraction, repeat))
                            # Truth/oracle records are consulted after execution, outside the
                            # measured interval, solely to validate completed exact decisions.
                            ids = {c["case_id"]: c for c in pool}
                            if len(set(row["solved_ids"])) != row["solved"]:
                                raise AssertionError("duplicate pool completion")
                            for attempt in row["attempts"]:
                                case = ids[attempt["case_id"]]
                                status = attempt.get("returned_status", attempt["status"])
                                check(case["weights"], case["target"], case["truth"] == "yes",
                                      {"status": status, "witness": attempt.get("witness")})
                            rows.append(row)
                            handle.write(json.dumps(row, separators=(",", ":")) + "\n")
                            handle.flush()
                        print(f"completed {mode} {cohort} fraction={fraction} repeat={repeat}", flush=True)
    verify(output)
    summary = aggregate(rows)
    save_json(output / "priority_summary.json", summary)
    (output / "PRIORITY_REPORT.md").write_text(report(summary), encoding="utf-8")
    save_json(output / "priority_hashes.json", {name: sha(output / name) for name in (
        "priority_runs.jsonl", "priority_summary.json", "PRIORITY_REPORT.md")})
    print(f"Completed and checked {len(rows)} practical pool runs", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
