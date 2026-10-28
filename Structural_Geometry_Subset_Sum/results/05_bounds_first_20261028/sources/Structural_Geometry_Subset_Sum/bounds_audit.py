"""Independent arithmetic/truth checks and deterministic Experiment 05 replay."""
from collections import defaultdict
from datetime import datetime, timezone
import argparse
import json
from pathlib import Path

from threadpoolctl import threadpool_limits

from Structural_Geometry_Subset_Sum.audit import audit_event
from Structural_Geometry_Subset_Sum.bounds_solver import POLICIES, solve_bounds_portfolio
from Structural_Geometry_Subset_Sum.bounds_study import CONFIG, PREVIOUS, report, summarize, verify
from Structural_Geometry_Subset_Sum.classifier_audit import canonical
from Structural_Geometry_Subset_Sum.compat import independent_halves, independent_query, input_length, reduce_instance
from Structural_Geometry_Subset_Sum.cost_gate_study import check_answer
from Structural_Geometry_Subset_Sum.exception_audit import stable
from Structural_Geometry_Subset_Sum.study import check_manifest, read_jsonl, save_json, sha, signature


def certificate(case,result,policy):
    check_answer(case,result)
    if result.get('returned_status','unresolved') != 'unresolved':
        assert result['returned_status'] == case['truth']
    assert 0 <= result['work'] <= case['budget']
    assert result['work'] == sum(result['phase_work'].values())
    kernel = reduce_instance(case['weights'],case['target'])
    g = result['geometry']
    if g is not None:
        audit_event(dict(geometry=g,weights=kernel.weights,target=kernel.target,witness=None,
            status='no' if result['reason']=='aggregate_gap' else 'unresolved',reason=result['reason']),CONFIG['solver'])
    if result['root_event'] is not None:
        audit_event(result['root_event'],CONFIG['solver'])
    discovery = result.get('discovery_event')
    if discovery is not None:
        assert discovery['work'] == result['phase_work']['core_discovery']
        assert 0 <= discovery['work'] <= discovery['cap'] <= CONFIG['solver']['discovery_work_cap']
    plan = result['plan']
    if plan is not None:
        core,exceptions = plan['core'],plan['exceptions']
        n = len(g['p'])
        assert len(set(core+exceptions))==n and sorted(core+exceptions)==list(range(n))
        assert len(exceptions)<=CONFIG['solver']['maximum_exceptions']
        assert exceptions == sorted(range(n),key=lambda i:(-abs(g['r'][i]),i))[:len(exceptions)]
        lo = sum(min(0,g['r'][i]) for i in core)
        hi = sum(max(0,g['r'][i]) for i in core)
        q = min(sum(g['p'][i] for i in core),(g['target']-lo)//g['base'])
        assert (lo,hi,q)==(plan['r_min'],plan['r_max'],plan['maximum_q'])
        assert plan['width']==hi-lo+1
        assert plan['dp_bits']==(q+1)*plan['width']<=CONFIG['solver']['max_dp_bits']
        assert plan['history_bits']==(len(core)+1)*plan['dp_bits']<=CONFIG['solver']['max_history_bits']
    event = result['core_event']
    if event is None:
        return
    assert event['plan']==plan and event['geometry']==g
    assert event['work']<=event['allowance'] and event['work']==result['phase_work']['core_solving']
    assert 0<=event['core_builds']<=1
    assert event['assignments']<=event['total_assignments']==1<<len(plan['exceptions'])
    if event['status']!='unresolved':
        assert event['status']==case['truth'] and event['work']<=plan['estimated_work']
    if event['status']=='yes':
        assert event['core_builds']==1
        chosen=event['witness']
        assert len(set(chosen))==len(chosen)
        assert all(0<=i<len(kernel.weights) for i in chosen)
        assert sum(kernel.weights[i] for i in chosen)==kernel.target
    if event['status']=='no':
        assert event['assignments']==event['total_assignments']
    if policy=='bounds_only':
        assert event['core_builds']==event['point_queries']==0
        assert event['status']!='yes'
    if policy in ('bounds_only','bounds_first','fast_eager'):
        # Independently enumerate binary masks (solver uses Gray code), and test
        # the declared necessary interval. No DP or solver code is reused here.
        rejected=0
        for mask in range(1<<len(plan['exceptions'])):
            shifted=g['target']-sum(g['base']*g['p'][i]+g['r'][i]
                for j,i in enumerate(plan['exceptions']) if mask>>j&1)
            total=sum(g['base']*g['p'][i]+g['r'][i] for i in plan['core'])
            low=max(0,-((plan['r_max']-shifted)//g['base']))
            high=min(plan['maximum_q'],(shifted-plan['r_min'])//g['base'])
            rejected += shifted<0 or shifted>total or low>high
        assert event['bound_rejections']+event['feasible_assignments']==event['assignments']
        if event['assignments']==event['total_assignments']:
            assert event['bound_rejections']==rejected
        if event['reason']=='exception_bounds_exhausted':
            assert rejected==event['total_assignments']
            assert event['core_builds']==event['point_queries']==event['feasible_assignments']==0
            assert event['status']=='no'
        if policy=='bounds_first' and event['core_builds']==1:
            assert event['feasible_assignments']>=1


def audit(output):
    protocol=verify(output)
    generation=json.loads((output/'generation.started.json').read_text())
    evaluation=json.loads((output/'evaluation.started.json').read_text())
    assert datetime.fromisoformat(protocol['frozen_at_utc'])<datetime.fromisoformat(generation['utc'])<datetime.fromisoformat(evaluation['utc'])
    check_manifest(output,'data_hashes.json')
    check_manifest(output,'evaluation_hashes.json')
    cases,lists=read_jsonl(output/'cases.jsonl'),read_jsonl(output/'lists.jsonl')
    assert len(lists)==len(CONFIG['sizes'])*len(CONFIG['families'])*CONFIG['replicates']
    assert len(cases)==len(lists)*len(CONFIG['targets'])
    case_map={c['case_id']:c for c in cases}
    assert len(case_map)==len(cases)
    groups=defaultdict(list)
    for c in cases:
        assert c['budget']==CONFIG['work_multiplier']*input_length(c['weights'],c['target'])
        groups[c['list_id']].append(c)
    seen=set(protocol['prior_signatures'])
    for i,row in enumerate(lists):
        code=signature(row['weights'])
        assert code not in seen
        seen.add(code)
        group=groups[row['list_id']]
        assert len(group)==len(CONFIG['targets']) and all(c['weights']==row['weights'] for c in group)
        assert {c['target_rule'] for c in group}==set(CONFIG['targets'])
        halves=independent_halves(row['weights'])
        for c in group:
            mask=independent_query(halves,c['target'])
            assert mask==c['oracle_mask']
            assert ('yes' if mask is not None else 'no')==c['truth']
        del halves
        if (i+1)%96==0:
            print(f'independent truths: {i+1}/{len(lists)} lists',flush=True)
    counters=read_jsonl(output/'counter_runs.jsonl')
    assert len(counters)==len(cases)*len(POLICIES)
    assert len({(r['case_id'],r['policy']) for r in counters})==len(counters)
    for i,row in enumerate(counters):
        c=case_map[row['case_id']]
        certificate(c,row['result'],row['policy'])
        repeated=solve_bounds_portfolio(c['weights'],c['target'],row['policy'],max_work=c['budget'],config=CONFIG['solver'])
        assert stable(repeated)==stable(row['result'])
        if (i+1)%1152==0:
            print(f'fresh counter replay: {i+1}/{len(counters)}',flush=True)
    lookup={(r['case_id'],r['policy']):r['result'] for r in counters}
    for c in cases:
        a,b=lookup[(c['case_id'],'bounds_first')],lookup[(c['case_id'],'fast_eager')]
        assert a['plan']==b['plan']
        assert a['phase_work']['core_discovery']==b['phase_work']['core_discovery']
    live=read_jsonl(output/'live_runs.jsonl')
    assert len(live)==len(cases)*len(POLICIES)*CONFIG['live_repeats']
    assert len({(r['case_id'],r['policy'],r['repeat']) for r in live})==len(live)
    for row in live:
        certificate(case_map[row['case_id']],row['result'],row['policy'])
        result=row['result']
        if result['status']!='unresolved':
            assert result['measured_seconds']<CONFIG['live_seconds']
        assert result['overshoot_seconds']==max(0.,result['measured_seconds']-CONFIG['live_seconds'])
    previous_cases={c['case_id']:c for c in read_jsonl(PREVIOUS/'cases.jsonl')}
    previous_runs={(r['case_id'],r['policy']):r['result'] for r in read_jsonl(PREVIOUS/'counter_runs.jsonl')}
    selected={cid for cid in previous_cases if previous_runs[(cid,'root')]['status']!='unresolved'
        and previous_runs[(cid,'reuse')]['status']=='unresolved'}
    retrospective=read_jsonl(output/'retrospective_runs.jsonl')
    assert {(r['case_id'],r['policy']) for r in retrospective}=={(cid,p) for cid in selected for p in POLICIES}
    assert len(retrospective)==len(selected)*len(POLICIES)
    for row in retrospective:
        c=previous_cases[row['case_id']]
        certificate(c,row['result'],row['policy'])
        replay=solve_bounds_portfolio(c['weights'],c['target'],row['policy'],max_work=c['budget'],config=CONFIG['solver'])
        assert stable(replay)==stable(row['result'])
    summary=summarize(cases,counters,live,retrospective)
    assert canonical(summary)==json.loads((output/'summary.json').read_text())
    assert report(summary)==(output/'REPORT.md').read_text(encoding='utf-8')
    record=dict(status='passed',utc=datetime.now(timezone.utc).isoformat(),auditor_sha256=sha(Path(__file__)),
        lists=len(lists),fresh_cases=len(cases),fresh_counter_replays=len(counters),live_runs=len(live),
        retrospective_replays=len(retrospective),checks='source/input/artifact hashes; fresh independent truths; partition and projection arithmetic; independent complete bounds NO certificates; charged phases/caps; all deterministic counter and retrospective replays; live witnesses/deadlines; matched discovery plans; report reconstruction')
    path=output/'VALIDATION.json'
    if path.exists():
        old=json.loads(path.read_text())
        assert old['status']=='passed' and old['auditor_sha256']==record['auditor_sha256']
        print('Checks passed again; original validation preserved',flush=True)
    else:
        save_json(path,record)
    print(json.dumps(record,indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    with threadpool_limits(limits=1):
        audit(args.output.resolve())
