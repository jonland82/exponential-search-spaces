"""Experiment 04: fresh costed evaluation of geometric cores with exceptions."""
from collections import defaultdict
from datetime import datetime, timezone
import argparse
import json
from pathlib import Path
import random
import shutil
from statistics import median
from time import perf_counter

import numpy as np
from threadpoolctl import threadpool_limits

from Structural_Geometry_Subset_Sum.classifier_features import new_weights
from Structural_Geometry_Subset_Sum.compat import ROOT, independent_halves, independent_query, input_length
from Structural_Geometry_Subset_Sum.cost_gate_study import FAMILIES, STRUCTURED, check_answer
from Structural_Geometry_Subset_Sum.exception_solver import DEFAULTS, POLICIES, solve_exceptions
from Structural_Geometry_Subset_Sum.study import (check_manifest, make_weights, manifest,
    read_jsonl, save_json, save_jsonl, sha, signature)


HERE = Path(__file__).resolve().parent
PREVIOUS = HERE/"results/03_cost_aware_gate_20261028"
CONFIG = dict(seed=790281028, sizes=[24,30,36], families=FAMILIES, replicates=4,
    targets=["planted", "middle", "fractional_band"], work_multiplier=32,
    policies=list(POLICIES), solver=DEFAULTS, live_seconds=.020, live_repeats=3,
    pool_fractions=[.2,.5], bootstrap_draws=2000,
    primary="fresh full individual 32L completion count: reuse minus root; paired whole-list bootstrap",
    status="locally frozen new exact solver experiment; no ML; old-failure replay explicitly retrospective")


def utc():
    return datetime.now(timezone.utc).isoformat()


def freeze(output):
    if output.exists():
        raise FileExistsError("use a fresh output directory")
    previous = json.loads((PREVIOUS/"protocol.json").read_text())
    sources = [ROOT/name for name in previous["source_hashes"]]
    sources += [HERE/name for name in ("structures/exception_core.py", "exception_solver.py",
        "exception_study.py", "exception_audit.py", "tests/test_exception_core.py", "audit.py",
        "experiments/04_exception_core/PROTOCOL.md", "experiments/04_exception_core/THEORY.md")]
    sources = sorted(set(sources))
    prior = sorted(p for p in ROOT.rglob("lists.jsonl") if not
        {"sources", "upstream", "reruns", ".git", ".build"}.intersection(p.relative_to(ROOT).parts))
    seen = sorted({signature(row["weights"]) for p in prior for row in read_jsonl(p)})
    inputs = prior+[PREVIOUS/"test_cases.jsonl", PREVIOUS/"counter_runs.jsonl", PREVIOUS/"VALIDATION.json"]
    output.mkdir(parents=True)
    for source in sources:
        dest = output/"sources"/source.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
    protocol = dict(config=CONFIG, frozen_at_utc=utc(),
        source_hashes={str(p.relative_to(ROOT)):sha(p) for p in sources},
        input_hashes={str(p.relative_to(ROOT)):sha(p) for p in inputs}, prior_signatures=seen)
    save_json(output/"protocol.json", protocol)
    (output/"protocol.sha256").write_text(sha(output/"protocol.json")+"\n")
    print(f"FROZEN: five exact policies, {len(seen)} previous normalized lists excluded", flush=True)


def verify(output):
    protocol = json.loads((output/"protocol.json").read_text())
    assert protocol["config"] == CONFIG
    assert sha(output/"protocol.json") == (output/"protocol.sha256").read_text().strip()
    for name, digest in protocol["source_hashes"].items():
        assert sha(ROOT/name) == sha(output/"sources"/name) == digest, name
    for name, digest in protocol["input_hashes"].items():
        assert sha(ROOT/name) == digest, name
    return protocol


