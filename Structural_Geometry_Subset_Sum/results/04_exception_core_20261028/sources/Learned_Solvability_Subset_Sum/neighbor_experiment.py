"""Frozen empirical easy/hard proximity follow-up; preserve previous experiments."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
import json
from math import gcd
from pathlib import Path
import platform
import random
import shutil
from statistics import median
import sys

import joblib
import numpy as np
import sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, balanced_accuracy_score,
                             confusion_matrix, precision_score, recall_score)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from advanced_features import reduce_instance
from features import input_length
from fit_development import matrix, metrics, read_jsonl
from neighbor_models import NeighborModel, ReferenceBank, design
from priority_experiment import aggregate, live_pool, replay_pool
from prospective_study import (CONFIG as OLD_CONFIG, DEVELOPMENT, cohort_for,
    encode_signature, feature_vectors, infer, new_weights, reference, verify as verify_old)
from run_pilot import ROOT, check, independent_halves, independent_query, save_json, save_jsonl, sha

HERE = Path(__file__).resolve().parent
OLD = HERE / 'results/prospective_20261025'
ARMS = ('baseline', 'hard', 'both', 'distances', 'knn')
CONFIG = dict(seed=730251026, k=5, arms=list(ARMS), sizes=[24,32,38],
              families=OLD_CONFIG['families'], fractions=[0,.25], replicates=2,
              scales=[1,(1<<24)+1], targets=OLD_CONFIG['targets'],
              logistic=dict(C=1.,max_iter=2000,random_state=630251026),
              fractions_pool=[.2,.5], repeats=3,
              pool_policies=['arrival','distance_rule',*ARMS],
              primary='fresh pooled unscaled Brier(both) minus Brier(baseline)',
              status='plot-motivated local model freeze; old sample reuse exploratory')


def normalized_signature(weights):
    divisor=gcd(*weights)
    return encode_signature([w//divisor for w in weights])


def probabilities(bundle, x):
    if not len(x):
        return np.array([])
    return np.asarray(infer(bundle, np.asarray(x).tolist(), count_work=False)[0])


def calibrated_bundle(model, calibration_x, calibration_y, dimensions):
    raw=np.clip(model.predict_proba(calibration_x)[:,1],1e-6,1-1e-6)
    logits=np.log(raw/(1-raw)).reshape(-1,1)
    calibrator=LogisticRegression(**CONFIG['logistic']).fit(logits,calibration_y)
    return dict(model=model,calibrator=calibrator,dimensions=dimensions)


def freeze(output):
    if output.exists():
        raise FileExistsError('use a fresh output directory')
    verify_old(OLD)
    cases=read_jsonl(DEVELOPMENT/'cases.jsonl')
    common={r['case_id']:r for r in read_jsonl(DEVELOPMENT/'runs.jsonl') if r['policy']=='common'}
    x=matrix(cases,'hybrid')
    y=np.array([int(common[c['case_id']]['status']!='unresolved') for c in cases])
    train=np.array([c['split']=='train' for c in cases])
    calibration=np.array([c['split']=='calibration' for c in cases])
    groups=np.array([c['list_id'] for c in cases])
    assert not set(groups[train]) & set(groups[calibration])
    bank=ReferenceBank(x[train],y[train],groups[train],CONFIG['k'])
    bundles={'baseline':joblib.load(OLD/'models.joblib')['hybrid:logistic']}
    for arm in ARMS[1:]:
        if arm=='knn':
            model=NeighborModel(bank,arm)
            dimensions=0
        else:
            train_x=design(x[train],bank,arm,groups[train])
            fitted=make_pipeline(StandardScaler(),LogisticRegression(**CONFIG['logistic'])).fit(train_x,y[train])
            model=NeighborModel(bank,arm,fitted)
            dimensions=train_x.shape[1]
        bundles[arm]=calibrated_bundle(model,x[calibration],y[calibration],dimensions)
    # Verify baseline can be reproduced from the specified train/calibration data.
    fit=make_pipeline(StandardScaler(),LogisticRegression(**CONFIG['logistic'])).fit(x[train],y[train])
    rebuilt=calibrated_bundle(fit,x[calibration],y[calibration],15)
    np.testing.assert_allclose(probabilities(rebuilt,x),probabilities(bundles['baseline'],x),atol=1e-12,rtol=0)
    signatures=set()
    prior_files=[]
    for folder in ('pilot_20261025','development_20261025','prospective_20261025','branch_pruning_20261025'):
        path=HERE/'results'/folder/'lists.jsonl'
        prior_files.append(path)
        signatures.update(normalized_signature(row['weights']) for row in read_jsonl(path))
    output.mkdir(parents=True)
    protected=[HERE/name for name in ('neighbor_models.py','neighbor_experiment.py','NEIGHBOR_PROTOCOL.md','test_neighbors.py')]
    protected += [ROOT/name for name in json.loads((OLD/'protocol.json').read_text())['source_hashes']]
    protected=list(dict.fromkeys(protected))
    for source in protected:
        dest=output/'sources'/source.relative_to(ROOT)
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,dest)
    joblib.dump(dict(bank=bank,bundles=bundles,constant=float(y[train].mean())),output/'models.joblib')
    train_distances=bank.class_distances(x[train],groups[train])
    save_jsonl(output/'training_distances.jsonl',[
        dict(case_id=c['case_id'],list_id=c['list_id'],label=int(label),hard_distance=float(d[0]),easy_distance=float(d[1]))
        for c,label,d in zip(np.array(cases,dtype=object)[train],y[train],train_distances)])
    protocol=dict(config=CONFIG,frozen_at_utc=datetime.now(timezone.utc).isoformat(),
        source_hashes={str(p.relative_to(ROOT)):sha(p) for p in protected},
        input_hashes={str(p.relative_to(ROOT)):sha(p) for p in [*prior_files,DEVELOPMENT/'cases.jsonl',DEVELOPMENT/'runs.jsonl',OLD/'models.joblib']},
        model_sha256=sha(output/'models.joblib'),training_distances_sha256=sha(output/'training_distances.jsonl'),
        prior_signatures=sorted(signatures),training_lists=len(set(groups[train])),
        training_cases=int(train.sum()),training_hard_cases=int((1-y[train]).sum()),
        calibration_lists=len(set(groups[calibration])),python=sys.version,
        sklearn=sklearn.__version__,numpy=np.__version__,platform=platform.platform())
    save_json(output/'protocol.json',protocol)
    (output/'protocol.sha256').write_text(sha(output/'protocol.json')+'\n')
    print(f'FROZEN: {len(bundles)} models; {protocol["training_lists"]} training lists; {protocol["training_hard_cases"]} hard reference targets',flush=True)


def verify(output):
    p=json.loads((output/'protocol.json').read_text())
    assert sha(output/'protocol.json')==(output/'protocol.sha256').read_text().strip()
    assert p['config']==CONFIG
    assert sha(output/'models.joblib')==p['model_sha256']
    assert sha(output/'training_distances.jsonl')==p['training_distances_sha256']
    for name,digest in p['source_hashes'].items():
        assert sha(ROOT/name)==sha(output/'sources'/name)==digest,name
    for name,digest in p['input_hashes'].items():
        assert sha(ROOT/name)==digest,name
    return p


def generate(output):
    p=verify(output)
    save_json(output/'generation.started.json',dict(utc=datetime.now(timezone.utc).isoformat()))
    signatures=set(p['prior_signatures'])
    rows,cases,refs,proposals=[],[],[],[]
    for n in CONFIG['sizes']:
        for family in CONFIG['families']:
            for fraction in CONFIG['fractions']:
                for replicate in range(CONFIG['replicates']):
                    base=f'neighbor-n{n}-{family}-r{round(n*fraction)}-s{replicate}'
                    weights=None
                    for proposal in range(32):
                        rng=random.Random(f'{CONFIG["seed"]}:{base}:{proposal}')
                        candidate=new_weights(family,n,round(n*fraction),rng)
                        signature=normalized_signature(candidate)
                        accepted=signature not in signatures
                        proposals.append(dict(base_list_id=base,proposal=proposal,accepted=accepted))
                        if accepted:
                            signatures.add(signature)
                            weights=candidate
                            break
                    if weights is None:
                        raise RuntimeError(f'No nonoverlapping input for {base}')
                    total=sum(weights)
                    below=max(1,min(max(weights)-1,2*total//5))
                    below=below if below%2 else max(1,below-1)
                    targets=[sum(w for w in weights if rng.getrandbits(1)),rng.randrange(3*total//10,7*total//10+1),below,rng.randrange(1,max(2,total//10+1))]
                    halves=independent_halves(weights)
                    truths=[independent_query(halves,t) for t in targets]
                    del halves
                    for scale in CONFIG['scales']:
                        scaled=[w*scale for w in weights]
                        list_id=f'{base}-scale{scale}'
                        cohort=cohort_for(n,family,scale)
                        rows.append(dict(list_id=list_id,base_list_id=base,n=n,family=family,fraction=fraction,replicate=replicate,scale=scale,cohort=cohort,weights=scaled))
                        for rule,t,mask in zip(CONFIG['targets'],targets,truths):
                            target=t*scale
                            kernel=reduce_instance(scaled,target)
                            budget=8*input_length(scaled,target)
                            vectors,work,seconds,reuse=feature_vectors(scaled,target,kernel)
                            case=dict(case_id=f'{list_id}-{rule}',list_id=list_id,base_list_id=base,n=n,family=family,scale=scale,cohort=cohort,target_rule=rule,weights=scaled,target=target,budget=budget,truth='yes' if mask is not None else 'no',oracle_mask=mask,kernel=asdict(kernel),vectors=vectors,feature_work=work,feature_seconds=seconds,reuse=reuse)
                            result=reference(scaled,target,kernel,budget)
                            check(scaled,target,mask is not None,result)
                            check(scaled,target,mask is not None,reuse)
                            cases.append(case)
                            refs.append(dict(case_id=case['case_id'],**result))
                    print(f'generated {base}: {len(cases)} cases',flush=True)
    verify(output)
    for name,data in [('lists.jsonl',rows),('cases.jsonl',cases),('references.jsonl',refs),('proposals.jsonl',proposals)]:
        save_jsonl(output/name,data)
    save_json(output/'data_hashes.json',{name:sha(output/name) for name in ('lists.jsonl','cases.jsonl','references.jsonl','proposals.jsonl')})


def score(y,p):
    y=np.asarray(y,dtype=int)
    p=np.asarray(p,dtype=float)
    result=metrics(y,p)
    if not len(y):
        return result
    hard=1-y
    prediction=(p<.5).astype(int)
    result.update(hard_count=int(hard.sum()),hard_precision=float(precision_score(hard,prediction,zero_division=0)),
        hard_recall=float(recall_score(hard,prediction,zero_division=0)),
        balanced_accuracy=float(balanced_accuracy_score(hard,prediction)),
        hard_average_precision=float(average_precision_score(hard,1-p)) if len(set(y))==2 else None,
        confusion_easy_hard=confusion_matrix(hard,prediction,labels=[0,1]).tolist())
    return result


def bootstrap(cases,y,p,baseline):
    groups=defaultdict(list)
    for i,c in enumerate(cases):
        groups[c['base_list_id']].append(i)
    blocks=list(groups.values())
    loss=(p-y)**2-(baseline-y)**2
    sums=np.array([loss[ids].sum() for ids in blocks])
    counts=np.array([len(ids) for ids in blocks])
    rng=np.random.default_rng(CONFIG['seed'])
    draws=rng.integers(0,len(blocks),(1000,len(blocks)))
    delta=sums[draws].sum(axis=1)/counts[draws].sum(axis=1)
    return dict(difference=float(loss.mean()),list_bootstrap_95_percentile=np.quantile(delta,[.025,.975]).tolist(),base_lists=len(groups),conditional_on_fitted_models=True)


def evaluation_masks(cases):
    scale=np.array([c['scale'] for c in cases])
    masks={'unscaled':scale==1,'scaled':scale!=1,'all_encodings':np.ones(len(cases),dtype=bool)}
    masks.update({name:np.array([c['cohort']==name for c in cases]) for name in sorted({c['cohort'] for c in cases})})
    return masks


def analyze_sample(cases,refs,bank,bundles,constant):
    refmap={r['case_id']:r for r in refs}
    y=np.array([int(refmap[c['case_id']]['status']!='unresolved') for c in cases])
    x=np.array([c['vectors']['hybrid'] for c in cases])
    distances=bank.class_distances(x)
    scores={arm:probabilities(bundle,x) for arm,bundle in bundles.items()}
    scores.update(constant_prior=np.full(len(cases),constant),always_easy=np.ones(len(cases)))
    records=[dict(case_id=c['case_id'],base_list_id=c['base_list_id'],label=int(y[i]),hard_distance=float(distances[i,0]),easy_distance=float(distances[i,1]),probabilities={arm:float(p[i]) for arm,p in scores.items()}) for i,c in enumerate(cases)]
    result=dict(models={},paired={})
    for subgroup,mask in evaluation_masks(cases).items():
        subcases=[c for c,m in zip(cases,mask) if m]
        kernel=mask & np.array([c['kernel']['status']=='unresolved' for c in cases])
        reuse=kernel & np.array([c['reuse']['status']=='unresolved' for c in cases])
        result['models'][subgroup]={arm:dict(all=score(y[mask],p[mask]),unresolved_kernel=score(y[kernel],p[kernel]),unresolved_after_reuse=score(y[reuse],p[reuse])) for arm,p in scores.items()}
        result['paired'][subgroup]={arm:bootstrap(subcases,y[mask],p[mask],scores['baseline'][mask]) for arm,p in scores.items() if arm!='baseline'}
    result['counts']=dict(cases=len(cases),base_lists=len({c['base_list_id'] for c in cases}),completed=int(y.sum()),hard=int((1-y).sum()))
    return result,records


def hashes(output,manifest):
    for name,digest in json.loads((output/manifest).read_text()).items():
        assert sha(output/name)==digest,name


def analyze(output):
    verify(output)
    hashes(output,'data_hashes.json')
    saved=joblib.load(output/'models.joblib')
    cases=read_jsonl(output/'cases.jsonl')
    refs=read_jsonl(output/'references.jsonl')
    result,records=analyze_sample(cases,refs,**saved)
    # Explicitly exploratory: this sample motivated the new hypothesis.
    oldrefs=[r for r in read_jsonl(OLD/'references.jsonl') if r['mode']=='work']
    old,oldrecords=analyze_sample(read_jsonl(OLD/'cases.jsonl'),oldrefs,**saved)
    save_json(output/'prediction_metrics.json',dict(fresh=result,inspected_old_sample_exploratory=old))
    save_jsonl(output/'predictions.jsonl',records)
    save_jsonl(output/'old_predictions_exploratory.jsonl',oldrecords)
    (output/'PREDICTION_REPORT.md').write_text(prediction_report(result,old),encoding='utf-8')
    names=('prediction_metrics.json','predictions.jsonl','old_predictions_exploratory.jsonl','PREDICTION_REPORT.md')
    save_json(output/'prediction_hashes.json',{n:sha(output/n) for n in names})
    print((output/'PREDICTION_REPORT.md').read_text(encoding='utf-8'),flush=True)


def prediction_report(result,old):
    lines=['# Empirical distance-to-hard / distance-to-easy follow-up','',
        'Frozen before new generation; motivated by the previously inspected plot. Hard means reference completion failure under 8L, not proven intrinsic hardness. All geometry uses the 15 original standardized features and development-training reference lists only. k=5 distinct lists; training rows exclude their entire own list. Separate calibration lists fit sigmoid calibration.','',
        '## Fresh unscaled inputs','',
        '| Model | Accuracy | Balanced accuracy | Hard precision | Hard recall | Hard AP | Brier |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for arm,m in result['models']['unscaled'].items():
        r=m['all']
        lines.append(f'| {arm} | {r["accuracy_at_half"]:.3%} | {r["balanced_accuracy"]:.3%} | {r["hard_precision"]:.3%} | {r["hard_recall"]:.3%} | {r["hard_average_precision"]:.4f} | {r["brier"]:.4f} |')
    m=result['models']['unscaled']['baseline']['all']
    lines+=['',f'{m["n"]} cases: {m["n"]-m["hard_count"]} completed and {m["hard_count"]} unresolved. Hard AP is average precision for the hard class; Brier is lower-is-better. Threshold is fixed at p(easy)=0.5. Confusion matrices, log loss, ROC AUC and calibration bins are in prediction_metrics.json.','',
        '## Paired fresh comparisons against baseline','',
        '| Cohort | Cases | Baseline Brier | Hard-added Brier | Both-added Brier | Both minus baseline [conditional list-bootstrap 95% interval] |',
        '|---|---:|---:|---:|---:|---|']
    for group,models in result['models'].items():
        diff=result['paired'][group]['both']
        lo,hi=diff['list_bootstrap_95_percentile']
        lines.append(f'| {group} | {models["baseline"]["all"]["n"]} | {models["baseline"]["all"]["brier"]:.4f} | {models["hard"]["all"]["brier"]:.4f} | {models["both"]["all"]["brier"]:.4f} | {diff["difference"]:+.4f} [{lo:+.4f}, {hi:+.4f}] |')
    lines+=['','## Remaining cases after exact shortcuts','','| Subgroup, fresh unscaled | Cases | Model | Hard recall | Brier |','|---|---:|---|---:|---:|']
    for subset in ('unresolved_kernel','unresolved_after_reuse'):
        for arm in ARMS:
            r=result['models']['unscaled'][arm][subset]
            lines.append(f'| {subset} | {r["n"]} | {arm} | {r["hard_recall"]:.3%} | {r["brier"]:.4f} |')
    lines+=['','## Previously inspected sample: exploratory reuse','','| Model | Accuracy | Hard recall | Brier |','|---|---:|---:|---:|']
    for arm in ARMS:
        r=old['models']['unscaled'][arm]['all']
        lines.append(f'| {arm} | {r["accuracy_at_half"]:.3%} | {r["hard_recall"]:.3%} | {r["brier"]:.4f} |')
    lines+=['','No hyperparameters or thresholds were selected on either evaluation sample. Intervals resample base lists with all related targets and paired encodings kept together; they condition on fixed models. Secondary comparisons have no multiplicity-adjusted significance interpretation. These features re-express existing inputs; they do not add independent information or correctness certificates. See the separately paid priority experiment for actual solver benefit.']
    return '\n'.join(lines)+'\n'


def inference_work(saved,arm):
    bundle=saved['bundles'][arm]
    base=6*bundle['dimensions']+20
    return base+(0 if arm=='baseline' else saved['bank'].work(arm))


def pool_run(cases,refs,saved,predictions,arm,mode,fraction,repeat):
    if arm in ('arrival','distance_rule'):
        return (replay_pool(cases,refs,arm,fraction,repeat) if mode=='work' else live_pool(cases,{},arm,fraction,repeat))
    # Reuse the exact existing runner under its 'hybrid' alias: every learned
    # arm acquires identical original features/cores. The adapter adds paid
    # neighbor lookup inside online inference, never at data-loading time.
    if mode=='time':
        row=live_pool(cases,{'hybrid:logistic':saved['bundles'][arm]},'hybrid',fraction,repeat)
    else:
        adapted=[]
        for c in cases:
            row=dict(c)
            row['predictions']={'hybrid:logistic':predictions[c['case_id']]['probabilities'][arm]}
            row['inference_work']={'hybrid:logistic':inference_work(saved,arm)}
            adapted.append(row)
        row=replay_pool(adapted,refs,'hybrid',fraction,repeat)
    row['policy']=arm
    return row


def priorities(output):
    verify(output)
    hashes(output,'data_hashes.json')
    hashes(output,'prediction_hashes.json')
    saved=joblib.load(output/'models.joblib')
    cases=read_jsonl(output/'cases.jsonl')
    refs={r['case_id']:r for r in read_jsonl(output/'references.jsonl')}
    predictions={r['case_id']:r for r in read_jsonl(output/'predictions.jsonl')}
    groups=defaultdict(list)
    for c in cases:
        groups[c['cohort']].append(c)
    rows=[]
    save_json(output/'priority.started.json',dict(utc=datetime.now(timezone.utc).isoformat()))
    with (output/'priority_runs.jsonl').open('x',encoding='utf-8') as handle:
        for mode in ('work','time'):
            for cohort,pool in sorted(groups.items()):
                for fraction in CONFIG['fractions_pool']:
                    for repeat in range(CONFIG['repeats']):
                        arms=CONFIG['pool_policies'].copy()
                        random.Random(f'{CONFIG["seed"]}:{mode}:{cohort}:{fraction}:{repeat}').shuffle(arms)
                        for arm in arms:
                            row=pool_run(pool,refs,saved,predictions,arm,mode,fraction,repeat)
                            validate_row(row,pool,refs)
                            rows.append(row)
                            handle.write(json.dumps(row,separators=(',',':'))+'\n')
                            handle.flush()
                        print(f'paid pools: {mode} {cohort} fraction={fraction} repeat={repeat}',flush=True)
    verify(output)
    summary=aggregate(rows)
    save_json(output/'priority_summary.json',summary)
    (output/'PRIORITY_REPORT.md').write_text(priority_report(rows,summary),encoding='utf-8')
    names=('priority_runs.jsonl','priority_summary.json','PRIORITY_REPORT.md')
    save_json(output/'priority_hashes.json',{n:sha(output/n) for n in names})
    print((output/'PRIORITY_REPORT.md').read_text(),flush=True)


def validate_row(row,cases,refs):
    ids={c['case_id']:c for c in cases}
    assert len(set(row['solved_ids']))==row['solved']
    assert set(row['solved_ids'])<=set(ids)
    if row['mode']=='work':
        assert row['spent']<=row['budget']
        assert sum(row['costs'].values())==row['spent']
    else:
        assert sum(row['costs'].values())<=row['spent']+1e-6
        for attempt in row['attempts']:
            c=ids[attempt['case_id']]
            check(c['weights'],c['target'],c['truth']=='yes',dict(status=attempt['returned_status'],witness=attempt['witness']))
            assert attempt['within_case_deadline']==(attempt['seconds']<=attempt['allowance_seconds'])
    attempts={a['case_id']:a for a in row['attempts']}
    for case_id in row['solved_ids']:
        c=ids[case_id]
        if c['kernel']['status']!='unresolved':
            check(c['weights'],c['target'],c['truth']=='yes',c['kernel'])
        elif row['policy']!='arrival' and c['reuse']['status']!='unresolved':
            check(c['weights'],c['target'],c['truth']=='yes',c['reuse'])
        else:
            a=attempts[case_id]
            assert a['status']!='unresolved'
            if row['mode']=='time':
                assert a['within_case_deadline']
            else:
                assert a['status']==refs[case_id]['status'] or a['clipped']


def priority_report(rows,summary):
    lines=['# Paid neighbor-guided prioritization','','Same features, core queries, fallback solvers and deadlines in every learned arm. Neighbor lookup is executed inside live inference and fully charged in the declared counter model. No predicted label prunes a case.','',
        'Totals below sum separately budgeted cohort completions within each repetition, then report the median and range over three repetitions. Scaled copies and timing repetitions are not independent problems.','',
        '| Mode | Budget fraction | Policy | Total median [range] | Planning exhaustions / 24 cohort-runs |','|---|---:|---|---:|---:|']
    for mode in ('work','time'):
        for fraction in CONFIG['fractions_pool']:
            for arm in CONFIG['pool_policies']:
                group=[r for r in rows if (r['mode'],r['fraction'],r['policy'])==(mode,fraction,arm)]
                totals=[sum(r['solved'] for r in group if r['repeat']==i) for i in range(3)]
                exhausted=sum(r['exhausted_phase'] in ('features','inference','sorting','core_queries') for r in group)
                lines.append(f'| {mode} | {fraction} | {arm} | {median(totals)} [{min(totals)}, {max(totals)}] | {exhausted} / {len(group)} |')
    lines+=['','Complete per-cohort summaries are in priority_summary.json; per-run phase costs, attempts, deadline flags and completion IDs are in priority_runs.jsonl. Work units are declared heterogeneous counters, not uniform CPU/bit operations. Live times are machine-specific cooperative deadlines and exclude late answers. Training and model loading are offline; every online lookup is included. All learned arms share exact core reuse, so their differences isolate changed prediction/lookup behavior for this pool task. This is prioritization, not branch pruning or a proof of faster asymptotic solving.']
    return '\n'.join(lines)+'\n'


def validate(output):
    protocol=verify(output)
    assert datetime.fromisoformat(json.loads((output/'generation.started.json').read_text())['utc'])>datetime.fromisoformat(protocol['frozen_at_utc'])
    for manifest in ('data_hashes.json','prediction_hashes.json','priority_hashes.json'):
        hashes(output,manifest)
    cases=read_jsonl(output/'cases.jsonl')
    lists=read_jsonl(output/'lists.jsonl')
    refs={r['case_id']:r for r in read_jsonl(output/'references.jsonl')}
    assert len(cases)==1152 and len(lists)==288 and len(refs)==1152
    assert len({c['case_id'] for c in cases})==len(cases)
    assert len({normalized_signature(r['weights']) for r in lists})==144
    assert not {normalized_signature(r['weights']) for r in lists}&set(protocol['prior_signatures'])
    for c in cases:
        kernel=asdict(reduce_instance(c['weights'],c['target']))
        expected=dict(c['kernel'])
        kernel.pop('seconds');expected.pop('seconds')
        assert json.loads(json.dumps(kernel))==expected
        vectors,work,_,reuse=feature_vectors(c['weights'],c['target'],reduce_instance(c['weights'],c['target']))
        assert vectors==c['vectors'] and work==c['feature_work']
        assert json.loads(json.dumps(reuse))==c['reuse']
        check(c['weights'],c['target'],c['truth']=='yes',refs[c['case_id']])
        assert refs[c['case_id']]['work']<=c['budget']
        # Independent fresh oracle replay by base list is below.
    by_base=defaultdict(list)
    for c in cases:
        if c['scale']==1:
            by_base[c['base_list_id']].append(c)
    for group in by_base.values():
        halves=independent_halves(group[0]['weights'])
        for c in group:
            assert independent_query(halves,c['target'])==c['oracle_mask']
        del halves
    saved=joblib.load(output/'models.joblib')
    result,records=analyze_sample(cases,list(refs.values()),**saved)
    assert result==json.loads((output/'prediction_metrics.json').read_text())['fresh']
    assert records==read_jsonl(output/'predictions.jsonl')
    predictions={r['case_id']:r for r in records}
    by_cohort=defaultdict(list)
    for c in cases:
        by_cohort[c['cohort']].append(c)
    rows=read_jsonl(output/'priority_runs.jsonl')
    assert len(rows)==672
    assert len({(r['mode'],r['cohort'],r['fraction'],r['repeat'],r['policy']) for r in rows})==672
    for row in rows:
        pool=by_cohort[row['cohort']]
        validate_row(row,pool,refs)
        if row['mode']=='work':
            assert row==pool_run(pool,refs,saved,predictions,row['policy'],'work',row['fraction'],row['repeat'])
    assert aggregate(rows)==json.loads((output/'priority_summary.json').read_text())
    save_json(output/'VALIDATION.json',dict(status='passed',cases=len(cases),base_lists=144,pool_runs=len(rows),counter_replays_checked=336,oracle_replayed=True,predictions_reproduced=True,hashes_verified=True,utc=datetime.now(timezone.utc).isoformat()))
    print('VALIDATED: 1152 cases, 144 independent base lists, 672 pools, all predictions and 336 counter replays.',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['freeze','generate','analyze','priorities','validate'])
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    globals()[args.stage](args.output)
