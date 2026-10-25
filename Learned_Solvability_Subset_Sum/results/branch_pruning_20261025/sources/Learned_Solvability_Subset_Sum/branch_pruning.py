"""Stage 10: frozen completion scores select sound residual-tree certificates.

No existing study source, model or artifact is modified. See BRANCH_PROTOCOL.md.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from math import exp, gcd, log
from pathlib import Path
import platform
import random
import shutil
from statistics import median
from time import perf_counter

import joblib

from advanced_features import extract_advanced, lift_witness, query_advanced, reduce_instance
from run_development import conventional
from run_pilot import independent_halves, independent_query, save_json, save_jsonl, sha
from prospective_study import CONFIG as OLD_CONFIG, new_weights


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FROZEN = HERE / "results/prospective_20261025"
POLICIES = ("dfs", "always_native", "distance_native", "always_matched",
            "distance_matched", "conventional", "hybrid")
CONFIG = dict(seed=720251026, sizes=[24, 32, 36], fractions=[0, .125],
              families=OLD_CONFIG["families"], targets=["planted", "middle", "odd"],
              checkpoint_stride=4, minimum_remaining=8, checkpoint_cap=128,
              exceptions_cap=6, distance_threshold=2, probability_threshold=.5,
              deterministic_node_cap=10000, live_node_cap=1000000,
              live_seconds=.05, live_repeats=3, policies=list(POLICIES),
              diagnostic_checkpoints=8, status="exploratory frozen-model transfer")


def sigmoid(value):
    return 1 / (1 + exp(-value)) if value >= 0 else exp(value) / (1 + exp(value))


class FrozenScorer:
    """Algebraic scalar equivalent of saved scaler + logistic + calibration."""
    def __init__(self, bundle):
        scaler, model = bundle["model"].steps[0][1], bundle["model"].steps[1][1]
        self.mean = scaler.mean_.tolist()
        self.scale = scaler.scale_.tolist()
        self.coef = model.coef_[0].tolist()
        self.intercept = float(model.intercept_[0])
        self.cal_coef = float(bundle["calibrator"].coef_[0, 0])
        self.cal_intercept = float(bundle["calibrator"].intercept_[0])

    def __call__(self, vector):
        if len(vector) != len(self.coef):
            raise ValueError("wrong vector dimension")
        margin = self.intercept + sum(c * (v - m) / s for v, m, s, c in
                                      zip(vector, self.mean, self.scale, self.coef))
        raw = min(1 - 1e-6, max(1e-6, sigmoid(margin)))
        return sigmoid(self.cal_coef * log(raw / (1 - raw)) + self.cal_intercept)


def load_scorers():
    protocol = json.loads((FROZEN / "protocol.json").read_text())
    # The saved protocol fixes the model bytes; never trust an unverified pickle.
    expected = protocol["model_sha256"]
    if sha(FROZEN / "models.joblib") != expected:
        raise AssertionError("frozen model hash mismatch")
    bundles = joblib.load(FROZEN / "models.joblib")
    return {arm: FrozenScorer(bundles[f"{arm}:logistic"])
            for arm in ("conventional", "hybrid")}


def core_partition(features, dimension):
    if dimension == 4 and features.progression is not None:
        core = features.progression.indices
        kept = set(core)
        exceptions = tuple(i for i in range(len(features.base.weights)) if i not in kept)
        return core, exceptions
    cert = features.base.certificates[dimension]
    return cert.indices, cert.exceptions


def bounded_check(features, target, *, max_exceptions=6, deadline=None):
    """An exhaustive exceptional assignment test, with no probabilistic answers."""
    dimension = min(range(5), key=lambda i: (features.values[i], i))
    _, exceptions = core_partition(features, dimension)
    if len(exceptions) > max_exceptions:
        return dict(status="unresolved", witness=None, queries=0, dimension=dimension,
                    reason="distance_cap")
    weights = tuple(w * features.base.divisor for w in features.base.weights)
    queries = 0
    for mask in range(1 << len(exceptions)):
        if deadline is not None and perf_counter() >= deadline:
            return dict(status="unresolved", witness=None, queries=queries,
                        dimension=dimension, reason="deadline")
        selected = tuple(i for j, i in enumerate(exceptions) if mask & (1 << j))
        residual = target - sum(weights[i] for i in selected)
        witness = query_advanced(features, dimension, residual)
        queries += 1
        if deadline is not None and perf_counter() >= deadline:
            return dict(status="unresolved", witness=None, queries=queries,
                        dimension=dimension, reason="deadline")
        if witness is not None:
            witness = tuple(sorted(selected + witness))
            if len(set(witness)) != len(witness) or sum(weights[i] for i in witness) != target:
                raise AssertionError("bad core/exception witness")
            return dict(status="yes", witness=witness, queries=queries,
                        dimension=dimension, reason="witness")
    return dict(status="no", witness=None, queries=queries, dimension=dimension,
                reason="all_exception_assignments")


def solve_branch(weights, target, policy, scorers, *, seconds=None, node_cap=10000,
                 checkpoints=128, stride=4, minimum_remaining=8,
                 exceptions_cap=6, distance_threshold=2, probability_threshold=.5,
                 probe_limit=8):
    if policy not in POLICIES:
        raise ValueError("unknown policy")
    if any(type(w) is not int or w <= 0 for w in weights):
        raise ValueError("positive integer weights required")
    started = perf_counter()
    deadline = None if seconds is None else started + seconds
    counts = Counter(nodes=0, checkpoints=0, structural_checks=0, structural_yes=0,
                     structural_no=0, core_queries=0, structural_no_leaves=0,
                     cheap_no=0, reduction_no=0, reduction_yes=0,
                     predictions=0, skipped_by_policy=0, ineligible_distance=0)
    times = dict(features=0., inference=0., checker=0., reductions=0.)
    order = sorted(range(len(weights)), key=lambda i: (-weights[i], i))
    ordered = tuple(weights[i] for i in order)
    n = len(ordered)
    suffix_sum, suffix_gcd = [0] * (n + 1), [0] * (n + 1)
    for i in range(n - 1, -1, -1):
        suffix_sum[i] = suffix_sum[i + 1] + ordered[i]
        suffix_gcd[i] = gcd(suffix_gcd[i + 1], ordered[i])
    probes = []
    trace = hashlib.sha256()

    class Stop(Exception):
        pass

    def check_time():
        if deadline is not None and perf_counter() >= deadline:
            raise Stop("deadline")

    def visit(i, residual, chosen):
        check_time()
        if counts["nodes"] >= node_cap:
            raise Stop("node_cap")
        counts["nodes"] += 1
        m = n - i
        if residual == 0:
            return chosen
        if residual < 0 or residual > suffix_sum[i] or (
                suffix_gcd[i] and residual % suffix_gcd[i]):
            counts["cheap_no"] += 1
            return None
        if residual == suffix_sum[i]:
            return chosen + tuple(order[i:])
        if m >= minimum_remaining and i % stride == 0 and counts["checkpoints"] < checkpoints:
            counts["checkpoints"] += 1
            stamp = perf_counter()
            kernel = reduce_instance(ordered[i:], residual)
            times["reductions"] += perf_counter() - stamp
            check_time()
            if kernel.status == "no":
                counts["reduction_no"] += 1
                return None
            if kernel.status == "yes":
                counts["reduction_yes"] += 1
                return chosen + tuple(order[i + j] for j in kernel.witness)
            if len(probes) < probe_limit:
                probes.append((i, residual))
            if policy != "dfs":
                stamp = perf_counter()
                features = extract_advanced(kernel.weights)
                numerical = (None if policy.endswith("native") else
                             conventional(ordered[i:], residual))
                times["features"] += perf_counter() - stamp
                check_time()
                distance = min(features.values)
                allowed = distance <= exceptions_cap
                probability = None
                if not allowed:
                    counts["ineligible_distance"] += 1
                elif policy.startswith("distance"):
                    allowed = distance <= distance_threshold
                elif policy in scorers:
                    stamp = perf_counter()
                    vector = (list(features.values) + numerical if policy == "hybrid" else numerical)
                    probability = scorers[policy](vector)
                    times["inference"] += perf_counter() - stamp
                    counts["predictions"] += 1
                    check_time()
                    allowed = probability >= probability_threshold
                trace.update(f"{i}:{residual}:{distance}:{int(allowed)};".encode())
                if allowed:
                    counts["structural_checks"] += 1
                    stamp = perf_counter()
                    result = bounded_check(features, kernel.target,
                                           max_exceptions=exceptions_cap, deadline=deadline)
                    times["checker"] += perf_counter() - stamp
                    counts["core_queries"] += result["queries"]
                    check_time()
                    if result["status"] == "yes":
                        counts["structural_yes"] += 1
                        lifted = lift_witness(kernel, result["witness"])
                        return chosen + tuple(order[i + j] for j in lifted)
                    if result["status"] == "no":
                        counts["structural_no"] += 1
                        counts["structural_no_leaves"] += 1 << m
                        return None
                elif distance <= exceptions_cap:
                    counts["skipped_by_policy"] += 1
        if i == n:
            return None
        witness = visit(i + 1, residual - ordered[i], chosen + (order[i],))
        return witness if witness is not None else visit(i + 1, residual, chosen)

    try:
        witness = visit(0, target, ())
        if witness is not None and (len(witness) != len(set(witness)) or
                                   sum(weights[i] for i in witness) != target):
            raise AssertionError("bad lifted tree witness")
        check_time()
        status, reason = ("yes", "witness") if witness is not None else ("no", "exhausted")
    except Stop as exc:
        status, reason, witness = "unresolved", str(exc), None
    elapsed = perf_counter() - started
    if seconds is not None and elapsed >= seconds:
        status, reason, witness = "unresolved", "deadline", None
    return dict(status=status, reason=reason, witness=witness, seconds=elapsed,
                overshoot=0 if seconds is None else max(0., elapsed - seconds),
                counts=dict(counts), component_seconds=times, probes=probes,
                decision_trace_sha256=trace.hexdigest())


def prior_signatures():
    seen = set()
    for path in HERE.glob("results/*/lists.jsonl"):
        for line in path.read_text().splitlines():
            row = json.loads(line)
            if "weights" in row:
                seen.add(tuple(sorted(row["weights"])))
    return seen


def make_cases(output):
    rng, seen = random.Random(CONFIG["seed"]), prior_signatures()
    cases, lists = [], []
    for n in CONFIG["sizes"]:
        for family in CONFIG["families"]:
            for fraction in CONFIG["fractions"]:
                for attempt in range(128):
                    weights = new_weights(family, n, round(n * fraction), rng)
                    key = tuple(sorted(weights))
                    if key not in seen:
                        break
                else:
                    raise AssertionError("duplicate exclusion exhausted")
                seen.add(key)
                list_id = f"n{n}-{family}-r{fraction:g}"
                lists.append(dict(list_id=list_id, n=n, family=family, fraction=fraction,
                                  weights=weights, generation_attempt=attempt + 1))
                halves = independent_halves(weights)
                total = sum(weights)
                planted_mask = rng.getrandbits(n)
                planted = sum(w for j, w in enumerate(weights) if planted_mask & (1 << j))
                largest = max(weights)
                targets = [planted, rng.randrange(3 * total // 10, 7 * total // 10 + 1),
                           2 * rng.randrange(max(1, largest // 2)) + 1]
                for rule, target in zip(CONFIG["targets"], targets):
                    mask = independent_query(halves, target)
                    cases.append(dict(case_id=f"{list_id}-{rule}", list_id=list_id,
                                      family=family, n=n, fraction=fraction, target_rule=rule,
                                      weights=weights, target=target,
                                      truth="yes" if mask is not None else "no", oracle_mask=mask))
                del halves
                print(f"Generated {list_id} ({len(cases)} cases)", flush=True)
    save_jsonl(output / "lists.jsonl", lists)
    save_jsonl(output / "cases.jsonl", cases)
    return cases


def diagnose(cases, probes, scorers):
    rows = []
    for case in cases:
        weights = sorted(case["weights"], reverse=True)
        for depth, target in probes.get(case["case_id"], []):
            kernel = reduce_instance(weights[depth:], target)
            if kernel.status != "unresolved":
                raise AssertionError("diagnostic probe must be unresolved by reduction")
            features = extract_advanced(kernel.weights)
            numbers = conventional(weights[depth:], target)
            result = bounded_check(features, kernel.target, max_exceptions=CONFIG["exceptions_cap"])
            rows.append(dict(case_id=case["case_id"], list_id=case["list_id"], depth=depth,
                             residual_target=target, kernel_n=len(kernel.weights),
                             distances=list(features.values), checker_status=result["status"],
                             queries=result["queries"],
                             conventional=scorers["conventional"](numbers),
                             hybrid=scorers["hybrid"](list(features.values) + numbers)))
    return rows


def aggregate(rows):
    return dict(cases=len(rows), completed=sum(r["status"] != "unresolved" for r in rows),
                yes=sum(r["status"] == "yes" for r in rows),
                no=sum(r["status"] == "no" for r in rows),
                total_seconds=sum(r["seconds"] for r in rows),
                total_nodes=sum(r["counts"]["nodes"] for r in rows),
                structural_checks=sum(r["counts"]["structural_checks"] for r in rows),
                structural_no=sum(r["counts"]["structural_no"] for r in rows),
                structural_yes=sum(r["counts"]["structural_yes"] for r in rows),
                structural_no_leaves=sum(r["counts"]["structural_no_leaves"] for r in rows),
                feature_seconds=sum(r["component_seconds"]["features"] for r in rows),
                inference_seconds=sum(r["component_seconds"]["inference"] for r in rows),
                checker_seconds=sum(r["component_seconds"]["checker"] for r in rows),
                max_overshoot=max((r["overshoot"] for r in rows), default=0.))


def diagnostic_metrics(rows, name, label):
    confusion = Counter(tp=0, tn=0, fp=0, fn=0)
    for row in rows:
        predicted = row[name] >= .5
        observed = row["checker_status"] != "unresolved" if label == "completion" else row["checker_status"] == "no"
        confusion[("t" if predicted == observed else "f") + ("p" if predicted else "n")] += 1
    tp, fp, tn, fn = (confusion[k] for k in ("tp", "fp", "tn", "fn"))
    return dict(confusion, n=len(rows), accuracy=(tp + tn) / len(rows) if rows else None,
                precision=tp / (tp + fp) if tp + fp else None,
                recall=tp / (tp + fn) if tp + fn else None)


def summarize(output, cases, runs, diagnostics):
    summary = dict(config=CONFIG, cases=len(cases), lists=len({c["list_id"] for c in cases}),
                   truths=dict(Counter(c["truth"] for c in cases)), by_mode={}, by_family={},
                   by_size={}, diagnostics={}, paired={}, live_paired={})
    for mode in ("nodes", "live"):
        repeats = 1 if mode == "nodes" else CONFIG["live_repeats"]
        summary["by_mode"][mode] = {}
        for policy in POLICIES:
            blocks = [aggregate([r for r in runs if (r["mode"], r["policy"], r["repeat"]) ==
                                 (mode, policy, repeat)]) for repeat in range(repeats)]
            summary["by_mode"][mode][policy] = dict(
                repeats=blocks, median={key: median(b[key] for b in blocks) for key in blocks[0]})
        for field in ("family", "n"):
            destination = summary["by_family" if field == "family" else "by_size"]
            destination[mode] = {}
            for value in sorted({c[field] for c in cases}):
                destination[mode][str(value)] = {}
                for policy in POLICIES:
                    blocks = [aggregate([r for r in runs if r[field] == value and
                                         (r["mode"], r["policy"], r["repeat"]) ==
                                         (mode, policy, repeat)]) for repeat in range(repeats)]
                    destination[mode][str(value)][policy] = {
                        key: median(b[key] for b in blocks) for key in blocks[0]}
    for name in ("hybrid", "conventional"):
        summary["diagnostics"][name] = {
            label: diagnostic_metrics(diagnostics, name, label) for label in ("completion", "no")}
    # Paired deterministic results do not depend on cooperative timing censoring.
    by_policy = {p: {r["case_id"]: r for r in runs if r["mode"] == "nodes" and r["policy"] == p}
                 for p in POLICIES}
    for baseline in ("dfs", "always_matched", "distance_matched", "distance_native", "conventional"):
        common = [c["case_id"] for c in cases if all(by_policy[p][c["case_id"]]["status"] != "unresolved"
                                                     for p in ("hybrid", baseline))]
        summary["paired"][baseline] = dict(
            both_complete=len(common),
            hybrid_seconds=sum(by_policy["hybrid"][c]["seconds"] for c in common),
            baseline_seconds=sum(by_policy[baseline][c]["seconds"] for c in common),
            hybrid_nodes=sum(by_policy["hybrid"][c]["counts"]["nodes"] for c in common),
            baseline_nodes=sum(by_policy[baseline][c]["counts"]["nodes"] for c in common))
        live = {p: {(r["repeat"], r["case_id"]): r for r in runs if r["mode"] == "live" and r["policy"] == p}
                for p in ("hybrid", baseline)}
        groups = defaultdict(list)
        for case in cases:
            delta = 0.
            for repeat in range(CONFIG["live_repeats"]):
                key = (repeat, case["case_id"])
                delta += (int(live["hybrid"][key]["status"] != "unresolved") -
                          int(live[baseline][key]["status"] != "unresolved")) / CONFIG["live_repeats"]
            groups[case["list_id"]].append(delta)
        blocks = [sum(group) for group in groups.values()]
        rng = random.Random(CONFIG["seed"])
        boot = sorted(sum(rng.choices(blocks, k=len(blocks))) for _ in range(1000))
        summary["live_paired"][baseline] = dict(
            mean_repeat_completion_difference=sum(blocks),
            list_bootstrap_95_percentile=[boot[24], boot[974]],
            lists=len(blocks), conditional_on_fixed_models=True,
            uncertainty="descriptive list resampling; no multiple-comparison adjustment")
    save_json(output / "summary.json", summary)
    lines = ["# Stage 10: certified branch checks guided by frozen completion scores", "",
             "Exploratory transfer experiment; no refitting or threshold selection. "
             "The original frozen Paper VI study remains unchanged.", "",
             f"{summary['lists']} fresh lists, {len(cases)} targets; truths: {summary['truths']}.", "",
             "## Live 50 ms budget", "",
             "Medians of aggregate totals across three repeats. Lower time and node totals "
             "alone are not improvements when fewer cases finish. Timing is descriptive.", "",
             "| Policy | Completed | YES | NO | Total seconds | Nodes | Structural NO checks |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    for policy in POLICIES:
        a = summary["by_mode"]["live"][policy]["median"]
        lines.append(f"| {policy} | {a['completed']:g} | {a['yes']:g} | {a['no']:g} | "
                     f"{a['total_seconds']:.3f} | {a['total_nodes']:g} | {a['structural_no']:g} |")
    lines += ["", "## Deterministic 10,000-node cap", "",
              "This cap is on visited DFS nodes, not on total computational work. "
              "Feature, inference and certificate costs are included in elapsed seconds.", "",
              "| Policy | Completed | Total seconds | Nodes | Structural NO checks | Feature seconds | Checker seconds |",
              "|---|---:|---:|---:|---:|---:|---:|"]
    for policy in POLICIES:
        a = summary["by_mode"]["nodes"][policy]["median"]
        lines.append(f"| {policy} | {a['completed']:g} | {a['total_seconds']:.3f} | "
                     f"{a['total_nodes']:g} | {a['structural_no']:g} | "
                     f"{a['feature_seconds']:.3f} | {a['checker_seconds']:.3f} |")
    lines += ["", "## Transfer diagnostic", "",
              "First eight unresolved checkpoints per unguided deterministic DFS case; "
              "these are selected, dependent nodes. The completion model was not trained "
              "for this checker or for NO prediction. A high score never permits removal.", "",
              "| Model | Diagnostic event | Nodes | Accuracy | Precision | Recall |",
              "|---|---|---:|---:|---:|---:|"]
    for name, labels in summary["diagnostics"].items():
        for label, a in labels.items():
            values = ["undefined" if a[k] is None else f"{a[k]:.1%}" for k in ("accuracy", "precision", "recall")]
            lines.append(f"| {name} | {label} | {a['n']} | " + " | ".join(values) + " |")
    lines += ["", "Per-family/size results, all repeat totals, paired common-completion timings, "
              "component costs, certificate counts and deadline overshoots are in summary.json. "
              "Raw inputs, truths, runs, diagnostics and source hashes are preserved. "
              "Certified NO leaf coverage counts assignments, not measured work saved. "
              "No asymptotic runtime claim follows.", ""]
    (output / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    return summary


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    sources = [HERE / name for name in ("branch_pruning.py", "BRANCH_PROTOCOL.md", "features.py",
               "advanced_features.py", "run_pilot.py", "run_development.py", "prospective_study.py",
               "test_branch_pruning.py", "validate_branch_pruning.py")]
    sources += [ROOT / "Structural_Distance_Subset_Sum/structural_subset_sum.py"]
    hashes = {}
    for path in sources:
        relative = path.relative_to(ROOT)
        destination = output / "sources" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)
        hashes[str(relative).replace("\\", "/")] = sha(path)
    freeze = dict(config=CONFIG, started_utc=datetime.now(timezone.utc).isoformat(),
                  sources=hashes, model_sha256=sha(FROZEN / "models.joblib"),
                  old_protocol_sha256=sha(FROZEN / "protocol.json"),
                  python=platform.python_version(), platform=platform.platform(),
                  processor=platform.processor())
    save_json(output / "protocol.json", freeze)
    scorers = load_scorers()
    cases = make_cases(output)
    runs, probes = [], {}
    for mode, repeats in (("nodes", 1), ("live", CONFIG["live_repeats"])):
        for repeat in range(repeats):
            jobs = [(c, p) for c in cases for p in POLICIES]
            random.Random(CONFIG["seed"] + 100 * (mode == "live") + repeat).shuffle(jobs)
            for index, (case, policy) in enumerate(jobs):
                result = solve_branch(case["weights"], case["target"], policy, scorers,
                                      seconds=CONFIG["live_seconds"] if mode == "live" else None,
                                      node_cap=CONFIG["live_node_cap"] if mode == "live" else CONFIG["deterministic_node_cap"])
                if result["status"] != "unresolved" and result["status"] != case["truth"]:
                    raise AssertionError(f"wrong decision: {case['case_id']} {policy}")
                if mode == "nodes" and policy == "dfs":
                    probes[case["case_id"]] = result["probes"]
                result.update(case_id=case["case_id"], list_id=case["list_id"],
                              family=case["family"], n=case["n"], policy=policy,
                              mode=mode, repeat=repeat)
                runs.append(result)
                if (index + 1) % 100 == 0:
                    print(f"{mode} repeat {repeat}: {index + 1}/{len(jobs)} runs", flush=True)
            save_jsonl(output / f"runs_{mode}_{repeat}.jsonl", runs[-len(jobs):])
    diagnostics = diagnose(cases, probes, scorers)
    save_jsonl(output / "diagnostics.jsonl", diagnostics)
    for name, digest in hashes.items():
        if sha(ROOT / name) != digest:
            raise AssertionError("source changed during experiment")
    summary = summarize(output, cases, runs, diagnostics)
    artifacts = [p for p in output.iterdir() if p.is_file()]
    save_json(output / "artifact_hashes.json", {p.name: sha(p) for p in artifacts})
    print(json.dumps({mode: {p: v["median"]["completed"] for p, v in group.items()}
                      for mode, group in summary["by_mode"].items()}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.output)
