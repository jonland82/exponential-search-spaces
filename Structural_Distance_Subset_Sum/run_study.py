"""Freeze, generate, time, and separately profile a structural-distance study."""

from __future__ import annotations

import argparse
from dataclasses import asdict, replace
from datetime import datetime, timezone
import gc
import hashlib
import json
from math import gcd
from pathlib import Path
import platform
import random
import shutil
import sys
from time import perf_counter
import tracemalloc

from core_selection import solve_selected
from run_pilot import check_result, oracle_halves, oracle_query
from structural_subset_sum import Limits, find_core, solve, solve_bitset, solve_dfs, solve_mitm


HERE = Path(__file__).resolve().parent
PROTECTED = (
    "structural_subset_sum.py", "core_selection.py", "run_pilot.py",
    "run_study.py", "analyze_study.py", "test_structural_subset_sum.py",
    "test_core_selection.py", "test_study.py", "STUDY_PROTOCOL.md",
    "SELECTION_THEORY.md", "LITERATURE.md",
)
CONFIG = {
    "version": 1,
    "seed": 902_410_631,
    "sizes": [20, 28, 36],
    "injected": [4, 8, 12],
    "families": ["unrelated", "repeated", "gadget"],
    "replicates": 2,
    "generic_controls_per_size": 2,
    "max_gcd_draws": 32,
    "max_no_proposals": 256,
    "moduli": [8, 10, 16, 32],
    "timing_repeats": 3,
    "memory_n": 20,
    "memory_injected": 8,
    "memory_replicate": 0,
    "timing_limits": asdict(Limits(
        max_work=2_000_000, max_states=1_048_576,
        max_seconds=1.5, max_bitset_bits=16_000_000,
    )),
    "methods": [
        "core_distinct", "core_enumerate", "select_multiplicity",
        "select_support", "dfs", "mitm", "bitset",
    ],
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_json(path, data):
    with path.open("x", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def signature(weights):
    return hashlib.sha256(json.dumps(sorted(weights), separators=(",", ":")).encode()).hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def prior_signatures():
    found = set()
    for path in (HERE / "results").glob("pilot_*/cases.jsonl"):
        for case in read_jsonl(path):
            found.add(signature(case["weights"]))
    return sorted(found)


def freeze(output):
    if output.exists():
        raise FileExistsError("freeze requires a new output directory")
    hashes = {name: sha(HERE / name) for name in PROTECTED}
    output.mkdir(parents=True)
    snapshots = output / "sources"
    snapshots.mkdir()
    for name in PROTECTED:
        shutil.copy2(HERE / name, snapshots / name)
    protocol = {
        "frozen_at_utc": utc(), "config": CONFIG,
        "protected_hashes": hashes, "prior_list_signatures": prior_signatures(),
        "python": sys.version, "platform": platform.platform(),
        "registration": "local immutable protocol freeze, not external preregistration",
    }
    save_json(output / "protocol.json", protocol)
    (output / "protocol.sha256").write_text(sha(output / "protocol.json") + "\n")
    print(f"Frozen protocol and {len(hashes)} source snapshots at {output}", flush=True)


def verify(output):
    protocol = json.loads((output / "protocol.json").read_text())
    assert sha(output / "protocol.json") == (output / "protocol.sha256").read_text().strip()
    assert protocol["config"] == CONFIG, "configuration changed after freeze"
    for name, expected in protocol["protected_hashes"].items():
        assert sha(HERE / name) == expected, f"protected source changed: {name}"
        assert sha(output / "sources" / name) == expected, f"snapshot changed: {name}"
    return protocol


def specs():
    for n in CONFIG["sizes"]:
        for injected in CONFIG["injected"]:
            for family in CONFIG["families"]:
                for replicate in range(CONFIG["replicates"]):
                    yield n, injected, family, replicate
        for replicate in range(CONFIG["generic_controls_per_size"]):
            yield n, None, "generic", replicate


def list_name(n, injected, family, replicate):
    return f"n{n}-r{injected}-{family}-s{replicate}"


def draw_weights(n, injected, family, rng):
    if family == "generic":
        weights = [rng.randrange(1 << 40, 1 << 41) for _ in range(n)]
    elif family == "gadget":
        a = rng.randrange(1, 5)
        weights = [a] * injected + [2 * a, 3 * a]
        total = sum(weights)
        for _ in range(n - len(weights)):
            gap = rng.randrange(max(2, total // 4), max(3, total // 2 + 1))
            weight = total + gap
            weights.append(weight)
            total += weight
    else:
        core = [rng.randrange(1 << 24, 1 << 25)]
        total = core[0]
        for _ in range(n - injected - 1):
            gap = rng.randrange(max(2, total // 4), max(3, total // 2 + 1))
            weight = total + gap
            core.append(weight)
            total += weight
        noise = (
            [core[len(core) // 2]] * injected
            if family == "repeated"
            else [rng.randrange(1, total + 1) for _ in range(injected)]
        )
        weights = core + noise
    rng.shuffle(weights)
    return weights


def residue_sets(weights):
    output = []
    for modulus in CONFIG["moduli"]:
        residues = {0}
        for weight in weights:
            residues |= {(value + weight) % modulus for value in residues}
        output.append((modulus, residues))
    return output


def eligible(target, residues):
    return all(target % modulus in allowed for modulus, allowed in residues)


def case_record(weights, metadata, target, kind, halves, residues):
    start = perf_counter()
    mask = oracle_query(halves, target)
    query_seconds = perf_counter() - start
    if mask is not None:
        assert sum(w for i, w in enumerate(weights) if mask >> i & 1) == target
    return {
        **metadata, "case_id": f"{metadata['list_id']}-{kind}",
        "weights": weights, "target": target, "target_rule": kind,
        "truth": "yes" if mask is not None else "no",
        "oracle_witness_mask": mask, "oracle_query_seconds": query_seconds,
        "passes_moduli": eligible(target, residues),
    }


def generate(output):
    protocol = verify(output)
    for name in ("lists.jsonl", "cases.jsonl", "proposals.jsonl", "generation.json"):
        if (output / name).exists():
            raise FileExistsError(name)
    start = perf_counter()
    prior = set(protocol["prior_list_signatures"])
    seen = set()
    counts = {"lists": 0, "cases": 0, "missing_no": 0, "gcd_failures": 0,
              "overlap_with_pilots": 0, "within_study_overlap": 0}
    with (
        (output / "lists.jsonl").open("x", encoding="utf-8") as list_file,
        (output / "cases.jsonl").open("x", encoding="utf-8") as case_file,
        (output / "proposals.jsonl").open("x", encoding="utf-8") as proposal_file,
    ):
        for n, injected, family, replicate in specs():
            name = list_name(n, injected, family, replicate)
            rng = random.Random(f"{CONFIG['seed']}:{name}")
            weights = None
            for draw in range(CONFIG["max_gcd_draws"]):
                candidate = draw_weights(n, injected, family, rng)
                if gcd(*candidate) == 1:
                    weights = candidate
                    break
            if weights is None:
                counts["gcd_failures"] += 1
                list_file.write(json.dumps({"list_id": name, "status": "gcd_generation_failed"}) + "\n")
                continue
            sig = signature(weights)
            counts["overlap_with_pilots"] += sig in prior
            counts["within_study_overlap"] += sig in seen
            seen.add(sig)
            core = find_core(weights)
            oracle_start = perf_counter()
            halves = oracle_halves(weights)
            oracle_seconds = perf_counter() - oracle_start
            residues = residue_sets(weights)
            total = sum(weights)
            metadata = {
                "list_id": name, "n": n, "injected": injected,
                "family": family, "replicate": replicate,
                "actual_k": len(core.exceptions),
                "max_weight_bits": max(w.bit_length() for w in weights),
                "oracle_preprocessing_seconds": oracle_seconds,
                "weight_draws": draw + 1, "signature": sig,
            }
            targets = [
                ("planted", sum(w for w in weights if rng.getrandbits(1))),
                ("uniform_middle", rng.randint(round(.30 * total), round(.70 * total))),
            ]
            for kind, target in targets:
                case = case_record(weights, metadata, target, kind, halves, residues)
                case_file.write(json.dumps(case) + "\n")
                counts["cases"] += 1
            no_start = perf_counter()
            accepted, filtered, oracle_calls = None, 0, 0
            for attempt in range(1, CONFIG["max_no_proposals"] + 1):
                target = rng.randint(round(.30 * total), round(.70 * total))
                passes = eligible(target, residues)
                case = None
                if passes:
                    oracle_calls += 1
                    case = case_record(
                        weights, metadata, target, "conditioned_no", halves, residues
                    )
                else:
                    filtered += 1
                is_no = case is not None and case["truth"] == "no"
                proposal_file.write(json.dumps({
                    "list_id": name, "attempt": attempt, "target": target,
                    "passes_moduli": passes,
                    "oracle_truth": None if case is None else case["truth"],
                    "oracle_query_seconds": None if case is None else case["oracle_query_seconds"],
                    "accepted": is_no,
                }) + "\n")
                if is_no:
                    accepted = case
                    break
            if accepted is not None:
                assert accepted["passes_moduli"] and accepted["truth"] == "no"
                case_file.write(json.dumps(accepted) + "\n")
                counts["cases"] += 1
            else:
                counts["missing_no"] += 1
            list_file.write(json.dumps({
                **metadata, "status": "generated", "weights": weights,
                "no_proposals": attempt, "no_modular_rejections": filtered,
                "no_oracle_calls": oracle_calls, "conditioned_no_obtained": accepted is not None,
                "no_generation_seconds": perf_counter() - no_start,
            }) + "\n")
            counts["lists"] += 1
            del halves
            print(f"Labeled {name}: k={metadata['actual_k']}, NO={'yes' if accepted else 'missing'}", flush=True)
    verify(output)
    save_json(output / "generation.json", {
        "completed_at_utc": utc(), "counts": counts,
        "elapsed_seconds": perf_counter() - start,
        "file_hashes": {name: sha(output / name) for name in ("lists.jsonl", "cases.jsonl", "proposals.jsonl")},
    })
    print(counts, flush=True)


def load_cases(output):
    verify(output)
    generation = json.loads((output / "generation.json").read_text())
    for name, expected in generation["file_hashes"].items():
        assert sha(output / name) == expected, f"generation artifact changed: {name}"
    return read_jsonl(output / "cases.jsonl")


def run_method(name, weights, target, limits):
    if name == "core_distinct":
        return solve(weights, target, method="distinct", limits=limits)
    if name == "core_enumerate":
        return solve(weights, target, method="enumerate", limits=limits)
    if name == "select_multiplicity":
        return solve_selected(weights, target, policy="multiplicity", limits=limits)
    if name == "select_support":
        return solve_selected(weights, target, policy="support", limits=limits)
    return {"dfs": solve_dfs, "mitm": solve_mitm, "bitset": solve_bitset}[name](
        weights, target, limits=limits
    )


def timing(output):
    cases = load_cases(output)
    if (output / "timing.json").exists() or (output / "runs.jsonl").exists():
        raise FileExistsError("timing output already exists")
    limits = Limits(**CONFIG["timing_limits"])
    rng = random.Random(f"{CONFIG['seed']}:method-order")
    completed = unresolved = 0
    start = perf_counter()
    with (output / "runs.jsonl").open("x", encoding="utf-8") as handle:
        for offset, case in enumerate(cases):
            for repetition in range(CONFIG["timing_repeats"]):
                order = list(CONFIG["methods"])
                rng.shuffle(order)
                for method in order:
                    result = run_method(method, case["weights"], case["target"], limits)
                    check_result(case["weights"], case["target"], case["truth"] == "yes", result)
                    completed += result.status != "unresolved"
                    unresolved += result.status == "unresolved"
                    handle.write(json.dumps({
                        "case_id": case["case_id"], "method": method,
                        "repetition": repetition, **result.to_dict(),
                    }) + "\n")
            handle.flush()
            print(f"Timed {offset + 1}/{len(cases)}: {case['case_id']}", flush=True)
    verify(output)
    save_json(output / "timing.json", {
        "completed_at_utc": utc(), "elapsed_seconds": perf_counter() - start,
        "completed_answers": completed, "unresolved": unresolved, "mismatches": 0,
        "runs_sha256": sha(output / "runs.jsonl"),
    })


def memory_subset(cases):
    return [
        case for case in cases
        if case["n"] == CONFIG["memory_n"]
        and case["replicate"] == CONFIG["memory_replicate"]
        and case["target_rule"] == "conditioned_no"
        and (case["family"] == "generic" or case["injected"] == CONFIG["memory_injected"])
    ]


def memory(output):
    cases = load_cases(output)
    if (output / "memory.jsonl").exists():
        raise FileExistsError("memory output already exists")
    limits = replace(Limits(**CONFIG["timing_limits"]), max_seconds=None)
    with (output / "memory.jsonl").open("x", encoding="utf-8") as handle:
        for case in memory_subset(cases):
            for method in CONFIG["methods"]:
                gc.collect()
                tracemalloc.start(1)
                try:
                    result = run_method(method, case["weights"], case["target"], limits)
                    current, peak = tracemalloc.get_traced_memory()
                finally:
                    tracemalloc.stop()
                check_result(case["weights"], case["target"], case["truth"] == "yes", result)
                handle.write(json.dumps({
                    "case_id": case["case_id"], "method": method,
                    "python_current_bytes": current, "python_peak_bytes": peak,
                    "time_limit_disabled": True, **result.to_dict(),
                }) + "\n")
                handle.flush()
                print(f"Profiled {case['case_id']} / {method}: {result.status}, {peak} bytes", flush=True)
    verify(output)
    save_json(output / "memory_stage.json", {
        "completed_at_utc": utc(), "cases": len(memory_subset(cases)),
        "memory_sha256": sha(output / "memory.jsonl"),
    })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("freeze", "generate", "time", "memory", "report"))
    parser.add_argument("--output", type=Path, default=HERE / "results" / "prospective_20261024")
    args = parser.parse_args()
    output = args.output.resolve()
    if args.stage == "freeze":
        freeze(output)
    elif args.stage == "generate":
        generate(output)
    elif args.stage == "time":
        timing(output)
    elif args.stage == "memory":
        memory(output)
    else:
        from analyze_study import report
        verify(output)
        report(output)


if __name__ == "__main__":
    main()