def generate(output):
    protocol = verify(output)
    save_json(output/"generation.started.json", dict(utc=utc()))
    seen = set(protocol["prior_signatures"])
    lists, cases, proposals = [], [], []
    for n in CONFIG["sizes"]:
        for family in FAMILIES:
            for replicate in range(CONFIG["replicates"]):
                list_id = f"exception-n{n}-{family}-s{replicate}"
                for proposal in range(64):
                    rng = random.Random(f'{CONFIG["seed"]}:{list_id}:{proposal}')
                    variant = rng.randrange(4)
                    if family == "wide_aggregate":
                        base = (1 << 28) if variant % 2 == 0 else rng.randrange(1 << 28, 1 << 29)
                        pmax, radius = (32 if variant < 2 else 128), (8 if variant % 2 == 0 else 64)
                        weights = [base*rng.randrange(1,pmax+1)+rng.randrange(-radius,radius+1) for _ in range(n)]
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
                lists.append(dict(list_id=list_id, family=family, n=n, cohort=cohort,
                                  weights=weights, metadata=metadata))
                total = sum(weights)
                targets = [sum(w for w in weights if rng.getrandbits(1)),
                    rng.randrange(3*total//10,7*total//10+1),
                    metadata["base"]*(sum(metadata["p"])//2)+metadata["base"]//2 if "base" in metadata else total//2+1]
                halves = independent_halves(weights)
                for rule, target in zip(CONFIG["targets"], targets):
                    mask = independent_query(halves,target)
                    cases.append(dict(case_id=f"{list_id}-{rule}",list_id=list_id,family=family,n=n,
                        cohort=cohort,weights=weights,target=target,target_rule=rule,oracle_mask=mask,
                        truth="yes" if mask is not None else "no",budget=32*input_length(weights,target)))
                del halves
                if len(lists) % 24 == 0:
                    print(f"generated {len(lists)}/192 lists, {len(cases)} cases",flush=True)
    for name, rows in (("lists.jsonl",lists),("cases.jsonl",cases),("proposals.jsonl",proposals)):
        save_jsonl(output/name,rows)
    manifest(output,"data_hashes.json",["lists.jsonl","cases.jsonl","proposals.jsonl"])


def paired(cases, lookup, first, second):
    blocks = defaultdict(list)
    for case in cases:
        a,b = lookup[(case["case_id"],first)],lookup[(case["case_id"],second)]
        blocks[case["list_id"]].append(int(a["status"]!="unresolved")-int(b["status"]!="unresolved"))
    sums = np.array([sum(v) for v in blocks.values()])
    draws = np.random.default_rng(CONFIG["seed"]).integers(0,len(sums),(CONFIG["bootstrap_draws"],len(sums)))
    values = sums[draws].sum(axis=1)
    return dict(difference=int(sums.sum()),lists=len(sums),list_bootstrap_95=np.quantile(values,[.025,.975]).tolist(),
                first_only=sum(lookup[(c["case_id"],first)]["status"]!="unresolved" and lookup[(c["case_id"],second)]["status"]=="unresolved" for c in cases),
                second_only=sum(lookup[(c["case_id"],second)]["status"]!="unresolved" and lookup[(c["case_id"],first)]["status"]=="unresolved" for c in cases))


def counter_pool(cases, lookup, policy, fraction, repeat):
    ordered=list(cases)
    random.Random(f'{CONFIG["seed"]}:arrival:{cases[0]["cohort"]}:{repeat}').shuffle(ordered)
    budget=int(fraction*sum(c["budget"] for c in cases))
    spent, attempts, solved=0,[],[]
    for case in ordered:
        remaining=budget-spent
        if remaining<=0:
            break
        cap=min(case["budget"],remaining)
        result=lookup[(case["case_id"],policy)] if cap==case["budget"] else solve_exceptions(
            case["weights"],case["target"],policy,max_work=cap,config=CONFIG["solver"])
        check_answer(dict(case,budget=cap),result)
        spent+=result["work"]
        attempts.append(dict(case_id=case["case_id"],allowance=cap,result=result))
        if result["status"]!="unresolved":
            solved.append(case["case_id"])
    return dict(policy=policy,cohort=cases[0]["cohort"],fraction=fraction,repeat=repeat,
                budget=budget,spent=spent,solved=len(solved),solved_ids=solved,attempts=attempts)


def summarize(cases, counters, live, pools, retrospective):
    lookup={(r["case_id"],r["policy"]):r["result"] for r in counters}
    summary=dict(cases=len(cases),lists=len({c["list_id"] for c in cases}),work={},live={},families={},pools=[],
        primary=paired(cases,lookup,"reuse","root"),
        secondary={p:paired(cases,lookup,"reuse",p) for p in POLICIES if p not in ("reuse","root")},retrospective={})
    for p in POLICIES:
        group=[lookup[(c["case_id"],p)] for c in cases]
        summary["work"][p]=dict(completed=sum(r["status"]!="unresolved" for r in group),
            actual_work=sum(r["work"] for r in group),
            capped_cost=sum(r["work"] if r["status"]!="unresolved" else c["budget"] for c,r in zip(cases,group)),
            plans=sum(r["plan"] is not None for r in group),
            core_calls=sum(r["core_event"] is not None for r in group),
            core_completed=sum(r["core_event"] is not None and r["core_event"]["status"]!="unresolved" for r in group),
            core_builds=sum(r["core_event"]["core_builds"] for r in group if r["core_event"] is not None),
            max_history_bits=max(r["peak_history_bits"] for r in group))
        selected=[r for r in live if r["policy"]==p]
        totals=[sum(r["result"]["status"]!="unresolved" for r in selected if r["repeat"]==rep) for rep in range(CONFIG["live_repeats"])]
        summary["live"][p]=dict(median=median(totals),minimum=min(totals),maximum=max(totals),
            max_overshoot_seconds=max(r["result"]["overshoot_seconds"] for r in selected))
    for family in FAMILIES:
        chosen=[c for c in cases if c["family"]==family]
        summary["families"][family]={p:sum(lookup[(c["case_id"],p)]["status"]!="unresolved" for c in chosen) for p in POLICIES}
    groups=defaultdict(list)
    for row in pools:
        groups[(row["cohort"],row["fraction"],row["policy"])].append(row["solved"])
    for (cohort,fraction,policy),values in sorted(groups.items()):
        summary["pools"].append(dict(cohort=cohort,fraction=fraction,policy=policy,
            median=median(values),minimum=min(values),maximum=max(values)))
    for p in ("root","reuse","direct_mitm"):
        chosen=[r for r in retrospective if r["policy"]==p]
        summary["retrospective"][p]=dict(completed=sum(r["result"]["status"]!="unresolved" for r in chosen),
            selected_cases=len(chosen),many_outlier_completed=sum(r["family"]=="large_base_many_outliers" and r["result"]["status"]!="unresolved" for r in chosen))
    return summary


def report(summary):
    lines=["# Reusable geometric cores with exceptional weights","",
        "Fresh inputs after a source/config freeze; no ML. All online discovery, prefix-history copies, core construction, exceptional queries, exact fallback and witness checking are paid. No planted decomposition or family metadata enters solving.","",
        "| Policy | Full 32L completions | Actual work | Live 20ms median [range] | Core calls / completions |",
        "|---|---:|---:|---:|---|"]
    for p in POLICIES:
        w,t=summary["work"][p],summary["live"][p]
        lines.append(f'| {p} | {w["completed"]} | {w["actual_work"]} | {t["median"]} [{t["minimum"]},{t["maximum"]}] | {w["core_calls"]}/{w["core_completed"]} |')
    primary=summary["primary"]
    lines += ["",f'Primary reuse-minus-root completion difference: {primary["difference"]:+d}; conditional whole-list-bootstrap 95% interval {primary["list_bootstrap_95"]}. Reuse-only completions: {primary["first_only"]}; root-only: {primary["second_only"]}.',"",
        "The primary is full individual work-capped completion on all fresh cases, not a pool endpoint. Bootstrap keeps targets from each weight list together and conditions on the fixed solver. Capped-cost, family, timing and other-control comparisons are secondary; timing repeats share the same cases.","",
        "## Fresh family completions","","| Family | Lean | Root DP | Discovery only | Reuse | Direct MITM |","|---|---:|---:|---:|---:|---:|"]
    for f,group in summary["families"].items():
        lines.append(f"| {f} | "+" | ".join(str(group[p]) for p in POLICIES)+" |")
    lines += ["","## Paid work pools","","| Cohort | Budget fraction | Lean | Root | Discovery only | Reuse | Direct MITM |","|---|---:|---:|---:|---:|---:|---:|"]
    index={(r["cohort"],r["fraction"],r["policy"]):r for r in summary["pools"]}
    for key in sorted({k[:2] for k in index}):
        lines.append(f"| {key[0]} | {key[1]} | "+" | ".join(str(index[(*key,p)]["median"]) for p in POLICIES)+" |")
    lines += ["","## Retrospective repair diagnostic","",
        "The following previously inspected failures motivated the algorithm. This is explicitly exploratory reuse, not fresh evidence or an additional primary endpoint. Root here omits the old classifier's unnecessary doubling/inference costs.","",
        "| Policy | Completed / 115 old misses | Many-outlier cases completed / 14 |","|---|---:|---:|"]
    for p,row in summary["retrospective"].items():
        lines.append(f'| {p} | {row["completed"]} | {row["many_outlier_completed"]} |')
    lines += ["","The route uses the single existing blind projection, removes largest absolute residuals until fixed size/work gates fit, builds one signed two-coordinate bitset table with prefix witnesses, then queries every necessary Gray-code exceptional assignment. Nonnegative quotients and positive exceptional weights justify truncating q using the original target. NO requires a complete core and exhaustion of all assignments. Work/time caps always yield unresolved. Up to nine exceptions and logical DP/history caps bound the route; these are not exact Python/RSS allocation bounds. Heterogeneous work counters are not uniform bit operations. All returned witnesses/answers are independently checked; live late answers are excluded.","",
        "The primary root control shares all existing five-core reuse, original root geometry, caps and bitset/DFS/MITM fallback. Discovery-only measures new partition-search cost without solving; lean/direct MITM are additional controls. Results concern this constructed small-size mixture, not arbitrary subset sum or a new worst-case complexity theorem. Earlier models, experiments and manuscripts are preserved."]
    return "\n".join(lines)+"\n"


def evaluate(output):
    verify(output)
    check_manifest(output,"data_hashes.json")
    save_json(output/"evaluation.started.json",dict(utc=utc()))
    cases=read_jsonl(output/"cases.jsonl")
    counters,live,pools,old=[],[],[],[]
    for index,case in enumerate(cases):
        for policy in POLICIES:
            result=solve_exceptions(case["weights"],case["target"],policy,max_work=case["budget"],config=CONFIG["solver"])
            check_answer(case,result)
            counters.append(dict(case_id=case["case_id"],policy=policy,result=result))
        if (index+1)%96==0:
            print(f"fresh work comparisons: {index+1}/{len(cases)}",flush=True)
    save_jsonl(output/"counter_runs.jsonl",counters)
    with (output/"live_runs.jsonl").open("x",encoding="utf-8") as handle:
        for repeat in range(CONFIG["live_repeats"]):
            ordered=list(cases)
            random.Random(f'{CONFIG["seed"]}:live:{repeat}').shuffle(ordered)
            for index,case in enumerate(ordered):
                policies=list(POLICIES)
                random.Random(f'{CONFIG["seed"]}:{repeat}:{case["case_id"]}').shuffle(policies)
                for policy in policies:
                    start=perf_counter()
                    result=solve_exceptions(case["weights"],case["target"],policy,max_work=case["budget"],
                        seconds=CONFIG["live_seconds"],config=CONFIG["solver"])
                    measured=perf_counter()-start
                    result.update(measured_seconds=measured,returned_status=result["status"],
                        overshoot_seconds=max(0.,measured-CONFIG["live_seconds"]))
                    if measured>=CONFIG["live_seconds"]:
                        result.update(status="unresolved",reason="outer_deadline")
                    check_answer(case,result)
                    row=dict(case_id=case["case_id"],policy=policy,repeat=repeat,result=result)
                    live.append(row)
                    handle.write(json.dumps(row,separators=(",",":"))+"\n")
                    handle.flush()
                if (index+1)%192==0:
                    print(f"fresh live comparisons: repeat={repeat}, {index+1}/{len(cases)}",flush=True)
    lookup={(r["case_id"],r["policy"]):r["result"] for r in counters}
    groups=defaultdict(list)
    for case in cases:
        groups[case["cohort"]].append(case)
    for cohort,group in sorted(groups.items()):
        for fraction in CONFIG["pool_fractions"]:
            for repeat in range(3):
                for policy in POLICIES:
                    pools.append(counter_pool(group,lookup,policy,fraction,repeat))
    save_jsonl(output/"pool_runs.jsonl",pools)
    previous_cases=read_jsonl(PREVIOUS/"test_cases.jsonl")
    previous_missed={r["case_id"] for r in read_jsonl(PREVIOUS/"counter_runs.jsonl")
        if r["policy"]=="learned" and r["result"]["status"]=="unresolved"}
    for case in previous_cases:
        if case["case_id"] not in previous_missed:
            continue
        for policy in ("root","reuse","direct_mitm"):
            result=solve_exceptions(case["weights"],case["target"],policy,max_work=case["budget"],config=CONFIG["solver"])
            check_answer(case,result)
            old.append(dict(case_id=case["case_id"],family=case["family"],policy=policy,result=result))
    save_jsonl(output/"retrospective_runs.jsonl",old)
    summary=summarize(cases,counters,live,pools,old)
    save_json(output/"summary.json",summary)
    (output/"REPORT.md").write_text(report(summary),encoding="utf-8")
    manifest(output,"evaluation_hashes.json",["counter_runs.jsonl","live_runs.jsonl","pool_runs.jsonl",
        "retrospective_runs.jsonl","summary.json","REPORT.md"])
    print((output/"REPORT.md").read_text(),flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser(__doc__)
    parser.add_argument("stage",choices=("freeze","generate","evaluate","all"))
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    with threadpool_limits(limits=1):
        for stage in ("freeze","generate","evaluate") if args.stage=="all" else [args.stage]:
            globals()[stage](args.output.resolve())
