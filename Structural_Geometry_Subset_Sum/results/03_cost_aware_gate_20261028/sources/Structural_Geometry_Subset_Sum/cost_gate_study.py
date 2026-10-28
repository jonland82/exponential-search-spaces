"""Experiment 03: learn whether a bounded geometric check repays its cost."""
from collections import defaultdict
from datetime import datetime, timezone
import argparse
import json
from pathlib import Path
import random
import shutil
from time import perf_counter

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from Structural_Geometry_Subset_Sum.classifier_features import LEGACY_CONFIG, SCHEMAS, new_weights
from Structural_Geometry_Subset_Sum.compat import ROOT, independent_halves, independent_query, input_length
from Structural_Geometry_Subset_Sum.cost_gate import POLICIES, DEFAULTS, capped_cost, gate_score, solve_gate
from Structural_Geometry_Subset_Sum.study import (check_manifest, make_weights, manifest,
    read_jsonl, save_json, save_jsonl, sha, signature)


HERE = Path(__file__).resolve().parent
STRUCTURED = ("large_base", "large_base_one_outlier", "large_base_many_outliers", "wide_aggregate")
FAMILIES = list(LEGACY_CONFIG["families"])+list(STRUCTURED)
CONFIG = dict(seed=780281028, sizes=[24, 30, 36], families=FAMILIES,
    replicates=dict(train=4, calibration=2, test=4),
    targets=["planted", "middle", "fractional_band"], work_multiplier=32,
    solver=DEFAULTS, logistic=dict(C=1., max_iter=2000, random_state=630251026),
    thresholds=[0., .1, .25, .5, .75, .9, 1.1],
    pool_fractions=[.2, .5], repeats=3, per_case_seconds=.020,
    bootstrap_draws=2000, policies=list(POLICIES),
    primary="learned minus simple exact completions at 50% work-pool budget, repeat-average summed across cohorts",
    training="sign of paired censored-work saving, weighted by absolute saving; ties excluded",
    calibration="minimize actual learned-policy capped-work cost, ties prefer higher threshold",
    status="locally frozen root cost-aware gate experiment; work-trained, live transfer secondary")


def utc():
    return datetime.now(timezone.utc).isoformat()


def verify(output):
    p = json.loads((output/"protocol.json").read_text())
    assert p["config"] == CONFIG
    assert sha(output/"protocol.json") == (output/"protocol.sha256").read_text().strip()
    for name, digest in p["source_hashes"].items():
        assert sha(ROOT/name) == sha(output/"sources"/name) == digest, name
    for name, digest in p["input_hashes"].items():
        assert sha(ROOT/name) == digest, name
    return p


def freeze(output):
    if output.exists():
        raise FileExistsError("use a fresh output directory")
    sources = [HERE/name for name in ("cost_gate.py", "cost_gate_study.py", "cost_gate_audit.py",
        "tests/test_cost_gate.py", "experiments/03_cost_aware_gate/PROTOCOL.md",
        "classifier_features.py", "budget.py", "compat.py", "structures/large_base.py", "study.py", "solver.py")]
    # Include every dependency protected by the preceding classifier experiment.
    previous = json.loads((HERE/"results/02_literature_classifier_20261028/protocol.json").read_text())
    sources += [ROOT/name for name in previous["source_hashes"]]
    sources = sorted(set(sources))
    prior = sorted(p for p in ROOT.rglob("lists.jsonl") if not
        {"sources", "upstream", "reruns", ".git", ".build"}.intersection(p.relative_to(ROOT).parts))
    seen = sorted({signature(r["weights"]) for p in prior for r in read_jsonl(p)})
    output.mkdir(parents=True)
    for source in sources:
        dest = output/"sources"/source.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
    p = dict(config=CONFIG, frozen_at_utc=utc(),
        source_hashes={str(p.relative_to(ROOT)):sha(p) for p in sources},
        input_hashes={str(p.relative_to(ROOT)):sha(p) for p in prior},
        prior_signatures=seen, feature_schema=SCHEMAS["doubling19"])
    save_json(output/"protocol.json", p)
    (output/"protocol.sha256").write_text(sha(output/"protocol.json")+"\n")
    print(f"FROZEN: cost-sensitive root gate, {len(seen)} prior normalized lists excluded", flush=True)


