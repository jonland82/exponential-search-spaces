"""Independent truths/partition arithmetic plus deterministic experiment replay."""
from collections import defaultdict
from datetime import datetime, timezone
import argparse
import json
from pathlib import Path

from threadpoolctl import threadpool_limits

from Structural_Geometry_Subset_Sum.audit import audit_event
from Structural_Geometry_Subset_Sum.classifier_audit import canonical
from Structural_Geometry_Subset_Sum.compat import independent_halves, independent_query, input_length, reduce_instance
from Structural_Geometry_Subset_Sum.cost_gate_study import check_answer
from Structural_Geometry_Subset_Sum.exception_solver import POLICIES, solve_exceptions
from Structural_Geometry_Subset_Sum.exception_study import (CONFIG, PREVIOUS,
    counter_pool, report, summarize, verify)
from Structural_Geometry_Subset_Sum.study import check_manifest, read_jsonl, save_json, sha, signature


def stable(value):
    if isinstance(value,dict):
        return {k:stable(v) for k,v in value.items() if k not in
            ("seconds","phase_seconds","overshoot_seconds","measured_seconds")}
    if isinstance(value,(list,tuple)):
        return [stable(v) for v in value]
    return value


def certificate(case,result):
    check_answer(case,result)
    if result.get("returned_status","unresolved")!="unresolved":
        assert result["returned_status"]==case["truth"]
    kernel=reduce_instance(case["weights"],case["target"])
    g=result["geometry"]
    if g is not None:
        audit_event(dict(geometry=g,weights=kernel.weights,target=kernel.target,witness=None,
            status="no" if result["reason"]=="aggregate_gap" else "unresolved",reason=result["reason"]),CONFIG["solver"])
    if result["root_event"] is not None:
        audit_event(result["root_event"],CONFIG["solver"])
    plan=result["plan"]
    if plan is not None:
        core,exceptions=plan["core"],plan["exceptions"]
        n=len(g["p"])
        assert len(set(core+exceptions))==n and sorted(core+exceptions)==list(range(n))
        assert len(exceptions)<=CONFIG["solver"]["maximum_exceptions"]
        ranking=sorted(range(n),key=lambda i:(-abs(g["r"][i]),i))
        assert exceptions==ranking[:len(exceptions)]
        lo=sum(min(0,g["r"][i]) for i in core)
        hi=sum(max(0,g["r"][i]) for i in core)
        q=min(sum(g["p"][i] for i in core),(g["target"]-lo)//g["base"])
        area=(q+1)*(hi-lo+1)
        assert (lo,hi,q)==(plan["r_min"],plan["r_max"],plan["maximum_q"])
        assert area==plan["dp_bits"]<=CONFIG["solver"]["max_dp_bits"]
        assert (len(core)+1)*area==plan["history_bits"]<=CONFIG["solver"]["max_history_bits"]
    event=result["core_event"]
    if event is not None:
        assert event["plan"]==plan and event["geometry"]==g
        assert 0<=event["core_builds"]<=1
        assert event["work"]<=event["allowance"]
        assert event["assignments"]<=event["total_assignments"]==1<<len(plan["exceptions"])
        if event["status"]!="unresolved":
            assert event["core_builds"]==1 and event["work"]<=plan["estimated_work"]
            assert event["status"]==case["truth"]
        if event["status"]=="no":
            assert event["reason"]=="exception_assignments_exhausted"
            assert event["assignments"]==event["total_assignments"]
        if event["status"]=="yes":
            chosen=event["witness"]
            assert len(set(chosen))==len(chosen)
            assert all(0<=i<len(kernel.weights) for i in chosen)
            assert sum(kernel.weights[i] for i in chosen)==kernel.target


def audit(output):
    protocol=verify(output)
    check_manifest(output,"data_hashes.json")
    check_manifest(output,"evaluation_hashes.json")
    cases=read_jsonl(output/"cases.jsonl")
    lists=read_jsonl(output/"lists.jsonl")
    assert len(lists)==len(CONFIG["sizes"])*len(CONFIG["families"])*CONFIG["replicates"]
    assert len(cases)==3*len(lists) and len({c["case_id"] for c in cases})==len(cases)
    bylist=defaultdict(list)
    case_map={c["case_id"]:c for c in cases}
    for c in cases:
        bylist[c["list_id"]].append(c)
        assert c["budget"]==CONFIG["work_multiplier"]*input_length(c["weights"],c["target"])
    seen=set(protocol["prior_signatures"])
    for index,row in enumerate(lists):
        code=signature(row["weights"])
        assert code not in seen
        seen.add(code)
        group=bylist[row["list_id"]]
        assert len(group)==3 and all(c["weights"]==row["weights"] for c in group)
        halves=independent_halves(row["weights"])
        for c in group:
            mask=independent_query(halves,c["target"])
            assert mask==c["oracle_mask"]
            assert ("yes" if mask is not None else "no")==c["truth"]
        del halves
        if (index+1)%48==0:
            print(f"independent exact truths: {index+1}/{len(lists)} lists",flush=True)
    counters=read_jsonl(output/"counter_runs.jsonl")
    assert len(counters)==len(cases)*len(POLICIES)
    lookup={}
    for index,row in enumerate(counters):
        c=case_map[row["case_id"]]
        certificate(c,row["result"])
        repeated=solve_exceptions(c["weights"],c["target"],row["policy"],max_work=c["budget"],config=CONFIG["solver"])
        assert stable(repeated)==stable(row["result"])
        lookup[(c["case_id"],row["policy"])]=row["result"]
        if (index+1)%576==0:
            print(f"fresh counter replay: {index+1}/{len(counters)}",flush=True)
    assert len(lookup)==len(counters)
    live=read_jsonl(output/"live_runs.jsonl")
    assert len(live)==len(cases)*len(POLICIES)*CONFIG["live_repeats"]
    assert len({(r["case_id"],r["policy"],r["repeat"]) for r in live})==len(live)
    for row in live:
        certificate(case_map[row["case_id"]],row["result"])
        if row["result"]["status"]!="unresolved":
            assert row["result"]["measured_seconds"]<CONFIG["live_seconds"]
    groups=defaultdict(list)
    for c in cases:
        groups[c["cohort"]].append(c)
    pools=read_jsonl(output/"pool_runs.jsonl")
    assert len(pools)==len(groups)*len(CONFIG["pool_fractions"])*3*len(POLICIES)
    assert len({(r["cohort"],r["fraction"],r["repeat"],r["policy"]) for r in pools})==len(pools)
    for row in pools:
        assert row["spent"]==sum(a["result"]["work"] for a in row["attempts"])<=row["budget"]
        accepted=[]
        for attempt in row["attempts"]:
            certificate(case_map[attempt["case_id"]],attempt["result"])
            assert attempt["result"]["work"]<=attempt["allowance"]
            if attempt["result"]["status"]!="unresolved":
                accepted.append(attempt["case_id"])
        assert row["solved_ids"]==accepted and row["solved"]==len(set(accepted))
        repeated=counter_pool(groups[row["cohort"]],lookup,row["policy"],row["fraction"],row["repeat"])
        assert stable(repeated)==stable(row)
    previous_cases={c["case_id"]:c for c in read_jsonl(PREVIOUS/"test_cases.jsonl")}
    selected={r["case_id"] for r in read_jsonl(PREVIOUS/"counter_runs.jsonl") if
        r["policy"]=="learned" and r["result"]["status"]=="unresolved"}
    old=read_jsonl(output/"retrospective_runs.jsonl")
    assert len(old)==3*len(selected)
    assert len({(r["case_id"],r["policy"]) for r in old})==len(old)
    for row in old:
        assert row["case_id"] in selected
        c=previous_cases[row["case_id"]]
        certificate(c,row["result"])
        repeated=solve_exceptions(c["weights"],c["target"],row["policy"],max_work=c["budget"],config=CONFIG["solver"])
        assert stable(repeated)==stable(row["result"])
    summary=summarize(cases,counters,live,pools,old)
    assert canonical(summary)==json.loads((output/"summary.json").read_text())
    assert report(summary)==(output/"REPORT.md").read_text(encoding="utf-8")
    record=dict(status="passed",utc=datetime.now(timezone.utc).isoformat(),auditor_sha256=sha(Path(__file__)),
        lists=len(lists),fresh_cases=len(cases),fresh_counter_replays=len(counters),
        live_runs=len(live),counter_pool_replays=len(pools),retrospective_replays=len(old),
        checks="sources/inputs/artifacts; independent fresh truths; partition/decomposition arithmetic; one-build/full-enumeration invariants; witnesses; all counter/pool/retrospective replays; live deadlines; report reconstruction")
    path=output/"VALIDATION.json"
    if path.exists():
        previous=json.loads(path.read_text())
        assert previous["status"]=="passed" and previous["auditor_sha256"]==record["auditor_sha256"]
        print("All checks passed again; original validation record preserved",flush=True)
    else:
        save_json(path,record)
    print(json.dumps(record,indent=2),flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser(__doc__)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    with threadpool_limits(limits=1):
        audit(args.output.resolve())
