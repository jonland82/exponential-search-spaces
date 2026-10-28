"""Experiment 05: prospectively frozen bounds-first mechanism comparison."""
from collections import defaultdict
from datetime import datetime, timezone
import argparse
import json
from pathlib import Path
import platform
import random
import shutil
from statistics import median
import sys
from time import perf_counter

import numpy as np
from threadpoolctl import threadpool_limits

from Structural_Geometry_Subset_Sum.bounds_solver import DEFAULTS, POLICIES, solve_bounds_portfolio
from Structural_Geometry_Subset_Sum.compat import ROOT, independent_halves, independent_query, input_length
from Structural_Geometry_Subset_Sum.classifier_features import new_weights
from Structural_Geometry_Subset_Sum.cost_gate_study import FAMILIES, STRUCTURED, check_answer
from Structural_Geometry_Subset_Sum.study import (check_manifest, make_weights, manifest,
    read_jsonl, save_json, save_jsonl, sha, signature)


HERE = Path(__file__).resolve().parent
PREVIOUS = HERE/'results/04_exception_core_20261028'
CONFIG = dict(seed=800281028, sizes=[24,30,36], families=FAMILIES, replicates=8,
    targets=['planted','middle','fractional_band'], work_multiplier=32,
    policies=list(POLICIES), solver=DEFAULTS, live_seconds=.020, live_repeats=3,
    bootstrap_draws=4000,
    primary='bounds_first minus frozen reuse: fresh full individual 32L exact completions; paired whole-list bootstrap',
    secondary='capped work, live deadlines, families, bounds-only and matched fast-eager attribution; exploratory unadjusted intervals',
    status='fixed before fresh generation; no ML, parameter fitting, pool claims or asymptotic claim')


def utc():
    return datetime.now(timezone.utc).isoformat()


def freeze(output):
    if output.exists():
        raise FileExistsError('use a fresh output directory')
    previous = json.loads((PREVIOUS/'protocol.json').read_text())
    sources = [ROOT/name for name in previous['source_hashes']]
    sources += [HERE/name for name in ('bounds_solver.py','structures/bounds_core.py',
        'bounds_study.py','bounds_audit.py','tests/test_bounds_core.py',
        'experiments/05_bounds_first/PROTOCOL.md','experiments/05_bounds_first/THEORY.md')]
    sources = sorted(set(sources))
    prior = sorted(p for p in ROOT.rglob('lists.jsonl') if not
        {'sources','upstream','reruns','.git','.build'}.intersection(p.relative_to(ROOT).parts))
    inputs = prior+[PREVIOUS/'cases.jsonl',PREVIOUS/'counter_runs.jsonl',PREVIOUS/'VALIDATION.json']
    seen = sorted({signature(row['weights']) for p in prior for row in read_jsonl(p)})
    output.mkdir(parents=True)
    for source in sources:
        dest = output/'sources'/source.relative_to(ROOT)
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,dest)
    save_json(output/'protocol.json',dict(config=CONFIG,frozen_at_utc=utc(),
        source_hashes={str(p.relative_to(ROOT)):sha(p) for p in sources},
        input_hashes={str(p.relative_to(ROOT)):sha(p) for p in inputs},
        prior_signatures=seen,python=sys.version,platform=platform.platform()))
    (output/'protocol.sha256').write_text(sha(output/'protocol.json')+'\n')
    print(f'FROZEN: {len(sources)} sources; {len(seen)} prior normalized lists excluded',flush=True)


def verify(output):
    p = json.loads((output/'protocol.json').read_text())
    assert p['config'] == CONFIG
    assert sha(output/'protocol.json') == (output/'protocol.sha256').read_text().strip()
    for name,digest in p['source_hashes'].items():
        assert sha(ROOT/name) == sha(output/'sources'/name) == digest,name
    for name,digest in p['input_hashes'].items():
        assert sha(ROOT/name) == digest,name
    return p