def check_answer(case, result):
    assert result["work"] <= case["budget"]
    assert result["work"] == sum(result["phase_work"].values())
    if result["status"] != "unresolved":
        assert result["status"] == case["truth"]
    witness = result["witness"]
    if witness is not None:
        assert len(set(witness)) == len(witness)
        assert all(0 <= i < len(case["weights"]) for i in witness)
        assert sum(case["weights"][i] for i in witness) == case["target"]


def paired_records(case):
    pair = {p:solve_gate(case["weights"], case["target"], p, max_work=case["budget"])
            for p in ("never", "always")}
    for row in pair.values():
        check_answer(case, row)
    delta = capped_cost(pair["never"], case["budget"])-capped_cost(pair["always"], case["budget"])
    return dict(case_id=case["case_id"], split=case["split"], list_id=case["list_id"],
        eligible=pair["never"]["decision_eligible"], features=pair["never"]["gate_features"],
        saving=delta, label=int(delta > 0), absolute_saving=abs(delta), runs=pair)


def generate(output, test=False):
    p = verify(output)
    prefix = "test" if test else "development"
    if test:
        check_manifest(output, "model_hashes.json")
    save_json(output/f"{prefix}.started.json", dict(utc=utc(),
        model_sha256=sha(output/"gate.json") if test else None))
    seen = set(p["prior_signatures"])
    if test:
        seen.update(signature(r["weights"]) for r in read_jsonl(output/"development_lists.jsonl"))
    lists, cases, proposals, pairs = [], [], [], []
    for split in (["test"] if test else ["train", "calibration"]):
        for n in CONFIG["sizes"]:
            for family in FAMILIES:
                for replicate in range(CONFIG["replicates"][split]):
                    list_id = f"costgate-{split}-n{n}-{family}-s{replicate}"
                    for proposal in range(64):
                        rng = random.Random(f'{CONFIG["seed"]}:{list_id}:{proposal}')
                        variant = rng.randrange(4)
                        if family == "wide_aggregate":
                            base = (1 << 28) if variant % 2 == 0 else rng.randrange(1 << 28, 1 << 29)
                            pmax, radius = (32 if variant < 2 else 128), (8 if variant % 2 == 0 else 64)
                            weights = [base*rng.randrange(1, pmax+1)+rng.randrange(-radius, radius+1) for _ in range(n)]
                            rng.shuffle(weights)
                            metadata = dict(base=base, pmax=pmax, residual_radius=radius)
                            metadata["p"] = [(w+base//2)//base for w in weights]
                        elif family in STRUCTURED:
                            weights, metadata = make_weights(family, n, variant, rng)
                        else:
                            replacements = round(n*.25) if rng.getrandbits(1) else 0
                            weights = new_weights(family, n, replacements, rng)
                            metadata = dict(replacements=replacements)
                        code = signature(weights)
                        accepted = code not in seen
                        proposals.append(dict(list_id=list_id, proposal=proposal, accepted=accepted))
                        if accepted:
                            seen.add(code)
                            break
                    else:
                        raise RuntimeError(f"no fresh list for {list_id}")
                    cohort = "large_base" if family in STRUCTURED else "legacy_families"
                    row = dict(list_id=list_id, split=split, family=family, n=n, cohort=cohort,
                               weights=weights, metadata=metadata)
                    lists.append(row)
                    total = sum(weights)
                    targets = [sum(w for w in weights if rng.getrandbits(1)),
                        rng.randrange(3*total//10, 7*total//10+1),
                        metadata["base"]*(sum(metadata["p"])//2)+metadata["base"]//2 if "base" in metadata else total//2+1]
                    halves = independent_halves(weights)
                    for rule, target in zip(CONFIG["targets"], targets):
                        mask = independent_query(halves, target)
                        case = dict(case_id=f"{list_id}-{rule}", list_id=list_id, split=split,
                            family=family, n=n, cohort=cohort, weights=weights, target=target,
                            target_rule=rule, oracle_mask=mask, truth="yes" if mask is not None else "no",
                            budget=CONFIG["work_multiplier"]*input_length(weights, target))
                        cases.append(case)
                        if not test:
                            pairs.append(paired_records(case))
                    del halves
                    if len(lists) % 24 == 0:
                        print(f"{prefix}: {len(lists)} lists / {len(cases)} cases", flush=True)
    names = [f"{prefix}_lists.jsonl", f"{prefix}_cases.jsonl", f"{prefix}_proposals.jsonl"]
    for name, rows in zip(names, (lists, cases, proposals)):
        save_jsonl(output/name, rows)
    if not test:
        save_jsonl(output/"development_pairs.jsonl", pairs)
        names.append("development_pairs.jsonl")
    else:
        save_jsonl(output/"lists.jsonl", read_jsonl(output/"development_lists.jsonl")+lists)
        names.append("lists.jsonl")
    manifest(output, f"{prefix}_hashes.json", names)


def fit_model(pairs):
    training = [p for p in pairs if p["split"] == "train" and p["eligible"] and p["saving"] != 0]
    if not training:
        return dict(constant=0., threshold=.5), None, dict(training_decisions=0, positive=0, negative=0)
    x = np.array([p["features"] for p in training])
    y = np.array([p["label"] for p in training])
    weights = np.array([p["absolute_saving"] for p in training], dtype=float)
    weights /= weights.mean()
    diagnostics = dict(training_decisions=len(training), positive=int(y.sum()), negative=int((1-y).sum()),
        mean_absolute_saving=float(np.mean([p["absolute_saving"] for p in training])))
    if len(set(y)) == 1:
        return dict(constant=float(y[0]), threshold=.5), None, diagnostics
    fitted = make_pipeline(StandardScaler(), LogisticRegression(**CONFIG["logistic"]))
    fitted.fit(x, y, logisticregression__sample_weight=weights)
    scaler, logistic = fitted[0], fitted[-1]
    coef = logistic.coef_[0]/scaler.scale_
    offset = logistic.intercept_[0]-np.dot(coef, scaler.mean_)
    model = dict(coefficients=coef.tolist(), intercept=float(offset), threshold=.5)
    np.testing.assert_allclose([gate_score(model, row) for row in x], fitted.predict_proba(x)[:, 1], atol=1e-12, rtol=0)
    return model, fitted, diagnostics


def select_threshold(cases, model):
    records = []
    for threshold in CONFIG["thresholds"]:
        candidate = dict(model, threshold=threshold)
        results = [solve_gate(c["weights"], c["target"], "learned", max_work=c["budget"], model=candidate)
                   for c in cases]
        for case, result in zip(cases, results):
            check_answer(case, result)
        records.append(dict(threshold=threshold,
            capped_cost=sum(capped_cost(r, c["budget"]) for c, r in zip(cases, results)),
            completed=sum(r["status"] != "unresolved" for r in results),
            checks=sum(r["check_taken"] for r in results)))
    selected = min(records, key=lambda r:(r["capped_cost"], -r["threshold"]))
    return dict(model, threshold=selected["threshold"]), records


def fit(output):
    verify(output)
    check_manifest(output, "development_hashes.json")
    assert not (output/"test.started.json").exists()
    cases = read_jsonl(output/"development_cases.jsonl")
    pairs = read_jsonl(output/"development_pairs.jsonl")
    with threadpool_limits(limits=1):
        model, fitted, diagnostics = fit_model(pairs)
        model, thresholds = select_threshold([c for c in cases if c["split"] == "calibration"], model)
    save_json(output/"gate.json", model)
    joblib.dump(fitted, output/"fitted.joblib")
    save_json(output/"fit_diagnostics.json", dict(**diagnostics, thresholds=thresholds,
        training_pairs=sum(p["split"] == "train" for p in pairs),
        training_eligible=sum(p["split"] == "train" and p["eligible"] for p in pairs),
        zero_saving_eligible=sum(p["split"] == "train" and p["eligible"] and p["saving"] == 0 for p in pairs)))
    save_json(output/"model_freeze.json", dict(utc=utc(), model_sha256=sha(output/"gate.json"),
        development_manifest_sha256=sha(output/"development_hashes.json"),
        training_lists=sorted({c["list_id"] for c in cases if c["split"] == "train"}),
        calibration_lists=sorted({c["list_id"] for c in cases if c["split"] == "calibration"})))
    manifest(output, "model_hashes.json", ["gate.json", "fitted.joblib", "fit_diagnostics.json", "model_freeze.json"])
    print(f"MODEL FROZEN: {diagnostics}, threshold={model['threshold']}", flush=True)


def pool(cases, policy, mode, fraction, repeat, model, counter_map=None):
    cohort = cases[0]["cohort"]
    budget = (int(fraction*sum(c["budget"] for c in cases)) if mode == "work" else
              fraction*len(cases)*CONFIG["per_case_seconds"])
    ordered = list(cases)
    random.Random(f'{CONFIG["seed"]}:arrival:{cohort}:{repeat}').shuffle(ordered)
    started, spent = perf_counter(), 0
    attempts, solved = [], []
    for case in ordered:
        remaining = budget-(spent if mode == "work" else perf_counter()-started)
        if remaining <= 0:
            break
        cap = min(case["budget"], remaining) if mode == "work" else case["budget"]
        allowance = None if mode == "work" else min(CONFIG["per_case_seconds"], remaining)
        cached = mode == "work" and cap == case["budget"] and counter_map is not None
        result = counter_map[(case["case_id"], policy)] if cached else solve_gate(
            case["weights"], case["target"], policy, max_work=cap, seconds=allowance, model=model)
        check_answer(case, result)
        spent += result["work"]
        accepted_at = perf_counter()-started if mode == "time" else spent
        accepted = accepted_at <= budget and (mode == "work" or result["seconds"] < allowance)
        attempts.append(dict(case_id=case["case_id"], accepted=accepted, accepted_at=accepted_at,
            allowance=cap if mode == "work" else allowance, result=result))
        if accepted and result["status"] != "unresolved":
            solved.append(case["case_id"])
    elapsed = perf_counter()-started
    return dict(policy=policy, mode=mode, cohort=cohort, fraction=fraction, repeat=repeat,
        budget=budget, spent=spent if mode == "work" else elapsed, solved=len(solved),
        solved_ids=solved, attempts=attempts,
        overshoot_seconds=0 if mode == "work" else max(0., elapsed-budget))


def bootstrap_counter(cases, counter_map, first, second):
    groups = defaultdict(list)
    for case in cases:
        a, b = counter_map[(case["case_id"], first)], counter_map[(case["case_id"], second)]
        groups[case["list_id"]].append((int(a["status"] != "unresolved")-int(b["status"] != "unresolved"),
            capped_cost(a, case["budget"])-capped_cost(b, case["budget"])))
    sums = np.array([np.sum(v, axis=0) for v in groups.values()])
    draw = np.random.default_rng(CONFIG["seed"]).integers(0, len(sums), (CONFIG["bootstrap_draws"], len(sums)))
    samples = sums[draw].sum(axis=1)
    return dict(completion_difference=int(sums[:, 0].sum()),
        completion_list_bootstrap_95=np.quantile(samples[:, 0], [.025, .975]).tolist(),
        capped_cost_difference=int(sums[:, 1].sum()),
        capped_cost_list_bootstrap_95=np.quantile(samples[:, 1], [.025, .975]).tolist())


def summarize(cases, counter_rows, pools):
    lookup = {(r["case_id"], r["policy"]):r["result"] for r in counter_rows}
    summary = dict(cases=len(cases), lists=len({c["list_id"] for c in cases}), work={}, pools=[],
        paired={p:bootstrap_counter(cases, lookup, "learned", p) for p in POLICIES if p != "learned"})
    for policy in POLICIES:
        group = [lookup[(c["case_id"], policy)] for c in cases]
        summary["work"][policy] = dict(completed=sum(r["status"] != "unresolved" for r in group),
            capped_cost=sum(capped_cost(r, c["budget"]) for c, r in zip(cases, group)),
            actual_work=sum(r["work"] for r in group),
            eligible=sum(r["decision_eligible"] for r in group), checks=sum(r["check_taken"] for r in group),
            checker_completed=sum(r["checker_event"] is not None and r["checker_event"]["status"] != "unresolved" for r in group))
    grouped = defaultdict(list)
    for row in pools:
        grouped[(row["mode"], row["cohort"], row["fraction"], row["policy"])].append(row)
    for (mode, cohort, fraction, policy), group in sorted(grouped.items()):
        values = [r["solved"] for r in group]
        summary["pools"].append(dict(mode=mode, cohort=cohort, fraction=fraction, policy=policy,
            median=float(np.median(values)), minimum=min(values), maximum=max(values)))
    selected = [r for r in pools if r["mode"] == "work" and r["fraction"] == .5]
    totals = {p:[sum(r["solved"] for r in selected if r["policy"] == p and r["repeat"] == repeat)
        for repeat in range(CONFIG["repeats"])] for p in POLICIES}
    summary["primary"] = dict(endpoint=CONFIG["primary"], totals_by_repeat=totals,
        learned_minus_simple=float(np.mean(totals["learned"])-np.mean(totals["simple"])),
        uncertainty="descriptive three paired arrival orders on one fixed test sample; per-case list-bootstrap comparisons are separate endpoints")
    return summary


def report(summary, diagnostics, model):
    lines = ["# Cost-aware root geometric gate", "",
        "A new weighted logistic gate learns the sign of net paired censored-work savings, not ordinary solver completion. Training and threshold selection use disjoint original lists; the model is frozen before fresh test generation. Scores are cost-sensitive decision scores, not calibrated reachability probabilities.", "",
        f'Train decisions with nonzero savings: {diagnostics["training_decisions"]}, positive {diagnostics["positive"]}, negative {diagnostics["negative"]}; selected threshold {model["threshold"]}.', "",
        "## Fixed 32L per-case work endpoint", "",
        "| Policy | Completed | Capped cost | Actual work | Eligible decisions | DP checks | DP completions |",
        "|---|---:|---:|---:|---:|---:|---:|"]
    for p in POLICIES:
        r = summary["work"][p]
        lines.append(f'| {p} | {r["completed"]} | {r["capped_cost"]} | {r["actual_work"]} | {r["eligible"]} | {r["checks"]} | {r["checker_completed"]} |')
    lines += ["", "Unresolved cases contribute their full prescribed budget to capped cost; actual work is reported separately. All policies share exact target reductions, original five-core reuse, and a bitset/DFS/MITM fallback with remaining work/time split among remaining methods. direct_mitm instead spends its fallback allowance on MITM. lean_never and direct_mitm omit geometric discovery. Matched never/always/simple/learned pay the same 19-feature acquisition at eligible decisions and share exact aggregate-gap answers. The learned policy also pays inference; caps always return unresolved, never an unsupported NO.", "",
        "## Paid pools", "",
        "Median exact completions over three paired arrival orders. Both work and live pools include all online phases. Live feature extraction and exact solving are recomputed under real deadlines; late answers are excluded. Work reuses complete deterministic traces only when the complete per-case allowance remains, and reruns any clipped solve.", "",
        "| Mode | Cohort | Fraction | Lean never | Matched never | Always | Simple | Learned | Direct MITM |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    index = {(r["mode"], r["cohort"], r["fraction"], r["policy"]):r for r in summary["pools"]}
    for key in sorted({k[:3] for k in index}):
        lines.append(f"| {key[0]} | {key[1]} | {key[2]} | "+" | ".join(str(index[(*key,p)]["median"]) for p in POLICIES)+" |")
    lines += ["", f'Primary learned-minus-simple repeat-average completion difference at 50% work pools: {summary["primary"]["learned_minus_simple"]:+.2f}.', "",
        "This is a root-only gate for an already discovered eligible geometric DP, not a repeated internal branch gate or a gate avoiding discovery itself. It transfers a work-trained policy to live time only as a secondary test. Capped work is a censored training objective, not an uncensored runtime claim; heterogeneous counters do not measure uniform bit operations. Pooled completion repeats use the same sample, so no independent-repetition significance claim is made. Per-case paired whole-list bootstrap intervals are saved for separate completion/capped-cost endpoints. Constructed families, fixed small sizes and schedule limit generalization. No default model or manuscript is changed."]
    return "\n".join(lines)+"\n"


def evaluate(output):
    verify(output)
    for name in ("development_hashes.json", "model_hashes.json", "test_hashes.json"):
        check_manifest(output, name)
    save_json(output/"evaluation.started.json", dict(utc=utc()))
    cases = read_jsonl(output/"test_cases.jsonl")
    model = json.loads((output/"gate.json").read_text())
    rows, lookup = [], {}
    for index, case in enumerate(cases):
        for policy in POLICIES:
            result = solve_gate(case["weights"], case["target"], policy, max_work=case["budget"], model=model)
            check_answer(case, result)
            lookup[(case["case_id"], policy)] = result
            rows.append(dict(case_id=case["case_id"], policy=policy, result=result))
        if (index+1) % 72 == 0:
            print(f"work policies: {index+1}/{len(cases)} cases", flush=True)
    save_jsonl(output/"counter_runs.jsonl", rows)
    groups = defaultdict(list)
    for case in cases:
        groups[case["cohort"]].append(case)
    pools = []
    with (output/"pool_runs.jsonl").open("x", encoding="utf-8") as handle:
        for mode in ("work", "time"):
            for cohort, group in sorted(groups.items()):
                for fraction in CONFIG["pool_fractions"]:
                    for repeat in range(CONFIG["repeats"]):
                        policies = list(POLICIES)
                        random.Random(f'{CONFIG["seed"]}:{mode}:{cohort}:{fraction}:{repeat}').shuffle(policies)
                        for policy in policies:
                            row = pool(group, policy, mode, fraction, repeat, model, lookup)
                            pools.append(row)
                            handle.write(json.dumps(row, separators=(",", ":"))+"\n")
                            handle.flush()
                        print(f"pools: {mode} {cohort} {fraction} repeat {repeat}", flush=True)
    summary = summarize(cases, rows, pools)
    save_json(output/"summary.json", summary)
    diagnostics = json.loads((output/"fit_diagnostics.json").read_text())
    (output/"REPORT.md").write_text(report(summary, diagnostics, model), encoding="utf-8")
    manifest(output, "evaluation_hashes.json", ["counter_runs.jsonl", "pool_runs.jsonl", "summary.json", "REPORT.md"])
    print((output/"REPORT.md").read_text(), flush=True)


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("stage", choices=("freeze", "development", "fit", "test", "evaluate", "all"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    stages = dict(freeze=freeze, development=lambda p:generate(p), fit=fit,
                  test=lambda p:generate(p, True), evaluate=evaluate)
    with threadpool_limits(limits=1):
        for name in stages if args.stage == "all" else [args.stage]:
            stages[name](args.output.resolve())


if __name__ == "__main__":
    main()