def generate(output):
    protocol = verify(output)
    save_json(output/'generation.started.json',dict(utc=utc()))
    seen = set(protocol['prior_signatures'])
    lists,cases,proposals = [],[],[]
    for n in CONFIG['sizes']:
        for family in FAMILIES:
            for replicate in range(CONFIG['replicates']):
                list_id = f'bounds-n{n}-{family}-s{replicate}'
                for proposal in range(64):
                    rng = random.Random(f'{CONFIG["seed"]}:{list_id}:{proposal}')
                    variant = rng.randrange(4)
                    if family == 'wide_aggregate':
                        base = (1 << 28) if variant % 2 == 0 else rng.randrange(1 << 28,1 << 29)
                        pmax,radius = (32 if variant < 2 else 128),(8 if variant % 2 == 0 else 64)
                        weights = [base*rng.randrange(1,pmax+1)+rng.randrange(-radius,radius+1) for _ in range(n)]
                        rng.shuffle(weights)
                        metadata = dict(base=base,pmax=pmax,residual_radius=radius,
                            p=[(w+base//2)//base for w in weights])
                    elif family in STRUCTURED:
                        weights,metadata = make_weights(family,n,variant,rng)
                    else:
                        replacements = round(n*.25) if rng.getrandbits(1) else 0
                        weights = new_weights(family,n,replacements,rng)
                        metadata = dict(replacements=replacements)
                    code = signature(weights)
                    accepted = code not in seen
                    proposals.append(dict(list_id=list_id,proposal=proposal,accepted=accepted))
                    if accepted:
                        seen.add(code)
                        break
                else:
                    raise RuntimeError(f'no fresh list for {list_id}')
                cohort = 'large_base' if family in STRUCTURED else 'legacy_families'
                lists.append(dict(list_id=list_id,family=family,n=n,cohort=cohort,weights=weights,metadata=metadata))
                total = sum(weights)
                targets = [sum(w for w in weights if rng.getrandbits(1)),
                    rng.randrange(3*total//10,7*total//10+1),
                    metadata['base']*(sum(metadata['p'])//2)+metadata['base']//2 if 'base' in metadata else total//2+1]
                halves = independent_halves(weights)
                for rule,target in zip(CONFIG['targets'],targets):
                    mask = independent_query(halves,target)
                    cases.append(dict(case_id=f'{list_id}-{rule}',list_id=list_id,family=family,n=n,
                        cohort=cohort,weights=weights,target=target,target_rule=rule,oracle_mask=mask,
                        truth='yes' if mask is not None else 'no',budget=CONFIG['work_multiplier']*input_length(weights,target)))
                del halves
                if len(lists)%48 == 0:
                    print(f'generated {len(lists)}/384 lists',flush=True)
    for name,rows in (('lists.jsonl',lists),('cases.jsonl',cases),('proposals.jsonl',proposals)):
        save_jsonl(output/name,rows)
    manifest(output,'data_hashes.json',['lists.jsonl','cases.jsonl','proposals.jsonl'])


def paired(cases,lookup,first,second,metric='completion'):
    blocks = defaultdict(float)
    first_only = second_only = 0
    for c in cases:
        a,b = lookup[(c['case_id'],first)],lookup[(c['case_id'],second)]
        a_done,b_done = a['status'] != 'unresolved',b['status'] != 'unresolved'
        first_only += a_done and not b_done
        second_only += b_done and not a_done
        if metric == 'completion':
            difference = int(a_done)-int(b_done)
        else:
            # Positive means first saves work relative to second. Censor failures.
            difference = (b['work'] if b_done else c['budget'])-(a['work'] if a_done else c['budget'])
        blocks[c['list_id']] += difference
    values = np.array(list(blocks.values()))
    draws = np.random.default_rng(CONFIG['seed']).integers(0,len(values),(CONFIG['bootstrap_draws'],len(values)))
    return dict(difference=int(values.sum()),list_bootstrap_95=np.quantile(values[draws].sum(axis=1),[.025,.975]).tolist(),
        first_only=int(first_only),second_only=int(second_only),lists=len(values))


def summarize(cases,counters,live,retrospective):
    lookup = {(r['case_id'],r['policy']):r['result'] for r in counters}
    summary = dict(cases=len(cases),lists=len({c['list_id'] for c in cases}),work={},live={},families={},
        primary=paired(cases,lookup,'bounds_first','reuse'),comparisons={},retrospective={})
    for p in POLICIES:
        group = [lookup[(c['case_id'],p)] for c in cases]
        events = [r['core_event'] for r in group if r['core_event'] is not None]
        summary['work'][p] = dict(completed=sum(r['status'] != 'unresolved' for r in group),
            actual_work=sum(r['work'] for r in group),
            capped_cost=sum(r['work'] if r['status'] != 'unresolved' else c['budget'] for c,r in zip(cases,group)),
            discovery_work=sum(r['phase_work']['core_discovery'] for r in group),
            discovery_caps=sum(r.get('discovery_event') is not None and r['discovery_event']['reason']=='discovery_cap' for r in group),
            core_calls=len(events),core_completed=sum(e['status'] != 'unresolved' for e in events),
            core_builds=sum(e['core_builds'] for e in events),
            bounds_no=sum(e['reason']=='exception_bounds_exhausted' for e in events),
            point_queries=sum(e['point_queries'] for e in events),
            max_history_bits=max(r['peak_history_bits'] for r in group))
        totals = [sum(r['policy']==p and r['repeat']==rep and r['result']['status'] != 'unresolved' for r in live)
            for rep in range(CONFIG['live_repeats'])]
        summary['live'][p] = dict(totals=totals,median=median(totals),minimum=min(totals),maximum=max(totals),
            max_overshoot_seconds=max(r['result']['overshoot_seconds'] for r in live if r['policy']==p))
        if p != 'bounds_first':
            summary['comparisons'][p] = dict(completions=paired(cases,lookup,'bounds_first',p),
                capped_work_saved=paired(cases,lookup,'bounds_first',p,'work'))
        summary['retrospective'][p] = dict(cases=sum(r['policy']==p for r in retrospective),
            completed=sum(r['policy']==p and r['result']['status'] != 'unresolved' for r in retrospective))
    for family in FAMILIES:
        chosen = [c for c in cases if c['family']==family]
        summary['families'][family] = {p:sum(lookup[(c['case_id'],p)]['status'] != 'unresolved' for c in chosen) for p in POLICIES}
    return summary


def report(s):
    lines = ['# Bounds before geometric core construction','',
        'Fresh source/config freeze; every acquisition, bound, construction, fallback and verification cost is paid. Root/reuse call the frozen Experiment 04 implementation. No ML or family labels enter solving.','',
        '| Policy | Exact completions | Capped work | Actual work | Discovery work | Core builds | Live 20ms median [range] |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for p in POLICIES:
        w,t = s['work'][p],s['live'][p]
        lines.append(f'| {p} | {w["completed"]}/{s["cases"]} | {w["capped_cost"]} | {w["actual_work"]} | {w["discovery_work"]} | {w["core_builds"]} | {t["median"]} [{t["minimum"]},{t["maximum"]}] |')
    lines += ['',f'Primary bounds-first minus previous reuse completions: {s["primary"]}.','',
        'Intervals resample whole weight lists (three dependent targets per list). They condition on these fixed solvers and this generated mixture. Secondary intervals are exploratory and unadjusted. Timing repeats share the same inputs; counters are heterogeneous units, not CPU/bit operations.','',
        '## Attribution comparisons','',
        '| Comparator | Bounds-first completion difference [95% interval] | Capped work saved [95% interval] |',
        '|---|---:|---:|']
    for p,row in s['comparisons'].items():
        a,b = row['completions'],row['capped_work_saved']
        lines.append(f'| {p} | {a["difference"]:+d} {a["list_bootstrap_95"]} | {b["difference"]:+d} {b["list_bootstrap_95"]} |')
    lines += ['','fast_eager shares the fast discovery, selected plan and gates with bounds_first; only table timing differs. bounds_only uses those same DP-affordability gates and returns unresolved at the first interval-feasible assignment. It is an attribution control, not an unrestricted bounds-only solver.','',
        '## Fresh family completions','','| Family | '+' | '.join(POLICIES)+' |','|---|'+'---:|'*len(POLICIES)]
    for f,group in s['families'].items():
        lines.append('| '+f+' | '+' | '.join(str(group[p]) for p in POLICIES)+' |')
    lines += ['','## Previously observed regressions (retrospective only)','',
        'The three Experiment 04 cases completed by root but missed by reuse are replayed as a diagnostic. They are excluded from all fresh counts and intervals.','']
    for p,row in s['retrospective'].items():
        lines.append(f'- {p}: {row["completed"]}/{row["cases"]}')
    lines += ['','NO requires all exceptional assignments to be rejected by necessary bounds, or complete exact core queries. An interrupted check returns unresolved. Logical DP/history limits do not measure exact Python allocation or RSS. Earlier frozen studies and manuscripts are preserved. No general worst-case or state-of-the-art claim is made.']
    return '\n'.join(lines)+'\n'


def evaluate(output):
    verify(output)
    check_manifest(output,'data_hashes.json')
    save_json(output/'evaluation.started.json',dict(utc=utc()))
    cases = read_jsonl(output/'cases.jsonl')
    counters,live,retrospective = [],[],[]
    for i,c in enumerate(cases):
        for p in POLICIES:
            result = solve_bounds_portfolio(c['weights'],c['target'],p,max_work=c['budget'],config=CONFIG['solver'])
            check_answer(c,result)
            counters.append(dict(case_id=c['case_id'],policy=p,result=result))
        if (i+1)%192 == 0:
            print(f'fresh work comparisons: {i+1}/{len(cases)}',flush=True)
    save_jsonl(output/'counter_runs.jsonl',counters)
    with (output/'live_runs.jsonl').open('x',encoding='utf-8') as handle:
        for repeat in range(CONFIG['live_repeats']):
            ordered = list(cases)
            random.Random(f'{CONFIG["seed"]}:live:{repeat}').shuffle(ordered)
            for i,c in enumerate(ordered):
                policies = list(POLICIES)
                random.Random(f'{CONFIG["seed"]}:{repeat}:{c["case_id"]}').shuffle(policies)
                for p in policies:
                    start = perf_counter()
                    result = solve_bounds_portfolio(c['weights'],c['target'],p,max_work=c['budget'],
                        seconds=CONFIG['live_seconds'],config=CONFIG['solver'])
                    measured = perf_counter()-start
                    result.update(measured_seconds=measured,returned_status=result['status'],
                        overshoot_seconds=max(0.,measured-CONFIG['live_seconds']))
                    if measured >= CONFIG['live_seconds']:
                        result.update(status='unresolved',reason='outer_deadline')
                    check_answer(c,result)
                    row = dict(case_id=c['case_id'],policy=p,repeat=repeat,result=result)
                    live.append(row)
                    handle.write(json.dumps(row,separators=(',',':'))+'\n')
                handle.flush()
                if (i+1)%384 == 0:
                    print(f'live comparisons: repeat={repeat}, {i+1}/{len(cases)}',flush=True)
    old_cases = {c['case_id']:c for c in read_jsonl(PREVIOUS/'cases.jsonl')}
    old_runs = {(r['case_id'],r['policy']):r['result'] for r in read_jsonl(PREVIOUS/'counter_runs.jsonl')}
    for cid,c in old_cases.items():
        if old_runs[(cid,'root')]['status'] == 'unresolved' or old_runs[(cid,'reuse')]['status'] != 'unresolved':
            continue
        for p in POLICIES:
            result = solve_bounds_portfolio(c['weights'],c['target'],p,max_work=c['budget'],config=CONFIG['solver'])
            check_answer(c,result)
            retrospective.append(dict(case_id=cid,policy=p,result=result))
    save_jsonl(output/'retrospective_runs.jsonl',retrospective)
    summary = summarize(cases,counters,live,retrospective)
    save_json(output/'summary.json',summary)
    (output/'REPORT.md').write_text(report(summary),encoding='utf-8')
    manifest(output,'evaluation_hashes.json',['counter_runs.jsonl','live_runs.jsonl',
        'retrospective_runs.jsonl','summary.json','REPORT.md'])
    print(report(summary),flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('stage',choices=('freeze','generate','evaluate','all'))
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        for stage in ('freeze','generate','evaluate') if args.stage=='all' else [args.stage]:
            globals()[stage](args.output.resolve())
